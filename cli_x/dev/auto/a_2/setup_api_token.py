#!/usr/bin/env python3
"""
Guide to set up the correct API token for Fastmail JMAP API.
The issue was using an app password instead of an API token.
"""

import requests
import json
import os
import time

def explain_the_difference():
    """Explain the difference between app passwords and API tokens."""
    print("🔍 Understanding the Difference")
    print("=" * 50)
    print()
    print("❌ App Passwords:")
    print("   - 16 characters (like: 596k5l263p9v796e)")
    print("   - Used for: IMAP, SMTP, CalDAV, CardDAV")
    print("   - NOT for JMAP API access")
    print()
    print("✅ API Tokens:")
    print("   - Longer format (like: fma1-xxx-xxx-xxx)")
    print("   - Used for: JMAP API access")
    print("   - Required for creating aliases")
    print()
    print("💡 The Problem:")
    print("   You created an app password, but alias creation requires an API token!")
    print()

def guide_api_token_creation():
    """Guide the user through creating an API token."""
    print("📋 How to Create an API Token")
    print("=" * 50)
    print()
    print("1. 🌐 Log in to Fastmail web interface")
    print("   https://app.fastmail.com")
    print()
    print("2. ⚙️  Go to Settings → Privacy & Security")
    print()
    print("3. 🔧 Find 'Connected apps & API tokens' section")
    print()
    print("4. 🎯 Click 'Manage API tokens' (NOT 'Manage app passwords')")
    print()
    print("5. ➕ Click 'New API token'")
    print()
    print("6. 📝 Fill in the form:")
    print("   - Name: 'Alias Creation Script'")
    print("   - Access level: Select what you need")
    print("   - ✅ Make sure to include permissions for aliases")
    print()
    print("7. 🔑 Copy the generated API token")
    print("   - It will look like: fma1-xxxxxxxxxx-xxxx-xxxx")
    print("   - This is what you need for JMAP API access")
    print()
    print("⚠️  Important:")
    print("   - You can only see the API token once")
    print("   - Copy it immediately and store it safely")
    print("   - Do NOT use the app password for JMAP API")
    print()

def test_api_token(api_token):
    """Test if the API token works correctly."""
    print("🧪 Testing API Token")
    print("=" * 30)
    
    if not api_token:
        print("❌ No API token provided")
        return False
    
    if not api_token.startswith("fma1-"):
        print("⚠️  Warning: API token should start with 'fma1-'")
        print(f"   Your token starts with: {api_token[:10]}...")
        print("   This might be an app password instead of an API token")
        return False
    
    print(f"🔍 Testing token: {api_token[:20]}...")
    
    # Test with session endpoint
    session_url = "https://api.fastmail.com/jmap/session"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(session_url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ API token works!")
            try:
                data = response.json()
                print(f"   📊 Session data received: {len(str(data))} characters")
                
                # Show some session info
                if "accounts" in data:
                    accounts = list(data["accounts"].keys())
                    print(f"   📋 Found {len(accounts)} account(s): {accounts}")
                
                if "apiUrl" in data:
                    print(f"   🔗 API URL: {data['apiUrl']}")
                    
                return True
            except json.JSONDecodeError:
                print("   ⚠️  Response is not JSON")
                return False
        else:
            print(f"   ❌ API token failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Error testing API token: {e}")
        return False

def test_alias_creation(api_token):
    """Test creating an alias with the API token."""
    print("\n🎯 Testing Alias Creation")
    print("=" * 30)
    
    if not api_token:
        print("❌ No API token provided")
        return False
    
    # Get session first
    session_url = "https://api.fastmail.com/jmap/session"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
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
        
        if not accounts:
            print("❌ No accounts found in session")
            return False
        
        # Get the first account ID
        account_id = list(accounts.keys())[0]
        print(f"   📋 Using account ID: {account_id}")
        print(f"   🔗 API URL: {api_url}")
        
        # Try to create a test alias
        test_alias = f"test-api-token-{int(time.time())}@fastmail.com"
        target_email = "wg0@fastmail.com"
        
        payload = {
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
                                "description": "Test alias created via API token"
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        
        print(f"   📝 Creating test alias: {test_alias}")
        
        response = requests.post(api_url, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   📊 Response: {json.dumps(result, indent=2)}")
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    if method_response[0] == "Alias/set" and "created" in method_response[1]:
                        print(f"   🎉 Alias created successfully!")
                        print(f"   ✅ API token works for alias creation!")
                        return True
                    else:
                        print(f"   ❌ Alias creation failed: {method_response}")
                        return False
                else:
                    print(f"   ❌ Unexpected response format")
                    return False
                    
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                return False
        else:
            print(f"   ❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Error testing alias creation: {e}")
        return False

def main():
    """Main function to guide through API token setup."""
    print("🔧 Fastmail API Token Setup Guide")
    print("=" * 50)
    
    # Explain the difference
    explain_the_difference()
    
    # Guide through creation
    guide_api_token_creation()
    
    # Test the API token
    print("🧪 Ready to Test Your API Token")
    print("=" * 50)
    
    # Check if they have the API token
    api_token = os.getenv('FASTMAIL_API_TOKEN')
    if not api_token:
        print("🔑 Enter your Fastmail API token:")
        print("   (Should start with 'fma1-')")
        api_token = input("API Token: ").strip()
    
    if not api_token:
        print("❌ No API token provided")
        return
    
    print(f"\n🔍 Testing API token: {api_token[:20]}...")
    
    # Test the API token
    if test_api_token(api_token):
        print("✅ API token authentication works!")
        
        # Test alias creation
        if test_alias_creation(api_token):
            print("\n🎉 SUCCESS!")
            print("=" * 50)
            print("✅ Your API token works for alias creation!")
            print("✅ You can now use it to create aliases via JMAP API!")
            print()
            print("💡 Next steps:")
            print("   1. Set environment variable: export FASTMAIL_API_TOKEN='your_token_here'")
            print("   2. Use the working alias creation scripts")
            print("   3. Create the nya01 alias successfully!")
        else:
            print("\n❌ Alias creation failed")
            print("   Check your API token permissions")
    else:
        print("\n❌ API token test failed")
        print("   Please create a new API token (not app password)")

if __name__ == "__main__":
    main() 