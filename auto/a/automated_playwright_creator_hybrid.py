#!/usr/bin/env python3
"""
Hybrid Fastmail alias creation: Automated login + Manual Bearer token capture
This script combines the best of both approaches:
1. Automated login (like stealth version)
2. Brief manual step to capture Bearer token (like working version)
3. Automated alias creation with traditional Alias/set method
"""

from playwright.sync_api import sync_playwright
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def auto_login_fastmail(page, email, password):
    """Automate the Fastmail login process using Playwright"""
    print("🔐 Attempting to log in automatically...")
    
    try:
        # Wait for login form to load
        page.wait_for_load_state('networkidle')
        
        # Use the specific selectors that work
        email_selectors = [
            '#v22-input',  # Primary selector
            '.v-TextInput-input',
            'input[name="username"]',
            'input[placeholder="email@fastmail.com"]',
            'input[autocomplete*="username"]'
        ]
        
        email_input = None
        for selector in email_selectors:
            try:
                email_input = page.wait_for_selector(selector, timeout=5000)
                if email_input and email_input.is_visible():
                    print(f"✅ Found email input using: {selector}")
                    break
            except:
                print(f"❌ Could not find email input with: {selector}")
                continue
        
        if not email_input:
            print("❌ Could not find email input field")
            return False
        
        # Clear and fill email
        email_input.fill("")  # Clear by filling with empty string
        time.sleep(0.3)
        email_input.fill(email)
        print(f"✅ Entered email: {email}")
        
        # Look for password field
        password_input = None
        try:
            password_input = page.query_selector('input[type="password"]')
        except:
            pass
        
        if password_input and password_input.is_visible():
            # Fill password if field is visible
            password_input.fill("")  # Clear
            password_input.fill(password)
            print("✅ Entered password")
        else:
            # Click Continue button first
            continue_selectors = [
                '#v25',  # Primary selector for Continue button
                '.v-Button--cta',
                'button.v-Button--sizeM',
                'button:has-text("Continue")',
                'button[type="submit"]'
            ]
            
            for selector in continue_selectors:
                try:
                    continue_btn = page.wait_for_selector(selector, timeout=3000)
                    if continue_btn and continue_btn.is_visible() and continue_btn.is_enabled():
                        continue_btn.click()
                        print(f"✅ Clicked continue button using: {selector}")
                        time.sleep(2)  # Wait for password field to appear
                        break
                except:
                    print(f"❌ Could not find continue button with: {selector}")
                    continue
            
            # Wait for password field to appear
            try:
                password_input = page.wait_for_selector('input[type="password"]', timeout=10000)
                password_input.fill("")  # Clear
                password_input.fill(password)
                print("✅ Entered password (second step)")
            except:
                print("❌ Could not find password field")
                return False
        
        # Submit the form
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            '.btn-primary'
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = page.query_selector(selector)
                if submit_btn and submit_btn.is_visible():
                    submit_btn.click()
                    print("✅ Clicked login button")
                    break
            except:
                continue
        
        # Wait for login to complete
        print("⏳ Waiting for login to complete...")
        try:
            # Wait for URL to change to indicate successful login
            page.wait_for_function(
                "() => window.location.href.includes('mail/Inbox') || window.location.href.includes('u=')",
                timeout=20000
            )
            
            current_url = page.url
            print(f"✅ Login successful! Current URL: {current_url}")
            
            # Extract user ID from URL if present
            if 'u=' in current_url:
                user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                print(f"✅ Detected User ID: {user_id}")
            
            return True
            
        except:
            # Fallback: check if we're on any fastmail page that's not login
            current_url = page.url
            if 'app.fastmail.com' in current_url and 'login' not in current_url:
                print("✅ Detected successful login (fallback check)")
                return True
            
            print("❌ Login timeout - may have failed")
            return False
            
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def create_alias_with_hybrid_approach(alias_email, target_email, description="", headless=False):
    """Create alias using hybrid approach: automated login + manual Bearer token capture"""
    
    # Load credentials from environment
    email = os.getenv('FASTMAIL_EMAIL')
    password = os.getenv('FASTMAIL_API_PASSWORD')
    
    if not email or not password:
        print("❌ Missing FASTMAIL_EMAIL or FASTMAIL_API_PASSWORD in .env file")
        return False
    
    with sync_playwright() as p:
        # Launch browser - prefer headed mode for manual interaction
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            print("🌐 Navigating to Fastmail...")
            page.goto("https://app.fastmail.com")
            
            # Auto-login
            if not auto_login_fastmail(page, email, password):
                print("❌ Auto-login failed.")
                browser.close()
                return False
            
            print("✅ Login successful! Now setting up Bearer token capture...")
            
            # Set up request interception to capture Bearer token
            bearer_token = None
            user_id = None
            account_id = None
            
            def handle_request(request):
                nonlocal bearer_token, user_id, account_id
                if 'api.fastmail.com/jmap/api/' in request.url:
                    print(f"🎯 JMAP API call: {request.url}")
                    # Extract user ID from URL
                    if 'u=' in request.url:
                        user_id = request.url.split('u=')[1].split('&')[0]
                    
                    # Extract Bearer token
                    auth_header = request.headers.get('authorization', '')
                    if auth_header.startswith('Bearer '):
                        bearer_token = auth_header.replace('Bearer ', '')
                        print(f"✅ Captured Bearer token: {bearer_token[:20]}...")
                        print(f"✅ Captured User ID: {user_id}")
            
            page.on('request', handle_request)
            
            # Brief manual step to trigger authenticated API calls
            print("\n" + "="*60)
            print("🔍 MANUAL STEP REQUIRED")
            print("="*60)
            print("👤 In the browser window that opened:")
            print("   1. Navigate to Settings → Aliases (or any settings page)")
            print("   2. Click around a bit to trigger API calls")
            print("   3. This should capture the Bearer token we need")
            print("⏳ Press Enter here when you see the Bearer token captured above...")
            print("   (Look for: ✅ Captured Bearer token: xxxxxxxxxx...)")
            print("="*60)
            
            input()
            
            # Give a moment for any final API calls
            time.sleep(2)
            
            # Try to extract account ID
            try:
                account_id = page.evaluate("""
                    () => {
                        const storage = window.localStorage;
                        for (let key in storage) {
                            try {
                                const data = JSON.parse(storage[key]);
                                if (data.accountId) return data.accountId;
                                if (data.id && data.id.startsWith('c')) return data.id;
                            } catch (e) {}
                        }
                        return null;
                    }
                """)
                
                if not account_id:
                    account_id = "c75164099"  # Fallback from working version
                    print(f"⚠️  Using fallback account ID: {account_id}")
                else:
                    print(f"✅ Extracted Account ID: {account_id}")
                    
            except:
                account_id = "c75164099"
                print(f"⚠️  Using fallback account ID: {account_id}")
            
            # Extract cookies
            cookies_dict = {}
            cookies = context.cookies()
            for cookie in cookies:
                if cookie['domain'] in ['.fastmail.com', 'app.fastmail.com', 'api.fastmail.com']:
                    cookies_dict[cookie['name']] = cookie['value']
            
            browser.close()
            
            if not bearer_token or not user_id:
                print("❌ Failed to capture Bearer token. Please try again.")
                print("💡 Make sure to navigate to Settings → Aliases in the browser")
                return False
            
            # Now create the traditional alias using the captured session data
            print(f"🎯 Creating traditional alias: {alias_email} -> {target_email}")
            return create_traditional_alias(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description)
            
        except Exception as e:
            print(f"❌ Error with hybrid approach: {e}")
            browser.close()
            return False

