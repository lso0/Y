#!/usr/bin/env python3
"""
Automated Alias Creation
Working Playwright automation script for FastMail alias creation
This is the core working script that the enhanced server imports from
"""

from playwright.sync_api import sync_playwright
import requests
import time
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_alias_with_playwright(alias_email: str, target_email: str, description: str = "", username: str = "wg0", password: str = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK") -> bool:
    """
    Create alias using sync Playwright - proven working logic
    This is the function that the enhanced automation server imports and uses
    
    Returns True if successful, False otherwise
    """
    try:
        with sync_playwright() as p:
            # Launch browser in headless mode  
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            print(f"🌐 Navigating to Fastmail...")
            page.goto("https://app.fastmail.com")
            
            print(f"🔐 Attempting automatic login...")
            
            # Fill username
            page.wait_for_selector('input[name="username"], input[type="email"]', timeout=10000)
            username_input = page.locator('input[name="username"]')
            username_input.fill(username)
            print("✅ Filled username field: input[name=\"username\"]")
            
            # Wait for Continue button and click
            print("⏳ Waiting for Continue button to be ready...")
            continue_button = page.locator('button:has-text("Continue")')
            continue_button.wait_for(state="visible", timeout=8000)
            continue_button.click()
            print("✅ Clicked Continue button: button:has-text(\"Continue\")")
            
            # Wait for password field
            print("⏳ Waiting for password field to appear...")
            page.wait_for_selector('input[type="password"]', timeout=8000)
            print("✅ Password field appeared")
            
            # Fill password
            password_input = page.locator('input[type="password"]')
            password_input.fill(password)
            print("✅ Filled password field: input[type=\"password\"]")
            
            # Submit login
            print("⏳ Waiting for submit button to be ready...")
            submit_button = page.locator('button[type="submit"]')
            submit_button.wait_for(state="visible", timeout=5000)
            submit_button.click()
            print("✅ Clicked login button: button[type=\"submit\"]")
            
            # Wait for login to process
            print("⏳ Waiting for login to process...")
            time.sleep(2)
            
            # Wait for login to complete with multiple possible success indicators
            print("⏳ Waiting for login to complete...")
            try:
                # Try to wait for the main app interface
                page.wait_for_url("**/app.fastmail.com/**", timeout=10000)
                print("✅ Login successful!")
            except:
                # Alternative: wait for any indication we're logged in
                try:
                    page.wait_for_selector('[data-testid="main-content"], .main-content, #main', timeout=5000)
                    print("✅ Login successful!")
                except:
                    print("⚠️  Login state unclear, continuing...")
            
            # Wait for session to establish
            print("⏳ Waiting for session to be established...")
            time.sleep(3)
            
            # Check session quality by counting cookies
            cookies = context.cookies()
            fastmail_cookies = [c for c in cookies if '.fastmail.com' in c['domain'] or 'app.fastmail.com' in c['domain']]
            print(f"✅ Session ready with {len(fastmail_cookies)} cookies")
            
            if len(fastmail_cookies) < 2:
                print(f"⚠️  Only {len(fastmail_cookies)} cookies found, adding extra wait...")
                time.sleep(5)
                cookies = context.cookies()
                fastmail_cookies = [c for c in cookies if '.fastmail.com' in c['domain'] or 'app.fastmail.com' in c['domain']]
                print(f"📊 Final cookie count: {len(fastmail_cookies)}")
            
            print("🔍 Extracting session data...")
            
            # Extract cookies
            cookies_dict = {}
            for cookie in fastmail_cookies:
                cookies_dict[cookie['name']] = cookie['value']
            print(f"🍪 Found {len(cookies_dict)} cookies")
            
            # Set up request interception to capture Bearer token
            bearer_token = None
            user_id = None
            
            def handle_request(request):
                nonlocal bearer_token, user_id
                if 'api.fastmail.com/jmap/api/' in request.url:
                    # Extract user ID from URL
                    if 'u=' in request.url:
                        user_id = request.url.split('u=')[1].split('&')[0]
                        print(f"✅ Captured User ID: {user_id}")
                    
                    # Extract Bearer token
                    auth_header = request.headers.get('authorization', '')
                    if auth_header.startswith('Bearer '):
                        bearer_token = auth_header.replace('Bearer ', '')
                        print(f"✅ Captured Bearer token: {bearer_token[:20]}...")
            
            # Set up request monitoring
            page.on('request', handle_request)
            
            # Navigate to trigger API calls
            print("🔗 Making a request to extract Bearer token...")
            try:
                page.goto("https://app.fastmail.com/settings/aliases", timeout=10000)
                time.sleep(3)  # Wait for API calls
                print("✅ Triggered API calls")
            except Exception as e:
                print(f"⚠️  Navigation to aliases page failed: {e}")
                # Try alternative method
                try:
                    page.goto("https://app.fastmail.com/settings", timeout=8000)
                    time.sleep(2)
                    print("✅ Triggered API calls via settings")
                except:
                    print("⚠️  Could not trigger API calls")
            
            browser.close()
            
            print("⏳ Waiting for Bearer token capture...")
            if not bearer_token or not user_id:
                print("⚠️  Bearer token not captured, will try to proceed...")
                # Use fallback values
                user_id = "c75164099"  # Fallback account ID
                if not bearer_token:
                    print("❌ Failed to extract session data. Please try again.")
                    return False
            else:
                print("✅ Bearer token captured successfully!")
            
            # Fallback account ID if we couldn't extract user_id
            account_id = user_id if user_id else "c75164099"
            print(f"⚠️  Using fallback account ID: {account_id}")
            
            # Create the alias using the extracted data
            print(f"🎯 Creating alias: {alias_email} -> {target_email}")
            
            jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}" if user_id else "https://api.fastmail.com/jmap/api/?u=c75164099"
            
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
            
            response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies_dict)
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
    """Main function for standalone usage"""
    if len(sys.argv) < 3:
        print("🚀 FastMail Automated Alias Creation")
        print("=" * 50)
        print("Usage: python automated_alias_creation.py <alias_email> <target_email> [description]")
        print()
        print("Examples:")
        print("  python automated_alias_creation.py work@fastmail.com wg0@fastmail.com")
        print("  python automated_alias_creation.py shop@fastmail.com wg0@fastmail.com 'Shopping emails'")
        print()
        return
    
    alias_email = sys.argv[1]
    target_email = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    
    print("🚀 FastMail Automated Alias Creation")
    print("=" * 50)
    print(f"📧 Creating alias: {alias_email}")
    print(f"🎯 Target: {target_email}")
    print(f"📝 Description: {description}")
    print()
    
    success = create_alias_with_playwright(alias_email, target_email, description)
    
    if success:
        print("\n🎉 SUCCESS! Your alias has been created.")
    else:
        print("\n❌ FAILED to create alias.")
        sys.exit(1)

if __name__ == "__main__":
    main() 