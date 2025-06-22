#!/bin/bash

# Comprehensive Tailscale Status Checker
# Checks installation, authentication, VPN status, and connectivity

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Icons
SUCCESS="✅"
FAIL="❌"
INFO="ℹ️"
WARNING="⚠️"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🔗 Tailscale Comprehensive Status Check${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to print status with color
print_status() {
    local icon="$1"
    local message="$2"
    local color="$3"
    echo -e "${color}${icon} ${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Initialize status variables
tailscale_installed=false
tailscale_running=false
tailscale_authenticated=false
tailscale_connected=false
has_peers=false

# Check 1: Tailscale Installation
echo -e "${BLUE}🔍 Step 1: Checking Tailscale Installation${NC}"
if command_exists tailscale; then
    TAILSCALE_VERSION=$(tailscale version --short 2>/dev/null || echo "unknown")
    print_status "$SUCCESS" "Tailscale CLI is installed (version: $TAILSCALE_VERSION)" "$GREEN"
    tailscale_installed=true
else
    print_status "$FAIL" "Tailscale CLI is not installed" "$RED"
    echo -e "${INFO} Install Tailscale:"
    echo "  - Linux: curl -fsSL https://tailscale.com/install.sh | sh"
    echo "  - macOS: brew install tailscale"
    echo "  - Or run: ./tailscale/tailscale-setup.sh"
fi
echo ""

if [ "$tailscale_installed" = false ]; then
    echo -e "${RED}❌ Cannot proceed without Tailscale installation${NC}"
    exit 1
fi

# Check 2: Tailscale Service Status
echo -e "${BLUE}🔍 Step 2: Checking Tailscale Service Status${NC}"
if sudo tailscale status >/dev/null 2>&1; then
    print_status "$SUCCESS" "Tailscale service is running" "$GREEN"
    tailscale_running=true
else
    print_status "$FAIL" "Tailscale service is not running" "$RED"
    echo -e "${INFO} Start Tailscale with: sudo tailscale up"
fi
echo ""

# Check 3: Authentication Status
echo -e "${BLUE}🔍 Step 3: Checking Authentication Status${NC}"
if [ "$tailscale_running" = true ]; then
    TAILSCALE_STATUS_OUTPUT=$(sudo tailscale status 2>/dev/null || echo "")
    
    if echo "$TAILSCALE_STATUS_OUTPUT" | grep -q "Logged out" || [ -z "$TAILSCALE_STATUS_OUTPUT" ]; then
        print_status "$FAIL" "Not authenticated with Tailscale" "$RED"
        echo -e "${INFO} Authenticate with: sudo tailscale up"
    else
        print_status "$SUCCESS" "Authenticated with Tailscale" "$GREEN"
        tailscale_authenticated=true
        
        # Extract and display current user/account info
        CURRENT_USER=$(echo "$TAILSCALE_STATUS_OUTPUT" | head -1 | awk '{print $2}' | cut -d'@' -f1)
        TAILNET=$(echo "$TAILSCALE_STATUS_OUTPUT" | head -1 | awk '{print $2}' | cut -d'@' -f2)
        echo -e "${INFO} User: $CURRENT_USER"
        echo -e "${INFO} Tailnet: $TAILNET"
    fi
else
    print_status "$WARNING" "Cannot check authentication - service not running" "$YELLOW"
fi
echo ""

# Check 4: Network Connectivity & IP Address
echo -e "${BLUE}🔍 Step 4: Checking Network Connectivity${NC}"
if [ "$tailscale_authenticated" = true ]; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
    TAILSCALE_IP6=$(tailscale ip -6 2>/dev/null || echo "")
    
    if [ -n "$TAILSCALE_IP" ]; then
        print_status "$SUCCESS" "Tailscale IPv4: $TAILSCALE_IP" "$GREEN"
        tailscale_connected=true
    else
        print_status "$WARNING" "No Tailscale IPv4 address assigned" "$YELLOW"
    fi
    
    if [ -n "$TAILSCALE_IP6" ]; then
        print_status "$SUCCESS" "Tailscale IPv6: $TAILSCALE_IP6" "$GREEN"
    fi
    
    # Test connectivity to Tailscale coordination server
    if ping -c 1 -W 3 login.tailscale.com >/dev/null 2>&1; then
        print_status "$SUCCESS" "Can reach Tailscale coordination server" "$GREEN"
    else
        print_status "$WARNING" "Cannot reach Tailscale coordination server" "$YELLOW"
    fi
else
    print_status "$WARNING" "Cannot check connectivity - not authenticated" "$YELLOW"
fi
echo ""

# Check 5: Peer Information
echo -e "${BLUE}🔍 Step 5: Checking Peer Connectivity${NC}"
if [ "$tailscale_authenticated" = true ]; then
    PEER_COUNT=$(echo "$TAILSCALE_STATUS_OUTPUT" | tail -n +2 | wc -l)
    
    if [ "$PEER_COUNT" -gt 0 ]; then
        print_status "$SUCCESS" "Found $PEER_COUNT peer(s) in your tailnet" "$GREEN"
        has_peers=true
        
        echo -e "${INFO} Peer details:"
        echo "$TAILSCALE_STATUS_OUTPUT" | tail -n +2 | while read -r line; do
            if [ -n "$line" ]; then
                PEER_IP=$(echo "$line" | awk '{print $1}')
                PEER_NAME=$(echo "$line" | awk '{print $2}')
                PEER_STATUS=$(echo "$line" | awk '{print $NF}')
                
                if echo "$PEER_STATUS" | grep -q "active"; then
                    echo -e "  ${SUCCESS} $PEER_NAME ($PEER_IP) - Online"
                else
                    echo -e "  ${WARNING} $PEER_NAME ($PEER_IP) - Offline"
                fi
            fi
        done
    else
        print_status "$INFO" "No other peers found in your tailnet" "$BLUE"
    fi
else
    print_status "$WARNING" "Cannot check peers - not authenticated" "$YELLOW"
fi
echo ""

# Check 6: Environment Configuration
echo -e "${BLUE}🔍 Step 6: Checking Environment Configuration${NC}"
if [ -f ".env.tailscale" ]; then
    print_status "$SUCCESS" "Tailscale environment file exists" "$GREEN"
    source .env.tailscale
    echo -e "${INFO} Configuration:"
    echo "   TAILSCALE_IP: ${TAILSCALE_IP:-'not set'}"
    echo "   TAILSCALE_ENABLED: ${TAILSCALE_ENABLED:-'not set'}"
    echo "   TAILSCALE_HOSTNAME: ${TAILSCALE_HOSTNAME:-'not set'}"
else
    print_status "$WARNING" "Tailscale environment file (.env.tailscale) not found" "$YELLOW"
    echo -e "${INFO} Run ./tailscale/tailscale-setup.sh to create configuration"
fi
echo ""

# Check 7: Python Integration
echo -e "${BLUE}🔍 Step 7: Checking Python Integration${NC}"
if [ -f "RC/tailscale_utils.py" ]; then
    cd RC 2>/dev/null || true
    if python3 -c "from tailscale_utils import get_tailscale_client; client = get_tailscale_client(); print('Python integration works')" 2>/dev/null; then
        print_status "$SUCCESS" "Python Tailscale integration is working" "$GREEN"
        
        # Get network info via Python
        PYTHON_STATUS=$(python3 -c "
from tailscale_utils import get_tailscale_client
import json
client = get_tailscale_client()
info = client.get_network_info()
print(f'Enabled: {info[\"enabled\"]}')
print(f'IP: {info[\"ip\"]}')
print(f'Peers: {len(info[\"peers\"])}')
" 2>/dev/null || echo "Error getting Python status")
        
        if [ "$PYTHON_STATUS" != "Error getting Python status" ]; then
            echo -e "${INFO} Python client status:"
            echo "$PYTHON_STATUS" | sed 's/^/   /'
        fi
    else
        print_status "$WARNING" "Python Tailscale integration has issues" "$YELLOW"
        echo -e "${INFO} Check that requirements are installed: pip install -r RC/requirements.txt"
    fi
    cd - >/dev/null 2>&1 || true
else
    print_status "$WARNING" "Python Tailscale utilities not found" "$YELLOW"
fi
echo ""

# Check 8: VPN Traffic Test (if peers available)
if [ "$has_peers" = true ] && [ "$tailscale_connected" = true ]; then
    echo -e "${BLUE}🔍 Step 8: Testing VPN Traffic${NC}"
    
    # Get first online peer for testing
    FIRST_PEER=$(echo "$TAILSCALE_STATUS_OUTPUT" | tail -n +2 | head -1 | awk '{print $1}')
    
    if [ -n "$FIRST_PEER" ]; then
        echo -e "${INFO} Testing connectivity to peer: $FIRST_PEER"
        if ping -c 1 -W 3 "$FIRST_PEER" >/dev/null 2>&1; then
            PING_TIME=$(ping -c 1 -W 3 "$FIRST_PEER" 2>/dev/null | grep "time=" | sed 's/.*time=\([0-9.]*\).*/\1/')
            print_status "$SUCCESS" "VPN traffic working - ping to $FIRST_PEER: ${PING_TIME}ms" "$GREEN"
        else
            print_status "$WARNING" "Cannot ping peer $FIRST_PEER" "$YELLOW"
        fi
    fi
    echo ""
fi

# Final Summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}📋 Tailscale Status Summary${NC}"
echo -e "${BLUE}================================================${NC}"

if [ "$tailscale_installed" = true ]; then
    print_status "$SUCCESS" "Tailscale is installed" "$GREEN"
else
    print_status "$FAIL" "Tailscale is not installed" "$RED"
fi

if [ "$tailscale_running" = true ]; then
    print_status "$SUCCESS" "Tailscale service is running" "$GREEN"
else
    print_status "$FAIL" "Tailscale service is not running" "$RED"
fi

if [ "$tailscale_authenticated" = true ]; then
    print_status "$SUCCESS" "Authenticated with Tailscale" "$GREEN"
else
    print_status "$FAIL" "Not authenticated with Tailscale" "$RED"
fi

if [ "$tailscale_connected" = true ]; then
    print_status "$SUCCESS" "VPN connection is active" "$GREEN"
else
    print_status "$FAIL" "VPN connection is not active" "$RED"
fi

echo ""

# Exit with appropriate code
if [ "$tailscale_installed" = true ] && [ "$tailscale_running" = true ] && [ "$tailscale_authenticated" = true ] && [ "$tailscale_connected" = true ]; then
    echo -e "${GREEN}🎉 All Tailscale checks passed! Your VPN is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some Tailscale checks failed. See details above.${NC}"
    echo -e "${INFO} Quick setup: ./tailscale/tailscale-setup.sh"
    exit 1
fi 