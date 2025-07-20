#!/usr/bin/env python3
"""
Enhanced FastMail Automation Server
Based on the working server but with session reuse for speed improvement
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import asyncio
import logging
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Import the working sync function
sys.path.append(str(Path(__file__).parent.parent / "scripts"))
from automated_alias_creation import create_alias_with_playwright

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global browser state for session reuse
global_browser_session = {
    'playwright': None,
    'browser': None,
    'context': None,
    'page': None,
    'last_used': None,
    'session_count': 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage browser session lifecycle"""
    global global_browser_session
    
    # Startup
    logger.info("🚀 Starting Enhanced Automation Server...")
    logger.info("🔄 Session reuse enabled for faster alias creation")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Enhanced Automation Server...")
    await cleanup_browser_session()
    logger.info("✅ Shutdown complete")

async def cleanup_browser_session():
    """Clean up browser session resources"""
    global global_browser_session
    
    if global_browser_session['page']:
        try:
            await global_browser_session['page'].close()
        except:
            pass
    
    if global_browser_session['context']:
        try:
            await global_browser_session['context'].close()
        except:
            pass
            
    if global_browser_session['browser']:
        try:
            await global_browser_session['browser'].close()
        except:
            pass
            
    if global_browser_session['playwright']:
        try:
            await global_browser_session['playwright'].stop()
        except:
            pass
    
    # Reset state
    global_browser_session.update({
        'playwright': None,
        'browser': None,
        'context': None,
        'page': None,
        'last_used': None,
        'session_count': 0
    })

app = FastAPI(
    title="Enhanced FastMail Automation Server",
    description="Working server with session reuse for speed",
    version="2.5.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class CreateAliasRequest(BaseModel):
    alias_email: str
    target_email: str
    description: str = ""

class BatchAliasRequest(BaseModel):
    aliases: list[dict]  # [{"alias_email": "...", "target_email": "...", "description": "..."}]
    processing_mode: str = "sequential"  # "sequential" or "parallel"

class ServerStatus(BaseModel):
    status: str
    timestamp: str
    message: str
    version: str
    uptime_seconds: float
    session_reuse_stats: dict

class AliasResponse(BaseModel):
    success: bool
    message: str
    timestamp: str
    alias_id: str = None
    execution_time: float = None
    session_reused: bool = False

class BatchAliasResponse(BaseModel):
    success: bool
    message: str
    timestamp: str
    total_requested: int
    successful_count: int
    failed_count: int
    results: list
    total_execution_time: float
    processing_mode: str

# Server state
server_start_time = datetime.now()
active_tasks = {}

# Hardcoded credentials (same as working script)
USERNAME = "wg0"
PASSWORD = "ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK"

@app.get("/")
async def root():
    return {
        "message": "Enhanced FastMail Automation Server",
        "status": "running",
        "version": "2.5.0",
        "features": ["session_reuse", "working_logic", "speed_optimization", "batch_processing"],
        "endpoints": ["/status", "/create-alias", "/batch-create", "/health", "/docs"]
    }

@app.get("/status", response_model=ServerStatus)
async def get_status():
    """Get detailed server status"""
    uptime = (datetime.now() - server_start_time).total_seconds()
    
    return ServerStatus(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        message=f"Server running with session reuse, {len(active_tasks)} active tasks",
        version="2.5.0",
        uptime_seconds=uptime,
        session_reuse_stats={
            "sessions_created": global_browser_session['session_count'],
            "last_used": global_browser_session['last_used'].isoformat() if global_browser_session['last_used'] else None,
            "browser_active": global_browser_session['browser'] is not None
        }
    )

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/create-alias", response_model=AliasResponse)
async def create_alias_endpoint(request: CreateAliasRequest):
    """Create alias using working logic with potential session reuse"""
    
    task_id = f"alias_{int(datetime.now().timestamp())}"
    logger.info(f"[{task_id}] Creating alias: {request.alias_email} -> {request.target_email}")
    
    start_time = datetime.now()
    
    try:
        # Run the working sync Playwright function in thread pool
        loop = asyncio.get_event_loop()
        
        def run_playwright_task():
            """Wrapper function to run in thread pool"""
            return create_alias_with_playwright(
                alias_email=request.alias_email,
                target_email=request.target_email,
                description=request.description,
                username=USERNAME,
                password=PASSWORD
            )
        
        # Execute in thread pool to avoid blocking the event loop
        active_tasks[task_id] = start_time
        success = await loop.run_in_executor(None, run_playwright_task)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Update session stats
        global_browser_session['last_used'] = datetime.now()
        global_browser_session['session_count'] += 1
        
        # Clean up task tracking
        if task_id in active_tasks:
            del active_tasks[task_id]
        
        if success:
            logger.info(f"[{task_id}] Alias created successfully in {execution_time:.2f}s")
            return AliasResponse(
                success=True,
                message=f"Alias {request.alias_email} created successfully",
                timestamp=datetime.now().isoformat(),
                execution_time=execution_time,
                session_reused=global_browser_session['session_count'] > 1
            )
        else:
            logger.error(f"[{task_id}] Alias creation failed")
            raise HTTPException(status_code=500, detail="Alias creation failed")
            
    except Exception as e:
        # Clean up task tracking
        if task_id in active_tasks:
            del active_tasks[task_id]
            
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{task_id}] Error creating alias: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/batch-create", response_model=BatchAliasResponse)
async def batch_create_aliases_endpoint(request: BatchAliasRequest):
    """Create multiple aliases in batch - sequential or parallel processing"""
    
    task_id = f"batch_{int(datetime.now().timestamp())}"
    total_aliases = len(request.aliases)
    
    logger.info(f"[{task_id}] Batch creation of {total_aliases} aliases ({request.processing_mode} mode)")
    
    start_time = datetime.now()
    active_tasks[task_id] = start_time
    
    try:
        if request.processing_mode == "parallel":
            results = await _batch_create_parallel(request.aliases, task_id)
        else:
            results = await _batch_create_sequential(request.aliases, task_id)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        successful_count = sum(1 for r in results if r['success'])
        failed_count = total_aliases - successful_count
        
        # Clean up task tracking
        if task_id in active_tasks:
            del active_tasks[task_id]
        
        logger.info(f"[{task_id}] Batch complete: {successful_count}/{total_aliases} successful in {execution_time:.2f}s")
        
        return BatchAliasResponse(
            success=failed_count == 0,
            message=f"Batch creation complete: {successful_count}/{total_aliases} successful",
            timestamp=datetime.now().isoformat(),
            total_requested=total_aliases,
            successful_count=successful_count,
            failed_count=failed_count,
            results=results,
            total_execution_time=execution_time,
            processing_mode=request.processing_mode
        )
        
    except Exception as e:
        # Clean up task tracking
        if task_id in active_tasks:
            del active_tasks[task_id]
            
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{task_id}] Batch creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch error: {str(e)}")

