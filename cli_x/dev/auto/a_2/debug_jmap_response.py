#!/usr/bin/env python3
"""
Debug JMAP Response - Inspect what we're getting from the successful endpoint
"""

import requests
import json
import re
import time

class FastmailDebugAuth:
    """Debug version to inspect JMAP responses."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        
    def authenticate_and_debug(self):
        """Perform authentication and debug the JMAP response."""
        print("🔍 Debug Authentication Flow")
        print("=" * 60)
        
        # Step 1: Login
        print("📄 Step 1: Getting login page...")
        login_page = self.session.get('https://www.fastmail.com/login/')
        
        if login_page.status_code != 200:
            print(f"   ❌ Failed to load login page: {login_page.status_code}")
            return False
        
        print("   ✅ Login page loaded successfully")
        
        # Step 2: Perform login
        print("\n🔑 Step 2: Performing login...")
        login_data = {
            'username': self.username,
            'password': self.password,
            'rememberme': '1'
        }
        
        response = self.session.post(
            'https://www.fastmail.com/login/',
            data=login_data,
            allow_redirects=False
        )
        
        print(f"   🎯 Login response status: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Login successful - got redirect!")
            location = response.headers.get('Location')
            print(f"   ↪️  Redirect to: {location}")
            
            # Follow redirect
            app_response = self.session.get(location)
            print(f"   📱 App response status: {app_response.status_code}")
            
            if app_response.status_code == 200:
                print("   ✅ Successfully reached main app!")
                return self._debug_jmap_endpoints()
            else:
                print("   ❌ Failed to reach main app")
                return False
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            return False
    
    def _debug_jmap_endpoints(self):
        """Debug different JMAP endpoints."""
        print("\n🔍 Step 3: Debugging JMAP endpoints...")
        
        # Print current cookies
        print(f"   📊 Current cookies: {len(self.session.cookies)}")
        for cookie in self.session.cookies:
            print(f"      🍪 {cookie.name}: {cookie.value[:50]}...")
        
        # Test different endpoints
        endpoints = [
            'https://api.fastmail.com/jmap/session',
            'https://jmap.fastmail.com/jmap/session',
            'https://app.fastmail.com/jmap/session'
        ]
        
        for endpoint in endpoints:
            print(f"\n   🎯 Testing endpoint: {endpoint}")
            
            try:
                response = self.session.get(endpoint)
                print(f"      Status: {response.status_code}")
                print(f"      Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                print(f"      Content-Length: {len(response.content)}")
                
                if response.status_code == 200:
                    print(f"      ✅ SUCCESS! Got 200 response")
                    
                    # Print first 500 characters of response
                    print(f"      📄 Response preview (first 500 chars):")
                    print(f"      {'-' * 50}")
                    print(f"      {response.text[:500]}")
                    print(f"      {'-' * 50}")
                    
                    # Try to parse as JSON
                    try:
                        json_data = response.json()
                        print(f"      ✅ Valid JSON response!")
                        print(f"      📋 JSON keys: {list(json_data.keys())}")
                        
                        # If this is a valid JMAP session, extract info
                        if 'accounts' in json_data:
                            print(f"      🎉 Found accounts in response!")
                            accounts = json_data['accounts']
                            account_id = list(accounts.keys())[0]
                            print(f"      📋 Account ID: {account_id}")
                            
                            if 'apiUrl' in json_data:
                                api_url = json_data['apiUrl']
                                print(f"      🔗 API URL: {api_url}")
                                
                                # Test alias creation
                                return self._test_alias_creation(json_data, account_id, api_url)
                        
                    except json.JSONDecodeError as e:
                        print(f"      ❌ Invalid JSON: {e}")
                        
                        # Check if it's HTML
                        if response.text.strip().startswith('<'):
                            print(f"      📄 Response appears to be HTML")
                            
                            # Look for any tokens or useful info in the HTML
                            token_patterns = [
                                r'(fma1-[a-f0-9-]+)',
                                r'(fmu1-[a-f0-9-]+)',
                                r'bearer["\']?\s*:\s*["\']([^"\']+)["\']',
                                r'apiUrl["\']?\s*:\s*["\']([^"\']+)["\']',
                                r'accountId["\']?\s*:\s*["\']([^"\']+)["\']'
                            ]
                            
                            for pattern in token_patterns:
                                matches = re.findall(pattern, response.text, re.IGNORECASE)
                                if matches:
                                    print(f"      🔑 Found {len(matches)} potential tokens with pattern: {pattern}")
                                    for match in matches:
                                        if len(match) > 10:
                                            print(f"         {match[:50]}...")
                        
                        # Check if it's a different format
                        elif response.text.strip().startswith('{'):
                            print(f"      ⚠️  Looks like JSON but parsing failed")
                            # Maybe it's malformed JSON, try to fix it
                            try:
                                # Try to find the actual JSON part
                                json_start = response.text.find('{')
                                json_end = response.text.rfind('}') + 1
                                if json_start >= 0 and json_end > json_start:
                                    json_part = response.text[json_start:json_end]
                                    fixed_json = json.loads(json_part)
                                    print(f"      ✅ Fixed JSON parsing!")
                                    print(f"      📋 JSON keys: {list(fixed_json.keys())}")
                            except:
                                print(f"      ❌ Could not fix JSON parsing")
                        
                        else:
                            print(f"      ❓ Unknown response format")
                
                else:
                    print(f"      ❌ Failed with status {response.status_code}")
                    if response.text:
                        print(f"      Error: {response.text[:200]}...")
                        
            except Exception as e:
                print(f"      ❌ Exception: {e}")
        
        return False
    
    def _test_alias_creation(self, session_data, account_id, api_url):
        """Test alias creation with the session data."""
        print(f"\n🎯 Step 4: Testing alias creation...")
        print(f"   📋 Using Account ID: {account_id}")
        print(f"   🔗 Using API URL: {api_url}")
        
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
                            "test_debug": {
                                "emailPrefix": f"debugauth{int(time.time())}",
                                "description": "Created via debug HTTP auth",
                                "forwardingEmail": "wg0@fastmail.com"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        try:
            response = self.session.post(api_url, json=test_payload)
            print(f"   🎯 Alias creation response: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Got JSON response!")
                    
                    if "methodResponses" in result:
                        method_response = result["methodResponses"][0]
                        print(f"   📋 Method response: {method_response[0]}")
                        
                        if method_response[0] == "MaskedEmail/set":
                            if "created" in method_response[1]:
                                created = method_response[1]["created"]["test_debug"]
                                print(f"   🎉 SUCCESS! Created: {created['email']}")
                                return True
                            else:
                                print(f"   ❌ Creation failed: {method_response[1]}")
                                return False
                        else:
                            print(f"   ❌ Unexpected method: {method_response}")
                            return False
                    else:
                        print(f"   ❌ No methodResponses: {result}")
                        return False
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON in alias creation response")
                    print(f"   Response: {response.text[:200]}...")
                    return False
                    
            else:
                print(f"   ❌ Alias creation failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during alias creation: {e}")
            return False

def main():
    """Main function to debug authentication."""
    print("🔍 Fastmail Authentication Debug")
    print("=" * 60)
    print("🔎 This will show us exactly what responses we get!")
    print()
    
    username = "wg0@fastmail.com"
    password = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"
    
    auth = FastmailDebugAuth(username, password)
    
    start_time = time.time()
    success = auth.authenticate_and_debug()
    duration = time.time() - start_time
    
    if success:
        print(f"\n🎉 DEBUG SUCCESS!")
        print("=" * 60)
        print(f"✅ Authentication and alias creation working in {duration:.2f} seconds")
        print("✅ We found the working method!")
        
    else:
        print(f"\n🔍 DEBUG COMPLETE")
        print("=" * 60)
        print(f"⚠️  Completed debug in {duration:.2f} seconds")
        print("📋 Check the output above for working endpoints and responses")

if __name__ == "__main__":
    main() 