#!/usr/bin/env python3
"""
Automated Fastmail alias creation using nodriver
This script uses nodriver's superior anti-detection capabilities to attempt
100% automated headless alias creation with Bearer token capture.
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
        
        # Use nodriver's find methods which are more intelligent
        print("✅ Looking for email input field...")
        
        # Try to find email input using various methods
        email_input = None
        
        # Method 1: Try specific ID (most reliable)
        try:
            email_input = await tab.select('#v22-input', timeout=5)
            print("✅ Found email input using ID selector")
        except:
            # Method 2: Try by input type
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
        # Clear field by selecting all and typing over it
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

async def create_alias_with_nodriver(alias_email, target_email, description="", headless=True):
    """Create alias using nodriver's advanced capabilities"""
    
    # Load credentials from environment
    email = os.getenv('FASTMAIL_EMAIL')
    password = os.getenv('FASTMAIL_API_PASSWORD')
    
    if not email or not password:
        print("❌ Missing FASTMAIL_EMAIL or FASTMAIL_API_PASSWORD in .env file")
        return False
    
    print("🥷 Starting nodriver with expert mode...")
    # Use nodriver's start function with proper arguments
    browser = await uc.start(
        headless=headless,
        browser_args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080'
        ],
        expert=True  # Enable expert mode for advanced capabilities
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
        
        print("✅ Login successful! Now setting up advanced request interception...")
        
        # Set up variables for token capture
        bearer_token = None
        user_id = None
        account_id = None
        captured_requests = []
        
        # Add CDP event handler for network requests
        async def handle_request_will_be_sent(event):
            nonlocal bearer_token, user_id, account_id, captured_requests
            
            request = event.get('request', {})
            url = request.get('url', '')
            headers = request.get('headers', {})
            
            # Log all Fastmail API requests
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
        
        # Try to enable network events - if it fails, continue without it
        network_monitoring = False
        try:
            # Simple approach - try basic network enable first
            await tab.send('Network.enable')
            tab.add_handler('Network.requestWillBeSent', handle_request_will_be_sent)
            network_monitoring = True
            print("✅ Network event monitoring enabled")
        except Exception as e:
            print(f"⚠️  Advanced network monitoring failed: {e}")
            print("⚠️  Will try alternative Bearer token extraction methods")
        
        print("🔥 Forcing JMAP API calls with nodriver techniques...")
        
        # Method 1: Navigate to aliases page
        try:
            await tab.get("https://app.fastmail.com/settings/aliases")
            await tab.sleep(3)
            print("✅ Navigated to aliases page")
        except Exception as e:
            print(f"⚠️  Could not navigate to aliases: {e}")
        
        # Method 2: Try to trigger actions that cause API calls
        try:
            # Look for any settings-related elements and interact with them
            settings_elements = await tab.select_all('[data-testid], .settings, [class*="setting"]', timeout=2)
            if settings_elements:
                for elem in settings_elements[:3]:  # Try first 3 elements
                    try:
                        await elem.click()
                        await tab.sleep(1)
                    except:
                        pass
                print("✅ Interacted with settings elements")
        except:
            print("⚠️  Could not find settings elements")
        
        # Method 3: Try navigating to different pages
        pages_to_try = [
            "https://app.fastmail.com/settings/identities",
            "https://app.fastmail.com/settings/account",
            "https://app.fastmail.com/mail/Inbox/"
        ]
        
        for page_url in pages_to_try:
            if bearer_token:  # Stop if we got the token
                break
            try:
                await tab.get(page_url)
                await tab.sleep(2)
                print(f"✅ Navigated to {page_url}")
            except:
                print(f"⚠️  Could not navigate to {page_url}")
        
        # Wait a bit more for any delayed API calls
        await tab.sleep(3)
        
        print(f"📊 Total Fastmail API requests captured: {len(captured_requests)}")
        
        # If we didn't capture Bearer token through network monitoring, try alternative methods
        if not bearer_token:
            print("🔍 Trying alternative Bearer token extraction methods...")
            
            # Method 1: Try to extract from browser storage/localStorage
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
                        
                        return null;
                    }
                """)
                
                if stored_token:
                    bearer_token = stored_token
                    print(f"✅ Found Bearer token in browser storage: {bearer_token[:20]}...")
            except Exception as e:
                print(f"⚠️  Could not extract from storage: {e}")
            
            # Method 2: Try to extract user ID from current URL if available
            if not user_id:
                current_url = tab.url
                if 'u=' in current_url:
                    user_id = current_url.split('u=')[1].split('&')[0].split('#')[0]
                    print(f"✅ Extracted User ID from URL: {user_id}")
        
        # Try to extract account ID from page storage
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
                print("⚠️  Could not extract account ID from browser storage")
        except Exception as e:
            print(f"⚠️  Error extracting account ID: {e}")
        
        # Get cookies
        cookies_dict = {}
        try:
            # nodriver might have a different way to get cookies
            # For now, we'll handle this in the API call
            pass
        except:
            pass
        
        try:
            await browser.stop()
        except:
            browser.stop()
        
        # Check what we captured
        if bearer_token and user_id:
            print(f"🎉 Successfully captured session data!")
            print(f"   Bearer token: {bearer_token[:20]}...")
            print(f"   User ID: {user_id}")
            print(f"   Account ID: {account_id or 'Will fetch via API'}")
            
            # Create the traditional alias
            return await create_traditional_alias(bearer_token, user_id, account_id, cookies_dict, alias_email, target_email, description)
        else:
            print("❌ Failed to capture Bearer token from JMAP calls")
            print("💡 Falling back to API token method...")
            
            # Fallback to API token
            api_token = os.getenv('FASTMAIL_API_TOKEN')
            if api_token:
                return await create_traditional_alias(api_token, user_id or "2ef64041", None, {}, alias_email, target_email, description, is_api_token=True)
            else:
                print("❌ No FASTMAIL_API_TOKEN found for fallback")
                return False
        
    except Exception as e:
        print(f"❌ Error with nodriver: {e}")
        try:
            await browser.stop()
        except:
            browser.stop()
        return False

async def create_traditional_alias(bearer_token, user_id, account_id, cookies, alias_email, target_email, description="", is_api_token=False):
    """Create traditional alias using captured session data"""
    
    # If we don't have account_id, get it from API
    if not account_id:
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
                else:
                    account_id = "c75164099"  # Fallback
                    print(f"⚠️  Using fallback account ID: {account_id}")
            else:
                account_id = "c75164099"  # Fallback
                print(f"⚠️  Using fallback account ID: {account_id}")
        except Exception as e:
            account_id = "c75164099"  # Fallback
            print(f"⚠️  Using fallback account ID: {account_id}")
    
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
    
    if is_api_token:
        # Use MaskedEmail for API tokens
        print("🔄 Using API token - creating masked email...")
        payload = {
            "using": [
                "urn:ietf:params:jmap:core",
                "urn:ietf:params:jmap:mail",
                "urn:ietf:params:jmap:submission",
                "https://www.fastmail.com/dev/maskedemail"
            ],
            "methodCalls": [
                [
                    "MaskedEmail/set",
                    {
                        "accountId": account_id,
                        "create": {
                            "k45": {
                                "email": alias_email,
                                "forDomain": target_email.split('@')[1],
                                "description": description,
                                "state": "enabled",
                                "emailPrefix": alias_email.split('@')[0]
                            }
                        }
                    },
                    "0"
                ]
            ]
        }
        method_name = "MaskedEmail/set"
    else:
        # Use traditional Alias/set for browser session tokens
        print("🔄 Using browser session token - creating traditional alias...")
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
        method_name = "Alias/set"
    
    try:
        response = requests.post(jmap_url, json=payload, headers=headers, cookies=cookies)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            method_responses = result.get('methodResponses', [])
            for method_response in method_responses:
                if len(method_response) > 1 and method_response[0] == method_name:
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        if method_name == "Alias/set":
                            print(f"🎉 Traditional Alias created successfully!")
                            print(f"🎉 Alias ID: {created_alias.get('id', 'Unknown')}")
                            print(f"🎉 Alias Email: {alias_email}")
                            print(f"🎯 Target Email: {target_email}")
                        else:
                            print(f"🎉 Masked Email created successfully!")
                            print(f"🎉 Masked Email ID: {created_alias.get('id', 'Unknown')}")
                            print(f"🎉 Masked Email: {created_alias.get('email', 'Unknown')}")
                        print(f"🕐 Created at: {created_alias.get('createdAt', 'Unknown')}")
                        return True
                    elif 'notCreated' in alias_result:
                        print(f"❌ {method_name} failed: {alias_result['notCreated']}")
                        return False
                elif len(method_response) > 1 and method_response[0] == "error":
                    print(f"❌ API Error: {method_response[1]}")
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
    print("🥷 Fastmail Automated Alias Creator (nodriver)")
    print("Advanced Anti-Detection Technology")
    print("=" * 50)
    
    # Check for headless mode argument
    headless = True  # Default to headless for testing
    if '--headed' in sys.argv:
        headless = False
        print("🖥️  Running in headed mode")
    else:
        print("👻 Running in headless mode with advanced anti-detection")
    
    # Get alias details from user
    alias_email = input("Enter the alias email (e.g., nya04@fastmail.com): ").strip()
    target_email = input("Enter the target email (e.g., wg0@fastmail.com): ").strip()
    description = input("Enter description (optional): ").strip()
    
    if not alias_email or not target_email:
        print("❌ Alias email and target email are required!")
        return False
    
    print(f"\n🎯 Creating alias: {alias_email} -> {target_email}")
    print("📁 Make sure you have a .env file with credentials")
    
    success = await create_alias_with_nodriver(alias_email, target_email, description, headless=headless)
    
    if success:
        print("\n🎉 Success! Your alias has been created.")
        print("📧 Check your Fastmail dashboard!")
        return True
    else:
        print("\n❌ Failed to create alias.")
        return False

if __name__ == "__main__":
    # Use nodriver's event loop
    uc.loop().run_until_complete(main()) 