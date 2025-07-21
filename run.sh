#!/bin/bash

# Streamlined automation runner for the containerized platform
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
        Linux*)     
            OS=Linux
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO="$NAME"
                VERSION="$VERSION_ID"
            else
                DISTRO="Unknown Linux"
                VERSION="Unknown"
            fi
            ;;
        Darwin*)    
            OS=Mac
            DISTRO="macOS"
            VERSION=$(sw_vers -productVersion)
            ;;
        CYGWIN*|MINGW*)    
            OS=Windows
            DISTRO="Windows"
            VERSION=$(uname -r)
            ;;
        *)          
            OS=Unknown
            DISTRO="Unknown"
            VERSION="Unknown"
            ;;
    esac
    
    print_info "Detected OS: $DISTRO $VERSION"
}

# Check Docker installation
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo ""
        print_info "Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
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

# Check Docker Compose
check_docker_compose() {
    local use_sudo=""
    if ! docker info &> /dev/null && sudo docker info &> /dev/null; then
        use_sudo="sudo "
    fi
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="${use_sudo}docker-compose"
    elif ${use_sudo}docker compose version &> /dev/null; then
        COMPOSE_CMD="${use_sudo}docker compose"
    else
        print_error "Docker Compose is not available"
        return 1
    fi
    
    print_status "Docker Compose is available: $COMPOSE_CMD"
    return 0
}

# Set environment variables based on OS
set_environment() {
    detect_os
    
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
    $COMPOSE_CMD build automation
    print_status "Docker image built successfully"
}

# Show usage information
show_usage() {
    echo -e "${BLUE}🚀 Streamlined Automation Platform${NC}"
    echo ""
    echo "Usage: ./run.sh [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${GREEN}Setup Commands:${NC}"
    echo "  check                   Check system prerequisites"
    echo "  build                   Build Docker image"
    echo "  setup                   Complete setup (build + environment check)"
    echo "  local-setup             Set up local Python environment (no Docker)"
    echo "  setup-complete          Complete local setup + YubiKey secrets sync (all-in-one)"
    echo ""
    echo -e "${GREEN}Infisical & Secrets:${NC}"
    echo "  secrets-status          Show Infisical system status"
    echo "  secrets-sync            Sync secrets from Infisical (interactive)"
    echo "  secrets-update          Update encrypted Infisical credentials"
    echo ""
    echo -e "${GREEN}YouTube Automation:${NC}"
    echo "  youtube-test            Test YouTube automation with consent handling"
    echo "  youtube-run [channel]   Run YouTube automation with .env credentials"
    echo ""
    echo -e "${GREEN}System Commands:${NC}"
    echo "  shell                   Open interactive shell in container"
    echo "  test-chrome             Test Chrome setup in container" 
    echo "  check-env               Check container environment and dependencies"
    echo "  logs                    View container logs"
    echo "  clean                   Clean up containers and images"
    echo ""
    echo -e "${GREEN}Legacy Commands:${NC}"
    echo "  tailscale-check         Check Tailscale connectivity"
    echo "  system-check            Run system diagnostics"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./run.sh setup                                     # Complete setup"
    echo "  ./run.sh secrets-sync                              # Sync Infisical secrets"
    echo "  ./run.sh youtube-test                              # Test YouTube automation"
    echo "  ./run.sh youtube-run                               # Run YouTube automation"
    echo "  ./run.sh shell                                     # Debug/development"
    echo ""
    echo -e "${GREEN}Requirements:${NC}"
    echo "  - Docker Desktop installed and running"
    echo "  - Encrypted Infisical credentials (optional)"
    echo ""
    echo -e "${YELLOW}💡 First Time Setup:${NC} Run './run.sh setup' to build and configure everything"
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
    $COMPOSE_CMD logs -f automation
}

# Run system check
run_system_check() {
    print_info "Running system check..."
    
    detect_os
    
    if ! check_docker || ! check_docker_compose; then
        print_error "System check failed"
        return 1
    fi
    
    if ! set_environment; then
        print_error "Environment setup failed"
        return 1
    fi
    
            print_status "System check passed"
}

