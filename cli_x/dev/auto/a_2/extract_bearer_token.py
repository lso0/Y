#!/usr/bin/env python3
"""
Bearer Token Extraction - Extract bearer token from authenticated HTTP session
This script tries multiple methods to find and extract the bearer token.
"""

import requests
import json
import re
import time
import base64
from urllib.parse import parse_qs, urlparse

class BearerTokenExtractor:
    """Extract bearer token from authenticated HTTP session."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        self.bearer_token = None
        
    def authenticate_and_extract(self):
        """Authenticate and extract bearer token using various methods."""
        print("🔍 Bearer Token Extraction")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self._authenticate():
            return False
            
        # Step 2: Try multiple extraction methods
        print("\n🔎 Trying multiple token extraction methods...")
        
        methods = [
            ("HTML Content Analysis", self._extract_from_html),
            ("JavaScript Variables", self._extract_from_js_vars),
            ("API Endpoint Discovery", self._discover_api_endpoints),
            ("Session Token Conversion", self._convert_session_tokens),
            ("Network Requests Analysis", self._analyze_network_requests),
            ("Cookie Analysis", self._analyze_cookies),
            ("Local Storage Simulation", self._simulate_local_storage),
            ("Configuration Files", self._find_config_files)
        ]
        
        for method_name, method_func in methods:
            print(f"\n   🎯 Method: {method_name}")
            try:
                result = method_func()
                if result:
                    print(f"   ✅ SUCCESS! Found bearer token with {method_name}")
                    self.bearer_token = result
                    return self._test_bearer_token()
                else:
                    print(f"   ❌ No token found with {method_name}")
            except Exception as e:
                print(f"   ❌ Error with {method_name}: {e}")
        
        print("\n❌ No bearer token found with any method")
        return False
    
    def _authenticate(self):
        """Perform HTTP authentication."""
        print("🔐 Step 1: Authenticating...")
        
        # Get login page
        login_page = self.session.get('https://www.fastmail.com/login/')
        if login_page.status_code != 200:
            print("   ❌ Failed to load login page")
            return False
        
        # Perform login
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
        
        if response.status_code == 302:
            print("   ✅ Login successful!")
            
            # Follow redirect
            location = response.headers.get('Location')
            app_response = self.session.get(location)
            
            if app_response.status_code == 200:
                print("   ✅ Successfully accessed main app")
                return True
        
        print("   ❌ Authentication failed")
        return False
    
    def _extract_from_html(self):
        """Extract bearer token from HTML content."""
        print("      🔍 Analyzing HTML content...")
        
        # Get the main app page
        response = self.session.get('https://app.fastmail.com/')
        if response.status_code != 200:
            return None
        
        html_content = response.text
        
        # Pattern 1: Direct bearer token patterns
        token_patterns = [
            r'"bearer":\s*"([^"]+)"',
            r"'bearer':\s*'([^']+)'",
            r'"authorization":\s*"Bearer\s+([^"]+)"',
            r"'authorization':\s*'Bearer\s+([^']+)'",
            r'"token":\s*"(fma1-[^"]+)"',
            r"'token':\s*'(fma1-[^']+)'",
            r'"apiToken":\s*"([^"]+)"',
            r"'apiToken':\s*'([^']+)'",
            r'bearer["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'(fma1-[a-f0-9\-]+)',
            r'(fmu1-[a-f0-9\-]+)',
        ]
        
        for pattern in token_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if len(match) > 30:  # Bearer tokens are long
                    print(f"         🎉 Found potential token: {match[:40]}...")
                    return match
        
        print("      ❌ No bearer token found in HTML")
        return None
    
    def _extract_from_js_vars(self):
        """Extract bearer token from JavaScript variables."""
        print("      🔍 Analyzing JavaScript variables...")
        
        response = self.session.get('https://app.fastmail.com/')
        if response.status_code != 200:
            return None
        
        html_content = response.text
        
        # Look for common JavaScript variable patterns
        js_patterns = [
            r'var\s+bearer\s*=\s*["\']([^"\']+)["\']',
            r'let\s+bearer\s*=\s*["\']([^"\']+)["\']',
            r'const\s+bearer\s*=\s*["\']([^"\']+)["\']',
            r'var\s+token\s*=\s*["\']([^"\']+)["\']',
            r'let\s+token\s*=\s*["\']([^"\']+)["\']',
            r'const\s+token\s*=\s*["\']([^"\']+)["\']',
            r'window\.token\s*=\s*["\']([^"\']+)["\']',
            r'window\.bearer\s*=\s*["\']([^"\']+)["\']',
            r'localStorage\.setItem\(["\']token["\'],\s*["\']([^"\']+)["\']',
            r'localStorage\.setItem\(["\']bearer["\'],\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if len(match) > 30:
                    print(f"         🎉 Found JS token: {match[:40]}...")
                    return match
        
        print("      ❌ No bearer token found in JS variables")
        return None
    
    def _discover_api_endpoints(self):
        """Discover API endpoints that might return bearer tokens."""
        print("      🔍 Discovering API endpoints...")
        
        # Common API endpoints that might return tokens
        endpoints = [
            'https://app.fastmail.com/api/auth/token',
            'https://app.fastmail.com/api/session',
            'https://app.fastmail.com/api/user/token',
            'https://app.fastmail.com/auth/token',
            'https://app.fastmail.com/session/token',
            'https://api.fastmail.com/auth/session',
            'https://api.fastmail.com/session/create',
            'https://app.fastmail.com/login/token',
            'https://app.fastmail.com/token',
            'https://app.fastmail.com/api/token',
        ]
        
        for endpoint in endpoints:
            try:
                print(f"         Testing: {endpoint}")
                response = self.session.get(endpoint)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Look for token fields
                        token_fields = ['token', 'bearer', 'authorization', 'access_token', 'apiToken']
                        for field in token_fields:
                            if field in data:
                                token = data[field]
                                if isinstance(token, str) and len(token) > 30:
                                    print(f"         🎉 Found token in {field}: {token[:40]}...")
                                    return token
                                    
                    except json.JSONDecodeError:
                        # Check if it's a plain text token
                        if len(response.text) > 30 and response.text.startswith('fma1-'):
                            print(f"         🎉 Found plain text token: {response.text[:40]}...")
                            return response.text.strip()
                            
            except Exception as e:
                pass
        
        print("      ❌ No tokens found in API endpoints")
        return None
    
    def _convert_session_tokens(self):
        """Try to convert session cookies into bearer tokens."""
        print("      🔍 Converting session tokens...")
        
        # Look for session cookies that might contain encoded tokens
        for cookie in self.session.cookies:
            if len(cookie.value) > 50:  # Long enough to be a token
                print(f"         Analyzing cookie: {cookie.name}")
                
                # Try base64 decoding
                try:
                    decoded = base64.b64decode(cookie.value + '==').decode('utf-8')
                    if 'fma1-' in decoded or 'fmu1-' in decoded:
                        token_match = re.search(r'(fma1-[a-f0-9\-]+|fmu1-[a-f0-9\-]+)', decoded)
                        if token_match:
                            print(f"         🎉 Found token in cookie: {token_match.group(1)[:40]}...")
                            return token_match.group(1)
                except:
                    pass
                
                # Try URL decoding
                try:
                    from urllib.parse import unquote
                    decoded = unquote(cookie.value)
                    if 'fma1-' in decoded or 'fmu1-' in decoded:
                        token_match = re.search(r'(fma1-[a-f0-9\-]+|fmu1-[a-f0-9\-]+)', decoded)
                        if token_match:
                            print(f"         🎉 Found token in URL decoded cookie: {token_match.group(1)[:40]}...")
                            return token_match.group(1)
                except:
                    pass
        
        print("      ❌ No bearer token found in session cookies")
        return None
    
    def _analyze_network_requests(self):
        """Analyze network requests for bearer tokens."""
        print("      🔍 Analyzing network requests...")
        
        # Make requests to different parts of the app and look for tokens in responses
        app_urls = [
            'https://app.fastmail.com/',
            'https://app.fastmail.com/mail/',
            'https://app.fastmail.com/settings/',
            'https://app.fastmail.com/contacts/',
            'https://app.fastmail.com/calendar/',
        ]
        
        for url in app_urls:
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    # Look for tokens in response headers
                    for header_name, header_value in response.headers.items():
                        if 'token' in header_name.lower() or 'bearer' in header_name.lower():
                            if len(header_value) > 30:
                                print(f"         🎉 Found token in header {header_name}: {header_value[:40]}...")
                                return header_value
                    
                    # Look for XHR/fetch requests in the HTML
                    xhr_patterns = [
                        r'xhr\.setRequestHeader\(["\']Authorization["\'],\s*["\']Bearer\s+([^"\']+)["\']',
                        r'fetch\([^)]+headers[^}]+["\']Authorization["\']:\s*["\']Bearer\s+([^"\']+)["\']',
                    ]
                    
                    for pattern in xhr_patterns:
                        matches = re.findall(pattern, response.text, re.IGNORECASE)
                        for match in matches:
                            if len(match) > 30:
                                print(f"         🎉 Found token in XHR: {match[:40]}...")
                                return match
                                
            except Exception as e:
                pass
        
        print("      ❌ No bearer token found in network requests")
        return None
    
    def _analyze_cookies(self):
        """Deep analysis of cookies for bearer tokens."""
        print("      🔍 Deep cookie analysis...")
        
        print(f"         Current cookies: {len(self.session.cookies)}")
        
        for cookie in self.session.cookies:
            print(f"         🍪 {cookie.name}: {cookie.value[:50]}...")
            
            # Look for patterns in cookie values
            if 'fma1-' in cookie.value or 'fmu1-' in cookie.value:
                token_match = re.search(r'(fma1-[a-f0-9\-]+|fmu1-[a-f0-9\-]+)', cookie.value)
                if token_match:
                    print(f"         🎉 Found token in cookie value: {token_match.group(1)[:40]}...")
                    return token_match.group(1)
        
        print("      ❌ No bearer token found in cookies")
        return None
    
    def _simulate_local_storage(self):
        """Simulate local storage access by looking for localStorage patterns."""
        print("      🔍 Simulating localStorage access...")
        
        response = self.session.get('https://app.fastmail.com/')
        if response.status_code != 200:
            return None
        
        # Look for localStorage patterns
        localStorage_patterns = [
            r'localStorage\.getItem\(["\']([^"\']*token[^"\']*)["\']',
            r'localStorage\.setItem\(["\']([^"\']*token[^"\']*)["\'],\s*["\']([^"\']+)["\']',
            r'localStorage\[["\']([^"\']*token[^"\']*)["\']',
        ]
        
        for pattern in localStorage_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) > 1:
                    key, value = match[0], match[1]
                    if len(value) > 30:
                        print(f"         🎉 Found localStorage token {key}: {value[:40]}...")
                        return value
                else:
                    print(f"         📝 Found localStorage key: {match}")
        
        print("      ❌ No bearer token found in localStorage simulation")
        return None
    
    def _find_config_files(self):
        """Look for configuration files that might contain tokens."""
        print("      🔍 Looking for configuration files...")
        
        config_urls = [
            'https://app.fastmail.com/config.json',
            'https://app.fastmail.com/app.json',
            'https://app.fastmail.com/settings.json',
            'https://app.fastmail.com/user.json',
            'https://app.fastmail.com/auth.json',
            'https://app.fastmail.com/api/config',
            'https://app.fastmail.com/api/settings',
        ]
        
        for url in config_urls:
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Recursively search for tokens in the JSON
                        def find_tokens_in_dict(obj, path=""):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if isinstance(value, str) and len(value) > 30 and ('fma1-' in value or 'fmu1-' in value):
                                        print(f"         🎉 Found token at {path}.{key}: {value[:40]}...")
                                        return value
                                    elif isinstance(value, (dict, list)):
                                        result = find_tokens_in_dict(value, f"{path}.{key}")
                                        if result:
                                            return result
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj):
                                    result = find_tokens_in_dict(item, f"{path}[{i}]")
                                    if result:
                                        return result
                            return None
                        
                        result = find_tokens_in_dict(data)
                        if result:
                            return result
                            
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                pass
        
        print("      ❌ No bearer token found in config files")
        return None
    
    def _test_bearer_token(self):
        """Test the extracted bearer token."""
        print(f"\n🎯 Testing extracted bearer token...")
        
        if not self.bearer_token:
            print("   ❌ No bearer token to test")
            return False
        
        # Test with JMAP session
        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        response = requests.get('https://api.fastmail.com/jmap/session', headers=headers)
        
        if response.status_code == 200:
            try:
                session_data = response.json()
                if 'accounts' in session_data:
                    account_id = list(session_data['accounts'].keys())[0]
                    api_url = session_data.get('apiUrl', 'https://api.fastmail.com/jmap/api/')
                    
                    print(f"   ✅ Bearer token works!")
                    print(f"   📋 Account ID: {account_id}")
                    print(f"   🔗 API URL: {api_url}")
                    
                    # Test alias creation
                    return self._test_alias_creation(account_id, api_url)
                    
            except json.JSONDecodeError:
                print("   ❌ Invalid JSON response")
                return False
        else:
            print(f"   ❌ Bearer token test failed: {response.status_code}")
            return False
    
    def _test_alias_creation(self, account_id, api_url):
        """Test alias creation with extracted token."""
        print(f"\n🎯 Testing alias creation...")
        
        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        
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
                            "test_extracted": {
                                "emailPrefix": f"extracted{int(time.time())}",
                                "description": "Created via extracted bearer token",
                                "forwardingEmail": "wg0@fastmail.com"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    
                    if method_response[0] == "MaskedEmail/set" and "created" in method_response[1]:
                        created = method_response[1]["created"]["test_extracted"]
                        print(f"   🎉 SUCCESS! Created: {created['email']}")
                        return True
                    else:
                        print(f"   ❌ Creation failed: {method_response[1]}")
                        return False
                        
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                return False
        else:
            print(f"   ❌ Alias creation failed: {response.status_code}")
            return False

def main():
    """Main function to extract bearer token."""
    print("🔍 Fastmail Bearer Token Extractor")
    print("=" * 60)
    print("🎯 Extracting bearer token from HTTP session - NO BROWSER!")
    print()
    
    username = "wg0@fastmail.com"
    password = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"
    
    extractor = BearerTokenExtractor(username, password)
    
    start_time = time.time()
    success = extractor.authenticate_and_extract()
    duration = time.time() - start_time
    
    if success:
        print(f"\n🎉 COMPLETE SUCCESS!")
        print("=" * 60)
        print(f"✅ Bearer token extracted and tested in {duration:.2f} seconds")
        print(f"🔑 Token: {extractor.bearer_token[:50]}...")
        print("✅ This IS the pure HTTP automation you wanted!")
        
    else:
        print(f"\n❌ EXTRACTION FAILED")
        print("=" * 60)
        print(f"❌ Could not extract bearer token after {duration:.2f} seconds")
        print("💡 The API token method still works as backup")

if __name__ == "__main__":
    main() 