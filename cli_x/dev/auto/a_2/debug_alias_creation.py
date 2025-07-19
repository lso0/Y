#!/usr/bin/env python3
"""
Debug script to understand why alias creation isn't working properly.
We need to understand the correct API calls and responses.
"""

import requests
import json
import os
import base64
import time

def test_session_info(username, app_password):
    """Test getting session information to understand the account structure."""
    print("🔍 Testing Session Information...")
    
    auth_string = f"{username}:{app_password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # Test different URLs
    urls = [
        "https://jmap.fastmail.com/jmap/api/",
        "https://api.fastmail.com/jmap/api/",
        f"https://jmap.fastmail.com/jmap/api/?u={username.split('@')[0]}",
        f"https://api.fastmail.com/jmap/api/?u={username.split('@')[0]}"
    ]
    
    for url in urls:
        print(f"\n📡 Testing URL: {url}")
        
        payload = {
            "using": ["urn:ietf:params:jmap:core"],
            "methodCalls": [["getSession", {}, "0"]]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.text.strip():
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                    
                    if "methodResponses" in data:
                        session_info = data["methodResponses"][0][1]
                        print(f"   📋 Session Info Analysis:")
                        print(f"      Accounts: {list(session_info.get('accounts', {}).keys())}")
                        print(f"      Primary Accounts: {session_info.get('primaryAccounts', {})}")
                        print(f"      Capabilities: {list(session_info.get('capabilities', {}).keys())}")
                        
                        return url, data
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON Parse Error: {e}")
                    print(f"   Raw Response: {response.text[:200]}...")
            else:
                print("   ⚠️  Empty response")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    return None, None

def test_capabilities(username, app_password, working_url):
    """Test what capabilities are available."""
    print("\n🔍 Testing Available Capabilities...")
    
    auth_string = f"{username}:{app_password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # Test different capability combinations
    capability_sets = [
        ["urn:ietf:params:jmap:core"],
        ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail"],
        ["urn:ietf:params:jmap:core", "https://www.fastmail.com/dev/aliases"],
        ["urn:ietf:params:jmap:core", "urn:ietf:params:jmap:mail", "https://www.fastmail.com/dev/aliases"],
        # Test all Fastmail capabilities from the original script
        [
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
        ]
    ]
    
    for i, capabilities in enumerate(capability_sets):
        print(f"\n📋 Testing capability set {i+1}: {len(capabilities)} capabilities")
        
        payload = {
            "using": capabilities,
            "methodCalls": [["getSession", {}, "0"]]
        }
        
        try:
            response = requests.post(working_url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Capability set {i+1} works!")
                if response.text.strip():
                    try:
                        data = response.json()
                        # Check what methods are available
                        if "methodResponses" in data:
                            session_info = data["methodResponses"][0][1]
                            server_capabilities = session_info.get('capabilities', {})
                            print(f"   📡 Server capabilities: {list(server_capabilities.keys())}")
                    except:
                        pass
            else:
                print(f"   ❌ Capability set {i+1} failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   💥 Error testing capability set {i+1}: {e}")

def test_alias_methods(username, app_password, working_url, session_data):
    """Test different alias-related methods."""
    print("\n🔍 Testing Alias Methods...")
    
    auth_string = f"{username}:{app_password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # Extract account information from session
    account_id = None
    if session_data and "methodResponses" in session_data:
        session_info = session_data["methodResponses"][0][1]
        
        # Try to get the correct account ID
        if "primaryAccounts" in session_info:
            primary_accounts = session_info["primaryAccounts"]
            for key, value in primary_accounts.items():
                print(f"   Primary account {key}: {value}")
                if not account_id:
                    account_id = value
        
        if "accounts" in session_info:
            accounts = session_info["accounts"]
            print(f"   Available accounts: {list(accounts.keys())}")
            if not account_id and accounts:
                account_id = list(accounts.keys())[0]
    
    if not account_id:
        account_id = username.split('@')[0]
    
    print(f"   Using account ID: {account_id}")
    
    # Test different alias methods
    methods_to_test = [
        # Method 1: Alias/get to list existing aliases
        {
            "name": "Alias/get (list all)",
            "using": ["urn:ietf:params:jmap:core", "https://www.fastmail.com/dev/aliases"],
            "methodCalls": [["Alias/get", {"accountId": account_id, "ids": None}, "0"]]
        },
        # Method 2: Try different account IDs
        {
            "name": "Alias/get (with primary account)",
            "using": ["urn:ietf:params:jmap:core", "https://www.fastmail.com/dev/aliases"],
            "methodCalls": [["Alias/get", {"accountId": account_id, "ids": None}, "0"]]
        },
        # Method 3: Test alias creation with minimal payload
        {
            "name": "Alias/set (create test)",
            "using": ["urn:ietf:params:jmap:core", "https://www.fastmail.com/dev/aliases"],
            "methodCalls": [[
                "Alias/set",
                {
                    "accountId": account_id,
                    "create": {
                        "test123": {
                            "email": "test-debug-123@fastmail.com",
                            "targetEmails": ["wg0@fastmail.com"]
                        }
                    }
                },
                "0"
            ]]
        }
    ]
    
    for method in methods_to_test:
        print(f"\n📋 Testing: {method['name']}")
        
        payload = {
            "using": method["using"],
            "methodCalls": method["methodCalls"]
        }
        
        try:
            response = requests.post(working_url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.text.strip():
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)}")
                    
                    # Analyze the response
                    if "methodResponses" in data:
                        method_response = data["methodResponses"][0]
                        print(f"   📊 Method: {method_response[0]}")
                        print(f"   📊 Result keys: {list(method_response[1].keys()) if len(method_response) > 1 else 'No result'}")
                        
                        if method_response[0] == "error":
                            print(f"   ❌ Error: {method_response[1]}")
                        elif method_response[0] == "Alias/get" and "list" in method_response[1]:
                            aliases = method_response[1]["list"]
                            print(f"   ✅ Found {len(aliases)} aliases")
                            for alias in aliases[:3]:  # Show first 3
                                print(f"      - {alias.get('email', 'N/A')} -> {alias.get('targetEmails', ['N/A'])}")
                        elif method_response[0] == "Alias/set":
                            if "created" in method_response[1]:
                                print(f"   ✅ Created aliases: {method_response[1]['created']}")
                            else:
                                print(f"   ❌ No 'created' field in response")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON Parse Error: {e}")
                    print(f"   Raw response: {response.text[:200]}...")
            else:
                print("   ⚠️  Empty response")
                
        except Exception as e:
            print(f"   💥 Error: {e}")

def main():
    """Main debugging function."""
    print("🐞 Comprehensive Alias Creation Debug")
    print("=" * 50)
    
    # Get credentials
    username = "wg0@fastmail.com"
    app_password = os.getenv('FASTMAIL_APP_PASSWORD')
    
    if not app_password:
        print("🔑 Enter your Fastmail App Password:")
        app_password = input("App Password: ").strip()
    
    if not app_password:
        print("❌ No app password provided.")
        return
    
    print(f"Testing with username: {username}")
    print(f"App password: {app_password[:8]}...")
    
    # Step 1: Test session info
    working_url, session_data = test_session_info(username, app_password)
    
    if not working_url:
        print("❌ No working URL found for session info")
        return
    
    print(f"\n✅ Using working URL: {working_url}")
    
    # Step 2: Test capabilities
    test_capabilities(username, app_password, working_url)
    
    # Step 3: Test alias methods
    test_alias_methods(username, app_password, working_url, session_data)
    
    print("\n" + "=" * 50)
    print("🎯 Debug Complete")
    print("=" * 50)

if __name__ == "__main__":
    main() 