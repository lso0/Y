#!/usr/bin/env python3
"""
YouTube Automation Client
Client for interacting with YouTube Automation Server with Infisical integration
"""

import argparse
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import aiohttp
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self, server_url: str = "http://localhost:8003"):
        """Initialize YouTube automation client"""
        self.server_url = server_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        try:
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Server is healthy")
                    
                    # Log credential status
                    if result.get('credentials_available'):
                        source = result.get('credential_source', 'unknown')
                        logger.info(f"🔐 Credentials available from: {source}")
                    else:
                        logger.warning("⚠️ No credentials detected on server")
                    
                    return result
                else:
                    logger.error(f"❌ Server health check failed: {response.status}")
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            return {"status": "unreachable", "error": str(e)}
    
    async def signin(
        self,
        signin_url: Optional[str] = None,
        headless: bool = True,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform YouTube/Google sign-in"""
        try:
            payload = {
                "headless": headless
            }
            
            if signin_url:
                payload["signin_url"] = signin_url
            if email:
                payload["email"] = email
            if password:
                payload["password"] = password
            
            logger.info(f"🔐 Requesting YouTube sign-in...")
            
            async with self.session.post(f"{self.server_url}/signin", json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    if result.get('success'):
                        logger.info("✅ Sign-in successful")
                    else:
                        logger.error(f"❌ Sign-in failed: {result.get('error')}")
                else:
                    logger.error(f"❌ Server error: {response.status}")
                
                return result
        except Exception as e:
            logger.error(f"❌ Sign-in request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def subscribe(
        self,
        channel_url: str,
        headless: bool = True
    ) -> Dict[str, Any]:
        """Subscribe to a YouTube channel"""
        try:
            payload = {
                "channel_url": channel_url,
                "headless": headless
            }
            
            logger.info(f"👤 Requesting channel subscription...")
            
            async with self.session.post(f"{self.server_url}/subscribe", json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    if result.get('success'):
                        if result.get('subscribed'):
                            logger.info("✅ Successfully subscribed to channel")
                        else:
                            logger.info("ℹ️ Already subscribed to channel")
                        
                        if result.get('channel_info'):
                            info = result['channel_info']
                            logger.info(f"📺 Channel: {info.get('channel_name', 'Unknown')}")
                            logger.info(f"👥 Subscribers: {info.get('subscriber_count', 'Unknown')}")
                    else:
                        logger.error(f"❌ Subscription failed: {result.get('error')}")
                else:
                    logger.error(f"❌ Server error: {response.status}")
                
                return result
        except Exception as e:
            logger.error(f"❌ Subscription request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def workflow(
        self,
        channel_url: str,
        signin_url: Optional[str] = None,
        headless: bool = True,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete workflow: Sign in and subscribe to channel"""
        try:
            payload = {
                "channel_url": channel_url,
                "headless": headless
            }
            
            if signin_url:
                payload["signin_url"] = signin_url
            if email:
                payload["email"] = email
            if password:
                payload["password"] = password
            
            logger.info(f"🎥 Starting complete YouTube automation workflow...")
            
            async with self.session.post(f"{self.server_url}/workflow", json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"✅ Workflow completed in {result.get('execution_time', 0):.2f}s")
                    
                    if result.get('success'):
                        logger.info(f"🔐 Signed in: {result.get('signed_in')}")
                        logger.info(f"👤 Subscribed: {result.get('subscribed')}")
                        
                        if result.get('channel_info'):
                            info = result['channel_info']
                            logger.info(f"📺 Channel: {info.get('channel_name', 'Unknown')}")
                            logger.info(f"👥 Subscribers: {info.get('subscriber_count', 'Unknown')}")
                    else:
                        logger.error(f"❌ Workflow failed: {result.get('error')}")
                else:
                    logger.error(f"❌ Server error: {response.status}")
                
                return result
        except Exception as e:
            logger.error(f"❌ Workflow request failed: {e}")
            return {"success": False, "error": str(e)}

# CLI Functions
async def test_server_health(server_url: str):
    """Test server connectivity and health"""
    async with YouTubeClient(server_url) as client:
        result = await client.health_check()
        print(json.dumps(result, indent=2))

async def perform_signin(server_url: str, signin_url: Optional[str], headless: bool, email: Optional[str], password: Optional[str]):
    """Perform YouTube sign-in"""
    async with YouTubeClient(server_url) as client:
        result = await client.signin(
            signin_url=signin_url,
            headless=headless,
            email=email,
            password=password
        )
        print(json.dumps(result, indent=2))

async def perform_subscription(server_url: str, channel_url: str, headless: bool):
    """Subscribe to a channel"""
    async with YouTubeClient(server_url) as client:
        result = await client.subscribe(
            channel_url=channel_url,
            headless=headless
        )
        print(json.dumps(result, indent=2))

async def perform_workflow(
    server_url: str,
    channel_url: str,
    signin_url: Optional[str],
    headless: bool,
    email: Optional[str],
    password: Optional[str]
):
    """Perform complete sign-in and subscription workflow"""
    async with YouTubeClient(server_url) as client:
        result = await client.workflow(
            channel_url=channel_url,
            signin_url=signin_url,
            headless=headless,
            email=email,
            password=password
        )
        print(json.dumps(result, indent=2))

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="YouTube Automation Client")
    parser.add_argument('--server', default='http://localhost:8003', help='Server URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check server health')
    
    # Sign-in command
    signin_parser = subparsers.add_parser('signin', help='Perform YouTube sign-in')
    signin_parser.add_argument('--signin-url', help='Custom Google sign-in URL (optional)')
    signin_parser.add_argument('--email', help='YouTube/Google email (optional - uses Infisical G_LSD_M_0)')
    signin_parser.add_argument('--password', help='YouTube/Google password (optional - uses Infisical G_LSD_P_0)')
    signin_parser.add_argument('--visible', action='store_true', help='Run browser in visible mode')
    
    # Subscribe command
    subscribe_parser = subparsers.add_parser('subscribe', help='Subscribe to a YouTube channel')
    subscribe_parser.add_argument('--channel-url', required=True, help='YouTube channel URL')
    subscribe_parser.add_argument('--visible', action='store_true', help='Run browser in visible mode')
    
    # Complete workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Complete sign-in and subscription workflow')
    workflow_parser.add_argument('--channel-url', required=True, help='YouTube channel URL')
    workflow_parser.add_argument('--signin-url', help='Custom Google sign-in URL (optional)')
    workflow_parser.add_argument('--email', help='YouTube/Google email (optional - uses Infisical G_LSD_M_0)')
    workflow_parser.add_argument('--password', help='YouTube/Google password (optional - uses Infisical G_LSD_P_0)')
    workflow_parser.add_argument('--visible', action='store_true', help='Run browser in visible mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute commands
    try:
        if args.command == 'health':
            asyncio.run(test_server_health(args.server))
        
        elif args.command == 'signin':
            asyncio.run(perform_signin(
                server_url=args.server,
                signin_url=args.signin_url,
                headless=not args.visible,
                email=args.email,
                password=args.password
            ))
        
        elif args.command == 'subscribe':
            asyncio.run(perform_subscription(
                server_url=args.server,
                channel_url=args.channel_url,
                headless=not args.visible
            ))
        
        elif args.command == 'workflow':
            asyncio.run(perform_workflow(
                server_url=args.server,
                channel_url=args.channel_url,
                signin_url=args.signin_url,
                headless=not args.visible,
                email=args.email,
                password=args.password
            ))
    
    except KeyboardInterrupt:
        logger.info("🛑 Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 