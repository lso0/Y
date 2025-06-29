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

# Detect operating system with more detailed information
detect_os() {
    case "$(uname -s)" in
        Linux*)     
            OS=Linux
            # Detect Linux distribution
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
        CYGWIN*)    
            OS=Windows
            DISTRO="Windows (Cygwin)"
            VERSION=$(uname -r)
            ;;
        MINGW*)     
            OS=Windows
            DISTRO="Windows (MinGW/Git Bash)"
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

# Provide OS-specific Docker installation instructions
provide_docker_installation_instructions() {
    case "$OS" in
        Linux)
            print_error "Docker is not installed on your Linux system ($DISTRO)"
            echo ""
            print_info "Installation options for Linux:"
            echo "  📋 Option 1 - Official Docker installation:"
            echo "     curl -fsSL https://get.docker.com -o get-docker.sh"
            echo "     sudo sh get-docker.sh"
            echo "     sudo usermod -aG docker \$USER"
            echo "     # Log out and back in for group changes to take effect"
            echo ""
            echo "  📋 Option 2 - Package manager (Ubuntu/Debian):"
            echo "     sudo apt update"
            echo "     sudo apt install docker.io docker-compose-plugin"
            echo "     sudo systemctl enable --now docker"
            echo "     sudo usermod -aG docker \$USER"
            echo ""
            echo "  📋 Option 3 - Docker Desktop for Linux:"
            echo "     Download from: https://docs.docker.com/desktop/install/linux-install/"
            ;;
        Mac)
            print_error "Docker is not installed on your macOS system"
            echo ""
            print_info "Installation options for macOS:"
            echo "  📋 Option 1 - Docker Desktop (Recommended):"
            echo "     Download from: https://www.docker.com/products/docker-desktop"
            echo ""
            echo "  📋 Option 2 - Homebrew:"
            echo "     brew install --cask docker"
            echo "     # Then start Docker Desktop from Applications"
            echo ""
            echo "  📋 Option 3 - Command line (if you have Homebrew):"
            echo "     brew install docker docker-compose"
            echo "     # Note: You'll need Docker Desktop or Colima for the Docker daemon"
            ;;
        Windows)
            print_error "Docker is not installed on your Windows system"
            echo ""
            print_info "Installation options for Windows:"
            echo "  📋 Option 1 - Docker Desktop (Recommended):"
            echo "     Download from: https://www.docker.com/products/docker-desktop"
            echo "     Requires Windows 10/11 with WSL2"
            echo ""
            echo "  📋 Option 2 - Using winget:"
            echo "     winget install Docker.DockerDesktop"
            echo ""
            echo "  💡 Note: After installation, ensure WSL2 is enabled:"
            echo "     wsl --install"
            echo "     wsl --set-default-version 2"
            ;;
        *)
            print_error "Docker is not installed on your system (Unknown OS)"
            print_info "Please visit: https://docs.docker.com/get-docker/"
            ;;
    esac
}

# Detect specific Linux distribution for better Docker installation
detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        LINUX_DISTRO_ID="$ID"
        LINUX_DISTRO_VERSION="$VERSION_ID"
        LINUX_DISTRO_CODENAME="${VERSION_CODENAME:-}"
    else
        LINUX_DISTRO_ID="unknown"
        LINUX_DISTRO_VERSION="unknown"
        LINUX_DISTRO_CODENAME="unknown"
    fi
}

