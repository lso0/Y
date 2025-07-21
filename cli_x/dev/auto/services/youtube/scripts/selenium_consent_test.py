#!/usr/bin/env python3
"""
Focused test for YouTube consent handling with multiple strategies
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
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def take_screenshot(driver, name: str, description: str = ""):
    """Take a screenshot and save it"""
    try:
        screenshots_dir = Path("services/youtube/data/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consent_{name}_{timestamp}.png"
        filepath = screenshots_dir / filename
        
        driver.save_screenshot(str(filepath))
        print(f"📸 Screenshot saved: {filename} - {description}")
        return str(filepath)
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return ""

def debug_page_elements(driver, name_prefix):
    """Debug what elements are available on the page"""
    try:
        print(f"\n🔍 DEBUG - {name_prefix}:")
        print(f"URL: {driver.current_url}")
        print(f"Title: {driver.title}")
        
        # Find all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} buttons:")
        for i, button in enumerate(buttons[:10]):  # Limit to first 10
            try:
                text = button.text.strip()
                aria_label = button.get_attribute("aria-label") or ""
                print(f"  Button {i}: '{text}' (aria-label: '{aria_label}')")
            except:
                print(f"  Button {i}: <error reading text>")
        
        # Find elements with specific text
        reject_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Reject') or contains(text(), 'Decline') or contains(text(), 'reject') or contains(text(), 'decline')]")
        print(f"Found {len(reject_elements)} elements with 'reject/decline' text:")
        for i, elem in enumerate(reject_elements):
            try:
                text = elem.text.strip()
                tag = elem.tag_name
                print(f"  Reject Element {i}: <{tag}> '{text}'")
            except:
                print(f"  Reject Element {i}: <error reading>")
                
    except Exception as e:
        print(f"Debug error: {e}")

def handle_youtube_consent_advanced(driver):
    """Advanced consent handling with multiple strategies"""
    try:
        current_url = driver.current_url
        if 'consent.youtube.com' not in current_url:
            print("✅ No consent page detected")
            return True
            
        print("🍪 YouTube consent page detected!")
        take_screenshot(driver, "01_consent_detected", "Consent page detected")
        debug_page_elements(driver, "CONSENT_PAGE")
        
        # Strategy 1: Find by exact text content
        print("\n🎯 Strategy 1: Looking for exact text...")
        text_patterns = ["Reject all", "Decline all", "I disagree", "Reject", "Decline"]
        
        for pattern in text_patterns:
            try:
                xpath = f"//*[text()='{pattern}' or contains(text(), '{pattern}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"Found element with text '{pattern}': {len(elements)} matches")
                    element = elements[0]
                    take_screenshot(driver, f"02_found_{pattern.lower().replace(' ', '_')}", f"Found {pattern} button")
                    
                    # Try different click methods
                    try:
                        element.click()
                        print(f"✅ Clicked '{pattern}' with normal click")
                        time.sleep(3)
                        take_screenshot(driver, "03_after_text_click", f"After clicking {pattern}")
                        return True
                    except:
                        # Try ActionChains click
                        try:
                            ActionChains(driver).move_to_element(element).click().perform()
                            print(f"✅ Clicked '{pattern}' with ActionChains")
                            time.sleep(3)
                            take_screenshot(driver, "04_after_action_click", f"After ActionChains {pattern}")
                            return True
                        except:
                            print(f"❌ Failed to click '{pattern}'")
                            continue
            except Exception as e:
                print(f"Error with pattern '{pattern}': {e}")
                continue
        
        # Strategy 2: Look for form buttons and try the second one
        print("\n🎯 Strategy 2: Form button approach...")
        try:
            # Look for buttons in forms
            form_buttons = driver.find_elements(By.CSS_SELECTOR, "form button")
            if len(form_buttons) >= 2:
                print(f"Found {len(form_buttons)} form buttons")
                # Usually: [Accept, Reject] - so try the second one
                reject_button = form_buttons[1]
                button_text = reject_button.text.strip()
                print(f"Trying second form button: '{button_text}'")
                take_screenshot(driver, "05_form_button_attempt", f"Trying form button: {button_text}")
                
                reject_button.click()
                time.sleep(3)
                take_screenshot(driver, "06_after_form_click", "After form button click")
                print("✅ Clicked second form button")
                return True
        except Exception as e:
            print(f"Form button strategy failed: {e}")
        
        # Strategy 3: Try all buttons with reject-related attributes
        print("\n🎯 Strategy 3: Attribute-based search...")
        try:
            attribute_selectors = [
                "button[data-value*='reject']",
                "button[data-value*='decline']", 
                "button[aria-label*='reject']",
                "button[aria-label*='decline']",
                "[role='button'][data-value*='reject']",
                "[role='button'][aria-label*='reject']"
            ]
            
            for selector in attribute_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found element with selector '{selector}'")
                    element = elements[0]
                    take_screenshot(driver, "07_attribute_found", f"Found with {selector}")
                    element.click()
                    time.sleep(3)
                    take_screenshot(driver, "08_after_attribute_click", f"After {selector} click")
                    print(f"✅ Clicked element with {selector}")
                    return True
        except Exception as e:
            print(f"Attribute strategy failed: {e}")
        
        # Strategy 4: JavaScript click on all buttons containing "reject"
        print("\n🎯 Strategy 4: JavaScript execution...")
        try:
            js_script = '''
            var buttons = document.querySelectorAll('button, [role="button"]');
            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                var text = (btn.textContent || btn.innerText || '').toLowerCase();
                var ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                if (text.includes('reject') || text.includes('decline') || 
                    ariaLabel.includes('reject') || ariaLabel.includes('decline')) {
                    console.log('Clicking button:', btn);
                    btn.click();
                    return true;
                }
            }
            return false;
            '''
            
            result = driver.execute_script(js_script)
            if result:
                print("✅ JavaScript click successful")
                time.sleep(3)
                take_screenshot(driver, "09_after_js_click", "After JavaScript click")
                return True
            else:
                print("❌ JavaScript click found no suitable buttons")
        except Exception as e:
            print(f"JavaScript strategy failed: {e}")
        
        print("❌ All consent handling strategies failed")
        take_screenshot(driver, "10_all_failed", "All strategies failed")
        return False
        
    except Exception as e:
        print(f"❌ Consent handling error: {e}")
        take_screenshot(driver, "11_consent_error", f"Error: {str(e)[:50]}")
        return False

def test_consent_handling():
    """Test focused consent handling"""
    driver = None
    try:
        print("🚀 Starting Consent Test...")
        
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
        
        # Go directly to Kurzgesagt channel (likely to trigger consent)
        channel_url = "https://www.youtube.com/@kurzgesagt"
        print(f"📺 Navigating to: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)
        
        take_screenshot(driver, "00_initial_load", "Initial page load")
        
        # Handle consent
        consent_handled = handle_youtube_consent_advanced(driver)
        
        if consent_handled:
            print("✅ Consent handled successfully")
            time.sleep(5)  # Wait for redirect
            
            final_url = driver.current_url
            final_title = driver.title
            
            print(f"📄 Final URL: {final_url}")
            print(f"📄 Final Title: {final_title}")
            
            take_screenshot(driver, "12_final_result", f"Final result - {final_title[:30]}")
            
            # Check if we're now on the actual YouTube channel
            if 'consent.youtube.com' not in final_url:
                print("🎉 SUCCESS: Bypassed consent page!")
                return True
            else:
                print("⚠️ Still on consent page after handling")
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
    print("🧪 Starting YouTube Consent Handling Test...")
    success = test_consent_handling()
    print(f"🎯 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}") 