#!/usr/bin/env python3
"""
App Store Connect Login Automation
==================================

This script automates the login process for App Store Connect using nodriver.
It handles Apple ID authentication, potential 2FA, and navigates to the main ASC dashboard.

Features:
- Visible browser mode for reliability and 2FA handling
- Automatic screenshot capture at key steps
- Detailed logging with timestamps
- Error handling and recovery
- Support for 2FA verification

Usage:
    python asc/asc_login_nodriver.py
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
    
    log_file = f"logs/asc_login_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('asc_login')
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
        logger.info(f"📸 Screenshot saved: {filename}")
        
        return filename
    except Exception as e:
        logger.error(f"❌ Error taking screenshot: {e}")
        return None

async def wait_for_element(tab, selector: str, timeout: int = 15, logger=None):
    """Wait for an element to appear and return it."""
    try:
        if logger:
            logger.info(f"🔍 Waiting for element: {selector}")
        
        element = await tab.find(selector, timeout=timeout)
        if element:
            if logger:
                logger.info(f"✅ Element found: {selector}")
            return element
        else:
            if logger:
                logger.warning(f"⚠️ Element not found: {selector}")
            return None
            
    except Exception as e:
        if logger:
            logger.error(f"❌ Error waiting for element {selector}: {e}")
        return None

async def asc_login_automation(email: str, password: str, logger):
    """
    Perform App Store Connect login automation.
    
    Args:
        email: Apple ID email
        password: Apple ID password
        logger: Logger instance
    
    Returns:
        bool: True if login successful, False otherwise
    """
    logger.info("=== APP STORE CONNECT LOGIN AUTOMATION ===")
    logger.info(f"Apple ID: {email}")
    logger.info(f"Target: App Store Connect Console")
    
    browser = None
    
    try:
        # Start visible browser (important for 2FA and Apple's detection)
        logger.info("🚀 Starting visible browser...")
        browser = await uc.start(
            headless=False,  # Visible mode for 2FA and security
            no_sandbox=True,
            args=[
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--window-size=1280,720',
                '--disable-web-security',  # Sometimes needed for Apple sites
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Navigate to App Store Connect
        logger.info("🌐 Navigating to App Store Connect...")
        tab = await browser.get("https://appstoreconnect.apple.com")
        
        # Take initial screenshot
        await take_screenshot(tab, "asc_01_initial", logger)
        await asyncio.sleep(2)
        
        # Look for sign-in button/link
        logger.info("🔍 Looking for sign-in options...")
        
        # Try different sign-in selectors
        sign_in_selectors = [
            'a[href*="signin"]',
            'button:contains("Sign In")',
            'a:contains("Sign In")',
            '.signin-button',
            '#signin',
            '[data-testid="signin"]'
        ]
        
        sign_in_element = None
        for selector in sign_in_selectors:
            sign_in_element = await wait_for_element(tab, selector, timeout=5, logger=logger)
            if sign_in_element:
                break
        
        if sign_in_element:
            logger.info("✅ Found sign-in button, clicking...")
            await sign_in_element.click()
            await asyncio.sleep(3)
        else:
            logger.info("ℹ️ No sign-in button found, checking if already on login page...")
        
        # Take screenshot after clicking sign-in
        await take_screenshot(tab, "asc_02_signin_clicked", logger)
        
        # Wait for email field (Apple ID login page)
        logger.info("📧 Looking for Apple ID email field...")
        email_field = await wait_for_element(tab, 'input[type="email"]', timeout=15, logger=logger)
        
        if not email_field:
            # Try alternative selectors for Apple ID field
            email_selectors = [
                'input[name="accountName"]',
                'input[id="account_name_text_field"]',
                'input[placeholder*="Apple ID"]',
                '#appleId',
                'input[autocomplete="username"]'
            ]
            
            for selector in email_selectors:
                email_field = await wait_for_element(tab, selector, timeout=5, logger=logger)
                if email_field:
                    break
        
        if not email_field:
            logger.error("❌ Email field not found!")
            return False
        
        # Enter email
        logger.info("✏️ Entering Apple ID email...")
        await email_field.click()
        await asyncio.sleep(0.5)
        await email_field.send_keys(email)
        await asyncio.sleep(1)
        
        # Take screenshot after entering email
        await take_screenshot(tab, "asc_03_email_entered", logger)
        
        # Look for "Continue" or "Next" button
        logger.info("▶️ Looking for Continue/Next button...")
        continue_selectors = [
            'button:contains("Continue")',
            'button:contains("Next")',
            'input[type="submit"]',
            '#sign-in',
            '.signin-button',
            'button[type="submit"]'
        ]
        
        continue_button = None
        for selector in continue_selectors:
            continue_button = await wait_for_element(tab, selector, timeout=5, logger=logger)
            if continue_button:
                break
        
        if continue_button:
            logger.info("✅ Found Continue button, clicking...")
            await continue_button.click()
        else:
            # Try pressing Enter on email field
            logger.info("📧 Trying Enter key on email field...")
            await email_field.send_keys('\n')
        
        await asyncio.sleep(3)
        
        # Wait for password field
        logger.info("🔒 Looking for password field...")
        password_field = await wait_for_element(tab, 'input[type="password"]', timeout=15, logger=logger)
        
        if not password_field:
            logger.error("❌ Password field not found!")
            return False
        
        # Enter password
        logger.info("✏️ Entering password...")
        await password_field.click()
        await asyncio.sleep(0.5)
        await password_field.send_keys(password)
        await asyncio.sleep(1)
        
        # Take screenshot after entering password
        await take_screenshot(tab, "asc_04_password_entered", logger)
        
        # Look for sign-in button
        logger.info("🔐 Looking for sign-in submit button...")
        signin_selectors = [
            'button:contains("Sign In")',
            'input[type="submit"]',
            'button[type="submit"]',
            '#sign-in',
            '.signin-button'
        ]
        
        signin_button = None
        for selector in signin_selectors:
            signin_button = await wait_for_element(tab, selector, timeout=5, logger=logger)
            if signin_button:
                break
        
        if signin_button:
            logger.info("✅ Found sign-in button, clicking...")
            await signin_button.click()
        else:
            # Try pressing Enter on password field
            logger.info("🔒 Trying Enter key on password field...")
            await password_field.send_keys('\n')
        
        await asyncio.sleep(5)
        
        # Take screenshot after clicking sign-in
        await take_screenshot(tab, "asc_05_signin_submitted", logger)
        
        # Check for 2FA or additional verification
        logger.info("🔐 Checking for 2FA or additional verification...")
        
        # Wait and check URL for success or 2FA
        current_url = tab.url
        logger.info(f"📍 Current URL: {current_url}")
        
        # Check if we're on App Store Connect dashboard or need 2FA
        if "appstoreconnect.apple.com" in current_url and "signin" not in current_url.lower():
            logger.info("✅ Successfully logged into App Store Connect!")
            await take_screenshot(tab, "asc_06_success", logger)
            return True
        
        # Check for 2FA indicators
        two_fa_indicators = [
            "two-factor",
            "verification",
            "authenticate",
            "verify",
            "code"
        ]
        
        page_text = ""
        try:
            page_text = await tab.evaluate("document.body.innerText.toLowerCase()")
        except:
            pass
        
        if any(indicator in current_url.lower() or indicator in page_text for indicator in two_fa_indicators):
            logger.info("🔐 2FA/Verification detected!")
            logger.info("⚠️ Please complete 2FA verification manually in the browser")
            logger.info("⏳ Waiting for manual 2FA completion (60 seconds)...")
            
            await take_screenshot(tab, "asc_07_2fa_detected", logger)
            
            # Wait for user to complete 2FA
            wait_time = 60
            for i in range(wait_time):
                await asyncio.sleep(1)
                current_url = tab.url
                
                if "appstoreconnect.apple.com" in current_url and "signin" not in current_url.lower():
                    logger.info("✅ 2FA completed! Successfully logged into App Store Connect!")
                    await take_screenshot(tab, "asc_08_2fa_success", logger)
                    return True
                
                if i % 10 == 0:  # Log every 10 seconds
                    logger.info(f"⏳ Still waiting for 2FA... ({wait_time - i} seconds remaining)")
            
            logger.warning("⚠️ 2FA wait timeout. Please check if login was successful.")
        
        # Final check
        current_url = tab.url
        if "appstoreconnect.apple.com" in current_url and "signin" not in current_url.lower():
            logger.info("✅ Login appears successful!")
            await take_screenshot(tab, "asc_09_final_check", logger)
            return True
        else:
            logger.error(f"❌ Login may have failed. Final URL: {current_url}")
            await take_screenshot(tab, "asc_10_final_failure", logger)
            return False
    
    except Exception as e:
        logger.error(f"❌ Error during login automation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        if browser:
            try:
                await take_screenshot(browser.tabs[0], "asc_error", logger)
            except:
                pass
        
        return False
    
    finally:
        # Keep browser open for manual interaction
        logger.info("🌐 Keeping browser open for manual interaction...")
        logger.info("📋 Press Ctrl+C to close browser and exit")
        
        try:
            # Wait indefinitely until user interrupts
            while True:
                await asyncio.sleep(5)
                # Check if browser is still alive
                if browser and browser.tabs:
                    current_url = browser.tabs[0].url
                    if "appstoreconnect.apple.com" in current_url:
                        # We're on ASC, just wait
                        pass
                else:
                    break
        except KeyboardInterrupt:
            logger.info("🛑 User interrupted, closing browser...")
        except Exception as e:
            logger.error(f"Error in browser maintenance: {e}")
        
        # Close browser
        if browser:
            try:
                await browser.stop()
                logger.info("🔒 Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

async def main():
    """Main function to run the App Store Connect login automation."""
    # Setup logging
    logger, log_file = setup_logging()
    
    # App Store Connect credentials
    # TODO: Replace with your Apple ID credentials
    email = "wiktor11gal@gmail.com"  # Replace with your Apple ID
    password = "FVqKwV9XceWirEGLJaabMY-6Evc3nG"  # Replace with your password
    
    logger.info("=== APP STORE CONNECT LOGIN AUTOMATION STARTED ===")
    logger.info(f"📋 Log file: {log_file}")
    logger.info("🚀 Starting automation...")
    
    # Check if credentials are set
    if email == "your-apple-id@example.com":
        logger.error("❌ Please update the email and password in the script!")
        logger.error("📝 Edit the script and replace 'your-apple-id@example.com' with your Apple ID")
        return
    
    try:
        start_time = datetime.now()
        
        # Run the login automation
        success = await asc_login_automation(email, password, logger)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if success:
            logger.info(f"✅ App Store Connect login completed successfully in {duration:.1f} seconds!")
            logger.info("🎉 You should now be logged into App Store Connect")
        else:
            logger.error(f"❌ App Store Connect login failed after {duration:.1f} seconds")
            logger.error("💡 Check the screenshots and logs for troubleshooting")
        
        logger.info(f"📸 Screenshots saved in: images/")
        logger.info(f"📋 Full log saved in: {log_file}")
        
    except KeyboardInterrupt:
        logger.info("🛑 Automation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted by user")
        sys.exit(0) 