"""
Tailscale utilities for RC automation.
Provides functions to interact with Tailscale network and authentication.
"""

import os
import subprocess
import json
import socket
from typing import Dict, List, Optional, Tuple
import requests


class TailscaleClient:
    """Client for interacting with Tailscale."""
    
    def __init__(self):
        self.tailscale_ip = os.getenv('TAILSCALE_IP', '')
        self.tailscale_enabled = os.getenv('TAILSCALE_ENABLED', 'false').lower() == 'true'
        self.hostname = os.getenv('TAILSCALE_HOSTNAME', socket.gethostname())
    
    def is_enabled(self) -> bool:
        """Check if Tailscale is enabled."""
        return self.tailscale_enabled
    
    def get_status(self) -> Dict:
        """Get Tailscale status."""
        try:
            result = subprocess.run(['tailscale', 'status', '--json'], 
                                  capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def get_ip(self) -> Optional[str]:
        """Get the current Tailscale IP address."""
        if self.tailscale_ip:
            return self.tailscale_ip
        
        try:
            result = subprocess.run(['tailscale', 'ip', '-4'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_peers(self) -> List[Dict]:
        """Get list of Tailscale peers."""
        status = self.get_status()
        if not status or 'Peer' not in status:
            return []
        
        peers_dict = status.get('Peer')
        if not peers_dict or not isinstance(peers_dict, dict):
            return []
            
        return [peer for peer in peers_dict.values()]
    
    def is_peer_online(self, peer_ip: str) -> bool:
        """Check if a specific peer is online."""
        peers = self.get_peers()
        for peer in peers:
            if peer.get('TailscaleIPs', []):
                if peer_ip in peer['TailscaleIPs'] and peer.get('Online', False):
                    return True
        return False
    
    def ping_peer(self, peer_ip: str, timeout: int = 5) -> Tuple[bool, float]:
        """
        Ping a peer through Tailscale.
        Returns (success, response_time_ms)
        """
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', str(timeout * 1000), peer_ip],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract time from ping output
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        time_part = line.split('time=')[1].split(' ')[0]
                        return True, float(time_part)
                return True, 0.0
            return False, 0.0
        except Exception:
            return False, 0.0
    
    def make_request(self, peer_ip: str, port: int, path: str = '', 
                    method: str = 'GET', **kwargs) -> requests.Response:
        """
        Make an HTTP request to a peer through Tailscale.
        """
        if not self.is_enabled():
            raise RuntimeError("Tailscale is not enabled")
        
        url = f"http://{peer_ip}:{port}{path}"
        
        # Add Tailscale-specific headers
        headers = kwargs.get('headers', {})
        headers['X-Tailscale-User'] = self.hostname
        kwargs['headers'] = headers
        
        return requests.request(method, url, **kwargs)
    
    def get_network_info(self) -> Dict:
        """Get comprehensive Tailscale network information."""
        info = {
            'enabled': self.is_enabled(),
            'ip': self.get_ip(),
            'hostname': self.hostname,
            'status': self.get_status(),
            'peers': self.get_peers()
        }
        
        # Add connectivity test results
        info['connectivity'] = {}
        for peer in info['peers']:
            if peer.get('TailscaleIPs'):
                peer_ip = peer['TailscaleIPs'][0]
                online, ping_time = self.ping_peer(peer_ip)
                info['connectivity'][peer_ip] = {
                    'online': online,
                    'ping_ms': ping_time,
                    'hostname': peer.get('HostName', 'unknown')
                }
        
        return info


def get_tailscale_client() -> TailscaleClient:
    """Get a configured Tailscale client instance."""
    return TailscaleClient()


def ensure_tailscale_connectivity(required_peers: List[str] = None) -> bool:
    """
    Ensure Tailscale is working and required peers are accessible.
    
    Args:
        required_peers: List of peer IPs that must be accessible
    
    Returns:
        True if all checks pass, False otherwise
    """
    client = get_tailscale_client()
    
    if not client.is_enabled():
        print("❌ Tailscale is not enabled")
        return False
    
    if not client.get_ip():
        print("❌ Could not get Tailscale IP address")
        return False
    
    print(f"✅ Tailscale IP: {client.get_ip()}")
    
    if required_peers:
        for peer_ip in required_peers:
            online, ping_time = client.ping_peer(peer_ip)
            if online:
                print(f"✅ Peer {peer_ip} is reachable ({ping_time:.1f}ms)")
            else:
                print(f"❌ Peer {peer_ip} is not reachable")
                return False
    
    return True


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        client = get_tailscale_client()
        
        if command == "status":
            info = client.get_network_info()
            print(json.dumps(info, indent=2))
        elif command == "ip":
            print(client.get_ip() or "Not available")
        elif command == "peers":
            peers = client.get_peers()
            for peer in peers:
                print(f"{peer.get('HostName', 'unknown')}: {peer.get('TailscaleIPs', [])}")
        elif command == "ping" and len(sys.argv) > 2:
            peer_ip = sys.argv[2]
            online, ping_time = client.ping_peer(peer_ip)
            print(f"Ping {peer_ip}: {'OK' if online else 'FAIL'} ({ping_time:.1f}ms)")
        else:
            print("Usage: python tailscale_utils.py [status|ip|peers|ping <ip>]")
    else:
        # Run connectivity check
        ensure_tailscale_connectivity() 