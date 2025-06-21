#!/usr/bin/env python3
"""
Stealth Fastmail alias creation using Playwright with advanced headless evasion
This script uses multiple techniques to make headless mode behave like a real browser
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

def create_stealth_browser_context(p):
    """Create a browser context with stealth techniques to avoid headless detection"""
    print("🥷 Setting up stealth browser context...")
    
    # Launch browser with stealth options
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-component-extensions-with-background-pages',
            '--disable-ipc-flooding-protection'
        ]
    )
    
    # Create context with realistic settings
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='America/New_York',
        permissions=['geolocation'],
        geolocation={'latitude': 40.7128, 'longitude': -74.0060},
        color_scheme='light',
        reduced_motion='no-preference'
    )
    
    return browser, context

def force_jmap_api_calls(page):
    """Force the web app to make JMAP API calls using various techniques"""
    print("🔥 Forcing JMAP API calls with stealth techniques...")
    
    # Inject stealth scripts to make the browser look real
    page.add_init_script("""
        // Override webdriver detection
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override headless detection
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock screen properties
        Object.defineProperty(screen, 'availHeight', {
            get: () => 1050,
        });
        Object.defineProperty(screen, 'availWidth', {
            get: () => 1920,
        });
        
        // Override permission API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Add realistic chrome object
        window.chrome = {
            runtime: {}
        };
        
        console.log('🥷 Stealth scripts injected successfully');
    """)
    
    # Wait for the app to fully load
    time.sleep(5)
    
    # Try multiple aggressive techniques to trigger JMAP calls
    techniques = [
        # Technique 1: Force navigation to aliases page
        lambda: page.goto("https://app.fastmail.com/settings/aliases", wait_until='networkidle'),
        
        # Technique 2: Simulate user interactions
        lambda: page.evaluate("""
            // Simulate real user activity
            const events = ['mousedown', 'mouseup', 'click', 'mousemove'];
            events.forEach(eventType => {
                const event = new MouseEvent(eventType, {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: 100,
                    clientY: 100
                });
                document.dispatchEvent(event);
            });
            
            // Trigger keyboard events
            const keyEvents = ['keydown', 'keyup', 'keypress'];
            keyEvents.forEach(eventType => {
                const event = new KeyboardEvent(eventType, {
                    bubbles: true,
                    cancelable: true,
                    key: 'Tab'
                });
                document.dispatchEvent(event);
            });
        """),
        
        # Technique 3: Force app state changes
        lambda: page.evaluate("""
            // Try to force app state refresh
            if (window.App && window.App.refresh) {
                window.App.refresh();
            }
            
            // Dispatch custom events that might trigger API calls
            window.dispatchEvent(new CustomEvent('focus'));
            window.dispatchEvent(new CustomEvent('beforeunload'));
            window.dispatchEvent(new CustomEvent('load'));
            
            // Force localStorage access that might trigger API calls
            localStorage.setItem('test', 'test');
            localStorage.getItem('test');
            localStorage.removeItem('test');
        """),
        
        # Technique 4: Navigate through pages that definitely trigger API calls
        lambda: page.goto("https://app.fastmail.com/settings/aliases", wait_until='networkidle'),
        lambda: page.goto("https://app.fastmail.com/settings/identities", wait_until='networkidle'),
        lambda: page.goto("https://app.fastmail.com/settings/account", wait_until='networkidle'),
        lambda: page.goto("https://app.fastmail.com/mail/Inbox/", wait_until='networkidle'),
        
        # Technique 5: Force AJAX/fetch calls
        lambda: page.evaluate("""
            // Try to trigger background API calls
            if (window.fetch) {
                // Don't actually make calls, just access the API to trigger initialization
                try {
                    const controller = new AbortController();
                    setTimeout(() => controller.abort(), 100);
                    
                    fetch('https://api.fastmail.com/jmap/api/', {
                        method: 'POST',
                        signal: controller.signal,
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({})
                    }).catch(() => {});
                } catch(e) {}
            }
        """)
    ]
    
    # Execute each technique and wait for API calls
    for i, technique in enumerate(techniques):
        try:
            print(f"🔄 Executing stealth technique #{i+1}...")
            technique()
            time.sleep(2)  # Wait for potential API calls
        except Exception as e:
            print(f"⚠️  Technique #{i+1} failed: {e}")
            continue

def create_alias_with_stealth_playwright(alias_email, target_email, description="", headless=True):
    """Create an alias using stealth Playwright techniques"""
    
    # Load credentials from environment
    email = os.getenv('FASTMAIL_EMAIL')
    password = os.getenv('FASTMAIL_API_PASSWORD')
    
    if not email or not password:
        print("❌ Missing FASTMAIL_EMAIL or FASTMAIL_API_PASSWORD in .env file")
        return False
    
    with sync_playwright() as p:
        # Create stealth browser context
        browser, context = create_stealth_browser_context(p)
        page = context.new_page()
        
        try:
            print("🌐 Navigating to Fastmail...")
            page.goto("https://app.fastmail.com")
            
            # Auto-login
            if not auto_login_fastmail(page, email, password):
                print("❌ Auto-login failed.")
                browser.close()
                return False
            
            # Set up advanced request interception
            print("🔍 Setting up advanced request interception...")
            
            bearer_token = None
            user_id = None
            account_id = None
            request_count = 0
            captured_tokens = []
            
            def handle_request(request):
                nonlocal bearer_token, user_id, account_id, request_count, captured_tokens
                request_count += 1
                
                # Capture ALL authorization headers for analysis
                auth_header = request.headers.get('authorization', '')
                if auth_header and auth_header.startswith('Bearer '):
                    print(f"🔐 Bearer token found: {auth_header[:50]}...")
                    captured_tokens.append(auth_header)
                    
                    # Always capture the latest Bearer token
                    new_token = auth_header.replace('Bearer ', '')
                    if bearer_token != new_token:
                        bearer_token = new_token
                        print(f"🎯 Updated Bearer token: {bearer_token[:20]}...")
                
                # Look for any API calls to fastmail
                if 'api.fastmail.com' in request.url:
                    print(f"🎯 Fastmail API call: {request.url}")
                    
                    if 'jmap/api/' in request.url:
                        print(f"🏆 JMAP API call found: {request.url}")
                        # Extract user ID from URL
                        if 'u=' in request.url:
                            user_id = request.url.split('u=')[1].split('&')[0]
                            print(f"✅ Captured User ID: {user_id}")
                        
                        # Ensure we have the Bearer token from this JMAP call
                        if auth_header and auth_header.startswith('Bearer '):
                            bearer_token = auth_header.replace('Bearer ', '')
                            print(f"✅ Captured JMAP Bearer token: {bearer_token[:20]}...")
            
            # Also capture responses for additional token extraction
            def handle_response(response):
                nonlocal bearer_token, user_id, account_id
                
                if 'api.fastmail.com' in response.url:
                    print(f"📥 API Response: {response.status} from {response.url[:80]}...")
                    
                    # Try to extract tokens from response headers
                    auth_header = response.headers.get('authorization', '')
                    if auth_header and auth_header.startswith('Bearer '):
                        bearer_token = auth_header.replace('Bearer ', '')
                        print(f"✅ Token from response: {bearer_token[:20]}...")
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # Force JMAP API calls using stealth techniques
            force_jmap_api_calls(page)
            
            print(f"📊 Total requests intercepted: {request_count}")
            print(f"🔐 Total auth headers captured: {len(captured_tokens)}")
            
            # Check what type of token we have
            is_api_token = False
            if not bearer_token:
                print("⚠️  No Bearer token captured from browser session")
                print("💡 Falling back to API token (will create masked email instead of alias)")
                api_token = os.getenv('FASTMAIL_API_TOKEN')
                if api_token:
                    bearer_token = api_token
                    is_api_token = True
                    print(f"✅ Using API token from .env: {bearer_token[:20]}...")
                    
                    # Extract user ID from current URL
                    current_url = page.url
                    if 'u=' in current_url:
                        user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                        print(f"✅ Extracted User ID from URL: {user_id}")
                    else:
                        user_id = "2ef64041"  # Fallback
                        print(f"⚠️  Using fallback User ID: {user_id}")
                else:
                    print("❌ No FASTMAIL_API_TOKEN found in .env file")
                    browser.close()
                    return False
            else:
                print(f"✅ Using browser session Bearer token: {bearer_token[:20]}...")
                print("🎯 This will create a traditional alias!")
            
            # Extract account ID - try to get the real one first
            account_id = None
            
            # First, try to get account ID from browser session
            try:
                account_id = page.evaluate("""
                    () => {
                        // Look for account ID in localStorage
                        const storage = window.localStorage;
                        for (let key in storage) {
                            try {
                                const data = JSON.parse(storage[key]);
                                if (data.accountId) return data.accountId;
                                if (data.id && data.id.startsWith('c')) return data.id;
                            } catch (e) {}
                        }
                        
                        // Look in sessionStorage
                        const sessionStorage = window.sessionStorage;
                        for (let key in sessionStorage) {
                            try {
                                const data = JSON.parse(sessionStorage[key]);
                                if (data.accountId) return data.accountId;
                                if (data.id && data.id.startsWith('c')) return data.id;
                            } catch (e) {}
                        }
                        
                        return null;
                    }
                """)
                
                if account_id:
                    print(f"✅ Extracted Account ID from browser: {account_id}")
                else:
                    print("⚠️  Could not extract account ID from browser")
                    
            except Exception as e:
                print(f"⚠️  Browser account ID extraction failed: {e}")
            
            # If we still don't have an account ID, we'll get it via API
            if not account_id:
                print("💡 Will fetch account ID via JMAP API...")
            
            # Extract cookies
            cookies_dict = {}
            cookies = context.cookies()
            for cookie in cookies:
                if cookie['domain'] in ['.fastmail.com', 'app.fastmail.com', 'api.fastmail.com']:
                    cookies_dict[cookie['name']] = cookie['value']
            
            browser.close()
            
            if not bearer_token or not user_id:
                print("❌ Failed to extract session data.")
                return False
            
            # Get account ID via API if we don't have it
            if not account_id:
                account_id = get_account_id_from_api(bearer_token, user_id, cookies_dict)
                if not account_id:
                    print("❌ Failed to get account ID")
                    return False
            
            # Create the alias
            print(f"🎯 Creating alias: {alias_email} -> {target_email}")
            return create_alias_api(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description, is_api_token)
            
        except Exception as e:
            print(f"❌ Error with stealth Playwright: {e}")
            browser.close()
            return False

def get_account_id_from_api(bearer_token, user_id, cookies):
    """Get the account ID using JMAP Session API"""
    print("🔍 Fetching account ID from JMAP API...")
    
    session_url = f"https://api.fastmail.com/jmap/session/?u={user_id}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = requests.get(session_url, headers=headers, cookies=cookies)
        print(f"📊 Session API Status: {response.status_code}")
        
        if response.status_code == 200:
            session_data = response.json()
            print(f"📊 Session Data: {json.dumps(session_data, indent=2)}")
            
            # Extract account ID from session data
            accounts = session_data.get('accounts', {})
            if accounts:
                # Get the first (primary) account ID
                account_id = list(accounts.keys())[0]
                print(f"✅ Found Account ID: {account_id}")
                return account_id
            else:
                print("❌ No accounts found in session data")
                return None
        else:
            print(f"❌ Session API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting account ID: {e}")
        return None

def create_alias_api(bearer_token, user_id, account_id, cookies, alias_email, target_email, description="", is_api_token=False):
    """Create alias using the JMAP API - try both methods"""
    
    jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://app.fastmail.com",
        "Referer": "https://app.fastmail.com/",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    
    if is_api_token:
        # Use MaskedEmail/set for API tokens (limited capabilities)
        print("🔄 Using API token - trying MaskedEmail/set method...")
        alias_payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "urn:ietf:params:jmap:mail",
                "urn:ietf:params:jmap:submission",
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "methodCalls": [
                [
                    "MaskedEmail/set",
                    {
                        "accountId": account_id,
                        "create": {
                            "k45": {
                                "email": alias_email,
                                "forDomain": target_email.split('@')[1],
                                "description": description,
                                "state": "enabled",
                                "emailPrefix": alias_email.split('@')[0]
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        method_name = "MaskedEmail/set"
    else:
        # Use Alias/set for browser session tokens (full capabilities like working version)
        print("🔄 Using browser session token - trying Alias/set method...")
        alias_payload = {
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
        method_name = "Alias/set"
    try:
        response = requests.post(jmap_url, json=alias_payload, headers=headers, cookies=cookies)
        print(f"📊 API Response Status: {response.status_code}")
        print(f"📊 API Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Full API Response: {json.dumps(result, indent=2)}")
            
            method_responses = result.get('methodResponses', [])
            if not method_responses:
                print("❌ No method responses in API result")
                return False
                
            for method_response in method_responses:
                print(f"📊 Method Response: {method_response}")
                if len(method_response) > 1 and method_response[0] == method_name:
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        if method_name == "Alias/set":
                            print(f"🎉 Traditional Alias ID: {created_alias.get('id', 'Unknown')}")
                            print(f"🎉 Alias Email: {created_alias.get('email', alias_email)}")
                        else:
                            print(f"🎉 Masked Email ID: {created_alias.get('id', 'Unknown')}")
                            print(f"🎉 Masked Email: {created_alias.get('email', 'Unknown')}")
                        print(f"🕐 Created at: {created_alias.get('createdAt', 'Unknown')}")
                        return True
                    elif 'notCreated' in alias_result:
                        print(f"❌ {method_name} failed: {alias_result['notCreated']}")
                        return False
                    else:
                        print(f"❌ Unexpected {method_name} result: {alias_result}")
                        return False
                elif len(method_response) > 1 and method_response[0] == "error":
                    print(f"❌ API Error: {method_response[1]}")
                    return False
            
            print(f"⚠️  No {method_name} response found in method responses")
            return False
        else:
            print(f"⚠️  {method_name} failed with status {response.status_code}")
            if response.status_code == 403:
                print("🔄 Trying Identity/set method as fallback...")
    except Exception as e:
        print(f"⚠️  {method_name} method failed: {e}")
    
    # Fallback to Identity/set method
    identity_payload = {
        "using": [
            "urn:ietf:params:jmap:core",
            "urn:ietf:params:jmap:mail",
            "urn:ietf:params:jmap:submission"
        ],
        "methodCalls": [
            [
                "Identity/set",
                {
                    "accountId": account_id,
                    "create": {
                        "k45": {
                            "name": description if description else f"Alias {alias_email}",
                            "email": alias_email,
                            "replyTo": [{"email": target_email}],
                            "bcc": None,
                            "textSignature": "",
                            "htmlSignature": ""
                        }
                    }
                },
                "0"
            ]
        ],
        "lastActivity": 0,
        "clientVersion": "b457b8b325-5000d76b8ac6ae6b"
    }
    
    try:
        response = requests.post(jmap_url, json=identity_payload, headers=headers, cookies=cookies)
        if response.status_code == 200:
            result = response.json()
            print("✅ Identity created successfully!")
            return True
        else:
            print(f"❌ Failed to create identity. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating identity: {e}")
        return False

def main():
    print("🥷 Fastmail Stealth Automated Alias Creator")
    print("=" * 50)
    
    # Check for headless mode argument
    headless = True
    if '--headed' in sys.argv:
        headless = False
        print("🖥️  Running in headed mode")
    else:
        print("👻 Running in stealth headless mode")
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        return False
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    print("📁 Make sure you have a .env file with credentials")
    
    success = create_alias_with_stealth_playwright(alias_email, target_email, description, headless=headless)
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
        return True
    else:
        print("\n❌ Failed to create alias. Please try again.")
        return False

if __name__ == "__main__":
    main() 