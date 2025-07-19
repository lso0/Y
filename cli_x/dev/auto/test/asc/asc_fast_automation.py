#!/usr/bin/env python3
"""
App Store Connect Fast Automation
=================================

This script provides fast automation for App Store Connect login.
It's optimized for speed but may require manual 2FA handling.

Features:
- Faster execution with minimal waits
- Reactive element detection
- Basic 2FA detection (manual completion required)
- Automated screenshot capture
- Production-ready automation

Usage:
    python asc/asc_fast_automation.py
"""

import asyncio
import nodriver as uc
import os
import logging
from datetime import datetime
import sys

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    log_file = f"logs/asc_fast_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('asc_fast')
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

async def take_screenshot(tab, filename_prefix: str, logger):
    """Take a screenshot and save it with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create images directory if it doesn't exist
        os.makedirs("images", exist_ok=True)
        
        filename = f"images/{filename_prefix}_{timestamp}.png"
        
        # Take screenshot
        await tab.save_screenshot(filename)
        logger.info(f"📸 Screenshot: {filename}")
        
        return filename
    except Exception as e:
        logger.error(f"❌ Screenshot error: {e}")
        return None

async def wait_for_element_reactive(tab, selectors: list, timeout: int = 10, logger=None):
    """
    Reactively wait for any of multiple selectors to appear.
    Checks every 0.1 seconds for maximum responsiveness.
    """
    if isinstance(selectors, str):
        selectors = [selectors]
    
    if logger:
        logger.info(f"🔍 Reactive search for: {selectors[0]}...")
    
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        for selector in selectors:
            try:
                element = await tab.find(selector, timeout=0.1)
                if element:
                    if logger:
                        logger.info(f"✅ Found: {selector}")
                    return element
            except:
                continue
        
        await asyncio.sleep(0.1)  # Fast polling
    
    if logger:
        logger.warning(f"⚠️ Elements not found after {timeout}s")
    return None

async def asc_fast_automation(email: str, password: str, logger):
    """
    Fast App Store Connect login automation.
    
    Args:
        email: Apple ID email
        password: Apple ID password
        logger: Logger instance
    
    Returns:
        bool: True if login successful, False otherwise
    """
    logger.info("=== APP STORE CONNECT FAST AUTOMATION ===")
    logger.info(f"Apple ID: {email}")
    logger.info("🚀 Optimized for speed")
    
    browser = None
    
    try:
        # Start browser with speed-optimized settings
        logger.info("🚀 Starting browser (speed mode)...")
        browser = await uc.start(
            headless=False,  # Keep visible for 2FA
            no_sandbox=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-images',  # Speed optimization
                '--disable-javascript-harmony-shipping',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--window-size=1280,720',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Navigate to App Store Connect
        logger.info("🌐 Navigating to ASC...")
        tab = await browser.get("https://appstoreconnect.apple.com")
        
        await take_screenshot(tab, "fast_01_initial", logger)
        await asyncio.sleep(1)  # Minimal wait
        
        # Look for sign-in (reactive)
        logger.info("🔍 Finding sign-in...")
        sign_in_selectors = [
            'a[href*="signin"]',
            'button:contains("Sign In")',
            'a:contains("Sign In")',
            '.signin-button'
        ]
        
        sign_in_element = await wait_for_element_reactive(tab, sign_in_selectors, timeout=8, logger=logger)
        
        if sign_in_element:
            logger.info("✅ Clicking sign-in...")
            await sign_in_element.click()
            await asyncio.sleep(1.5)
        
        # Fast email field detection
        logger.info("📧 Finding email field...")
        email_selectors = [
            'input[type="email"]',
            'input[name="accountName"]',
            'input[id="account_name_text_field"]',
            'input[autocomplete="username"]'
        ]
        
        email_field = await wait_for_element_reactive(tab, email_selectors, timeout=10, logger=logger)
        
        if not email_field:
            logger.error("❌ Email field not found!")
            return False
        
        # Enter email quickly
        logger.info("✏️ Entering email...")
        await email_field.click()
        await asyncio.sleep(0.2)
        await email_field.send_keys(email)
        
        await take_screenshot(tab, "fast_02_email", logger)
        
        # Fast continue button detection
        continue_selectors = [
            'button:contains("Continue")',
            'button:contains("Next")',
            'input[type="submit"]',
            'button[type="submit"]'
        ]
        
        continue_button = await wait_for_element_reactive(tab, continue_selectors, timeout=5, logger=logger)
        
        if continue_button:
            logger.info("▶️ Clicking continue...")
            await continue_button.click()
        else:
            logger.info("📧 Using Enter key...")
            await email_field.send_keys('\n')
        
        await asyncio.sleep(2)
        
        # Fast password field detection
        logger.info("🔒 Finding password field...")
        password_field = await wait_for_element_reactive(tab, ['input[type="password"]'], timeout=10, logger=logger)
        
        if not password_field:
            logger.error("❌ Password field not found!")
            return False
        
        # Enter password quickly
        logger.info("✏️ Entering password...")
        await password_field.click()
        await asyncio.sleep(0.2)
        await password_field.send_keys(password)
        
        await take_screenshot(tab, "fast_03_password", logger)
        
        # Fast sign-in button detection
        signin_selectors = [
            'button:contains("Sign In")',
            'input[type="submit"]',
            'button[type="submit"]'
        ]
        
        signin_button = await wait_for_element_reactive(tab, signin_selectors, timeout=5, logger=logger)
        
        if signin_button:
            logger.info("🔐 Submitting login...")
            await signin_button.click()
        else:
            logger.info("🔒 Using Enter key...")
            await password_field.send_keys('\n')
        
        await asyncio.sleep(3)
        
        # Quick success/2FA check
        current_url = tab.url
        logger.info(f"📍 URL: {current_url}")
        
        await take_screenshot(tab, "fast_04_submitted", logger)
        
        # Check for immediate success
        if "appstoreconnect.apple.com" in current_url and "signin" not in current_url.lower():
            logger.info("✅ Fast login successful!")
            await take_screenshot(tab, "fast_05_success", logger)
            return True
        
        # Quick 2FA check
        page_text = ""
        try:
            page_text = await tab.evaluate("document.body.innerText.toLowerCase()")
        except:
            pass
        
        two_fa_keywords = ["verify", "code", "authentication", "factor"]
        if any(keyword in current_url.lower() or keyword in page_text for keyword in two_fa_keywords):
            logger.info("🔐 2FA detected - manual completion required")
            logger.info("⏳ Waiting 30 seconds for manual 2FA...")
            
            await take_screenshot(tab, "fast_06_2fa", logger)
            
            # Shorter 2FA wait (30 seconds)
            for i in range(30):
                await asyncio.sleep(1)
                current_url = tab.url
                
                if "appstoreconnect.apple.com" in current_url and "signin" not in current_url.lower():
                    logger.info("✅ 2FA completed!")
                    await take_screenshot(tab, "fast_07_2fa_success", logger)
                    return True
                
                if i % 10 == 0 and i > 0:
                    logger.info(f"⏳ 2FA wait: {30-i}s remaining")
        
        # Final quick check
        current_url = tab.url
        if "appstoreconnect.apple.com" in current_url and "signin" not in current_url.lower():
            logger.info("✅ Login successful!")
            await take_screenshot(tab, "fast_08_final", logger)
            return True
        else:
            logger.error(f"❌ Login failed. URL: {current_url}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Fast automation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    finally:
        # Keep browser open briefly
        logger.info("🌐 Keeping browser open (30 seconds)...")
        logger.info("📋 Press Ctrl+C to close immediately")
        
        try:
            # Shorter wait time for fast mode
            for i in range(30):
                await asyncio.sleep(1)
                if i % 10 == 0 and i > 0:
                    logger.info(f"⏳ Auto-close in {30-i} seconds...")
        except KeyboardInterrupt:
            logger.info("🛑 User interrupted")
        
        # Close browser
        if browser:
            try:
                await browser.stop()
                logger.info("🔒 Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

async def main():
    """Main function for fast automation."""
    # Setup logging
    logger, log_file = setup_logging()
    
    # Credentials - TODO: Replace with your Apple ID
    email = "your-apple-id@example.com"  # Replace with your Apple ID
    password = "your-password"  # Replace with your password
    
    logger.info("=== APP STORE CONNECT FAST AUTOMATION ===")
    logger.info(f"📋 Log: {log_file}")
    
    # Check if credentials are set
    if email == "your-apple-id@example.com":
        logger.error("❌ Please update credentials in the script!")
        logger.error("📝 Edit asc_fast_automation.py and update email/password")
        return
    
    try:
        start_time = datetime.now()
        
        # Run fast automation
        success = await asc_fast_automation(email, password, logger)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if success:
            logger.info(f"✅ Fast automation completed in {duration:.1f}s!")
            logger.info("🎉 App Store Connect login successful")
        else:
            logger.error(f"❌ Fast automation failed after {duration:.1f}s")
        
        logger.info(f"📸 Screenshots: images/")
        logger.info(f"📋 Log: {log_file}")
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted")
        sys.exit(0) 