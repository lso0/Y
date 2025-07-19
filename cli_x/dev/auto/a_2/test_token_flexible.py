#!/usr/bin/env python3
"""
Flexible test script for different Fastmail token formats.
Tests the actual token provided regardless of prefix.
"""

import requests
import json
import os
import time

def test_token_formats(token):
    """Test the token with different approaches."""
    print(f"🧪 Testing Token: {token[:20]}...")
    print("=" * 50)
    
    # Test different endpoints and methods
    test_configs = [
        {
            "name": "JMAP Session Endpoint",
            "method": "GET",
            "url": "https://api.fastmail.com/jmap/session",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": None
        },
        {
            "name": "JMAP API Endpoint (POST)",
            "method": "POST", 
            "url": "https://api.fastmail.com/jmap/api/",
            "headers": {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            "data": {
                "using": ["urn:ietf:params:jmap:core"],
                "methodCalls": [["getSession", {}, "0"]]
            }
        },
        {
            "name": "JMAP API with User ID",
            "method": "POST",
            "url": "https://api.fastmail.com/jmap/api/?u=2ef64041",  # Extract user ID from token
            "headers": {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            "data": {
                "using": ["urn:ietf:params:jmap:core"],
                "methodCalls": [["getSession", {}, "0"]]
            }
        }
    ]
    
    for config in test_configs:
        print(f"\n📋 Testing: {config['name']}")
        print(f"   URL: {config['url']}")
        
        try:
            if config['method'] == 'GET':
                response = requests.get(config['url'], headers=config['headers'])
            else:
                response = requests.post(config['url'], 
                                       headers=config['headers'], 
                                       json=config['data'])
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success!")
                
                try:
                    data = response.json()
                    print(f"   📊 Response type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"   📋 Response keys: {list(data.keys())}")
                        
                        if "accounts" in data:
                            accounts = data["accounts"]
                            print(f"   👥 Found {len(accounts)} account(s)")
                            for account_id, account_info in accounts.items():
                                print(f"      - Account ID: {account_id}")
                                print(f"        Name: {account_info.get('name', 'N/A')}")
                        
                        if "apiUrl" in data:
                            print(f"   🔗 API URL: {data['apiUrl']}")
                        
                        if "methodResponses" in data:
                            print(f"   📤 Method responses: {len(data['methodResponses'])}")
                            for i, response in enumerate(data['methodResponses']):
                                print(f"      Response {i}: {response[0]}")
                        
                        return config['url'], data
                    else:
                        print(f"   📊 Raw response: {str(data)[:200]}...")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON response: {response.text[:200]}...")
                    
            else:
                print(f"   ❌ Failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    return None, None

def test_alias_creation_with_token(token):
    """Test alias creation with the working token."""
    print("\n🎯 Testing Alias Creation")
    print("=" * 50)
    
    # First, get session information
    session_url = "https://api.fastmail.com/jmap/session"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(session_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get session: {response.status_code}")
            return False
        
        session_data = response.json()
        api_url = session_data.get("apiUrl")
        accounts = session_data.get("accounts", {})
        
        if not api_url:
            print("❌ No API URL found in session")
            return False
        
        print(f"✅ Session obtained successfully")
        print(f"   🔗 API URL: {api_url}")
        print(f"   👥 Accounts: {list(accounts.keys())}")
        
        # Use the first account
        account_id = list(accounts.keys())[0]
        print(f"   📋 Using account: {account_id}")
        
        # Create test alias
        test_alias = f"test-working-{int(time.time())}@fastmail.com"
        target_email = "wg0@fastmail.com"
        
        alias_payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/aliases"
            ],
            "methodCalls": [
                [
                    "Alias/set",
                    {
                        "accountId": account_id,
                        "create": {
                            "test1": {
                                "email": test_alias,
                                "targetEmails": [target_email],
                                "description": "Test alias via working token"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        print(f"\n📝 Creating test alias: {test_alias}")
        
        alias_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=alias_payload, headers=alias_headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   📊 Response: {json.dumps(result, indent=2)}")
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    print(f"   📤 Method: {method_response[0]}")
                    
                    if method_response[0] == "Alias/set":
                        if "created" in method_response[1]:
                            print(f"   🎉 ALIAS CREATED SUCCESSFULLY!")
                            print(f"   ✅ Token works for alias creation!")
                            return True
                        elif "notCreated" in method_response[1]:
                            print(f"   ❌ Alias not created: {method_response[1]['notCreated']}")
                            return False
                        else:
                            print(f"   ❓ Unexpected response: {method_response[1]}")
                            return False
                    else:
                        print(f"   ❌ Unexpected method response: {method_response[0]}")
                        return False
                else:
                    print(f"   ❌ No method responses in result")
                    return False
                    
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                return False
        else:
            print(f"   ❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False

def create_nya01_alias(token):
    """Create the specific nya01 alias."""
    print("\n🎯 Creating nya01 Alias")
    print("=" * 50)
    
    # Get session
    session_url = "https://api.fastmail.com/jmap/session"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(session_url, headers=headers)
        if response.status_code != 200:
            return False
        
        session_data = response.json()
        api_url = session_data.get("apiUrl")
        accounts = session_data.get("accounts", {})
        account_id = list(accounts.keys())[0]
        
        # Create nya01 alias
        alias_payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/aliases"
            ],
            "methodCalls": [
                [
                    "Alias/set",
                    {
                        "accountId": account_id,
                        "create": {
                            "nya01": {
                                "email": "nya01@fastmail.com",
                                "targetEmails": ["wg0@fastmail.com"],
                                "description": "Created via working API token"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        print(f"📝 Creating nya01@fastmail.com -> wg0@fastmail.com")
        
        alias_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=alias_payload, headers=alias_headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    
                    if method_response[0] == "Alias/set" and "created" in method_response[1]:
                        print(f"   🎉 NYA01 ALIAS CREATED SUCCESSFULLY!")
                        print(f"   ✅ nya01@fastmail.com is now active!")
                        return True
                    else:
                        print(f"   ❌ Failed: {method_response}")
                        return False
                        
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                return False
        else:
            print(f"   ❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False

def main():
    """Main function to test the token."""
    print("🔧 Fastmail Token Tester")
    print("=" * 50)
    
    # Use the token from the previous run
    token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    
    print(f"🔍 Testing token: {token[:30]}...")
    
    # Test different approaches
    working_url, session_data = test_token_formats(token)
    
    if working_url and session_data:
        print(f"\n✅ TOKEN WORKS!")
        print(f"   Working URL: {working_url}")
        
        # Test alias creation
        if test_alias_creation_with_token(token):
            print(f"\n🎉 ALIAS CREATION WORKS!")
            
            # Ask if they want to create nya01
            print(f"\n❓ Create nya01 alias now? (y/n)")
            choice = input("Choice: ").strip().lower()
            
            if choice == 'y':
                if create_nya01_alias(token):
                    print(f"\n🎉 SUCCESS! nya01@fastmail.com alias created!")
                    print(f"✅ The app password method is NOT needed!")
                    print(f"✅ Your API token works perfectly!")
                else:
                    print(f"\n❌ Failed to create nya01 alias")
            else:
                print(f"\n💡 You can create nya01 alias anytime using this token")
        else:
            print(f"\n❌ Alias creation failed")
    else:
        print(f"\n❌ Token doesn't work with any method")
        print(f"   Please create a new API token at:")
        print(f"   https://app.fastmail.com/settings/security/tokens/new")

if __name__ == "__main__":
    main() 