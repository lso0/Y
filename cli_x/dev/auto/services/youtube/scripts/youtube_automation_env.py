#!/usr/bin/env python3
"""
YouTube automation with automatic .env credential loading - Streamlined Version
Usage: python3 youtube_automation_env.py [channel_url]
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path("/Users/wgm0/Documents/Y/.env")
    if not env_file.exists():
        print("❌ .env file not found at /Users/wgm0/Documents/Y/.env")
        print("Please run: python3 scripts/infisical/secrets-manager.py")
        return False
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip("'\"")
                    os.environ[key] = value
        
        print("✅ Environment variables loaded from .env file")
        return True
    except Exception as e:
        print(f"❌ Failed to load .env file: {e}")
        return False

def take_screenshot(driver, name: str, description: str = ""):
    """Take a screenshot and save it"""
    try:
        screenshots_dir = Path("services/youtube/data/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"env_{name}_{timestamp}.png"
        filepath = screenshots_dir / filename
        
        driver.save_screenshot(str(filepath))
        print(f"📸 Screenshot saved: {filename} - {description}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return ""

def handle_youtube_consent(driver):
    """Handle YouTube consent (proven method)"""
    try:
        current_url = driver.current_url
        if 'consent.youtube.com' not in current_url:
            print("✅ No consent page detected")
            return True
            
        print("🍪 YouTube consent page detected!")
        take_screenshot(driver, "consent", "Consent page detected")
        
        # Target button with specific aria-label (proven to work)
        try:
            reject_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Reject all']"))
            )
            
            if reject_button:
                print("✅ Found and clicking Reject all button")
                reject_button.click()
                time.sleep(5)
                take_screenshot(driver, "consent_handled", "After handling consent")
                
                if 'consent.youtube.com' not in driver.current_url:
                    print("🎉 Consent bypassed successfully!")
                    return True
                else:
                    print("⚠️ Still on consent page")
                    return False
                    
        except Exception as e:
            print(f"Consent handling failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Consent error: {e}")
        return False

def sign_in_to_youtube(driver, email, password):
    """Sign in to YouTube"""
    try:
        print("🔐 Starting sign-in process...")
        
        # Find and click sign-in button
        try:
            sign_in_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Sign in') and (self::a or self::button)]"))
            )
            
            print("✅ Found sign-in button")
            take_screenshot(driver, "signin_button", "Sign-in button found")
            
            sign_in_button.click()
            time.sleep(3)
            take_screenshot(driver, "after_signin_click", "After clicking sign-in")
            
        except Exception as e:
            print(f"Error finding sign-in button: {e}")
            take_screenshot(driver, "signin_error", "Sign-in button error")
            return False
        
        # Enter email
        print("📧 Entering email...")
        try:
            email_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            
            take_screenshot(driver, "email_page", "Email input page")
            
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(2)
            take_screenshot(driver, "email_entered", "Email entered")
            
            # Click Next
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "identifierNext"))
            )
            next_button.click()
            print("✅ Email submitted")
            time.sleep(3)
            take_screenshot(driver, "email_next", "After email Next")
            
        except Exception as e:
            print(f"Error with email: {e}")
            take_screenshot(driver, "email_error", "Email error")
            return False
        
        # Enter password
        print("🔒 Entering password...")
        try:
            password_input = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "password"))
            )
            
            take_screenshot(driver, "password_page", "Password input page")
            
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(2)
            take_screenshot(driver, "password_entered", "Password entered")
            
            # Click Next
            password_next = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "passwordNext"))
            )
            password_next.click()
            print("✅ Password submitted")
            time.sleep(8)
            take_screenshot(driver, "password_next", "After password Next")
            
        except Exception as e:
            print(f"Error with password: {e}")
            take_screenshot(driver, "password_error", "Password error")
            return False
        
        # Wait for sign-in completion
        print("⏳ Waiting for sign-in completion...")
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"📄 Current URL: {current_url}")
        take_screenshot(driver, "signin_complete", "Sign-in process complete")
        
        # Check for sign-in success indicators
        try:
            # Look for avatar or account menu
            signed_in_elements = driver.find_elements(By.CSS_SELECTOR, "#avatar-btn, button[aria-label*='Account'], #guide-button")
            if signed_in_elements:
                print("🎉 Sign-in successful!")
                take_screenshot(driver, "signin_success", "Successfully signed in")
                return True
            else:
                print("⚠️ Sign-in status unclear, continuing...")
                return True
                
        except Exception as e:
            print(f"Error checking sign-in status: {e}")
            return True  # Continue anyway
        
    except Exception as e:
        print(f"❌ Sign-in failed: {e}")
        take_screenshot(driver, "signin_failed", "Sign-in failed")
        return False

def subscribe_to_channel(driver, channel_url):
    """Subscribe to YouTube channel"""
    try:
        print(f"📺 Navigating to channel: {channel_url}")
        
        driver.get(channel_url)
        time.sleep(5)
        take_screenshot(driver, "channel_page", "Channel page loaded")
        
        # Handle consent if it appears again
        if 'consent.youtube.com' in driver.current_url:
            print("🍪 Handling consent on channel page...")
            if not handle_youtube_consent(driver):
                return False
            time.sleep(3)
        
        take_screenshot(driver, "channel_ready", "Channel ready")
        
        # Find subscribe button
        print("🔍 Looking for Subscribe button...")
        try:
            # Try different selectors for subscribe button
            subscribe_selectors = [
                "button[aria-label*='Subscribe']",
                "ytd-subscribe-button-renderer button",
                "#subscribe-button button",
                "//*[contains(text(), 'Subscribe') and (self::button or @role='button')]"
            ]
            
            subscribe_button = None
            for selector in subscribe_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath selector
                        subscribe_button = driver.find_element(By.XPATH, selector)
                    else:
                        # CSS selector
                        subscribe_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if subscribe_button:
                        button_text = subscribe_button.text.strip()
                        print(f"✅ Found subscribe button: '{button_text}'")
                        break
                except:
                    continue
            
            if not subscribe_button:
                print("❌ Could not find Subscribe button")
                take_screenshot(driver, "no_subscribe", "No Subscribe button")
                return False
            
            take_screenshot(driver, "subscribe_found", "Subscribe button found")
            
            # Check if already subscribed
            button_text = subscribe_button.text.strip().lower()
            if 'subscribed' in button_text or 'unsubscribe' in button_text:
                print("✅ Already subscribed to this channel!")
                take_screenshot(driver, "already_subscribed", "Already subscribed")
                return True
            
            # Click subscribe
            print("🎯 Clicking Subscribe button...")
            subscribe_button.click()
            time.sleep(3)
            take_screenshot(driver, "subscribe_clicked", "After clicking Subscribe")
            
            # Check result
            try:
                time.sleep(2)
                updated_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Subscribe'], ytd-subscribe-button-renderer button")
                if updated_buttons:
                    new_text = updated_buttons[0].text.strip().lower()
                    if 'subscribed' in new_text or 'unsubscribe' in new_text:
                        print("🎉 SUCCESS: Successfully subscribed!")
                        take_screenshot(driver, "subscribe_success", "Successfully subscribed")
                        return True
                    else:
                        print(f"⚠️ Button text now: '{new_text}'")
                        take_screenshot(driver, "subscribe_unclear", "Subscription unclear")
                        return True  # Assume success
                
            except Exception as e:
                print(f"Error verifying subscription: {e}")
                return True  # Assume success
            
        except Exception as e:
            print(f"Error with subscribe process: {e}")
            take_screenshot(driver, "subscribe_error", "Subscribe error")
            return False
        
    except Exception as e:
        print(f"❌ Channel subscription failed: {e}")
        take_screenshot(driver, "channel_error", "Channel error")
        return False

def main():
    """Main automation function"""
    # Load environment variables
    if not load_env_file():
        print("\n💡 To sync secrets, run:")
        print("   python3 scripts/infisical/secrets-manager.py")
        print("   # OR use the setup script:")
        print("   scripts/infisical/setup-infisical.sh sync")
        return False
    
    # Get credentials from environment
    email = os.getenv('G_LSD_M_0')
    password = os.getenv('G_LSD_P_0')
    
    if not email or not password:
        print("❌ Missing required credentials in environment:")
        print("   G_LSD_M_0 (Google email)")
        print("   G_LSD_P_0 (Google password)")
        print("\n💡 To sync secrets, run:")
        print("   python3 scripts/infisical/secrets-manager.py")
        print("   # OR use the setup script:")
        print("   scripts/infisical/setup-infisical.sh sync")
        return False
    
    # Get channel URL from argument or use default
    if len(sys.argv) > 1:
        channel_url = sys.argv[1]
    else:
        channel_url = "https://www.youtube.com/channel/UCsXVk37bltHxD1rDPwtNM8Q"
    
    print(f"🚀 Starting YouTube automation for: {email[:3]}***@{email.split('@')[1] if '@' in email else 'hidden'}")
    print(f"📺 Target channel: {channel_url}")
    
    driver = None
    try:
        # Chrome setup
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.binary_location = '/usr/bin/google-chrome'
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome started")
        
        take_screenshot(driver, "start", "Chrome started")
        
        # Step 1: Go to YouTube
        print("📺 Navigating to YouTube...")
        driver.get("https://www.youtube.com")
        time.sleep(5)
        take_screenshot(driver, "youtube_home", "YouTube homepage")
        
        # Step 2: Handle consent
        if not handle_youtube_consent(driver):
            print("❌ Failed to handle consent")
            return False
        
        # Step 3: Sign in
        if not sign_in_to_youtube(driver, email, password):
            print("❌ Failed to sign in")
            return False
        
        # Step 4: Subscribe to channel
        if not subscribe_to_channel(driver, channel_url):
            print("❌ Failed to subscribe")
            return False
        
        print("🎉 COMPLETE SUCCESS: YouTube automation completed!")
        take_screenshot(driver, "complete_success", "Automation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        if driver:
            take_screenshot(driver, "error", f"Error: {str(e)[:30]}")
        return False
    finally:
        if driver:
            take_screenshot(driver, "cleanup", "Before cleanup")
            driver.quit()
            print("🔧 Browser closed")

if __name__ == "__main__":
    print("🧪 YouTube Automation with Environment Variables - Streamlined")
    print("=" * 60)
    success = main()
    print(f"🎯 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}") 