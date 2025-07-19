#!/usr/bin/env python3
"""
Debug script to test Fastmail JMAP authentication with app passwords.
This helps understand why the 401 error is occurring.
"""

import requests
import json
import base64
import os

def test_bearer_auth(app_password, user_id=None):
    """Test Bearer token authentication."""
    print("🔍 Testing Bearer Token Authentication...")
    
    if user_id:
        url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    else:
        url = "https://api.fastmail.com/jmap/api/"
    
    headers = {
        "Authorization": f"Bearer {app_password}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "using": ["urn:ietf:params:jmap:core"],
        "methodCalls": [["getSession", {}, "0"]]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   URL: {url}")
        
        if response.status_code == 200:
            print("   ✅ Bearer auth successful!")
            return response.json()
        else:
            print(f"   ❌ Bearer auth failed: {response.text}")
            return None
    except Exception as e:
        print(f"   💥 Bearer auth error: {e}")
        return None

def test_basic_auth(username, app_password, user_id=None):
    """Test Basic authentication."""
    print("🔍 Testing Basic Authentication...")
    
    if user_id:
        url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    else:
        url = "https://api.fastmail.com/jmap/api/"
    
    # Basic auth with username and app password
    auth_string = f"{username}:{app_password}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "using": ["urn:ietf:params:jmap:core"],
        "methodCalls": [["getSession", {}, "0"]]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   URL: {url}")
        
        if response.status_code == 200:
            print("   ✅ Basic auth successful!")
            return response.json()
        else:
            print(f"   ❌ Basic auth failed: {response.text}")
            return None
    except Exception as e:
        print(f"   💥 Basic auth error: {e}")
        return None

def test_different_urls(app_password, username):
    """Test different URL formats."""
    print("🔍 Testing Different URL Formats...")
    
    urls = [
        "https://api.fastmail.com/jmap/api/",
        "https://api.fastmail.com/jmap/api/?u=",
        f"https://api.fastmail.com/jmap/api/?u={username}",
        "https://jmap.fastmail.com/jmap/api/",
        f"https://jmap.fastmail.com/jmap/api/?u={username}",
    ]
    
    for url in urls:
        print(f"\n   Testing URL: {url}")
        
        # Try Bearer auth
        headers = {
            "Authorization": f"Bearer {app_password}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "using": ["urn:ietf:params:jmap:core"],
            "methodCalls": [["getSession", {}, "0"]]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"      Status: {response.status_code}")
            if response.status_code == 200:
                print("      ✅ Success!")
                return response.json(), url
            else:
                print(f"      ❌ Failed: {response.text[:100]}...")
        except Exception as e:
            print(f"      💥 Error: {e}")
    
    return None, None

def analyze_original_token():
    """Analyze the token format from the original a_1 script."""
    print("🔍 Analyzing Original Token Format...")
    
    # From the original a_1 script
    original_token = "fma1-2ef64041-f0fe715e03eb23ecfb1f99685bb6e6e1-0-b81dcc290c0e4f36d9ee9da2015efa77"
    user_id = "2ef64041"
    
    print(f"   Original token: {original_token}")
    print(f"   User ID: {user_id}")
    print(f"   Token format: fma1-{user_id}-[rest]")
    
    # Test with the original format
    url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    headers = {
        "Authorization": f"Bearer {original_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "using": ["urn:ietf:params:jmap:core"],
        "methodCalls": [["getSession", {}, "0"]]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"   Status with original token: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Original token format works!")
            return response.json()
        else:
            print(f"   ❌ Original token failed: {response.text}")
    except Exception as e:
        print(f"   💥 Original token error: {e}")
    
    return None

def get_user_info_from_fastmail():
    """Instructions for getting user information."""
    print("📋 How to Get Your User Information:")
    print("=" * 50)
    print("1. Log into Fastmail web interface")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Network tab")
    print("4. Look for requests to 'api.fastmail.com'")
    print("5. Find the 'u=' parameter in the URL")
    print("6. That's your user ID")
    print("")
    print("Alternative: Look at the URL bar when logged in:")
    print("https://app.fastmail.com/mail/?u=YOUR_USER_ID")

def main():
    """Main debug function."""
    print("🐞 Fastmail JMAP Authentication Debug")
    print("=" * 50)
    
    # Get credentials
    app_password = os.getenv('FASTMAIL_APP_PASSWORD')
    if not app_password:
        print("Enter your app password:")
        app_password = input("App Password: ").strip()
    
    print("Enter your Fastmail username/email:")
    username = input("Username: ").strip()
    
    if not app_password or not username:
        print("❌ Need both app password and username")
        return
    
    print(f"\nTesting with:")
    print(f"Username: {username}")
    print(f"App Password: {app_password[:8]}...")
    
    # Test different authentication methods
    print("\n" + "=" * 50)
    
    # Test 1: Bearer auth without user ID
    result1 = test_bearer_auth(app_password)
    
    # Test 2: Bearer auth with username as user ID
    result2 = test_bearer_auth(app_password, username)
    
    # Test 3: Basic auth
    result3 = test_basic_auth(username, app_password)
    
    # Test 4: Basic auth with user ID
    result4 = test_basic_auth(username, app_password, username)
    
    # Test 5: Different URLs
    result5, working_url = test_different_urls(app_password, username)
    
    # Test 6: Analyze original token format
    result6 = analyze_original_token()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Debug Summary")
    print("=" * 50)
    
    if result1:
        print("✅ Bearer auth (no user ID) works")
    if result2:
        print("✅ Bearer auth (with user ID) works")
    if result3:
        print("✅ Basic auth works")
    if result4:
        print("✅ Basic auth (with user ID) works")
    if result5:
        print(f"✅ Alternative URL works: {working_url}")
    if result6:
        print("✅ Original token format analysis")
    
    if not any([result1, result2, result3, result4, result5]):
        print("❌ All authentication methods failed")
        print("\n💡 Possible issues:")
        print("   - App password doesn't have correct scope")
        print("   - App password is incorrect")
        print("   - Need to extract user ID from Fastmail session")
        print("   - Different authentication method required")
        
        get_user_info_from_fastmail()

if __name__ == "__main__":
    main() 