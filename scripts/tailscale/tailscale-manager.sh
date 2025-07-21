#!/bin/bash

# Unified Tailscale Manager
# Consolidates setup, checking, testing, and status functionality
# Replaces: tailscale-setup.sh, tailscale-check.sh, test-tailscale.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
SUCCESS="✅"
FAIL="❌"
INFO="ℹ️"
WARNING="⚠️"

# Global variables
TAILSCALE_INSTALLED=false
TAILSCALE_RUNNING=false
TAILSCALE_AUTHENTICATED=false

# Print functions
print_status() {
    local icon="$1"
    local message="$2"
    local color="$3"
    echo -e "${color}${icon} ${message}${NC}"
}

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}🔍 $1${NC}"
}

# Help function
show_help() {
    echo "🔗 Tailscale Manager - Unified Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup       Install and configure Tailscale"
    echo "  check       Comprehensive status and connectivity check"
    echo "  test        Run integration tests"
    echo "  status      Quick status overview"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # Install Tailscale and authenticate"
    echo "  $0 check     # Full system check"
    echo "  $0 status    # Quick status"
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)     
            OS_TYPE="linux"
            ;;
        Darwin*)    
            OS_TYPE="macos"
            ;;
        *)
            echo "❌ Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
}

# Install Tailscale on macOS
install_tailscale_macos() {
    echo "📦 Installing Tailscale on macOS..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        print_status "$FAIL" "Homebrew is required for macOS installation" "$RED"
        echo "Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    
    # Install Tailscale
    if brew list tailscale &> /dev/null; then
        print_status "$SUCCESS" "Tailscale is already installed via Homebrew" "$GREEN"
    else
        echo "Installing Tailscale via Homebrew..."
        brew install tailscale
        print_status "$SUCCESS" "Tailscale installed successfully" "$GREEN"
    fi
}

# Install Tailscale on Linux
install_tailscale_linux() {
    echo "📦 Installing Tailscale on Linux..."
    
    # Add Tailscale's GPG key and repository
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.gpg | sudo apt-key add -
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.list | sudo tee /etc/apt/sources.list.d/tailscale.list
    
    # Update package list and install
    sudo apt update
    sudo apt install -y tailscale
    print_status "$SUCCESS" "Tailscale installed successfully" "$GREEN"
}

# Check if Tailscale is installed
check_installation() {
    if command -v tailscale &> /dev/null; then
        TAILSCALE_VERSION=$(tailscale version 2>/dev/null | head -1 | awk '{print $2}' || echo "unknown")
        print_status "$SUCCESS" "Tailscale CLI is installed (version: $TAILSCALE_VERSION)" "$GREEN"
        TAILSCALE_INSTALLED=true
    else
        print_status "$FAIL" "Tailscale CLI is not installed" "$RED"
        echo -e "${INFO} Install with: $0 setup"
        TAILSCALE_INSTALLED=false
    fi
}

# Check service status
check_service() {
    if sudo tailscale status >/dev/null 2>&1; then
        print_status "$SUCCESS" "Tailscale service is running" "$GREEN"
        TAILSCALE_RUNNING=true
    else
        print_status "$FAIL" "Tailscale service is not running" "$RED"
        echo -e "${INFO} Start with: sudo tailscale up"
        TAILSCALE_RUNNING=false
    fi
}

# Check authentication
check_authentication() {
    if [ "$TAILSCALE_RUNNING" = true ]; then
        TAILSCALE_STATUS_OUTPUT=$(sudo tailscale status 2>/dev/null || echo "")
        
        if echo "$TAILSCALE_STATUS_OUTPUT" | grep -q "Logged out" || [ -z "$TAILSCALE_STATUS_OUTPUT" ]; then
            print_status "$FAIL" "Not authenticated with Tailscale" "$RED"
            echo -e "${INFO} Authenticate with: sudo tailscale up"
            TAILSCALE_AUTHENTICATED=false
        else
            print_status "$SUCCESS" "Authenticated with Tailscale" "$GREEN"
            TAILSCALE_AUTHENTICATED=true
            
            # Extract and display current user/account info
            CURRENT_USER=$(echo "$TAILSCALE_STATUS_OUTPUT" | head -1 | awk '{print $2}' | cut -d'@' -f1 2>/dev/null || echo "unknown")
            TAILNET=$(echo "$TAILSCALE_STATUS_OUTPUT" | head -1 | awk '{print $2}' | cut -d'@' -f2 2>/dev/null || echo "unknown")
            echo -e "${INFO} User: $CURRENT_USER"
            echo -e "${INFO} Tailnet: $TAILNET"
        fi
    else
        print_status "$WARNING" "Cannot check authentication - service not running" "$YELLOW"
        TAILSCALE_AUTHENTICATED=false
    fi
}

