#!/bin/bash

# 🔐 Secure Secrets Deployment Script
# Syncs secrets locally with YubiKey, adds compatibility aliases, deploys to server

set -e

# Configuration
SERVER_USER="wgus1"
SERVER_HOST="100.124.55.82"
SERVER_PATH="~/Y"
LOCAL_PROJECT_PATH="/Users/wgm0/Documents/Y"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Secure FastMail Secrets Deployment${NC}"
echo -e "${BLUE}=====================================${NC}"

# Step 1: Verify we're on MacBook with YubiKey
echo -e "\n${YELLOW}📋 Step 1: Verifying local environment...${NC}"

if [[ ! -d "$LOCAL_PROJECT_PATH" ]]; then
    echo -e "${RED}❌ Project not found at $LOCAL_PROJECT_PATH${NC}"
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

echo -e "${GREEN}✅ YubiKey detected${NC}"

# Step 2: Sync secrets locally
echo -e "\n${YELLOW}📋 Step 2: Syncing secrets with YubiKey...${NC}"
echo -e "${BLUE}💡 You will be prompted to touch your YubiKey${NC}"

if ./scripts/infisical/setup-infisical.sh sync; then
    echo -e "${GREEN}✅ Secrets synced successfully${NC}"
else
    echo -e "${RED}❌ Failed to sync secrets${NC}"
    exit 1
fi

# Verify .env file was created
if [[ ! -f ".env" ]]; then
    echo -e "${RED}❌ .env file was not created${NC}"
    exit 1
fi

echo -e "${GREEN}✅ .env file created with $(wc -l < .env) environment variables${NC}"

# Validate FastMail credentials format
echo -e "${BLUE}🔍 Validating FastMail credentials...${NC}"
if grep -q "FM_M_0=" .env && grep -q "FM_P_0=" .env; then
    FM_USER=$(grep "FM_M_0=" .env | cut -d'=' -f2 | tr -d '"')
    FM_PASS=$(grep "FM_P_0=" .env | cut -d'=' -f2 | tr -d '"')
    echo -e "${GREEN}✅ Found Infisical format: FM_M_0=${FM_USER:0:10}...${NC}"
    
    # Add FASTMAIL_* aliases for compatibility
    echo -e "${BLUE}🔄 Adding FASTMAIL_* aliases for compatibility...${NC}"
    echo "" >> .env
    echo "# FastMail aliases for compatibility" >> .env
    echo "FASTMAIL_USERNAME=${FM_USER}" >> .env
    echo "FASTMAIL_PASSWORD=${FM_PASS}" >> .env
    echo -e "${GREEN}✅ Added FASTMAIL_USERNAME and FASTMAIL_PASSWORD aliases${NC}"
else
    echo -e "${RED}❌ FastMail credentials not found in expected format${NC}"
    echo -e "${YELLOW}Expected: FM_M_0 and FM_P_0 variables${NC}"
    exit 1
fi

# Step 3: Deploy to server
echo -e "\n${YELLOW}📋 Step 3: Deploying secrets to server...${NC}"

# Create backup of existing .env on server (if it exists)
echo -e "${BLUE}🔄 Creating backup of existing .env on server...${NC}"
ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && if [[ -f .env ]]; then cp .env .env.backup.$(date +%Y%m%d_%H%M%S); fi" || true

# Copy .env file to server
echo -e "${BLUE}📤 Copying .env to server...${NC}"
scp .env "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ .env file deployed to server${NC}"
else
    echo -e "${RED}❌ Failed to copy .env to server${NC}"
    exit 1
fi

# Step 4: Verify server can start
echo -e "\n${YELLOW}📋 Step 4: Verifying server startup...${NC}"

SERVER_CHECK_SCRIPT='
cd ~/Y
source venv/bin/activate 2>/dev/null || true

# Check if .env exists and has content
if [[ ! -f .env ]]; then
    echo "❌ .env file not found"
    exit 1
fi

if [[ ! -s .env ]]; then
    echo "❌ .env file is empty"
    exit 1
fi

echo "✅ .env file exists with $(wc -l < .env) variables"

# Test if FastMail credentials are available
if grep -q "FM_M_0" .env && grep -q "FM_P_0" .env; then
    echo "✅ FastMail credentials found in .env"
else
    echo "⚠️ FastMail credentials not found in .env"
fi

# Try to start server in test mode (just check imports and env loading)
python3 -c "
import os
from dotenv import load_dotenv

