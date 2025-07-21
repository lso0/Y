#!/usr/bin/env python3
"""
YouTube Automation Server
FastAPI server for YouTube sign-in and channel management automation with Infisical integration
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add the scripts directory to the path to import our automation
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

try:
    from youtube_auth import automate_youtube_signin_and_subscribe, YouTubeAutomator
except ImportError as e:
    print(f"❌ Failed to import YouTube automation: {e}")
    print("Make sure you're running from the correct directory and dependencies are installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="YouTube Automation Server",
    description="Secure YouTube authentication and channel management automation with Infisical",
    version="1.0.0"
)

# Pydantic models for API requests
class YouTubeSignInRequest(BaseModel):
    signin_url: Optional[str] = Field(None, description="Custom Google sign-in URL (optional)")
    channel_url: Optional[str] = Field(None, description="YouTube channel URL to subscribe to")
    headless: bool = Field(True, description="Run browser in headless mode")
    email: Optional[str] = Field(None, description="YouTube/Google email (optional, uses env if not provided)")
    password: Optional[str] = Field(None, description="YouTube/Google password (optional, uses env if not provided)")

class YouTubeSubscribeRequest(BaseModel):
    channel_url: str = Field(..., description="YouTube channel URL to subscribe to")
    headless: bool = Field(True, description="Run browser in headless mode")

class YouTubeWorkflowRequest(BaseModel):
    channel_url: str = Field(..., description="YouTube channel URL to subscribe to")
    signin_url: Optional[str] = Field(None, description="Custom Google sign-in URL (optional)")
    headless: bool = Field(True, description="Run browser in headless mode")
    email: Optional[str] = Field(None, description="YouTube/Google email (optional, uses env if not provided)")
    password: Optional[str] = Field(None, description="YouTube/Google password (optional, uses env if not provided)")

class YouTubeOperationResponse(BaseModel):
    success: bool
    signed_in: bool = False
    subscribed: bool = False
    channel_info: Dict[str, Any] = {}
    error: Optional[str] = None
    timestamp: str
    execution_time: Optional[float] = None

# Global variables for session management
active_sessions: Dict[str, Dict] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    logger.info("🎥 YouTube Automation Server starting...")
    
    # Check for Infisical credentials (primary) and fallbacks
    yt_email = os.getenv('G_LSD_M_0') or os.getenv('YT_EMAIL')
    yt_password = os.getenv('G_LSD_P_0') or os.getenv('YT_PASSWORD')
    
    if not yt_email or not yt_password:
        logger.warning("⚠️ YouTube credentials not found in environment variables")
        logger.info("Expected: G_LSD_M_0, G_LSD_P_0 (Infisical) or YT_EMAIL, YT_PASSWORD (fallback)")
    else:
        credential_source = "Infisical" if os.getenv('G_LSD_M_0') else "Environment"
        logger.info(f"✅ Credentials loaded from {credential_source} for: {yt_email[:3]}***@{yt_email.split('@')[1]}")
    
    logger.info("✅ YouTube Automation Server ready!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "YouTube Automation Server",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "signin": "/signin",
            "subscribe": "/subscribe",
            "workflow": "/workflow"
        },
        "credentials": {
            "infisical_vars": ["G_LSD_M_0", "G_LSD_P_0"],
            "fallback_vars": ["YT_EMAIL", "YT_PASSWORD"]
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check if credentials are available
    yt_email = os.getenv('G_LSD_M_0') or os.getenv('YT_EMAIL')
    yt_password = os.getenv('G_LSD_P_0') or os.getenv('YT_PASSWORD')
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions),
        "credentials_available": bool(yt_email and yt_password),
        "credential_source": "infisical" if os.getenv('G_LSD_M_0') else "environment" if yt_email else "none"
    }

@app.post("/signin", response_model=YouTubeOperationResponse)
async def youtube_signin(request: YouTubeSignInRequest, background_tasks: BackgroundTasks):
    """Perform YouTube/Google sign-in"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info(f"🔐 Starting YouTube sign-in...")
        
        # Set up environment variables if provided (temporary override)
        original_email = os.getenv('G_LSD_M_0')
        original_password = os.getenv('G_LSD_P_0')
        
        if request.email:
            os.environ['G_LSD_M_0'] = request.email
        if request.password:
            os.environ['G_LSD_P_0'] = request.password
        
        # Create automator instance
        automator = YouTubeAutomator(headless=request.headless)
        
        # Perform sign-in
        success = False
        error = None
        
        try:
            if await automator.start_browser():
                if await automator.navigate_to_youtube_signin(request.signin_url):
                    if await automator.perform_google_signin():
                        success = True
                        logger.info("✅ YouTube sign-in successful")
                    else:
                        error = "Failed to complete sign-in process"
                else:
                    error = "Failed to navigate to sign-in page"
            else:
                error = "Failed to start browser"
        except Exception as e:
            error = str(e)
            logger.error(f"❌ Sign-in error: {e}")
        finally:
            await automator.close_browser()
            
            # Restore original environment variables
            if original_email:
                os.environ['G_LSD_M_0'] = original_email
            elif 'G_LSD_M_0' in os.environ:
                del os.environ['G_LSD_M_0']
                
            if original_password:
                os.environ['G_LSD_P_0'] = original_password
            elif 'G_LSD_P_0' in os.environ:
                del os.environ['G_LSD_P_0']
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return YouTubeOperationResponse(
            success=success,
            signed_in=success,
            error=error,
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ Sign-in endpoint error: {e}")
        
        return YouTubeOperationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time
        )

