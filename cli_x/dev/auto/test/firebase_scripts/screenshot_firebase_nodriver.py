#!/usr/bin/env python3
"""
Script to take a screenshot of Google Firebase using nodriver (no profile).
"""

import asyncio
import nodriver as uc
import os
from datetime import datetime

async def main():
    # Screenshot save path (current directory)
    screenshot_dir = os.getcwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_filename = f"firebase_screenshot_nodriver_{timestamp}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    
    print(f"Starting Chrome with nodriver (no profile)...")
    print(f"Navigating to Google Firebase...")
    print(f"Screenshot will be saved to: {screenshot_path}")
    
    try:
        # Initialize nodriver with default settings
        browser = await uc.start(
            headless=False,  # Keep visible
            no_sandbox=True
        )
        
        # Navigate to Google Firebase
        tab = await browser.get("https://firebase.google.com")
        
        print("Waiting for Firebase page to load...")
        
        # Wait for the page to load completely
        await asyncio.sleep(3)
        
        # Take screenshot
        print("Taking screenshot...")
        await tab.save_screenshot(screenshot_path, full_page=True)
        
        print(f"Screenshot saved successfully: {screenshot_path}")
        
        # Keep the browser open for a few seconds
        print("Keeping browser open for 5 seconds...")
        await asyncio.sleep(5)
        
        # Close the browser
        await browser.stop()
        print("Browser closed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 