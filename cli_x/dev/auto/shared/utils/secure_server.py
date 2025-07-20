#!/usr/bin/env python3
"""
Secure Server Launcher
Starts the FastMail automation server using YubiKey-encrypted tokens
"""

import sys
import os
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent))
from secure_token_manager import SecureTokenManager

def main():
    print("🔐 Secure FastMail Automation Server Launcher")
    print("=" * 50)
    
    manager = SecureTokenManager()
    
    # Server command
    server_cmd = [
        'python', 'servers/enhanced_automation_server.py'
    ]
    
    print("🚀 Starting server with YubiKey authentication...")
    success = manager.run_infisical_command(server_cmd)
    
    if not success:
        print("❌ Failed to start server")
        sys.exit(1)

if __name__ == "__main__":
    main() 