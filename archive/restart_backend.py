#!/usr/bin/env python3
"""
Quick script to restart the backend with the new domains API endpoint.
"""

import psutil
import sys
import subprocess
import time

def kill_backend():
    """Kill any existing backend processes."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'unified_api_server.py' in ' '.join(cmdline):
                print(f"Killing backend process: {proc.info['pid']}")
                proc.kill()
                time.sleep(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def start_backend():
    """Start the backend server."""
    print("Starting backend server...")
    subprocess.Popen([sys.executable, 'unified_api_server.py'], 
                    cwd='X:/Programs/agile-backlog-automation')
    time.sleep(3)

if __name__ == "__main__":
    kill_backend()
    start_backend()
    print("Backend restarted. Testing domains API...")
    
    import requests
    try:
        response = requests.get('http://localhost:8000/api/domains')
        if response.status_code == 200:
            domains = response.json()
            print(f"✅ Domains API working! Found {len(domains)} domains")
            for domain in domains[:3]:
                print(f"  - {domain['display_name']} ({domain['domain_key']})")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing API: {e}")