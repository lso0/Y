#!/usr/bin/env python3
"""
Simple Alias Creator - Command Line Version
Uses the same working logic as automated_alias_creation.py
"""

import sys
import asyncio
from playwright.async_api import async_playwright
import requests
import json
import time

async def create_alias(alias_email, target_email, description=""):
    """Create alias using the working approach from automated_alias_creation.py"""
    
    USERNAME = "wg0"
    PASSWORD = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"
    
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await browser.new_page()
        
        print(f"🌐 Navigating to Fastmail...")
        await page.goto("https://app.fastmail.com")
        
        print(f"🔐 Performing automatic login...")
        
        # Fill username
        await page.wait_for_selector('input[name="username"], input[type="email"]', timeout=10000)
        await page.fill('input[name="username"]', USERNAME)
        print("✅ Filled username")
        
        # Click Continue
        await page.click('button:has-text("Continue")')
        print("✅ Clicked Continue")
        
        # Wait for and fill password
        await page.wait_for_selector('input[type="password"]', timeout=8000)
        await page.fill('input[type="password"]', PASSWORD)
        print("✅ Filled password")
        
        # Submit login
        await page.wait_for_selector('button[type="submit"]', timeout=5000)
        await page.click('button[type="submit"]')
        print("✅ Clicked login")
        
        # Wait for login to complete
        await page.wait_for_url("**/app.fastmail.com/**", timeout=15000)
        print("✅ Login successful!")
        
        # Wait for session to establish
        await asyncio.sleep(3)
        
        print("🔍 Extracting session data...")
        
        # Extract cookies
        cookies_dict = {}
        cookies = await context.cookies()
        for cookie in cookies:
            if '.fastmail.com' in cookie['domain'] or 'app.fastmail.com' in cookie['domain']:
                cookies_dict[cookie['name']] = cookie['value']
        
        print(f"🍪 Found {len(cookies_dict)} cookies")
        
        # Set up request interception to capture Bearer token
        bearer_token = None
        user_id = None
        
        def handle_request(request):
            nonlocal bearer_token, user_id
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
        
        await page.route("**/*", lambda route: route.continue_())
        page.on('request', handle_request)
        
        # Navigate to aliases page to trigger API calls
        try:
            await page.goto("https://app.fastmail.com/settings/aliases")
            await page.wait_for_load_state("domcontentloaded", timeout=8000)
            await asyncio.sleep(2)  # Wait for API calls
            print("✅ Triggered API calls for session data")
        except Exception as e:
            print(f"⚠️  Could not navigate to aliases page: {e}")
        
        await browser.close()
        
        if not bearer_token or not user_id:
            print("❌ Failed to extract session data")
            return False
        
        # Create the alias using the extracted data
        print(f"🎯 Creating alias: {alias_email} -> {target_email}")
        
        jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
        
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
                        "accountId": "c75164099",  # Fallback account ID
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
        
        try:
            response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies_dict)
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
    if len(sys.argv) < 3:
        print("Usage: python simple_alias_creator.py <alias_email> <target_email> [description]")
        print("Example: python simple_alias_creator.py test@fastmail.com wg0@fastmail.com 'Test alias'")
        sys.exit(1)
    
    alias_email = sys.argv[1]
    target_email = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    
    print("🚀 Simple Alias Creator")
    print("=" * 40)
    print(f"📧 Alias: {alias_email}")
    print(f"🎯 Target: {target_email}")
    print(f"📝 Description: {description}")
    print()
    
    success = asyncio.run(create_alias(alias_email, target_email, description))
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
    else:
        print("\n❌ Failed to create alias.") 