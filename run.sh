#!/bin/bash

# Cross-platform containerized RC Automation runner
# Works on Linux, macOS, and Windows (with WSL/Git Bash)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS=Linux;;
        Darwin*)    OS=Mac;;
        CYGWIN*)    OS=Windows;;
        MINGW*)     OS=Windows;;
        *)          OS=Unknown;;
    esac
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_info "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        print_info "Please start Docker Desktop and try again"
        return 1
    fi
    
    print_status "Docker is available and running"
    return 0
}

# Check if Docker Compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available"
        print_info "Please install Docker Compose or update Docker Desktop"
        return 1
    fi
    
    print_status "Docker Compose is available: $COMPOSE_CMD"
    return 0
}

# Set environment variables based on OS
set_environment() {
    detect_os
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning ".env file not found, creating template..."
        cat > .env << 'EOF'
# Infisical Configuration (REQUIRED)
INFISICAL_TOKEN=your_infisical_token_here

# RC Automation Variables (Optional - will be fetched from Infisical)
RC_E_1=
RC_P_1=
RC_E_2=
RC_P_2=

# Tailscale Configuration (Optional)
TAILSCALE_IP=
TAILSCALE_ENABLED=false
TAILSCALE_HOSTNAME=

# Docker Configuration
NETWORK_MODE=bridge
EOF
        print_info "Please edit .env file and add your INFISICAL_TOKEN"
        print_info "Then run this script again"
        return 1
    fi
    
    # Set network mode based on OS
    if [ "$OS" = "Linux" ]; then
        export NETWORK_MODE="host"  # Host networking works on Linux
    else
        export NETWORK_MODE="bridge"  # Use bridge networking on macOS/Windows
    fi
    
    print_status "Environment configured for $OS"
}

# Build the Docker image
build_image() {
    print_info "Building Docker image..."
    $COMPOSE_CMD build
    print_status "Docker image built successfully"
}

# Show usage information
show_usage() {
    echo -e "${BLUE}🚀 Cross-Platform RC Automation${NC}"
    echo ""
    echo "Usage: ./run.sh [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  setup                    Initial setup and build"
    echo "  run [args...]           Run RC automation"
    echo "  shell                   Open interactive shell"
    echo "  build                   Build Docker image"
    echo "  logs                    View container logs"
    echo "  clean                   Clean up containers and images"
    echo "  help                    Show this help"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./run.sh setup          # First time setup"
    echo "  ./run.sh run            # Run automation"
    echo "  ./run.sh shell          # Debug/development"
    echo "  ./run.sh logs           # View logs"
    echo ""
    echo -e "${GREEN}Requirements:${NC}"
    echo "  - Docker Desktop installed and running"
    echo "  - INFISICAL_TOKEN set in .env file"
    echo ""
    echo -e "${YELLOW}OS Support:${NC} Linux, macOS, Windows (WSL/Git Bash)"
}

# Clean up containers and images
cleanup() {
    print_info "Cleaning up containers and images..."
    $COMPOSE_CMD down --remove-orphans
    docker system prune -f
    print_status "Cleanup completed"
}

# View logs
view_logs() {
    print_info "Viewing container logs..."
    $COMPOSE_CMD logs -f rc-automation
}

# Main execution
main() {
    # Check prerequisites
    if ! check_docker || ! check_docker_compose; then
        exit 1
    fi
    
    # Set environment
    if ! set_environment; then
        exit 1
    fi
    
    case "${1:-help}" in
        setup)
            print_info "Running initial setup..."
            build_image
            print_info "Running containerized setup..."
            $COMPOSE_CMD run --rm rc-automation setup
            print_status "Setup completed! You can now run: ./run.sh run"
            ;;
        run)
            shift
            if [ $# -eq 0 ]; then
                $COMPOSE_CMD run --rm rc-automation run
            else
                $COMPOSE_CMD run --rm rc-automation run "$@"
            fi
            ;;
        shell)
            $COMPOSE_CMD run --rm rc-automation shell
            ;;
        build)
            build_image
            ;;
        logs)
            view_logs
            ;;
        clean)
            cleanup
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 