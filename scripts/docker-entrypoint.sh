#!/bin/bash

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

# Function to set up virtual display for headless Chrome
setup_virtual_display() {
    print_info "Setting up virtual display for headless Chrome..."
    
    # Start Xvfb if not running
    if ! pgrep -f Xvfb > /dev/null; then
        Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
        export DISPLAY=:99
        sleep 2
        print_status "Virtual display started on :99"
    else
        print_info "Virtual display already running"
    fi
}

# Function to check environment setup
check_environment() {
    print_info "Checking environment setup..."
    
    # Check if we're in a virtual environment
    if [[ -n "$VIRTUAL_ENV" ]] || [[ "$PATH" == *"/venv/bin:"* ]]; then
        print_status "Virtual environment active"
    else
        print_warning "Virtual environment not detected, activating..."
        export PATH="/app/venv/bin:$PATH"
    fi
    
    # Check Python environment
    python --version
    print_status "Python environment ready"
}

# Function to check Infisical setup
check_infisical_setup() {
    print_info "Checking Infisical setup..."
    
    # Check if Infisical CLI is available
    if ! command -v infisical &> /dev/null; then
        print_error "Infisical CLI not found"
        return 1
    fi
    
    # Check if encrypted token file exists
    if [ ! -f "/app/scripts/enc/encrypted_token.json" ]; then
        print_warning "Encrypted token file not found at /app/scripts/enc/encrypted_token.json"
        print_info "Secrets sync may not work without encrypted credentials"
        return 0
    fi
    
    print_status "Infisical setup ready"
    return 0
}

# Function to sync secrets if needed
sync_secrets_if_needed() {
    # Check if .env file exists and has content
    if [ ! -f "/app/.env" ] || [ ! -s "/app/.env" ]; then
        print_info "No .env file found, checking if we can sync secrets..."
        
        if [ -f "/app/scripts/enc/encrypted_token.json" ]; then
            print_info "Encrypted token found, but sync requires interactive password"
            print_info "Run: scripts/infisical/setup-infisical.sh sync"
        else
            print_warning "No encrypted token file found"
            print_info "Set up Infisical credentials first"
        fi
    else
        print_status ".env file exists"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}🚀 Streamlined Automation Container${NC}"
    echo ""
    echo "Available commands:"
    echo ""
    echo -e "${GREEN}Infisical & Secrets:${NC}"
    echo "  secrets-status           Show Infisical system status"
    echo "  secrets-sync             Sync secrets from Infisical (interactive)"
    echo "  secrets-update           Update encrypted Infisical credentials"
    echo ""
    echo -e "${GREEN}YouTube Automation:${NC}"
    echo "  youtube-test             Test YouTube automation with consent handling"
    echo "  youtube-run [channel]    Run YouTube automation (uses .env credentials)"
    echo ""
    echo -e "${GREEN}System Commands:${NC}"
    echo "  shell                    Open interactive shell"
    echo "  test-chrome              Test Chrome setup in container"
    echo "  check-env                Check environment and dependencies"
    echo ""
    echo -e "${GREEN}Legacy Commands:${NC}"
    echo "  tailscale-check          Check Tailscale connectivity"
    echo "  system-check             Run system diagnostics"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  docker-compose run --rm automation secrets-status"
    echo "  docker-compose run --rm automation youtube-test"
    echo "  docker-compose run --rm automation shell"
}

# Function to test Chrome setup
test_chrome_setup() {
    print_info "Testing Chrome setup in container..."
    
    setup_virtual_display
    
    # Check if Chrome is installed
    if ! command -v google-chrome &> /dev/null; then
        print_error "Google Chrome not found"
        return 1
    fi
    
    # Test Chrome startup
    if google-chrome --version > /dev/null 2>&1; then
        chrome_version=$(google-chrome --version)
        print_status "Chrome is working: $chrome_version"
    else
        print_error "Chrome failed to start"
        return 1
    fi
    
    # Test headless Chrome with a simple page
    print_info "Testing headless Chrome navigation..."
    if python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--headless')
options.binary_location = '/usr/bin/google-chrome'

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.google.com')
    title = driver.title
    driver.quit()
    print(f'✅ Successfully loaded: {title}')
except Exception as e:
    print(f'❌ Chrome test failed: {e}')
    exit(1)
"; then
        print_status "Chrome automation test passed"
    else
        print_error "Chrome automation test failed"
        return 1
    fi
}

# Main execution
main() {
    # Set up environment
    check_environment
    
    # Set up virtual display for GUI applications
    setup_virtual_display
    
    # Check Infisical setup
    check_infisical_setup
    
    case "${1:-help}" in
        help|--help|-h)
            show_help
            ;;
        shell)
            print_info "Starting interactive shell..."
            exec /bin/bash
            ;;
        secrets-status)
            print_info "Checking Infisical system status..."
            python3 /app/scripts/infisical/secrets-manager.py --status
            ;;
        secrets-sync)
            print_info "Starting interactive secrets sync..."
            /app/scripts/infisical/setup-infisical.sh sync
            ;;
        secrets-update)
            print_info "Starting encrypted token update..."
            python3 /app/scripts/infisical/update-token.py
            ;;
        youtube-test)
            print_info "Testing YouTube automation..."
            cd /app
            python3 cli_x/dev/auto/services/youtube/scripts/selenium_consent_fixed.py
            ;;
        youtube-run)
            print_info "Running YouTube automation..."
            cd /app
            if [ -n "$2" ]; then
                python3 cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py "$2"
            else
                python3 cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py
            fi
            ;;
        test-chrome)
            test_chrome_setup
            ;;
        check-env)
            print_info "Checking environment and dependencies..."
            check_environment
            check_infisical_setup
            if command -v google-chrome &> /dev/null; then
                print_status "Google Chrome: $(google-chrome --version)"
            else
                print_error "Google Chrome not found"
            fi
            python3 --version
            pip list | grep -E "(selenium|cryptography|nodriver)" || print_warning "Some automation packages not found"
            ;;
        tailscale-check)
            print_info "Running Tailscale connectivity check..."
            if [ -f "/app/scripts/tailscale/tailscale-check.sh" ]; then
                /app/scripts/tailscale/tailscale-check.sh
            else
                print_warning "Tailscale check script not found"
            fi
            ;;
        system-check)
            print_info "Running system diagnostics..."
            if [ -f "/app/scripts/system-check.sh" ]; then
                /app/scripts/system-check.sh
            else
                print_warning "System check script not found"
            fi
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 