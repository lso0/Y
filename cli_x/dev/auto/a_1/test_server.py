#!/usr/bin/env python3
"""
Quick test script for automation server
"""

import requests
import time
import sys

def test_server(server_url):
    """Test automation server functionality"""
    print(f"🧪 Testing automation server: {server_url}")
    print("=" * 50)
    
    try:
        # Test 1: Server status
        print("1️⃣  Testing server status...")
        response = requests.get(f"{server_url}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server is running (uptime: {data.get('uptime', 0):.0f}s)")
            session = data.get('session', {})
            print(f"   📊 Session: logged_in={session.get('logged_in')}, cookies={session.get('cookies_count')}")
        else:
            print(f"   ❌ Server status failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        return False
    
    try:
        # Test 2: Session health
        print("\n2️⃣  Testing session health...")
        response = requests.get(f"{server_url}/session/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            healthy = data.get('healthy', False)
            print(f"   {'✅' if healthy else '⚠️'} Session healthy: {healthy}")
            details = data.get('details', {})
            print(f"   📋 Details: {details}")
        else:
            print(f"   ❌ Session health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Session health check error: {e}")
    
    try:
        # Test 3: Create test alias
        print("\n3️⃣  Testing alias creation...")
        test_alias = f"test-{int(time.time())}@fastmail.com"
        payload = {
            "alias_email": test_alias,
            "target_email": "wg0@fastmail.com",
            "description": "Automated test alias"
        }
        
        response = requests.post(f"{server_url}/alias/create", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Alias created successfully!")
                print(f"   📧 Alias: {test_alias}")
                print(f"   🆔 ID: {data.get('alias_id')}")
            else:
                print(f"   ❌ Alias creation returned false success")
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_msg)
            except:
                pass
            print(f"   ❌ Alias creation failed: {response.status_code} - {error_msg}")
            
    except Exception as e:
        print(f"   ❌ Alias creation error: {e}")
    
    print("\n🎯 Test complete!")
    return True

if __name__ == "__main__":
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8888"
    test_server(server_url) 