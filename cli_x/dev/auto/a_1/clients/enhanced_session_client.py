#!/usr/bin/env python3
"""
Enhanced Session Client
Client for the enhanced automation server with session reuse
"""

import requests
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any

class EnhancedSessionClient:
    def __init__(self, server_url: str = "http://100.124.55.82:8002", timeout: int = 120):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def get_status(self) -> Dict[str, Any]:
        """Get server status including session reuse stats"""
        try:
            response = self.session.get(f"{self.server_url}/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to get status: {e}"}
    
    def test_automation(self) -> Dict[str, Any]:
        """Test the automation system"""
        try:
            response = self.session.post(f"{self.server_url}/test-automation")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to test automation: {e}"}
    
    def reset_session(self) -> Dict[str, Any]:
        """Reset browser session"""
        try:
            response = self.session.post(f"{self.server_url}/reset-session")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to reset session: {e}"}
    
    def create_alias(self, alias_email: str, target_email: str, description: str = "") -> Dict[str, Any]:
        """Create alias using enhanced server with session reuse"""
        try:
            payload = {
                "alias_email": alias_email,
                "target_email": target_email,
                "description": description
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.server_url}/create-alias", json=payload)
            execution_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            result['client_measured_time'] = execution_time
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to create alias: {e}"}
    
    def batch_create_aliases(self, aliases_list: list, processing_mode: str = "sequential") -> Dict[str, Any]:
        """Create multiple aliases in batch"""
        try:
            payload = {
                "aliases": aliases_list,
                "processing_mode": processing_mode
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.server_url}/batch-create", json=payload)
            execution_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            result['client_measured_time'] = execution_time
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to batch create aliases: {e}"}
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """Get information about active tasks"""
        try:
            response = self.session.get(f"{self.server_url}/tasks")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to get tasks: {e}"}

def display_status(client: EnhancedSessionClient):
    """Display comprehensive server status"""
    print("🔍 Checking enhanced server status...")
    
    # Get status
    status = client.get_status()
    if "error" in status:
        print(f"❌ Status Error: {status['error']}")
        return False
    
    print(f"✅ Server Status: {status['status']}")
    print(f"🕐 Uptime: {status['uptime_seconds']:.0f} seconds")
    print(f"📊 Version: {status['version']}")
    
    # Show session reuse stats
    reuse_stats = status.get('session_reuse_stats', {})
    print(f"🔄 Sessions Created: {reuse_stats.get('sessions_created', 0)}")
    print(f"🌐 Browser Active: {reuse_stats.get('browser_active', False)}")
    if reuse_stats.get('last_used'):
        print(f"⏰ Last Used: {reuse_stats['last_used']}")
    
    return True

def test_automation_system(client: EnhancedSessionClient):
    """Test the automation system"""
    print("\n🧪 Testing enhanced automation system...")
    
    result = client.test_automation()
    if "error" in result:
        print(f"❌ Test failed: {result['error']}")
        return False
    
    print(f"✅ Test Result: {result.get('success', False)}")
    print(f"📝 Message: {result.get('message', 'N/A')}")
    
    dependencies = result.get('dependencies', {})
    if dependencies:
        print("🛠️  Dependencies:")
        for dep, status in dependencies.items():
            print(f"   ✅ {dep}: {status}")
    
    return result.get('success', False)

def create_single_alias(client: EnhancedSessionClient, alias_email: str, target_email: str, description: str = ""):
    """Create a single alias and show timing with session reuse info"""
    print(f"\n📧 Creating alias: {alias_email} -> {target_email}")
    
    start_time = time.time()
    result = client.create_alias(alias_email, target_email, description)
    total_time = time.time() - start_time
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    if result.get('success'):
        print(f"✅ Success!")
        print(f"🎉 Message: {result.get('message', 'N/A')}")
        print(f"⚡ Server Time: {result.get('execution_time', 0):.2f}s")
        print(f"🌐 Total Time: {total_time:.2f}s")
        print(f"🔄 Session Reused: {result.get('session_reused', False)}")
        return True
    else:
        print(f"❌ Failed: {result.get('message', 'Unknown error')}")
        return False

