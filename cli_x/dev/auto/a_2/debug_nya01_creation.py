#!/usr/bin/env python3
"""
Debug nya01 alias creation - see what the actual API response is.
"""

import requests
import json
import time

def debug_nya01_creation():
    """Debug the nya01 alias creation to see the actual response."""
    
    print("🔍 Debug nya01 Alias Creation")
    print("=" * 40)
    
    # Working API token and configuration
    api_token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    api_url = "https://api.fastmail.com/jmap/api/"
    account_id = "u2ef64041"
    
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
                            "description": "Debug creation of nya01 alias",
                            "forwardingEmail": "wg0@fastmail.com"
                        }
                    }
                },
                "0"
            ]
        ]
    }
    
    print(f"📝 Sending request...")
    print(f"   API URL: {api_url}")
    print(f"   Account ID: {account_id}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(api_url, json=payload, headers=headers)
        duration = time.time() - start_time
        
        print(f"\n📊 Response Details:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Response Time: {duration:.2f} seconds")
        
        if response.status_code == 200:
            print(f"   ✅ Got 200 response!")
            
            try:
                result = response.json()
                print(f"\n📄 Full Response JSON:")
                print(json.dumps(result, indent=2))
                
                if "methodResponses" in result:
                    method_response = result["methodResponses"][0]
                    print(f"\n🔍 Method Response Analysis:")
                    print(f"   Method: {method_response[0]}")
                    print(f"   Response Data: {json.dumps(method_response[1], indent=2)}")
                    
                    if method_response[0] == "MaskedEmail/set":
                        response_data = method_response[1]
                        
                        if "created" in response_data:
                            print(f"   ✅ Found 'created' field")
                            created = response_data["created"]
                            print(f"   Created objects: {list(created.keys())}")
                            
                            if "nya01" in created:
                                nya01_data = created["nya01"]
                                print(f"   🎉 nya01 created successfully!")
                                print(f"   📧 Email: {nya01_data.get('email', 'Unknown')}")
                                print(f"   📧 Forwards to: {nya01_data.get('forwardingEmail', 'Unknown')}")
                                return True
                            else:
                                print(f"   ❌ 'nya01' not found in created objects")
                                return False
                        elif "notCreated" in response_data:
                            print(f"   ❌ Found 'notCreated' field")
                            not_created = response_data["notCreated"]
                            print(f"   Not created objects: {json.dumps(not_created, indent=2)}")
                            return False
                        else:
                            print(f"   ❌ No 'created' or 'notCreated' field found")
                            return False
                    else:
                        print(f"   ❌ Unexpected method response: {method_response[0]}")
                        return False
                else:
                    print(f"   ❌ No 'methodResponses' field in response")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON decode error: {e}")
                print(f"   Raw response: {response.text[:500]}...")
                return False
                
        else:
            print(f"   ❌ Non-200 response: {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to debug nya01 creation."""
    
    print("🚀 Debug nya01 Alias Creation")
    print("=" * 50)
    print("🔍 This will show us exactly what happens when we try to create nya01")
    print()
    
    success = debug_nya01_creation()
    
    if success:
        print(f"\n🎉 SUCCESS!")
        print("=" * 50)
        print("✅ nya01 alias created successfully!")
        
    else:
        print(f"\n❌ FAILED")
        print("=" * 50)
        print("❌ Check the debug output above for details")

if __name__ == "__main__":
    main() 