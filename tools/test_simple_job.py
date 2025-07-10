#!/usr/bin/env python3
"""
Create a simple test job to validate the system after fixing the stall
"""

import sys
import os
import requests
import time
from datetime import datetime

def create_simple_test_job():
    """Create a simple test job with minimal complexity."""
    print("🧪 Creating Simple Test Job")
    print("=" * 40)
    
    # Simple test project data
    test_project_data = {
        "basics": {
            "name": "Simple Todo Test App",
            "description": "Basic todo application for testing system functionality",
            "domain": "software_development"
        },
        "vision": {
            "visionStatement": "Create a simple todo app where users can add, edit, and delete tasks. Users need basic task management with priority levels. Success measured by task completion rate and user engagement.",
            "businessObjectives": ["Test system functionality"],
            "successMetrics": ["System completes end-to-end"],
            "targetAudience": "test users"
        },
        "azureConfig": {
            "organizationUrl": "https://dev.azure.com/testorg",
            "personalAccessToken": os.getenv("AZURE_DEVOPS_PAT", ""),
            "project": "TestProject",
            "areaPath": "Test Area",
            "iterationPath": "Test Sprint"
        }
    }
    
    base_url = "http://localhost:8000"
    
    try:
        print("📝 Creating test project...")
        
        # Create project
        response = requests.post(f"{base_url}/api/projects", json=test_project_data)
        
        if response.status_code != 200:
            print(f"❌ Failed to create project: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
        
        project_data = response.json()
        project_id = project_data.get('data', {}).get('projectId')
        
        if not project_id:
            print(f"❌ No project ID returned: {project_data}")
            return None, None
        
        print(f"✅ Test project created: {project_id}")
        
        # Start backlog generation
        print("🚀 Starting backlog generation...")
        response = requests.post(f"{base_url}/api/backlog/generate/{project_id}")
        
        if response.status_code != 200:
            print(f"❌ Failed to start backlog generation: {response.status_code}")
            print(f"Response: {response.text}")
            return project_id, None
        
        job_data = response.json()
        job_id = job_data.get('data', {}).get('jobId')
        
        if not job_id:
            print(f"❌ No job ID returned: {job_data}")
            return project_id, None
        
        print(f"✅ Backlog generation started: {job_id}")
        print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        
        return project_id, job_id
        
    except Exception as e:
        print(f"❌ Error creating test job: {e}")
        return None, None

def monitor_test_job(job_id, timeout_minutes=15):
    """Monitor the test job with timeout."""
    print(f"\n🔍 Monitoring Test Job: {job_id}")
    print(f"⏰ Timeout: {timeout_minutes} minutes")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    start_time = datetime.now()
    last_progress = -1
    
    while True:
        try:
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            
            # Check timeout
            if elapsed > timeout_minutes:
                print(f"\n⏰ TIMEOUT after {timeout_minutes} minutes")
                print("❌ Test job took too long - likely stalled again")
                return False
            
            # Get job status
            response = requests.get(f"{base_url}/api/backlog/status/{job_id}")
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                return False
            
            data = response.json()
            job_data = data.get('data', {})
            
            status = job_data.get('status', 'unknown')
            progress = job_data.get('progress', 0)
            current_agent = job_data.get('currentAgent', 'Unknown')
            current_action = job_data.get('currentAction', 'Unknown')
            error = job_data.get('error')
            
            # Show progress updates
            if progress != last_progress or progress % 20 == 0:
                timestamp = datetime.now().strftime('%H:%M:%S')
                runtime_mins = elapsed
                
                print(f"\n📅 {timestamp} ({runtime_mins:.1f}m runtime)")
                print(f"📊 Progress: {progress}%")
                print(f"🤖 Agent: {current_agent}")
                print(f"⚡ Action: {current_action}")
                print(f"🔄 Status: {status}")
                
                last_progress = progress
            
            # Check for errors
            if error:
                print(f"\n❌ JOB ERROR: {error}")
                return False
            
            # Check completion
            if status == 'completed':
                runtime = (datetime.now() - start_time).total_seconds() / 60
                print(f"\n🎉 JOB COMPLETED SUCCESSFULLY!")
                print(f"⏱️ Total Runtime: {runtime:.1f} minutes")
                print(f"📊 Final Progress: {progress}%")
                return True
            
            elif status == 'failed':
                runtime = (datetime.now() - start_time).total_seconds() / 60
                print(f"\n❌ JOB FAILED")
                print(f"⏱️ Runtime: {runtime:.1f} minutes")
                print(f"📊 Progress at failure: {progress}%")
                if error:
                    print(f"🔍 Error: {error}")
                return False
            
            time.sleep(10)  # Check every 10 seconds for faster feedback
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            return False

def main():
    """Run the complete test."""
    print("🚨 SYSTEM VALIDATION TEST")
    print("Testing if the stall issue is resolved")
    print("=" * 50)
    
    # Create test job
    project_id, job_id = create_simple_test_job()
    
    if not job_id:
        print("❌ Failed to create test job")
        return False
    
    # Monitor with 15-minute timeout
    success = monitor_test_job(job_id, timeout_minutes=15)
    
    print("\n" + "=" * 50)
    if success:
        print("🎊 SYSTEM VALIDATION: SUCCESS!")
        print("✅ The stall issue appears to be resolved")
        print("✅ System is ready for your original complex job")
    else:
        print("⚠️ SYSTEM VALIDATION: FAILED")
        print("❌ The system still has issues")
        print("🔧 Need to investigate further")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