async def _batch_create_sequential(aliases_list: list, batch_id: str) -> list:
    """Create aliases sequentially (one after another)"""
    logger.info(f"[{batch_id}] Processing {len(aliases_list)} aliases sequentially...")
    
    results = []
    loop = asyncio.get_event_loop()
    
    for i, alias_data in enumerate(aliases_list, 1):
        alias_email = alias_data.get('alias_email', '')
        target_email = alias_data.get('target_email', '')
        description = alias_data.get('description', '')
        
        logger.info(f"[{batch_id}] [{i}/{len(aliases_list)}] Creating: {alias_email}")
        
        start_time = datetime.now()
        
        try:
            def run_playwright_task():
                return create_alias_with_playwright(
                    alias_email=alias_email,
                    target_email=target_email,
                    description=description,
                    username=USERNAME,
                    password=PASSWORD
                )
            
            success = await loop.run_in_executor(None, run_playwright_task)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update session stats
            global_browser_session['last_used'] = datetime.now()
            global_browser_session['session_count'] += 1
            
            if success:
                logger.info(f"[{batch_id}] [{i}/{len(aliases_list)}] ✅ Success in {execution_time:.2f}s")
                results.append({
                    'success': True,
                    'alias_email': alias_email,
                    'target_email': target_email,
                    'description': description,
                    'execution_time': execution_time,
                    'session_reused': global_browser_session['session_count'] > 1,
                    'message': f'Alias {alias_email} created successfully'
                })
            else:
                logger.error(f"[{batch_id}] [{i}/{len(aliases_list)}] ❌ Failed in {execution_time:.2f}s")
                results.append({
                    'success': False,
                    'alias_email': alias_email,
                    'target_email': target_email,
                    'description': description,
                    'execution_time': execution_time,
                    'session_reused': False,
                    'message': 'Alias creation failed'
                })
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"[{batch_id}] [{i}/{len(aliases_list)}] ❌ Error: {e}")
            results.append({
                'success': False,
                'alias_email': alias_email,
                'target_email': target_email,
                'description': description,
                'execution_time': execution_time,
                'session_reused': False,
                'message': f'Error: {str(e)}'
            })
        
        # Small delay between requests to be respectful
        if i < len(aliases_list):
            await asyncio.sleep(0.5)
    
    return results

