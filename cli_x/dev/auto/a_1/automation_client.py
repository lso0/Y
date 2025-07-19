#!/usr/bin/env python3
"""
Automation Client
Sends requests to the persistent automation server
"""

import requests
import json
import sys
import argparse
from typing import Optional

class AutomationClient:
    def __init__(self, server_url: str = "http://localhost:8888"):
        self.server_url = server_url.rstrip('/')
        
    def get_status(self):
        """Get server status"""
        try:
            response = requests.get(f"{self.server_url}/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to server: {e}"}
            
    def check_session_health(self):
        """Check session health"""
        try:
            response = requests.get(f"{self.server_url}/session/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to check session health: {e}"}
            
    def refresh_session(self):
        """Force refresh session"""
        try:
            response = requests.post(f"{self.server_url}/session/refresh")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to refresh session: {e}"}
            
    def create_alias(self, alias_email: str, target_email: str, description: str = ""):
        """Create a new alias"""
        try:
            payload = {
                "alias_email": alias_email,
                "target_email": target_email,
                "description": description
            }
            response = requests.post(f"{self.server_url}/alias/create", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except:
                    error_detail = str(e)
                return {"error": f"Alias creation failed: {error_detail}"}
            return {"error": f"Failed to create alias: {e}"}

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Automation Client CLI")
    parser.add_argument("--server", default="http://localhost:8888", 
                       help="Server URL (default: http://localhost:8888)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Get server status")
    
    # Session commands
    session_parser = subparsers.add_parser("session", help="Session management")
    session_subparsers = session_parser.add_subparsers(dest="session_action")
    session_subparsers.add_parser("health", help="Check session health")
    session_subparsers.add_parser("refresh", help="Refresh session")
    
    # Alias command
    alias_parser = subparsers.add_parser("alias", help="Create alias")
    alias_parser.add_argument("alias_email", help="Alias email address")
    alias_parser.add_argument("target_email", help="Target email address")
    alias_parser.add_argument("--description", default="", help="Alias description")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    client = AutomationClient(args.server)
    
    if args.command == "status":
        result = client.get_status()
        print_json(result)
        
    elif args.command == "session":
        if args.session_action == "health":
            result = client.check_session_health()
            print_json(result)
        elif args.session_action == "refresh":
            print("🔄 Refreshing session...")
            result = client.refresh_session()
            print_json(result)
        else:
            session_parser.print_help()
            
    elif args.command == "alias":
        print(f"🎯 Creating alias: {args.alias_email} -> {args.target_email}")
        result = client.create_alias(args.alias_email, args.target_email, args.description)
        print_json(result)
        
        if "success" in result and result["success"]:
            print(f"✅ Alias created successfully!")
        elif "error" in result:
            print(f"❌ Error: {result['error']}")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 