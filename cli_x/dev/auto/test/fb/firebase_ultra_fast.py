#!/usr/bin/env python3
"""
Ultra-fast headless Firebase Console authentication script.
Optimized for maximum speed with better authentication handling.
"""

import asyncio
import nodriver as uc
import os
import logging
from datetime import datetime

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/firebase_ultra_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('firebase_ultra')
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
    
    logger.info("=== FIREBASE ULTRA-FAST AUTHENTICATION ===")
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
                '--disable-backgrounding-occluded-windows',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        logger.info("Navigating to Firebase Console...")
        tab = await browser.get("https://console.firebase.google.com")
        
        # Minimal wait - just enough for page structure
        await asyncio.sleep(0.8)
        
        logger.info("Looking for email input field...")
        email_field = await tab.find('input[type="email"]', timeout=6)
        
        if email_field:
            logger.info("Email field found - entering email...")
            await email_field.click()
            await asyncio.sleep(0.1)
            await email_field.send_keys(email)
            
            # Use Enter key (fastest method)
            logger.info("Proceeding with Enter key...")
            await email_field.send_keys('\n')
            await asyncio.sleep(1.2)  # Minimal wait
            
            logger.info("Looking for password input field...")
            password_field = await tab.find('input[type="password"]', timeout=6)
            
            if password_field:
                logger.info("Password field found - entering password...")
                await password_field.click()
                await asyncio.sleep(0.1)
                await password_field.send_keys(password)
                
                # Use Enter key for fastest submission
                logger.info("Submitting with Enter key...")
                await password_field.send_keys('\n')
                
                # Wait longer for authentication and potential redirects
                logger.info("Waiting for authentication to complete...")
                
                # Check URL changes over time to detect successful login
                for i in range(8):  # Check 8 times over 8 seconds
                    await asyncio.sleep(1)
                    current_url = tab.url
                    logger.info(f"Check {i+1}: {current_url[:80]}...")
                    
                    # If we see Firebase console URL, we're likely logged in
                    if "console.firebase.google.com" in current_url and "signin" not in current_url:
                        logger.info("🎯 Detected successful redirect to Firebase Console!")
                        break
                    elif "myaccount.google.com" in current_url:
                        logger.info("🎯 Detected Google Account page - likely authenticated!")
                        break
                    elif i == 7:  # Last check
                        logger.info("⏰ Max wait time reached")
                
                # Take final screenshot of current state
                final_screenshot = f"images/firebase_ultra_{timestamp}.png"
                await tab.save_screenshot(final_screenshot, full_page=True)
                
                # Calculate total time
                end_time = datetime.now()
                total_time = (end_time - start_time).total_seconds()
                
                # Final URL check
                final_url = tab.url
                logger.info(f"🌐 Final URL: {final_url}")
                
                # Determine success based on URL
                success = False
                if "console.firebase.google.com" in final_url and "signin" not in final_url:
                    success = True
                    status_msg = "✅ Successfully authenticated to Firebase Console!"
                elif "myaccount.google.com" in final_url:
                    success = True
                    status_msg = "✅ Successfully authenticated to Google (Firebase accessible)!"
                elif "accounts.google.com" not in final_url:
                    success = True
                    status_msg = "✅ Authentication completed - navigated away from login!"
                else:
                    status_msg = "⚠️  Still on authentication page - may need manual verification"
                
                logger.info(status_msg)
                logger.info(f"📸 Screenshot saved: {final_screenshot}")
                logger.info(f"⚡ Total time: {total_time:.2f} seconds")
                
                return {
                    'success': success,
                    'screenshot': final_screenshot,
                    'total_time': total_time,
                    'final_url': final_url,
                    'log_file': log_file,
                    'status': status_msg
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
    
    print("\n" + "="*60)
    print("🚀 FIREBASE ULTRA-FAST AUTHENTICATION SUMMARY")
    print("="*60)
    
    if result and result.get('success'):
        print(f"✅ Status: SUCCESS")
        print(f"📸 Screenshot: {result['screenshot']}")
        print(f"⚡ Time: {result['total_time']:.2f} seconds")
        print(f"📋 Log: {result['log_file']}")
        print(f"💬 Details: {result.get('status', 'N/A')}")
        print(f"🌐 URL: {result['final_url'][:100]}...")
    else:
        print(f"❌ Status: FAILED")
        if result:
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
    
    print("="*60) 