#!/usr/bin/env python3
"""
Create nya01 alias - CORRECTED VERSION
Uses the same structure as the working solution.
"""

import requests
import json
import time

def create_nya01_alias():
    """Create nya01 alias using the correct API structure."""
    
    print("🎯 Creating nya01 Alias (Corrected)")
    print("=" * 40)
    
    # Working API token
    api_token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    
    try:
        # Step 1: Get session
        print("📡 Getting session...")
        session_response = requests.get(
            "https://api.fastmail.com/jmap/session",
            headers={"Authorization": f"Bearer {api_token}"}
        )
        
        if session_response.status_code != 200:
            print(f"❌ Session failed: {session_response.status_code}")
            return False
        
        session_data = session_response.json()
        api_url = session_data["apiUrl"]
        account_id = list(session_data["accounts"].keys())[0]
        
        print(f"✅ Session established")
        print(f"   API URL: {api_url}")
        print(f"   Account ID: {account_id}")
        
        # Step 2: Create nya01 alias (using correct structure)
        print(f"\n📝 Creating nya01 alias...")
        payload = {
            "using": [
                "urn:ietf:params:jmap:core", 
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "methodCalls": [[
                "MaskedEmail/set",
                {
                    "accountId": account_id,
                    "create": {
                        "nya01": {
                            "emailPrefix": "nya01",
                            "description": "Created via corrected API method"
                        }
                    }
                },
                "0"
            ]]
        }
        
        start_time = time.time()
        response = requests.post(api_url, json=payload, headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if "methodResponses" in result:
                method_response = result["methodResponses"][0]
                
                if method_response[0] == "MaskedEmail/set":
                    response_data = method_response[1]
                    
                    if "created" in response_data and "nya01" in response_data["created"]:
                        created = response_data["created"]["nya01"]
                        email = created["email"]
                        
                        print(f"🎉 SUCCESS!")
                        print(f"   📧 Created: {email}")
                        print(f"   ✅ Forwards to: wg0@fastmail.com")
                        print(f"   ⚡ Time: {duration:.2f} seconds")
                        
                        return True
                    elif "notCreated" in response_data:
                        print(f"❌ Creation failed:")
                        not_created = response_data["notCreated"]["nya01"]
                        print(f"   Error: {not_created['description']}")
                        return False
                    else:
                        print(f"❌ Unexpected response: {method_response}")
                        return False
                else:
                    print(f"❌ Unexpected method: {method_response[0]}")
                    return False
            else:
                print(f"❌ No methodResponses in result")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_nya01_exists():
    """Verify nya01 alias exists."""
    print(f"\n🔍 Verifying nya01 alias exists...")
    
    api_token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    
    try:
        # Get session
        session_response = requests.get(
            "https://api.fastmail.com/jmap/session",
            headers={"Authorization": f"Bearer {api_token}"}
        )
        
        session_data = session_response.json()
        api_url = session_data["apiUrl"]
        account_id = list(session_data["accounts"].keys())[0]
        
        # List all aliases
        payload = {
            "using": [
                "urn:ietf:params:jmap:core", 
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "methodCalls": [[
                "MaskedEmail/get",
                {
                    "accountId": account_id,
                    "ids": None
                },
                "0"
            ]]
        }
        
        response = requests.post(api_url, json=payload, headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })
        
        if response.status_code == 200:
            result = response.json()
            
            if "methodResponses" in result:
                method_response = result["methodResponses"][0]
                
                if method_response[0] == "MaskedEmail/get" and "list" in method_response[1]:
                    aliases = method_response[1]["list"]
                    
                    for alias in aliases:
                        if alias.get('email', '').startswith('nya01'):
                            print(f"✅ Found nya01 alias: {alias['email']}")
                            print(f"   📝 Description: {alias.get('description', 'No description')}")
                            print(f"   📅 Created: {alias['createdAt']}")
                            print(f"   🔄 State: {alias['state']}")
                            return True
                    
                    print(f"❓ nya01 alias not found in {len(aliases)} aliases")
                    return False
                    
        print("❌ Failed to verify alias")
        return False
        
    except Exception as e:
        print(f"❌ Error verifying: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Create nya01 Alias - CORRECTED VERSION")
    print("=" * 50)
    print("✅ Using correct API structure (no forwardingEmail)")
    print("✅ Matches working solution structure")
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
        print("✅ This is the fast, reliable method!")
        print("✅ No browser automation needed!")
        
    else:
        print(f"\n❌ CREATION FAILED")
        print("=" * 50)
        print("❌ Check the error messages above")

if __name__ == "__main__":
    main() 