#!/usr/bin/env python3
"""
YouTube Automation Service
Complete YouTube automation with Infisical secrets sync and subscription functionality
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def run_secrets_sync():
    """Sync secrets from Infisical"""
    try:
        # Simple approach: script is in cli_x/dev/auto/services/youtube/scripts/, so project root is 6 levels up
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent.parent.parent.parent.parent
        print("🔐 Syncing secrets from Infisical...")
        
        result = subprocess.run([
            "scripts/infisical/setup-infisical.sh", "sync"
        ], capture_output=True, text=True, cwd=str(project_root))
        
        if result.returncode == 0:
            print("✅ Secrets synced successfully")
            return True
        else:
            print(f"❌ Secrets sync failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Secrets sync error: {e}")
        return False

def run_environment_check():
    """Check if environment variables are properly loaded"""
    try:
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent.parent.parent.parent.parent
        print("🧪 Checking environment variables...")
        
        result = subprocess.run([
            "python3", "cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py"
        ], capture_output=True, text=True, cwd=str(project_root))
        
        if result.returncode == 0:
            print("✅ Environment check passed")
            print(result.stdout)
            return True
        else:
            print(f"❌ Environment check failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Environment check error: {e}")
        return False

def run_youtube_automation(channel_url=None):
    """Run YouTube automation with the specified channel"""
    try:
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent.parent.parent.parent.parent
        print("🎬 Starting YouTube automation...")
        
        cmd = ["python3", "cli_x/dev/auto/services/youtube/scripts/youtube_automation_env.py"]
        if channel_url:
            cmd.append(channel_url)
            
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(project_root)
        )
        
        if result.returncode == 0:
            print("✅ YouTube automation completed successfully")
            print(result.stdout)
            return True
        else:
            print(f"❌ YouTube automation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ YouTube automation error: {e}")
        return False

def main():
    """Complete YouTube automation workflow"""
    print("🚀 Starting Complete YouTube Automation Workflow")
    print("=" * 60)
    
    # Step 1: Sync secrets from Infisical
    if not run_secrets_sync():
        print("❌ Secrets sync failed - cannot proceed")
        return False
    
    # Step 2: Check environment variables
    if not run_environment_check():
        print("❌ Environment check failed - cannot proceed")
        return False
    
    # Step 3: Run YouTube automation
    channel_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/channel/UCsXVk37bltHxD1rDPwtNM8Q"
    if not run_youtube_automation(channel_url):
        print("❌ YouTube automation failed")
        return False
    
    print("🎉 COMPLETE SUCCESS: Full YouTube automation workflow completed!")
    return True

if __name__ == "__main__":
    success = main()
    print(f"🎯 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1) 