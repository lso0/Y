#!/bin/bash

# Advanced Infisical Secrets Sync Script
# Supports multiple environments, custom output files, and automation options

set -e  # Exit on any error

# Default configuration
DEFAULT_PROJECT_NAME="Y"
DEFAULT_PROJECT_ID="13bce4c5-1ffc-478b-b1ce-76726074f358"  # Project Y ID
DEFAULT_ENV_FILE=".env"
DEFAULT_ENVIRONMENT="dev"

# Parse command line arguments
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
ENV_FILE="$DEFAULT_ENV_FILE"
PROJECT_NAME="$DEFAULT_PROJECT_NAME"
PROJECT_ID="$DEFAULT_PROJECT_ID"
FORCE_REINIT=false
QUIET=false
AUTO_SOURCE=false

# Help function
show_help() {
    cat << EOF
Infisical Secrets Sync Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --env ENVIRONMENT       Environment to sync (dev, staging, production, etc.)
                               Default: $DEFAULT_ENVIRONMENT
    -f, --file FILE            Output file for secrets
                               Default: $DEFAULT_ENV_FILE
    -p, --project PROJECT      Project name
                               Default: $DEFAULT_PROJECT_NAME
    -r, --reinit              Force re-initialization of project
    -q, --quiet               Quiet mode (minimal output)
    -s, --source              Automatically source the .env file after export
    -h, --help                Show this help message

EXAMPLES:
    $0                              # Sync dev environment to .env
    $0 -e production -f .env.prod   # Sync production to .env.prod
    $0 -e staging --source          # Sync staging and auto-source
    $0 --quiet --env production     # Quiet sync of production

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--file)
            ENV_FILE="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -r|--reinit)
            FORCE_REINIT=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -s|--source)
            AUTO_SOURCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    if [ "$QUIET" = false ]; then
        echo "$1"
    fi
}

log_error() {
    echo "❌ $1" >&2
}

log_success() {
    if [ "$QUIET" = false ]; then
        echo "✅ $1"
    fi
}

# Main script
log_info "🔐 Starting Infisical secrets sync..."
log_info "   Environment: $ENVIRONMENT"
log_info "   Output file: $ENV_FILE"
log_info "   Project: $PROJECT_NAME"

# Check if infisical CLI is installed
if ! command -v infisical &> /dev/null; then
    log_error "Infisical CLI is not installed. Please install it first."
    log_error "You can install it with: brew install infisical/infisical/infisical"
    exit 1
fi

# Check if user is logged in by testing export command with timeout
if ! timeout 3 infisical export --projectId="$PROJECT_ID" --env="$ENVIRONMENT" --format=dotenv --silent >/dev/null 2>&1; then
    log_error "You are not logged into Infisical."
    log_info "🔐 Automatically starting login process..."
    
    # Automatically trigger login
    if infisical login; then
        log_success "Login successful! Continuing with secrets sync..."
    else
        log_error "Login failed. Please check your credentials and try again."
        exit 1
    fi
fi

# Create backup of existing env file if it exists
if [ -f "$ENV_FILE" ] && [ "$QUIET" = false ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    log_info "📋 Created backup: ${ENV_FILE}.backup"
fi

# Export secrets to file using project ID directly (fully automated)
log_info "📤 Exporting secrets from environment: $ENVIRONMENT"
log_info "📋 Using project ID: $PROJECT_ID"
if infisical export --projectId="$PROJECT_ID" --env="$ENVIRONMENT" --format=dotenv > "$ENV_FILE"; then
    log_success "Secrets successfully exported to $ENV_FILE"
    
    # Show number of secrets exported (without revealing values)
    SECRET_COUNT=$(grep -c "^[^#]" "$ENV_FILE" 2>/dev/null || echo "0")
    log_info "📊 Exported $SECRET_COUNT secrets"
    
    # Set appropriate permissions on env file
    chmod 600 "$ENV_FILE"
    log_info "🔒 Set secure permissions on $ENV_FILE"
    
    # Auto-source if requested
    if [ "$AUTO_SOURCE" = true ]; then
        set -a  # automatically export all variables
        source "$ENV_FILE"
        set +a  # turn off automatic export
        log_success "Environment variables loaded into current shell"
    fi
    
else
    log_error "Failed to export secrets"
    exit 1
fi

if [ "$QUIET" = false ]; then
    echo "🎉 Secrets sync completed successfully!"
    echo ""
    echo "💡 To use the secrets in your current shell:"
    echo "   source $ENV_FILE"
    echo ""
    echo "💡 To run a command with secrets loaded:"
    echo "   infisical run --env=$ENVIRONMENT -- your-command"
    echo ""
    echo "💡 To automatically source next time:"
    echo "   $0 --env=$ENVIRONMENT --source"
fi
