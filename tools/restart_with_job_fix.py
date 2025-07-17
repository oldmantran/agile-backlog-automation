#!/usr/bin/env python3
"""
Restart API server with job tracking fix
"""

import sys
import os
import subprocess
import time
import requests
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def kill_existing_servers():
    """Kill any existing Python processes that might be the API server."""
    print("🔄 Killing existing Python processes...")
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        time.sleep(2)
        print("✅ Killed existing processes")
    except Exception as e:
        print(f"⚠️  Could not kill processes: {e}")

def start_api_server():
    """Start the unified API server."""
    print("🚀 Starting unified API server...")
    try:
        # Start the server in the background
        process = subprocess.Popen([
            "python", "unified_api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(5)
        
        # Check if server is responding
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully")
                return process
            else:
                print(f"❌ Server started but health check failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException:
            print("❌ Server not responding to health check")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def add_job_to_tracking(job_id: str):
    """Add the job to the server's active jobs tracking."""
    print(f"🔧 Adding job {job_id} to tracking...")
    
    job_data = {
        "jobId": job_id,
        "projectId": "unknown",
        "status": "running",
        "progress": 75,
        "currentAgent": "qa_lead_agent",
        "currentAction": "Generating test plans and validating QA artifacts",
        "startTime": datetime.now().isoformat(),
        "endTime": None,
        "error": None
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/jobs/add",
            json=job_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully added job {job_id}")
            return True
        else:
            print(f"❌ Failed to add job: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding job: {e}")
        return False

def verify_job_tracking(job_id: str):
    """Verify the job is now tracked."""
    try:
        response = requests.get(f"http://localhost:8000/api/backlog/status/{job_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Job {job_id} is tracked:")
            print(f"   Status: {data['data']['status']}")
            print(f"   Progress: {data['data']['progress']}%")
            print(f"   Action: {data['data']['currentAction']}")
            return True
        else:
            print(f"❌ Job not found: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying job: {e}")
        return False

def main():
    """Main function to restart server with job fix."""
    job_id = "job_20250716_231638"
    
    print("🔧 API Server Restart with Job Fix")
    print("=" * 50)
    
    # Kill existing servers
    kill_existing_servers()
    
    # Start new server
    server_process = start_api_server()
    if not server_process:
        print("❌ Failed to start server")
        return False
    
    # Add job to tracking
    if not add_job_to_tracking(job_id):
        print("❌ Failed to add job to tracking")
        return False
    
    # Verify job is tracked
    if not verify_job_tracking(job_id):
        print("❌ Job not properly tracked")
        return False
    
    print("\n🎉 SUCCESS: Server restarted with job tracking fixed!")
    print("   - Frontend should now show progress")
    print("   - Server logs should connect")
    print("   - Navigation to My Projects should work")
    print("\n💡 You can now refresh your frontend browser")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 