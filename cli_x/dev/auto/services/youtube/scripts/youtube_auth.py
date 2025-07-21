#!/usr/bin/env python3
"""
YouTube Authentication & Channel Management Automation
Uses nodriver for undetected Chrome automation with Infisical secrets
"""

import asyncio
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import nodriver as uc
from fake_useragent import UserAgent
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeAutomator:
    def __init__(self, headless: bool = True):
        """Initialize YouTube automation with nodriver"""
        self.browser = None
        self.page = None
        self.headless = headless
        self.user_data_dir = os.path.expanduser("~/.youtube_automation")
        self.ua = UserAgent()
        
        # Screenshot directory
        self.screenshot_dir = Path("services/youtube/data/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Load credentials from environment
        self.email = os.getenv('G_LSD_M_0') or os.getenv('YT_EMAIL', '')
        self.password = os.getenv('G_LSD_P_0') or os.getenv('YT_PASSWORD', '')
        
        if not self.email or not self.password:
            logger.error("❌ Missing credentials!")
            logger.info("Expected: G_LSD_M_0, G_LSD_P_0 (Infisical) or YT_EMAIL, YT_PASSWORD (fallback)")
        else:
            logger.info(f"✅ Credentials loaded for: {self.email[:3]}***@{self.email.split('@')[1]}")
    
    async def take_screenshot(self, name: str, description: str = "") -> str:
        """Take a screenshot and save it with timestamp"""
        try:
            if not self.page:
                logger.warning("No page available for screenshot")
                return ""
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            await self.page.save_screenshot(str(filepath))
            logger.info(f"📸 Screenshot saved: {filename} - {description}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Failed to take screenshot {name}: {e}")
            return ""
    
    async def start_browser(self) -> bool:
        """Start undetected Chrome browser"""
        try:
            logger.info("🚀 Starting undetected Chrome browser...")
            
            # Create user data directory
            Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
            
            # Browser configuration for maximum stealth
            config = uc.Config(
                headless=self.headless,
                user_data_dir=self.user_data_dir,
                no_sandbox=True,  # Critical for Ubuntu servers
                browser_args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Faster loading
                    '--disable-javascript-harmony-shipping',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-component-extensions-with-background-pages',
                    f'--user-agent={self.ua.random}'
                ]
            )
            
            self.browser = await uc.start(config=config)
            self.page = await self.browser.get('about:blank')
            
            # Take initial screenshot
            await self.take_screenshot("01_browser_started", "Browser startup successful")
            
            logger.info("✅ Browser started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start browser: {e}")
            return False
    
    async def navigate_to_youtube_signin(self, signin_url: Optional[str] = None) -> bool:
        """Navigate to YouTube sign-in URL"""
        try:
            # Use provided URL or default YouTube sign-in
            if not signin_url:
                signin_url = "https://accounts.google.com/signin/v2/identifier?service=youtube&hl=en&continue=https://www.youtube.com/"
            
            logger.info("🔗 Navigating to YouTube sign-in...")
            
            # Navigate to the sign-in URL
            await self.page.get(signin_url)
            await asyncio.sleep(3)
            
            await self.take_screenshot("02_signin_page", f"Sign-in page loaded: {signin_url[:50]}...")
            
            # Wait for page to load
            await self.page.wait_for_element('input[type="email"]', timeout=10)
            logger.info("✅ Sign-in page loaded")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to sign-in: {e}")
            await self.take_screenshot("02_signin_error", f"Sign-in navigation error: {str(e)[:50]}")
            return False
    
    async def perform_google_signin(self) -> bool:
        """Perform Google OAuth sign-in for YouTube"""
        try:
            if not self.email or not self.password:
                logger.error("❌ Credentials not available")
                return False
            
            logger.info("🔐 Starting Google sign-in process...")
            
            # Step 1: Enter email
            email_input = await self.page.wait_for_element('input[type="email"]', timeout=10)
            await email_input.clear()
            await email_input.send_keys(self.email)
            logger.info(f"📧 Entered email: {self.email[:3]}***@{self.email.split('@')[1]}")
            
            await self.take_screenshot("03_email_entered", f"Email entered: {self.email[:3]}***")
            
            # Click Next button (try multiple selectors)
            next_selectors = [
                '#identifierNext button',
                'button[jsname="LgbsSe"]',
                'div[role="button"][jsname="LgbsSe"]',
                '[data-primary-action-label] button'
            ]
            
            next_clicked = False
            for selector in next_selectors:
                try:
                    next_button = await self.page.wait_for_element(selector, timeout=3)
                    await next_button.click()
                    next_clicked = True
                    break
                except:
                    continue
            
            if not next_clicked:
                logger.error("❌ Could not find Next button after email")
                await self.take_screenshot("04_no_next_button", "Next button not found after email")
                return False
            
            await asyncio.sleep(3)
            await self.take_screenshot("05_after_email_next", "After clicking Next on email")
            
            # Step 2: Enter password
            password_input = await self.page.wait_for_element('input[type="password"]', timeout=10)
            await password_input.clear()
            await password_input.send_keys(self.password)
            logger.info("🔒 Entered password")
            
            await self.take_screenshot("06_password_entered", "Password entered")
            
            # Click Next button for password
            password_next_selectors = [
                '#passwordNext button',
                'button[jsname="LgbsSe"]',
                'div[role="button"][jsname="LgbsSe"]'
            ]
            
            password_next_clicked = False
            for selector in password_next_selectors:
                try:
                    password_next = await self.page.wait_for_element(selector, timeout=3)
                    await password_next.click()
                    password_next_clicked = True
                    break
                except:
                    continue
            
            if not password_next_clicked:
                logger.error("❌ Could not find Next button after password")
                await self.take_screenshot("07_no_password_next", "Next button not found after password")
                return False
            
            # Wait for successful login
            await asyncio.sleep(5)
            await self.take_screenshot("08_after_signin", "After clicking Sign In")
            
            current_url = await self.page.evaluate('window.location.href')
            
            if 'youtube.com' in current_url and 'accounts.google.com' not in current_url:
                logger.info("✅ Successfully signed in to YouTube")
                await self.take_screenshot("09_signin_success", f"Successfully signed in: {current_url[:50]}...")
                return True
            else:
                logger.warning(f"⚠️ Unexpected redirect: {current_url}")
                await self.take_screenshot("10_unexpected_redirect", f"Unexpected redirect: {current_url[:50]}...")
                # Still might be successful, let's check for YouTube elements
                try:
                    await self.page.wait_for_element('ytd-app', timeout=5)
                    logger.info("✅ YouTube app detected - sign-in successful")
                    await self.take_screenshot("11_youtube_app_detected", "YouTube app detected")
                    return True
                except:
                    await self.take_screenshot("12_signin_failed", "Sign-in verification failed")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Sign-in failed: {e}")
            await self.take_screenshot("13_signin_exception", f"Sign-in exception: {str(e)[:50]}")
            return False
    
    async def navigate_to_channel(self, channel_url: str) -> bool:
        """Navigate to a specific YouTube channel"""
        try:
            logger.info(f"📺 Navigating to channel: {channel_url}")
            await self.page.get(channel_url)
            await asyncio.sleep(3)
            
            await self.take_screenshot("14_channel_page", f"Channel page loaded: {channel_url}")
            
            # Wait for channel page to load
            await self.page.wait_for_element('ytd-c4-tabbed-header-renderer', timeout=10)
            logger.info("✅ Channel page loaded")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to navigate to channel: {e}")
            await self.take_screenshot("15_channel_error", f"Channel navigation error: {str(e)[:50]}")
            return False
    
    async def subscribe_to_channel(self) -> bool:
        """Subscribe to the current channel"""
        try:
            logger.info("👤 Attempting to subscribe to channel...")
            
            await self.take_screenshot("16_before_subscribe", "Before looking for subscribe button")
            
            # Look for subscribe button (multiple selectors for reliability)
            subscribe_selectors = [
                'ytd-subscribe-button-renderer button[aria-label*="Subscribe"]',
                'ytd-subscribe-button-renderer button:has-text("Subscribe")',
                '.ytd-subscribe-button-renderer #subscribe-button button',
                'yt-button-shape button[aria-label*="Subscribe"]',
                'button:has-text("Subscribe")'
            ]
            
            subscribe_button = None
            for selector in subscribe_selectors:
                try:
                    subscribe_button = await self.page.wait_for_element(selector, timeout=3)
                    if subscribe_button:
                        break
                except:
                    continue
            
            if not subscribe_button:
                logger.warning("⚠️ Subscribe button not found - might already be subscribed")
                await self.take_screenshot("17_no_subscribe_button", "Subscribe button not found")
                return False
            
            # Check if already subscribed
            button_text = await subscribe_button.evaluate('el => el.textContent')
            if 'subscribed' in button_text.lower():
                logger.info("ℹ️ Already subscribed to this channel")
                await self.take_screenshot("18_already_subscribed", "Already subscribed to channel")
                return True
            
            await self.take_screenshot("19_before_click_subscribe", "Before clicking subscribe button")
            
            # Click subscribe button
            await subscribe_button.click()
            await asyncio.sleep(2)
            
            await self.take_screenshot("20_after_subscribe", "After clicking subscribe")
            
            logger.info("✅ Successfully subscribed to channel")
            return True
            
        except Exception as e:
            logger.error(f"❌ Subscription failed: {e}")
            await self.take_screenshot("21_subscribe_error", f"Subscribe error: {str(e)[:50]}")
            return False
    
    async def get_channel_info(self) -> Dict[str, Any]:
        """Get information about the current channel"""
        try:
            # Extract channel name
            channel_name = await self.page.evaluate('''
                () => {
                    const nameElement = document.querySelector('ytd-channel-name yt-formatted-string') || 
                                      document.querySelector('#channel-name') ||
                                      document.querySelector('yt-formatted-string.ytd-channel-name');
                    return nameElement ? nameElement.textContent.trim() : null;
                }
            ''')
            
            # Extract subscriber count
            subscriber_count = await self.page.evaluate('''
                () => {
                    const subElement = document.querySelector('#subscriber-count') ||
                                     document.querySelector('.subscriber-count') ||
                                     document.querySelector('yt-formatted-string:has-text("subscriber")');
                    return subElement ? subElement.textContent.trim() : null;
                }
            ''')
            
            return {
                'channel_name': channel_name,
                'subscriber_count': subscriber_count,
                'url': await self.page.evaluate('window.location.href')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get channel info: {e}")
            return {}
    
    async def close_browser(self):
        """Clean up browser resources"""
        try:
            if self.browser:
                await self.take_screenshot("22_before_cleanup", "Before browser cleanup")
                await self.browser.stop()
                logger.info("🔧 Browser closed")
        except Exception as e:
            logger.error(f"❌ Error closing browser: {e}")

# Main automation function
async def automate_youtube_signin_and_subscribe(
    channel_url: str,
    signin_url: Optional[str] = None,
    headless: bool = True
) -> Dict[str, Any]:
    """
    Complete YouTube automation workflow
    
    Args:
        channel_url: YouTube channel URL to subscribe to
        signin_url: Optional custom Google sign-in URL (uses default if not provided)
        headless: Run browser in headless mode
    
    Returns:
        Dict with automation results
    """
    automator = YouTubeAutomator(headless=headless)
    result = {
        'success': False,
        'signed_in': False,
        'subscribed': False,
        'channel_info': {},
        'error': None
    }
    
    try:
        # Start browser
        if not await automator.start_browser():
            result['error'] = 'Failed to start browser'
            return result
        
        # Navigate to sign-in
        if not await automator.navigate_to_youtube_signin(signin_url):
            result['error'] = 'Failed to navigate to sign-in'
            return result
        
        # Perform sign-in
        if not await automator.perform_google_signin():
            result['error'] = 'Failed to sign in'
            return result
        
        result['signed_in'] = True
        
        # Navigate to channel
        if not await automator.navigate_to_channel(channel_url):
            result['error'] = 'Failed to navigate to channel'
            return result
        
        # Get channel info
        result['channel_info'] = await automator.get_channel_info()
        
        # Subscribe to channel
        if await automator.subscribe_to_channel():
            result['subscribed'] = True
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"❌ Automation failed: {e}")
    
    finally:
        await automator.close_browser()
    
    return result

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Authentication & Subscription Automation")
    parser.add_argument('--signin-url', help='Custom Google sign-in URL (optional)')
    parser.add_argument('--channel-url', required=True, help='YouTube channel URL to subscribe to')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--visible', action='store_true', help='Run with visible browser')
    
    args = parser.parse_args()
    
    # Run automation
    headless_mode = args.headless and not args.visible
    
    async def main():
        result = await automate_youtube_signin_and_subscribe(
            channel_url=args.channel_url,
            signin_url=args.signin_url,
            headless=headless_mode
        )
        
        print("\n🎥 YouTube Automation Results:")
        print(f"✅ Success: {result['success']}")
        print(f"🔐 Signed In: {result['signed_in']}")
        print(f"👤 Subscribed: {result['subscribed']}")
        
        if result['channel_info']:
            print(f"📺 Channel: {result['channel_info'].get('channel_name', 'Unknown')}")
            print(f"👥 Subscribers: {result['channel_info'].get('subscriber_count', 'Unknown')}")
        
        if result['error']:
            print(f"❌ Error: {result['error']}")
    
    asyncio.run(main()) 