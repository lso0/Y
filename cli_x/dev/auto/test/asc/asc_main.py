#!/usr/bin/env python3
"""
App Store Connect Automation Suite - Main CLI
==============================================

This is the main command-line interface for App Store Connect automation.
It provides different modes for various use cases and automation needs.

Usage:
    python asc/asc_main.py --mode MODE

Available Modes:
    visible     - Visible browser login (most reliable, handles 2FA)
    fast        - Fast automation mode (less 2FA handling)
    screenshot  - Simple screenshot of App Store Connect
    test        - Test login credentials without full automation
    
Examples:
    python asc/asc_main.py --mode visible
    python asc/asc_main.py --mode fast
    python asc/asc_main.py --list
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to path so we can import from asc_login_nodriver
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print the ASC automation banner."""
    print("🍎" + "="*60 + "🍎")
    print("📱  APP STORE CONNECT AUTOMATION SUITE")
    print("🍎" + "="*60 + "🍎")
    print()

def list_modes():
    """List all available automation modes."""
    print_banner()
    print("📋 Available Automation Modes:")
    print()
    
    modes = [
        ("visible", "🟢 Visible Browser (RECOMMENDED)", "Most reliable, handles 2FA, good for debugging"),
        ("fast", "⚡ Fast Automation", "Faster login, less 2FA handling, good for production"),
        ("screenshot", "📸 Screenshot Only", "Just take a screenshot of App Store Connect"),
        ("test", "🧪 Test Credentials", "Test login credentials without full automation"),
    ]
    
    for mode, title, description in modes:
        print(f"  {title}")
        print(f"    Mode: {mode}")
        print(f"    Description: {description}")
        print(f"    Usage: python asc/asc_main.py --mode {mode}")
        print()
    
    print("💡 Recommended: Start with '--mode visible' for most reliable results")
    print("🔧 For production automation, use '--mode fast' after testing")

async def run_visible_mode():
    """Run visible browser automation (most reliable)."""
    print("🟢 Starting Visible Browser Mode...")
    print("📋 This mode is most reliable and handles 2FA automatically")
    print()
    
    try:
        from asc_login_nodriver import main as asc_main
        await asc_main()
    except ImportError:
        print("❌ Error: Could not import asc_login_nodriver module")
        print("💡 Make sure you're running from the correct directory")
        return False
    except Exception as e:
        print(f"❌ Error in visible mode: {e}")
        return False
    
    return True

async def run_fast_mode():
    """Run fast automation mode."""
    print("⚡ Starting Fast Automation Mode...")
    print("📋 This mode is faster but may need manual 2FA handling")
    print()
    
    # Import and run the fast automation
    try:
        from asc_fast_automation import main as fast_main
        await fast_main()
    except ImportError:
        print("⚠️ Fast automation module not found, falling back to visible mode")
        return await run_visible_mode()
    except Exception as e:
        print(f"❌ Error in fast mode: {e}")
        return False
    
    return True

async def run_screenshot_mode():
    """Take a simple screenshot of App Store Connect."""
    print("📸 Starting Screenshot Mode...")
    print("📋 Taking a simple screenshot of App Store Connect homepage")
    print()
    
    import nodriver as uc
    import logging
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('asc_screenshot')
    
    try:
        # Start browser
        browser = await uc.start(headless=False)
        tab = await browser.get("https://appstoreconnect.apple.com")
        
        await asyncio.sleep(3)
        
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("images", exist_ok=True)
        filename = f"images/asc_screenshot_{timestamp}.png"
        
        await tab.save_screenshot(filename)
        print(f"✅ Screenshot saved: {filename}")
        
        await browser.stop()
        return True
        
    except Exception as e:
        print(f"❌ Error taking screenshot: {e}")
        return False

async def run_test_mode():
    """Test credentials without full automation."""
    print("🧪 Starting Test Mode...")
    print("📋 This will test your credentials without full login automation")
    print()
    
    # Simple credential test - just navigate and check for login page
    import nodriver as uc
    
    try:
        browser = await uc.start(headless=False)
        tab = await browser.get("https://appstoreconnect.apple.com")
        
        await asyncio.sleep(3)
        
        current_url = tab.url
        print(f"📍 Current URL: {current_url}")
        
        # Check if we're on login page or already logged in
        if "signin" in current_url.lower() or "login" in current_url.lower():
            print("✅ Successfully reached login page")
            print("💡 You can now manually test your credentials")
        elif "appstoreconnect.apple.com" in current_url:
            print("✅ Already logged into App Store Connect!")
        else:
            print("⚠️ Unexpected page reached")
        
        # Take screenshot for reference
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("images", exist_ok=True)
        filename = f"images/asc_test_{timestamp}.png"
        await tab.save_screenshot(filename)
        print(f"📸 Screenshot saved: {filename}")
        
        print("🌐 Browser will stay open for manual testing")
        print("📋 Press Ctrl+C to close and exit")
        
        # Wait for user interrupt
        try:
            while True:
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Closing browser...")
        
        await browser.stop()
        return True
        
    except Exception as e:
        print(f"❌ Error in test mode: {e}")
        return False

async def main():
    """Main function to handle CLI arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(
        description="App Store Connect Automation Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python asc/asc_main.py --mode visible      # Most reliable mode
  python asc/asc_main.py --mode fast         # Fast automation
  python asc/asc_main.py --mode screenshot   # Screenshot only
  python asc/asc_main.py --list              # List all modes
  
For more information, visit: https://developer.apple.com/app-store-connect/
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['visible', 'fast', 'screenshot', 'test'],
        help='Automation mode to run'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available modes'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_modes()
        return
    
    if not args.mode:
        print("❌ Error: No mode specified")
        print("💡 Use --list to see available modes")
        print("💡 Use --mode MODE to run a specific mode")
        return
    
    print_banner()
    print(f"🚀 Starting App Store Connect automation in '{args.mode}' mode")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = False
    start_time = datetime.now()
    
    try:
        if args.mode == 'visible':
            success = await run_visible_mode()
        elif args.mode == 'fast':
            success = await run_fast_mode()
        elif args.mode == 'screenshot':
            success = await run_screenshot_mode()
        elif args.mode == 'test':
            success = await run_test_mode()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("🍎" + "="*60 + "🍎")
        if success:
            print(f"✅ App Store Connect automation completed successfully in {duration:.1f} seconds!")
        else:
            print(f"❌ App Store Connect automation failed after {duration:.1f} seconds")
        print("🍎" + "="*60 + "🍎")
        
    except KeyboardInterrupt:
        print("\n🛑 Automation interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
        sys.exit(0) 