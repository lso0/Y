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
    
    # Handle Tailscale configuration
    if [ -f "/app/.env.tailscale" ]; then
        print_info "Adding Tailscale configuration..."
        echo "" >> /app/.env.secrets
        echo "# Tailscale Configuration" >> /app/.env.secrets
        cat /app/.env.tailscale >> /app/.env.secrets
        print_status "Tailscale configuration added"
    fi
    
    # Copy final environment file to RC directory
    cp /app/.env.secrets /app/RC/.env
    
    print_status "Environment setup complete!"
}

# Function to run RC automation
run_rc_automation() {
    print_info "Running RC automation with arguments: $*"
    
    # Ensure environment is set up
    if [ ! -f "/app/RC/.env" ]; then
        print_warning "Environment not set up, running setup first..."
        setup_environment
    fi
    
    # Load environment variables
    set -a
    source /app/RC/.env
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
    echo -e "${GREEN}Examples:${NC}"
    echo "  docker-compose run --rm rc-automation setup"
    echo "  docker-compose run --rm rc-automation run"
    echo "  docker-compose run --rm rc-automation run --some-arg value"
    echo "  docker-compose run --rm rc-automation shell"
    echo ""
    echo -e "${GREEN}Environment Variables:${NC}"
    echo "  INFISICAL_TOKEN         Your Infisical authentication token"
    echo "  TAILSCALE_IP           Tailscale IP address (optional)"
    echo "  TAILSCALE_ENABLED      Enable Tailscale features (optional)"
    echo "  TAILSCALE_HOSTNAME     Tailscale hostname (optional)"
    echo ""
    echo -e "${YELLOW}Note:${NC} Make sure to set your INFISICAL_TOKEN in .env file"
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