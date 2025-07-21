#!/bin/bash
# Infisical Setup & Sync Script - Streamlined Version
# Sets up the Infisical secrets management system and provides sync functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="/Users/wgm0/Documents/Y"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
INFISICAL_DIR="$SCRIPTS_DIR/infisical"
ENCRYPTED_TOKEN_FILE="$SCRIPTS_DIR/enc/encrypted_token.json"
ENV_FILE="$PROJECT_ROOT/.env"

show_usage() {
    echo -e "${BLUE}Infisical Setup & Sync - Streamlined Version${NC}"
    echo "Usage:"
    echo "  $0 setup                    # Initial setup and install dependencies"
    echo "  $0 sync                     # Interactive secrets sync"
    echo "  $0 sync <password>          # Non-interactive secrets sync"
    echo "  $0 status                   # Show current system status"
    echo "  $0 backup                   # Backup current .env file"
    echo "  $0 update-token             # Update encrypted Infisical credentials"
    echo "  $0 help                     # Show this help"
}

setup_infisical() {
    echo -e "${BLUE}🚀 Setting up Infisical Secrets Management...${NC}"
    echo "============================================="
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/.infisical.json" ]]; then
        echo -e "${RED}❌ Not in project root directory (missing .infisical.json)${NC}"
        echo "Please ensure you're running from the correct location"
        exit 1
    fi
    
    # Check if Infisical CLI is installed
    if ! command -v infisical &> /dev/null; then
        echo -e "${YELLOW}📦 Installing Infisical CLI...${NC}"
        
        # Install Infisical CLI for macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install infisical
            else
                echo -e "${RED}❌ Homebrew not found. Please install Homebrew first:${NC}"
                echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
        else
            echo -e "${RED}❌ This setup script is designed for macOS. Please install Infisical CLI manually:${NC}"
            echo "   https://infisical.com/docs/cli/overview"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Infisical CLI already installed${NC}"
    fi
    
    # Check Python dependencies
    echo -e "${YELLOW}🐍 Checking Python dependencies...${NC}"
    
    # Check if cryptography is installed
    if ! python3 -c "import cryptography" 2>/dev/null; then
        echo -e "${YELLOW}📦 Installing cryptography library...${NC}"
        pip3 install cryptography
    else
        echo -e "${GREEN}✅ cryptography library already installed${NC}"
    fi
    
    # Check if encrypted token file exists
    if [[ ! -f "$ENCRYPTED_TOKEN_FILE" ]]; then
        echo -e "${YELLOW}⚠️  Encrypted token file not found: $ENCRYPTED_TOKEN_FILE${NC}"
        echo "Please ensure you have moved the encrypted token file to the new location."
    else
        echo -e "${GREEN}✅ Encrypted token file found${NC}"
    fi
    
    # Make the secrets manager executable
    chmod +x "$INFISICAL_DIR/secrets-manager.py"
    
    echo ""
    echo -e "${GREEN}🎉 Infisical setup completed!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "1. Run secrets sync: $0 sync"
    echo "2. Check status: $0 status"
    echo "3. Run automation: python3 cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py"
}

show_status() {
    echo -e "${BLUE}📊 Infisical System Status${NC}"
    echo "=========================="
    
    # Use the Python script's status function
    cd "$PROJECT_ROOT"
    python3 scripts/infisical/secrets-manager.py --status
}

backup_env() {
    echo -e "${YELLOW}💾 Creating backup of .env file...${NC}"
    if [[ -f "$ENV_FILE" ]]; then
        backup_file="$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$ENV_FILE" "$backup_file"
        echo -e "${GREEN}✅ Backup created: $backup_file${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env file to backup${NC}"
    fi
}

sync_secrets() {
    local password="$1"
    
    echo -e "${BLUE}🔄 Infisical Secrets Sync${NC}"
    echo "========================="
    
    # Check prerequisites
    if [[ ! -f "$PROJECT_ROOT/.infisical.json" ]]; then
        echo -e "${RED}❌ Not in project root directory${NC}"
        exit 1
    fi
    
    if [[ ! -f "$INFISICAL_DIR/secrets-manager.py" ]]; then
        echo -e "${RED}❌ secrets-manager.py not found${NC}"
        echo "Please run: $0 setup"
        exit 1
    fi
    
    # Show pre-sync status
    echo -e "${YELLOW}📋 Pre-sync status:${NC}"
    if [[ -f "$ENV_FILE" ]]; then
        current_vars=$(grep -c "^[A-Z]" "$ENV_FILE" 2>/dev/null || echo "0")
        echo "  Current .env variables: $current_vars"
    else
        echo "  No .env file exists"
    fi
    
    echo ""
    
    # Run the secrets manager
    cd "$PROJECT_ROOT"
    if [[ -n "${password}" ]]; then
        echo -e "${BLUE}🔐 Running in non-interactive mode...${NC}"
        python3 scripts/infisical/secrets-manager.py "$password"
        sync_result=$?
    else
        echo -e "${BLUE}🔐 Running in interactive mode...${NC}"
        echo -e "${YELLOW}💡 You will be prompted for your decryption password${NC}"
        python3 scripts/infisical/secrets-manager.py
        sync_result=$?
    fi
    
    echo ""
    
    # Check sync result
    if [[ $sync_result -eq 0 ]]; then
        echo -e "${GREEN}🎉 Secrets sync completed successfully!${NC}"
        
        # Show post-sync status
        if [[ -f "$ENV_FILE" ]]; then
            new_vars=$(grep -c "^[A-Z]" "$ENV_FILE" 2>/dev/null || echo "0")
            echo -e "${YELLOW}📊 Post-sync status:${NC}"
            echo "  Total .env variables: $new_vars"
            
            # Show variable categories
            echo "  Variable categories:"
            for prefix in $(grep "^# [A-Z]" "$ENV_FILE" 2>/dev/null | sed 's/# \([A-Z]*\) Configuration/\1/' | sort -u); do
                count=$(grep -c "^${prefix}_" "$ENV_FILE" 2>/dev/null || echo "0")
                echo "    $prefix: $count variables"
            done
        fi
        
        echo ""
        echo -e "${BLUE}💡 Quick usage examples:${NC}"
        echo "  # Check secrets:"
        echo "  cat .env"
        echo ""
        echo "  # Run YouTube automation:"
        echo "  python3 cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py"
        
    else
        echo -e "${RED}❌ Secrets sync failed!${NC}"
        echo "Please check the error messages above and:"
        echo "1. Verify your decryption password"
        echo "2. Check Infisical authentication"
        echo "3. Ensure all prerequisites are met"
        echo ""
        echo "For help, run: $0 help"
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    setup)
        setup_infisical
        ;;
    sync)
        sync_secrets "$2"
        ;;
    status)
        show_status
        ;;
    backup)
        backup_env
        ;;
    update-token)
        echo -e "${BLUE}🔄 Updating encrypted Infisical credentials...${NC}"
        echo "============================================="
        if [[ ! -f "$ENCRYPTED_TOKEN_FILE" ]]; then
            echo -e "${YELLOW}⚠️  Encrypted token file not found: $ENCRYPTED_TOKEN_FILE${NC}"
            echo "Please ensure you have moved the encrypted token file to the new location."
            exit 1
        fi
        echo -e "${YELLOW}💡 You will be prompted to enter your current decryption password.${NC}"
        cd "$PROJECT_ROOT"
        python3 scripts/infisical/update-token.py
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac 