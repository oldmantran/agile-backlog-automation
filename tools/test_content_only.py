#!/usr/bin/env python3
"""
Create a test job focused on content generation only (no Azure integration)
"""

import sys
import os
import requests
import time
from datetime import datetime

def create_content_only_test_job():
    """Create a test job that focuses on content generation without Azure integration."""
    print("🧪 Creating Content-Only Test Job")
    print("=" * 40)
    
    # Simple test project data with NO Azure config to skip integration
    test_project_data = {
        "basics": {
            "name": "Simple Todo Test App",
            "description": "Basic todo application for testing content generation",
            "domain": "software_development"
        },
        "vision": {
            "visionStatement": "Create a simple todo app where users can add, edit, and delete tasks. Basic functionality only.",
            "businessObjectives": ["Enable task creation", "Enable task editing", "Enable task deletion"],
            "successMetrics": ["User can add tasks", "User can edit tasks", "User can delete tasks"],
            "targetAudience": "individual users"
        }
        # Note: No azureConfig section at all to ensure content-only mode
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
        print("🚀 Starting content generation (no Azure upload)...")
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
        
        print(f"✅ Content generation started: {job_id}")
        print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        
        return project_id, job_id
        
    except Exception as e:
        print(f"❌ Error creating test job: {e}")
        return None, None

def monitor_content_test_job(job_id, timeout_minutes=10):
    """Monitor the content generation test job."""
    print(f"\n🔍 Monitoring Content Test Job: {job_id}")
    print(f"⏰ Timeout: {timeout_minutes} minutes")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    start_time = datetime.now()
    last_progress = -1
    progress_updates = []
    
    while True:
        try:
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            
            # Check timeout
            if elapsed > timeout_minutes:
                print(f"\n⏰ TIMEOUT after {timeout_minutes} minutes")
                print("❌ Test job took too long - likely stalled")
                print(f"📊 Last progress: {last_progress}%")
                print(f"📈 Progress updates: {len(progress_updates)}")
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
            
            # Track progress changes
            if progress != last_progress:
                progress_updates.append({
                    'time': datetime.now(),
                    'progress': progress,
                    'agent': current_agent,
                    'action': current_action
                })
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                runtime_mins = elapsed
                
                print(f"\n📅 {timestamp} ({runtime_mins:.1f}m)")
                print(f"📊 Progress: {progress}%")
                print(f"🤖 Agent: {current_agent}")
                print(f"⚡ Action: {current_action}")
                print(f"🔄 Status: {status}")
                
                last_progress = progress
            
            # Check for stall (no progress for 3 minutes)
            if len(progress_updates) >= 2:
                last_update = progress_updates[-1]['time']
                if (datetime.now() - last_update).total_seconds() > 180:
                    print(f"\n🚨 STALL DETECTED!")
                    print(f"⏰ No progress for 3+ minutes")
                    print(f"📊 Stuck at: {progress}%")
                    print(f"🤖 Agent: {current_agent}")
                    print(f"⚡ Action: {current_action}")
                    return False
            
            # Check for errors
            if error:
                print(f"\n❌ JOB ERROR: {error}")
                return False
            
            # Check completion
            if status == 'completed':
                runtime = (datetime.now() - start_time).total_seconds() / 60
                print(f"\n🎉 CONTENT GENERATION COMPLETED!")
                print(f"⏱️ Total Runtime: {runtime:.1f} minutes")
                print(f"📊 Final Progress: {progress}%")
                print(f"📈 Total progress updates: {len(progress_updates)}")
                return True
            
            elif status == 'failed':
                runtime = (datetime.now() - start_time).total_seconds() / 60
                print(f"\n❌ CONTENT GENERATION FAILED")
                print(f"⏱️ Runtime: {runtime:.1f} minutes")
                print(f"📊 Progress at failure: {progress}%")
                if error:
                    print(f"🔍 Error: {error}")
                return False
            
            time.sleep(5)  # Check every 5 seconds for faster stall detection
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            return False

def main():
    """Run the content generation test."""
    print("🧠 CONTENT GENERATION TEST")
    print("Testing AI content generation without Azure upload")
    print("=" * 55)
    
    # Create test job
    project_id, job_id = create_content_only_test_job()
    
    if not job_id:
        print("❌ Failed to create test job")
        return False
    
    # Monitor with 10-minute timeout and stall detection
    success = monitor_content_test_job(job_id, timeout_minutes=10)
    
    print("\n" + "=" * 55)
    if success:
        print("🎊 CONTENT GENERATION TEST: SUCCESS!")
        print("✅ AI content generation is working properly")
        print("✅ No stall detected in content generation phase")
    else:
        print("⚠️ CONTENT GENERATION TEST: FAILED")
        print("❌ Issue found in content generation phase")
        print("🔧 Need to debug content generation agents")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
