#!/usr/bin/env python3
"""
Fix job tracking issue by manually adding job to API server's active jobs
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_job_tracking(job_id: str, project_name: str = "AI Generated Project"):
    """Add the job back to the API server's active jobs tracking."""
    
    print(f"🔧 Fixing job tracking for: {job_id}")
    
    # Create job status data
    job_status = {
        "jobId": job_id,
        "projectId": "unknown",  # We don't have the original project ID
        "status": "running",
        "progress": 75,  # Based on the logs, it's in QA stage
        "currentAgent": "qa_lead_agent",
        "currentAction": "Generating test plans and validating QA artifacts",
        "startTime": datetime.now().isoformat(),
        "endTime": None,
        "error": None
    }
    
    try:
        # Add job to API server's active jobs
        response = requests.post(
            "http://localhost:8000/api/jobs/add",
            json=job_status,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully added job {job_id} to active jobs")
            return True
        else:
            print(f"❌ Failed to add job: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error adding job: {e}")
        return False

def check_job_status(job_id: str):
    """Check if the job is now tracked by the API server."""
    try:
        response = requests.get(f"http://localhost:8000/api/backlog/status/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Job {job_id} is now tracked:")
            print(f"   Status: {data['data']['status']}")
            print(f"   Progress: {data['data']['progress']}%")
            print(f"   Current Action: {data['data']['currentAction']}")
            return True
        else:
            print(f"❌ Job {job_id} still not found: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking job status: {e}")
        return False

def main():
    """Main function to fix job tracking."""
    job_id = "job_20250716_231638"
    
    print("🔧 Job Tracking Fix Tool")
    print("=" * 40)
    
    # Check current status
    print("🔍 Checking current job status...")
    if check_job_status(job_id):
        print("✅ Job is already tracked - no fix needed")
        return True
    
    # Try to fix the job tracking
    print("\n🔧 Attempting to fix job tracking...")
    if fix_job_tracking(job_id):
        print("\n🔍 Verifying fix...")
        if check_job_status(job_id):
            print("\n🎉 SUCCESS: Job tracking fixed!")
            print("   - Frontend should now show progress")
            print("   - Server logs should connect")
            print("   - Navigation to My Projects should work")
            return True
        else:
            print("\n❌ Fix applied but job still not tracked")
            return False
    else:
        print("\n❌ Failed to apply fix")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 