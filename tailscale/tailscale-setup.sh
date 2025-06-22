#!/bin/bash

# Tailscale Setup Script
# This script installs and configures Tailscale for secure networking

set -e

echo "🔒 Starting Tailscale setup..."

# Detect OS
OS_TYPE=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
else
    echo "❌ Unsupported operating system: $OSTYPE"
    exit 1
fi

# Function to install Tailscale on macOS
install_tailscale_macos() {
    echo "📦 Installing Tailscale on macOS..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is required for macOS installation"
        echo "Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    
    # Install Tailscale
    if ! brew list tailscale &> /dev/null; then
        brew install tailscale
    else
        echo "✅ Tailscale already installed via Homebrew"
    fi
}

# Function to install Tailscale on Linux
install_tailscale_linux() {
    echo "📦 Installing Tailscale on Linux..."
    
    # Add Tailscale repository
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.noarmor.gpg | sudo apt-key add -
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.list | sudo tee /etc/apt/sources.list.d/tailscale.list
    
    # Update and install
    sudo apt update
    sudo apt install -y tailscale
}

# Install Tailscale based on OS
if [[ "$OS_TYPE" == "macos" ]]; then
    install_tailscale_macos
elif [[ "$OS_TYPE" == "linux" ]]; then
    install_tailscale_linux
fi

# Check if Tailscale is already running and authenticated
if sudo tailscale status &> /dev/null; then
    echo "✅ Tailscale is already running and authenticated"
    echo "Current status:"
    sudo tailscale status
else
    echo "🔐 Starting Tailscale authentication..."
    echo "This will open a browser window for authentication."
    echo "Please complete the authentication process in your browser."
    
    # Start Tailscale with authentication
    sudo tailscale up
    
    if [ $? -eq 0 ]; then
        echo "✅ Tailscale authentication successful!"
    else
        echo "❌ Tailscale authentication failed"
        exit 1
    fi
fi

# Display current Tailscale status
echo ""
echo "📊 Current Tailscale status:"
sudo tailscale status

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
echo ""
echo "🌐 Your Tailscale IP address: $TAILSCALE_IP"

# Create Tailscale environment file
echo "📝 Creating Tailscale environment configuration..."
cat > .env.tailscale << EOF
# Tailscale Configuration
TAILSCALE_IP=$TAILSCALE_IP
TAILSCALE_ENABLED=true
TAILSCALE_HOSTNAME=$(hostname)
EOF

echo "✅ Tailscale setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Your Tailscale network is now active"
echo "2. The .env.tailscale file contains your configuration"
echo "3. Run './setup.sh' to integrate with your existing setup"
echo ""
echo "🔗 Tailscale Admin Console: https://login.tailscale.com/admin/machines" 