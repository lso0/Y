#!/usr/bin/env python3
"""
Debug script for persistent session and optimized alias creator
"""

import asyncio
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent))

try:
    from persistent_session_manager import PersistentSessionManager
    from optimized_alias_creator import OptimizedAliasCreator, create_alias_fast
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_session_and_alias():
    """Test session manager and alias creation directly"""
    
    # Test 1: Create session manager
    print("🔍 Testing session manager...")
    manager = PersistentSessionManager(
        username="wg0",
        password="ZhkEVNW6nyUNFKvbuhQ2f!Csi@!dJK",
        check_interval=60  # Longer interval for testing
    )
    
    try:
        # Start session
        print("🚀 Starting session manager...")
        if await manager.start():
            print("✅ Session manager started successfully!")
            
            # Get session stats
            stats = await manager.get_session_stats()
            print(f"📊 Session stats: {stats}")
            
            # Check if session is ready
            is_ready = await manager.is_session_ready()
            print(f"🔐 Session ready: {is_ready}")
            
            if is_ready:
                # Test 2: Get session data
                print("🔍 Testing session data retrieval...")
                session_data = await manager.get_session_data()
                print(f"🔑 Bearer token: {session_data['bearer_token'][:20]}...")
                print(f"🆔 User ID: {session_data['user_id']}")
                print(f"🍪 Cookies count: {len(session_data['cookies'])}")
                
                # Test 3: Create alias directly
                print("🎯 Testing direct alias creation...")
                creator = OptimizedAliasCreator(manager)
                
                result = await creator.create_alias(
                    alias_email="debugtest001@fastmail.com",
                    target_email="wg0@fastmail.com", 
                    description="Debug test alias"
                )
                
                print(f"📧 Alias creation result: {result}")
                
            else:
                print("❌ Session not ready for testing")
                
        else:
            print("❌ Failed to start session manager")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🛑 Stopping session manager...")
        await manager.stop()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    print("🧪 Debug Script for Persistent Session")
    print("=" * 50)
    asyncio.run(test_session_and_alias()) 