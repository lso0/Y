#!/bin/bash

# Data Folder Encryption Script
# Encrypts the cli_x/data folder using YubiKey + passphrase

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_FOLDER="$PROJECT_ROOT/cli_x/data"
ENCRYPTION_SCRIPT="$SCRIPT_DIR/enc/yubikey_token_manager.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔐 Data Folder Encryption Manager"
echo "================================="
echo ""

# Check if YubiKey manager exists
if [ ! -f "$ENCRYPTION_SCRIPT" ]; then
    echo -e "${RED}❌ YubiKey token manager not found at: $ENCRYPTION_SCRIPT${NC}"
    exit 1
fi

# Check if data folder exists
if [ ! -d "$DATA_FOLDER" ]; then
    echo -e "${RED}❌ Data folder not found at: $DATA_FOLDER${NC}"
    exit 1
fi

# Function to show data folder status
check_status() {
    echo -e "${BLUE}📊 Checking data folder encryption status...${NC}"
    python3 "$ENCRYPTION_SCRIPT" --check-data-status
    echo ""
}

# Function to encrypt data folder
encrypt_data() {
    echo -e "${YELLOW}⚠️  WARNING: This will encrypt your data folder!${NC}"
    echo "Data folder: $DATA_FOLDER"
    echo ""
    echo "The original folder will be backed up with '_unencrypted_backup' suffix."
    echo "You can delete the backup after verifying decryption works."
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}🔐 Starting encryption...${NC}"
        echo ""
        
        if python3 "$ENCRYPTION_SCRIPT" --encrypt-data "$DATA_FOLDER"; then
            echo ""
            echo -e "${GREEN}✅ Data folder encryption completed successfully!${NC}"
            echo ""
            echo "Next steps:"
            echo "1. Test decryption with: $0 --decrypt"
            echo "2. If decryption works, delete the backup folder:"
            echo "   rm -rf '${DATA_FOLDER}_unencrypted_backup'"
            echo "3. Add 'cli_x/data' to your .gitignore if not already there"
        else
            echo -e "${RED}❌ Encryption failed!${NC}"
            exit 1
        fi
    else
        echo "Operation cancelled."
        exit 0
    fi
}

# Function to decrypt data folder
decrypt_data() {
    echo -e "${BLUE}🔓 Starting decryption...${NC}"
    echo ""
    
    if python3 "$ENCRYPTION_SCRIPT" --decrypt-data; then
        echo ""
        echo -e "${GREEN}✅ Data folder decryption completed successfully!${NC}"
    else
        echo -e "${RED}❌ Decryption failed!${NC}"
        exit 1
    fi
}

# Function to decrypt to specific location
decrypt_data_to() {
    local target_path="$1"
    echo -e "${BLUE}🔓 Decrypting data folder to: $target_path${NC}"
    echo ""
    
    if python3 "$ENCRYPTION_SCRIPT" --decrypt-data-to "$target_path"; then
        echo ""
        echo -e "${GREEN}✅ Data folder decrypted to: $target_path${NC}"
    else
        echo -e "${RED}❌ Decryption failed!${NC}"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --status         Check encryption status of data folder"
    echo "  --encrypt        Encrypt the data folder"
    echo "  --decrypt        Decrypt and restore the data folder"
    echo "  --decrypt-to PATH Decrypt data folder to specific location"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --status                    # Check if data folder is encrypted"
    echo "  $0 --encrypt                   # Encrypt the data folder"
    echo "  $0 --decrypt                   # Decrypt and restore data folder"
    echo "  $0 --decrypt-to /tmp/data      # Decrypt to /tmp/data"
    echo ""
    echo "Security:"
    echo "  - Uses YubiKey challenge-response + passphrase"
    echo "  - AES-256-CBC encryption"
    echo "  - Creates encrypted archive stored in scripts/enc/encrypted_tokens.json"
}

# Parse arguments
case "${1:-}" in
    --status)
        check_status
        ;;
    --encrypt)
        check_status
        encrypt_data
        ;;
    --decrypt)
        check_status
        decrypt_data
        ;;
    --decrypt-to)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify target path for --decrypt-to${NC}"
            exit 1
        fi
        check_status
        decrypt_data_to "$2"
        ;;
    --help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac