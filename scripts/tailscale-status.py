#!/usr/bin/env python3
"""
Tailscale Status Checker - Python version
Uses the existing tailscale_utils.py library to provide detailed status information
"""

import sys
import os
import json
from datetime import datetime

# Add RC directory to path to import tailscale_utils
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'RC'))

try:
    from tailscale_utils import get_tailscale_client, ensure_tailscale_connectivity
except ImportError as e:
    print(f"❌ Could not import tailscale_utils: {e}")
    print("ℹ️  Please ensure you're in the correct project directory")
    print("ℹ️  And that RC/tailscale_utils.py exists")
    sys.exit(1)

def print_status(icon, message, level="info"):
    """Print status with appropriate formatting"""
    colors = {
        "success": "\033[0;32m",  # Green
        "error": "\033[0;31m",    # Red
        "warning": "\033[1;33m",  # Yellow
        "info": "\033[0;34m",     # Blue
        "reset": "\033[0m"        # Reset
    }
    
    color = colors.get(level, colors["info"])
    print(f"{color}{icon} {message}{colors['reset']}")

def format_json_output(data, indent=2):
    """Format JSON data for pretty printing"""
    return json.dumps(data, indent=indent, default=str)

def check_tailscale_detailed():
    """Perform detailed Tailscale status check"""
    print("🔗 Tailscale Python Status Check")
    print("=" * 50)
    print()
    
    try:
        # Initialize client
        client = get_tailscale_client()
        
        # Get comprehensive network info
        print("📊 Getting network information...")
        network_info = client.get_network_info()
        
        # Check basic status
        print("🔍 Basic Status:")
        if network_info.get('enabled'):
            print_status("✅", "Tailscale is enabled", "success")
        else:
            print_status("❌", "Tailscale is not enabled", "error")
        
        # Check IP address
        tailscale_ip = network_info.get('ip')
        if tailscale_ip:
            print_status("✅", f"Tailscale IP: {tailscale_ip}", "success")
        else:
            print_status("❌", "No Tailscale IP address assigned", "error")
        
        # Check hostname
        hostname = network_info.get('hostname')
        if hostname:
            print_status("ℹ️", f"Hostname: {hostname}", "info")
        
        print()
        
        # Check peers
        peers = network_info.get('peers', [])
        print(f"👥 Peers: {len(peers)} found")
        
        if peers:
            print("📋 Peer Details:")
            for i, peer in enumerate(peers, 1):
                peer_ips = peer.get('TailscaleIPs', [])
                peer_name = peer.get('HostName', 'Unknown')
                peer_online = peer.get('Online', False)
                
                status_icon = "🟢" if peer_online else "🔴"
                status_text = "Online" if peer_online else "Offline"
                
                print(f"  {i}. {status_icon} {peer_name}")
                if peer_ips:
                    print(f"     IP: {', '.join(peer_ips)}")
                print(f"     Status: {status_text}")
                
                # Show additional peer info if available
                if peer.get('OS'):
                    print(f"     OS: {peer['OS']}")
                if peer.get('HostInfo', {}).get('OS'):
                    print(f"     System: {peer['HostInfo']['OS']}")
        else:
            print_status("ℹ️", "No peers found in your tailnet", "info")
        
        print()
        
        # Check connectivity
        connectivity = network_info.get('connectivity', {})
        if connectivity:
            print("🌐 Connectivity Tests:")
            for peer_ip, conn_info in connectivity.items():
                peer_name = conn_info.get('hostname', peer_ip)
                is_online = conn_info.get('online', False)
                ping_time = conn_info.get('ping_ms', 0)
                
                if is_online:
                    print_status("✅", f"{peer_name} ({peer_ip}): {ping_time:.1f}ms", "success")
                else:
                    print_status("❌", f"{peer_name} ({peer_ip}): Not reachable", "error")
        
        print()
        
        # Environment variables check
        print("🔧 Environment Configuration:")
        env_vars = {
            'TAILSCALE_IP': os.getenv('TAILSCALE_IP'),
            'TAILSCALE_ENABLED': os.getenv('TAILSCALE_ENABLED'),
            'TAILSCALE_HOSTNAME': os.getenv('TAILSCALE_HOSTNAME')
        }
        
        for var_name, var_value in env_vars.items():
            if var_value:
                print_status("✅", f"{var_name}={var_value}", "success")
            else:
                print_status("⚠️", f"{var_name} not set", "warning")
        
        print()
        
        # Overall status summary
        print("📋 Summary:")
        issues = []
        
        if not network_info.get('enabled'):
            issues.append("Tailscale not enabled")
        
        if not tailscale_ip:
            issues.append("No IP address assigned")
        
        if not peers:
            issues.append("No peers found")
        
        offline_peers = [p for p in peers if not p.get('Online', False)]
        if offline_peers:
            issues.append(f"{len(offline_peers)} peer(s) offline")
        
        if not issues:
            print_status("🎉", "All Tailscale checks passed!", "success")
            return True
        else:
            print_status("⚠️", f"Issues found: {', '.join(issues)}", "warning")
            return False
            
    except Exception as e:
        print_status("❌", f"Error checking Tailscale status: {e}", "error")
        return False

def check_connectivity_only(peer_ips=None):
    """Check connectivity to specific peers"""
    if not peer_ips:
        print("❌ No peer IPs provided for connectivity check")
        return False
    
    print(f"🌐 Testing connectivity to {len(peer_ips)} peer(s)...")
    
    success = ensure_tailscale_connectivity(peer_ips)
    
    if success:
        print_status("✅", "All required peers are accessible", "success")
    else:
        print_status("❌", "Some peers are not accessible", "error")
    
    return success

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # Default: comprehensive check
        success = check_tailscale_detailed()
        sys.exit(0 if success else 1)
    
    command = sys.argv[1].lower()
    
    if command in ['status', 'check', 'detailed']:
        success = check_tailscale_detailed()
        sys.exit(0 if success else 1)
    
    elif command == 'json':
        # Output raw JSON
        try:
            client = get_tailscale_client()
            network_info = client.get_network_info()
            print(format_json_output(network_info))
        except Exception as e:
            print(f'{{"error": "{e}"}}')
            sys.exit(1)
    
    elif command == 'ip':
        # Just get IP
        try:
            client = get_tailscale_client()
            ip = client.get_ip()
            if ip:
                print(ip)
            else:
                print("No IP assigned")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == 'ping' and len(sys.argv) > 2:
        # Ping specific peer
        peer_ip = sys.argv[2]
        try:
            client = get_tailscale_client()
            online, ping_time = client.ping_peer(peer_ip)
            if online:
                print(f"✅ {peer_ip}: {ping_time:.1f}ms")
            else:
                print(f"❌ {peer_ip}: Not reachable")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == 'connectivity' and len(sys.argv) > 2:
        # Test connectivity to specific peers
        peer_ips = sys.argv[2:]
        success = check_connectivity_only(peer_ips)
        sys.exit(0 if success else 1)
    
    else:
        print("Tailscale Status Checker")
        print()
        print("Usage:")
        print("  python3 tailscale-status.py [command] [options]")
        print()
        print("Commands:")
        print("  (no args)           - Comprehensive status check")
        print("  status/check        - Comprehensive status check")
        print("  json               - Output raw JSON data")
        print("  ip                 - Show Tailscale IP only")
        print("  ping <ip>          - Ping specific peer")
        print("  connectivity <ip>+ - Test connectivity to specific peers")
        print()
        print("Examples:")
        print("  python3 tailscale-status.py")
        print("  python3 tailscale-status.py json")
        print("  python3 tailscale-status.py ping 100.64.1.2")
        print("  python3 tailscale-status.py connectivity 100.64.1.2 100.64.1.3")

if __name__ == "__main__":
    main() 