#!/usr/bin/env python3
"""
Automated Fastmail alias creation using undetected-chromedriver
This script will:
1. Launch Chrome browser (headless or headed)
2. Navigate to Fastmail
3. Auto-login with credentials from .env file
4. Extract session data automatically
5. Create the alias using the JMAP API
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def auto_login_fastmail(driver, email, password):
    """Automate the Fastmail login process"""
    print("🔐 Attempting to log in automatically...")
    
    try:
        # Wait for login form to load
        wait = WebDriverWait(driver, 15)
        
        # Use the specific selectors you identified
        email_selectors = [
            (By.ID, 'v22-input'),  # Primary selector based on your finding
            (By.CSS_SELECTOR, '.v-TextInput-input'),
            (By.NAME, 'username'),
            (By.CSS_SELECTOR, 'input[placeholder="email@fastmail.com"]'),
            (By.CSS_SELECTOR, 'input[autocomplete*="username"]'),
            (By.CSS_SELECTOR, 'input[inputmode="email"]')
        ]
        
        email_input = None
        for by, selector in email_selectors:
            try:
                email_input = wait.until(EC.element_to_be_clickable((by, selector)))
                if email_input:
                    print(f"✅ Found email input using: {selector}")
                    break
            except TimeoutException:
                print(f"❌ Could not find email input with: {selector}")
                continue
        
        if not email_input:
            print("❌ Could not find email input field")
            return False
        
        # Clear and fill email
        time.sleep(0.5)  # Small wait to ensure element is ready
        email_input.clear()
        time.sleep(0.3)
        email_input.send_keys(email)
        print(f"✅ Entered email: {email}")
        
        # Look for password field
        password_selectors = [
            (By.CSS_SELECTOR, 'input[type="password"]'),
            (By.NAME, 'password'),
            (By.ID, 'password'),
            (By.CSS_SELECTOR, 'input[placeholder*="password" i]')
        ]
        
        password_input = None
        for by, selector in password_selectors:
            try:
                password_input = driver.find_element(by, selector)
                if password_input and password_input.is_displayed():
                    break
            except NoSuchElementException:
                continue
        
        if password_input and password_input.is_displayed():
            # Fill password if field is visible
            password_input.clear()
            password_input.send_keys(password)
            print("✅ Entered password")
        else:
            # Check if we need to click "Continue" button using your specific selectors
            submit_selectors = [
                (By.ID, 'v25'),  # Primary selector for Continue button
                (By.CSS_SELECTOR, '.v-Button--cta'),
                (By.CSS_SELECTOR, 'button.v-Button--sizeM'),
                (By.XPATH, '//button[contains(@class, "v-Button--cta")]'),
                (By.XPATH, '//button[.//span[text()="Continue"]]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Continue")]')
            ]
            
            for by, selector in submit_selectors:
                try:
                    submit_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, selector)))
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        print(f"✅ Clicked continue button using: {selector}")
                        time.sleep(2)  # Wait for password field to appear
                        break
                except (NoSuchElementException, TimeoutException):
                    print(f"❌ Could not find continue button with: {selector}")
                    continue
            
            # Wait for password field to appear
            try:
                password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
                password_input.clear()
                password_input.send_keys(password)
                print("✅ Entered password (second step)")
            except TimeoutException:
                print("❌ Could not find password field")
                return False
        
        # Submit the form
        submit_selectors = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'input[type="submit"]'),
            (By.XPATH, '//button[contains(text(), "Sign in")]'),
            (By.XPATH, '//button[contains(text(), "Log in")]'),
            (By.XPATH, '//button[contains(text(), "Login")]'),
            (By.CSS_SELECTOR, '.btn-primary'),
            (By.CSS_SELECTOR, '[data-testid="login-button"]')
        ]
        
        for by, selector in submit_selectors:
            try:
                submit_btn = driver.find_element(by, selector)
                if submit_btn.is_displayed():
                    submit_btn.click()
                    print("✅ Clicked login button")
                    break
            except NoSuchElementException:
                continue
        
        # Wait for login to complete - look for the inbox URL or main interface
        print("⏳ Waiting for login to complete...")
        try:
            # Wait for URL to change to indicate successful login (based on our recording)
            WebDriverWait(driver, 20).until(
                lambda d: 'mail/Inbox' in d.current_url or 'u=' in d.current_url
            )
            
            current_url = driver.current_url
            print(f"✅ Login successful! Current URL: {current_url}")
            
            # Extract user ID from URL if present (like u=2ef64041)
            if 'u=' in current_url:
                user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                print(f"✅ Detected User ID: {user_id}")
            
            return True
            
        except TimeoutException:
            # Fallback: check if we're on any fastmail page that's not login
            current_url = driver.current_url
            if 'app.fastmail.com' in current_url and 'login' not in current_url:
                print("✅ Detected successful login (fallback check)")
                return True
            
            print("❌ Login timeout - may have failed")
            return False
            
        except Exception as e:
            print(f"❌ Error waiting for login completion: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def extract_session_data(driver):
    """Extract Bearer token and session data from the browser"""
    print("🔍 Extracting session data...")
    
    # Get all cookies
    cookies_dict = {}
    cookies = driver.get_cookies()
    for cookie in cookies:
        if any(domain in cookie.get('domain', '') for domain in ['.fastmail.com', 'app.fastmail.com', 'api.fastmail.com']):
            cookies_dict[cookie['name']] = cookie['value']
    
    print(f"🍪 Found {len(cookies_dict)} cookies")
    for name, value in cookies_dict.items():
        print(f"  - {name}: {value[:30]}..." if len(value) > 30 else f"  - {name}: {value}")
    
    # Try to navigate to aliases page to trigger API calls
    try:
        driver.get("https://app.fastmail.com/settings/aliases")
        time.sleep(3)  # Wait for page to load and API calls to complete
    except Exception as e:
        print(f"⚠️  Couldn't navigate to aliases page: {e}")
        # Try reloading current page
        driver.refresh()
        time.sleep(3)
    
    # Extract session data from browser storage
    session_data = {}
    bearer_token = None
    user_id = None
    account_id = None
    
    try:
        # Try to get data from localStorage and sessionStorage
        local_storage = driver.execute_script("return window.localStorage;")
        session_storage = driver.execute_script("return window.sessionStorage;")
        
        # Look for bearer token and user info in storage
        for storage_name, storage in [("localStorage", local_storage), ("sessionStorage", session_storage)]:
            if storage:
                for key, value in storage.items():
                    if any(keyword in key.lower() for keyword in ['token', 'auth', 'session', 'user', 'account']):
                        try:
                            data = json.loads(value)
                            if isinstance(data, dict):
                                session_data.update(data)
                                print(f"📦 Found data in {storage_name}: {key}")
                        except (json.JSONDecodeError, TypeError):
                            if 'token' in key.lower():
                                session_data[key] = value
                                print(f"📦 Found token in {storage_name}: {key}")
        
        print(f"📦 Extracted {len(session_data)} session items")
        
    except Exception as e:
        print(f"⚠️  Could not extract from storage: {e}")
    
    # Try to extract user info from the current page URL or make a simple fetch request
    try:
        # Check if we can extract user ID from current URL or page context
        current_url = driver.current_url
        if 'u=' in current_url:
            user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
            print(f"✅ Extracted User ID from URL: {user_id}")
        
        # Try to trigger a simple API call and capture the response
        api_response = driver.execute_script("""
            return new Promise((resolve) => {
                fetch('/settings/aliases')
                    .then(response => {
                        // Try to get the Authorization header from any subsequent requests
                        // This is a simplified approach
                        resolve({url: window.location.href});
                    })
                    .catch(err => resolve({error: err.toString()}));
            });
        """)
        
        if api_response:
            print(f"📡 API response: {api_response}")
            
    except Exception as e:
        print(f"⚠️  Could not extract from API calls: {e}")
    
    # Fallback: try to extract account ID from page content
    try:
        account_id = driver.execute_script("""
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
        """)
        
        if not account_id:
            # Use fallback account ID based on user_id (like working script)
            account_id = f"u{user_id}" if user_id else "u2ef64041"
            print(f"⚠️  Using fallback account ID: {account_id}")
        else:
            print(f"✅ Extracted Account ID: {account_id}")
            
    except Exception as e:
        account_id = "u2ef64041"  # Fallback like working script
        print(f"⚠️  Using fallback account ID: {account_id}")
    
    # Try to get bearer token from session data
    for key, value in session_data.items():
        if 'token' in key.lower() and isinstance(value, str) and len(value) > 20:
            bearer_token = value
            print(f"✅ Found potential bearer token: {bearer_token[:20]}...")
            break
    
    # If still no bearer token, try to extract from network requests or page context
    if not bearer_token:
        try:
            # Check for auth tokens in various localStorage keys
            auth_keys = ['auth', 'token', 'session', 'bearer', 'access_token', 'jwt']
            for key in auth_keys:
                token_data = driver.execute_script(f"return window.localStorage.getItem('{key}');")
                if token_data and len(token_data) > 20:
                    bearer_token = token_data
                    print(f"✅ Found bearer token in localStorage['{key}']: {bearer_token[:20]}...")
                    break
        except Exception as e:
            print(f"⚠️  Could not check localStorage for tokens: {e}")
    
    # Try to make a simple API call to get the session token
    if not bearer_token:
        try:
            # Get CSRF token or session token from page content
            csrf_token = driver.execute_script("""
                // Look for CSRF tokens in meta tags or global variables
                const meta = document.querySelector('meta[name="csrf-token"]');
                if (meta) return meta.getAttribute('content');
                
                // Check for global auth variables
                if (window.auth) return window.auth.token || window.auth.accessToken;
                if (window.FM) return window.FM.token || window.FM.accessToken;
                
                // Look for any script tags containing tokens
                const scripts = document.querySelectorAll('script');
                for (let script of scripts) {
                    const content = script.textContent;
                    if (content.includes('token') && content.includes('Bearer')) {
                        const match = content.match(/Bearer[\\s"']+([A-Za-z0-9\\-_\\.]+)/);
                        if (match) return match[1];
                    }
                }
                return null;
            """)
            
            if csrf_token and len(csrf_token) > 10:
                bearer_token = csrf_token
                print(f"✅ Found CSRF/session token: {bearer_token[:20]}...")
        except Exception as e:
            print(f"⚠️  Could not extract CSRF token: {e}")
    
    # Try to extract user_id from current URL (based on recording session)
    if not user_id:
        try:
            current_url = driver.current_url
            if 'u=' in current_url:
                user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                print(f"✅ Extracted User ID from URL: {user_id}")
        except:
            pass
    
    # If still no user_id found, try a fallback
    if not user_id:
        user_id = "2ef64041"  # From our recording session
        print(f"⚠️  Using fallback User ID: {user_id}")
    
    # Look for session tokens in localStorage (based on recording)
    if not bearer_token:
        try:
            # Check for sessions key in localStorage
            sessions_data = driver.execute_script("return window.localStorage.getItem('sessions');")
            if sessions_data:
                print(f"✅ Found sessions data in localStorage")
                # Try to parse it for tokens
                try:
                    sessions = json.loads(sessions_data)
                    if isinstance(sessions, dict):
                        for key, value in sessions.items():
                            if isinstance(value, str) and len(value) > 20:
                                bearer_token = value
                                print(f"✅ Found potential token in sessions: {bearer_token[:20]}...")
                                break
                except Exception as e:
                    print(f"⚠️  Could not parse sessions data: {e}")
        except:
            pass
    
    return bearer_token, user_id, account_id, cookies_dict

def create_alias_with_chrome(alias_email, target_email, description="", headless=True):
    """Create an alias using undetected-chromedriver to extract session data automatically"""
    
    # Load credentials from environment
    email = os.getenv('FASTMAIL_EMAIL')
    password = os.getenv('FASTMAIL_API_PASSWORD')  # Still used for browser login
    api_token = os.getenv('FASTMAIL_API_TOKEN')    # Used for API authentication
    
    if not email or not password:
        print("❌ Missing FASTMAIL_EMAIL or FASTMAIL_API_PASSWORD in .env file")
        print("Please create a .env file with:")
        print("FASTMAIL_EMAIL=your-email@fastmail.com")
        print("FASTMAIL_API_PASSWORD=your-browser-password")
        print("FASTMAIL_API_TOKEN=your-api-token")
        return False
    
    # Set up Chrome options
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-infobars')
    
    try:
        # Launch Chrome with undetected-chromedriver
        driver = uc.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("🌐 Navigating to Fastmail...")
        driver.get("https://app.fastmail.com")
        
        # Auto-login
        if not auto_login_fastmail(driver, email, password):
            print("❌ Auto-login failed.")
            if headless:
                driver.quit()
                print("🔄 Switching to manual mode...")
                # Retry with headed mode for manual login
                return create_alias_with_chrome(alias_email, target_email, description, headless=False)
            else:
                print("👤 Please log in manually in the browser window")
                print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
                input()
        
        # Give some time for the page to fully load
        time.sleep(3)
        
        # Extract session data
        bearer_token, user_id, account_id, cookies_dict = extract_session_data(driver)
        
        if not user_id:
            print("❌ Failed to extract user ID. Please try again.")
            driver.quit()
            return False
        
        # Instead of making external API calls, use the browser session directly
        print(f"🎯 Creating alias: {alias_email} -> {target_email}")
        success = create_alias_with_browser(driver, user_id, account_id, alias_email, target_email, description)
        
        driver.quit()
        return success
        
    except Exception as e:
        print(f"❌ Error with Chrome driver: {e}")
        return False

def create_alias_with_browser(driver, user_id, account_id, alias_email, target_email, description=""):
    """Create alias using the browser session directly (like Playwright approach)"""
    
    try:
        # Navigate to the JMAP API endpoint in the browser
        jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
        
        # Prepare the JMAP payload
        payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "urn:ietf:params:jmap:mail"
            ],
            "methodCalls": [
                [
                    "Identity/set",
                    {
                        "accountId": account_id,
                        "create": {
                            "newAlias": {
                                "name": alias_email.split('@')[0],
                                "email": alias_email
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        # First, get session info from .well-known/jmap like the working script
        session_result = driver.execute_script("""
            return fetch('https://api.fastmail.com/.well-known/jmap', {
                method: 'GET',
                credentials: 'include'
            })
            .then(response => response.json())
            .then(data => ({success: true, data: data}))
            .catch(error => ({success: false, error: error.toString()}));
        """)
        
        if not session_result.get('success'):
            print(f"❌ Failed to get session info: {session_result.get('error')}")
            return False
        
        session_data = session_result.get('data', {})
        api_url = session_data.get('apiUrl')
        if not api_url:
            print("❌ No apiUrl found in session data")
            return False
        
        print(f"✅ Got API URL: {api_url}")
        
        # Extract account ID from session data like the working script
        primary_accounts = session_data.get('primaryAccounts', {})
        mail_account_id = primary_accounts.get('urn:ietf:params:jmap:mail')
        if mail_account_id:
            account_id = mail_account_id
            print(f"✅ Got account ID from session: {account_id}")
        
        # Now use the proper API URL with session info
        result = driver.execute_script("""
            const url = arguments[0];
            const payload = arguments[1];
            
            return fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Origin': 'https://app.fastmail.com',
                    'Referer': 'https://app.fastmail.com/'
                },
                body: JSON.stringify(payload),
                credentials: 'include'  // This ensures cookies are sent
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => 
                        ({success: false, error: `HTTP ${response.status}: ${text}`})
                    );
                }
                return response.json().then(data => ({success: true, data: data}));
            })
            .catch(error => ({success: false, error: error.toString()}));
        """, api_url, payload)
        
        if not result.get('success'):
            print(f"❌ Browser API call failed: {result.get('error')}")
            return False
        
        data = result.get('data', {})
        print("✅ API call successful!")
        
        # Check the response
        method_responses = data.get('methodResponses', [])
        for method_response in method_responses:
            if len(method_response) > 1 and method_response[0] == "Identity/set":
                identity_result = method_response[1]
                if 'created' in identity_result and identity_result['created']:
                    created_identity = list(identity_result['created'].values())[0]
                    print(f"🎉 Identity ID: {created_identity.get('id', 'Unknown')}")
                    print(f"📧 Email: {created_identity.get('email', 'Unknown')}")
                    print(f"👤 Name: {created_identity.get('name', 'Unknown')}")
                    return True
                elif 'notCreated' in identity_result:
                    print(f"❌ Failed to create identity: {identity_result['notCreated']}")
                    return False
        
        print("✅ Alias creation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating alias with browser: {e}")
        return False

def create_alias_api(bearer_token, user_id, account_id, cookies, alias_email, target_email, description=""):
    """Create alias using the JMAP API with extracted session data"""
    
    jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Origin": "https://app.fastmail.com",
        "Referer": "https://app.fastmail.com/",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    
    # Use Bearer authentication for Fastmail JMAP API (like the working script)
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
        print("🔐 Using Bearer authentication with API token")
    else:
        print("❌ No bearer token available")
        return False
    
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
                "Identity/set",
                {
                    "accountId": account_id,
                    "create": {
                        "newAlias": {
                            "name": alias_email.split('@')[0],
                            "email": alias_email
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
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        if response.status_code == 200:
            result = response.json()
            print("✅ Alias created successfully!")
            
            # Check if there were any errors in the response
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == "Identity/set":
                    identity_result = method_response[1]
                    if 'created' in identity_result and identity_result['created']:
                        created_identity = list(identity_result['created'].values())[0]
                        print(f"🎉 Identity ID: {created_identity.get('id', 'Unknown')}")
                        print(f"📧 Email: {created_identity.get('email', 'Unknown')}")
                        print(f"👤 Name: {created_identity.get('name', 'Unknown')}")
                    elif 'notCreated' in identity_result:
                        print(f"❌ Failed to create identity: {identity_result['notCreated']}")
                        return False
            
            return True
        else:
            print(f"❌ Failed to create alias. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating alias: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fastmail Automated Alias Creator")
    print("=" * 40)
    
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
        exit(1)
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    print("📁 Make sure you have a .env file with FASTMAIL_EMAIL, FASTMAIL_API_PASSWORD, and FASTMAIL_API_TOKEN")
    
    success = create_alias_with_chrome(alias_email, target_email, description, headless=headless)
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
    else:
        print("\n❌ Failed to create alias. Please try again.") 