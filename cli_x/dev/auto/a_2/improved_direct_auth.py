#!/usr/bin/env python3
"""
Improved Direct HTTP Authentication to Fastmail
This script handles the successful login response and extracts session tokens.
"""

import requests
import json
import re
import time
from urllib.parse import urljoin, urlparse

class FastmailDirectAuth:
    """Direct HTTP authentication that handles successful login responses."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        self.bearer_token = None
        self.account_id = None
        self.api_url = None
        
    def authenticate(self):
        """Perform direct HTTP authentication with proper response handling."""
        print("🔐 Starting Improved Direct HTTP Authentication...")
        print("=" * 60)
        
        try:
            # Step 1: Get initial login page and extract any required tokens
            print("📄 Step 1: Getting login page...")
            login_page = self.session.get('https://www.fastmail.com/login/')
            
            if login_page.status_code != 200:
                print(f"   ❌ Failed to load login page: {login_page.status_code}")
                return False
            
            print("   ✅ Login page loaded successfully")
            
            # Extract any form tokens or hidden fields
            csrf_token = self._extract_csrf_token(login_page.text)
            
            # Step 2: Perform the actual login
            print("\n🔑 Step 2: Performing login...")
            login_data = {
                'username': self.username,
                'password': self.password,
                'action': 'login',
                'rememberme': '1'
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
                print(f"   🔑 Using CSRF token: {csrf_token[:20]}...")
            
            # Set headers for the login request
            login_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.fastmail.com',
                'Referer': 'https://www.fastmail.com/login/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            # Perform login
            response = self.session.post(
                'https://www.fastmail.com/login/',
                data=login_data,
                headers=login_headers,
                allow_redirects=True
            )
            
            print(f"   🎯 Login response status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Login request successful!")
                
                # Check if we're now authenticated
                if self._check_authentication_success(response):
                    print("   🎉 Authentication successful!")
                    return self._extract_session_tokens()
                else:
                    print("   ⚠️  Login response received but authentication unclear")
                    return self._try_extract_tokens_anyway()
                    
            elif response.status_code == 302:
                print(f"   ↪️  Redirected to: {response.headers.get('Location', 'Unknown')}")
                return self._handle_redirect(response)
                
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_csrf_token(self, html_content):
        """Extract CSRF token from login page."""
        patterns = [
            r'name="csrf_token"\s+value="([^"]+)"',
            r'name="_token"\s+value="([^"]+)"',
            r'<input[^>]*name="csrf[^"]*"[^>]*value="([^"]+)"',
            r'csrf["\']:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _check_authentication_success(self, response):
        """Check if authentication was successful."""
        # Look for signs of successful authentication
        success_indicators = [
            'app.fastmail.com',
            'dashboard',
            'logout',
            'settings',
            'inbox',
            'Welcome'
        ]
        
        response_text = response.text.lower()
        for indicator in success_indicators:
            if indicator.lower() in response_text:
                print(f"   ✅ Found success indicator: {indicator}")
                return True
        
        # Check if we have authentication cookies
        auth_cookies = [cookie for cookie in self.session.cookies if 'auth' in cookie.name.lower() or 'session' in cookie.name.lower()]
        if auth_cookies:
            print(f"   ✅ Found {len(auth_cookies)} authentication cookies")
            return True
        
        # Check final URL
        if hasattr(response, 'url') and 'app.fastmail.com' in response.url:
            print("   ✅ Redirected to app.fastmail.com")
            return True
        
        return False
    
    def _handle_redirect(self, response):
        """Handle redirect responses."""
        location = response.headers.get('Location', '')
        
        if 'app.fastmail.com' in location:
            print("   🎉 Redirected to main app - authentication successful!")
            return self._extract_session_tokens()
        elif 'login' in location:
            print("   ❌ Redirected back to login - authentication failed")
            return False
        else:
            print(f"   ↪️  Following redirect to: {location}")
            try:
                redirect_response = self.session.get(location)
                if redirect_response.status_code == 200:
                    return self._check_authentication_success(redirect_response)
            except Exception as e:
                print(f"   ❌ Error following redirect: {e}")
            
            return False
    
    def _try_extract_tokens_anyway(self):
        """Try to extract tokens even if authentication status is unclear."""
        print("   🔍 Trying to extract tokens anyway...")
        
        # Try to access the main app directly
        try:
            app_response = self.session.get('https://app.fastmail.com/')
            
            if app_response.status_code == 200:
                print("   ✅ Successfully accessed main app")
                return self._extract_session_tokens()
            else:
                print(f"   ❌ Cannot access main app: {app_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error accessing main app: {e}")
        
        return False
    
    def _extract_session_tokens(self):
        """Extract session tokens from authenticated session."""
        print("🔍 Step 3: Extracting session tokens...")
        
        # Print current cookies for debugging
        print(f"   📊 Current cookies: {len(self.session.cookies)}")
        for cookie in self.session.cookies:
            print(f"      🍪 {cookie.name}: {cookie.value[:30]}...")
        
        # Try to access JMAP session endpoint
        try:
            jmap_response = self.session.get('https://api.fastmail.com/jmap/session')
            
            if jmap_response.status_code == 200:
                print("   ✅ JMAP session accessible!")
                
                try:
                    session_data = jmap_response.json()
                    print("   📋 Session data retrieved successfully")
                    
                    # Extract account information
                    if 'accounts' in session_data:
                        accounts = session_data['accounts']
                        self.account_id = list(accounts.keys())[0]
                        print(f"   📋 Account ID: {self.account_id}")
                    
                    if 'apiUrl' in session_data:
                        self.api_url = session_data['apiUrl']
                        print(f"   🔗 API URL: {self.api_url}")
                    
                    # Test alias creation
                    return self._test_alias_creation(session_data)
                    
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response from JMAP session")
                    return False
                    
            else:
                print(f"   ❌ JMAP session failed: {jmap_response.status_code}")
                print(f"   Response: {jmap_response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Error accessing JMAP session: {e}")
            return False
    
    def _test_alias_creation(self, session_data):
        """Test alias creation with the authenticated session."""
        print("🎯 Step 4: Testing alias creation...")
        
        try:
            api_url = session_data.get('apiUrl', 'https://api.fastmail.com/jmap/api/')
            account_id = self.account_id
            
            if not account_id:
                print("   ❌ No account ID available")
                return False
            
            # Test MaskedEmail creation
            test_payload = {
                "using": [
                    "urn:ietf:params:jmap:core",
                    "https://www.fastmail.com/dev/maskedemail"
                ],
                "methodCalls": [
                    [
                        "MaskedEmail/set",
                        {
                            "accountId": account_id,
                            "create": {
                                "test_direct": {
                                    "emailPrefix": f"directtest{int(time.time())}",
                                    "description": "Created via direct HTTP auth",
                                    "forwardingEmail": "wg0@fastmail.com"
                                }
                            }
                        },
                        "0"
                    ]
                ]
            }
            
            response = self.session.post(api_url, json=test_payload)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    if "methodResponses" in result:
                        method_response = result["methodResponses"][0]
                        
                        if method_response[0] == "MaskedEmail/set":
                            if "created" in method_response[1]:
                                created = method_response[1]["created"]["test_direct"]
                                print(f"   🎉 SUCCESS! Created test email: {created['email']}")
                                print(f"   📧 Forwarding to: {created.get('forwardingEmail', 'Unknown')}")
                                return True
                            else:
                                print(f"   ❌ Creation failed: {method_response[1]}")
                                return False
                        else:
                            print(f"   ❌ Unexpected response: {method_response}")
                            return False
                    else:
                        print(f"   ❌ No methodResponses in result: {result}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response: {response.text[:200]}...")
                    return False
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Error testing alias creation: {e}")
            return False
    
    def create_alias(self, email_prefix, description=""):
        """Create a new alias with the authenticated session."""
        if not self.account_id or not self.api_url:
            print("❌ Not authenticated - run authenticate() first")
            return False
        
        print(f"📧 Creating alias: {email_prefix}@fastmail.com")
        
        payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "methodCalls": [
                [
                    "MaskedEmail/set",
                    {
                        "accountId": self.account_id,
                        "create": {
                            "new_alias": {
                                "emailPrefix": email_prefix,
                                "description": description,
                                "forwardingEmail": "wg0@fastmail.com"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        try:
            response = self.session.post(self.api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    
                    if method_response[0] == "MaskedEmail/set" and "created" in method_response[1]:
                        created = method_response[1]["created"]["new_alias"]
                        print(f"🎉 SUCCESS! Created: {created['email']}")
                        return created['email']
                    else:
                        print(f"❌ Creation failed: {method_response}")
                        return False
            else:
                print(f"❌ Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating alias: {e}")
            return False

def main():
    """Main function to test improved direct HTTP authentication."""
    print("🚀 Improved Fastmail Direct HTTP Authentication")
    print("=" * 60)
    print("✅ Handles successful login responses properly!")
    print("✅ No browser required!")
    print("✅ Much faster than browser automation!")
    print()
    
    # Use the credentials from the user's previous attempts
    username = "wg0@fastmail.com"
    password = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"
    
    print(f"👤 Testing with username: {username}")
    print()
    
    auth = FastmailDirectAuth(username, password)
    
    start_time = time.time()
    success = auth.authenticate()
    duration = time.time() - start_time
    
    if success:
        print(f"\n🎉 COMPLETE SUCCESS!")
        print("=" * 60)
        print(f"✅ Authenticated and tested in {duration:.2f} seconds")
        print("✅ This is the headless automation you wanted!")
        print("✅ Ready for production alias creation!")
        
        # Test creating a real alias
        print("\n🎯 Testing real alias creation...")
        alias_email = auth.create_alias("directauth01", "Created via direct HTTP authentication")
        
        if alias_email:
            print(f"🎉 Final success! Created: {alias_email}")
        
    else:
        print(f"\n❌ AUTHENTICATION FAILED")
        print("=" * 60)
        print(f"❌ Failed after {duration:.2f} seconds")
        print("💡 The API token method still works as backup")

if __name__ == "__main__":
    main() 