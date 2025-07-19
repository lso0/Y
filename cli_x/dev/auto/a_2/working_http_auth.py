#!/usr/bin/env python3
"""
Working HTTP Authentication - Sets correct headers for JSON responses
This fixes the issue where we were getting HTML instead of JSON from JMAP endpoints.
"""

import requests
import json
import time

class FastmailWorkingAuth:
    """Working HTTP authentication with correct headers for JSON responses."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        self.account_id = None
        self.api_url = None
        
    def authenticate(self):
        """Perform authentication with proper headers."""
        print("🔐 Working HTTP Authentication")
        print("=" * 60)
        
        try:
            # Step 1: Get login page
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
                
                # Follow redirect to establish session
                app_response = self.session.get(location)
                print(f"   📱 App response status: {app_response.status_code}")
                
                if app_response.status_code == 200:
                    print("   ✅ Successfully reached main app!")
                    return self._access_jmap_with_correct_headers()
                else:
                    print("   ❌ Failed to reach main app")
                    return False
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def _access_jmap_with_correct_headers(self):
        """Access JMAP API with correct headers for JSON responses."""
        print("\n🔍 Step 3: Accessing JMAP with correct headers...")
        
        # Print current cookies
        print(f"   📊 Current cookies: {len(self.session.cookies)}")
        for cookie in self.session.cookies:
            print(f"      🍪 {cookie.name}: {cookie.value[:50]}...")
        
        # Set correct headers for JSON response
        jmap_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Test different endpoints with proper headers
        endpoints = [
            'https://api.fastmail.com/jmap/session',
            'https://jmap.fastmail.com/jmap/session',
            'https://app.fastmail.com/jmap/session'
        ]
        
        for endpoint in endpoints:
            print(f"\n   🎯 Testing endpoint: {endpoint}")
            
            try:
                # Make request with proper JSON headers
                response = self.session.get(endpoint, headers=jmap_headers)
                print(f"      Status: {response.status_code}")
                print(f"      Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                
                if response.status_code == 200:
                    print(f"      ✅ SUCCESS! Got 200 response")
                    
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        print(f"      ✅ Got JSON content type!")
                        
                        try:
                            json_data = response.json()
                            print(f"      ✅ Valid JSON response!")
                            print(f"      📋 JSON keys: {list(json_data.keys())}")
                            
                            # Check if this is a valid JMAP session
                            if 'accounts' in json_data:
                                print(f"      🎉 Found accounts in response!")
                                accounts = json_data['accounts']
                                self.account_id = list(accounts.keys())[0]
                                print(f"      📋 Account ID: {self.account_id}")
                                
                                if 'apiUrl' in json_data:
                                    self.api_url = json_data['apiUrl']
                                    print(f"      🔗 API URL: {self.api_url}")
                                    
                                    # Test alias creation
                                    return self._test_alias_creation()
                                    
                        except json.JSONDecodeError:
                            print(f"      ❌ Invalid JSON despite correct content type")
                            print(f"      Response: {response.text[:200]}...")
                    else:
                        print(f"      ⚠️  Got HTML instead of JSON (Content-Type: {content_type})")
                        
                        # Let's try a different approach - maybe we need to access the API differently
                        if endpoint == 'https://api.fastmail.com/jmap/session':
                            print("      🔄 Trying alternative API access...")
                            alt_response = self._try_alternative_api_access()
                            if alt_response:
                                return alt_response
                                
                else:
                    print(f"      ❌ Failed with status {response.status_code}")
                    if response.text:
                        print(f"      Error: {response.text[:200]}...")
                        
            except Exception as e:
                print(f"      ❌ Exception: {e}")
        
        return False
    
    def _try_alternative_api_access(self):
        """Try alternative ways to access the API."""
        print("   🔄 Trying alternative API access methods...")
        
        # Method 1: Try with different User-Agent
        print("      🎯 Method 1: Different User-Agent...")
        alt_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Fastmail-CLI/1.0'
        }
        
        response = self.session.get('https://api.fastmail.com/jmap/session', headers=alt_headers)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            try:
                json_data = response.json()
                print("      ✅ Success with different User-Agent!")
                if 'accounts' in json_data:
                    self.account_id = list(json_data['accounts'].keys())[0]
                    self.api_url = json_data.get('apiUrl', 'https://api.fastmail.com/jmap/api/')
                    return self._test_alias_creation()
            except json.JSONDecodeError:
                pass
        
        # Method 2: Try accessing the API endpoint directly
        print("      🎯 Method 2: Direct API endpoint...")
        try:
            # Try to find the API endpoint by looking at existing working solution
            api_endpoints = [
                'https://api.fastmail.com/jmap/api/',
                'https://jmap.fastmail.com/jmap/api/',
                'https://app.fastmail.com/jmap/api/'
            ]
            
            for api_url in api_endpoints:
                print(f"         Testing: {api_url}")
                
                # Try a simple JMAP query to see if we can access the API
                test_payload = {
                    "using": ["urn:ietf:params:jmap:core"],
                    "methodCalls": [
                        ["Session/get", {}, "0"]
                    ]
                }
                
                response = self.session.post(api_url, json=test_payload)
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"         ✅ Success with {api_url}!")
                        
                        # Extract account info from the response
                        if "methodResponses" in result:
                            session_response = result["methodResponses"][0]
                            if session_response[0] == "Session/get":
                                session_data = session_response[1]
                                if 'accounts' in session_data:
                                    self.account_id = list(session_data['accounts'].keys())[0]
                                    self.api_url = api_url
                                    print(f"         📋 Account ID: {self.account_id}")
                                    return self._test_alias_creation()
                        
                    except json.JSONDecodeError:
                        print(f"         ❌ Invalid JSON from {api_url}")
                        
        except Exception as e:
            print(f"      ❌ Exception in alternative methods: {e}")
        
        return False
    
    def _test_alias_creation(self):
        """Test alias creation with the authenticated session."""
        print(f"\n🎯 Step 4: Testing alias creation...")
        print(f"   📋 Using Account ID: {self.account_id}")
        print(f"   🔗 Using API URL: {self.api_url}")
        
        if not self.account_id or not self.api_url:
            print("   ❌ Missing account ID or API URL")
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
                        "accountId": self.account_id,
                        "create": {
                            "test_working": {
                                "emailPrefix": f"workingauth{int(time.time())}",
                                "description": "Created via working HTTP auth",
                                "forwardingEmail": "wg0@fastmail.com"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        try:
            response = self.session.post(self.api_url, json=test_payload)
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
                                created = method_response[1]["created"]["test_working"]
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
    """Main function to test working HTTP authentication."""
    print("🚀 Working Fastmail HTTP Authentication")
    print("=" * 60)
    print("✅ Sets correct headers for JSON responses!")
    print("✅ No browser required!")
    print("✅ Pure HTTP automation!")
    print()
    
    username = "wg0@fastmail.com"
    password = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"
    
    auth = FastmailWorkingAuth(username, password)
    
    start_time = time.time()
    success = auth.authenticate()
    duration = time.time() - start_time
    
    if success:
        print(f"\n🎉 COMPLETE SUCCESS!")
        print("=" * 60)
        print(f"✅ Authentication and alias creation working in {duration:.2f} seconds")
        print("✅ This is the headless HTTP automation you wanted!")
        print("✅ Ready for production use!")
        
        # Test creating a real alias
        print("\n🎯 Testing real alias creation...")
        alias_email = auth.create_alias("workingauth01", "Created via working HTTP auth")
        
        if alias_email:
            print(f"🎉 Final success! Created: {alias_email}")
        
    else:
        print(f"\n❌ AUTHENTICATION FAILED")
        print("=" * 60)
        print(f"❌ Failed after {duration:.2f} seconds")
        print("💡 But we're very close - the login is working!")
        print("💡 The issue is getting JSON instead of HTML responses")

if __name__ == "__main__":
    main() 