def speed_test(client: EnhancedSessionClient):
    """Perform a speed test to demonstrate session reuse benefits"""
    print("\n🏃‍♂️ Speed Test: Testing session reuse performance...")
    
    # Generate test aliases
    timestamp = int(time.time())
    aliases = []
    for i in range(3):
        aliases.append({
            "alias_email": f"enhanced{timestamp}_{i+1}@fastmail.com",
            "target_email": "wg0@fastmail.com",
            "description": f"Enhanced test {i+1}"
        })
    
    # Create them and track session reuse
    total_start = time.time()
    successful = 0
    times = []
    
    for i, alias in enumerate(aliases, 1):
        print(f"\n⚡ [{i}/3] Creating {alias['alias_email']}")
        
        start = time.time()
        result = client.create_alias(alias['alias_email'], alias['target_email'], alias['description'])
        end = time.time()
        
        if "error" not in result and result.get('success'):
            successful += 1
            execution_time = result.get('execution_time', 0)
            session_reused = result.get('session_reused', False)
            times.append(execution_time)
            
            reuse_indicator = "🔄 (session reused)" if session_reused else "🆕 (new session)"
            print(f"   ✅ Success in {execution_time:.2f}s {reuse_indicator}")
        else:
            print(f"   ❌ Failed")
    
    total_time = time.time() - total_start
    
    print(f"\n🏁 Speed Test Complete!")
    print(f"✅ Successful: {successful}/3")
    print(f"⚡ Total Time: {total_time:.2f}s")
    if times:
        print(f"📊 Average per alias: {sum(times)/len(times):.2f}s")
        print(f"🚀 Fastest: {min(times):.2f}s")
        print(f"🐌 Slowest: {max(times):.2f}s")
    
    if successful == 3:
        print("🎉 Perfect score! Session reuse working!")

def create_batch_aliases(client: EnhancedSessionClient, aliases_list: list, processing_mode: str = "sequential"):
    """Create multiple aliases in batch"""
    print(f"\n📦 Creating {len(aliases_list)} aliases in batch ({processing_mode} mode)...")
    
    for i, alias in enumerate(aliases_list, 1):
        print(f"   {i}. {alias['alias_email']} -> {alias['target_email']}")
    
    start_time = time.time()
    result = client.batch_create_aliases(aliases_list, processing_mode)
    total_time = time.time() - start_time
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"\n🏁 Batch Complete!")
    print(f"📊 Processing Mode: {result.get('processing_mode', 'unknown')}")
    print(f"📋 Total Requested: {result.get('total_requested', 0)}")
    print(f"✅ Successful: {result.get('successful_count', 0)}")
    print(f"❌ Failed: {result.get('failed_count', 0)}")
    print(f"⚡ Server Time: {result.get('total_execution_time', 0):.2f}s")
    print(f"🌐 Total Time: {total_time:.2f}s")
    
    # Show individual results
    results = result.get('results', [])
    if results:
        print("\n📋 Individual Results:")
        for i, res in enumerate(results, 1):
            status = "✅" if res.get('success') else "❌"
            time_taken = res.get('execution_time', 0)
            reused = "🔄" if res.get('session_reused') else "🆕"
            alias_email = res.get('alias_email', 'unknown')
            print(f"   {i}. {status} {alias_email} - {time_taken:.2f}s {reused}")
    
    success_rate = result.get('successful_count', 0) / result.get('total_requested', 1) * 100
    print(f"\n📊 Success Rate: {success_rate:.1f}%")
    
    if result.get('total_requested', 0) > 0:
        avg_time = result.get('total_execution_time', 0) / result.get('total_requested', 1)
        print(f"⚡ Average per alias: {avg_time:.2f}s")
    
    return result.get('successful_count', 0) == result.get('total_requested', 0)

def bulk_test(client: EnhancedSessionClient, count: int = 5, processing_mode: str = "sequential"):
    """Perform a bulk test with multiple aliases"""
    print(f"\n🚀 Bulk Test: Creating {count} aliases using {processing_mode} processing...")
    
    # Generate test aliases
    timestamp = int(time.time())
    aliases = []
    for i in range(count):
        aliases.append({
            "alias_email": f"bulk{processing_mode}{timestamp}_{i+1}@fastmail.com",
            "target_email": "wg0@fastmail.com",
            "description": f"Bulk {processing_mode} test {i+1}"
        })
    
    return create_batch_aliases(client, aliases, processing_mode)

