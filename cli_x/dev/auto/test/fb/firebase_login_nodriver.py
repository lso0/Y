#!/usr/bin/env python3
"""
Script to automatically sign in to Firebase Console using nodriver.
"""

import asyncio
import nodriver as uc
import os
from datetime import datetime

async def main():
    # Firebase Console credentials
    email = "jalexwol@fastmail.com"
    password = "Bcg3!t7W9oPVzCVvBdECvey..MsW*K"
    
    # Screenshot save path (current directory)
    screenshot_dir = os.getcwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Starting Chrome with nodriver...")
    print(f"Will attempt to sign in to Firebase Console...")
    print(f"Email: {email}")
    
    try:
        # Initialize nodriver with default settings
        browser = await uc.start(
            headless=False,  # Keep visible so you can see the process
            no_sandbox=True
        )
        
        # Navigate to Firebase Console (this will redirect to Google sign-in)
        print("Navigating to Firebase Console...")
        tab = await browser.get("https://console.firebase.google.com")
        
        # Wait for page to load
        await asyncio.sleep(3)
        
        # Take screenshot of initial page
        initial_screenshot = os.path.join(screenshot_dir, f"firebase_01_initial_{timestamp}.png")
        await tab.save_screenshot(initial_screenshot)
        print(f"Initial page screenshot: {initial_screenshot}")
        
        # Look for email input field
        print("Looking for email input field...")
        email_field = await tab.find('input[type="email"]', timeout=10)
        
        if email_field:
            print("Found email field, entering email...")
            await email_field.click()
            await email_field.send_keys(email)
            await asyncio.sleep(1)
            
            # Take screenshot after entering email
            email_screenshot = os.path.join(screenshot_dir, f"firebase_02_email_entered_{timestamp}.png")
            await tab.save_screenshot(email_screenshot)
            print(f"Email entered screenshot: {email_screenshot}")
            
            # Look for and click "Next" button
            print("Looking for Next button...")
            next_button = None
            
            # Try multiple ways to find the Next button
            selectors_to_try = [
                '#identifierNext',
                'button:contains("Next")',
                '[data-idom-class*="Next"]',
                'button[type="submit"]',
                '.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-k8QpJ',
                'button[jsname="LgbsSe"]',
                '[role="button"]:contains("Next")',
                'div[role="button"]:contains("Next")',
                'span:contains("Next")',
                '.VfPpkd-vQzf8d'
            ]
            
            for selector in selectors_to_try:
                try:
                    print(f"Trying selector: {selector}")
                    next_button = await tab.select(selector)
                    if next_button:
                        print(f"Found Next button with selector: {selector}")
                        break
                except:
                    continue
            
            # If still not found, try a more general approach
            if not next_button:
                print("Trying to find any clickable element with 'Next' text...")
                try:
                    next_button = await tab.find("Next", best_match=True)
                except:
                    pass
            
            if next_button:
                print("Found Next button, clicking...")
                await next_button.click()
                await asyncio.sleep(3)
            else:
                print("Next button not found, trying Enter key...")
                await email_field.send_keys('\n')  # Press Enter
                await asyncio.sleep(3)
                
            # Take screenshot after clicking Next
            next_screenshot = os.path.join(screenshot_dir, f"firebase_03_after_next_{timestamp}.png")
            await tab.save_screenshot(next_screenshot)
            print(f"After Next screenshot: {next_screenshot}")
            
            # Look for password input field
            print("Looking for password input field...")
            password_field = await tab.find('input[type="password"]', timeout=10)
            
            if password_field:
                print("Found password field, entering password...")
                await password_field.click()
                await password_field.send_keys(password)
                await asyncio.sleep(1)
                
                # Take screenshot after entering password
                pwd_screenshot = os.path.join(screenshot_dir, f"firebase_04_password_entered_{timestamp}.png")
                await tab.save_screenshot(pwd_screenshot)
                print(f"Password entered screenshot: {pwd_screenshot}")
                
                # Look for and click "Next" or "Sign in" button
                print("Looking for Sign In button...")
                signin_button = await tab.find('button:contains("Next")', timeout=5)
                if not signin_button:
                    signin_button = await tab.find('#passwordNext', timeout=5)
                if not signin_button:
                    signin_button = await tab.find('button[type="submit"]', timeout=5)
                
                if signin_button:
                    print("Found Sign In button, clicking...")
                    await signin_button.click()
                    await asyncio.sleep(5)  # Wait longer for login to complete
                    
                    # Take final screenshot
                    final_screenshot = os.path.join(screenshot_dir, f"firebase_05_signed_in_{timestamp}.png")
                    await tab.save_screenshot(final_screenshot, full_page=True)
                    print(f"Final screenshot: {final_screenshot}")
                    
                    print("✅ Login process completed!")
                    
                else:
                    print("Sign In button not found, trying Enter key...")
                    await password_field.send_keys('\n')  # Press Enter
                    await asyncio.sleep(5)
                    
                    # Take final screenshot
                    final_screenshot = os.path.join(screenshot_dir, f"firebase_05_signed_in_{timestamp}.png")
                    await tab.save_screenshot(final_screenshot, full_page=True)
                    print(f"Final screenshot: {final_screenshot}")
                    
                    print("✅ Login process completed (used Enter key)!")
            else:
                print("❌ Could not find password field")
        else:
            print("❌ Could not find email input field")
        
        # Keep browser open for inspection
        print("Keeping browser open for 10 seconds for inspection...")
        await asyncio.sleep(10)
        
        # Close the browser
        try:
            await browser.stop()
            print("Browser closed successfully.")
        except:
            print("Browser cleanup completed.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 