# Auto-install Docker based on OS
auto_install_docker() {
    print_info "Attempting to auto-install Docker..."
    
    case "$OS" in
        Linux)
            detect_linux_distro
            
            # Try different installation methods based on distribution
            case "$LINUX_DISTRO_ID" in
                ubuntu|debian)
                    print_info "Installing Docker on $LINUX_DISTRO_ID using official script..."
                    if install_docker_official_script; then
                        return 0
                    else
                        print_warning "Official script failed, trying package manager..."
                        install_docker_package_manager
                        return $?
                    fi
                    ;;
                kali)
                    print_info "Installing Docker on Kali Linux using package manager..."
                    if install_docker_kali; then
                        return 0
                    else
                        print_warning "Package manager failed, trying manual approach..."
                        install_docker_manual_kali
                        return $?
                    fi
                    ;;
                fedora|centos|rhel)
                    print_info "Installing Docker on $LINUX_DISTRO_ID using package manager..."
                    install_docker_redhat
                    return $?
                    ;;
                arch)
                    print_info "Installing Docker on Arch Linux using pacman..."
                    install_docker_arch
                    return $?
                    ;;
                *)
                    print_info "Unknown Linux distribution, trying official script..."
                    if install_docker_official_script; then
                        return 0
                    else
                        print_warning "Official script failed, trying generic package manager..."
                        install_docker_generic
                        return $?
                    fi
                    ;;
            esac
            ;;
        Mac)
            print_warning "Auto-installation on macOS requires manual intervention"
            print_info "Please install Docker Desktop manually:"
            echo "1. Visit: https://www.docker.com/products/docker-desktop"
            echo "2. Download Docker Desktop for Mac"
            echo "3. Install and start Docker Desktop"
            echo "4. Run this setup script again"
            return 1
            ;;
        Windows)
            print_warning "Auto-installation on Windows requires manual intervention"
            print_info "Please install Docker Desktop manually:"
            echo "1. Visit: https://www.docker.com/products/docker-desktop"
            echo "2. Download Docker Desktop for Windows"
            echo "3. Ensure WSL2 is enabled"
            echo "4. Install and start Docker Desktop"
            echo "5. Run this setup script again"
            return 1
            ;;
        *)
            print_error "Unsupported OS for auto-installation"
            return 1
            ;;
    esac
}

# Install Docker using official script
install_docker_official_script() {
    if curl -fsSL https://get.docker.com -o get-docker.sh; then
        if sudo sh get-docker.sh; then
            post_install_docker_setup
            return 0
        else
            print_error "Failed to install Docker using official script"
            return 1
        fi
    else
        print_error "Failed to download Docker installation script"
        return 1
    fi
}

# Install Docker using package manager (Ubuntu/Debian)
install_docker_package_manager() {
    print_info "Installing Docker using package manager..."
    if sudo apt update && sudo apt install -y docker.io docker-compose-plugin; then
        post_install_docker_setup
        return 0
    else
        print_error "Failed to install Docker using package manager"
        return 1
    fi
}

# Install Docker on Kali Linux
install_docker_kali() {
    print_info "Installing Docker on Kali Linux..."
    if sudo apt update && sudo apt install -y docker.io docker-compose; then
        post_install_docker_setup
        return 0
    else
        print_error "Failed to install Docker using Kali package manager"
        return 1
    fi
}

# Manual Docker installation for Kali Linux
install_docker_manual_kali() {
    print_info "Attempting manual Docker installation for Kali Linux..."
    # Add Docker's official GPG key for Debian
    sudo apt update
    sudo apt install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository using Debian stable instead of Kali rolling
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt update
    if sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin; then
        post_install_docker_setup
        return 0
    else
        print_error "Manual Docker installation failed"
        return 1
    fi
}

# Install Docker on Red Hat based systems
install_docker_redhat() {
    print_info "Installing Docker on Red Hat based system..."
    if command -v dnf &> /dev/null; then
        sudo dnf install -y docker docker-compose
    elif command -v yum &> /dev/null; then
        sudo yum install -y docker docker-compose
    else
        print_error "No package manager found (dnf/yum)"
        return 1
    fi
    post_install_docker_setup
    return 0
}

# Install Docker on Arch Linux
install_docker_arch() {
    print_info "Installing Docker on Arch Linux..."
    if sudo pacman -S --noconfirm docker docker-compose; then
        post_install_docker_setup
        return 0
    else
        print_error "Failed to install Docker using pacman"
        return 1
    fi
}

# Generic Docker installation fallback
install_docker_generic() {
    print_info "Attempting generic Docker installation..."
    # Try common package managers
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y docker.io docker-compose
    elif command -v yum &> /dev/null; then
        sudo yum install -y docker docker-compose
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y docker docker-compose
    elif command -v zypper &> /dev/null; then
        sudo zypper install -y docker docker-compose
    else
        print_error "No supported package manager found"
        return 1
    fi
    post_install_docker_setup
    return 0
}

# Post-installation setup for Docker
post_install_docker_setup() {
    print_status "Docker installed successfully"
    print_info "Adding user to docker group..."
    sudo usermod -aG docker $USER
    print_info "Starting Docker service..."
    sudo systemctl enable docker
    sudo systemctl start docker
    print_status "Docker service started"
    print_warning "You may need to log out and back in for group changes to take effect"
}

