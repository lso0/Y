#!/usr/bin/env python3
"""
Firebase Authentication Suite - Main Script
Run different Firebase authentication modes with command-line flags.

Usage:
    python main.py --mode reactive     # Ultra-fast reactive authentication
    python main.py --mode visible      # Visible browser authentication
    python main.py --mode step         # Step-by-step authentication
    python main.py --mode headless     # Headless authentication
    python main.py --mode screenshot   # Simple screenshot mode
    python main.py --mode login        # Visual login with all steps
    python main.py --list              # List all available modes
"""

import asyncio
import argparse
import sys
import os
import importlib.util
from datetime import datetime

def load_script_module(script_path):
    """Dynamically load a Python script as a module."""
    spec = importlib.util.spec_from_file_location("firebase_script", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def print_banner():
    """Print the application banner."""
    print("\n" + "="*70)
    print("🔥 FIREBASE AUTHENTICATION SUITE")
    print("="*70)
    print("Ultra-fast, organized Firebase Console authentication")
    print("Multiple modes for different use cases")
    print("="*70)

def list_modes():
    """List all available authentication modes."""
    modes = {
        'reactive': {
            'name': 'Reactive Ultra-Fast',
            'file': 'firebase_scripts/firebase_reactive_fast.py',
            'description': 'Immediately clicks elements as they appear (FASTEST)',
            'speed': '⚡⚡⚡ Ultra-Fast',
            'reliability': '🟢 High'
        },
        'visible': {
            'name': 'Visible Browser',
            'file': 'firebase_scripts/firebase_visible_auth.py',
            'description': 'Step-by-step visible authentication (MOST RELIABLE)',
            'speed': '⚡⚡ Fast',
            'reliability': '🟢 Very High'
        },
        'step': {
            'name': 'Step-by-Step',
            'file': 'firebase_scripts/firebase_step_by_step.py',
            'description': 'Detailed step-by-step process with screenshots',
            'speed': '⚡ Normal',
            'reliability': '🟡 Medium'
        },
        'headless': {
            'name': 'Headless Fast',
            'file': 'firebase_scripts/firebase_fast_headless.py',
            'description': 'Fast headless mode (may be blocked by Google)',
            'speed': '⚡⚡⚡ Ultra-Fast',
            'reliability': '🔴 Low (blocked)'
        },
        'ultra': {
            'name': 'Ultra Fast',
            'file': 'firebase_scripts/firebase_ultra_fast.py',
            'description': 'Ultra-fast headless with URL monitoring',
            'speed': '⚡⚡⚡ Ultra-Fast',
            'reliability': '🔴 Low (blocked)'
        },
        'screenshot': {
            'name': 'Simple Screenshot',
            'file': 'firebase_scripts/screenshot_firebase_nodriver.py',
            'description': 'Just take a screenshot of Firebase homepage',
            'speed': '⚡ Normal',
            'reliability': '🟢 High'
        },
        'login': {
            'name': 'Visual Login',
            'file': 'firebase_scripts/firebase_login_nodriver.py',
            'description': 'Visual login with detailed step screenshots',
            'speed': '⚡ Normal',
            'reliability': '🟢 High'
        }
    }
    
    print("\n📋 Available Authentication Modes:")
    print("-" * 70)
    
    for mode_key, mode_info in modes.items():
        print(f"🔹 {mode_key:12} - {mode_info['name']}")
        print(f"   Description: {mode_info['description']}")
        print(f"   Speed:       {mode_info['speed']}")
        print(f"   Reliability: {mode_info['reliability']}")
        print(f"   File:        {mode_info['file']}")
        print()

def get_script_path(mode):
    """Get the script path for a given mode."""
    script_map = {
        'reactive': 'firebase_scripts/firebase_reactive_fast.py',
        'visible': 'firebase_scripts/firebase_visible_auth.py',
        'step': 'firebase_scripts/firebase_step_by_step.py',
        'headless': 'firebase_scripts/firebase_fast_headless.py',
        'ultra': 'firebase_scripts/firebase_ultra_fast.py',
        'screenshot': 'firebase_scripts/screenshot_firebase_nodriver.py',
        'login': 'firebase_scripts/firebase_login_nodriver.py'
    }
    
    return script_map.get(mode)

async def run_firebase_script(mode):
    """Run the specified Firebase authentication script."""
    script_path = get_script_path(mode)
    
    if not script_path:
        print(f"❌ Error: Unknown mode '{mode}'")
        print("Use --list to see available modes")
        return False
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Script file not found: {script_path}")
        return False
    
    print(f"\n🚀 Running mode: {mode}")
    print(f"📄 Script: {script_path}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Load and run the script
        module = load_script_module(script_path)
        
        if hasattr(module, 'main'):
            # Run the async main function
            result = await module.main()
            
            print("\n" + "="*60)
            print("📊 EXECUTION SUMMARY")
            print("="*60)
            
            if result and isinstance(result, dict):
                if result.get('success'):
                    print("✅ Status: SUCCESS")
                    if 'total_time' in result:
                        print(f"⚡ Total Time: {result['total_time']:.2f} seconds")
                    if 'screenshot' in result:
                        print(f"📸 Screenshot: {result['screenshot']}")
                    if 'final_url' in result:
                        print(f"🌐 Final URL: {result['final_url'][:80]}...")
                    if 'log_file' in result:
                        print(f"📋 Log File: {result['log_file']}")
                else:
                    print("❌ Status: FAILED")
                    if 'error' in result:
                        print(f"💥 Error: {result['error']}")
            else:
                print("✅ Script executed successfully")
            
            return True
            
        else:
            print("❌ Error: Script does not have a main() function")
            return False
            
    except Exception as e:
        print(f"❌ Error running script: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to handle command-line arguments and run scripts."""
    parser = argparse.ArgumentParser(
        description='Firebase Authentication Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode reactive      # Ultra-fast reactive authentication
  python main.py --mode visible       # Reliable visible browser authentication
  python main.py --list               # List all available modes
  
Recommended modes:
  - reactive: Fastest, most advanced
  - visible:  Most reliable, step-by-step
  - login:    Visual debugging mode
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        type=str,
        help='Authentication mode to run'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available authentication modes'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.list:
        list_modes()
        return
    
    if not args.mode:
        print("❌ Error: No mode specified")
        print("\nUse --list to see available modes")
        print("Example: python main.py --mode reactive")
        sys.exit(1)
    
    # Ensure directories exist
    os.makedirs('images', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the specified mode
    success = asyncio.run(run_firebase_script(args.mode))
    
    if success:
        print(f"\n✅ Mode '{args.mode}' completed successfully!")
    else:
        print(f"\n❌ Mode '{args.mode}' failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 