# Check network connectivity
check_network() {
    if [ "$TAILSCALE_AUTHENTICATED" = true ]; then
        # Get Tailscale IP
        TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
        if [ -n "$TAILSCALE_IP" ]; then
            print_status "$SUCCESS" "Tailscale IP address: $TAILSCALE_IP" "$GREEN"
        else
            print_status "$WARNING" "Could not retrieve Tailscale IP" "$YELLOW"
        fi
        
        # Display device list
        echo -e "${INFO} Connected devices:"
        sudo tailscale status | head -5
    else
        print_status "$WARNING" "Cannot check network - not authenticated" "$YELLOW"
    fi
}

# Setup Tailscale
tailscale_setup() {
    print_header "🔗 Tailscale Setup"
    
    detect_os
    echo -e "${INFO} Operating System: $OS_TYPE"
    echo ""
    
    # Install Tailscale based on OS
    if [[ "$OS_TYPE" == "macos" ]]; then
        install_tailscale_macos
    elif [[ "$OS_TYPE" == "linux" ]]; then
        install_tailscale_linux
    fi
    
    echo ""
    
    # Check if already running and authenticated
    if sudo tailscale status &> /dev/null; then
        print_status "$SUCCESS" "Tailscale is already running and authenticated" "$GREEN"
        echo "Current status:"
        sudo tailscale status
    else
        echo "🔐 Starting Tailscale authentication..."
        echo "This will open a browser window for authentication."
        echo "Please complete the authentication process in your browser."
        
        # Start Tailscale with authentication
        sudo tailscale up
        
        if [ $? -eq 0 ]; then
            print_status "$SUCCESS" "Tailscale authentication successful!" "$GREEN"
        else
            print_status "$FAIL" "Tailscale authentication failed" "$RED"
            exit 1
        fi
    fi
    
    # Display current status
    echo ""
    echo "📊 Current Tailscale status:"
    sudo tailscale status
    
    # Get and display Tailscale IP
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [ -n "$TAILSCALE_IP" ]; then
        echo ""
        echo "🌐 Your Tailscale IP address: $TAILSCALE_IP"
        
        # Create Tailscale environment file
        echo "📝 Creating Tailscale environment configuration..."
        cat > .env.tailscale << EOF
# Tailscale Configuration
TAILSCALE_IP=$TAILSCALE_IP
TAILSCALE_ENABLED=true
TAILSCALE_HOSTNAME=$(hostname)
EOF
        print_status "$SUCCESS" "Environment file created: .env.tailscale" "$GREEN"
    fi
    
    echo ""
    print_status "$SUCCESS" "Tailscale setup complete!" "$GREEN"
    echo ""
    echo "📋 Next steps:"
    echo "1. Your Tailscale network is now active"
    echo "2. Run '$0 check' to verify everything is working"
    echo "3. Visit Tailscale Admin Console: https://login.tailscale.com/admin/machines"
}

# Comprehensive check
tailscale_check() {
    print_header "🔍 Tailscale Comprehensive Check"
    
    # Step 1: Installation
    print_section "Step 1: Checking Installation"
    check_installation
    echo ""
    
    if [ "$TAILSCALE_INSTALLED" = false ]; then
        print_status "$FAIL" "Cannot proceed without Tailscale installation" "$RED"
        echo -e "${INFO} Run: $0 setup"
        exit 1
    fi
    
    # Step 2: Service Status
    print_section "Step 2: Checking Service Status"
    check_service
    echo ""
    
    # Step 3: Authentication
    print_section "Step 3: Checking Authentication"
    check_authentication
    echo ""
    
    # Step 4: Network Connectivity
    print_section "Step 4: Checking Network Connectivity"
    check_network
    echo ""
    
    # Step 5: Environment Configuration
    print_section "Step 5: Checking Environment Configuration"
    if [ -f ".env.tailscale" ]; then
        print_status "$SUCCESS" "Tailscale environment file exists" "$GREEN"
        source .env.tailscale 2>/dev/null || true
        echo -e "${INFO} Configuration:"
        echo "   IP: ${TAILSCALE_IP:-'Not set'}"
        echo "   Enabled: ${TAILSCALE_ENABLED:-'Not set'}"
        echo "   Hostname: ${TAILSCALE_HOSTNAME:-'Not set'}"
    else
        print_status "$WARNING" "Tailscale environment file not found" "$YELLOW"
        echo -e "${INFO} Run '$0 setup' to create configuration"
    fi
    echo ""
    
    # Summary
    print_section "Summary"
    if [ "$TAILSCALE_INSTALLED" = true ] && [ "$TAILSCALE_RUNNING" = true ] && [ "$TAILSCALE_AUTHENTICATED" = true ]; then
        print_status "$SUCCESS" "Tailscale is fully operational!" "$GREEN"
    else
        print_status "$WARNING" "Tailscale has issues that need attention" "$YELLOW"
        echo -e "${INFO} Run '$0 setup' to resolve issues"
    fi
}

