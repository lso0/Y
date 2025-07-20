#!/usr/bin/env python3
"""
Session Monitor
Tracks session health and expiration patterns
"""

import time
import json
import requests
import csv
from datetime import datetime
import argparse

class SessionMonitor:
    def __init__(self, server_url="http://localhost:8888"):
        self.server_url = server_url.rstrip('/')
        self.log_file = "session_monitor.csv"
        
    def check_session(self):
        """Check session status and return metrics"""
        try:
            # Get session health
            health_response = requests.get(f"{self.server_url}/session/health", timeout=10)
            health_data = health_response.json()
            
            # Get server status
            status_response = requests.get(f"{self.server_url}/status", timeout=10)
            status_data = status_response.json()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "server_reachable": True,
                "session_healthy": health_data.get("healthy", False),
                "logged_in": status_data.get("session", {}).get("logged_in", False),
                "session_age": status_data.get("session", {}).get("session_age", 0),
                "cookies_count": status_data.get("session", {}).get("cookies_count", 0),
                "bearer_token_present": status_data.get("session", {}).get("bearer_token_present", False),
                "uptime": status_data.get("uptime", 0),
                "error": None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "server_reachable": False,
                "session_healthy": False,
                "logged_in": False,
                "session_age": 0,
                "cookies_count": 0,
                "bearer_token_present": False,
                "uptime": 0,
                "error": str(e)
            }
            
    def log_session_data(self, data):
        """Log session data to CSV file"""
        file_exists = False
        try:
            with open(self.log_file, 'r'):
                file_exists = True
        except FileNotFoundError:
            pass
            
        with open(self.log_file, 'a', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'server_reachable', 'session_healthy', 'logged_in',
                'session_age', 'cookies_count', 'bearer_token_present', 'uptime', 'error'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(data)
            
    def print_status(self, data):
        """Print formatted status"""
        timestamp = data['timestamp']
        
        if not data['server_reachable']:
            print(f"❌ [{timestamp}] Server unreachable: {data['error']}")
            return
            
        status_icon = "✅" if data['session_healthy'] else "⚠️"
        session_age_min = data['session_age'] // 60
        uptime_min = data['uptime'] // 60
        
        print(f"{status_icon} [{timestamp}] "
              f"Session: {'Healthy' if data['session_healthy'] else 'Unhealthy'} | "
              f"Age: {session_age_min}m | "
              f"Cookies: {data['cookies_count']} | "
              f"Bearer: {'✓' if data['bearer_token_present'] else '✗'} | "
              f"Uptime: {uptime_min}m")
              
    def analyze_session_patterns(self):
        """Analyze session expiration patterns from log file"""
        try:
            with open(self.log_file, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
                
            if not data:
                print("No session data available for analysis")
                return
                
            print(f"\n📊 Session Analysis ({len(data)} data points)")
            print("=" * 50)
            
            # Find session failures
            failures = [row for row in data if row['session_healthy'] == 'False']
            recoveries = []
            
            prev_healthy = True
            for row in data:
                current_healthy = row['session_healthy'] == 'True'
                if not prev_healthy and current_healthy:
                    recoveries.append(row)
                prev_healthy = current_healthy
                
            print(f"🔴 Session failures: {len(failures)}")
            print(f"🟢 Session recoveries: {len(recoveries)}")
            
            # Analyze session ages at failure
            failure_ages = [int(row['session_age']) for row in failures if row['session_age'].isdigit()]
            if failure_ages:
                avg_failure_age = sum(failure_ages) / len(failure_ages)
                max_failure_age = max(failure_ages)
                min_failure_age = min(failure_ages)
                
                print(f"📈 Session age at failure:")
                print(f"   Average: {avg_failure_age/3600:.1f} hours")
                print(f"   Maximum: {max_failure_age/3600:.1f} hours")
                print(f"   Minimum: {min_failure_age/3600:.1f} hours")
                
            # Recent session health
            recent_data = data[-20:] if len(data) > 20 else data
            healthy_recent = sum(1 for row in recent_data if row['session_healthy'] == 'True')
            health_percentage = (healthy_recent / len(recent_data)) * 100
            
            print(f"🎯 Recent health (last {len(recent_data)} checks): {health_percentage:.1f}%")
            
        except FileNotFoundError:
            print(f"Log file {self.log_file} not found. Run monitoring first.")
        except Exception as e:
            print(f"Analysis error: {e}")
            
    def monitor(self, interval=60, duration=None):
        """Monitor session continuously"""
        print(f"🔍 Starting session monitoring (interval: {interval}s)")
        print(f"📝 Logging to: {self.log_file}")
        print("Press Ctrl+C to stop\n")
        
        start_time = time.time()
        
        try:
            while True:
                data = self.check_session()
                self.log_session_data(data)
                self.print_status(data)
                
                if duration and (time.time() - start_time) >= duration:
                    break
                    
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            
        print(f"\n📊 Run 'python {__file__} --analyze' to view session patterns")

def main():
    parser = argparse.ArgumentParser(description="Session Monitor for Automation Server")
    parser.add_argument("--server", default="http://localhost:8888",
                       help="Server URL (default: http://localhost:8888)")
    parser.add_argument("--interval", type=int, default=60,
                       help="Check interval in seconds (default: 60)")
    parser.add_argument("--duration", type=int,
                       help="Duration to monitor in seconds (default: infinite)")
    parser.add_argument("--analyze", action="store_true",
                       help="Analyze existing session data")
    parser.add_argument("--check", action="store_true",
                       help="Single session check")
    
    args = parser.parse_args()
    
    monitor = SessionMonitor(args.server)
    
    if args.analyze:
        monitor.analyze_session_patterns()
    elif args.check:
        data = monitor.check_session()
        monitor.print_status(data)
    else:
        monitor.monitor(args.interval, args.duration)

if __name__ == "__main__":
    main() 