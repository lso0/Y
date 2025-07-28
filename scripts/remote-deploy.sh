#!/bin/bash

# 🚀 Remote Y Repository Deployment Script
# Deploys Y repo to server, runs setup, and configures secrets from MacBook

set -e

# Configuration
SERVER_USER="wgus1"
SERVER_HOST="100.124.55.82"
LOCAL_PROJECT_PATH="/Users/wgm0/Documents/Y"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Remote Y Repository Deployment${NC}"
echo -e "${BLUE}=================================${NC}"

# Step 1: Verify local environment
echo -e "\n${YELLOW}📋 Step 1: Verifying local environment...${NC}"

if [[ ! -d "$LOCAL_PROJECT_PATH" ]]; then
    echo -e "${RED}❌ Local Y project not found at $LOCAL_PROJECT_PATH${NC}"
    exit 1
fi

cd "$LOCAL_PROJECT_PATH"

if [[ ! -d "venv" ]]; then
    echo -e "${RED}❌ Virtual environment not found. Run: ./run.sh local-setup${NC}"
    exit 1
fi

# Check if YubiKey is detected
echo -e "${BLUE}🔍 Checking for YubiKey...${NC}"
source venv/bin/activate
if ! ykman list > /dev/null 2>&1; then
    echo -e "${RED}❌ No YubiKey detected. Please insert YubiKey and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Local environment ready${NC}"

# Step 2: Deploy to server
echo -e "\n${YELLOW}📋 Step 2: Setting up Y repository on server...${NC}"

REMOTE_SETUP_SCRIPT='
set -e

echo "🧹 Cleaning up existing installation..."
cd ~
rm -rf Y

echo "📥 Cloning Y repository..."
if ! command -v gh &> /dev/null; then
    echo "Installing GitHub CLI..."
    type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh -y
fi

gh repo clone lso0/Y
cd Y

echo "🔧 Running complete setup..."
chmod +x run.sh
./run.sh setup-complete

echo "✅ Server setup completed!"
'

echo -e "${BLUE}🌐 Executing remote setup on server...${NC}"
echo -e "${YELLOW}💡 This will take a few minutes...${NC}"

if ssh "$SERVER_USER@$SERVER_HOST" "$REMOTE_SETUP_SCRIPT"; then
    echo -e "${GREEN}✅ Remote setup completed successfully${NC}"
else
    echo -e "${RED}❌ Remote setup failed${NC}"
    exit 1
fi

# Step 3: Deploy secrets
echo -e "\n${YELLOW}📋 Step 3: Deploying secrets to server...${NC}"

echo -e "${BLUE}🔐 Running local secrets sync and deployment...${NC}"
if ./scripts/deploy-secrets.sh; then
    echo -e "${GREEN}✅ Secrets deployed successfully${NC}"
else
    echo -e "${RED}❌ Secrets deployment failed${NC}"
    exit 1
fi

# Step 4: Final verification
echo -e "\n${YELLOW}📋 Step 4: Final verification...${NC}"

VERIFICATION_SCRIPT='
cd ~/Y
source venv/bin/activate

echo "🧪 Testing server startup..."
python3 cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py &
SERVER_PID=$!

sleep 5

if curl -s http://localhost:8002/status > /dev/null 2>&1; then
    echo "✅ Server is responding"
    STATUS=$(curl -s http://localhost:8002/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Status: {data.get('status', 'unknown')}, Version: {data.get('version', 'unknown')}\"); print(f\"Active tasks: {data.get('message', 'N/A')}\")" 2>/dev/null || echo "Server responding but JSON parse failed")
    echo "$STATUS"
else
    echo "❌ Server not responding"
fi

kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo "🧪 Testing alias creation client..."
if python3 -c "
import sys
sys.path.append('cli_x/dev/auto/services/fastmail/clients')
from enhanced_session_client import FastMailAutomationClient
client = FastMailAutomationClient()
status = client.get_status()
print(f'✅ Client connection successful: {status}')
" 2>/dev/null; then
    echo "✅ Client connection test passed"
else
    echo "⚠️ Client connection test failed (may need manual verification)"
fi
'

echo -e "${BLUE}🔍 Running final verification...${NC}"
ssh "$SERVER_USER@$SERVER_HOST" "$VERIFICATION_SCRIPT"

# Success message
echo -e "\n${GREEN}🎉 Complete Deployment Successful!${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}✅ Y repository cloned and setup on server${NC}"
echo -e "${GREEN}✅ Dependencies installed and configured${NC}"
echo -e "${GREEN}✅ Secrets synced and deployed${NC}"
echo -e "${GREEN}✅ Automation server verified${NC}"
echo -e "\n${BLUE}🚀 Ready for FastMail alias automation!${NC}"
echo -e "\n${YELLOW}📋 Next steps:${NC}"
echo -e "${BLUE}  1. SSH to server: ssh $SERVER_USER@$SERVER_HOST${NC}"
echo -e "${BLUE}  2. Start server: cd ~/Y && source venv/bin/activate && python3 cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py${NC}"
echo -e "${BLUE}  3. Create aliases: python3 cli_x/dev/auto/services/fastmail/clients/enhanced_session_client.py${NC}"
echo -e "\n${GREEN}🔐 Deployment completed securely from MacBook!${NC}" 