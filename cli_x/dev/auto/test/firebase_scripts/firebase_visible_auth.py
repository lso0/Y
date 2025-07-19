#!/usr/bin/env python3
"""
Visible Firebase Console authentication script.
Runs with visible browser to bypass Google's "insecure browser" detection.
"""

import asyncio
import nodriver as uc
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/firebase_visible_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('firebase_visible')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

async def main():
    # Setup logging
    logger, log_file = setup_logging()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Firebase Console credentials
    email = "jalexwol@fastmail.com"
    password = "Bcg3!t7W9oPVzCVvBdECvey..MsW*K"
    
    logger.info("=== FIREBASE VISIBLE AUTHENTICATION ===")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Session ID: {timestamp}")
    logger.info(f"Email: {email}")
    
    try:
        # Start timing
        start_time = datetime.now()
        logger.info("Starting VISIBLE Chrome with nodriver...")
        
        # Initialize nodriver - VISIBLE to bypass security detection
        browser = await uc.start(
            headless=False,  # VISIBLE browser to avoid security detection
            no_sandbox=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions-except=',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-infobars',
                '--window-size=1280,720'
            ]
        )
        
        logger.info("Navigating to Firebase Console...")
        tab = await browser.get("https://console.firebase.google.com")
        
        # Wait for page to load completely
        await asyncio.sleep(3)
        
        # Take initial screenshot
        initial_screenshot = f"images/visible_01_initial_{timestamp}.png"
        await tab.save_screenshot(initial_screenshot)
        logger.info(f"📸 Initial page screenshot: {initial_screenshot}")
        
        # STEP 1: Find and fill email field
        logger.info("🔍 STEP 1: Looking for email input field...")
        email_field = await tab.find('input[type="email"]', timeout=10)
        
        if not email_field:
            logger.error("❌ Email field not found")
            return {'success': False, 'error': 'Email field not found'}
        
        logger.info("✅ Email field found - entering email...")
        await email_field.click()
        await asyncio.sleep(0.8)
        await email_field.send_keys(email)
        await asyncio.sleep(0.8)
        
        # Take screenshot after entering email
        email_screenshot = f"images/visible_02_email_entered_{timestamp}.png"
        await tab.save_screenshot(email_screenshot)
        logger.info(f"📸 Email entered screenshot: {email_screenshot}")
        
        # STEP 2: Click Next and wait for page transition
        logger.info("🔍 STEP 2: Looking for Next button...")
        current_url = tab.url
        logger.info(f"Current URL before Next: {current_url[:80]}...")
        
        # Try multiple ways to proceed to next step
        next_clicked = False
        
        # Method 1: Try Enter key first (often works)
        logger.info("Trying Enter key...")
        await email_field.send_keys('\n')
        await asyncio.sleep(2)
        
        # Check if URL changed (indicating successful transition)
        new_url = tab.url
        if new_url != current_url:
            logger.info("✅ Successfully proceeded with Enter key")
            next_clicked = True
        else:
            # Method 2: Try finding Next button
            logger.info("Enter key didn't work, looking for Next button...")
            next_button = await tab.find('#identifierNext', timeout=5)
            if next_button:
                logger.info("Found Next button, clicking...")
                await next_button.click()
                await asyncio.sleep(2)
                next_clicked = True
            else:
                # Method 3: Try other selectors
                logger.info("Trying alternative selectors...")
                selectors = [
                    'button[type="submit"]',
                    '[role="button"]',
                    '.VfPpkd-LgbsSe'
                ]
                for selector in selectors:
                    try:
                        btn = await tab.select(selector)
                        if btn:
                            logger.info(f"Found button with {selector}, clicking...")
                            await btn.click()
                            await asyncio.sleep(2)
                            next_clicked = True
                            break
                    except:
                        continue
        
        if not next_clicked:
            logger.error("❌ Could not proceed past email step")
            return {'success': False, 'error': 'Could not click Next after email'}
        
        # Take screenshot after clicking Next
        after_next_screenshot = f"images/visible_03_after_next_{timestamp}.png"
        await tab.save_screenshot(after_next_screenshot)
        logger.info(f"📸 After Next screenshot: {after_next_screenshot}")
        
        # STEP 3: Wait for password page to load OR handle security warnings
        logger.info("⏳ STEP 3: Waiting for password page to load...")
        
        # Check for security warnings first
        await asyncio.sleep(2)
        current_content = await tab.get_content()
        
        if "browser or app may not be secure" in str(current_content).lower():
            logger.warning("⚠️  Detected 'insecure browser' warning!")
            security_screenshot = f"images/visible_03_security_warning_{timestamp}.png"
            await tab.save_screenshot(security_screenshot)
            logger.info(f"📸 Security warning screenshot: {security_screenshot}")
            
            # Try to find "Try again" or similar button
            try_again_button = await tab.find('Try again', timeout=5)
            if try_again_button:
                logger.info("Found 'Try again' button, clicking...")
                await try_again_button.click()
                await asyncio.sleep(3)
        
        # Wait for password field to appear (with retries)
        password_field = None
        for attempt in range(15):  # Try for up to 15 seconds
            try:
                password_field = await tab.find('input[type="password"]', timeout=1)
                if password_field:
                    logger.info(f"✅ Password field found on attempt {attempt + 1}")
                    break
            except:
                logger.info(f"Attempt {attempt + 1}: Password field not yet available...")
                await asyncio.sleep(1)
                
                # Take periodic screenshots to see what's happening
                if attempt == 5 or attempt == 10:
                    debug_screenshot = f"images/visible_debug_attempt_{attempt}_{timestamp}.png"
                    await tab.save_screenshot(debug_screenshot)
                    logger.info(f"📸 Debug screenshot: {debug_screenshot}")
        
        if not password_field:
            logger.error("❌ Password field not found after waiting")
            error_screenshot = f"images/visible_error_no_password_{timestamp}.png"
            await tab.save_screenshot(error_screenshot)
            logger.info(f"📸 Error screenshot: {error_screenshot}")
            
            # Keep browser open for manual inspection
            logger.info("Keeping browser open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)
            
            return {'success': False, 'error': 'Password field not found'}
        
        # Take screenshot after reaching password page
        password_page_screenshot = f"images/visible_04_password_page_{timestamp}.png"
        await tab.save_screenshot(password_page_screenshot)
        logger.info(f"📸 Password page screenshot: {password_page_screenshot}")
        
        # STEP 4: Enter password
        logger.info("🔑 STEP 4: Entering password...")
        await password_field.click()
        await asyncio.sleep(0.8)
        await password_field.send_keys(password)
        await asyncio.sleep(0.8)
        
        # Take screenshot after entering password
        password_entered_screenshot = f"images/visible_05_password_entered_{timestamp}.png"
        await tab.save_screenshot(password_entered_screenshot)
        logger.info(f"📸 Password entered screenshot: {password_entered_screenshot}")
        
        # STEP 5: Submit password and wait for authentication
        logger.info("🚀 STEP 5: Submitting password...")
        current_url = tab.url
        
        # Try Enter key first
        await password_field.send_keys('\n')
        await asyncio.sleep(2)
        
        # If Enter didn't work, try Next button
        if tab.url == current_url:
            logger.info("Looking for password Next button...")
            next_button = await tab.find('#passwordNext', timeout=3)
            if next_button:
                await next_button.click()
                await asyncio.sleep(2)
        
        # STEP 6: Wait for authentication to complete
        logger.info("⏳ STEP 6: Waiting for authentication to complete...")
        
        # Monitor URL changes for up to 20 seconds
        for i in range(20):
            await asyncio.sleep(1)
            current_url = tab.url
            logger.info(f"Check {i+1}: {current_url[:80]}...")
            
            # Check for successful authentication indicators
            if "console.firebase.google.com" in current_url and "signin" not in current_url:
                logger.info("🎯 SUCCESS! Reached Firebase Console!")
                break
            elif "myaccount.google.com" in current_url:
                logger.info("🎯 SUCCESS! Reached Google Account (Firebase accessible)!")
                break
            elif i == 19:  # Last check
                logger.info("⏰ Max wait time reached")
        
        # STEP 7: Take final screenshot
        logger.info("📸 STEP 7: Taking final screenshot...")
        final_screenshot = f"images/visible_06_final_{timestamp}.png"
        await tab.save_screenshot(final_screenshot, full_page=True)
        
        # Calculate total time
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Final analysis
        final_url = tab.url
        logger.info(f"🌐 Final URL: {final_url}")
        
        # Determine success
        success = False
        if "console.firebase.google.com" in final_url and "signin" not in final_url:
            status_msg = "✅ Successfully authenticated to Firebase Console!"
            success = True
        elif "myaccount.google.com" in final_url:
            status_msg = "✅ Successfully authenticated to Google Account!"
            success = True
        elif "accounts.google.com" not in final_url:
            status_msg = "✅ Authentication completed - navigated away from login!"
            success = True
        else:
            status_msg = "⚠️  Authentication may require additional verification"
        
        logger.info(status_msg)
        logger.info(f"📸 Final screenshot: {final_screenshot}")
        logger.info(f"⚡ Total time: {total_time:.2f} seconds")
        
        # Keep browser open longer for inspection
        logger.info("Keeping browser open for 15 seconds for inspection...")
        await asyncio.sleep(15)
        
        return {
            'success': success,
            'screenshot': final_screenshot,
            'total_time': total_time,
            'final_url': final_url,
            'log_file': log_file,
            'status': status_msg
        }
        
    except Exception as e:
        logger.error(f"❌ Error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'success': False, 'error': str(e)}
        
    finally:
        # Clean up
        try:
            await browser.stop()
            logger.info("🧹 Browser cleanup completed")
        except:
            logger.info("🧹 Browser cleanup skipped")

if __name__ == "__main__":
    result = asyncio.run(main())
    
    print("\n" + "="*60)
    print("👁️  FIREBASE VISIBLE AUTHENTICATION SUMMARY")
    print("="*60)
    
    if result and result.get('success'):
        print(f"✅ Status: SUCCESS")
        print(f"📸 Final Screenshot: {result['screenshot']}")
        print(f"⚡ Time: {result['total_time']:.2f} seconds")
        print(f"📋 Log: {result['log_file']}")
        print(f"💬 Details: {result.get('status', 'N/A')}")
        print(f"🌐 URL: {result['final_url'][:80]}...")
    else:
        print(f"❌ Status: FAILED")
        if result:
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
    
    print("="*60) 