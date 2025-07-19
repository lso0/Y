#!/usr/bin/env python3
"""
Persistent Automation Server
Keeps Chromium browser and Fastmail session alive
Provides HTTP API for automation tasks
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import uvicorn
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Automation Server", description="Persistent browser automation")

class AliasRequest(BaseModel):
    alias_email: str
    target_email: str
    description: str = ""

class SessionStatus(BaseModel):
    logged_in: bool
    session_age: Optional[int] = None
    cookies_count: int = 0
    bearer_token_present: bool = False

class AutomationServer:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session_data = {
            'bearer_token': None,
            'user_id': None,
            'account_id': 'c75164099',  # Fallback account ID
            'cookies': {},
            'login_time': None,
            'last_activity': None
        }
        self.is_logged_in = False
        
        # Credentials
        self.USERNAME = "wg0"
        self.PASSWORD = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"
        
    async def start_browser(self):
        """Initialize persistent browser session"""
        logger.info("🚀 Starting persistent browser...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']  # Good for Ubuntu servers
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Set up request interception for session data
        await self.page.route("**/*", self._intercept_requests)
        
        logger.info("✅ Browser started successfully")
        
    async def _intercept_requests(self, route):
        """Intercept requests to capture session data"""
        request = route.request
        
        if 'api.fastmail.com/jmap/api/' in request.url:
            # Extract user ID from URL
            if 'u=' in request.url:
                self.session_data['user_id'] = request.url.split('u=')[1].split('&')[0]
            
            # Extract Bearer token
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                self.session_data['bearer_token'] = auth_header.replace('Bearer ', '')
                self.session_data['last_activity'] = datetime.now()
                logger.info(f"🔑 Updated Bearer token: {self.session_data['bearer_token'][:20]}...")
        
        await route.continue_()
        
    async def login(self):
        """Perform login to Fastmail"""
        logger.info("🔐 Performing login...")
        
        try:
            # Navigate to Fastmail
            await self.page.goto("https://app.fastmail.com")
            
            # Fill username
            await self.page.wait_for_selector('input[name="username"], input[type="email"]', timeout=10000)
            username_selector = 'input[name="username"]'
            await self.page.fill(username_selector, self.USERNAME)
            logger.info("✅ Filled username")
            
            # Click Continue
            continue_button = 'button:has-text("Continue")'
            await self.page.click(continue_button)
            logger.info("✅ Clicked Continue")
            
            # Wait for and fill password
            await self.page.wait_for_selector('input[type="password"]', timeout=8000)
            await self.page.fill('input[type="password"]', self.PASSWORD)
            logger.info("✅ Filled password")
            
            # Submit login
            await self.page.wait_for_selector('button[type="submit"]', timeout=5000)
            await self.page.click('button[type="submit"]')
            logger.info("✅ Clicked login")
            
            # Wait for login to complete
            await self.page.wait_for_url("**/app.fastmail.com/**", timeout=15000)
            logger.info("✅ Login successful!")
            
            # Wait for session to establish
            await asyncio.sleep(3)
            
            # Update session data
            cookies = await self.context.cookies()
            self.session_data['cookies'] = {
                cookie['name']: cookie['value'] 
                for cookie in cookies 
                if '.fastmail.com' in cookie['domain']
            }
            self.session_data['login_time'] = datetime.now()
            self.session_data['last_activity'] = datetime.now()
            self.is_logged_in = True
            
            # Trigger API calls to get Bearer token
            await self._trigger_api_calls()
            
            logger.info(f"🎉 Login complete! Found {len(self.session_data['cookies'])} cookies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            self.is_logged_in = False
            return False
            
    async def _trigger_api_calls(self):
        """Navigate to trigger JMAP API calls for Bearer token"""
        try:
            await self.page.goto("https://app.fastmail.com/settings/aliases")
            await self.page.wait_for_load_state("domcontentloaded", timeout=8000)
            await asyncio.sleep(2)  # Wait for API calls
            logger.info("✅ Triggered API calls for session data")
        except Exception as e:
            logger.warning(f"⚠️  Could not trigger API calls: {e}")
            
    async def check_session_health(self):
        """Check if current session is healthy"""
        if not self.is_logged_in or not self.session_data['login_time']:
            return False
            
        # Check session age
        session_age = datetime.now() - self.session_data['login_time']
        if session_age > timedelta(hours=2):  # Assume 2-hour session timeout
            logger.warning("⚠️  Session appears to be expired (>2 hours)")
            return False
            
        # Check if we have essential session data
        if not self.session_data['bearer_token'] or not self.session_data['user_id']:
            logger.warning("⚠️  Missing essential session data")
            return False
            
        return True
        
    async def refresh_session_if_needed(self):
        """Refresh session if it's stale"""
        if not await self.check_session_health():
            logger.info("🔄 Session needs refresh, logging in...")
            return await self.login()
        return True
        
    async def create_alias(self, alias_email: str, target_email: str, description: str = ""):
        """Create alias using current session"""
        # Ensure session is healthy
        if not await self.refresh_session_if_needed():
            raise HTTPException(status_code=500, detail="Failed to establish session")
            
        logger.info(f"🎯 Creating alias: {alias_email} -> {target_email}")
        
        # Use the JMAP API directly
        jmap_url = f"https://api.fastmail.com/jmap/api/?u={self.session_data['user_id']}"
        
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
                        "accountId": self.session_data['account_id'],
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
        
        # Execute request using the browser to maintain session
        result = await self.page.evaluate(f"""
            async () => {{
                const response = await fetch('{jmap_url}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer {self.session_data["bearer_token"]}',
                        'Origin': 'https://app.fastmail.com'
                    }},
                    body: JSON.stringify({json.dumps(payload)})
                }});
                return await response.json();
            }}
        """)
        
        # Process result
        if result and 'methodResponses' in result:
            for method_response in result['methodResponses']:
                if len(method_response) > 1 and method_response[0] == "Alias/set":
                    alias_result = method_response[1]
                    if 'created' in alias_result and alias_result['created']:
                        created_alias = list(alias_result['created'].values())[0]
                        alias_id = created_alias.get('id', 'Unknown')
                        created_at = created_alias.get('createdAt', 'Unknown')
                        
                        logger.info(f"✅ Alias created! ID: {alias_id}")
                        return {
                            "success": True,
                            "alias_id": alias_id,
                            "created_at": created_at,
                            "message": f"Alias {alias_email} -> {target_email} created successfully"
                        }
                    elif 'notCreated' in alias_result:
                        error_msg = str(alias_result['notCreated'])
                        logger.error(f"❌ Alias creation failed: {error_msg}")
                        raise HTTPException(status_code=400, detail=f"Alias creation failed: {error_msg}")
        
        raise HTTPException(status_code=500, detail="Unexpected API response")
        
    async def get_session_status(self):
        """Get current session status"""
        session_age = None
        if self.session_data['login_time']:
            session_age = int((datetime.now() - self.session_data['login_time']).total_seconds())
            
        return SessionStatus(
            logged_in=self.is_logged_in,
            session_age=session_age,
            cookies_count=len(self.session_data['cookies']),
            bearer_token_present=bool(self.session_data['bearer_token'])
        )
        
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# Global server instance
automation_server = AutomationServer()

@app.on_event("startup")
async def startup_event():
    """Initialize the automation server on startup"""
    await automation_server.start_browser()
    await automation_server.login()

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    await automation_server.cleanup()

@app.get("/status")
async def get_status():
    """Get server and session status"""
    session_status = await automation_server.get_session_status()
    return {
        "server": "running",
        "session": session_status,
        "uptime": time.time() - startup_time if 'startup_time' in globals() else 0
    }

@app.post("/alias/create")
async def create_alias(request: AliasRequest):
    """Create a new Fastmail alias"""
    try:
        result = await automation_server.create_alias(
            request.alias_email,
            request.target_email, 
            request.description
        )
        return result
    except Exception as e:
        logger.error(f"❌ Alias creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/refresh")
async def refresh_session():
    """Force refresh the login session"""
    success = await automation_server.login()
    if success:
        return {"success": True, "message": "Session refreshed successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to refresh session")

@app.get("/session/health")
async def check_session_health():
    """Check if current session is healthy"""
    healthy = await automation_server.check_session_health()
    return {"healthy": healthy, "details": await automation_server.get_session_status()}

if __name__ == "__main__":
    startup_time = time.time()
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info") 