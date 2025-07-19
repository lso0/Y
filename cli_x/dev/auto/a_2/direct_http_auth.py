#!/usr/bin/env python3
"""
Direct HTTP Authentication to Fastmail - No Browser Required!
This script authenticates directly via HTTP requests and extracts session tokens.
Much faster than browser automation.
"""

import requests
import json
import re
import base64
from urllib.parse import parse_qs, urlparse
import time

class FastmailDirectAuth:
    """Direct HTTP authentication to Fastmail without browser."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        self.bearer_token = None
        self.account_id = None
        self.user_id = None
        
    def authenticate(self):
        """Perform direct HTTP authentication."""
        print("🔐 Starting Direct HTTP Authentication...")
        print("=" * 50)
        
        try:
            # Step 1: Get the login page to extract any CSRF tokens or session info
            print("📄 Step 1: Getting login page...")
            login_page = self.session.get('https://app.fastmail.com/login/')
            
            if login_page.status_code == 200:
                print("   ✅ Login page loaded")
                
                # Look for any hidden form fields or tokens
                csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"   🔑 Found CSRF token: {csrf_token[:20]}...")
                else:
                    csrf_token = None
                    print("   ⚠️  No CSRF token found")
            else:
                print(f"   ❌ Failed to load login page: {login_page.status_code}")
                return False
            
            # Step 2: Attempt direct login
            print("\n🔑 Step 2: Attempting direct login...")
            
            login_data = {
                'username': self.username,
                'password': self.password,
            }
            
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            # Try different login endpoints
            login_endpoints = [
                'https://app.fastmail.com/login/',
                'https://app.fastmail.com/ajax/login.php',
                'https://www.fastmail.com/login/',
                'https://api.fastmail.com/auth/login'
            ]
            
            for endpoint in login_endpoints:
                print(f"   🎯 Trying endpoint: {endpoint}")
                
                response = self.session.post(endpoint, data=login_data)
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("      ✅ Login request successful")
                    
                    # Check if we got redirected to the main app
                    if 'app.fastmail.com' in response.url and 'login' not in response.url:
                        print("      🎉 Successfully authenticated!")
                        return self._extract_tokens_from_session()
                    elif response.json() if self._is_json(response) else False:
                        # Check for JSON response with tokens
                        data = response.json()
                        if 'token' in data or 'session' in data:
                            print("      🎉 Got token in JSON response!")
                            return self._extract_tokens_from_json(data)
                
                elif response.status_code == 302:
                    print(f"      ↪️  Redirect to: {response.headers.get('Location', 'Unknown')}")
                    
                    # Follow redirect
                    if 'Location' in response.headers:
                        redirect_url = response.headers['Location']
                        if 'app.fastmail.com' in redirect_url and 'login' not in redirect_url:
                            print("      🎉 Redirected to main app - authentication successful!")
                            return self._extract_tokens_from_session()
                
                else:
                    print(f"      ❌ Failed: {response.text[:100]}...")
            
            # Step 3: Try OAuth-style authentication
            print("\n🔄 Step 3: Trying OAuth-style authentication...")
            return self._try_oauth_flow()
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def _is_json(self, response):
        """Check if response is JSON."""
        try:
            response.json()
            return True
        except:
            return False
    
    def _extract_tokens_from_session(self):
        """Extract tokens from the current session."""
        print("🔍 Extracting tokens from session...")
        
        # Try to access the main app and extract tokens
        try:
            # Get the main app page
            app_response = self.session.get('https://app.fastmail.com/')
            
            if app_response.status_code == 200:
                print("   ✅ Accessed main app")
                
                # Look for bearer tokens in the page content
                token_patterns = [
                    r'bearer["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'authorization["\']?\s*:\s*["\']Bearer\s+([^"\']+)["\']',
                    r'token["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'fma1-[a-f0-9-]+',
                    r'fmu1-[a-f0-9-]+',
                ]
                
                for pattern in token_patterns:
                    matches = re.findall(pattern, app_response.text, re.IGNORECASE)
                    for match in matches:
                        if len(match) > 20 and ('fma1-' in match or 'fmu1-' in match):
                            print(f"   🎉 Found bearer token: {match[:30]}...")
                            self.bearer_token = match
                            return self._extract_additional_info()
                
                # Look for session cookies that might contain tokens
                for cookie in self.session.cookies:
                    if 'token' in cookie.name.lower() or 'bearer' in cookie.name.lower():
                        print(f"   🍪 Found token cookie: {cookie.name} = {cookie.value[:30]}...")
                        self.bearer_token = cookie.value
                        return self._extract_additional_info()
                
                print("   ⚠️  No bearer token found in page content")
                
                # Try to make JMAP requests to see if session cookies work
                return self._test_session_cookies()
            else:
                print(f"   ❌ Failed to access main app: {app_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error extracting tokens: {e}")
            return False
    
    def _extract_tokens_from_json(self, data):
        """Extract tokens from JSON response."""
        print("🔍 Extracting tokens from JSON...")
        
        # Look for various token fields
        token_fields = ['token', 'bearer', 'access_token', 'session_token', 'auth_token']
        
        for field in token_fields:
            if field in data:
                token = data[field]
                if isinstance(token, str) and len(token) > 20:
                    print(f"   🎉 Found {field}: {token[:30]}...")
                    self.bearer_token = token
                    return self._extract_additional_info()
        
        print("   ⚠️  No suitable token found in JSON")
        return False
    
    def _test_session_cookies(self):
        """Test if session cookies can be used for JMAP API."""
        print("🍪 Testing session cookies for JMAP access...")
        
        try:
            # Try JMAP session endpoint
            jmap_response = self.session.get('https://api.fastmail.com/jmap/session')
            
            if jmap_response.status_code == 200:
                try:
                    session_data = jmap_response.json()
                    print("   🎉 JMAP session accessible with cookies!")
                    
                    # Extract account info
                    if 'accounts' in session_data:
                        accounts = session_data['accounts']
                        self.account_id = list(accounts.keys())[0]
                        print(f"   📋 Account ID: {self.account_id}")
                    
                    # Try to create alias using session cookies
                    return self._create_alias_with_cookies(session_data)
                    
                except json.JSONDecodeError:
                    print("   ❌ Invalid JSON response from JMAP session")
                    return False
            else:
                print(f"   ❌ JMAP session failed: {jmap_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error testing session cookies: {e}")
            return False
    
    def _create_alias_with_cookies(self, session_data):
        """Try to create an alias using session cookies."""
        print("🎯 Testing alias creation with session cookies...")
        
        try:
            api_url = session_data.get('apiUrl', 'https://api.fastmail.com/jmap/api/')
            account_id = list(session_data.get('accounts', {}).keys())[0]
            
            # Try MaskedEmail creation
            payload = {
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
                                    "emailPrefix": "directauth",
                                    "description": "Created via direct HTTP auth"
                                }
                            }
                        },
                        "0"
                    ]
                ]
            }
            
            response = self.session.post(api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    
                    if method_response[0] == "MaskedEmail/set" and "created" in method_response[1]:
                        created = method_response[1]["created"]["test_direct"]
                        print(f"   🎉 SUCCESS! Created: {created['email']}")
                        return True
                    else:
                        print(f"   ❌ Creation failed: {method_response}")
                        return False
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error creating alias: {e}")
            return False
    
    def _try_oauth_flow(self):
        """Try OAuth-style authentication flow."""
        print("🔄 Attempting OAuth-style flow...")
        
        # This would involve more complex flow with authorization codes
        # For now, return False and suggest using the working API token
        print("   ⚠️  OAuth flow not implemented yet")
        return False
    
    def _extract_additional_info(self):
        """Extract additional account information."""
        if not self.bearer_token:
            return False
        
        print("📋 Extracting additional account information...")
        
        # Try to use the bearer token
        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        
        try:
            response = requests.get('https://api.fastmail.com/jmap/session', headers=headers)
            
            if response.status_code == 200:
                session_data = response.json()
                
                if 'accounts' in session_data:
                    accounts = session_data['accounts']
                    self.account_id = list(accounts.keys())[0]
                    print(f"   📋 Account ID: {self.account_id}")
                
                if 'username' in session_data:
                    self.user_id = session_data['username']
                    print(f"   👤 User ID: {self.user_id}")
                
                return True
            else:
                print(f"   ❌ Bearer token test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error testing bearer token: {e}")
            return False
    
    def create_alias(self, alias_email, target_email, description=""):
        """Create an alias using the extracted tokens."""
        if not self.bearer_token and not self.session.cookies:
            print("❌ No authentication tokens available")
            return False
        
        print(f"📝 Creating alias: {alias_email} -> {target_email}")
        
        # Implementation would go here using either bearer token or session cookies
        # This is similar to what we already have working
        pass

def main():
    """Main function to test direct HTTP authentication."""
    print("🚀 Fastmail Direct HTTP Authentication")
    print("=" * 50)
    print("✅ No browser required!")
    print("✅ Much faster than Puppeteer!")
    print("✅ Pure HTTP requests!")
    print()
    
    username = input("Enter your Fastmail username: ").strip()
    password = input("Enter your Fastmail password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required")
        return
    
    auth = FastmailDirectAuth(username, password)
    
    start_time = time.time()
    success = auth.authenticate()
    duration = time.time() - start_time
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print("=" * 50)
        print(f"✅ Authenticated in {duration:.2f} seconds")
        print("✅ Much faster than browser automation!")
        print("✅ Ready for alias creation!")
        
        if auth.bearer_token:
            print(f"🔑 Bearer token: {auth.bearer_token[:30]}...")
        
        if auth.account_id:
            print(f"📋 Account ID: {auth.account_id}")
    else:
        print(f"\n❌ FAILED")
        print("=" * 50)
        print(f"❌ Authentication failed after {duration:.2f} seconds")
        print("💡 Consider using the API token method instead")
        print("   (Your fmu1-... token already works perfectly)")

if __name__ == "__main__":
    main() 