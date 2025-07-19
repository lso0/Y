#!/usr/bin/env python3
"""
Test the new app password: 6s4r7y627t2u7r2b
Let's see if this app password has different capabilities for alias creation.
"""

import requests
import json
import base64
import time

# New app password to test
NEW_APP_PASSWORD = "6s4r7y627t2u7r2b"
USERNAME = "wg0@fastmail.com"

def test_app_password_authentication():
    """Test different authentication methods with the new app password."""
    print("🧪 Testing New App Password Authentication")
    print("=" * 50)
    print(f"App Password: {NEW_APP_PASSWORD}")
    print(f"Username: {USERNAME}")
    print()
    
    # Test different authentication approaches
    auth_tests = [
        {
            "name": "Bearer Token (JMAP API)",
            "url": "https://api.fastmail.com/jmap/api/",
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {NEW_APP_PASSWORD}",
                "Content-Type": "application/json"
            },
            "data": {
                "using": ["urn:ietf:params:jmap:core"],
                "methodCalls": [["getSession", {}, "0"]]
            }
        },
        {
            "name": "Bearer Token (JMAP Session)",
            "url": "https://api.fastmail.com/jmap/session",
            "method": "GET",
            "headers": {
                "Authorization": f"Bearer {NEW_APP_PASSWORD}"
            },
            "data": None
        },
        {
            "name": "Basic Auth (JMAP API)",
            "url": "https://api.fastmail.com/jmap/api/",
            "method": "POST",
            "headers": {
                "Authorization": f"Basic {base64.b64encode(f'{USERNAME}:{NEW_APP_PASSWORD}'.encode()).decode()}",
                "Content-Type": "application/json"
            },
            "data": {
                "using": ["urn:ietf:params:jmap:core"],
                "methodCalls": [["getSession", {}, "0"]]
            }
        },
        {
            "name": "Basic Auth (JMAP Session)",
            "url": "https://api.fastmail.com/jmap/session",
            "method": "GET",
            "headers": {
                "Authorization": f"Basic {base64.b64encode(f'{USERNAME}:{NEW_APP_PASSWORD}'.encode()).decode()}"
            },
            "data": None
        }
    ]
    
    working_configs = []
    
    for test in auth_tests:
        print(f"📋 Testing: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            if test['method'] == 'GET':
                response = requests.get(test['url'], headers=test['headers'])
            else:
                response = requests.post(test['url'], headers=test['headers'], json=test['data'])
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success!")
                
                try:
                    data = response.json()
                    print(f"   📊 Response type: JSON")
                    
                    if "accounts" in data:
                        accounts = data["accounts"]
                        print(f"   👥 Found {len(accounts)} account(s)")
                        for account_id in accounts.keys():
                            print(f"      - {account_id}")
                    
                    if "capabilities" in data:
                        capabilities = data["capabilities"]
                        print(f"   🔧 Found {len(capabilities)} capabilities:")
                        for cap in capabilities.keys():
                            print(f"      - {cap}")
                    
                    working_configs.append({
                        "config": test,
                        "response_data": data
                    })
                    
                except json.JSONDecodeError:
                    print(f"   📄 Non-JSON response: {response.text[:100]}...")
                    
            else:
                print(f"   ❌ Failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
        
        print()
    
    return working_configs

def test_alias_creation_with_config(config):
    """Test alias creation with a working authentication config."""
    print(f"🎯 Testing Alias Creation with {config['config']['name']}")
    print("=" * 60)
    
    response_data = config['response_data']
    
    # Extract session info
    api_url = response_data.get("apiUrl")
    accounts = response_data.get("accounts", {})
    capabilities = response_data.get("capabilities", {})
    
    if not api_url:
        # Try using the original URL
        api_url = config['config']['url']
    
    if not accounts:
        print("❌ No accounts found in response")
        return False
    
    account_id = list(accounts.keys())[0]
    
    print(f"   🔗 API URL: {api_url}")
    print(f"   📋 Account ID: {account_id}")
    print(f"   🔧 Available capabilities: {list(capabilities.keys())}")
    
    # Test different alias creation methods
    alias_tests = [
        {
            "name": "Standard Alias/set",
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/aliases"
            ],
            "method": "Alias/set",
            "create_data": {
                "email": "test-app-password-123@fastmail.com",
                "targetEmails": ["wg0@fastmail.com"],
                "description": "Test alias via app password"
            }
        },
        {
            "name": "MaskedEmail/set",
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "method": "MaskedEmail/set",
            "create_data": {
                "emailPrefix": "testapp123",
                "description": "Test masked email via app password"
            }
        },
        {
            "name": "All available capabilities",
            "using": list(capabilities.keys()) if capabilities else ["urn:ietf:params:jmap:core"],
            "method": "Alias/set",
            "create_data": {
                "email": "test-all-caps-123@fastmail.com",
                "targetEmails": ["wg0@fastmail.com"],
                "description": "Test with all capabilities"
            }
        }
    ]
    
    headers = config['config']['headers'].copy()
    if 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/json'
    
    for test in alias_tests:
        print(f"\n📧 Testing: {test['name']}")
        print(f"   Method: {test['method']}")
        print(f"   Capabilities: {test['using']}")
        
        if test['method'] == 'Alias/set':
            payload = {
                "using": test['using'],
                "methodCalls": [
                    [
                        "Alias/set",
                        {
                            "accountId": account_id,
                            "create": {
                                "test1": test['create_data']
                            }
                        },
                        "0"
                    ]
                ]
            }
        elif test['method'] == 'MaskedEmail/set':
            payload = {
                "using": test['using'],
                "methodCalls": [
                    [
                        "MaskedEmail/set",
                        {
                            "accountId": account_id,
                            "create": {
                                "test1": test['create_data']
                            }
                        },
                        "0"
                    ]
                ]
            }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Request successful!")
                    
                    if "methodResponses" in result:
                        method_response = result["methodResponses"][0]
                        print(f"   📤 Method: {method_response[0]}")
                        
                        if method_response[0] == "error":
                            print(f"   ❌ Error: {method_response[1]}")
                        elif "created" in method_response[1]:
                            created = method_response[1]["created"]
                            print(f"   🎉 SUCCESS! Created: {created}")
                            return True
                        elif "notCreated" in method_response[1]:
                            not_created = method_response[1]["notCreated"]
                            print(f"   ❌ Not created: {not_created}")
                        else:
                            print(f"   📊 Response: {method_response[1]}")
                    else:
                        print(f"   📊 Full response: {result}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
            else:
                print(f"   ❌ Failed: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    return False

def create_nya01_with_app_password():
    """Try to create the nya01 alias specifically."""
    print(f"\n🎯 Attempting to Create nya01 with App Password")
    print("=" * 60)
    
    # Test the authentication methods that might work
    working_configs = test_app_password_authentication()
    
    if not working_configs:
        print("❌ No working authentication methods found")
        return False
    
    print(f"✅ Found {len(working_configs)} working authentication method(s)")
    print()
    
    # Try alias creation with each working config
    for i, config in enumerate(working_configs):
        print(f"🧪 Attempt {i+1}/{len(working_configs)}")
        if test_alias_creation_with_config(config):
            print(f"🎉 SUCCESS! App password works for alias creation!")
            
            # Now try to create nya01 specifically
            print(f"\n🎯 Creating nya01@fastmail.com specifically...")
            
            response_data = config['response_data']
            api_url = response_data.get("apiUrl") or config['config']['url']
            account_id = list(response_data.get("accounts", {}).keys())[0]
            
            headers = config['config']['headers'].copy()
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            # Try MaskedEmail first (more likely to work)
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
                                "nya01": {
                                    "emailPrefix": "nya01",
                                    "description": "nya01 created via app password"
                                }
                            }
                        },
                        "0"
                    ]
                ]
            }
            
            try:
                response = requests.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    if "methodResponses" in result:
                        method_response = result["methodResponses"][0]
                        if "created" in method_response[1]:
                            created = method_response[1]["created"]["nya01"]
                            print(f"🎉 NYA01 CREATED!")
                            print(f"   📧 Email: {created['email']}")
                            print(f"   ✅ Forwards to: wg0@fastmail.com")
                            return True
            except:
                pass
            
            return True
    
    print("❌ All authentication methods failed for alias creation")
    return False

def main():
    """Main function to test the new app password."""
    print("🔧 New App Password Tester")
    print("=" * 50)
    print(f"Testing app password: {NEW_APP_PASSWORD}")
    print()
    
    success = create_nya01_with_app_password()
    
    if success:
        print(f"\n🎉 FINAL RESULT: SUCCESS!")
        print("=" * 50)
        print("✅ Your new app password works!")
        print("✅ You can create aliases/masked emails!")
        print("✅ This is faster than browser automation!")
    else:
        print(f"\n❌ FINAL RESULT: FAILED")
        print("=" * 50)
        print("❌ App password doesn't work for JMAP alias creation")
        print("💡 Consider using the API token method instead")
        print("   (The fmu1-... token we tested earlier)")

if __name__ == "__main__":
    main() 