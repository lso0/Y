#!/usr/bin/env python3
"""
Automated Fastmail alias creation using Playwright
This script will:
1. Launch browser with Playwright
2. Navigate to Fastmail
3. Allow manual login
4. Use the browser context to create aliases via JMAP API
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_fastmail_alias_playwright(alias_email, target_email, description="", headless=False):
    """Create a Fastmail alias using Playwright"""
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Install with: pip install playwright")
        print("Then run: playwright install")
        return False
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Navigating to Fastmail...")
            await page.goto("https://app.fastmail.com")
            
            print("👤 Please log in manually in the browser")
            print("⏳ Press Enter here when you're logged in and can see the main Fastmail interface...")
            input()
            
            # Wait a moment for the page to fully load
            await asyncio.sleep(2)
            
            # Get current URL to extract user ID
            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            
            user_id = None
            if 'u=' in current_url:
                user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                print(f"✅ Detected User ID: {user_id}")
            else:
                print("⚠️  Could not detect user ID from URL, using fallback")
                user_id = "2ef64041"
            
            # Step 1: Get session info from .well-known/jmap (like the working script)
            print("🔍 Getting JMAP session info...")
            session_response = await page.evaluate("""
                fetch('https://api.fastmail.com/.well-known/jmap', {
                    method: 'GET',
                    credentials: 'include'
                })
                .then(response => response.json())
                .then(data => ({success: true, data: data}))
                .catch(error => ({success: false, error: error.toString()}))
            """)
            
            if not session_response.get('success'):
                print(f"❌ Failed to get session info: {session_response.get('error')}")
                return False
            
            session_data = session_response.get('data', {})
            api_url = session_data.get('apiUrl')
            if not api_url:
                print("❌ No apiUrl found in session data")
                return False
            
            print(f"✅ Got API URL: {api_url}")
            
            # Extract account ID from session data
            primary_accounts = session_data.get('primaryAccounts', {})
            account_id = primary_accounts.get('urn:ietf:params:jmap:mail')
            if not account_id:
                account_id = f"u{user_id}"
                print(f"⚠️  Using fallback account ID: {account_id}")
            else:
                print(f"✅ Got account ID: {account_id}")
            
            # Step 2: Create the alias using Identity/set
            print(f"🎯 Creating alias: {alias_email} -> {target_email}")
            
            # Prepare the JMAP payload (like the working script)
            payload = {
                "using": [
                    "urn:ietf:params:jmap:core",
                    "urn:ietf:params:jmap:mail"
                ],
                "methodCalls": [
                    [
                        "Identity/set",
                        {
                            "accountId": account_id,
                            "create": {
                                "newAlias": {
                                    "name": alias_email.split('@')[0],
                                    "email": alias_email
                                }
                            }
                        },
                        "0"
                    ]
                ]
            }
            
            # Make the API call using the browser context
            api_response = await page.evaluate("""
                async (args) => {
                    const [url, payload] = args;
                    try {
                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json',
                                'Origin': 'https://app.fastmail.com',
                                'Referer': 'https://app.fastmail.com/'
                            },
                            body: JSON.stringify(payload),
                            credentials: 'include'
                        });
                        
                        if (!response.ok) {
                            const text = await response.text();
                            return {success: false, error: `HTTP ${response.status}: ${text}`};
                        }
                        
                        const data = await response.json();
                        return {success: true, data: data};
                    } catch (error) {
                        return {success: false, error: error.toString()};
                    }
                }
            """, [api_url, payload])
            
            if not api_response.get('success'):
                print(f"❌ API call failed: {api_response.get('error')}")
                return False
            
            # Parse the response
            result = api_response.get('data', {})
            print("✅ API call successful!")
            
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == "Identity/set":
                    identity_result = method_response[1]
                    if 'created' in identity_result and identity_result['created']:
                        created_identity = list(identity_result['created'].values())[0]
                        print(f"🎉 Success! Created identity:")
                        print(f"   ID: {created_identity.get('id', 'Unknown')}")
                        print(f"   📧 Email: {created_identity.get('email', 'Unknown')}")
                        print(f"   👤 Name: {created_identity.get('name', 'Unknown')}")
                        return True
                    elif 'notCreated' in identity_result:
                        not_created = identity_result['notCreated']
                        print(f"❌ Failed to create identity:")
                        for key, error in not_created.items():
                            print(f"   {key}: {error}")
                        return False
            
            print("✅ Alias creation completed!")
            return True
            
        finally:
            await browser.close()

def main():
    print("🚀 Fastmail Alias Creator (Playwright)")
    print("=" * 50)
    
    # Check for headless mode argument
    headless = False  # Default to visible browser for manual login
    if '--headless' in sys.argv:
        headless = True
        print("👻 Running in headless mode (not recommended for manual login)")
    else:
        print("🖥️  Running in headed mode (browser will be visible)")
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        return False
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    
    # Run the async function
    success = asyncio.run(create_fastmail_alias_playwright(
        alias_email, target_email, description, headless=headless
    ))
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
        return True
    else:
        print("\n❌ Failed to create alias. Please try again.")
        return False

if __name__ == "__main__":
    main() 