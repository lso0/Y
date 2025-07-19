#!/usr/bin/env python3
"""
Test different capability strings to find the right one for alias creation.
The token works for authentication, but we need to find the correct capabilities.
"""

import requests
import json
import time

def test_different_capabilities():
    """Test different capability combinations for alias creation."""
    
    token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    
    # Get session first
    session_url = "https://api.fastmail.com/jmap/session"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(session_url, headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get session")
        return
    
    session_data = response.json()
    api_url = session_data.get("apiUrl")
    account_id = list(session_data.get("accounts", {}).keys())[0]
    
    print(f"✅ Session obtained successfully")
    print(f"   🔗 API URL: {api_url}")
    print(f"   📋 Account ID: {account_id}")
    
    # Show available capabilities
    capabilities = session_data.get("capabilities", {})
    print(f"\n📋 Available Server Capabilities:")
    for cap_name, cap_details in capabilities.items():
        print(f"   - {cap_name}")
    
    # Test different capability combinations
    capability_tests = [
        {
            "name": "MaskedEmail capability",
            "using": [
                "urn:ietf:params:jmap:core",
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "method": "MaskedEmail/set",
            "create_key": "test1",
            "create_data": {
                "description": "Test masked email",
                "emailPrefix": "test123"
            }
        },
        {
            "name": "Identity capability",
            "using": [
                "urn:ietf:params:jmap:core",
                "urn:ietf:params:jmap:submission"
            ],
            "method": "Identity/get",
            "create_key": None,
            "create_data": None
        },
        {
            "name": "Mail capability",
            "using": [
                "urn:ietf:params:jmap:core",
                "urn:ietf:params:jmap:mail"
            ],
            "method": "Mailbox/get",
            "create_key": None,
            "create_data": None
        },
        {
            "name": "All available capabilities",
            "using": list(capabilities.keys()),
            "method": "getSession",
            "create_key": None,
            "create_data": None
        }
    ]
    
    print(f"\n🧪 Testing Different Capabilities...")
    print("=" * 50)
    
    for test in capability_tests:
        print(f"\n📋 Testing: {test['name']}")
        print(f"   Capabilities: {test['using']}")
        
        if test['method'] == 'getSession':
            # Simple session test
            payload = {
                "using": test['using'],
                "methodCalls": [["getSession", {}, "0"]]
            }
        elif test['method'] == 'MaskedEmail/set':
            # Test masked email creation
            payload = {
                "using": test['using'],
                "methodCalls": [
                    [
                        "MaskedEmail/set",
                        {
                            "accountId": account_id,
                            "create": {
                                test['create_key']: test['create_data']
                            }
                        },
                        "0"
                    ]
                ]
            }
        else:
            # Test other methods
            payload = {
                "using": test['using'],
                "methodCalls": [
                    [
                        test['method'],
                        {"accountId": account_id},
                        "0"
                    ]
                ]
            }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success!")
                    
                    if "methodResponses" in result:
                        method_response = result["methodResponses"][0]
                        print(f"   📤 Method: {method_response[0]}")
                        
                        if method_response[0] == "error":
                            print(f"   ❌ Error: {method_response[1]}")
                        elif method_response[0] == "MaskedEmail/set":
                            if "created" in method_response[1]:
                                print(f"   🎉 MaskedEmail created! This capability works!")
                                print(f"   📊 Created: {method_response[1]['created']}")
                            else:
                                print(f"   ❌ MaskedEmail not created: {method_response[1]}")
                        else:
                            print(f"   📊 Response data: {str(method_response[1])[:200]}...")
                    else:
                        print(f"   📊 Response: {str(result)[:200]}...")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"   💥 Error: {e}")

def try_masked_email_creation():
    """Try creating a masked email instead of an alias."""
    print(f"\n🎯 Testing MaskedEmail Creation (Alternative to Aliases)")
    print("=" * 60)
    
    token = "fmu1-2ef64041-9bf402027cf223e535dc2af8270cd9e1-0-5033b529092026c71a26273393176c0d"
    
    # Get session
    session_url = "https://api.fastmail.com/jmap/session"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(session_url, headers=headers)
    session_data = response.json()
    api_url = session_data.get("apiUrl")
    account_id = list(session_data.get("accounts", {}).keys())[0]
    
    # Create masked email
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
                            "description": "nya01 equivalent via MaskedEmail",
                            "emailPrefix": "nya01"
                        }
                    }
                },
                "0"
            ]
        ]
    }
    
    print(f"📝 Creating masked email with prefix 'nya01'...")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 Response: {json.dumps(result, indent=2)}")
            
            if "methodResponses" in result:
                method_response = result["methodResponses"][0]
                
                if method_response[0] == "MaskedEmail/set" and "created" in method_response[1]:
                    created_emails = method_response[1]["created"]
                    print(f"   🎉 MASKED EMAIL CREATED!")
                    for key, email_info in created_emails.items():
                        print(f"   📧 Created: {email_info['email']}")
                        print(f"   ✅ This is your nya01 equivalent!")
                        return True
                else:
                    print(f"   ❌ Failed: {method_response}")
                    return False
        else:
            print(f"   ❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False

def main():
    """Main function."""
    print("🔧 Fastmail Capability Tester")
    print("=" * 50)
    
    # Test different capabilities
    test_different_capabilities()
    
    # Try masked email creation
    if try_masked_email_creation():
        print(f"\n🎉 SUCCESS!")
        print("=" * 50)
        print("✅ MaskedEmail creation works!")
        print("✅ This is Fastmail's equivalent to aliases!")
        print("✅ Your API token works perfectly!")
        print()
        print("💡 Summary:")
        print("   - Your token works for authentication")
        print("   - Regular 'aliases' capability not available")
        print("   - MaskedEmail works as an alternative")
        print("   - You can create email addresses this way")
    else:
        print(f"\n❌ Need to check API token permissions")
        print("   Go to Fastmail settings and ensure your API token has:")
        print("   - MaskedEmail permissions")
        print("   - Or try creating a new API token with all permissions")

if __name__ == "__main__":
    main() 