#!/bin/bash

# 🚀 Y Repository Setup Script
# For use with: curl wgms.uk -y | bash
# Automatically sets up the Y automation platform

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Y Automation Platform Setup${NC}"
echo -e "${BLUE}==============================${NC}"
echo -e "${BLUE}🎯 FastMail + YouTube + Docker Automation${NC}"
echo -e "${BLUE}🔐 YubiKey Secure Secrets Management${NC}"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    DISTRO="macOS"
else
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Detected: $DISTRO on $OS${NC}"

# Step 1: Clean up and clone
echo -e "\n${YELLOW}📋 Step 1: Setting up Y repository...${NC}"

cd ~
if [[ -d "Y" ]]; then
    echo -e "${YELLOW}🧹 Removing existing Y directory...${NC}"
    rm -rf Y
fi

echo -e "${BLUE}📥 Cloning Y repository...${NC}"

# Install GitHub CLI if needed
if ! command -v gh &> /dev/null; then
    echo -e "${BLUE}📦 Installing GitHub CLI...${NC}"
    
    if [[ "$OS" == "linux" ]]; then
        if command -v apt &> /dev/null; then
            type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh -y
        elif command -v yum &> /dev/null; then
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            sudo yum install gh -y
        fi
    elif [[ "$OS" == "macos" ]]; then
        if command -v brew &> /dev/null; then
            brew install gh
        else
            echo -e "${RED}❌ Please install Homebrew first: https://brew.sh${NC}"
            exit 1
        fi
    fi
fi

# Clone repository
gh repo clone lso0/Y
cd Y

# Step 2: Run setup
echo -e "\n${YELLOW}📋 Step 2: Running platform setup...${NC}"

chmod +x run.sh

if [[ "$OS" == "linux" ]]; then
    echo -e "${BLUE}🐧 Running Linux setup (with Docker support)...${NC}"
    ./run.sh setup-complete
elif [[ "$OS" == "macos" ]]; then
    echo -e "${BLUE}🍎 Running macOS setup (local development)...${NC}"
    ./run.sh local-setup
fi

# Step 3: Show next steps
echo -e "\n${GREEN}🎉 Y Platform Setup Complete!${NC}"
echo -e "${GREEN}=============================${NC}"

if [[ "$OS" == "linux" ]]; then
    echo -e "${GREEN}✅ Docker environment ready${NC}"
    echo -e "${GREEN}✅ Python virtual environment configured${NC}"
    echo -e "${GREEN}✅ All dependencies installed${NC}"
    echo -e "\n${YELLOW}📋 Next steps for Linux/Server:${NC}"
    echo -e "${BLUE}  1. 🔐 Sync secrets: ./run.sh secrets-sync${NC}"
    echo -e "${BLUE}  2. 🚀 Start services: ./run.sh start${NC}"
    echo -e "${BLUE}  3. 📊 Check status: ./run.sh status${NC}"
    echo -e "${BLUE}  4. 🌐 Test FastMail: python3 cli_x/dev/auto/services/fastmail/clients/enhanced_session_client.py${NC}"
elif [[ "$OS" == "macos" ]]; then
    echo -e "${GREEN}✅ Local development environment ready${NC}"
    echo -e "${GREEN}✅ Python virtual environment configured${NC}"
    echo -e "${GREEN}✅ YubiKey support installed${NC}"
    echo -e "\n${YELLOW}📋 Next steps for macOS:${NC}"
    echo -e "${BLUE}  1. 🔐 Sync secrets: ./scripts/infisical/setup-infisical.sh sync${NC}"
    echo -e "${BLUE}  2. 🚀 Deploy to server: ./scripts/remote-deploy.sh${NC}"
    echo -e "${BLUE}  3. 🧪 Local testing: ./run.sh test${NC}"
    echo -e "${BLUE}  4. 🌐 Local FastMail: source venv/bin/activate && python3 cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py${NC}"
fi

echo -e "\n${BLUE}📚 Available commands:${NC}"
echo -e "${BLUE}  ./run.sh help                    # Show all commands${NC}"
echo -e "${BLUE}  ./run.sh status                  # Check system status${NC}"
echo -e "${BLUE}  ./run.sh logs                    # View logs${NC}"

echo -e "\n${BLUE}🔗 Platform features:${NC}"
echo -e "${BLUE}  🔐 YubiKey secure secrets management${NC}"
echo -e "${BLUE}  📧 FastMail alias automation${NC}"
echo -e "${BLUE}  📺 YouTube automation tools${NC}"
echo -e "${BLUE}  🐳 Docker containerization${NC}"
echo -e "${BLUE}  🌐 FastAPI automation servers${NC}"

echo -e "\n${GREEN}🚀 Platform ready for automation workflows!${NC}"

# Platform-specific final messages
if [[ "$OS" == "linux" ]]; then
    echo -e "\n${YELLOW}💡 For server deployment, you can now:${NC}"
    echo -e "${BLUE}  - Run automation servers in Docker${NC}"
    echo -e "${BLUE}  - Create FastMail aliases remotely${NC}"
    echo -e "${BLUE}  - Use secure YubiKey token management${NC}"
elif [[ "$OS" == "macos" ]]; then
    echo -e "\n${YELLOW}💡 For development, you can now:${NC}"
    echo -e "${BLUE}  - Deploy to remote servers with one command${NC}"
    echo -e "${BLUE}  - Sync secrets securely with YubiKey${NC}"
    echo -e "${BLUE}  - Test automation locally before deployment${NC}"
fi

echo -e "\n${GREEN}🎯 Happy automating! 🚀${NC}" 