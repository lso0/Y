#!/usr/bin/env python3
"""
Simple script to help record Fastmail login steps
This will open a browser, navigate to Fastmail, and wait for you to perform the login.
Then it will capture the page elements for automation.
"""

from seleniumbase import SB
import time

def record_login():
    """Record the login process for Fastmail"""
    
    with SB(uc=True, headed=True, browser="chrome") as sb:
        print("🌐 Opening Fastmail...")
        sb.open("https://app.fastmail.com")
        
        print("👤 Please perform the login manually in the browser:")
        print("1. Enter your email: wg0@fastmail.com")
        print("2. Enter your password")
        print("3. Click login")
        print("4. Wait until you see the main Fastmail interface")
        
        # Wait for user to complete login
        input("⏳ Press Enter when you have successfully logged in and see the main Fastmail page...")
        
        # Capture current page info
        current_url = sb.get_current_url()
        print(f"✅ Current URL: {current_url}")
        
        # Try to find common elements that indicate successful login
        success_indicators = [
            'a[href*="settings"]',
            '[data-testid="main-content"]',
            '.fm-main',
            '#main-content',
            '.v-main',
            '.main-content',
            '.header',
            '.navbar',
            '.sidebar',
            'nav',
            '.topbar',
            '.app-header'
        ]
        
        print("🔍 Looking for elements that indicate successful login:")
        for selector in success_indicators:
            try:
                if sb.is_element_present(selector):
                    element = sb.find_element(selector)
                    text = element.text[:50] if hasattr(element, 'text') else ''
                    print(f"✅ Found: {selector} - Text: '{text}...'")
            except Exception as e:
                print(f"❌ Could not find: {selector}")
        
        # Look for login form elements to understand the structure
        print("\n🔍 Looking for form elements (if still on login page):")
        login_selectors = [
            'input[type="email"]',
            'input[type="password"]',
            'input[name="email"]',
            'input[name="password"]',
            'button[type="submit"]',
            'form',
            '.login-form',
            '.sign-in'
        ]
        
        for selector in login_selectors:
            try:
                if sb.is_element_present(selector):
                    element = sb.find_element(selector)
                    attrs = {}
                    for attr in ['id', 'name', 'class', 'type', 'placeholder']:
                        try:
                            value = element.get_attribute(attr)
                            if value:
                                attrs[attr] = value
                        except:
                            pass
                    print(f"✅ Found form element: {selector} - Attributes: {attrs}")
            except:
                pass
        
        # Try to navigate to settings to trigger API calls
        print("\n🔗 Attempting to navigate to aliases page...")
        try:
            sb.open("https://app.fastmail.com/settings/aliases")
            time.sleep(3)
            print("✅ Successfully navigated to aliases page")
        except Exception as e:
            print(f"⚠️  Could not navigate to aliases page: {e}")
        
        # Get cookies for session
        cookies = sb.driver.get_cookies()
        print(f"\n🍪 Found {len(cookies)} cookies")
        for cookie in cookies[:5]:  # Show first 5 cookies
            print(f"  - {cookie.get('name')}: {cookie.get('value')[:20]}...")
        
        # Extract any useful information from the page
        try:
            # Check localStorage for tokens or user info
            local_storage = sb.execute_script("return window.localStorage;")
            session_storage = sb.execute_script("return window.sessionStorage;")
            
            print("\n📦 LocalStorage keys:")
            for key in (local_storage.keys() if local_storage else []):
                print(f"  - {key}")
            
            print("📦 SessionStorage keys:")  
            for key in (session_storage.keys() if session_storage else []):
                print(f"  - {key}")
                
        except Exception as e:
            print(f"⚠️  Could not access storage: {e}")
        
        # Check for any JMAP API calls or tokens
        print("\n🌐 Checking for API endpoints in the page...")
        try:
            page_source = sb.get_page_source()
            if 'api.fastmail.com' in page_source:
                print("✅ Found api.fastmail.com references in page")
            if 'jmap' in page_source.lower():
                print("✅ Found JMAP references in page")
        except:
            pass
        
        print("\n✅ Recording complete! You can now close the browser.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    record_login() 