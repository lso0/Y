#!/usr/bin/env python3
"""
Optimized Alias Creator
Uses persistent session to create aliases instantly without re-login
"""

import asyncio
import logging
import requests
import json
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedAliasCreator:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        
    async def create_alias(self, alias_email: str, target_email: str, description: str = "") -> Dict[str, Any]:
        """Create alias using persistent session - no login required!"""
        start_time = datetime.now()
        
        try:
            # Ensure session is ready
            if not await self.session_manager.is_session_ready():
                logger.warning("🔄 Session not ready, waiting for initialization...")
                
                # Wait up to 30 seconds for session to be ready
                for i in range(30):
                    await asyncio.sleep(1)
                    if await self.session_manager.is_session_ready():
                        break
                else:
                    raise Exception("Session not ready after 30 seconds")
            
            # Get session data
            session_data = await self.session_manager.get_session_data()
            logger.info(f"🚀 Creating alias using persistent session: {alias_email} -> {target_email}")
            
            # Create alias using JMAP API
            result = await self._create_alias_api(
                session_data=session_data,
                alias_email=alias_email,
                target_email=target_email,
                description=description
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"⚡ Alias created in {execution_time:.2f}s (persistent session)")
            
            return {
                'success': True,
                'message': f'Alias {alias_email} created successfully',
                'alias_id': result.get('alias_id'),
                'created_at': result.get('created_at'),
                'execution_time': execution_time,
                'method': 'persistent_session'
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Failed to create alias: {e}")
            return {
                'success': False,
                'message': f'Failed to create alias: {str(e)}',
                'execution_time': execution_time,
                'method': 'persistent_session'
            }
    
    async def _create_alias_api(self, session_data: Dict[str, Any], alias_email: str, target_email: str, description: str = "") -> Dict[str, Any]:
        """Create alias using JMAP API with session data"""
        
        jmap_url = session_data['jmap_url']
        bearer_token = session_data['bearer_token']
        account_id = session_data['account_id']
        cookies = session_data['cookies']
        
        logger.info(f"🎯 Making JMAP API call to create alias...")
        
        # Prepare JMAP request payload
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
                            "alias1": {
                                "email": alias_email,
                                "forDomain": "fastmail.com",
                                "description": description,
                                "name": "",
                                "lastMessageAt": None,
                                "destination": target_email,
                                "isDisabled": False
                            }
                        }
                    },
                    "create_alias_request"
                ]
            ],
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
        
        # Run request in thread pool to avoid blocking async event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(jmap_url, json=payload, headers=headers, cookies=cookies, timeout=30)
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info("✅ JMAP API call successful!")
                
                # Parse the response
                method_responses = result.get('methodResponses', [])
                for method_response in method_responses:
                    if len(method_response) > 1 and method_response[0] == "Alias/set":
                        alias_result = method_response[1]
                        
                        if 'created' in alias_result and alias_result['created']:
                            # Success - extract alias details
                            created_alias = list(alias_result['created'].values())[0]
                            alias_id = created_alias.get('id', 'Unknown')
                            created_at = created_alias.get('createdAt', 'Unknown')
                            
                            logger.info(f"🎉 Alias ID: {alias_id}")
                            logger.info(f"🕐 Created at: {created_at}")
                            
                            return {
                                'alias_id': alias_id,
                                'created_at': created_at,
                                'email': alias_email,
                                'destination': target_email,
                                'description': description
                            }
                            
                        elif 'notCreated' in alias_result:
                            # Error creating alias
                            error_details = alias_result['notCreated']
                            error_msg = f"API error: {error_details}"
                            logger.error(f"❌ {error_msg}")
                            raise Exception(error_msg)
                
                # If we get here, the response format was unexpected
                logger.warning("⚠️  Unexpected response format")
                raise Exception("Unexpected API response format")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error: {e}")
                logger.error(f"Response text: {response.text[:200]}")
                raise Exception(f"Invalid JSON response: {str(e)}")
                
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"❌ API request failed: {error_msg}")
            raise Exception(error_msg)

# Convenience functions for different use cases

async def create_alias_fast(session_manager, alias_email: str, target_email: str, description: str = "") -> Dict[str, Any]:
    """Create alias using persistent session - fast convenience function"""
    creator = OptimizedAliasCreator(session_manager)
    return await creator.create_alias(alias_email, target_email, description)

async def batch_create_aliases(session_manager, aliases_list: list) -> list:
    """Create multiple aliases in batch using persistent session"""
    creator = OptimizedAliasCreator(session_manager)
    results = []
    
    logger.info(f"🚀 Starting batch creation of {len(aliases_list)} aliases...")
    
    for i, alias_data in enumerate(aliases_list, 1):
        alias_email = alias_data['alias_email']
        target_email = alias_data['target_email'] 
        description = alias_data.get('description', '')
        
        logger.info(f"📧 [{i}/{len(aliases_list)}] Creating: {alias_email}")
        
        result = await creator.create_alias(alias_email, target_email, description)
        results.append(result)
        
        # Small delay between requests to be respectful
        if i < len(aliases_list):
            await asyncio.sleep(0.5)
    
    successful = sum(1 for r in results if r['success'])
    logger.info(f"✅ Batch complete: {successful}/{len(aliases_list)} aliases created successfully")
    
    return results

# Example usage
async def demo():
    """Demo of optimized alias creation"""
    from persistent_session_manager import PersistentSessionManager
    
    # Start persistent session
    manager = PersistentSessionManager(
        username="wg0",
        password="ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK",
        check_interval=30
    )
    
    try:
        logger.info("🚀 Starting persistent session...")
        if await manager.start():
            logger.info("✅ Session ready!")
            
            # Single alias creation
            result1 = await create_alias_fast(
                manager, 
                "test001@fastmail.com", 
                "wg0@fastmail.com", 
                "Test alias"
            )
            print(f"📧 Single alias result: {result1}")
            
            # Batch alias creation
            aliases_to_create = [
                {'alias_email': 'batch001@fastmail.com', 'target_email': 'wg0@fastmail.com', 'description': 'Batch test 1'},
                {'alias_email': 'batch002@fastmail.com', 'target_email': 'wg0@fastmail.com', 'description': 'Batch test 2'},
                {'alias_email': 'batch003@fastmail.com', 'target_email': 'wg0@fastmail.com', 'description': 'Batch test 3'},
            ]
            
            batch_results = await batch_create_aliases(manager, aliases_to_create)
            print(f"📦 Batch results: {batch_results}")
            
        else:
            print("❌ Failed to start session")
            
    finally:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(demo()) 