# Set up local Python environment
setup_local_environment() {
    local auto_sync=${1:-false}
    
    print_info "🐍 Setting up local Python environment..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_info "Found Python $PYTHON_VERSION"
    
    # Create virtual environment
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    print_info "Creating virtual environment..."
    python3 -m venv venv
    
    # Activate and install dependencies
    print_info "Installing core dependencies..."
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install cryptography python-dotenv
    
    # Try to install other dependencies but don't fail if they don't work
    print_info "Installing additional dependencies (best effort)..."
    if ./venv/bin/pip install -r requirements.txt 2>/dev/null; then
        print_status "All dependencies installed successfully"
    else
        print_warning "Some dependencies failed to install. Core functionality available."
        print_info "You can use: ./venv/bin/pip install <package> to install specific packages"
    fi
    
    print_status "🎉 Local environment setup completed!"
    
    # If auto_sync is true, automatically run secrets sync
    if [ "$auto_sync" = "true" ]; then
        echo ""
        print_info "🔐 Starting automatic secrets sync..."
        echo "This will decrypt your YubiKey-encrypted tokens and create .env file"
        echo ""
        
        # Check if encrypted tokens exist
        if [ ! -f "scripts/enc/encrypted_tokens.json" ]; then
            print_error "No encrypted tokens found at scripts/enc/encrypted_tokens.json"
            print_info "Please encrypt your tokens first:"
            echo "  source venv/bin/activate"
            echo "  python scripts/enc/yubikey_token_manager.py --encrypt"
            return 1
        fi
        
        # Run secrets sync with the new venv
        if ./venv/bin/python scripts/infisical/secrets-manager.py; then
            echo ""
            print_status "🎉 COMPLETE SUCCESS! Your environment is ready!"
            echo ""
            print_info "✅ Virtual environment created"
            print_info "✅ Dependencies installed"
            print_info "✅ Secrets synced from YubiKey"
            print_info "✅ .env file created"
            echo ""
            print_info "🚀 Ready to use! To activate:"
            echo "  source venv/bin/activate"
        else
            print_warning "Secrets sync failed, but environment is still available"
            return 1
        fi
    else
        echo ""
        print_info "To use the local environment:"
        echo "  source venv/bin/activate"
        echo "  scripts/infisical/setup-infisical.sh sync    # Set up secrets"
        echo "  python scripts/infisical/secrets-manager.py  # Direct secrets access"
        echo ""
        print_info "To deactivate later: deactivate"
    fi
}

# Complete setup with automatic secrets sync
setup_complete() {
    print_info "🚀 Starting complete environment setup..."
    echo "This will:"
    echo "  1. Create Python virtual environment"
    echo "  2. Install dependencies"
    echo "  3. Decrypt YubiKey tokens and sync secrets"
    echo "  4. Create .env file with all credentials"
    echo ""
    
    setup_local_environment true
}

# Main execution
main() {
    case "${1:-help}" in
        check)
            run_system_check
            ;;
        build)
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            set_environment
            build_image
            ;;
        setup)
            run_setup
            ;;
        local-setup)
            setup_local_environment
            ;;
        setup-complete)
            setup_complete
            ;;
        secrets-status|secrets-sync|secrets-update)
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            set_environment
            print_info "Running: $1"
            $COMPOSE_CMD run --rm automation "$1"
            ;;
        youtube-test|youtube-run)
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            set_environment
            shift
            if [ "$1" = "youtube-run" ] && [ -n "$2" ]; then
                print_info "Running YouTube automation for channel: $2"
                $COMPOSE_CMD run --rm automation youtube-run "$2"
            else
                print_info "Running: $1"
                $COMPOSE_CMD run --rm automation "${1:-youtube-test}"
            fi
            ;;
        shell|test-chrome|check-env|tailscale-check|system-check)
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            set_environment
            print_info "Running: $1"
            $COMPOSE_CMD run --rm automation "$1"
            ;;
        logs)
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            set_environment
            view_logs
            ;;
        clean)
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            set_environment
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