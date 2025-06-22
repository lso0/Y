#!/bin/bash

# Test script for Tailscale integration

echo "🧪 Testing Tailscale Integration"
echo "================================="

# Test 1: Check if Tailscale is installed
echo "1. Checking Tailscale installation..."
if command -v tailscale &> /dev/null; then
    echo "✅ Tailscale CLI is installed"
else
    echo "❌ Tailscale CLI is not installed"
    echo "Run ./setup.sh to install and configure Tailscale"
    exit 1
fi

# Test 2: Check if Tailscale is running
echo "2. Checking Tailscale status..."
if sudo tailscale status &> /dev/null; then
    echo "✅ Tailscale is running and authenticated"
    echo "📊 Status:"
    sudo tailscale status | head -5
else
    echo "❌ Tailscale is not running or not authenticated"
    echo "Run ./setup.sh to configure Tailscale"
    exit 1
fi

# Test 3: Check environment variables
echo "3. Checking environment variables..."
if [ -f ".env.tailscale" ]; then
    echo "✅ Tailscale environment file exists"
    source .env.tailscale
    echo "📋 Configuration:"
    echo "   IP: $TAILSCALE_IP"
    echo "   Enabled: $TAILSCALE_ENABLED"
    echo "   Hostname: $TAILSCALE_HOSTNAME"
else
    echo "❌ Tailscale environment file not found"
    echo "Run ./setup.sh to create configuration"
fi

# Test 4: Test Python integration
echo "4. Testing Python integration..."
cd RC
if python -c "from tailscale_utils import get_tailscale_client; client = get_tailscale_client(); print('✅ Python integration works')" 2>/dev/null; then
    echo "✅ Python integration is working"
    echo "📊 Network info:"
    python tailscale_utils.py ip
else
    echo "❌ Python integration failed"
    echo "Check that requirements are installed"
fi

# Test 5: Docker environment
echo "5. Checking Docker configuration..."
if grep -q "TAILSCALE_IP" docker-compose.yml; then
    echo "✅ Docker compose includes Tailscale environment variables"
else
    echo "❌ Docker compose missing Tailscale configuration"
fi

if grep -q "network_mode.*host" docker-compose.yml; then
    echo "✅ Docker compose uses host networking"
else
    echo "❌ Docker compose not configured for host networking"
fi

echo ""
echo "🎉 Tailscale integration test complete!"
echo "Run './setup.sh' to set up the complete environment" 