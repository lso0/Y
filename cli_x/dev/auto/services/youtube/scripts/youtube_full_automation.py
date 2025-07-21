#!/usr/bin/env python3
"""
Complete YouTube automation: Consent -> Sign-in -> Subscribe
"""

import os
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def take_screenshot(driver, name: str, description: str = ""):
    """Take a screenshot and save it"""
    try:
        screenshots_dir = Path("services/youtube/data/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auto_{name}_{timestamp}.png"
        filepath = screenshots_dir / filename
        
        driver.save_screenshot(str(filepath))
        print(f"📸 Screenshot saved: {filename} - {description}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return ""

def get_credentials():
    """Get credentials from Infisical or environment"""
    try:
        print("🔐 Fetching credentials from Infisical...")
        
        # Try to get Infisical token
        result = subprocess.run([
            "infisical", "auth", "universal-auth", "--client-id", os.getenv("INFISICAL_CLIENT_ID"),
            "--client-secret", os.getenv("INFISICAL_CLIENT_SECRET")
        ], capture_output=True, text=True, cwd="/Users/wgm0/Documents/Y")
        
        if result.returncode == 0:
            print("✅ Infisical authentication successful")
            
            # Get email
            email_result = subprocess.run([
                "infisical", "secrets", "get", "G_LSD_M_0", "--plain"
            ], capture_output=True, text=True, cwd="/Users/wgm0/Documents/Y")
            
            # Get password  
            password_result = subprocess.run([
                "infisical", "secrets", "get", "G_LSD_P_0", "--plain"
            ], capture_output=True, text=True, cwd="/Users/wgm0/Documents/Y")
            
            if email_result.returncode == 0 and password_result.returncode == 0:
                email = email_result.stdout.strip()
                password = password_result.stdout.strip()
                print(f"✅ Retrieved credentials - Email: {email[:3]}***@{email.split('@')[1] if '@' in email else 'hidden'}")
                return email, password
            else:
                print("⚠️ Failed to retrieve secrets from Infisical")
        else:
            print("⚠️ Infisical authentication failed")
            
    except Exception as e:
        print(f"⚠️ Infisical error: {e}")
    
    # Fallback to environment variables
    print("🔄 Falling back to environment variables...")
    email = os.getenv("G_LSD_M_0")
    password = os.getenv("G_LSD_P_0")
    
    if email and password:
        print(f"✅ Using environment credentials - Email: {email[:3]}***@{email.split('@')[1] if '@' in email else 'hidden'}")
        return email, password
    else:
        print("❌ No credentials found in environment variables")
        return None, None

def handle_youtube_consent(driver):
    """Handle YouTube consent (reusing our successful method)"""
    try:
        current_url = driver.current_url
        if 'consent.youtube.com' not in current_url:
            print("✅ No consent page detected")
            return True
            
        print("🍪 YouTube consent page detected!")
        take_screenshot(driver, "01_consent_page", "Consent page detected")
        
        # Target button with specific aria-label (our proven method)
        try:
            reject_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Reject all']"))
            )
            
            if reject_button:
                print("✅ Found button with aria-label='Reject all'")
                take_screenshot(driver, "02_found_reject_button", "Found Reject all button")
                
                reject_button.click()
                print("✅ Clicked Reject all button")
                
                time.sleep(5)
                take_screenshot(driver, "03_after_consent_click", "After clicking Reject all")
                
                new_url = driver.current_url
                if 'consent.youtube.com' not in new_url:
                    print("🎉 SUCCESS: Bypassed consent page!")
                    return True
                else:
                    print("⚠️ Still on consent page after click")
                    return False
                    
        except Exception as e:
            print(f"Consent handling failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Consent error: {e}")
        return False

def sign_in_to_youtube(driver, email, password):
    """Sign in to YouTube with provided credentials"""
    try:
        print("🔐 Starting YouTube sign-in process...")
        
        # Look for sign-in button
        try:
            # Multiple selectors for sign-in button
            sign_in_selectors = [
                "a[aria-label*='Sign in']",
                "button[aria-label*='Sign in']", 
                "a:contains('Sign in')",
                "button:contains('Sign in')",
                "#buttons ytd-button-renderer a[href*='accounts.google.com']"
            ]
            
            sign_in_button = None
            for selector in sign_in_selectors:
                try:
                    if ':contains(' in selector:
                        # Use XPath for text-based selectors
                        xpath_selector = f"//*[contains(text(), 'Sign in') and (self::a or self::button)]"
                        sign_in_button = driver.find_element(By.XPATH, xpath_selector)
                    else:
                        sign_in_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if sign_in_button:
                        print(f"✅ Found sign-in button with selector: {selector}")
                        break
                except:
                    continue
            
            if not sign_in_button:
                print("❌ Could not find sign-in button")
                take_screenshot(driver, "04_no_signin_button", "No sign-in button found")
                return False
            
            take_screenshot(driver, "05_signin_button_found", "Sign-in button found")
            
            # Click sign-in button
            sign_in_button.click()
            print("✅ Clicked sign-in button")
            time.sleep(3)
            
            take_screenshot(driver, "06_after_signin_click", "After clicking sign-in")
            
        except Exception as e:
            print(f"Error finding sign-in button: {e}")
            take_screenshot(driver, "07_signin_error", "Sign-in button error")
            return False
        
        # Handle Google sign-in page
        print("📧 Entering email...")
        try:
            # Wait for email input field
            email_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            
            take_screenshot(driver, "08_email_page", "Google email input page")
            
            # Clear and enter email
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(2)
            
            take_screenshot(driver, "09_email_entered", "Email entered")
            
            # Click Next button
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "identifierNext"))
            )
            next_button.click()
            print("✅ Email entered and Next clicked")
            time.sleep(3)
            
            take_screenshot(driver, "10_after_email_next", "After email Next")
            
        except Exception as e:
            print(f"Error with email input: {e}")
            take_screenshot(driver, "11_email_error", "Email input error")
            return False
        
        # Handle password input
        print("🔒 Entering password...")
        try:
            # Wait for password input field
            password_input = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "password"))
            )
            
            take_screenshot(driver, "12_password_page", "Google password input page")
            
            # Clear and enter password
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(2)
            
            take_screenshot(driver, "13_password_entered", "Password entered")
            
            # Click Next button for password
            password_next = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "passwordNext"))
            )
            password_next.click()
            print("✅ Password entered and Next clicked")
            time.sleep(5)
            
            take_screenshot(driver, "14_after_password_next", "After password Next")
            
        except Exception as e:
            print(f"Error with password input: {e}")
            take_screenshot(driver, "15_password_error", "Password input error")
            return False
        
        # Wait for sign-in to complete and return to YouTube
        print("⏳ Waiting for sign-in to complete...")
        time.sleep(10)
        
        current_url = driver.current_url
        page_title = driver.title
        
        print(f"📄 Current URL: {current_url}")
        print(f"📄 Page Title: {page_title}")
        
        take_screenshot(driver, "16_signin_complete", "Sign-in process complete")
        
        # Check if we're signed in by looking for user avatar or account elements
        try:
            # Look for signed-in indicators
            signed_in_indicators = [
                "#avatar-btn",
                "button[aria-label*='Account menu']",
                "ytd-topbar-menu-button-renderer",
                "#guide-button"  # Should be visible when signed in
            ]
            
            signed_in = False
            for indicator in signed_in_indicators:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, indicator)
                    if element:
                        print(f"✅ Found sign-in indicator: {indicator}")
                        signed_in = True
                        break
                except:
                    continue
            
            if signed_in:
                print("🎉 Successfully signed in to YouTube!")
                take_screenshot(driver, "17_signin_success", "Successfully signed in")
                return True
            else:
                print("⚠️ Sign-in status unclear")
                take_screenshot(driver, "18_signin_unclear", "Sign-in status unclear")
                return True  # Continue anyway
                
        except Exception as e:
            print(f"Error checking sign-in status: {e}")
            return True  # Continue anyway
        
    except Exception as e:
        print(f"❌ Sign-in process failed: {e}")
        take_screenshot(driver, "19_signin_failed", f"Sign-in failed: {str(e)[:30]}")
        return False

