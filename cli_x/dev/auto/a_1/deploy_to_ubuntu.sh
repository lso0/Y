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

# Auto-detect current directory and copy files
CURRENT_DIR=$(pwd)
echo "📁 Current directory: $CURRENT_DIR"

if [[ "$CURRENT_DIR" == *"/cli_x/dev/auto/a_1" ]]; then
    echo "✅ Detected automation files in current directory"
    
    # Copy automation files to project directory
    echo "📂 Copying automation files..."
    cp automation_server.py $PROJECT_DIR/
    cp session_monitor.py $PROJECT_DIR/
    cp test_server.py $PROJECT_DIR/
    cp automation_client.py $PROJECT_DIR/
    cp server_requirements.txt $PROJECT_DIR/
    
    echo "✅ Files copied successfully!"
else
    echo "⚠️  Not in automation directory, please copy files manually:"
    echo "   cp automation_server.py $PROJECT_DIR/"
    echo "   cp session_monitor.py $PROJECT_DIR/"
    echo "   cp test_server.py $PROJECT_DIR/"
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
    
    if curl -s http://localhost:8888/status > /dev/null; then
        echo "✅ Server is responding on port 8888!"
        echo ""
        echo "🎉 DEPLOYMENT SUCCESSFUL!"
        echo "="*50
        echo "🌐 Server URL: http://$(hostname -I | awk '{print $1}'):8888"
        echo "📊 Status: curl http://localhost:8888/status"
        echo "📝 Logs: sudo journalctl -u automation-server -f"
        echo "🛠️  Restart: sudo systemctl restart automation-server"
        echo ""
        echo "🎮 Test from your MacBook:"
        echo "   python automation_client.py --server http://$(hostname -I | awk '{print $1}'):8888 status"
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
echo "🌐 Server will run on: http://0.0.0.0:8888" 