# Quick status
tailscale_status() {
    print_header "🔗 Tailscale Quick Status"
    
    check_installation
    if [ "$TAILSCALE_INSTALLED" = true ]; then
        check_service
        if [ "$TAILSCALE_RUNNING" = true ]; then
            check_authentication
            if [ "$TAILSCALE_AUTHENTICATED" = true ]; then
                TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
                if [ -n "$TAILSCALE_IP" ]; then
                    echo -e "${INFO} IP: $TAILSCALE_IP"
                fi
                echo ""
                echo "📊 Active devices:"
                sudo tailscale status | head -3
            fi
        fi
    fi
    
    echo ""
    print_status "$INFO" "Run '$0 check' for detailed analysis" "$BLUE"
}

# Integration tests
tailscale_test() {
    print_header "🧪 Tailscale Integration Tests"
    
    # Test 1: Basic functionality
    print_section "Test 1: Basic Functionality"
    check_installation
    if [ "$TAILSCALE_INSTALLED" = false ]; then
        print_status "$FAIL" "Cannot run tests - Tailscale not installed" "$RED"
        exit 1
    fi
    
    check_service
    check_authentication
    echo ""
    
    # Test 2: Environment Configuration
    print_section "Test 2: Environment Configuration"
    if [ -f ".env.tailscale" ]; then
        print_status "$SUCCESS" "Environment file exists" "$GREEN"
        source .env.tailscale
        echo -e "${INFO} Configuration loaded successfully"
    else
        print_status "$FAIL" "Environment file missing" "$RED"
        echo -e "${INFO} Run '$0 setup' to create configuration"
    fi
    echo ""
    
    # Test 3: Python Integration (if available)
    print_section "Test 3: Python Integration"
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    if [ -f "$PROJECT_ROOT/RC/tailscale_utils.py" ]; then
        cd "$PROJECT_ROOT/RC"
        if python3 -c "from tailscale_utils import get_tailscale_client; client = get_tailscale_client(); print('Python integration works')" 2>/dev/null; then
            print_status "$SUCCESS" "Python integration is working" "$GREEN"
        else
            print_status "$WARNING" "Python integration has issues" "$YELLOW"
        fi
        cd - > /dev/null
    else
        print_status "$INFO" "Python integration not available" "$BLUE"
    fi
    echo ""
    
    # Test 4: Docker Configuration (if available)
    print_section "Test 4: Docker Configuration"
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        if grep -q "TAILSCALE_IP" "$PROJECT_ROOT/docker-compose.yml"; then
            print_status "$SUCCESS" "Docker compose includes Tailscale variables" "$GREEN"
        else
            print_status "$WARNING" "Docker compose missing Tailscale configuration" "$YELLOW"
        fi
        
        if grep -q "network_mode.*host" "$PROJECT_ROOT/docker-compose.yml"; then
            print_status "$SUCCESS" "Docker compose uses host networking" "$GREEN"
        else
            print_status "$INFO" "Docker compose not configured for host networking" "$BLUE"
        fi
    else
        print_status "$INFO" "Docker configuration not found" "$BLUE"
    fi
    echo ""
    
    # Test Summary
    print_section "Test Summary"
    if [ "$TAILSCALE_INSTALLED" = true ] && [ "$TAILSCALE_RUNNING" = true ] && [ "$TAILSCALE_AUTHENTICATED" = true ]; then
        print_status "$SUCCESS" "All core tests passed!" "$GREEN"
    else
        print_status "$WARNING" "Some tests failed - check configuration" "$YELLOW"
    fi
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            tailscale_setup
            ;;
        check)
            tailscale_check
            ;;
        test)
            tailscale_test
            ;;
        status)
            tailscale_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "❌ Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 