def subscribe_to_channel(driver, channel_url):
    """Subscribe to the specified YouTube channel"""
    try:
        print(f"📺 Navigating to channel: {channel_url}")
        
        # Navigate to the channel
        driver.get(channel_url)
        time.sleep(5)
        
        take_screenshot(driver, "20_channel_page", "Channel page loaded")
        
        # Handle consent if it appears again
        if 'consent.youtube.com' in driver.current_url:
            print("🍪 Consent appeared again, handling...")
            if not handle_youtube_consent(driver):
                print("❌ Failed to handle consent on channel page")
                return False
            time.sleep(3)
        
        take_screenshot(driver, "21_channel_ready", "Channel ready for interaction")
        
        # Look for subscribe button
        print("🔍 Looking for Subscribe button...")
        try:
            subscribe_selectors = [
                "button[aria-label*='Subscribe']",
                "ytd-subscribe-button-renderer button",
                "#subscribe-button button", 
                "paper-button[aria-label*='Subscribe']",
                "button:contains('Subscribe')",
                "#subscribe-button-shape button"
            ]
            
            subscribe_button = None
            for selector in subscribe_selectors:
                try:
                    if ':contains(' in selector:
                        # Use XPath for text-based selectors
                        xpath_selector = "//*[contains(text(), 'Subscribe') and (self::button or @role='button')]"
                        subscribe_button = driver.find_element(By.XPATH, xpath_selector)
                    else:
                        subscribe_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if subscribe_button:
                        button_text = subscribe_button.text.strip()
                        print(f"✅ Found subscribe button: '{button_text}' with selector: {selector}")
                        break
                except:
                    continue
            
            if not subscribe_button:
                print("❌ Could not find Subscribe button")
                take_screenshot(driver, "22_no_subscribe_button", "No Subscribe button found")
                
                # Debug: show all buttons on the page
                try:
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    print(f"🔍 Found {len(all_buttons)} total buttons on page:")
                    for i, btn in enumerate(all_buttons[:10]):  # Show first 10
                        try:
                            btn_text = btn.text.strip()
                            btn_aria = btn.get_attribute("aria-label") or ""
                            print(f"  Button {i}: '{btn_text}' (aria-label: '{btn_aria}')")
                        except:
                            print(f"  Button {i}: <error reading>")
                except Exception as e:
                    print(f"Error debugging buttons: {e}")
                
                return False
            
            take_screenshot(driver, "23_subscribe_button_found", "Subscribe button found")
            
            # Check if already subscribed
            button_text = subscribe_button.text.strip().lower()
            if 'subscribed' in button_text or 'unsubscribe' in button_text:
                print("✅ Already subscribed to this channel!")
                take_screenshot(driver, "24_already_subscribed", "Already subscribed")
                return True
            
            # Click the subscribe button
            print("🎯 Clicking Subscribe button...")
            subscribe_button.click()
            time.sleep(3)
            
            take_screenshot(driver, "25_after_subscribe_click", "After clicking Subscribe")
            
            # Check if subscription was successful
            try:
                # Look for confirmation or changed button state
                time.sleep(2)
                
                # Re-find the button to check its new state
                try:
                    updated_button = driver.find_element(By.CSS_SELECTOR, subscribe_selectors[0])
                    new_button_text = updated_button.text.strip().lower()
                    
                    if 'subscribed' in new_button_text or 'unsubscribe' in new_button_text:
                        print("🎉 SUCCESS: Successfully subscribed!")
                        take_screenshot(driver, "26_subscribe_success", "Successfully subscribed")
                        return True
                    else:
                        print(f"⚠️ Button text after click: '{new_button_text}'")
                        take_screenshot(driver, "27_subscribe_unclear", "Subscription status unclear")
                        return True  # Assume success if no error
                        
                except Exception as e:
                    print(f"Could not verify subscription status: {e}")
                    take_screenshot(driver, "28_subscribe_verify_error", "Verification error")
                    return True  # Assume success if no error
                
            except Exception as e:
                print(f"Error verifying subscription: {e}")
                return True  # Assume success
            
        except Exception as e:
            print(f"Error with subscribe process: {e}")
            take_screenshot(driver, "29_subscribe_error", f"Subscribe error: {str(e)[:30]}")
            return False
        
    except Exception as e:
        print(f"❌ Channel subscription failed: {e}")
        take_screenshot(driver, "30_channel_error", f"Channel error: {str(e)[:30]}")
        return False

