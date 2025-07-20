#!/usr/bin/env python3
"""
Persistent Session Manager for Fastmail Automation
Keeps browser session alive and proactively refreshes authentication
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")  # Load from Y/.env

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersistentSessionManager:
    def __init__(self, username: str, password: str, check_interval: int = 30):
        self.username = username
        self.password = password
        self.check_interval = check_interval  # seconds between health checks
        
        # Browser components
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Session data
        self.session_data = {
            'bearer_token': None,
            'user_id': None,
            'account_id': 'c75164099',  # Fallback account ID
            'cookies': {},
            'login_time': None,
            'last_activity': None,
            'token_refresh_count': 0
        }
        
        # Session health tracking
        self.is_logged_in = False
        self.last_health_check = None
        self.session_failure_count = 0
        self.max_session_failures = 3
        
        # Background task management
        self._health_monitor_task = None
        self._session_refresh_task = None
        self._running = False
        
    async def start(self) -> bool:
        """Start the persistent session manager"""
        logger.info("🚀 Starting Persistent Session Manager...")
        
        try:
            # Initialize browser
            if not await self._init_browser():
                return False
            
            # Perform initial login
            if not await self._perform_login():
                return False
            
            # Start background monitoring
            self._running = True
            self._health_monitor_task = asyncio.create_task(self._background_health_monitor())
            self._session_refresh_task = asyncio.create_task(self._background_session_refresh())
            
            logger.info("✅ Persistent Session Manager started successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start session manager: {e}")
            await self.stop()
            return False
    
    async def stop(self):
        """Stop the session manager and cleanup resources"""
        logger.info("🛑 Stopping Persistent Session Manager...")
        
        self._running = False
        
        # Cancel background tasks
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
        if self._session_refresh_task:
            self._session_refresh_task.cancel()
        
        # Cleanup browser
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        logger.info("✅ Session manager stopped")
    
    async def _init_browser(self) -> bool:
        """Initialize persistent browser session"""
        try:
            logger.info("🌐 Initializing persistent browser...")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            # Set up request interception for token capture
            await self.page.route("**/*", self._intercept_requests)
            
            logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser initialization failed: {e}")
            return False
    
    async def _intercept_requests(self, route):
        """Intercept requests to capture session data"""
        request = route.request
        
        try:
            if 'api.fastmail.com/jmap/api/' in request.url:
                # Extract user ID from URL
                if 'u=' in request.url:
                    user_id = request.url.split('u=')[1].split('&')[0]
                    if user_id != self.session_data['user_id']:
                        self.session_data['user_id'] = user_id
                        logger.info(f"🆔 Updated User ID: {user_id}")
                
                # Extract Bearer token
                auth_header = request.headers.get('authorization', '')
                if auth_header.startswith('Bearer '):
                    new_token = auth_header.replace('Bearer ', '')
                    if new_token != self.session_data['bearer_token']:
                        self.session_data['bearer_token'] = new_token
                        self.session_data['last_activity'] = datetime.now()
                        self.session_data['token_refresh_count'] += 1
                        logger.info(f"🔑 Token refreshed #{self.session_data['token_refresh_count']}: {new_token[:20]}...")
            
            await route.continue_()
            
        except Exception as e:
            logger.warning(f"⚠️  Request interception error: {e}")
            await route.continue_()
    
    async def _perform_login(self) -> bool:
        """Perform login to Fastmail"""
        logger.info("🔐 Performing login to Fastmail...")
        
        try:
            # Navigate to Fastmail
            await self.page.goto("https://app.fastmail.com", timeout=30000)
            
            # Fill username
            await self.page.wait_for_selector('input[name="username"], input[type="email"]', timeout=15000)
            await self.page.fill('input[name="username"]', self.username)
            logger.info("✅ Username filled")
            
            # Click Continue
            await self.page.click('button:has-text("Continue")')
            logger.info("✅ Continue clicked")
            
            # Fill password
            await self.page.wait_for_selector('input[type="password"]', timeout=10000)
            await self.page.fill('input[type="password"]', self.password)
            logger.info("✅ Password filled")
            
            # Submit login
            await self.page.click('button[type="submit"]')
            logger.info("✅ Login submitted")
            
            # Wait for login completion
            await self.page.wait_for_url("**/app.fastmail.com/**", timeout=20000)
            logger.info("✅ Login successful!")
            
            # Wait for session establishment
            await asyncio.sleep(3)
            
            # Update session data
            await self._update_session_data()
            
            # Trigger API calls to get Bearer token
            await self._trigger_api_calls()
            
            # Wait for token capture
            await self._wait_for_token_capture()
            
            self.is_logged_in = True
            self.session_failure_count = 0
            self.last_health_check = datetime.now()
            
            logger.info(f"🎉 Login complete! Session data captured.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            self.is_logged_in = False
            return False
    
    async def _update_session_data(self):
        """Update session data with current cookies"""
        try:
            cookies = await self.context.cookies()
            self.session_data['cookies'] = {
                cookie['name']: cookie['value'] 
                for cookie in cookies 
                if '.fastmail.com' in cookie['domain'] or 'app.fastmail.com' in cookie['domain']
            }
            self.session_data['login_time'] = datetime.now()
            
            logger.info(f"🍪 Session updated with {len(self.session_data['cookies'])} cookies")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to update session data: {e}")
    
    async def _trigger_api_calls(self):
        """Navigate to trigger JMAP API calls for Bearer token"""
        try:
            logger.info("🔗 Triggering API calls for Bearer token...")
            await self.page.goto("https://app.fastmail.com/settings/aliases", timeout=15000)
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(2)  # Wait for API calls
            logger.info("✅ API calls triggered")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not trigger API calls: {e}")
    
    async def _wait_for_token_capture(self, timeout: int = 10):
        """Wait for Bearer token to be captured"""
        logger.info("⏳ Waiting for Bearer token capture...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.session_data['bearer_token'] and self.session_data['user_id']:
                logger.info("✅ Bearer token captured successfully!")
                return True
            await asyncio.sleep(0.5)
        
        logger.warning("⚠️  Token capture timeout")
        return False
    
    async def _background_health_monitor(self):
        """Background task to monitor session health"""
        logger.info("🔍 Starting background health monitor...")
        
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                
                if not self._running:
                    break
                
                health_status = await self._check_session_health()
                self.last_health_check = datetime.now()
                
                if not health_status:
                    logger.warning("⚠️  Session health check failed!")
                    self.session_failure_count += 1
                    
                    if self.session_failure_count >= self.max_session_failures:
                        logger.error("❌ Maximum session failures reached, triggering refresh...")
                        # Trigger session refresh
                        asyncio.create_task(self._refresh_session())
                else:
                    # Reset failure count on successful health check
                    if self.session_failure_count > 0:
                        logger.info("✅ Session health recovered")
                        self.session_failure_count = 0
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
        
        logger.info("🔍 Health monitor stopped")
    
    async def _background_session_refresh(self):
        """Background task for proactive session refresh"""
        logger.info("🔄 Starting background session refresh task...")
        
        while self._running:
            try:
                # Check every 30 minutes for proactive refresh
                await asyncio.sleep(30 * 60)  # 30 minutes
                
                if not self._running:
                    break
                
                # Check if session is getting old (refresh every 90 minutes)
                if self.session_data['login_time']:
                    session_age = datetime.now() - self.session_data['login_time']
                    if session_age > timedelta(minutes=90):
                        logger.info("🔄 Proactive session refresh (90+ minutes old)")
                        await self._refresh_session()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Session refresh task error: {e}")
        
        logger.info("🔄 Session refresh task stopped")
    
    async def _check_session_health(self) -> bool:
        """Check if current session is healthy"""
        try:
            if not self.is_logged_in or not self.session_data['login_time']:
                return False
            
            # Check session age (warn if >2 hours)
            session_age = datetime.now() - self.session_data['login_time']
            if session_age > timedelta(hours=2):
                logger.warning(f"⚠️  Session is old: {session_age}")
                return False
            
            # Check essential session data
            if not self.session_data['bearer_token'] or not self.session_data['user_id']:
                logger.warning("⚠️  Missing essential session data")
                return False
            
            # Try a simple API test (navigate to a page that triggers API calls)
            try:
                await self.page.goto("https://app.fastmail.com/mail", wait_until="domcontentloaded", timeout=10000)
                return True
            except Exception as e:
                logger.warning(f"⚠️  Page navigation failed: {e}")
                return False
            
        except Exception as e:
            logger.warning(f"⚠️  Health check error: {e}")
            return False
    
    async def _refresh_session(self):
        """Refresh the session by re-logging"""
        logger.info("🔄 Refreshing session...")
        
        try:
            # Mark as not logged in
            self.is_logged_in = False
            
            # Clear session data
            self.session_data['bearer_token'] = None
            self.session_data['user_id'] = None
            self.session_data['cookies'] = {}
            
            # Perform fresh login
            if await self._perform_login():
                logger.info("✅ Session refreshed successfully!")
            else:
                logger.error("❌ Session refresh failed!")
                
        except Exception as e:
            logger.error(f"❌ Session refresh error: {e}")
    
    # Public API methods
    
    async def get_session_data(self) -> Dict[str, Any]:
        """Get current session data for API requests"""
        if not self.is_logged_in:
            raise Exception("Session not available")
        
        return {
            'bearer_token': self.session_data['bearer_token'],
            'user_id': self.session_data['user_id'],
            'account_id': self.session_data['account_id'],
            'cookies': self.session_data['cookies'],
            'jmap_url': f"https://api.fastmail.com/jmap/api/?u={self.session_data['user_id']}"
        }
    
    async def is_session_ready(self) -> bool:
        """Check if session is ready for API requests"""
        return (
            self.is_logged_in and 
            self.session_data['bearer_token'] and 
            self.session_data['user_id']
        )
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics and health information"""
        session_age = None
        if self.session_data['login_time']:
            session_age = (datetime.now() - self.session_data['login_time']).total_seconds()
        
        return {
            'is_logged_in': self.is_logged_in,
            'session_age_seconds': session_age,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'token_refresh_count': self.session_data['token_refresh_count'],
            'session_failure_count': self.session_failure_count,
            'cookies_count': len(self.session_data['cookies']),
            'bearer_token_present': bool(self.session_data['bearer_token']),
            'user_id': self.session_data['user_id']
        }

# Example usage
async def main():
    """Example usage of the persistent session manager"""
    # Load credentials from environment
    username = os.getenv("FASTMAIL_USERNAME")
    password = os.getenv("FASTMAIL_PASSWORD")
    
    if not username or not password:
        logger.error("❌ FastMail credentials not found in environment variables!")
        return
    
    manager = PersistentSessionManager(
        username=username,
        password=password,
        check_interval=30  # Check every 30 seconds
    )
    
    try:
        # Start the session manager
        if await manager.start():
            print("✅ Session manager started!")
            
            # Keep running and show stats
            for i in range(10):
                await asyncio.sleep(10)
                stats = await manager.get_session_stats()
                print(f"📊 Session stats: {stats}")
                
                if await manager.is_session_ready():
                    session_data = await manager.get_session_data()
                    print(f"🔑 Session ready! Token: {session_data['bearer_token'][:20]}...")
                
        else:
            print("❌ Failed to start session manager")
            
    finally:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main()) 