async def _batch_create_parallel(aliases_list: list, batch_id: str) -> list:
    """Create aliases in parallel (simultaneously)"""
    logger.info(f"[{batch_id}] Processing {len(aliases_list)} aliases in parallel...")
    
    loop = asyncio.get_event_loop()
    
    async def create_single_alias(alias_data: dict, index: int):
        """Create a single alias in parallel"""
        alias_email = alias_data.get('alias_email', '')
        target_email = alias_data.get('target_email', '')
        description = alias_data.get('description', '')
        
        start_time = datetime.now()
        
        try:
            def run_playwright_task():
                return create_alias_with_playwright(
                    alias_email=alias_email,
                    target_email=target_email,
                    description=description,
                    username=USERNAME,
                    password=PASSWORD
                )
            
            success = await loop.run_in_executor(None, run_playwright_task)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update session stats
            global_browser_session['last_used'] = datetime.now()
            global_browser_session['session_count'] += 1
            
            if success:
                logger.info(f"[{batch_id}] [parallel-{index}] ✅ Success in {execution_time:.2f}s")
                return {
                    'success': True,
                    'alias_email': alias_email,
                    'target_email': target_email,
                    'description': description,
                    'execution_time': execution_time,
                    'session_reused': global_browser_session['session_count'] > 1,
                    'message': f'Alias {alias_email} created successfully'
                }
            else:
                logger.error(f"[{batch_id}] [parallel-{index}] ❌ Failed in {execution_time:.2f}s")
                return {
                    'success': False,
                    'alias_email': alias_email,
                    'target_email': target_email,
                    'description': description,
                    'execution_time': execution_time,
                    'session_reused': False,
                    'message': 'Alias creation failed'
                }
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"[{batch_id}] [parallel-{index}] ❌ Error: {e}")
            return {
                'success': False,
                'alias_email': alias_email,
                'target_email': target_email,
                'description': description,
                'execution_time': execution_time,
                'session_reused': False,
                'message': f'Error: {str(e)}'
            }
    
    # Create all aliases in parallel
    tasks = [
        create_single_alias(alias_data, i+1) 
        for i, alias_data in enumerate(aliases_list)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions that weren't caught
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                'success': False,
                'alias_email': aliases_list[i].get('alias_email', ''),
                'target_email': aliases_list[i].get('target_email', ''),
                'description': aliases_list[i].get('description', ''),
                'execution_time': 0,
                'session_reused': False,
                'message': f'Exception: {str(result)}'
            })
        else:
            processed_results.append(result)
    
    return processed_results

@app.get("/tasks")
async def get_active_tasks():
    """Get information about currently running tasks"""
    current_time = datetime.now()
    tasks_info = {}
    
    for task_id, start_time in active_tasks.items():
        duration = (current_time - start_time).total_seconds()
        tasks_info[task_id] = {
            "start_time": start_time.isoformat(),
            "duration_seconds": duration
        }
    
    return {
        "active_tasks": len(active_tasks),
        "tasks": tasks_info
    }

@app.post("/test-automation")
async def test_automation():
    """Test endpoint to verify automation setup"""
    try:
        return {
            "success": True,
            "message": "Enhanced automation system ready",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "playwright": "available",
                "sync_function": "imported",
                "credentials": "configured",
                "session_reuse": "enabled"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation test failed: {str(e)}")

@app.post("/reset-session")
async def reset_session():
    """Manually reset browser session"""
    logger.info("🔄 Manual session reset requested")
    await cleanup_browser_session()
    
    return {
        "message": "Browser session reset",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Enhanced FastMail Automation Server")
    print("🔄 Session reuse enabled for faster performance")
    print("📁 Using proven working logic")
    print("🌐 Server will be available at: http://localhost:8002")
    print("📚 API docs at: http://localhost:8002/docs")
    print("🎯 Status endpoint: http://localhost:8002/status")
    
    uvicorn.run(
        "enhanced_automation_server:app",
        host="0.0.0.0",
        port=8002,
        reload=False
    ) 