#!/usr/bin/env python3
"""
Quick script to check the status of a running backlog generation job
"""

import requests
import json
import sys

def check_job_status(job_id):
    """Check the status of a specific job"""
    
    api_base_url = "http://localhost:8000/api"
    
    try:
        # Check job status
        response = requests.get(f"{api_base_url}/backlog/status/{job_id}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                status_data = result.get('data', {})
                
                print(f"📊 Job Status for: {job_id}")
                print("=" * 50)
                print(f"Status: {status_data.get('status', 'Unknown')}")
                print(f"Progress: {status_data.get('progress', 0)}%")
                print(f"Current Agent: {status_data.get('currentAgent', 'Unknown')}")
                print(f"Current Action: {status_data.get('currentAction', 'Unknown')}")
                print(f"Start Time: {status_data.get('startTime', 'Unknown')}")
                
                if status_data.get('error'):
                    print(f"❌ Error: {status_data.get('error')}")
                
                # Show recent messages if available
                messages = status_data.get('messages', [])
                if messages:
                    print(f"\n📝 Recent Messages:")
                    for msg in messages[-5:]:  # Show last 5 messages
                        print(f"   • {msg}")
                
                return status_data
            else:
                print(f"❌ API returned error: {result.get('message', 'Unknown error')}")
                return None
        elif response.status_code == 404:
            print(f"❌ Job {job_id} not found")
            return None
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server at http://localhost:8000")
        print("Make sure the backend server is running with: python api_server.py")
        return None
    except Exception as e:
        print(f"❌ Error checking job status: {e}")
        return None

if __name__ == "__main__":
    job_id = "job_20250713_225753"
    
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
    
    print(f"🔍 Checking status for job: {job_id}")
    print()
    
    status = check_job_status(job_id)
    
    if status:
        if status.get('status') == 'completed':
            print(f"\n🎉 Job completed successfully!")
        elif status.get('status') == 'failed':
            print(f"\n💥 Job failed")
        elif status.get('status') in ['queued', 'running']:
            print(f"\n⏳ Job is still {status.get('status')}...")
        
        # Check if we should check Azure DevOps
        if status.get('status') == 'completed':
            print(f"\n💡 Check your Azure DevOps project for the generated work items!")