def compare_processing_modes(client: EnhancedSessionClient, count: int = 3):
    """Compare sequential vs parallel processing"""
    print(f"\n🏁 Performance Comparison: {count} aliases each mode")
    print("=" * 60)
    
    # Test sequential processing
    print(f"\n🔄 Testing SEQUENTIAL processing...")
    seq_success = bulk_test(client, count, "sequential")
    
    # Wait a bit between tests
    print(f"\n⏸️  Waiting 5 seconds before parallel test...")
    time.sleep(5)
    
    # Test parallel processing
    print(f"\n⚡ Testing PARALLEL processing...")
    par_success = bulk_test(client, count, "parallel")
    
    print(f"\n🏆 Comparison Results:")
    print(f"   🔄 Sequential: {'✅ Success' if seq_success else '❌ Failed'}")
    print(f"   ⚡ Parallel: {'✅ Success' if par_success else '❌ Failed'}")
    
    if seq_success and par_success:
        print("🎉 Both processing modes working successfully!")
    elif seq_success:
        print("⚠️  Sequential processing more reliable")
    elif par_success:
        print("⚠️  Parallel processing working, sequential had issues")
    else:
        print("❌ Both processing modes had issues")

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("📧 Enhanced Session Client")
        print("=" * 40)
        print("Usage: python enhanced_session_client.py <command> [args...]")
        print()
        print("Single Alias Commands:")
        print("  status                              - Show server status")
        print("  test                               - Test automation system")
        print("  create <alias> <target> [desc]     - Create single alias")
        print("  speedtest                          - Run speed test")
        print()
        print("Batch Commands:")
        print("  batch <alias1,target1> <alias2,target2> ... - Create multiple aliases sequentially")
        print("  batch-parallel <alias1,target1> <alias2,target2> ... - Create multiple aliases in parallel")
        print("  bulk <count> [mode]                - Bulk test (count aliases, mode: sequential/parallel)")
        print("  compare [count]                    - Compare sequential vs parallel processing")
        print()
        print("System Commands:")
        print("  reset                              - Reset browser session")
        print("  tasks                              - Show active tasks")
        print()
        print("Examples:")
        print("  python enhanced_session_client.py status")
        print("  python enhanced_session_client.py create work@fastmail.com wg0@fastmail.com \"Work emails\"")
        print("  python enhanced_session_client.py batch work1@fastmail.com,wg0@fastmail.com work2@fastmail.com,wg0@fastmail.com")
        print("  python enhanced_session_client.py bulk 5 sequential")
        print("  python enhanced_session_client.py compare 3")
        return
    
    client = EnhancedSessionClient()
    command = sys.argv[1].lower()
    
    if command == "status":
        display_status(client)
        
    elif command == "test":
        if display_status(client):
            test_automation_system(client)
        
    elif command == "create":
        if len(sys.argv) < 4:
            print("❌ Usage: create <alias_email> <target_email> [description]")
            return
        
        alias_email = sys.argv[2]
        target_email = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        
        if display_status(client):
            create_single_alias(client, alias_email, target_email, description)
    
    elif command in ["batch", "batch-parallel"]:
        if len(sys.argv) < 3:
            print("❌ Usage: batch <alias1,target1> <alias2,target2> ...")
            print("❌ Usage: batch-parallel <alias1,target1> <alias2,target2> ...")
            return
        
        processing_mode = "parallel" if command == "batch-parallel" else "sequential"
        aliases = []
        
        for arg in sys.argv[2:]:
            if ',' in arg:
                parts = arg.split(',')
                if len(parts) >= 2:
                    aliases.append({
                        "alias_email": parts[0],
                        "target_email": parts[1],
                        "description": parts[2] if len(parts) > 2 else ""
                    })
        
        if aliases and display_status(client):
            create_batch_aliases(client, aliases, processing_mode)
    
    elif command == "bulk":
        count = 5  # default
        mode = "sequential"  # default
        
        if len(sys.argv) > 2:
            try:
                count = int(sys.argv[2])
            except ValueError:
                print("❌ Count must be a number")
                return
        
        if len(sys.argv) > 3:
            mode = sys.argv[3].lower()
            if mode not in ["sequential", "parallel"]:
                print("❌ Mode must be 'sequential' or 'parallel'")
                return
        
        if display_status(client):
            bulk_test(client, count, mode)
    
    elif command == "compare":
        count = 3  # default
        
        if len(sys.argv) > 2:
            try:
                count = int(sys.argv[2])
            except ValueError:
                print("❌ Count must be a number")
                return
        
        if display_status(client):
            compare_processing_modes(client, count)
    
    elif command == "speedtest":
        if display_status(client):
            speed_test(client)
    
    elif command == "reset":
        print("🔄 Resetting browser session...")
        result = client.reset_session()
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ {result.get('message', 'Session reset complete')}")
    
    elif command == "tasks":
        print("📋 Checking active tasks...")
        result = client.get_active_tasks()
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            active_count = result.get('active_tasks', 0)
            print(f"🔄 Active tasks: {active_count}")
            
            tasks = result.get('tasks', {})
            if tasks:
                print("📋 Task Details:")
                for task_id, info in tasks.items():
                    duration = info.get('duration_seconds', 0)
                    print(f"   {task_id}: {duration:.1f}s")
            elif active_count == 0:
                print("✅ No active tasks")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see usage.")

if __name__ == "__main__":
    main() 