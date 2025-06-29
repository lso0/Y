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

# Function to check if Infisical is authenticated
check_infisical_auth() {
    # Check if we have a real Infisical CLI
    if ! infisical --version 2>/dev/null | grep -q "infisical version"; then
        print_warning "Using fallback Infisical - skipping authentication check"
        return 0
    fi
    
    if [ -z "$INFISICAL_TOKEN" ]; then
        print_error "INFISICAL_TOKEN environment variable is not set"
        print_info "Please set your Infisical token in the .env file or docker-compose.yml"
        return 1
    fi
    
    # Test authentication by trying to fetch secrets
    if timeout 5 infisical export --projectId="13bce4c5-1ffc-478b-b1ce-76726074f358" --env="dev" --format=dotenv --silent >/dev/null 2>&1; then
        print_status "Infisical authentication verified"
        return 0
    else
        print_error "Infisical authentication failed"
        print_info "Please check your INFISICAL_TOKEN in the .env file"
        return 1
    fi
}

# Function to setup environment
setup_environment() {
    print_info "Setting up containerized environment..."
    
    # Check if we have a real Infisical CLI or fallback
    if infisical --version 2>/dev/null | grep -q "infisical version"; then
        print_info "Using real Infisical CLI..."
        # Check Infisical authentication
        if ! check_infisical_auth; then
            print_error "Cannot proceed without valid Infisical authentication"
            exit 1
        fi
        
        # Fetch secrets from Infisical
        print_info "Fetching secrets from Infisical..."
        if infisical export --projectId="13bce4c5-1ffc-478b-b1ce-76726074f358" --env="dev" --format=dotenv > /app/.env.secrets; then
            print_status "Secrets fetched successfully"
        else
            print_error "Failed to fetch secrets from Infisical"
            exit 1
        fi
    else
        print_warning "Using fallback Infisical - will use environment variables from .env"
        # Use fallback - create .env.secrets from current environment
        print_info "Creating environment file from current variables..."
        infisical export > /app/.env.secrets 2>/dev/null || {
            echo "# Environment variables from docker-compose" > /app/.env.secrets
            echo "RC_E_1=${RC_E_1:-}" >> /app/.env.secrets  
            echo "RC_P_1=${RC_P_1:-}" >> /app/.env.secrets
            echo "RC_E_2=${RC_E_2:-}" >> /app/.env.secrets
            echo "RC_P_2=${RC_P_2:-}" >> /app/.env.secrets
        }
        print_status "Environment file created from current variables"
    fi
    
    # Handle Tailscale configuration
    if [ -f "/app/.env.tailscale" ]; then
        print_info "Adding Tailscale configuration..."
        echo "" >> /app/.env.secrets
        echo "# Tailscale Configuration" >> /app/.env.secrets
        cat /app/.env.tailscale >> /app/.env.secrets
        print_status "Tailscale configuration added"
    fi
    
    # Copy final environment file to root directory (RC will access from there)
    cp /app/.env.secrets /app/.env
    
    print_status "Environment setup complete!"
}

# Function to run RC automation
run_rc_automation() {
    print_info "Running RC automation with arguments: $*"
    
    # Check for debug/verbose flags in arguments
    DEBUG_MODE=false
    for arg in "$@"; do
        if [[ "$arg" == "--debug" || "$arg" == "-d" || "$arg" == "--verbose" || "$arg" == "-v" ]]; then
            DEBUG_MODE=true
            break
        fi
    done
    
    # Set LOG_LEVEL environment variable if debug mode is enabled
    if [ "$DEBUG_MODE" = true ]; then
        export LOG_LEVEL=DEBUG
        print_info "🐛 Debug mode enabled - verbose HTTP logging will be shown"
    fi
    
    # Ensure environment is set up
    if [ ! -f "/app/.env" ]; then
        print_warning "Environment not set up, running setup first..."
        setup_environment
    fi
    
    # Load environment variables
    set -a
    source /app/.env
    set +a
    
    # Change to RC directory and run the automation
    cd /app/RC
    
    if [ $# -eq 0 ]; then
        print_info "Running RC automation with default parameters..."
        python rc_a.py
    else
        print_info "Running RC automation with arguments: $*"
        python rc_a.py "$@"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}🐳 Containerized RC Automation${NC}"
    echo ""
    echo "Usage: docker-compose run --rm rc-automation [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  setup                    Setup environment and fetch secrets"
    echo "  run [args...]           Run RC automation with optional arguments"
    echo "  shell                   Open interactive shell in container"
    echo "  help                    Show this help message"
    echo ""
    echo -e "${GREEN}RC Automation Arguments:${NC}"
    echo "  -a, --accounts A1 A2    Account identifiers (required)"
    echo "  -x, --action ACTION     Action: c_p (create), d_p (delete), l_p (list)"
    echo "  -p, --projects P1 P2    Project names (required for create/delete)"
    echo "  -d, --debug             Enable verbose debug logging"
    echo "  -v, --verbose           Enable verbose debug logging (same as --debug)"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  docker-compose run --rm rc-automation setup"
    echo "  docker-compose run --rm rc-automation run -a A1 A2 -x c_p -p proj1 proj2"
    echo "  docker-compose run --rm rc-automation run -a A1 -x c_p -p proj1 --debug"
    echo "  docker-compose run --rm rc-automation run -a A1 -x l_p"
    echo "  docker-compose run --rm rc-automation shell"
    echo ""
    echo -e "${GREEN}Environment Variables:${NC}"
    echo "  INFISICAL_TOKEN         Your Infisical authentication token"
    echo "  RC_E_1, RC_P_1          RevenueCat account 1 email and password"
    echo "  RC_E_2, RC_P_2          RevenueCat account 2 email and password"
    echo "  LOG_LEVEL               Set to DEBUG for verbose logging"
    echo "  TAILSCALE_IP           Tailscale IP address (optional)"
    echo "  TAILSCALE_ENABLED      Enable Tailscale features (optional)"
    echo "  TAILSCALE_HOSTNAME     Tailscale hostname (optional)"
    echo ""
    echo -e "${YELLOW}Debug Mode:${NC} Use --debug or --verbose for detailed HTTP logging"
    echo -e "${YELLOW}Note:${NC} Make sure to set your INFISICAL_TOKEN and RC_E_*/RC_P_* in .env file"
}

# Function to open interactive shell
open_shell() {
    print_info "Opening interactive shell..."
    exec /bin/bash
}

# Main execution logic
case "$1" in
    setup)
        setup_environment
        ;;
    run)
        shift
        run_rc_automation "$@"
        ;;
    shell)
        open_shell
        ;;
    help)
        show_help
        ;;
    *)
        if [ "$1" = "help" ] || [ -z "$1" ]; then
            show_help
        else
            print_warning "Unknown command: $1"
            show_help
            exit 1
        fi
        ;;
esac 