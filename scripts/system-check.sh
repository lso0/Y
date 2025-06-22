#!/bin/bash

# Comprehensive System Check for RC Automation
# This script verifies all prerequisites before running setup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}🔍 $1${NC}"
}

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

# Track overall success
OVERALL_SUCCESS=true

# Detect operating system with detailed information
detect_system() {
    print_header "System Information"
    
    case "$(uname -s)" in
        Linux*)     
            OS=Linux
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO="$NAME"
                VERSION="$VERSION_ID"
                ARCH=$(uname -m)
            else
                DISTRO="Unknown Linux"
                VERSION="Unknown"
                ARCH=$(uname -m)
            fi
            ;;
        Darwin*)    
            OS=Mac
            DISTRO="macOS"
            VERSION=$(sw_vers -productVersion)
            ARCH=$(uname -m)
            ;;
        CYGWIN*)    
            OS=Windows
            DISTRO="Windows (Cygwin)"
            VERSION=$(uname -r)
            ARCH=$(uname -m)
            ;;
        MINGW*)     
            OS=Windows
            DISTRO="Windows (MinGW/Git Bash)"
            VERSION=$(uname -r)
            ARCH=$(uname -m)
            ;;
        *)          
            OS=Unknown
            DISTRO="Unknown"
            VERSION="Unknown"
            ARCH=$(uname -m)
            ;;
    esac
    
    echo "  Operating System: $DISTRO $VERSION"
    echo "  Architecture: $ARCH"
    echo "  Kernel: $(uname -r)"
    echo "  Shell: $SHELL"
    echo ""
}

# Check basic system tools
check_basic_tools() {
    print_header "Basic System Tools"
    
    local tools=("curl" "git" "bash")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            local version=$($tool --version 2>/dev/null | head -n1 || echo "version unknown")
            print_status "$tool is available ($version)"
        else
            print_error "$tool is not installed"
            missing_tools+=("$tool")
            OVERALL_SUCCESS=false
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo ""
        print_info "Missing tools installation instructions:"
        case "$OS" in
            Linux)
                echo "  sudo apt update && sudo apt install ${missing_tools[*]}"
                echo "  # Or for Red Hat/CentOS: sudo yum install ${missing_tools[*]}"
                ;;
            Mac)
                echo "  # Install Xcode Command Line Tools first:"
                echo "  xcode-select --install"
                echo "  # Or use Homebrew: brew install ${missing_tools[*]}"
                ;;
            Windows)
                echo "  # Install Git for Windows (includes bash and curl):"
                echo "  https://git-scm.com/download/win"
                ;;
        esac
    fi
    echo ""
}

# Check Docker installation and status
check_docker() {
    print_header "Docker Installation"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        OVERALL_SUCCESS=false
        
        case "$OS" in
            Linux)
                print_info "Install Docker on Linux:"
                echo "  # Option 1 - Official script:"
                echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
                echo "  sudo sh get-docker.sh"
                echo "  sudo usermod -aG docker \$USER"
                echo ""
                echo "  # Option 2 - Package manager (Ubuntu/Debian):"
                echo "  sudo apt update"
                echo "  sudo apt install docker.io docker-compose-plugin"
                echo "  sudo systemctl enable --now docker"
                echo "  sudo usermod -aG docker \$USER"
                ;;
            Mac)
                print_info "Install Docker on macOS:"
                echo "  # Download Docker Desktop:"
                echo "  https://www.docker.com/products/docker-desktop"
                echo "  # Or use Homebrew:"
                echo "  brew install --cask docker"
                ;;
            Windows)
                print_info "Install Docker on Windows:"
                echo "  # Download Docker Desktop:"
                echo "  https://www.docker.com/products/docker-desktop"
                echo "  # Requires Windows 10/11 with WSL2"
                ;;
        esac
        return
    fi
    
    # Docker is installed, check version
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_status "Docker is installed (version: $DOCKER_VERSION)"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        OVERALL_SUCCESS=false
        
        case "$OS" in
            Linux)
                print_info "Start Docker on Linux:"
                echo "  sudo systemctl start docker"
                echo "  sudo systemctl enable docker  # (to start on boot)"
                ;;
            Mac|Windows)
                print_info "Start Docker Desktop from your applications menu"
                ;;
        esac
        return
    fi
    
    print_status "Docker daemon is running"
    
    # Test Docker functionality
    if docker run --rm hello-world &> /dev/null; then
        print_status "Docker is functioning correctly"
    else
        print_warning "Docker may have permission issues"
        if [ "$OS" = "Linux" ]; then
            print_info "Fix Docker permissions on Linux:"
            echo "  sudo usermod -aG docker \$USER"
            echo "  # Then log out and back in"
        fi
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_status "Docker Compose is available: docker-compose (v$COMPOSE_VERSION)"
    elif docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short)
        print_status "Docker Compose is available: docker compose (v$COMPOSE_VERSION)"
    else
        print_error "Docker Compose is not available"
        OVERALL_SUCCESS=false
        
        case "$OS" in
            Linux)
                print_info "Install Docker Compose on Linux:"
                echo "  sudo apt install docker-compose-plugin"
                echo "  # Or standalone installation:"
                echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
                echo "  sudo chmod +x /usr/local/bin/docker-compose"
                ;;
            Mac|Windows)
                print_info "Docker Compose should be included with Docker Desktop"
                print_info "Try updating Docker Desktop to the latest version"
                ;;
        esac
    fi
    echo ""
}

