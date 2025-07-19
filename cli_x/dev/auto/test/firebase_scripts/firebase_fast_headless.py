#!/usr/bin/env python3
"""
Fast headless Firebase Console authentication script.
Optimized for speed with organized logging and image storage.
"""

import asyncio
import nodriver as uc
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/firebase_auth_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('firebase_auth')
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
    
    logger.info("=== FIREBASE FAST HEADLESS AUTHENTICATION ===")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Session ID: {timestamp}")
    logger.info(f"Email: {email}")
    
    try:
        # Start timing
        start_time = datetime.now()
        logger.info("Starting headless Chrome with nodriver...")
        
        # Initialize nodriver - HEADLESS for speed
        browser = await uc.start(
            headless=True,  # HEADLESS for maximum speed
            no_sandbox=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows'
            ]
        )
        
        logger.info("Navigating to Firebase Console...")
        tab = await browser.get("https://console.firebase.google.com")
        
        # Minimal wait - just enough for page structure
        await asyncio.sleep(1)
        
        logger.info("Looking for email input field...")
        email_field = await tab.find('input[type="email"]', timeout=8)
        
        if email_field:
            logger.info("Email field found - entering email...")
            await email_field.click()
            await email_field.send_keys(email)
            
            # Try Enter key first (fastest method)
            logger.info("Attempting to proceed with Enter key...")
            await email_field.send_keys('\n')
            await asyncio.sleep(1.5)  # Minimal wait
            
            logger.info("Looking for password input field...")
            password_field = await tab.find('input[type="password"]', timeout=8)
            
            if password_field:
                logger.info("Password field found - entering password...")
                await password_field.click()
                await password_field.send_keys(password)
                
                # Use Enter key for fastest submission
                logger.info("Submitting with Enter key...")
                await password_field.send_keys('\n')
                
                # Wait for authentication and redirect
                logger.info("Waiting for authentication to complete...")
                await asyncio.sleep(3)
                
                # Check if we're successfully logged in
                current_url = tab.url
                logger.info(f"Current URL: {current_url}")
                
                # Take final screenshot of authenticated state
                final_screenshot = f"images/firebase_authenticated_{timestamp}.png"
                await tab.save_screenshot(final_screenshot, full_page=True)
                
                # Calculate total time
                end_time = datetime.now()
                total_time = (end_time - start_time).total_seconds()
                
                logger.info("✅ AUTHENTICATION COMPLETED!")
                logger.info(f"📸 Screenshot saved: {final_screenshot}")
                logger.info(f"⚡ Total time: {total_time:.2f} seconds")
                logger.info(f"🌐 Final URL: {current_url}")
                
                # Get page title for verification
                try:
                    page_title = await tab.get_content()
                    if "Firebase" in str(page_title):
                        logger.info("✅ Successfully authenticated to Firebase Console")
                    else:
                        logger.warning("⚠️  Authentication status unclear")
                except:
                    logger.info("📋 Page content check skipped")
                
                return {
                    'success': True,
                    'screenshot': final_screenshot,
                    'total_time': total_time,
                    'final_url': current_url,
                    'log_file': log_file
                }
                
            else:
                logger.error("❌ Password field not found")
                return {'success': False, 'error': 'Password field not found'}
        else:
            logger.error("❌ Email field not found")
            return {'success': False, 'error': 'Email field not found'}
        
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
    
    print("\n" + "="*50)
    print("FIREBASE FAST AUTHENTICATION SUMMARY")
    print("="*50)
    
    if result and result.get('success'):
        print(f"✅ Status: SUCCESS")
        print(f"📸 Screenshot: {result['screenshot']}")
        print(f"⚡ Time: {result['total_time']:.2f} seconds")
        print(f"🌐 URL: {result['final_url']}")
        print(f"📋 Log: {result['log_file']}")
    else:
        print(f"❌ Status: FAILED")
        if result:
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
    
    print("="*50) 