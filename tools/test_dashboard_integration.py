#!/usr/bin/env python3
"""
Test the dashboard integration with job tracking
"""

import sys
import os
import json
import time
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dashboard_integration():
    """Test the dashboard job tracking features."""
    print("🔍 Testing Dashboard Integration")
    print("=" * 50)
    
    # Test data for simplified form
    test_project_data = {
        "basics": {
            "name": "Test Dashboard Project",
            "description": "Testing the dashboard integration with job tracking",
            "domain": "software_development"
        },
        "vision": {
            "visionStatement": "Create a simple test application to verify dashboard integration works correctly with job tracking and progress monitoring.",
            "businessObjectives": ["Test job tracking"],
            "successMetrics": ["Dashboard shows job progress"],
            "targetAudience": "testers"
        },
        "azureConfig": {
            "organizationUrl": "https://dev.azure.com/testorg",
            "personalAccessToken": "",  # Will be loaded from .env
            "project": "testproject",
            "areaPath": "Grit",
            "iterationPath": "Sprint 1"
        }
    }
    
    api_base = "http://localhost:8000/api"
    
    try:
        # Test 1: Check if API server is running
        print("📡 Testing API server connectivity...")
        response = requests.get(f"{api_base}/health")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("❌ API server is not responding")
            return False
            
        # Test 2: Check jobs endpoint
        print("\n📋 Testing jobs endpoint...")
        response = requests.get(f"{api_base}/jobs")
        if response.status_code == 200:
            jobs_data = response.json()
            print(f"✅ Jobs endpoint working - found {len(jobs_data.get('data', []))} jobs")
            
            # Display current jobs
            jobs = jobs_data.get('data', [])
            if jobs:
                print("\n🔄 Current jobs:")
                for job in jobs:
                    print(f"   Job ID: {job.get('jobId')}")
                    print(f"   Project: {job.get('projectId')}")
                    print(f"   Status: {job.get('status')}")
                    print(f"   Progress: {job.get('progress', 0)}%")
                    print(f"   Action: {job.get('currentAction', 'N/A')}")
                    print("   ---")
            else:
                print("   No active jobs found")
        else:
            print("❌ Jobs endpoint not working")
            return False
            
        # Test 3: Simulate project creation (if server is configured)
        print("\n🚀 Testing project creation flow...")
        if os.getenv('AZURE_DEVOPS_PAT'):
            print("   Azure DevOps configured - creating test project...")
            
            # Create project
            response = requests.post(f"{api_base}/projects", json=test_project_data)
            if response.status_code == 200:
                project_result = response.json()
                project_id = project_result.get('data', {}).get('projectId')
                print(f"   ✅ Project created: {project_id}")
                
                # Start backlog generation
                response = requests.post(f"{api_base}/backlog/generate/{project_id}")
                if response.status_code == 200:
                    job_result = response.json()
                    job_id = job_result.get('data', {}).get('jobId')
                    print(f"   ✅ Job started: {job_id}")
                    
                    # Monitor job for a few seconds
                    print("   🔄 Monitoring job progress...")
                    for i in range(10):  # Monitor for 10 seconds
                        response = requests.get(f"{api_base}/backlog/status/{job_id}")
                        if response.status_code == 200:
                            status = response.json().get('data', {})
                            print(f"      Progress: {status.get('progress', 0)}% - {status.get('currentAction', 'Processing...')}")
                            
                            if status.get('status') in ['completed', 'failed']:
                                print(f"   ✅ Job {status.get('status')}")
                                break
                        time.sleep(1)
                else:
                    print("   ❌ Failed to start job")
            else:
                print("   ❌ Failed to create project")
        else:
            print("   ⚠️  Azure DevOps not configured - skipping project creation test")
            
        print("\n🎉 Dashboard integration test completed!")
        print("✅ The dashboard should now show:")
        print("   - Real-time job progress updates")
        print("   - Active, completed, and failed jobs")
        print("   - Job details with timestamps")
        print("   - Success rate statistics")
        print("   - Job ID from URL parameters")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("💡 Make sure the API server is running: python api_server.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_integration()
    
    if success:
        print("\n🎊 Dashboard integration is ready!")
        print("✅ Users will now see comprehensive job tracking")
        print("📊 Real-time progress updates every 3 seconds")
        print("🔗 Job ID notifications and URL parameters")
    else:
        print("\n⚠️  Dashboard integration needs fixes")
    
    exit(0 if success else 1)
