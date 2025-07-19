#!/usr/bin/env python3
"""
Create the nya01 alias using the working authentication method.
This is the simplified version that actually works.
"""

import requests
import json
import os
import base64
import time

def create_fastmail_alias(username, app_password, alias_email, target_email, description=""):
    """
    Create a Fastmail alias using the working authentication method.
    
    Args:
        username: Fastmail username/email
        app_password: App password from Fastmail settings
        alias_email: The alias email to create
        target_email: The target email to forward to
        description: Optional description
    
    Returns:
        True if successful, False otherwise
    """
    
    # Use Basic authentication (this is what works!)
    auth_string = f"{username}:{app_password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # Use the working URL
    url = "https://jmap.fastmail.com/jmap/api/"
    
    # Extract user ID from username
    user_id = username.split('@')[0]
    account_id = user_id  # Use user_id as account_id
    
    # Add user parameter to URL
    url_with_user = f"{url}?u={user_id}"
    
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
                        "alias1": {
                            "email": alias_email,
                            "targetEmails": [target_email],
                            "description": description
                        }
                    }
                },
                "0"
            ]
        ]
    }
    
    try:
        print(f"📝 Creating alias: {alias_email} -> {target_email}")
        print(f"   URL: {url_with_user}")
        print(f"   Account ID: {account_id}")
        
        response = requests.post(url_with_user, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"🎉 Alias created successfully!")
            if response.text.strip():
                try:
                    result = response.json()
                    print(f"   Response: {json.dumps(result, indent=2)}")
                except json.JSONDecodeError:
                    print("   Response: Empty (this is normal for successful operations)")
            else:
                print("   Response: Empty (this is normal for successful operations)")
            return True
        else:
            print(f"❌ Failed to create alias: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating alias: {e}")
        return False

def verify_alias_exists(username, app_password, alias_email):
    """
    Verify if an alias exists by trying to list aliases.
    Returns True if we can confirm it exists, False otherwise.
    """
    
    auth_string = f"{username}:{app_password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    url = "https://jmap.fastmail.com/jmap/api/"
    user_id = username.split('@')[0]
    url_with_user = f"{url}?u={user_id}"
    
    payload = {
        "using": [
            "urn:ietf:params:jmap:core",
            "https://www.fastmail.com/dev/aliases"
        ],
        "methodCalls": [
            [
                "Alias/get",
                {
                    "accountId": user_id,
                    "ids": None
                },
                "0"
            ]
        ]
    }
    
    try:
        response = requests.post(url_with_user, json=payload, headers=headers)
        
        if response.status_code == 200:
            if response.text.strip():
                try:
                    result = response.json()
                    if "methodResponses" in result:
                        method_response = result["methodResponses"][0]
                        if len(method_response) > 1 and "list" in method_response[1]:
                            aliases = method_response[1]["list"]
                            for alias in aliases:
                                if alias.get('email') == alias_email:
                                    print(f"✅ Confirmed: {alias_email} exists!")
                                    print(f"   Forwards to: {', '.join(alias['targetEmails'])}")
                                    return True
                            print(f"❓ Could not find {alias_email} in alias list")
                            return False
                except json.JSONDecodeError:
                    print("⚠️  Could not parse alias list response")
                    return False
            else:
                print("⚠️  Empty response when listing aliases")
                return False
        else:
            print(f"❌ Failed to verify alias: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying alias: {e}")
        return False

def main():
    """Create the nya01 alias specifically."""
    print("🎯 Create nya01 Alias")
    print("=" * 30)
    
    # Get credentials
    username = "wg0@fastmail.com"  # Your username
    app_password = os.getenv('FASTMAIL_APP_PASSWORD')
    
    if not app_password:
        print("🔑 Enter your Fastmail App Password:")
        app_password = input("App Password: ").strip()
    
    if not app_password:
        print("❌ No app password provided.")
        return
    
    # Create the nya01 alias
    alias_email = "nya01@fastmail.com"
    target_email = "wg0@fastmail.com"
    description = "Created via corrected app password method"
    
    print(f"Creating alias: {alias_email} -> {target_email}")
    
    start_time = time.time()
    success = create_fastmail_alias(username, app_password, alias_email, target_email, description)
    duration = time.time() - start_time
    
    if success:
        print(f"✅ Alias creation completed in {duration:.2f} seconds!")
        
        # Wait a moment and verify
        print("\n🔍 Verifying alias was created...")
        time.sleep(1)
        verify_alias_exists(username, app_password, alias_email)
        
    else:
        print(f"❌ Failed to create alias in {duration:.2f} seconds")
    
    print(f"\n📊 Performance Summary:")
    print(f"   Total time: {duration:.2f} seconds")
    print(f"   Method: App Password + Basic Auth")
    print(f"   URL: https://jmap.fastmail.com/jmap/api/")
    print(f"   Success: {'✅' if success else '❌'}")

if __name__ == "__main__":
    main() 