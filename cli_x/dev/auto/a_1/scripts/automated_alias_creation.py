#!/usr/bin/env python3
"""
Automated Fastmail alias creation using Playwright
This script will:
1. Launch a browser
2. Navigate to Fastmail
3. Automatically log in with credentials from environment variables
4. Extract session data automatically
5. Create the alias using the JMAP API
"""

from playwright.sync_api import sync_playwright
import requests
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")  # Load from Y/.env

def create_alias_with_playwright(alias_email, target_email, description="", username=None, password=None):
    """Create an alias using Playwright to extract session data automatically"""
    
    # Use provided credentials or load from environment (Infisical format first, then fallback)
    username = username or os.getenv("FM_M_0") or os.getenv("FASTMAIL_USERNAME")
    password = password or os.getenv("FM_P_0") or os.getenv("FASTMAIL_PASSWORD")
    
    if not username or not password:
        print("❌ FastMail credentials not found!")
        print("Looking for either Infisical secrets (FM_M_0, FM_P_0) or .env variables (FASTMAIL_USERNAME, FASTMAIL_PASSWORD)")
        return False
    
    with sync_playwright() as p:
        # Launch browser in headless mode for automation
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print("🌐 Navigating to Fastmail...")
        page.goto("https://app.fastmail.com")
        
        if username and password:
            print("🔐 Attempting automatic login...")
            try:
                # Wait for login form to appear
                page.wait_for_selector('input[name="username"], input[type="email"], input[placeholder*="email"], input[placeholder*="username"]', timeout=10000)
                
                # Find and fill username field
                username_selectors = [
                    'input[name="username"]',
                    'input[type="email"]', 
                    'input[placeholder*="email"]',
                    'input[placeholder*="username"]',
                    'input[id*="email"]',
                    'input[id*="username"]'
                ]
                
                username_filled = False
                for selector in username_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.fill(selector, username)
                            print(f"✅ Filled username field: {selector}")
                            username_filled = True
                            break
                    except:
                        continue
                
                if not username_filled:
                    print("⚠️  Could not find username field, trying manual approach...")
                    print("👤 Please enter your username manually and press Enter here when done...")
                    input()
                else:
                    # Wait for Continue button to be ready
                    print("⏳ Waiting for Continue button to be ready...")
                    
                    # Look for and click Continue/Next button
                    continue_clicked = False
                    continue_buttons = [
                        'button:has-text("Continue")',
                        'button:has-text("Next")', 
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Sign in")',
                        'button:has-text("Log in")'
                    ]
                    
                    for button_selector in continue_buttons:
                        try:
                            if page.locator(button_selector).count() > 0:
                                page.click(button_selector)
                                print(f"✅ Clicked Continue button: {button_selector}")
                                continue_clicked = True
                                break
                        except:
                            continue
                    
                    if continue_clicked:
                        print("⏳ Waiting for password field to appear...")
                        # Dynamic wait handled below
                    
                    # Wait for password field to appear
                    try:
                        page.wait_for_selector('input[type="password"], input[name="password"]', timeout=8000)
                        print("✅ Password field appeared")
                    except:
                        print("⚠️  Password field didn't appear, trying to continue anyway...")
                    
                    # Fill password field
                    password_selectors = [
                        'input[name="password"]',
                        'input[type="password"]',
                        'input[placeholder*="password"]',
                        'input[id*="password"]'
                    ]
                    
                    password_filled = False
                    for selector in password_selectors:
                        try:
                            if page.locator(selector).count() > 0:
                                page.fill(selector, password)
                                print(f"✅ Filled password field: {selector}")
                                password_filled = True
                                break
                        except:
                            continue
                    
                    if password_filled:
                        # Wait for submit button to be ready
                        print("⏳ Waiting for submit button to be ready...")
                        page.wait_for_selector('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")', timeout=5000)
                        
                        # Submit the login form
                        submit_buttons = [
                            'button[type="submit"]',
                            'button:has-text("Sign in")',
                            'button:has-text("Log in")',
                            'button:has-text("Login")',
                            'input[type="submit"]',
                            'button:has-text("Continue")'  # Sometimes the second step also uses Continue
                        ]
                        
                        login_clicked = False
                        for button_selector in submit_buttons:
                            try:
                                if page.locator(button_selector).count() > 0:
                                    page.click(button_selector)
                                    print(f"✅ Clicked login button: {button_selector}")
                                    login_clicked = True
                                    break
                            except:
                                continue
                        
                        if not login_clicked:
                            print("⚠️  Could not find login button, trying Enter key...")
                            try:
                                page.keyboard.press('Enter')
                                print("✅ Pressed Enter key")
                            except:
                                print("⚠️  Enter key failed too")
                        
                        # Wait for login processing to start
                        print("⏳ Waiting for login to process...")
                        page.wait_for_timeout(1000)  # Brief wait to allow login to initiate
                        
                        # Wait for login to complete
                        print("⏳ Waiting for login to complete...")
                        try:
                            page.wait_for_url("**/app.fastmail.com/**", timeout=15000)
                            print("✅ Login successful!")
                        except:
                            print("⚠️  URL didn't change, but continuing - login might still be successful...")
                        
                        # Wait for session to be established with balanced timing
                        print("⏳ Waiting for session to be established...")
                        
                        # Initial wait for session to settle
                        page.wait_for_timeout(2500)  # Conservative wait for session
                        
                        # Check cookie count
                        cookies = context.cookies()
                        fastmail_cookies = [c for c in cookies if '.fastmail.com' in c['domain'] or 'app.fastmail.com' in c['domain']]
                        
                        if len(fastmail_cookies) >= 2:
                            print(f"✅ Session ready with {len(fastmail_cookies)} cookies")
                        else:
                            print(f"⚠️  Only {len(fastmail_cookies)} cookies found, adding extra wait...")
                            page.wait_for_timeout(2000)  # Extra wait if needed
                            cookies = context.cookies()
                            fastmail_cookies = [c for c in cookies if '.fastmail.com' in c['domain'] or 'app.fastmail.com' in c['domain']]
                            print(f"📊 Final cookie count: {len(fastmail_cookies)}")
                    else:
                        print("⚠️  Could not find password field, please complete login manually...")
                        print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
                        input()
                        
            except Exception as e:
                print(f"⚠️  Password step failed: {e}")
                print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
                input()
                        
            except Exception as e:
                print(f"⚠️  Automatic login failed: {e}")
                print("👤 Please log in to your Fastmail account manually in the browser window")
                print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
                input()
        else:
            print("👤 Please log in to your Fastmail account in the browser window")
            print("📝 Navigate to Settings > Aliases after logging in")
            print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
            input()
        
        print("🔍 Extracting session data...")
        
        # Give a moment for any final session setup
        page.wait_for_timeout(1000)
        
        # Extract cookies
        cookies_dict = {}
        cookies = context.cookies()
        for cookie in cookies:
            if cookie['domain'] in ['.fastmail.com', 'app.fastmail.com', 'api.fastmail.com']:
                cookies_dict[cookie['name']] = cookie['value']
        
        print(f"🍪 Found {len(cookies_dict)} cookies")
        
        # Navigate to trigger a JMAP API call to get the Bearer token
        print("🔗 Making a request to extract Bearer token...")
        
        # Set up request interception to capture the Bearer token
        bearer_token = None
        user_id = None
        account_id = None
        
        def handle_request(request):
            nonlocal bearer_token, user_id, account_id
            if 'api.fastmail.com/jmap/api/' in request.url:
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
        
        # Wait for Bearer token capture with timeout
        bearer_captured = False
        def check_bearer_captured():
            nonlocal bearer_captured
            if bearer_token and user_id:
                bearer_captured = True
                return True
            return False
        
        # Navigate to aliases page to trigger API calls
        try:
            page.goto("https://app.fastmail.com/settings/aliases")
            # Wait for page to load (domcontentloaded is more reliable than networkidle)
            page.wait_for_load_state("domcontentloaded", timeout=8000)
            page.wait_for_timeout(2000)  # Wait for initial API calls to trigger
        except:
            print("⚠️  Couldn't navigate to aliases page, trying alternative method...")
            # Try making any action that triggers an API call
            page.evaluate("window.location.reload()")
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            page.wait_for_timeout(2000)
        
        # Wait for Bearer token to be captured
        print("⏳ Waiting for Bearer token capture...")
        for i in range(20):  # Max 10 seconds
            if bearer_token and user_id:
                print("✅ Bearer token captured successfully!")
                break
            page.wait_for_timeout(500)
        else:
            print("⚠️  Bearer token not captured, will try to proceed...")
        
        # Try to extract account ID from page content or storage
        try:
            # Check if we can get account ID from localStorage or similar
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
                # Fallback: use the known account ID from the logs
                account_id = "c75164099"
                print(f"⚠️  Using fallback account ID: {account_id}")
            else:
                print(f"✅ Extracted Account ID: {account_id}")
                
        except:
            account_id = "c75164099"  # Fallback
            print(f"⚠️  Using fallback account ID: {account_id}")
        
        browser.close()
        
        if not bearer_token or not user_id:
            print("❌ Failed to extract session data. Please try again.")
            return False
        
        # Now create the alias using the extracted data
        print(f"🎯 Creating alias: {alias_email} -> {target_email}")
        return create_alias_api(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description)