# Check disk space
check_disk_space() {
    print_header "Disk Space"
    
    local available_space
    case "$OS" in
        Linux|Mac)
            available_space=$(df -h . | awk 'NR==2 {print $4}')
            ;;
        Windows)
            available_space=$(df -h . | awk 'NR==2 {print $4}' 2>/dev/null || echo "Unknown")
            ;;
        *)
            available_space="Unknown"
            ;;
    esac
    
    echo "  Available space in current directory: $available_space"
    
    # Extract numeric value for comparison (rough estimate)
    local space_num=$(echo "$available_space" | sed 's/[^0-9.]//g')
    local space_unit=$(echo "$available_space" | sed 's/[0-9.]//g')
    
    if [[ "$space_unit" == *"G"* ]] && (( $(echo "$space_num >= 2" | bc -l 2>/dev/null || echo 0) )); then
        print_status "Sufficient disk space available"
    elif [[ "$space_unit" == *"T"* ]]; then
        print_status "Sufficient disk space available"
    else
        print_warning "Low disk space - recommend at least 2GB free"
        print_info "Docker images and containers can take significant space"
    fi
    echo ""
}

# Check network connectivity
check_network() {
    print_header "Network Connectivity"
    
    local test_urls=("docker.com" "github.com")
    local failed_connections=0
    
    for url in "${test_urls[@]}"; do
        if curl -s --connect-timeout 5 --max-time 10 "https://$url" &> /dev/null; then
            print_status "Connection to $url: OK"
        else
            print_error "Connection to $url: FAILED"
            ((failed_connections++))
        fi
    done
    
    if [ $failed_connections -eq 0 ]; then
        print_status "Network connectivity is good"
    else
        print_warning "Some network connections failed"
        print_info "This may affect Docker image downloads and setup"
        if [ $failed_connections -eq ${#test_urls[@]} ]; then
            OVERALL_SUCCESS=false
        fi
    fi
    echo ""
}

# Check environment setup
check_environment() {
    print_header "Environment Setup"
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        print_status ".env file exists"
        
        # Check for INFISICAL_TOKEN
        if grep -q "INFISICAL_TOKEN=" ".env" && ! grep -q "INFISICAL_TOKEN=your_" ".env"; then
            print_status "INFISICAL_TOKEN appears to be configured"
        else
            print_warning "INFISICAL_TOKEN may not be properly configured"
            print_info "Make sure to set your actual Infisical token in .env file"
        fi
    else
        print_info ".env file does not exist (will be created during setup)"
    fi
    
    # Check if this looks like the correct directory
    if [ -f "run.sh" ] && [ -f "docker-compose.yml" ]; then
        print_status "In correct project directory"
    else
        print_error "This doesn't appear to be the RC Automation project directory"
        print_info "Make sure you're in the correct directory before running setup"
        OVERALL_SUCCESS=false
    fi
    echo ""
}

# Main system check
main() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}🔧 RC Automation - System Prerequisites Check${NC}"
    echo -e "${PURPLE}================================================${NC}"
    echo ""
    
    detect_system
    check_basic_tools
    check_docker
    check_disk_space
    check_network
    check_environment
    
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}📋 System Check Summary${NC}"
    echo -e "${PURPLE}================================================${NC}"
    
    if [ "$OVERALL_SUCCESS" = true ]; then
        print_status "All system checks passed! 🎉"
        echo ""
        print_info "You can now run the setup:"
        echo "  ./run.sh setup"
    else
        print_error "Some system checks failed"
        echo ""
        print_warning "Please address the issues above before running setup"
        print_info "After fixing the issues, you can:"
        echo "  1. Run this check again: ./system-check.sh"
        echo "  2. Proceed with setup: ./run.sh setup"
    fi
    
    echo ""
    echo -e "${PURPLE}================================================${NC}"
}

# Check if bc is available for numeric comparisons
if ! command -v bc &> /dev/null; then
    # Fallback function for systems without bc
    bc() {
        echo "scale=2; $1" | awk -F'[>=<]' '{
            if (NF == 1) print $1
            else if ($1 >= $2) print 1
            else print 0
        }'
    }
fi

# Run the main function
main "$@" 