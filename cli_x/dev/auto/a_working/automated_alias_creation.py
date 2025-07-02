#!/usr/bin/env python3
"""
Automated Fastmail alias creation using Playwright
This script will:
1. Launch a browser
2. Navigate to Fastmail
3. Let you log in
4. Extract session data automatically
5. Create the alias using the JMAP API
"""

from playwright.sync_api import sync_playwright
import requests
import json
import time

def create_alias_with_playwright(alias_email, target_email, description=""):
    """Create an alias using Playwright to extract session data automatically"""
    
    with sync_playwright() as p:
        # Launch browser in headed mode so user can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("🌐 Navigating to Fastmail...")
        page.goto("https://app.fastmail.com")
        
        print("👤 Please log in to your Fastmail account in the browser window")
        print("📝 Navigate to Settings > Aliases after logging in")
        print("⏳ Press Enter here when you're logged in and on the main Fastmail page...")
        input()
        
        print("🔍 Extracting session data...")
        
        # Extract cookies
        cookies_dict = {}
        cookies = context.cookies()
        for cookie in cookies:
            if cookie['domain'] in ['.fastmail.com', 'app.fastmail.com', 'api.fastmail.com']:
                cookies_dict[cookie['name']] = cookie['value']
        
        print(f"🍪 Found {len(cookies_dict)} cookies")
        
        # Navigate to trigger a JMAP API call to get the Bearer token
        print("🔗 Making a request to extract Bearer token...")
        
        # Set up request interception to capture the Bearer token
        bearer_token = None
        user_id = None
        account_id = None
        
        def handle_request(request):
            nonlocal bearer_token, user_id, account_id
            if 'api.fastmail.com/jmap/api/' in request.url:
                # Extract user ID from URL
                if 'u=' in request.url:
                    user_id = request.url.split('u=')[1].split('&')[0]
                
                # Extract Bearer token
                auth_header = request.headers.get('authorization', '')
                if auth_header.startswith('Bearer '):
                    bearer_token = auth_header.replace('Bearer ', '')
                
                print(f"✅ Captured Bearer token: {bearer_token[:20]}...")
                print(f"✅ Captured User ID: {user_id}")
        
        page.on('request', handle_request)
        
        # Navigate to aliases page to trigger API calls
        try:
            page.goto("https://app.fastmail.com/settings/aliases")
            time.sleep(2)  # Wait for API calls to complete
        except:
            print("⚠️  Couldn't navigate to aliases page, trying alternative method...")
            # Try making any action that triggers an API call
            page.evaluate("window.location.reload()")
            time.sleep(2)
        
        # Try to extract account ID from page content or storage
        try:
            # Check if we can get account ID from localStorage or similar
            account_id = page.evaluate("""
                () => {
                    // Try to find account ID in various places
                    const storage = window.localStorage;
                    for (let key in storage) {
                        if (key.includes('account') || key.includes('user')) {
                            try {
                                const data = JSON.parse(storage[key]);
                                if (data.accountId) return data.accountId;
                                if (data.id && data.id.startsWith('c')) return data.id;
                            } catch (e) {}
                        }
                    }
                    return null;
                }
            """)
            
            if not account_id:
                # Fallback: use the known account ID from the logs
                account_id = "c75164099"
                print(f"⚠️  Using fallback account ID: {account_id}")
            else:
                print(f"✅ Extracted Account ID: {account_id}")
                
        except:
            account_id = "c75164099"  # Fallback
            print(f"⚠️  Using fallback account ID: {account_id}")
        
        browser.close()
        
        if not bearer_token or not user_id:
            print("❌ Failed to extract session data. Please try again.")
            return False
        
        # Now create the alias using the extracted data
        print(f"🎯 Creating alias: {alias_email} -> {target_email}")
        return create_alias_api(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description)

def create_alias_api(bearer_token, user_id, account_id, cookies, alias_email, target_email, description=""):
    """Create alias using the JMAP API with extracted session data"""
    
    jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Origin": "https://app.fastmail.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    
    payload = {
        "using": [
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
        ],
        "methodCalls": [
            [
                "Alias/set",
                {
                    "accountId": account_id,
                    "create": {
                        "k45": {
                            "email": alias_email,
                            "targetEmails": [target_email],
                            "targetGroupRef": None,
                            "restrictSendingTo": "everybody",
                            "description": description
                        }
                    },
                    "onSuccessUpdateIdentities": True
                },
                "0"
            ]
        ],
        "lastActivity": 0,
        "clientVersion": "b457b8b325-5000d76b8ac6ae6b"
    }
    
    try:
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        if response.status_code == 200:
            result = response.json()
            print("✅ Alias created successfully!")
            
            # Check if there were any errors in the response
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == "Alias/set":
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        print(f"🎉 Alias ID: {created_alias.get('id', 'Unknown')}")
                        print(f"🕐 Created at: {created_alias.get('createdAt', 'Unknown')}")
                    elif 'notCreated' in alias_result:
                        print(f"❌ Failed to create alias: {alias_result['notCreated']}")
                        return False
            
            return True
        else:
            print(f"❌ Failed to create alias. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating alias: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fastmail Automated Alias Creator")
    print("=" * 40)
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        exit(1)
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    success = create_alias_with_playwright(alias_email, target_email, description)
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
    else:
        print("\n❌ Failed to create alias. Please try again.") 