def create_traditional_alias(bearer_token, user_id, account_id, cookies, alias_email, target_email, description=""):
    """Create a traditional alias using the working version's approach"""
    
    jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Origin": "https://app.fastmail.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    
    # Use the exact payload from the working version
    payload = {
        "using": [
            "urn:ietf:params:jmap:principals",
            "https://www.fastmail.com/dev/contacts",
            "https://www.fastmail.com/dev/backup",
            "https://www.fastmail.com/dev/auth",
            "https://www.fastmail.com/dev/calendars",
            "https://www.fastmail.com/dev/rules",
            "urn:ietf:params:jmap:mail",
            "urn:ietf:params:jmap:submission",
            "https://www.fastmail.com/dev/customer",
            "https://www.fastmail.com/dev/mail",
            "urn:ietf:params:jmap:vacationresponse",
            "urn:ietf:params:jmap:core",
            "https://www.fastmail.com/dev/files",
            "https://www.fastmail.com/dev/blob",
            "https://www.fastmail.com/dev/user",
            "urn:ietf:params:jmap:contacts",
            "https://www.fastmail.com/dev/performance",
            "https://www.fastmail.com/dev/compress",
            "https://www.fastmail.com/dev/notes",
            "urn:ietf:params:jmap:calendars"
        ],
        "methodCalls": [
            [
                "Alias/set",
                {
                    "accountId": account_id,
                    "create": {
                        "k45": {
                            "email": alias_email,
                            "targetEmails": [target_email],
                            "targetGroupRef": None,
                            "restrictSendingTo": "everybody",
                            "description": description
                        }
                    },
                    "onSuccessUpdateIdentities": True
                },
                "0"
            ]
        ],
        "lastActivity": 0,
        "clientVersion": "b457b8b325-5000d76b8ac6ae6b"
    }
    
    try:
        print("🔄 Creating traditional alias with Alias/set method...")
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Traditional alias created successfully!")
            
            # Check the response for success
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == "Alias/set":
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        print(f"🎉 Traditional Alias ID: {created_alias.get('id', 'Unknown')}")
                        print(f"🎉 Alias Email: {alias_email}")
                        print(f"🎯 Target Email: {target_email}")
                        print(f"🕐 Created at: {created_alias.get('createdAt', 'Unknown')}")
                        return True
                    elif 'notCreated' in alias_result:
                        print(f"❌ Failed to create alias: {alias_result['notCreated']}")
                        return False
            
            return True
        else:
            print(f"❌ Failed to create alias. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating alias: {e}")
        return False

def main():
    print("🔀 Fastmail Hybrid Alias Creator")
    print("Automated Login + Manual Bearer Token Capture")
    print("=" * 50)
    
    # Check for headless mode argument
    headless = False  # Default to headed for manual interaction
    if '--headless' in sys.argv:
        headless = True
        print("👻 Running in headless mode (not recommended for this hybrid approach)")
    else:
        print("🖥️  Running in headed mode (recommended)")
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        return False
    
    print(f"\n🎯 Creating traditional alias: {alias_email} -> {target_email}")
    print("📁 Make sure you have a .env file with FASTMAIL_EMAIL and FASTMAIL_API_PASSWORD")
    
    success = create_alias_with_hybrid_approach(alias_email, target_email, description, headless=headless)
    
    if success:
        print("\n🎉 Success! Your traditional alias has been created.")
        print("📧 Check Settings → Aliases in your Fastmail dashboard!")
        return True
    else:
        print("\n❌ Failed to create alias. Please try again.")
        return False

if __name__ == "__main__":
    main() 