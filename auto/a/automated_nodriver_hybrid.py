#!/usr/bin/env python3
"""
Hybrid nodriver Fastmail alias creation: Automated login + Manual Bearer token capture
This script combines nodriver's superior anti-detection with manual Bearer token capture
to create traditional aliases reliably.
"""

import asyncio
import json
import os
import sys
import time
import requests
from dotenv import load_dotenv
import nodriver as uc

# Load environment variables
load_dotenv()

async def auto_login_fastmail(tab, email, password):
    """Automate the Fastmail login process using nodriver"""
    print("🔐 Attempting to log in automatically...")
    
    try:
        # Wait for page to load
        await tab.sleep(2)
        
        print("✅ Looking for email input field...")
        
        # Try to find email input using various methods
        email_input = None
        
        # Method 1: Try specific ID (most reliable)
        try:
            email_input = await tab.select('#v22-input', timeout=5)
            print("✅ Found email input using ID selector")
        except:
            # Method 2: Try by input name
            try:
                email_input = await tab.select('input[name="username"]', timeout=5)
                print("✅ Found email input using name selector")
            except:
                # Method 3: Try by placeholder
                try:
                    email_input = await tab.select('input[placeholder*="email"]', timeout=5)
                    print("✅ Found email input using placeholder selector")
                except:
                    print("❌ Could not find email input field")
                    return False
        
        if not email_input:
            print("❌ Could not find email input field")
            return False
        
        # Clear and fill email
        await email_input.click()
        await email_input.send_keys(email)
        print(f"✅ Entered email: {email}")
        
        # Look for password field or continue button
        try:
            password_input = await tab.select('input[type="password"]', timeout=2)
            if password_input:
                print("✅ Found password field immediately")
                await password_input.click()
                await password_input.send_keys(password)
                print("✅ Entered password")
            else:
                raise Exception("Password field not visible")
        except:
            # Need to click Continue first
            print("🔄 Looking for Continue button...")
            try:
                # Try the specific continue button ID
                continue_btn = await tab.select('#v25', timeout=3)
                print("✅ Found continue button using ID")
            except:
                # Try finding by text
                try:
                    continue_btn = await tab.find("Continue", timeout=3)
                    print("✅ Found continue button using text search")
                except:
                    print("❌ Could not find continue button")
                    return False
            
            await continue_btn.click()
            print("✅ Clicked continue button")
            await tab.sleep(2)
            
            # Now find password field
            password_input = await tab.select('input[type="password"]', timeout=10)
            await password_input.click()
            await password_input.send_keys(password)
            print("✅ Entered password (second step)")
        
        # Submit the form
        try:
            submit_btn = await tab.select('button[type="submit"]', timeout=5)
            await submit_btn.click()
            print("✅ Clicked login button")
        except:
            # Try finding login button by text
            try:
                login_btn = await tab.find("Sign in", timeout=3)
                await login_btn.click()
                print("✅ Clicked Sign in button")
            except:
                print("⚠️  Could not find submit button, trying Enter key")
                await password_input.send_keys('\n')
        
        # Wait for login to complete
        print("⏳ Waiting for login to complete...")
        await tab.sleep(3)
        
        # Check if we're logged in by looking for URL change or specific elements
        current_url = tab.url
        print(f"🔍 Current URL: {current_url}")
        
        if 'u=' in current_url or 'mail' in current_url:
            print("✅ Login successful!")
            return True
        else:
            # Try waiting a bit more and check again
            await tab.sleep(5)
            current_url = tab.url
            if 'u=' in current_url or 'mail' in current_url:
                print("✅ Login successful (delayed)!")
                return True
            else:
                print("❌ Login may have failed")
                return False
            
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

