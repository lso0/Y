#!/usr/bin/env python3
"""
Simple Selenium test for YouTube automation with screenshots
"""

import os
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

def take_screenshot(driver, name: str, description: str = ""):
    """Take a screenshot and save it"""
    try:
        screenshots_dir = Path("services/youtube/data/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"selenium_{name}_{timestamp}.png"
        filepath = screenshots_dir / filename
        
        driver.save_screenshot(str(filepath))
        print(f"📸 Screenshot saved: {filename} - {description}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return ""

def test_youtube_with_selenium():
    """Test YouTube access with Selenium and take screenshots"""
    driver = None
    try:
        print("🚀 Starting Selenium Chrome...")
        
        # Chrome options for headless server
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-data-dir=/tmp/selenium_youtube')
        
        # Don't use headless for now to test if it works
        # chrome_options.add_argument('--headless')
        
        # Specify Chrome binary path
        chrome_options.binary_location = '/usr/bin/google-chrome'
        
        # Use webdriver-manager to automatically handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome started successfully")
        
        # Take initial screenshot
        take_screenshot(driver, "01_chrome_started", "Chrome started successfully")
        
        # Navigate to YouTube
        print("🎯 Navigating to YouTube...")
        driver.get('https://www.youtube.com')
        time.sleep(3)
        
        take_screenshot(driver, "02_youtube_homepage", "YouTube homepage loaded")
        
        # Handle YouTube consent/cookie dialog
        try:
            current_url = driver.current_url
            if 'consent.youtube.com' in current_url:
                print("🍪 YouTube consent page detected, looking for reject button...")
                take_screenshot(driver, "03_consent_page", "YouTube consent page detected")
                
                # Look for reject/decline buttons (try multiple selectors)
                reject_selectors = [
                    'button:contains("Reject all")',
                    'button:contains("Decline")', 
                    'button[aria-label*="Reject"]',
                    'button[aria-label*="Decline"]',
                    '[data-testid="reject-all-button"]',
                    '.VfPpkd-LgbsSe:contains("Reject")',
                    'form[action*="reject"] button',
                    'button[jsname][data-value*="reject"]',
                    '[role="button"]:contains("Reject")'
                ]
                
                reject_clicked = False
                for selector in reject_selectors:
                    try:
                        if ':contains(' in selector:
                            # Use XPath for text-based selectors
                            xpath_selector = f"//*[contains(text(), '{selector.split(':contains(')[1].split(')')[0].strip('\"')}') and (self::button or @role='button')]"
                            reject_button = driver.find_element(By.XPATH, xpath_selector)
                        else:
                            reject_button = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        
                        if reject_button:
                            print(f"🎯 Found reject button with selector: {selector}")
                            take_screenshot(driver, "04_reject_button_found", "Reject button found")
                            reject_button.click()
                            time.sleep(3)
                            reject_clicked = True
                            take_screenshot(driver, "05_after_reject_click", "After clicking reject")
                            break
                    except:
                        continue
                
                if not reject_clicked:
                    print("⚠️ Could not find reject button, trying alternative approaches...")
                    take_screenshot(driver, "06_no_reject_button", "No reject button found")
                    
                    # Try to find any form buttons and click the second one (usually reject)
                    try:
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        if len(buttons) >= 2:
                            print(f"🔄 Found {len(buttons)} buttons, trying second one as reject...")
                            buttons[1].click()  # Usually reject is the second button
                            time.sleep(3)
                            take_screenshot(driver, "07_clicked_second_button", "Clicked second button as reject")
                        
                    except Exception as e:
                        print(f"❌ Alternative approach failed: {e}")
            
            # Wait a moment for potential redirect
            time.sleep(3)
            take_screenshot(driver, "08_after_consent_handling", "After consent handling")
            
        except Exception as e:
            print(f"⚠️ Consent handling error: {e}")
            take_screenshot(driver, "09_consent_error", "Consent handling error")
        
        # Check if we can find YouTube elements
        try:
            # Look for YouTube logo or main content
            youtube_logo = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "logo"))
            )
            print("✅ YouTube logo found")
            take_screenshot(driver, "10_youtube_logo_found", "YouTube logo detected")
        except:
            print("⚠️ YouTube logo not found, but page loaded")
            take_screenshot(driver, "11_youtube_no_logo", "YouTube page without logo")
        
        # Navigate to a specific channel
        channel_url = "https://www.youtube.com/@kurzgesagt"
        print(f"📺 Navigating to channel: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)
        
        take_screenshot(driver, "12_channel_page", "Channel page loaded")
        
        # Handle consent on channel page if it appears again
        try:
            if 'consent.youtube.com' in driver.current_url:
                print("🍪 Consent page appeared on channel, handling again...")
                take_screenshot(driver, "13_channel_consent", "Consent on channel page")
                
                # Try to find and click reject button using XPath
                reject_xpath_selectors = [
                    "//*[contains(text(), 'Reject all')]",
                    "//*[contains(text(), 'Decline')]", 
                    "//*[contains(text(), 'Reject')]",
                    "//button[contains(@aria-label, 'Reject')]",
                ]
                
                for xpath_selector in reject_xpath_selectors:
                    try:
                        reject_button = driver.find_element(By.XPATH, xpath_selector)
                        if reject_button:
                            print(f"🎯 Found reject button with XPath: {xpath_selector}")
                            reject_button.click()
                            time.sleep(3)
                            break
                    except:
                        continue
                
                take_screenshot(driver, "14_after_channel_consent", "After handling channel consent")
                time.sleep(3)
        except Exception as e:
            print(f"Channel consent handling error: {e}")
        
        take_screenshot(driver, "15_final_channel_page", "Final channel page state")
        
        # Look for sign-in elements
        try:
            sign_in_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sign in') or contains(@aria-label, 'Sign in')]")
            if sign_in_elements:
                print(f"🔐 Found {len(sign_in_elements)} sign-in elements")
                take_screenshot(driver, "16_signin_elements_found", f"Found {len(sign_in_elements)} sign-in elements")
            else:
                print("ℹ️ No sign-in elements found")
                take_screenshot(driver, "17_no_signin_elements", "No sign-in elements found")
        except Exception as e:
            print(f"Error looking for sign-in elements: {e}")
        
        # Look for subscribe button
        try:
            subscribe_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Subscribe') or contains(@aria-label, 'Subscribe')]")
            if subscribe_elements:
                print(f"👤 Found {len(subscribe_elements)} subscribe elements")
                take_screenshot(driver, "18_subscribe_elements_found", f"Found {len(subscribe_elements)} subscribe elements")
            else:
                print("ℹ️ No subscribe elements found")
                take_screenshot(driver, "19_no_subscribe_elements", "No subscribe elements found")
        except Exception as e:
            print(f"Error looking for subscribe elements: {e}")
        
        # Get page info
        current_url = driver.current_url
        page_title = driver.title
        print(f"📄 Current URL: {current_url}")
        print(f"📄 Page Title: {page_title}")
        
        take_screenshot(driver, "20_final_state", f"Final state - {page_title[:30]}")
        
        print("✅ Selenium test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        if driver:
            take_screenshot(driver, "98_error_state", f"Error: {str(e)[:50]}")
        return False
    finally:
        if driver:
            take_screenshot(driver, "99_before_quit", "Before quitting browser")
            driver.quit()
            print("🔧 Browser closed")

if __name__ == "__main__":
    print("🧪 Starting Selenium YouTube Test...")
    success = test_youtube_with_selenium()
    print(f"🎯 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}") 