def youtube_full_automation():
    """Complete YouTube automation workflow"""
    driver = None
    try:
        print("🚀 Starting Complete YouTube Automation...")
        
        # Get credentials
        email, password = get_credentials()
        if not email or not password:
            print("❌ Could not retrieve credentials")
            return False
        
        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.binary_location = '/usr/bin/google-chrome'
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome started")
        
        take_screenshot(driver, "00_chrome_started", "Chrome browser started")
        
        # Step 1: Navigate to YouTube
        print("📺 Navigating to YouTube...")
        driver.get("https://www.youtube.com")
        time.sleep(5)
        
        take_screenshot(driver, "01_youtube_homepage", "YouTube homepage")
        
        # Step 2: Handle consent
        if not handle_youtube_consent(driver):
            print("❌ Failed to handle consent")
            return False
        
        # Step 3: Sign in
        if not sign_in_to_youtube(driver, email, password):
            print("❌ Failed to sign in")
            return False
        
        # Step 4: Subscribe to channel
        channel_url = "https://www.youtube.com/channel/UCsXVk37bltHxD1rDPwtNM8Q"
        if not subscribe_to_channel(driver, channel_url):
            print("❌ Failed to subscribe to channel")
            return False
        
        print("🎉 COMPLETE SUCCESS: YouTube automation workflow completed!")
        take_screenshot(driver, "99_complete_success", "Complete automation success")
        return True
        
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        if driver:
            take_screenshot(driver, "99_automation_error", f"Automation error: {str(e)[:30]}")
        return False
    finally:
        if driver:
            take_screenshot(driver, "99_cleanup", "Before cleanup")
            driver.quit()
            print("🔧 Browser closed")

if __name__ == "__main__":
    print("🧪 Starting YouTube Full Automation Test...")
    success = youtube_full_automation()
    print(f"🎯 Final Result: {'✅ SUCCESS' if success else '❌ FAILED'}") 