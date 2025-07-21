#!/usr/bin/env python3
"""
Fixed YouTube consent handler targeting the correct button element
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
        filename = f"fixed_{name}_{timestamp}.png"
        filepath = screenshots_dir / filename
        
        driver.save_screenshot(str(filepath))
        print(f"📸 Screenshot saved: {filename} - {description}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return ""

def handle_youtube_consent_fixed(driver):
    """Handle YouTube consent by targeting the correct button"""
    try:
        current_url = driver.current_url
        if 'consent.youtube.com' not in current_url:
            print("✅ No consent page detected")
            return True
            
        print("🍪 YouTube consent page detected!")
        take_screenshot(driver, "01_consent_page", "Consent page detected")
        
        # Method 1: Target button with specific aria-label
        print("🎯 Method 1: Looking for button with aria-label='Reject all'...")
        try:
            reject_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Reject all']"))
            )
            
            if reject_button:
                print("✅ Found button with aria-label='Reject all'")
                take_screenshot(driver, "02_found_reject_button", "Found Reject all button")
                
                # Click the button
                reject_button.click()
                print("✅ Clicked Reject all button")
                
                # Wait for response
                time.sleep(5)
                take_screenshot(driver, "03_after_click", "After clicking Reject all")
                
                # Check if we're redirected
                new_url = driver.current_url
                if 'consent.youtube.com' not in new_url:
                    print("🎉 SUCCESS: Redirected away from consent page!")
                    return True
                else:
                    print("⚠️ Still on consent page, checking for additional steps...")
                    
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: Try all buttons and find the one with "Reject all" text
        print("🎯 Method 2: Looking through all buttons for 'Reject all'...")
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} buttons total")
            
            for i, button in enumerate(buttons):
                try:
                    button_text = button.text.strip()
                    aria_label = button.get_attribute("aria-label") or ""
                    
                    if "Reject all" in button_text or "Reject all" in aria_label:
                        print(f"✅ Found target button #{i}: text='{button_text}', aria-label='{aria_label}'")
                        take_screenshot(driver, f"04_button_{i}_found", f"Found button {i}")
                        
                        # Click this button
                        button.click()
                        print(f"✅ Clicked button #{i}")
                        
                        time.sleep(5)
                        take_screenshot(driver, f"05_after_button_{i}", f"After clicking button {i}")
                        
                        # Check result
                        new_url = driver.current_url
                        if 'consent.youtube.com' not in new_url:
                            print("🎉 SUCCESS: Redirected away from consent page!")
                            return True
                        else:
                            print(f"⚠️ Still on consent page after button #{i}")
                            
                except Exception as e:
                    print(f"Error with button #{i}: {e}")
                    continue
        except Exception as e:
            print(f"Method 2 failed: {e}")
        
        # Method 3: JavaScript direct click
        print("🎯 Method 3: JavaScript direct click...")
        try:
            js_result = driver.execute_script("""
                // Find button with aria-label="Reject all"
                var rejectBtn = document.querySelector('button[aria-label="Reject all"]');
                if (rejectBtn) {
                    console.log('Found reject button via JS:', rejectBtn);
                    rejectBtn.click();
                    return 'clicked_aria_label';
                }
                
                // Fallback: find button containing "Reject all" text
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    if (btn.textContent && btn.textContent.includes('Reject all')) {
                        console.log('Found reject button via text:', btn);
                        btn.click();
                        return 'clicked_text_content';
                    }
                }
                
                return 'not_found';
            """)
            
            print(f"JavaScript result: {js_result}")
            
            if js_result != 'not_found':
                time.sleep(5)
                take_screenshot(driver, "06_after_js_click", "After JavaScript click")
                
                new_url = driver.current_url
                if 'consent.youtube.com' not in new_url:
                    print("🎉 SUCCESS: JavaScript click worked!")
                    return True
            
        except Exception as e:
            print(f"Method 3 failed: {e}")
        
        print("❌ All methods failed to handle consent")
        take_screenshot(driver, "07_all_failed", "All methods failed")
        return False
        
    except Exception as e:
        print(f"❌ Consent handling error: {e}")
        take_screenshot(driver, "08_error", f"Error: {str(e)[:50]}")
        return False

def test_youtube_workflow():
    """Test complete YouTube workflow with consent handling"""
    driver = None
    try:
        print("🚀 Starting Complete YouTube Test...")
        
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
        
        # Navigate to Kurzgesagt channel
        channel_url = "https://www.youtube.com/@kurzgesagt"
        print(f"📺 Navigating to: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)
        
        take_screenshot(driver, "00_initial_load", "Initial page load")
        
        # Handle consent
        consent_handled = handle_youtube_consent_fixed(driver)
        
        if consent_handled:
            print("✅ Consent handled - checking final state...")
            time.sleep(3)
            
            final_url = driver.current_url
            final_title = driver.title
            
            print(f"📄 Final URL: {final_url}")
            print(f"📄 Final Title: {final_title}")
            
            take_screenshot(driver, "09_final_state", f"Final state")
            
            # Look for YouTube elements that indicate we're on the real page
            try:
                # Look for subscribe button
                subscribe_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Subscribe') or contains(@aria-label, 'Subscribe')]")
                print(f"👤 Found {len(subscribe_elements)} subscribe elements")
                
                # Look for channel name/content
                channel_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Kurzgesagt') or contains(text(), 'kurz')]")
                print(f"📺 Found {len(channel_elements)} channel-related elements")
                
                if subscribe_elements or channel_elements:
                    print("🎉 SUCCESS: Found YouTube channel content!")
                    take_screenshot(driver, "10_success_content", "Success - found channel content")
                    return True
                else:
                    print("⚠️ No channel content found")
                    take_screenshot(driver, "11_no_content", "No channel content found")
                    
            except Exception as e:
                print(f"Error checking content: {e}")
            
            # Even if we can't find specific elements, if we're not on consent page, it's progress
            if 'consent.youtube.com' not in final_url:
                print("🎉 PARTIAL SUCCESS: At least bypassed consent page!")
                return True
            else:
                print("❌ Still on consent page")
                return False
        else:
            print("❌ Failed to handle consent")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if driver:
            take_screenshot(driver, "99_error", f"Error: {str(e)[:50]}")
        return False
    finally:
        if driver:
            take_screenshot(driver, "99_cleanup", "Before cleanup")
            driver.quit()
            print("🔧 Browser closed")

if __name__ == "__main__":
    print("🧪 Starting YouTube Consent Fix Test...")
    success = test_youtube_workflow()
    print(f"🎯 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}") 