def create_alias_api(bearer_token, user_id, account_id, cookies, alias_email, target_email, description=""):
    """Create alias using the JMAP API with extracted session data"""
    
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
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        if response.status_code == 200:
            result = response.json()
            print("✅ Alias created successfully!")
            
            # Check if there were any errors in the response
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

if __name__ == "__main__":
    print("🚀 Fastmail Automated Alias Creator")
    print("=" * 40)
    
    # Load credentials from environment variables (Infisical format first, then fallback)
    USERNAME = os.getenv("FM_M_0") or os.getenv("FASTMAIL_USERNAME")
    PASSWORD = os.getenv("FM_P_0") or os.getenv("FASTMAIL_PASSWORD")
    
    if not USERNAME or not PASSWORD:
        print("❌ FastMail credentials not found in environment variables!")
        print("Looking for either Infisical secrets (FM_M_0, FM_P_0) or .env variables (FASTMAIL_USERNAME, FASTMAIL_PASSWORD)")
        exit(1)
    
    # Get alias details from command line or use defaults for testing
    import sys
    if len(sys.argv) >= 3:
        alias_email = sys.argv[1]
        target_email = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""
    else:
        # Default values for testing
        alias_email = "nya19@fastmail.com"
        target_email = "wg0@fastmail.com"
        description = "Test alias"
    
    print(f"📧 Alias email: {alias_email}")
    print(f"🎯 Target email: {target_email}")
    print(f"📝 Description: {description}")
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    success = create_alias_with_playwright(alias_email, target_email, description, USERNAME, PASSWORD)
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
    else:
        print("\n❌ Failed to create alias. Please try again.") 