async def create_alias_with_nodriver_hybrid(alias_email, target_email, description=""):
    """Create alias using nodriver hybrid approach: automated login + manual Bearer token capture"""
    
    # Load credentials from environment
    email = os.getenv('FASTMAIL_EMAIL')
    password = os.getenv('FASTMAIL_API_PASSWORD')
    
    if not email or not password:
        print("❌ Missing FASTMAIL_EMAIL or FASTMAIL_API_PASSWORD in .env file")
        return False
    
    print("🥷 Starting nodriver in headed mode for hybrid approach...")
    # Use headed mode for manual interaction
    browser = await uc.start(
        headless=False,
        browser_args=[
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080'
        ],
        expert=True  # Enable expert mode for better capabilities
    )
    
    try:
        print("🌐 Navigating to Fastmail...")
        tab = await browser.get("https://app.fastmail.com")
        
        # Auto-login
        if not await auto_login_fastmail(tab, email, password):
            print("❌ Auto-login failed.")
            try:
                await browser.stop()
            except:
                browser.stop()
            return False
        
        print("✅ Login successful! Now setting up Bearer token capture...")
        
        # Set up variables for token capture
        bearer_token = None
        user_id = None
        account_id = None
        captured_requests = []
        
        # Enhanced request handler for nodriver
        async def handle_network_request(event):
            nonlocal bearer_token, user_id, account_id, captured_requests
            
            try:
                request = event.get('request', {})
                url = request.get('url', '')
                headers = request.get('headers', {})
                
                # Log Fastmail API requests
                if 'api.fastmail.com' in url:
                    captured_requests.append({'url': url, 'headers': headers})
                    print(f"🎯 Fastmail API call: {url}")
                    
                    if 'jmap/api/' in url:
                        print(f"🏆 JMAP API call found: {url}")
                        
                        # Extract user ID from URL
                        if 'u=' in url:
                            user_id = url.split('u=')[1].split('&')[0]
                            print(f"✅ Captured User ID: {user_id}")
                        
                        # Extract Bearer token from headers
                        auth_header = headers.get('authorization', '') or headers.get('Authorization', '')
                        if auth_header and auth_header.startswith('Bearer '):
                            bearer_token = auth_header.replace('Bearer ', '')
                            print(f"✅ Captured Bearer token: {bearer_token[:20]}...")
            except Exception as e:
                print(f"⚠️  Error processing network event: {e}")
        
        # Try to set up network monitoring
        try:
            # Enable network domain
            await tab.send('Network.enable')
            # Add event listener for network requests
            await tab.add_handler('Network.requestWillBeSent', handle_network_request)
            print("✅ Network monitoring enabled")
        except Exception as e:
            print(f"⚠️  Network monitoring setup failed: {e}")
            print("✅ Continuing with manual Bearer token capture")
        
        # Manual step for Bearer token capture (like hybrid Playwright approach)
        print("\n" + "="*70)
        print("🔍 MANUAL STEP REQUIRED FOR BEARER TOKEN CAPTURE")
        print("="*70)
        print("👤 In the browser window that just opened:")
        print("   1. Navigate to Settings → Aliases (or any settings page)")
        print("   2. Click around a bit to trigger API calls")
        print("   3. You should see Bearer token captured messages above")
        print("⏳ Press Enter here when you see:")
        print("   ✅ Captured Bearer token: xxxxxxxxxx...")
        print("   (If you don't see it, try refreshing the page or clicking different settings)")
        print("="*70)
        
        input()
        
        # Give a moment for any final API calls
        await tab.sleep(2)
        
        # Try alternative extraction methods if network monitoring didn't work
        if not bearer_token:
            print("🔍 Trying alternative Bearer token extraction methods...")
            
            # Method 1: Extract from browser storage
            try:
                stored_token = await tab.evaluate("""
                    () => {
                        // Look for tokens in localStorage
                        for (let key in localStorage) {
                            try {
                                const data = JSON.parse(localStorage[key]);
                                if (data.token && data.token.startsWith('fma1-')) {
                                    return data.token;
                                }
                                if (typeof data === 'string' && data.startsWith('fma1-')) {
                                    return data;
                                }
                            } catch (e) {}
                        }
                        
                        // Look for tokens in sessionStorage
                        for (let key in sessionStorage) {
                            try {
                                const data = JSON.parse(sessionStorage[key]);
                                if (data.token && data.token.startsWith('fma1-')) {
                                    return data.token;
                                }
                                if (typeof data === 'string' && data.startsWith('fma1-')) {
                                    return data;
                                }
                            } catch (e) {}
                        }
                        
                        // Try looking in window object
                        if (window.FM && window.FM.token) {
                            return window.FM.token;
                        }
                        
                        // Try looking for cookie or other auth data
                        if (document.cookie) {
                            const cookies = document.cookie.split(';');
                            for (let cookie of cookies) {
                                if (cookie.includes('fma1-')) {
                                    const match = cookie.match(/fma1-[a-zA-Z0-9-]+/);
                                    if (match) return match[0];
                                }
                            }
                        }
                        
                        return null;
                    }
                """)
                
                if stored_token:
                    bearer_token = stored_token
                    print(f"✅ Found Bearer token in browser storage: {bearer_token[:20]}...")
            except Exception as e:
                print(f"⚠️  Could not extract from storage: {e}")
            
            # Method 2: Try triggering some API calls to capture tokens
            if not bearer_token:
                print("🔄 Attempting to trigger API calls to capture Bearer token...")
                try:
                    # Navigate to a settings page that definitely makes API calls
                    current_url = tab.url
                    if 'app.fastmail.com' in current_url:
                        settings_url = current_url.replace('#', '#settings/aliases')
                        await tab.get(settings_url)
                        await tab.sleep(2)
                        
                        # Try extracting again after triggering API calls
                        stored_token = await tab.evaluate("""
                            () => {
                                for (let key in localStorage) {
                                    try {
                                        const data = JSON.parse(localStorage[key]);
                                        if (data.token && data.token.startsWith('fma1-')) {
                                            return data.token;
                                        }
                                    } catch (e) {}
                                }
                                return null;
                            }
                        """)
                        
                        if stored_token:
                            bearer_token = stored_token
                            print(f"✅ Captured Bearer token after API trigger: {bearer_token[:20]}...")
                
                except Exception as e:
                    print(f"⚠️  API trigger method failed: {e}")
        
        # Extract user ID from URL if not captured
        if not user_id:
            current_url = tab.url
            if 'u=' in current_url:
                user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                print(f"✅ Extracted User ID from URL: {user_id}")
        
        # Try to extract account ID
        try:
            account_id = await tab.evaluate("""
                () => {
                    // Try localStorage
                    for (let key in localStorage) {
                        try {
                            const data = JSON.parse(localStorage[key]);
                            if (data.accountId) return data.accountId;
                            if (data.id && data.id.startsWith('c')) return data.id;
                        } catch (e) {}
                    }
                    
                    // Try sessionStorage
                    for (let key in sessionStorage) {
                        try {
                            const data = JSON.parse(sessionStorage[key]);
                            if (data.accountId) return data.accountId;
                            if (data.id && data.id.startsWith('c')) return data.id;
                        } catch (e) {}
                    }
                    
                    return null;
                }
            """)
            
            if account_id:
                print(f"✅ Extracted Account ID from browser: {account_id}")
            else:
                account_id = "c75164099"  # Fallback
                print(f"⚠️  Using fallback account ID: {account_id}")
                
        except:
            account_id = "c75164099"
            print(f"⚠️  Using fallback account ID: {account_id}")
        
        # Get cookies (might be needed for API calls)
        cookies_dict = {}
        
        try:
            await browser.stop()
        except:
            browser.stop()
        
        if not bearer_token or not user_id:
            print("❌ Failed to capture Bearer token. Please try again.")
            print("💡 Make sure to navigate to Settings → Aliases and interact with the page")
            return False
        
        # Now create the traditional alias using the captured session data
        print(f"🎯 Creating traditional alias: {alias_email} -> {target_email}")
        return await create_traditional_alias(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description)
        
    except Exception as e:
        print(f"❌ Error with nodriver hybrid: {e}")
        try:
            await browser.stop()
        except:
            browser.stop()
        return False