@app.post("/subscribe", response_model=YouTubeOperationResponse)
async def youtube_subscribe(request: YouTubeSubscribeRequest, background_tasks: BackgroundTasks):
    """Subscribe to a YouTube channel (requires existing authentication)"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info(f"👤 Starting channel subscription: {request.channel_url}")
        
        # For this endpoint, we assume user is already signed in
        # and we just need to navigate and subscribe
        automator = YouTubeAutomator(headless=request.headless)
        
        success = False
        subscribed = False
        channel_info = {}
        error = None
        
        try:
            if await automator.start_browser():
                if await automator.navigate_to_channel(request.channel_url):
                    channel_info = await automator.get_channel_info()
                    if await automator.subscribe_to_channel():
                        subscribed = True
                        success = True
                        logger.info("✅ Channel subscription successful")
                    else:
                        success = True  # Navigation worked, just already subscribed
                        logger.info("ℹ️ Channel subscription skipped (already subscribed)")
                else:
                    error = "Failed to navigate to channel"
            else:
                error = "Failed to start browser"
        except Exception as e:
            error = str(e)
            logger.error(f"❌ Subscription error: {e}")
        finally:
            await automator.close_browser()
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return YouTubeOperationResponse(
            success=success,
            subscribed=subscribed,
            channel_info=channel_info,
            error=error,
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ Subscribe endpoint error: {e}")
        
        return YouTubeOperationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time
        )

@app.post("/workflow", response_model=YouTubeOperationResponse)
async def youtube_workflow(request: YouTubeWorkflowRequest, background_tasks: BackgroundTasks):
    """Complete workflow: Sign in to YouTube and subscribe to a channel"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info(f"🎥 Starting complete YouTube automation workflow...")
        logger.info(f"📺 Channel URL: {request.channel_url}")
        if request.signin_url:
            logger.info(f"🔗 Custom sign-in URL provided")
        
        # Set up environment variables if provided (temporary override)
        original_email = os.getenv('G_LSD_M_0')
        original_password = os.getenv('G_LSD_P_0')
        
        if request.email:
            os.environ['G_LSD_M_0'] = request.email
        if request.password:
            os.environ['G_LSD_P_0'] = request.password
        
        try:
            # Use the main automation function
            result = await automate_youtube_signin_and_subscribe(
                channel_url=request.channel_url,
                signin_url=request.signin_url,
                headless=request.headless
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✅ Complete workflow finished in {execution_time:.2f}s")
            
            return YouTubeOperationResponse(
                success=result['success'],
                signed_in=result['signed_in'],
                subscribed=result['subscribed'],
                channel_info=result['channel_info'],
                error=result['error'],
                timestamp=datetime.now().isoformat(),
                execution_time=execution_time
            )
        finally:
            # Restore original environment variables
            if original_email:
                os.environ['G_LSD_M_0'] = original_email
            elif 'G_LSD_M_0' in os.environ:
                del os.environ['G_LSD_M_0']
                
            if original_password:
                os.environ['G_LSD_P_0'] = original_password
            elif 'G_LSD_P_0' in os.environ:
                del os.environ['G_LSD_P_0']
        
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ Complete workflow error: {e}")
        
        return YouTubeOperationResponse(
            success=False,
            error=str(e),
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8003"))  # Different port from FastMail (8002)
    
    logger.info(f"🚀 Starting YouTube Automation Server on {host}:{port}")
    
    uvicorn.run(
        "youtube_automation_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    ) 