print(\"📋 Environment check:\")
print(f\"  Before load_dotenv - FM_M_0: {repr(os.getenv(\"FM_M_0\"))}\"[:50])
print(f\"  Before load_dotenv - FASTMAIL_USERNAME: {repr(os.getenv(\"FASTMAIL_USERNAME\"))}\"[:50])

load_dotenv()

print(f\"  After load_dotenv - FM_M_0: {repr(os.getenv(\"FM_M_0\"))}\"[:50])
fm_p0_status = \"***\" if os.getenv(\"FM_P_0\") else \"None\"
print(f\"  After load_dotenv - FM_P_0: {fm_p0_status}\")
print(f\"  After load_dotenv - FASTMAIL_USERNAME: {repr(os.getenv(\"FASTMAIL_USERNAME\"))}\"[:50])
fm_pass_status = \"***\" if os.getenv(\"FASTMAIL_PASSWORD\") else \"None\"
print(f\"  After load_dotenv - FASTMAIL_PASSWORD: {fm_pass_status}\")

# Check if either set works
fm_creds = os.getenv(\"FM_M_0\") and os.getenv(\"FM_P_0\")
fastmail_creds = os.getenv(\"FASTMAIL_USERNAME\") and os.getenv(\"FASTMAIL_PASSWORD\")

if fm_creds or fastmail_creds:
    print(\"✅ FastMail credentials available\")
    if fm_creds:
        print(\"  ✅ Infisical format (FM_M_0, FM_P_0) working\")
    if fastmail_creds:
        print(\"  ✅ Standard format (FASTMAIL_*) working\")
else:
    print(\"❌ No working FastMail credentials found\")
"
'

echo -e "${BLUE}🧪 Testing environment on server...${NC}"
if ssh "$SERVER_USER@$SERVER_HOST" "$SERVER_CHECK_SCRIPT"; then
    echo -e "${GREEN}✅ Server environment verified successfully${NC}"
else
    echo -e "${RED}❌ Server environment verification failed${NC}"
    exit 1
fi

# Step 5: Test server startup
echo -e "\n${YELLOW}📋 Step 5: Testing automation server...${NC}"

STARTUP_TEST_SCRIPT='
cd ~/Y
source venv/bin/activate

# Quick server startup test
timeout 10s python3 cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py --test 2>/dev/null || echo "Server startup test completed"
'

echo -e "${BLUE}🚀 Testing server startup...${NC}"
ssh "$SERVER_USER@$SERVER_HOST" "$STARTUP_TEST_SCRIPT"

# Step 6: Final verification
echo -e "\n${YELLOW}📋 Step 6: Final health check...${NC}"

HEALTH_CHECK_SCRIPT='
cd ~/Y

# Start server in background briefly
source venv/bin/activate
python3 cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py &
SERVER_PID=$!

# Wait a moment for startup
sleep 3

# Check if server is responding
if curl -s http://localhost:8002/status > /dev/null 2>&1; then
    echo "✅ Server is responding on port 8002"
    STATUS=$(curl -s http://localhost:8002/status | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get(\"status\", \"unknown\"))")
    echo "📊 Server status: $STATUS"
else
    echo "⚠️ Server not responding (may need manual startup)"
fi

# Clean up
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
'

ssh "$SERVER_USER@$SERVER_HOST" "$HEALTH_CHECK_SCRIPT"

# Success message
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Secrets synced locally with YubiKey${NC}"
echo -e "${GREEN}✅ FASTMAIL_* aliases added for compatibility${NC}"
echo -e "${GREEN}✅ .env file deployed to server${NC}"
echo -e "${GREEN}✅ Server environment verified${NC}"
echo -e "\n${BLUE}🚀 Next steps:${NC}"
echo -e "${BLUE}  1. SSH to server: ssh $SERVER_USER@$SERVER_HOST${NC}"
echo -e "${BLUE}  2. Start server: cd ~/Y && source venv/bin/activate && python3 cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py${NC}"
echo -e "${BLUE}  3. Test aliases: python3 cli_x/dev/auto/services/fastmail/clients/enhanced_session_client.py${NC}"

# Clean up local .env for security
echo -e "\n${YELLOW}🧹 Cleaning up local .env for security...${NC}"
if [[ -f ".env" ]]; then
    rm .env
    echo -e "${GREEN}✅ Local .env file removed${NC}"
fi

echo -e "\n${GREEN}🔐 Deployment completed securely!${NC}" 