#!/bin/bash

# Automation Server Deployment Script for Ubuntu
# Usage: ./deploy_to_ubuntu.sh

echo "🚀 Deploying Automation Server to Ubuntu..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not present
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies for Playwright
echo "🌐 Installing browser dependencies..."
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libatspi2.0-0 \
    libxss1 \
    libasound2

# Create project directory
PROJECT_DIR="$HOME/automation_server"
echo "📁 Creating project directory: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install fastapi==0.104.1 uvicorn==0.24.0 playwright==1.42.0 pydantic==2.5.0 requests==2.31.0 python-multipart==0.0.6 python-dotenv

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

# Create systemd service file
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/automation-server.service > /dev/null <<EOF
[Unit]
Description=Automation Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python automation_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Enabling automation server service..."
sudo systemctl daemon-reload
sudo systemctl enable automation-server

# Auto-detect current directory and copy files
CURRENT_DIR=$(pwd)
echo "📁 Current directory: $CURRENT_DIR"

# Updated path detection for new structure
if [[ "$CURRENT_DIR" == *"/cli_x/dev/auto/services/fastmail"* ]] || [[ "$CURRENT_DIR" == *"/cli_x/dev/auto/shared/utils"* ]] || [[ -d "../../services/fastmail" ]]; then
    echo "✅ Detected enhanced automation files structure"
    
    # Copy enhanced automation files to project directory
    echo "📂 Copying enhanced automation files..."
    
    # Find the correct paths relative to current location
    if [[ "$CURRENT_DIR" == *"/shared/utils"* ]]; then
        # We're in shared/utils, so services/fastmail is at ../../services/fastmail
        FASTMAIL_DIR="../../services/fastmail"
    elif [[ "$CURRENT_DIR" == *"/services/fastmail"* ]]; then
        # We're already in fastmail directory
        FASTMAIL_DIR="."
    else
        # Try to find the fastmail directory
        FASTMAIL_DIR=$(find . -path "*/services/fastmail" -type d | head -1)
        if [[ -z "$FASTMAIL_DIR" ]]; then
            FASTMAIL_DIR="cli_x/dev/auto/services/fastmail"
        fi
    fi
    
    echo "📍 Using FastMail directory: $FASTMAIL_DIR"
    
    # Copy the enhanced automation server as the main server
    if [[ -f "$FASTMAIL_DIR/servers/enhanced_automation_server.py" ]]; then
        cp "$FASTMAIL_DIR/servers/enhanced_automation_server.py" $PROJECT_DIR/automation_server.py
        echo "✅ Copied enhanced_automation_server.py -> automation_server.py"
    else
        echo "❌ Enhanced automation server not found at: $FASTMAIL_DIR/servers/enhanced_automation_server.py"
    fi
    
    # Copy the automation creation script
    if [[ -f "$FASTMAIL_DIR/scripts/automated_alias_creation.py" ]]; then
        cp "$FASTMAIL_DIR/scripts/automated_alias_creation.py" $PROJECT_DIR/
        echo "✅ Copied automated_alias_creation.py"
    else
        echo "❌ Automated alias creation script not found at: $FASTMAIL_DIR/scripts/automated_alias_creation.py"
    fi
    
    # Copy additional automation scripts if they exist
    if [[ -f "$FASTMAIL_DIR/scripts/automated_alias_creation2.py" ]]; then
        cp "$FASTMAIL_DIR/scripts/automated_alias_creation2.py" $PROJECT_DIR/
        echo "✅ Copied automated_alias_creation2.py"
    fi
    
    # Copy enhanced session client
    if [[ -f "$FASTMAIL_DIR/clients/enhanced_session_client.py" ]]; then
        cp "$FASTMAIL_DIR/clients/enhanced_session_client.py" $PROJECT_DIR/
        echo "✅ Copied enhanced_session_client.py"
    fi
    
    echo "✅ Enhanced automation files copied successfully!"
else
    echo "⚠️  Not in automation directory, please copy files manually:"
    echo "   cp cli_x/dev/auto/services/fastmail/servers/enhanced_automation_server.py $PROJECT_DIR/automation_server.py"
    echo "   cp cli_x/dev/auto/services/fastmail/scripts/automated_alias_creation.py $PROJECT_DIR/"
    echo "   cp cli_x/dev/auto/services/fastmail/clients/enhanced_session_client.py $PROJECT_DIR/"
fi

# Start the automation service
echo "🚀 Starting automation server..."
sudo systemctl start automation-server

# Wait a moment for startup
sleep 3

# Check service status
echo "📊 Checking service status..."
if sudo systemctl is-active --quiet automation-server; then
    echo "✅ Automation server is running!"
    
    # Test the server
    echo "🧪 Testing server connection..."
    sleep 5  # Give server time to fully start
    
    if curl -s http://localhost:8002/status > /dev/null; then
        echo "✅ Server is responding on port 8002!"
        echo ""
        echo "🎉 DEPLOYMENT SUCCESSFUL!"
        echo "="*50
        echo "🌐 Server URL: http://$(hostname -I | awk '{print $1}'):8002"
        echo "📊 Status: curl http://localhost:8002/status"
        echo "📝 Logs: sudo journalctl -u automation-server -f"
        echo "🛠️  Restart: sudo systemctl restart automation-server"
        echo ""
        echo "🎮 Test from your MacBook:"
        echo "   python enhanced_session_client.py --server http://$(hostname -I | awk '{print $1}'):8002 status"
        echo ""
    else
        echo "⚠️  Server started but not responding yet. Check logs:"
        echo "   sudo journalctl -u automation-server -f"
    fi
else
    echo "❌ Service failed to start. Check logs:"
    echo "   sudo journalctl -u automation-server -n 50"
    echo "   sudo systemctl status automation-server"
fi

echo "✅ Deployment complete!"
echo ""
echo "📍 Project directory: $PROJECT_DIR"
echo "🌐 Server will run on: http://0.0.0.0:8002" 