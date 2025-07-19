#!/usr/bin/env python3
"""
Ultra-fast reactive Firebase Console authentication script.
Immediately clicks elements as they become available for maximum speed.
"""

import asyncio
import nodriver as uc
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/firebase_reactive_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('firebase_reactive')
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

async def wait_and_click_immediately(tab, element_selector, action_name, timeout=10):
    """Wait for element and click immediately when available."""
    logger = logging.getLogger('firebase_reactive')
    start_time = datetime.now()
    
    for attempt in range(int(timeout * 10)):  # Check every 0.1 seconds
        try:
            element = await tab.find(element_selector, timeout=0.1)
            if element:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"⚡ {action_name} found in {elapsed:.2f}s - clicking immediately!")
                await element.click()
                return element
        except:
            await asyncio.sleep(0.1)  # Very short wait
    
    logger.error(f"❌ {action_name} not found within {timeout}s")
    return None

async def wait_and_type_immediately(tab, element_selector, text, action_name, timeout=10):
    """Wait for element and type immediately when available."""
    logger = logging.getLogger('firebase_reactive')
    start_time = datetime.now()
    
    for attempt in range(int(timeout * 10)):  # Check every 0.1 seconds
        try:
            element = await tab.find(element_selector, timeout=0.1)
            if element:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"⚡ {action_name} found in {elapsed:.2f}s - typing immediately!")
                await element.click()
                await asyncio.sleep(0.1)
                await element.send_keys(text)
                return element
        except:
            await asyncio.sleep(0.1)  # Very short wait
    
    logger.error(f"❌ {action_name} not found within {timeout}s")
    return None

async def main():
    # Setup logging
    logger, log_file = setup_logging()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Firebase Console credentials
    email = "jalexwol@fastmail.com"
    password = "Bcg3!t7W9oPVzCVvBdECvey..MsW*K"
    
    logger.info("=== FIREBASE REACTIVE ULTRA-FAST AUTHENTICATION ===")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Session ID: {timestamp}")
    logger.info(f"Email: {email}")
    
    try:
        # Start timing
        start_time = datetime.now()
        logger.info("Starting visible Chrome with nodriver...")
        
        # Initialize nodriver - VISIBLE for reliability
        browser = await uc.start(
            headless=False,  # Visible for reliability
            no_sandbox=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-infobars',
                '--window-size=1280,720',
                '--disable-web-security'
            ]
        )
        
        logger.info("Navigating to Firebase Console...")
        tab = await browser.get("https://console.firebase.google.com")
        
        # REACTIVE STEP 1: Wait for email field and type immediately
        logger.info("🚀 REACTIVE STEP 1: Waiting for email field...")
        email_field = await wait_and_type_immediately(
            tab, 'input[type="email"]', email, "Email field", timeout=10
        )
        
        if not email_field:
            return {'success': False, 'error': 'Email field not found'}
        
        # Take screenshot after email entry
        email_screenshot = f"images/reactive_01_email_{timestamp}.png"
        await tab.save_screenshot(email_screenshot)
        logger.info(f"📸 Email screenshot: {email_screenshot}")
        
        # REACTIVE STEP 2: Immediately try to proceed
        logger.info("🚀 REACTIVE STEP 2: Proceeding to next step...")
        
        # Try Enter key first (fastest)
        await email_field.send_keys('\n')
        await asyncio.sleep(0.3)  # Minimal wait
        
        # If Enter didn't work, try Next button immediately
        current_url = tab.url
        await asyncio.sleep(0.5)
        if tab.url == current_url:
            logger.info("Enter didn't work, looking for Next button...")
            next_button = await wait_and_click_immediately(
                tab, '#identifierNext', "Next button", timeout=5
            )
        
        # REACTIVE STEP 3: Wait for password field and type immediately
        logger.info("🚀 REACTIVE STEP 3: Waiting for password field...")
        password_field = await wait_and_type_immediately(
            tab, 'input[type="password"]', password, "Password field", timeout=15
        )
        
        if not password_field:
            # Take error screenshot
            error_screenshot = f"images/reactive_error_{timestamp}.png"
            await tab.save_screenshot(error_screenshot)
            logger.info(f"📸 Error screenshot: {error_screenshot}")
            return {'success': False, 'error': 'Password field not found'}
        
        # Take screenshot after password entry
        password_screenshot = f"images/reactive_02_password_{timestamp}.png"
        await tab.save_screenshot(password_screenshot)
        logger.info(f"📸 Password screenshot: {password_screenshot}")
        
        # REACTIVE STEP 4: Immediately submit password
        logger.info("🚀 REACTIVE STEP 4: Submitting password...")
        
        # Try Enter key first (fastest)
        await password_field.send_keys('\n')
        await asyncio.sleep(0.3)  # Minimal wait
        
        # If Enter didn't work, try Next button immediately
        current_url = tab.url
        await asyncio.sleep(0.5)
        if tab.url == current_url:
            logger.info("Enter didn't work, looking for password Next button...")
            next_button = await wait_and_click_immediately(
                tab, '#passwordNext', "Password Next button", timeout=5
            )
        
        # REACTIVE STEP 5: Monitor for authentication completion
        logger.info("🚀 REACTIVE STEP 5: Monitoring authentication...")
        
        # Fast monitoring - check every 0.5 seconds
        for i in range(40):  # 20 seconds max
            await asyncio.sleep(0.5)
            current_url = tab.url
            
            # Quick success checks
            if "console.firebase.google.com" in current_url and "signin" not in current_url:
                logger.info(f"🎯 SUCCESS! Reached Firebase Console in check {i+1}!")
                break
            elif "myaccount.google.com" in current_url:
                logger.info(f"🎯 SUCCESS! Reached Google Account in check {i+1}!")
                break
            elif i % 10 == 0:  # Log every 5 seconds
                logger.info(f"Check {i+1}: Monitoring... {current_url[:60]}...")
        
        # REACTIVE STEP 6: Immediate final screenshot
        logger.info("🚀 REACTIVE STEP 6: Taking final screenshot...")
        final_screenshot = f"images/reactive_03_final_{timestamp}.png"
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
        logger.info(f"⚡ TOTAL TIME: {total_time:.2f} seconds")
        
        # Keep browser open briefly for inspection
        logger.info("Keeping browser open for 5 seconds...")
        await asyncio.sleep(5)
        
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
    print("⚡ FIREBASE REACTIVE ULTRA-FAST AUTHENTICATION SUMMARY")
    print("="*60)
    
    if result and result.get('success'):
        print(f"✅ Status: SUCCESS")
        print(f"📸 Final Screenshot: {result['screenshot']}")
        print(f"⚡ Time: {result['total_time']:.2f} seconds")
        print(f"📋 Log: {result['log_file']}")
        print(f"💬 Details: {result.get('status', 'N/A')}")
        print(f"🌐 URL: {result['final_url'][:60]}...")
    else:
        print(f"❌ Status: FAILED")
        if result:
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
    
    print("="*60) 