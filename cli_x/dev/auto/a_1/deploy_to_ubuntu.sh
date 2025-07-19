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
pip install fastapi==0.104.1 uvicorn==0.24.0 playwright==1.42.0 pydantic==2.5.0 requests==2.31.0 python-multipart==0.0.6

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

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Copy automation_server.py to $PROJECT_DIR"
echo "2. Start the service: sudo systemctl start automation-server"
echo "3. Check status: sudo systemctl status automation-server"
echo "4. View logs: sudo journalctl -u automation-server -f"
echo "5. Test connection: curl http://localhost:8888/status"
echo ""
echo "📍 Project directory: $PROJECT_DIR"
echo "🌐 Server will run on: http://0.0.0.0:8888" 