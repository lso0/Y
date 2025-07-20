#!/bin/bash
# Deploy Persistent Automation Server to Ubuntu
# Ultra-fast alias creation with persistent session management

set -e

echo "🚀 Deploying Persistent Automation Server"
echo "⚡ Ultra-fast alias creation with persistent session"
echo "=" * 60

# Configuration
SERVER_USER="wgus1"
SERVER_IP="100.124.55.82"
PROJECT_DIR="/home/wgus1/Y/cli_x/dev/auto/a_1"
SERVICE_NAME="persistent-automation"

echo "📁 Copying files to server..."

# Copy the new server files
scp utils/persistent_session_manager.py ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}/utils/
scp utils/optimized_alias_creator.py ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}/utils/
scp servers/persistent_automation_server.py ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}/servers/
scp clients/persistent_client.py ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}/clients/

echo "✅ Files copied successfully!"

echo "🔧 Setting up server environment..."

# SSH to server and setup
ssh ${SERVER_USER}@${SERVER_IP} << 'EOF'
cd ~/Y/cli_x/dev/auto/a_1

# Install additional dependencies for persistent session
source venv/bin/activate
pip install fastapi uvicorn playwright requests

# Ensure Playwright is properly installed
python -m playwright install chromium
python -m playwright install-deps

# Create systemd service for persistent server
sudo tee /etc/systemd/system/persistent-automation.service > /dev/null << 'SYSTEMD_SERVICE'
[Unit]
Description=Persistent FastMail Automation Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=wgus1
Group=wgus1
WorkingDirectory=/home/wgus1/Y/cli_x/dev/auto/a_1
Environment=PATH=/home/wgus1/Y/cli_x/dev/auto/a_1/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PLAYWRIGHT_BROWSERS_PATH=/home/wgus1/.cache/ms-playwright
ExecStart=/home/wgus1/Y/cli_x/dev/auto/a_1/venv/bin/python servers/persistent_automation_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD_SERVICE

# Stop existing server if running
sudo systemctl stop fastmail-automation || true
sudo systemctl stop persistent-automation || true

# Enable and start the new persistent server
sudo systemctl daemon-reload
sudo systemctl enable persistent-automation
sudo systemctl start persistent-automation

echo "✅ Persistent Automation Server deployed!"
echo "📊 Service status:"
sudo systemctl status persistent-automation --no-pager -l

EOF

echo "🔍 Checking server health..."
sleep 10

# Test the server
echo "🧪 Testing server connectivity..."
if curl -s "http://${SERVER_IP}:8000/health" | grep -q "healthy"; then
    echo "✅ Server is responding!"
    
    echo "📊 Server status:"
    curl -s "http://${SERVER_IP}:8000/status" | python -m json.tool
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "=" * 60
    echo "🌐 Server URL: http://${SERVER_IP}:8000"
    echo "📚 API Docs: http://${SERVER_IP}:8000/docs"
    echo "📊 Status: http://${SERVER_IP}:8000/status"
    echo "⚡ Session Info: http://${SERVER_IP}:8000/session"
    echo "🔧 Performance: http://${SERVER_IP}:8000/performance-stats"
    echo ""
    echo "🛠️  Usage from MacBook:"
    echo "   python clients/persistent_client.py status"
    echo "   python clients/persistent_client.py create test@fastmail.com wg0@fastmail.com"
    echo "   python clients/persistent_client.py speedtest"
    echo "   python clients/persistent_client.py performance"
    echo ""
    echo "⚡ Features:"
    echo "   • Persistent browser session (no re-login)"
    echo "   • Ultra-fast alias creation (1-3 seconds)"
    echo "   • Background session monitoring"
    echo "   • Automatic session refresh"
    echo "   • Batch alias creation"
    echo "   • Performance monitoring"
    
else
    echo "❌ Server health check failed!"
    echo "📋 Checking logs..."
    ssh ${SERVER_USER}@${SERVER_IP} "sudo journalctl -u persistent-automation --no-pager -l --since '5 minutes ago'"
    exit 1
fi 