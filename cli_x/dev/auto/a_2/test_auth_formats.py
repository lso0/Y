#!/usr/bin/env python3
"""
Test different authentication formats for Fastmail app passwords.
The issue is that we're getting 401 "Invalid Authorization header, not bearer".
"""

import requests
import json
import os
import base64

def test_auth_formats(username, app_password):
    """Test different authentication formats."""
    print("🔍 Testing Different Authentication Formats...")
    
    # The API endpoint that expects Bearer auth
    url = "https://api.fastmail.com/jmap/api/"
    
    # Test different authentication methods
    auth_methods = [
        {
            "name": "App Password as Bearer Token",
            "headers": {
                "Authorization": f"Bearer {app_password}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "App Password with fma1 prefix",
            "headers": {
                "Authorization": f"Bearer fma1-{app_password}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Basic Auth (username:password)",
            "headers": {
                "Authorization": f"Basic {base64.b64encode(f'{username}:{app_password}'.encode()).decode()}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Basic Auth (email:password)",
            "headers": {
                "Authorization": f"Basic {base64.b64encode(f'{username}:{app_password}'.encode()).decode()}",
                "Content-Type": "application/json"
            }
        }
    ]
    
    payload = {
        "using": ["urn:ietf:params:jmap:core"],
        "methodCalls": [["getSession", {}, "0"]]
    }
    
    for method in auth_methods:
        print(f"\n📋 Testing: {method['name']}")
        
        try:
            response = requests.post(url, json=payload, headers=method['headers'])
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print(f"   ✅ {method['name']} works!")
                return method['headers']
            else:
                print(f"   ❌ {method['name']} failed")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    return None

def test_session_endpoint(username, app_password):
    """Test the session endpoint to understand the correct format."""
    print("\n🔍 Testing Session Endpoint...")
    
    # Try the session endpoint directly
    session_url = "https://api.fastmail.com/jmap/session/"
    
    auth_methods = [
        {
            "name": "Basic Auth to Session Endpoint",
            "headers": {
                "Authorization": f"Basic {base64.b64encode(f'{username}:{app_password}'.encode()).decode()}",
                "Content-Type": "application/json"
            }
        },
        {
            "name": "Bearer to Session Endpoint",
            "headers": {
                "Authorization": f"Bearer {app_password}",
                "Content-Type": "application/json"
            }
        }
    ]
    
    for method in auth_methods:
        print(f"\n📋 Testing: {method['name']}")
        
        try:
            response = requests.get(session_url, headers=method['headers'])
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print(f"   ✅ {method['name']} works!")
                try:
                    data = response.json()
                    print(f"   📊 Session data: {json.dumps(data, indent=2)}")
                    return data
                except:
                    pass
            else:
                print(f"   ❌ {method['name']} failed")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    return None

def research_fastmail_auth():
    """Research what we know about Fastmail authentication."""
    print("\n📚 Fastmail Authentication Research...")
    print("=" * 50)
    
    print("From the original a_1 script:")
    print("- Bearer token format: fma1-2ef64041-f0fe715e03eb23ecfb1f99685bb6e6e1-0-b81dcc290c0e4f36d9ee9da2015efa77")
    print("- User ID: 2ef64041")
    print("- Account ID: c75164099")
    print("- URL: https://api.fastmail.com/jmap/api/?u=2ef64041")
    
    print("\nApp Password Information:")
    print("- App passwords are meant to replace regular passwords")
    print("- They should work with Basic Auth (username:app_password)")
    print("- Or they might need to be converted to Bearer tokens")
    
    print("\nPossible issues:")
    print("1. App password scope might be incorrect")
    print("2. App password might need different formatting")
    print("3. We might need to get a bearer token first")
    print("4. The API endpoint might be different for app passwords")

def test_oauth_flow(username, app_password):
    """Test if we need to do an OAuth-style flow first."""
    print("\n🔍 Testing OAuth-style Authentication Flow...")
    
    # Try the standard OAuth token endpoint
    token_url = "https://api.fastmail.com/oauth/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": username,
        "client_secret": app_password
    }
    
    try:
        response = requests.post(token_url, data=data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("   ✅ OAuth flow works!")
            try:
                token_data = response.json()
                return token_data.get("access_token")
            except:
                pass
        else:
            print("   ❌ OAuth flow failed")
    except Exception as e:
        print(f"   💥 OAuth error: {e}")
    
    return None

def main():
    """Main function to test authentication."""
    print("🔐 Fastmail App Password Authentication Test")
    print("=" * 50)
    
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
    
    # Research what we know
    research_fastmail_auth()
    
    # Test different auth formats
    working_headers = test_auth_formats(username, app_password)
    
    # Test session endpoint
    session_data = test_session_endpoint(username, app_password)
    
    # Test OAuth flow
    oauth_token = test_oauth_flow(username, app_password)
    
    print("\n" + "=" * 50)
    print("🎯 Test Results")
    print("=" * 50)
    
    if working_headers:
        print(f"✅ Working authentication method found!")
        print(f"   Headers: {working_headers}")
    else:
        print("❌ No working authentication method found")
    
    if session_data:
        print(f"✅ Session endpoint works!")
    else:
        print("❌ Session endpoint failed")
    
    if oauth_token:
        print(f"✅ OAuth token obtained: {oauth_token[:20]}...")
    else:
        print("❌ OAuth flow failed")

if __name__ == "__main__":
    main() 