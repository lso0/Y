#!/usr/bin/env python3
"""
Step-by-step Firebase Console authentication script.
Properly handles email -> Next -> password -> Next -> wait -> screenshot flow.
"""

import asyncio
import nodriver as uc
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/firebase_step_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('firebase_step')
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

async def wait_for_url_change(tab, current_url, max_wait=10):
    """Wait for URL to change from current_url."""
    for i in range(max_wait):
        await asyncio.sleep(1)
        new_url = tab.url
        if new_url != current_url:
            return new_url
    return tab.url

async def main():
    # Setup logging
    logger, log_file = setup_logging()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Firebase Console credentials
    email = "jalexwol@fastmail.com"
    password = "Bcg3!t7W9oPVzCVvBdECvey..MsW*K"
    
    logger.info("=== FIREBASE STEP-BY-STEP AUTHENTICATION ===")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Session ID: {timestamp}")
    logger.info(f"Email: {email}")
    
    try:
        # Start timing
        start_time = datetime.now()
        logger.info("Starting headless Chrome with nodriver...")
        
        # Initialize nodriver - HEADLESS for speed
        browser = await uc.start(
            headless=True,  # HEADLESS for speed
            no_sandbox=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        
        logger.info("Navigating to Firebase Console...")
        tab = await browser.get("https://console.firebase.google.com")
        
        # Wait for page to load completely
        await asyncio.sleep(2)
        
        # Take initial screenshot
        initial_screenshot = f"images/step_01_initial_{timestamp}.png"
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
        await asyncio.sleep(0.5)
        await email_field.send_keys(email)
        await asyncio.sleep(0.5)
        
        # Take screenshot after entering email
        email_screenshot = f"images/step_02_email_entered_{timestamp}.png"
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
        await asyncio.sleep(1)
        
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
                            next_clicked = True
                            break
                    except:
                        continue
        
        if not next_clicked:
            logger.error("❌ Could not proceed past email step")
            return {'success': False, 'error': 'Could not click Next after email'}
        
        # STEP 3: Wait for password page to load
        logger.info("⏳ STEP 3: Waiting for password page to load...")
        
        # Wait for URL to change (indicating page transition)
        await asyncio.sleep(2)  # Give time for page transition
        
        # Wait for password field to appear (with retries)
        password_field = None
        for attempt in range(10):  # Try for up to 10 seconds
            try:
                password_field = await tab.find('input[type="password"]', timeout=1)
                if password_field:
                    logger.info(f"✅ Password field found on attempt {attempt + 1}")
                    break
            except:
                logger.info(f"Attempt {attempt + 1}: Password field not yet available...")
                await asyncio.sleep(1)
        
        if not password_field:
            logger.error("❌ Password field not found after waiting")
            error_screenshot = f"images/step_error_no_password_{timestamp}.png"
            await tab.save_screenshot(error_screenshot)
            logger.info(f"📸 Error screenshot: {error_screenshot}")
            return {'success': False, 'error': 'Password field not found'}
        
        # Take screenshot after reaching password page
        password_page_screenshot = f"images/step_03_password_page_{timestamp}.png"
        await tab.save_screenshot(password_page_screenshot)
        logger.info(f"📸 Password page screenshot: {password_page_screenshot}")
        
        # STEP 4: Enter password
        logger.info("🔑 STEP 4: Entering password...")
        await password_field.click()
        await asyncio.sleep(0.5)
        await password_field.send_keys(password)
        await asyncio.sleep(0.5)
        
        # Take screenshot after entering password
        password_entered_screenshot = f"images/step_04_password_entered_{timestamp}.png"
        await tab.save_screenshot(password_entered_screenshot)
        logger.info(f"📸 Password entered screenshot: {password_entered_screenshot}")
        
        # STEP 5: Submit password and wait for authentication
        logger.info("🚀 STEP 5: Submitting password...")
        current_url = tab.url
        
        # Try Enter key first
        await password_field.send_keys('\n')
        await asyncio.sleep(1)
        
        # If Enter didn't work, try Next button
        if tab.url == current_url:
            logger.info("Looking for password Next button...")
            next_button = await tab.find('#passwordNext', timeout=3)
            if next_button:
                await next_button.click()
        
        # STEP 6: Wait for authentication to complete
        logger.info("⏳ STEP 6: Waiting for authentication to complete...")
        
        # Monitor URL changes for up to 15 seconds
        for i in range(15):
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
            elif i == 14:  # Last check
                logger.info("⏰ Max wait time reached")
        
        # STEP 7: Take final screenshot
        logger.info("📸 STEP 7: Taking final screenshot...")
        final_screenshot = f"images/step_05_final_{timestamp}.png"
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
    print("🎯 FIREBASE STEP-BY-STEP AUTHENTICATION SUMMARY")
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