async def create_traditional_alias(bearer_token, user_id, account_id, cookies, alias_email, target_email, description=""):
    """Create a traditional alias using the working version's approach"""
    
    # If we don't have account_id, get it from API
    if not account_id or account_id == "c75164099":
        print("🔍 Fetching account ID from JMAP Session API...")
        session_url = f"https://api.fastmail.com/jmap/session/?u={user_id}"
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        try:
            response = requests.get(session_url, headers=headers, cookies=cookies)
            if response.status_code == 200:
                session_data = response.json()
                accounts = session_data.get('accounts', {})
                if accounts:
                    account_id = list(accounts.keys())[0]
                    print(f"✅ Got Account ID from API: {account_id}")
        except Exception as e:
            print(f"⚠️  Session API failed, using fallback: {e}")
    
    jmap_url = f"https://api.fastmail.com/jmap/api/?u={user_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Origin": "https://app.fastmail.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    }
    
    # Use the exact payload from the working version for traditional aliases
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
        print("🔄 Creating traditional alias with Alias/set method...")
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Traditional alias created successfully!")
            
            # Check the response for success
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == "Alias/set":
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        print(f"🎉 Traditional Alias ID: {created_alias.get('id', 'Unknown')}")
                        print(f"🎉 Alias Email: {alias_email}")
                        print(f"🎯 Target Email: {target_email}")
                        print(f"🕐 Created at: {created_alias.get('createdAt', 'Unknown')}")
                        return True
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

async def main():
    print("🥷 Fastmail nodriver Hybrid Alias Creator")
    print("Superior Anti-Detection + Manual Bearer Token Capture")
    print("=" * 60)
    print("🖥️  Running in headed mode (optimal for this approach)")
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        return False
    
    print(f"\n🎯 Creating traditional alias: {alias_email} -> {target_email}")
    print("📁 Make sure you have a .env file with FASTMAIL_EMAIL and FASTMAIL_API_PASSWORD")
    
    success = await create_alias_with_nodriver_hybrid(alias_email, target_email, description)
    
    if success:
        print("\n🎉 SUCCESS! Your traditional alias has been created.")
        print("📧 Check Settings → Aliases in your Fastmail dashboard!")
        return True
    else:
        print("\n❌ Failed to create alias. Please try again.")
        return False

if __name__ == "__main__":
    # Use nodriver's event loop
    uc.loop().run_until_complete(main()) 