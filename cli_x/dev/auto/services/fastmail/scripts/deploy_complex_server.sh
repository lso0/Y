#!/bin/bash
"""
Deploy Complex FastMail Automation Server
Organized deployment for the enhanced server setup
"""

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
UBUNTU_HOST="100.124.55.82"
UBUNTU_USER="wgus1"
TARGET_DIR="~/Y/cli_x/dev/auto/a_1"
SERVICE_NAME="fastmail-automation"

echo -e "${BLUE}🚀 FastMail Automation Server - Complex Setup Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "scripts/automated_alias_creation.py" ]]; then
    print_error "Must run from a_1 directory with scripts/ folder"
    exit 1
fi

print_info "Deploying organized complex server setup..."
print_info "Target: ${UBUNTU_USER}@${UBUNTU_HOST}:${TARGET_DIR}"
echo ""

# Step 1: Copy organized files to Ubuntu
print_info "📁 Copying organized files to Ubuntu..."

# Copy the entire organized structure
scp -r clients/ servers/ scripts/ utils/ "${UBUNTU_USER}@${UBUNTU_HOST}:${TARGET_DIR}/"

# Copy additional config files
scp server_requirements.txt "${UBUNTU_USER}@${UBUNTU_HOST}:${TARGET_DIR}/"

print_status "Files copied to Ubuntu server"
echo ""

# Step 2: Set up virtual environment and dependencies
print_info "🔧 Setting up virtual environment on Ubuntu..."

ssh "${UBUNTU_USER}@${UBUNTU_HOST}" "
cd ${TARGET_DIR}

# Create venv if it doesn't exist
if [[ ! -d venv ]]; then
    python3 -m venv venv
fi

# Activate and update pip
source venv/bin/activate
pip install --upgrade pip

# Install all dependencies
echo '📦 Installing FastAPI and dependencies...'
pip install fastapi uvicorn pydantic requests playwright

echo '📦 Installing Playwright browsers...'
playwright install chromium

echo '📦 Installing additional server dependencies...'
if [[ -f server_requirements.txt ]]; then
    pip install -r server_requirements.txt
fi

echo '✅ Dependencies installed successfully'
"

print_status "Virtual environment and dependencies set up"
echo ""

# Step 3: Create systemd service for the complex server
print_info "⚙️  Creating systemd service..."

ssh "${UBUNTU_USER}@${UBUNTU_HOST}" "
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=FastMail Automation Server (Complex Setup)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${UBUNTU_USER}
Group=${UBUNTU_USER}
WorkingDirectory=${TARGET_DIR}
Environment=PATH=${TARGET_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=${TARGET_DIR}
Environment=DISPLAY=:99
ExecStart=${TARGET_DIR}/venv/bin/python servers/fastmail_automation_server.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

echo '✅ Systemd service created and enabled'
"

print_status "Systemd service configured"
echo ""

# Step 4: Start the service
print_info "🚀 Starting the FastMail Automation Server..."

ssh "${UBUNTU_USER}@${UBUNTU_HOST}" "
# Stop any existing service
sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true

# Start the new service
sudo systemctl start ${SERVICE_NAME}

# Check status
sleep 3
sudo systemctl status ${SERVICE_NAME} --no-pager -l

echo ''
echo '📊 Service logs (last 10 lines):'
sudo journalctl -u ${SERVICE_NAME} -n 10 --no-pager
"

print_status "Server started"
echo ""

# Step 5: Test the deployment
print_info "🧪 Testing deployment..."

echo "Waiting for server to be ready..."
sleep 5

# Test from MacBook
print_info "Testing from MacBook client..."

if python clients/enhanced_client.py health; then
    print_status "Health check passed"
    
    if python clients/enhanced_client.py status; then
        print_status "Status check passed"
        
        if python clients/enhanced_client.py test; then
            print_status "Automation test passed"
            echo ""
            print_status "🎉 Complex server deployment successful!"
            print_info "You can now use: python clients/enhanced_client.py create <alias> <target>"
        else
            print_warning "Automation test failed"
        fi
    else
        print_warning "Status check failed"
    fi
else
    print_error "Health check failed"
    print_info "Check server logs with: ssh ${UBUNTU_USER}@${UBUNTU_HOST} 'sudo journalctl -u ${SERVICE_NAME} -f'"
fi

echo ""
print_info "📋 Available commands:"
echo "  • Start service: ssh ${UBUNTU_USER}@${UBUNTU_HOST} 'sudo systemctl start ${SERVICE_NAME}'"
echo "  • Stop service:  ssh ${UBUNTU_USER}@${UBUNTU_HOST} 'sudo systemctl stop ${SERVICE_NAME}'"
echo "  • View logs:     ssh ${UBUNTU_USER}@${UBUNTU_HOST} 'sudo journalctl -u ${SERVICE_NAME} -f'"
echo "  • Server status: python clients/enhanced_client.py status"
echo "  • Create alias:  python clients/enhanced_client.py create <alias> <target>"
echo ""
print_info "🌐 Server endpoints:"
echo "  • Main: http://${UBUNTU_HOST}:8000"
echo "  • Status: http://${UBUNTU_HOST}:8000/status"
echo "  • Docs: http://${UBUNTU_HOST}:8000/docs"
echo ""
print_status "🎉 Complex server deployment complete!" 