# Enhanced Docker checking with auto-install option
check_docker() {
    detect_os
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed on your $DISTRO system"
        echo ""
        
        # Offer auto-installation for supported OS
        if [ "$OS" = "Linux" ]; then
            # Check for non-interactive mode or environment variable
            if [ "${AUTO_INSTALL_DOCKER:-}" = "true" ] || [ "${CI:-}" = "true" ]; then
                print_info "Non-interactive mode: Auto-installing Docker..."
                response="y"
            else
                echo -e "${YELLOW}Would you like to automatically install Docker? (y/N)${NC}"
                read -r response
            fi
            
            if [[ "$response" =~ ^[Yy]$ ]]; then
                if auto_install_docker; then
                    print_status "Docker auto-installation completed"
                    # Verify installation worked
                    if command -v docker &> /dev/null; then
                        print_status "Docker command is now available"
                    else
                        print_error "Docker installation completed but command not found"
                        print_warning "You may need to restart your terminal or log out and back in"
                        return 1
                    fi
                else
                    print_error "Auto-installation failed, falling back to manual instructions"
                    provide_docker_installation_instructions
                    echo ""
                    print_warning "After installing Docker, please:"
                    print_warning "1. Restart your terminal/shell"
                    print_warning "2. Make sure Docker service is running"
                    print_warning "3. Run this setup script again"
                    return 1
                fi
            else
                provide_docker_installation_instructions
                echo ""
                print_warning "After installing Docker, please:"
                print_warning "1. Restart your terminal/shell"
                print_warning "2. Make sure Docker service is running"
                print_warning "3. Run this setup script again"
                return 1
            fi
        else
            provide_docker_installation_instructions
            echo ""
            print_warning "After installing Docker, please:"
            print_warning "1. Restart your terminal/shell"
            print_warning "2. Make sure Docker service is running"
            print_warning "3. Run this setup script again"
            return 1
        fi
    fi
    
    # Check if Docker daemon is running
    # Try with sudo if regular docker command fails (user not in docker group)
    if ! docker info &> /dev/null && ! sudo docker info &> /dev/null; then
        print_error "Docker is installed but not running"
        echo ""
        
        # Try to start Docker automatically on Linux
        if [ "$OS" = "Linux" ]; then
            # Check for non-interactive mode or environment variable
            if [ "${AUTO_START_DOCKER:-}" = "true" ] || [ "${CI:-}" = "true" ]; then
                print_info "Non-interactive mode: Auto-starting Docker service..."
                response="y"
            else
                echo -e "${YELLOW}Would you like to try starting Docker automatically? (y/N)${NC}"
                read -r response
            fi
            
            if [[ "$response" =~ ^[Yy]$ ]]; then
                print_info "Attempting to start Docker service..."
                if sudo systemctl start docker; then
                    print_status "Docker service started successfully"
                    # Wait a moment for Docker to fully start
                    sleep 3
                    if docker info &> /dev/null || sudo docker info &> /dev/null; then
                        print_status "Docker daemon is now running"
                    else
                        print_warning "Docker service started but daemon not responding yet"
                        print_info "Please wait a moment and try again"
                        return 1
                    fi
                else
                    print_error "Failed to start Docker service"
                    return 1
                fi
            else
                case "$OS" in
                    Linux)
                        print_info "To start Docker on Linux:"
                        echo "  sudo systemctl start docker"
                        echo "  sudo systemctl enable docker  # (to start on boot)"
                        echo ""
                        print_info "Or if you're using Docker Desktop:"
                        echo "  Start Docker Desktop from your applications menu"
                        ;;
                    Mac)
                        print_info "To start Docker on macOS:"
                        echo "  Open Docker Desktop from Applications folder"
                        echo "  Or use Spotlight: Cmd+Space, type 'Docker'"
                        ;;
                    Windows)
                        print_info "To start Docker on Windows:"
                        echo "  Start Docker Desktop from the Start menu"
                        echo "  Or run: 'Docker Desktop' from Run dialog (Win+R)"
                        ;;
                esac
                return 1
            fi
        else
            case "$OS" in
                Mac)
                    print_info "To start Docker on macOS:"
                    echo "  Open Docker Desktop from Applications folder"
                    echo "  Or use Spotlight: Cmd+Space, type 'Docker'"
                    ;;
                Windows)
                    print_info "To start Docker on Windows:"
                    echo "  Start Docker Desktop from the Start menu"
                    echo "  Or run: 'Docker Desktop' from Run dialog (Win+R)"
                    ;;
            esac
            return 1
        fi
    fi
    
    # Check Docker version and provide info
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_status "Docker is available and running (version: $DOCKER_VERSION)"
    
    # Verify Docker is working with a simple test
    if docker run --rm hello-world &> /dev/null; then
        print_status "Docker is functioning correctly"
    else
        print_warning "Docker is running but may have permission issues"
        case "$OS" in
            Linux)
                echo "  Try: sudo usermod -aG docker \$USER"
                echo "  Then log out and back in"
                ;;
        esac
    fi
    
    return 0
}

