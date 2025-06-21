#!/usr/bin/env python3
"""
Automated Fastmail alias creation using Playwright with automated login
This script will:
1. Launch browser (headless or headed)
2. Navigate to Fastmail
3. Auto-login with credentials from .env file
4. Extract Bearer token using request interception (like the working version)
5. Create the alias using the JMAP API
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

def create_alias_with_playwright(alias_email, target_email, description="", headless=True):
    """Create an alias using Playwright with automated login and Bearer token extraction"""
    
    # Load credentials from environment
    email = os.getenv('FASTMAIL_EMAIL')
    password = os.getenv('FASTMAIL_API_PASSWORD')
    
    if not email or not password:
        print("❌ Missing FASTMAIL_EMAIL or FASTMAIL_API_PASSWORD in .env file")
        print("Please create a .env file with:")
        print("FASTMAIL_EMAIL=your-email@fastmail.com")
        print("FASTMAIL_API_PASSWORD=your-password")
        return False
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("🌐 Navigating to Fastmail...")
            page.goto("https://app.fastmail.com")
            
            # Auto-login
            if not auto_login_fastmail(page, email, password):
                print("❌ Auto-login failed.")
                if headless:
                    print("⚠️  Headless login failed. Please run with --headed for manual login.")
                    browser.close()
                    return False
                else:
                    print("👤 Please log in manually in the browser window")
                    print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
                    input()
            
            # Set up request interception BEFORE any navigation (this is key!)
            print("🔍 Setting up request interception...")
            
            bearer_token = None
            user_id = None
            account_id = None
            request_count = 0
            
            def handle_request(request):
                nonlocal bearer_token, user_id, account_id, request_count
                request_count += 1
                
                # Debug: print all requests to see what's happening
                if 'fastmail.com' in request.url:
                    print(f"🔎 Request #{request_count}: {request.url[:80]}...")
                    
                if 'api.fastmail.com/jmap/api/' in request.url:
                    print(f"🎯 Found JMAP API call: {request.url}")
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
            
            # Give some time for the page to fully load
            time.sleep(3)
            
            print("🔍 Extracting session data...")
            
            # Extract cookies
            cookies_dict = {}
            cookies = context.cookies()
            for cookie in cookies:
                if cookie['domain'] in ['.fastmail.com', 'app.fastmail.com', 'api.fastmail.com']:
                    cookies_dict[cookie['name']] = cookie['value']
            
            print(f"🍪 Found {len(cookies_dict)} cookies")
            print("🔗 Attempting to trigger API calls to extract Bearer token...")
            
            # Try multiple ways to trigger API calls
            api_trigger_attempts = [
                "https://app.fastmail.com/settings/aliases",
                "https://app.fastmail.com/settings/identities", 
                "https://app.fastmail.com/settings/account",
                "https://app.fastmail.com/mail/Inbox/"
            ]
            
            for attempt_url in api_trigger_attempts:
                if bearer_token:  # Stop if we got the token
                    break
                    
                try:
                                        print(f"🔄 Trying: {attempt_url}")
                    page.goto(attempt_url)
                    time.sleep(2)  # Wait for API calls
                    
                    # Try to trigger JMAP API calls with specific JavaScript actions
                    try:
                         # Force JMAP API calls by executing JavaScript that the web app uses
                         page.evaluate("""
                             // Try to force JMAP calls by triggering common app actions
                             if (window.App && window.App.state) {
                                 console.log('Found App object, trying to trigger API calls');
                             }
                             
                             // Try to trigger a refresh or data fetch
                             if (window.location.reload) {
                                 // Don't actually reload, just access it to trigger events
                                 console.log('Page reload available');
                             }
                             
                             // Scroll and interact to trigger lazy loading
                             window.scrollTo(0, 100);
                             window.scrollTo(0, 0);
                             
                             // Try clicking on elements that might trigger API calls
                             const buttons = document.querySelectorAll('button, a, .clickable');
                             if (buttons.length > 0) {
                                 console.log('Found ' + buttons.length + ' clickable elements');
                             }
                             
                             // Try to trigger keyboard events that might cause API calls
                             document.dispatchEvent(new KeyboardEvent('keydown', { key: 'F5' }));
                         """)
                         time.sleep(2)
                         
                         # Try to force a settings refresh that might trigger JMAP calls
                         if 'settings' in attempt_url:
                             page.evaluate("""
                                 // Try to find and click on settings elements
                                 const settingsElements = document.querySelectorAll('[data-testid], .settings, .config');
                                 settingsElements.forEach(el => {
                                     try {
                                         el.click();
                                     } catch(e) {}
                                 });
                             """)
                             time.sleep(1)
                     except Exception as e:
                         print(f"⚠️  Could not trigger interactions: {e}")
                         pass
                        
                except Exception as e:
                    print(f"⚠️  Failed to navigate to {attempt_url}: {e}")
                    continue
            
            print(f"📊 Total requests intercepted: {request_count}")
            
            # Try to extract account ID (use working version's approach)
            try:
                account_id = page.evaluate("""
                    () => {
                        // Try to find account ID in various places
                        const storage = window.localStorage;
                        for (let key in storage) {
                            if (key.includes('account') || key.includes('user')) {
                                try {
                                    const data = JSON.parse(storage[key]);
                                    if (data.accountId) return data.accountId;
                                    if (data.id && data.id.startsWith('c')) return data.id;
                                } catch (e) {}
                            }
                        }
                        return null;
                    }
                """)
                
                if not account_id:
                    # Use the working version's fallback account ID
                    account_id = "c75164099"
                    print(f"⚠️  Using fallback account ID: {account_id}")
                else:
                    print(f"✅ Extracted Account ID: {account_id}")
                    
            except:
                account_id = "c75164099"  # Working version's fallback
                print(f"⚠️  Using fallback account ID: {account_id}")
            
            browser.close()
            
            if not bearer_token or not user_id:
                print("❌ Failed to extract session data. Please try again.")
                return False
            
            # Now create the alias using the extracted data (same as working version)
            print(f"🎯 Creating alias: {alias_email} -> {target_email}")
            return create_alias_api(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description)
            
        except Exception as e:
            print(f"❌ Error with Playwright: {e}")
            browser.close()
            return False

def create_alias_api(bearer_token, user_id, account_id, cookies, alias_email, target_email, description=""):
    """Create alias using the JMAP API with extracted session data (same as working version)"""
    
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
    
    # Use the exact same payload as the working version
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
                "Alias/set",  # Use Alias/set like the working version
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
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        if response.status_code == 200:
            result = response.json()
            print("✅ Alias created successfully!")
            
            # Check if there were any errors in the response (same as working version)
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == "Alias/set":
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        print(f"🎉 Alias ID: {created_alias.get('id', 'Unknown')}")
                        print(f"🕐 Created at: {created_alias.get('createdAt', 'Unknown')}")
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
    print("🚀 Fastmail Automated Alias Creator (Playwright)")
    print("=" * 50)
    
    # Check for headless mode argument
    headless = True  # Default to headless
    if '--headed' in sys.argv:
        headless = False
        print("🖥️  Running in headed mode")
    else:
        print("👻 Running in headless mode")
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        return False
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    print("📁 Make sure you have a .env file with FASTMAIL_EMAIL and FASTMAIL_API_PASSWORD")
    
    success = create_alias_with_playwright(alias_email, target_email, description, headless=headless)
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
        return True
    else:
        print("\n❌ Failed to create alias. Please try again.")
        return False

if __name__ == "__main__":
    main() 