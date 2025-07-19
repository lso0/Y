#!/usr/bin/env python3
"""
Create nya01 alias using the WORKING API token method.
This is the simple, fast, reliable method.
"""

import requests
import json
import time

def create_nya01_alias():
    """Create the nya01 alias using the working API token method."""
    
    print("🎯 Creating nya01 Alias")
    print("=" * 30)
    
    # Working API token and configuration
    api_token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    api_url = "https://api.fastmail.com/jmap/api/"
    account_id = "u2ef64041"
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Create MaskedEmail (nya01)
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
                            "description": "Created via API token method - working solution",
                            "forwardingEmail": "wg0@fastmail.com"
                        }
                    }
                },
                "0"
            ]
        ]
    }
    
    print(f"📝 Creating nya01 alias...")
    print(f"   API URL: {api_url}")
    print(f"   Account ID: {account_id}")
    print(f"   Method: API Token (working)")
    
    try:
        start_time = time.time()
        response = requests.post(api_url, json=payload, headers=headers)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    
                    if method_response[0] == "MaskedEmail/set":
                        if "created" in method_response[1]:
                            created = method_response[1]["created"]["nya01"]
                            print(f"🎉 SUCCESS!")
                            print(f"   📧 Created: {created['email']}")
                            print(f"   ✅ Forwards to: {created.get('forwardingEmail', 'wg0@fastmail.com')}")
                            print(f"   ⚡ Time: {duration:.2f} seconds")
                            return True
                        else:
                            print(f"❌ Creation failed: {method_response[1]}")
                            return False
                    else:
                        print(f"❌ Unexpected response: {method_response}")
                        return False
                else:
                    print(f"❌ Invalid response format: {result}")
                    return False
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text[:200]}...")
                return False
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error creating alias: {e}")
        return False

def verify_nya01_exists():
    """Verify that nya01 alias exists."""
    
    print(f"\n🔍 Verifying nya01 alias exists...")
    
    # Working API token and configuration
    api_token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    api_url = "https://api.fastmail.com/jmap/api/"
    account_id = "u2ef64041"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # List all MaskedEmails
    payload = {
        "using": [
            "urn:ietf:params:jmap:core",
            "https://www.fastmail.com/dev/maskedemail"
        ],
        "methodCalls": [
            [
                "MaskedEmail/get",
                {
                    "accountId": account_id,
                    "ids": None
                },
                "0"
            ]
        ]
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            if "methodResponses" in result:
                method_response = result["methodResponses"][0]
                
                if method_response[0] == "MaskedEmail/get" and "list" in method_response[1]:
                    aliases = method_response[1]["list"]
                    
                    for alias in aliases:
                        if alias.get('email', '').startswith('nya01'):
                            print(f"✅ Found nya01 alias: {alias['email']}")
                            print(f"   📧 Forwards to: {alias.get('forwardingEmail', 'Unknown')}")
                            print(f"   📝 Description: {alias.get('description', 'No description')}")
                            return True
                    
                    print(f"❓ nya01 alias not found in {len(aliases)} aliases")
                    return False
                else:
                    print(f"❌ Unexpected response format")
                    return False
            else:
                print(f"❌ Invalid response format")
                return False
                
        else:
            print(f"❌ Verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying alias: {e}")
        return False

def main():
    """Main function to create nya01 alias."""
    
    print("🚀 Create nya01 Alias - Working Solution")
    print("=" * 50)
    print("✅ Using API token method (proven to work)")
    print("✅ No browser automation required")
    print("✅ Pure HTTP automation")
    print()
    
    # Create the alias
    success = create_nya01_alias()
    
    if success:
        # Verify it exists
        verify_nya01_exists()
        
        print(f"\n🎉 COMPLETE SUCCESS!")
        print("=" * 50)
        print("✅ nya01 alias created successfully!")
        print("✅ This is the fast, reliable method you wanted!")
        print("✅ No ChromeDriver, Puppeteer, or Playwright needed!")
        
    else:
        print(f"\n❌ FAILED TO CREATE ALIAS")
        print("=" * 50)
        print("❌ Something went wrong - check the output above")

if __name__ == "__main__":
    main() 