# Enhanced Docker Compose checking
check_docker_compose() {
    # Check if user needs sudo for docker commands
    local use_sudo=""
    if ! docker info &> /dev/null && sudo docker info &> /dev/null; then
        use_sudo="sudo "
    fi
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="${use_sudo}docker-compose"
        COMPOSE_VERSION=$(${use_sudo}docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
    elif ${use_sudo}docker compose version &> /dev/null; then
        COMPOSE_CMD="${use_sudo}docker compose"
        COMPOSE_VERSION=$(${use_sudo}docker compose version --short)
    else
        print_error "Docker Compose is not available"
        echo ""
        case "$OS" in
            Linux)
                print_info "Install Docker Compose on Linux:"
                echo "  sudo apt install docker-compose-plugin  # (Ubuntu/Debian)"
                echo "  # Or install standalone:"
                echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
                echo "  sudo chmod +x /usr/local/bin/docker-compose"
                ;;
            Mac|Windows)
                print_info "Docker Compose should be included with Docker Desktop"
                print_info "Please update Docker Desktop to the latest version"
                ;;
        esac
        return 1
    fi
    
    print_status "Docker Compose is available: $COMPOSE_CMD (version: $COMPOSE_VERSION)"
    return 0
}

# Set environment variables based on OS
set_environment() {
    detect_os
    
    # Create .env file using Infisical if it doesn't exist
    if [ ! -f ".env" ]; then
        print_info ".env file not found, fetching secrets from Infisical..."
        
        # Check if infisical command is available
        if ! command -v infisical &> /dev/null; then
            print_error "Infisical CLI is not installed or not in PATH"
            print_info "Please install Infisical CLI first: https://infisical.com/docs/cli/overview"
            return 1
        fi
        
        # Check if .infisical.json exists for project configuration
        if [ ! -f ".infisical.json" ]; then
            print_error ".infisical.json file not found"
            print_info "Please ensure you're in the correct project directory"
            return 1
        fi
        
        # Export secrets to .env file using project ID and environment directly
        print_info "Exporting secrets from Infisical to .env file..."
        local project_id="13bce4c5-1ffc-478b-b1ce-76726074f358"
        local environment="dev"
        
        if ! infisical export --projectId="$project_id" --env="$environment" --format=dotenv-export > .env; then
            print_error "Failed to export secrets from Infisical"
            print_info "Please check your Infisical authentication and ensure you have access to:"
            print_info "  - Project ID: $project_id"
            print_info "  - Environment: $environment"
            print_info "You can also try running: infisical login"
            # Clean up partial .env file if it was created
            [ -f ".env" ] && rm .env
            return 1
        fi
        
        print_status ".env file created successfully from Infisical"
    else
        print_info ".env file already exists, skipping Infisical export"
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
    echo "  auto-setup              Complete setup from scratch (check + install + setup)"
    echo "  check                   Check system prerequisites"
    echo "  tailscale-check         Check Tailscale installation, status, and connectivity"
    echo "  install-docker          Auto-install Docker (Linux only)"
    echo "  setup                   Initial setup and build"
    echo "  run [args...]          Run RC automation"
    echo "  shell                  Open interactive shell"
    echo "  build                  Build Docker image"
    echo "  logs                   View container logs"
    echo "  clean                  Clean up containers and images"
    echo "  help                   Show this help"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  ./run.sh auto-setup                                    # Complete setup for new machines"
    echo "  ./run.sh check                                         # Check system prerequisites"
    echo "  ./run.sh tailscale-check                               # Check Tailscale VPN status"
    echo "  ./run.sh install-docker                                # Auto-install Docker (Linux)"
    echo "  ./run.sh setup                                         # First time setup"
    echo "  ./run.sh run -a A1 A2 -x c_p -p proj1 proj2           # Run automation"
    echo "  ./run.sh run -a A1 -x c_p -p proj1 --debug            # Run with verbose logging"
    echo "  ./run.sh shell                                         # Debug/development"
    echo "  ./run.sh logs                                          # View logs"
    echo ""
    echo -e "${GREEN}Requirements:${NC}"
    echo "  - Docker Desktop installed and running"
    echo "  - Infisical CLI installed and authenticated"
    echo ""
    echo -e "${YELLOW}OS Support:${NC} Linux, macOS, Windows (WSL/Git Bash)"
    echo ""
    echo -e "${YELLOW}💡 New Machine Setup:${NC} Run './run.sh auto-setup' for complete setup from scratch"
    echo -e "${YELLOW}💡 Manual Setup:${NC} Run './run.sh check' first to verify prerequisites individually"
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

# Run basic system check (non-blocking)
run_basic_system_check() {
    print_info "Running basic system check..."
    
    # Run the comprehensive system check but don't exit on failure
    if [ -f "./scripts/system-check.sh" ]; then
        if ./scripts/system-check.sh; then
            print_status "System check passed"
        else
            print_warning "System check found some issues, but continuing with setup"
            print_info "You can run './run.sh check' for detailed system information"
        fi
    fi
    echo ""
}

# Main execution
main() {
    # Commands that don't require Docker to be installed
    case "${1:-help}" in
        check|tailscale-check|help|--help|-h|install-docker|auto-setup)
            # Handle these commands without Docker prerequisites
            ;;
        *)
            # For setup command, run system check first
            if [ "${1:-}" = "setup" ]; then
                run_basic_system_check
            fi
            
            # Check prerequisites for commands that need Docker
            if ! check_docker || ! check_docker_compose; then
                exit 1
            fi
            
            # Set environment
            if ! set_environment; then
                exit 1
            fi
            ;;
    esac
    
    case "${1:-help}" in
        auto-setup)
            print_info "🚀 Starting complete auto-setup for new machine..."
            echo ""
            
            # Step 1: System Check
            print_info "Step 1/4: Running system prerequisites check..."
            if [ -f "./scripts/system-check.sh" ]; then
                if ./scripts/system-check.sh; then
                    print_status "System check completed"
                else
                    print_warning "System check found issues, but continuing..."
                fi
            else
                print_warning "scripts/system-check.sh not found, skipping detailed check"
            fi
            echo ""
            
            # Step 2: Auto-install Docker if needed
            print_info "Step 2/4: Checking Docker installation..."
            detect_os
            if ! command -v docker &> /dev/null; then
                if [ "$OS" = "Linux" ]; then
                    print_info "Docker not found. Auto-installing Docker..."
                    if [ "${AUTO_INSTALL_DOCKER:-}" = "true" ] || [ "${CI:-}" = "true" ]; then
                        print_info "Non-interactive mode: Installing Docker automatically..."
                        if auto_install_docker; then
                            print_status "Docker installation completed"
                        else
                            print_error "Docker auto-installation failed"
                            print_info "Please install Docker manually and run './run.sh setup' again"
                            exit 1
                        fi
                    else
                        echo -e "${YELLOW}Would you like to automatically install Docker? (y/N)${NC}"
                        read -r response
                        if [[ "$response" =~ ^[Yy]$ ]]; then
                            if auto_install_docker; then
                                print_status "Docker installation completed"
                            else
                                print_error "Docker auto-installation failed"
                                print_info "Please install Docker manually and run './run.sh setup' again"
                                exit 1
                            fi
                        else
                            print_info "Docker installation skipped"
                            print_info "Please install Docker manually:"
                            provide_docker_installation_instructions
                            exit 1
                        fi
                    fi
                else
                    print_warning "Auto-installation not available for $OS"
                    print_info "Please install Docker manually:"
                    provide_docker_installation_instructions
                    exit 1
                fi
            else
                print_status "Docker is already installed"
            fi
            echo ""
            
            # Step 3: Start Docker if needed
            print_info "Step 3/4: Ensuring Docker service is running..."
            if ! docker info &> /dev/null && ! sudo docker info &> /dev/null; then
                if [ "$OS" = "Linux" ]; then
                    if [ "${AUTO_START_DOCKER:-}" = "true" ] || [ "${CI:-}" = "true" ]; then
                        print_info "Non-interactive mode: Starting Docker service..."
                        if sudo systemctl start docker; then
                            print_status "Docker service started"
                            sleep 3  # Wait for Docker to fully start
                        else
                            print_error "Failed to start Docker service"
                            exit 1
                        fi
                    else
                        echo -e "${YELLOW}Docker is not running. Would you like to start it? (y/N)${NC}"
                        read -r response
                        if [[ "$response" =~ ^[Yy]$ ]]; then
                            if sudo systemctl start docker; then
                                print_status "Docker service started"
                                sleep 3  # Wait for Docker to fully start
                            else
                                print_error "Failed to start Docker service"
                                exit 1
                            fi
                        else
                            print_error "Docker must be running to continue"
                            exit 1
                        fi
                    fi
                else
                    print_error "Please start Docker Desktop and try again"
                    exit 1
                fi
            else
                print_status "Docker service is running"
            fi
            echo ""
            
            # Step 4: Run full setup
            print_info "Step 4/4: Running complete setup..."
            
            # Wait for Docker to be fully ready (especially after starting service)
            print_info "Waiting for Docker to be fully ready..."
            local retry_count=0
            local max_retries=10
            while [ $retry_count -lt $max_retries ]; do
                if docker info &> /dev/null || sudo docker info &> /dev/null; then
                    print_status "Docker is ready"
                    break
                fi
                print_info "Waiting for Docker daemon... (attempt $((retry_count + 1))/$max_retries)"
                sleep 2
                retry_count=$((retry_count + 1))
            done
            
            if [ $retry_count -eq $max_retries ]; then
                print_error "Docker daemon did not become ready in time"
                print_info "You may need to restart your terminal or log out/in for group changes"
                print_info "Then try running: ./run.sh setup"
                exit 1
            fi
            
            # Verify Docker and Compose are working
            if check_docker && check_docker_compose; then
                if set_environment; then
                    build_image
                    print_info "Running containerized setup..."
                    $COMPOSE_CMD run --rm rc-automation setup
                    print_status "🎉 Auto-setup completed successfully!"
                    echo ""
                    print_info "You can now run your automation with:"
                    echo "  ./run.sh run"
                else
                    print_error "Environment setup failed"
                    exit 1
                fi
            else
                print_error "Docker setup verification failed"
                print_info "This may be due to permission issues. Try:"
                print_info "1. Log out and back in (for group changes to take effect)"
                print_info "2. Or restart your terminal"
                print_info "3. Then run: ./run.sh setup"
                exit 1
            fi
            ;;
        check)
            print_info "Running system prerequisites check..."
            if [ -f "./scripts/system-check.sh" ]; then
                ./scripts/system-check.sh
            else
                print_error "scripts/system-check.sh not found"
                print_info "Please ensure you're in the correct project directory"
                exit 1
            fi
            ;;
        tailscale-check)
            print_info "Running Tailscale comprehensive status check..."
            if [ -f "./scripts/tailscale-check.sh" ]; then
                ./scripts/tailscale-check.sh
            else
                print_error "scripts/tailscale-check.sh not found"
                print_info "Please ensure you're in the correct project directory"
                print_info "Or run the existing Tailscale test with: ./tailscale/test-tailscale.sh"
                exit 1
            fi
            ;;
        install-docker)
            print_info "Auto-installing Docker..."
            detect_os
            if [ "$OS" != "Linux" ]; then
                print_error "Auto-installation is only supported on Linux"
                print_info "For $OS systems, please install Docker manually:"
                provide_docker_installation_instructions
                exit 1
            fi
            
            if command -v docker &> /dev/null; then
                print_warning "Docker is already installed"
                DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
                print_info "Current version: $DOCKER_VERSION"
                exit 0
            fi
            
            if auto_install_docker; then
                print_status "Docker installation completed successfully!"
                print_info "You can now run: ./run.sh setup"
            else
                print_error "Docker installation failed"
                print_info "Please try manual installation or run: ./run.sh check"
                exit 1
            fi
            ;;
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