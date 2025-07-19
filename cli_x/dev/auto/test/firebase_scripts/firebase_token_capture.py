#!/usr/bin/env python3
"""
Firebase Token Capture and Direct API Usage
============================================

This script demonstrates how to:
1. Authenticate via browser automation (existing scripts)
2. Capture authentication tokens (ID tokens, session cookies, access tokens)
3. Use these tokens for direct Firebase REST API calls
4. Bypass browser automation for subsequent operations

This approach is much faster and more reliable than continued browser automation.
"""

import asyncio
import nodriver as uc
import os
import logging
import requests
import json
from datetime import datetime
from typing import Dict, Optional, Any

def setup_logging():
    """Set up logging to both file and console."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/firebase_token_capture_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger('firebase_token_capture')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

class FirebaseTokenCapture:
    """Capture Firebase authentication tokens for direct API usage."""
    
    def __init__(self, logger):
        self.logger = logger
        self.tokens = {}
        self.cookies = {}
        self.project_id = None
        
    async def authenticate_and_capture(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate via browser and capture all relevant tokens.
        
        Returns:
            Dict containing tokens, cookies, and project info
        """
        self.logger.info("=== FIREBASE TOKEN CAPTURE AUTHENTICATION ===")
        self.logger.info(f"Email: {email}")
        
        try:
            # Start visible browser for authentication
            browser = await uc.start(
                headless=False,
                no_sandbox=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--window-size=1280,720'
                ]
            )
            
            # Navigate to Firebase Console
            self.logger.info("Navigating to Firebase Console...")
            tab = await browser.get("https://console.firebase.google.com")
            await asyncio.sleep(3)
            
            # Perform authentication (using existing logic)
            success = await self._perform_authentication(tab, email, password)
            if not success:
                return {'success': False, 'error': 'Authentication failed'}
            
            # Wait for full authentication completion
            await asyncio.sleep(5)
            
            # Capture authentication tokens
            tokens = await self._capture_tokens(tab)
            
            # Capture cookies
            cookies = await self._capture_cookies(tab)
            
            # Get project information
            project_info = await self._get_project_info(tab)
            
            await browser.stop()
            
            result = {
                'success': True,
                'tokens': tokens,
                'cookies': cookies,
                'project_info': project_info,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info("✅ Token capture completed successfully!")
            self.logger.info(f"📋 Captured {len(tokens)} tokens and {len(cookies)} cookies")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during token capture: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    async def _perform_authentication(self, tab, email: str, password: str) -> bool:
        """Perform the authentication process."""
        try:
            # Find and fill email field
            email_field = await tab.find('input[type="email"]', timeout=10)
            if not email_field:
                self.logger.error("❌ Email field not found")
                return False
                
            await email_field.click()
            await asyncio.sleep(0.5)
            await email_field.send_keys(email)
            
            # Submit email
            await email_field.send_keys('\n')
            await asyncio.sleep(2)
            
            # Find and fill password field
            password_field = await tab.find('input[type="password"]', timeout=15)
            if not password_field:
                self.logger.error("❌ Password field not found")
                return False
                
            await password_field.click()
            await asyncio.sleep(0.5)
            await password_field.send_keys(password)
            
            # Submit password
            await password_field.send_keys('\n')
            await asyncio.sleep(3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            return False
    
    async def _capture_tokens(self, tab) -> Dict[str, str]:
        """Capture Firebase ID tokens and access tokens."""
        tokens = {}
        
        try:
            # Execute JavaScript to get Firebase tokens
            js_code = """
            (async () => {
                const tokens = {};
                
                // Try to get Firebase ID token
                try {
                    if (window.firebase && window.firebase.auth) {
                        const user = window.firebase.auth().currentUser;
                        if (user) {
                            tokens.firebase_id_token = await user.getIdToken();
                            tokens.firebase_uid = user.uid;
                            tokens.firebase_email = user.email;
                        }
                    }
                } catch (e) {
                    console.log('Firebase auth not available via window.firebase');
                }
                
                // Try to get tokens from localStorage
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (key && (key.includes('firebase') || key.includes('token') || key.includes('auth'))) {
                            const value = localStorage.getItem(key);
                            if (value && value.length > 50) { // Likely a token
                                tokens[`localStorage_${key}`] = value;
                            }
                        }
                    }
                } catch (e) {
                    console.log('Error accessing localStorage');
                }
                
                // Try to get tokens from sessionStorage
                try {
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        if (key && (key.includes('firebase') || key.includes('token') || key.includes('auth'))) {
                            const value = sessionStorage.getItem(key);
                            if (value && value.length > 50) { // Likely a token
                                tokens[`sessionStorage_${key}`] = value;
                            }
                        }
                    }
                } catch (e) {
                    console.log('Error accessing sessionStorage');
                }
                
                return tokens;
            })();
            """
            
            result = await tab.evaluate(js_code)
            if result:
                tokens.update(result)
                self.logger.info(f"📱 Captured {len(tokens)} tokens from browser")
            
        except Exception as e:
            self.logger.error(f"❌ Error capturing tokens: {e}")
        
        return tokens
    
    async def _capture_cookies(self, tab) -> Dict[str, str]:
        """Capture all relevant cookies."""
        cookies = {}
        
        try:
            # Get all cookies for the current domain
            js_code = """
            document.cookie.split(';').reduce((cookies, cookie) => {
                const [name, value] = cookie.trim().split('=');
                if (name && value && (
                    name.includes('session') || 
                    name.includes('auth') || 
                    name.includes('token') ||
                    name.includes('firebase') ||
                    name.includes('google')
                )) {
                    cookies[name] = value;
                }
                return cookies;
            }, {});
            """
            
            result = await tab.evaluate(js_code)
            if result:
                cookies.update(result)
                self.logger.info(f"🍪 Captured {len(cookies)} relevant cookies")
                
        except Exception as e:
            self.logger.error(f"❌ Error capturing cookies: {e}")
            
        return cookies
    
    async def _get_project_info(self, tab) -> Dict[str, str]:
        """Extract project information from the Firebase console."""
        project_info = {}
        
        try:
            # Get current URL to extract project ID
            current_url = tab.url
            self.logger.info(f"Current URL: {current_url}")
            
            # Extract project ID from URL
            if '/project/' in current_url:
                project_id = current_url.split('/project/')[1].split('/')[0]
                project_info['project_id'] = project_id
                self.project_id = project_id
                self.logger.info(f"🔍 Extracted project ID: {project_id}")
            
            # Try to get more project info from the page
            js_code = """
            (() => {
                const info = {};
                
                // Try to find project name in the UI
                const titleElements = document.querySelectorAll('h1, h2, h3, .title, .project-name');
                for (const el of titleElements) {
                    if (el.textContent && el.textContent.trim() && el.textContent.length < 100) {
                        info.possible_project_name = el.textContent.trim();
                        break;
                    }
                }
                
                // Try to get Firebase config from page
                const scripts = document.querySelectorAll('script');
                for (const script of scripts) {
                    if (script.textContent && script.textContent.includes('firebaseConfig')) {
                        const match = script.textContent.match(/firebaseConfig\s*=\s*({[^}]+})/);
                        if (match) {
                            try {
                                info.firebase_config = JSON.parse(match[1]);
                            } catch (e) {
                                // Invalid JSON
                            }
                        }
                    }
                }
                
                return info;
            })();
            """
            
            result = await tab.evaluate(js_code)
            if result:
                project_info.update(result)
                
        except Exception as e:
            self.logger.error(f"❌ Error getting project info: {e}")
            
        return project_info

class FirebaseAPIClient:
    """Use captured tokens to make direct Firebase API calls."""
    
    def __init__(self, tokens: Dict[str, str], project_id: str, logger):
        self.tokens = tokens
        self.project_id = project_id
        self.logger = logger
        self.session = requests.Session()
    
    def get_firebase_id_token(self) -> Optional[str]:
        """Get the Firebase ID token from captured tokens."""
        return self.tokens.get('firebase_id_token')
    
    def list_firebase_projects(self) -> Dict[str, Any]:
        """List available Firebase projects using Management API."""
        try:
            url = "https://firebase.googleapis.com/v1beta1/availableProjects"
            
            # Try different authentication methods
            headers = {}
            if 'firebase_id_token' in self.tokens:
                headers['Authorization'] = f"Bearer {self.tokens['firebase_id_token']}"
            
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                self.logger.info("✅ Successfully called Firebase Management API")
                return response.json()
            else:
                self.logger.error(f"❌ API call failed: {response.status_code} - {response.text}")
                return {'error': f"HTTP {response.status_code}", 'details': response.text}
                
        except Exception as e:
            self.logger.error(f"❌ Error calling Firebase API: {e}")
            return {'error': str(e)}
    
    def get_firestore_documents(self, collection: str) -> Dict[str, Any]:
        """Get documents from Firestore using REST API."""
        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}"
            
            headers = {}
            if 'firebase_id_token' in self.tokens:
                headers['Authorization'] = f"Bearer {self.tokens['firebase_id_token']}"
            
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                self.logger.info(f"✅ Successfully retrieved {collection} documents")
                return response.json()
            else:
                self.logger.error(f"❌ Firestore API call failed: {response.status_code}")
                return {'error': f"HTTP {response.status_code}", 'details': response.text}
                
        except Exception as e:
            self.logger.error(f"❌ Error calling Firestore API: {e}")
            return {'error': str(e)}
    
    def create_firestore_document(self, collection: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a document in Firestore using REST API."""
        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}"
            
            headers = {'Content-Type': 'application/json'}
            if 'firebase_id_token' in self.tokens:
                headers['Authorization'] = f"Bearer {self.tokens['firebase_id_token']}"
            
            # Convert data to Firestore format
            firestore_data = self._convert_to_firestore_format(document_data)
            
            response = self.session.post(url, headers=headers, json=firestore_data)
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Successfully created document in {collection}")
                return response.json()
            else:
                self.logger.error(f"❌ Document creation failed: {response.status_code}")
                return {'error': f"HTTP {response.status_code}", 'details': response.text}
                
        except Exception as e:
            self.logger.error(f"❌ Error creating document: {e}")
            return {'error': str(e)}
    
    def _convert_to_firestore_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python dict to Firestore document format."""
        firestore_fields = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                firestore_fields[key] = {"stringValue": value}
            elif isinstance(value, int):
                firestore_fields[key] = {"integerValue": str(value)}
            elif isinstance(value, float):
                firestore_fields[key] = {"doubleValue": value}
            elif isinstance(value, bool):
                firestore_fields[key] = {"booleanValue": value}
            elif isinstance(value, dict):
                firestore_fields[key] = {"mapValue": {"fields": self._convert_to_firestore_format(value)}}
            else:
                firestore_fields[key] = {"stringValue": str(value)}
        
        return {"fields": firestore_fields}

async def main():
    # Setup logging
    logger, log_file = setup_logging()
    
    # Firebase Console credentials
    email = "jalexwol@fastmail.com"
    password = "Bcg3!t7W9oPVzCVvBdECvey..MsW*K"
    
    logger.info("=== FIREBASE TOKEN CAPTURE AND API DEMO ===")
    logger.info(f"Log file: {log_file}")
    
    try:
        # Step 1: Authenticate and capture tokens
        token_capture = FirebaseTokenCapture(logger)
        result = await token_capture.authenticate_and_capture(email, password)
        
        if not result['success']:
            logger.error(f"❌ Authentication failed: {result.get('error')}")
            return
        
        # Save tokens to file for reuse
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        token_file = f"logs/firebase_tokens_{timestamp}.json"
        with open(token_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"💾 Tokens saved to: {token_file}")
        
        # Step 2: Use tokens for direct API calls
        if result['project_info'].get('project_id'):
            logger.info("🚀 Testing direct API calls...")
            
            api_client = FirebaseAPIClient(
                result['tokens'], 
                result['project_info']['project_id'], 
                logger
            )
            
            # Test Firebase Management API
            projects = api_client.list_firebase_projects()
            if 'error' not in projects:
                logger.info(f"📋 Found {len(projects.get('projectInfo', []))} available projects")
            
            # Test Firestore API (example)
            # documents = api_client.get_firestore_documents('users')
            # logger.info(f"📄 Firestore response: {documents}")
            
            # Create a test document
            test_data = {
                'name': 'Test User',
                'email': email,
                'timestamp': datetime.now().isoformat(),
                'source': 'firebase_token_capture_script'
            }
            # create_result = api_client.create_firestore_document('test_collection', test_data)
            # logger.info(f"📝 Document creation result: {create_result}")
        
        logger.info("✅ Token capture and API testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 