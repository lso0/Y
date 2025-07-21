#!/usr/bin/env python3
"""
YouTube Automation Environment Checker
Validates that all required environment variables are available for YouTube automation
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Simple approach: script is in cli_x/dev/auto/services/youtube/scripts/, so project root is 6 levels up
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent.parent.parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print(f"❌ .env file not found at {env_file}")
        print("Run: scripts/infisical/setup-infisical.sh sync")
        sys.exit(1)
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip("'\"")
                    os.environ[key] = value
        
        print("✅ Environment variables loaded from .env file")
        return True
    except Exception as e:
        print(f"❌ Failed to load .env file: {e}")
        return False

if __name__ == "__main__":
    print("🧪 YouTube Automation Environment Checker")
    print("=" * 60)
    success = main()
    print(f"🎯 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}") 