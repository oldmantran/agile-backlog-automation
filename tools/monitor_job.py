#!/usr/bin/env python3
"""
Monitor job progress and provide updates
"""

import sys
import os
import time
import json
import requests
from datetime import datetime, timedelta

def monitor_job(job_id, check_interval_seconds=30):
    """Monitor a specific job and provide status updates."""
    base_url = "http://localhost:8000"
    last_status = None
    last_progress = None
    start_time = datetime.now()
    
    print(f"🔍 Monitoring Job: {job_id}")
    print(f"⏰ Started monitoring at: {start_time.strftime('%H:%M:%S')}")
    print("=" * 60)
    
    while True:
        try:
            # Get job status
            response = requests.get(f"{base_url}/api/backlog/status/{job_id}")
            
            if response.status_code == 200:
                data = response.json()
                job_data = data.get('data', {})
                
                status = job_data.get('status')
                progress = job_data.get('progress', 0)
                current_agent = job_data.get('currentAgent', 'Unknown')
                current_action = job_data.get('currentAction', 'Unknown')
                error = job_data.get('error')
                
                # Check for status or significant progress changes (reduced threshold for better tracking)
                if status != last_status or abs(progress - (last_progress or 0)) >= 5:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    runtime = datetime.now() - start_time
                    
                    print(f"\n📅 {timestamp} (Runtime: {str(runtime).split('.')[0]})")
                    print(f"📊 Progress: {progress}%")
                    print(f"🤖 Agent: {current_agent}")
                    print(f"⚡ Action: {current_action}")
                    print(f"🔄 Status: {status}")
                    
                    if error:
                        print(f"❌ ERROR: {error}")
                        return False
                    
                    last_status = status
                    last_progress = progress
                
                # Check if job is complete
                if status in ['completed', 'failed']:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    runtime = datetime.now() - start_time
                    
                    print(f"\n🏁 JOB COMPLETED at {timestamp}")
                    print(f"⏱️  Total Runtime: {str(runtime).split('.')[0]}")
                    print(f"📊 Final Progress: {progress}%")
                    print(f"🎯 Final Status: {status}")
                    
                    if status == 'failed':
                        print(f"❌ ERROR: {error}")
                        return False
                    else:
                        print("✅ SUCCESS!")
                        return True
                        
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Monitoring Error: {e}")
            
        time.sleep(check_interval_seconds)

if __name__ == "__main__":
    job_id = sys.argv[1] if len(sys.argv) > 1 else "job_20250710_135032"
    monitor_job(job_id, 10)  # Check every 10 seconds for better progress tracking
