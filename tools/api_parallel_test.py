#!/usr/bin/env python3
"""
Test parallel processing via API calls to avoid encoding issues.
"""

import requests
import json
import time
from datetime import datetime

def test_config_via_api():
    """Test configuration through the API."""
    print("=" * 60)
    print("TESTING PARALLEL CONFIGURATION VIA API")
    print("=" * 60)
    
    try:
        # Check API health
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"API Status: {health_data.get('status')}")
            print(f"API Version: {health_data.get('version')}")
            return True
        else:
            print(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"API connection failed: {e}")
        return False

def create_test_project():
    """Create a small test project via API."""
    print("\n" + "=" * 60)
    print("CREATING TEST PROJECT")
    print("=" * 60)
    
    test_project = {
        "basics": {
            "name": "Parallel Test Project",
            "description": "Small project to test parallel processing",
            "domain": "software_development"
        },
        "selectedDomains": [
            {"domain_key": "software_development", "display_name": "Software Development"}
        ],
        "azureConfig": {
            "organizationUrl": "https://dev.azure.com/c4workx",
            "project": "GritLite",
            "areaPath": "GritLite\\Test-Parallel",
            "iterationPath": "GritLite\\Sprint 1"
        },
        "vision": {
            "visionStatement": "Create a simple user authentication system with login, registration, and password reset features to test parallel task generation."
        },
        "limits": {
            "maxEpics": 1,
            "maxFeaturesPerEpic": 1,
            "maxUserStoriesPerFeature": 3,
            "maxTasksPerUserStory": 4
        },
        "includeTestArtifacts": False  # Disable test artifacts for faster processing
    }
    
    try:
        print("Creating project...")
        response = requests.post("http://localhost:8000/api/projects", json=test_project, timeout=30)
        
        if response.status_code == 200:
            project_data = response.json()
            project_id = project_data.get("data", {}).get("projectId")
            print(f"Project created successfully: {project_id}")
            return project_id
        else:
            print(f"Project creation failed: {response.status_code}")
            if response.text:
                print(f"Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"Project creation error: {e}")
        return None

def start_and_monitor_backlog_generation(project_id):
    """Start backlog generation and monitor progress."""
    print("\n" + "=" * 60)
    print("STARTING BACKLOG GENERATION")
    print("=" * 60)
    
    try:
        # Start backlog generation
        print("Starting backlog generation...")
        response = requests.post(f"http://localhost:8000/api/backlog/generate/{project_id}", timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to start backlog generation: {response.status_code}")
            return False
        
        job_data = response.json()
        job_id = job_data.get("data", {}).get("jobId")
        print(f"Job started: {job_id}")
        
        # Monitor progress
        print("\nMonitoring progress...")
        start_time = time.time()
        max_wait = 300  # 5 minutes
        
        while time.time() - start_time < max_wait:
            try:
                status_response = requests.get(f"http://localhost:8000/api/backlog/status/{job_id}", timeout=5)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status", "unknown")
                    progress = status_data.get("progress", 0)
                    current_action = status_data.get("currentAction", "Unknown")
                    
                    elapsed = time.time() - start_time
                    print(f"[{elapsed:6.1f}s] Status: {status:12} Progress: {progress:3}% Action: {current_action}")
                    
                    if status == "completed":
                        print("\nBacklog generation completed successfully!")
                        
                        # Get final project data
                        project_response = requests.get(f"http://localhost:8000/api/projects/{project_id}")
                        if project_response.status_code == 200:
                            final_project = project_response.json()
                            return analyze_project_results(final_project, elapsed)
                        else:
                            print("Could not retrieve final project data")
                            return True
                            
                    elif status == "failed":
                        error = status_data.get("error", "Unknown error")
                        print(f"\nBacklog generation failed: {error}")
                        return False
                    
                    time.sleep(2)  # Check every 2 seconds
                    
                else:
                    print(f"Status check failed: {status_response.status_code}")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"Status check error: {e}")
                time.sleep(5)
        
        print("Timeout waiting for completion")
        return False
        
    except Exception as e:
        print(f"Backlog generation error: {e}")
        return False

def analyze_project_results(project_data, duration):
    """Analyze the results of the backlog generation."""
    print("\n" + "=" * 60)
    print("ANALYZING RESULTS")
    print("=" * 60)
    
    try:
        epics = project_data.get("epics", [])
        total_features = 0
        total_user_stories = 0
        total_tasks = 0
        
        print(f"Generation completed in {duration:.1f} seconds")
        print(f"Found {len(epics)} epics")
        
        for epic in epics:
            features = epic.get("features", [])
            total_features += len(features)
            print(f"  Epic: {epic.get('title', 'Unknown')} ({len(features)} features)")
            
            for feature in features:
                user_stories = feature.get("user_stories", [])
                total_user_stories += len(user_stories)
                print(f"    Feature: {feature.get('title', 'Unknown')} ({len(user_stories)} stories)")
                
                for story in user_stories:
                    tasks = story.get("tasks", [])
                    total_tasks += len(tasks)
                    print(f"      Story: {story.get('title', 'Unknown')} ({len(tasks)} tasks)")
        
        print(f"\nTotals:")
        print(f"  Features: {total_features}")
        print(f"  User Stories: {total_user_stories}")
        print(f"  Tasks: {total_tasks}")
        
        # Analyze performance
        if total_user_stories > 1:
            avg_time_per_story = duration / total_user_stories
            print(f"  Average time per story: {avg_time_per_story:.1f} seconds")
            
            # Rough estimate: if each story took less than 6 seconds on average,
            # parallel processing was likely used (normal would be 8-15 seconds per story)
            if avg_time_per_story < 8:
                print("  ANALYSIS: Fast processing suggests parallel execution was used")
            else:
                print("  ANALYSIS: Slower processing suggests sequential execution")
        
        return total_tasks > 0
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return False

def main():
    """Main test function."""
    print("API-BASED PARALLEL PROCESSING TEST")
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Test API connectivity
    if not test_config_via_api():
        print("ERROR: Cannot connect to API")
        return False
    
    # Create test project
    project_id = create_test_project()
    if not project_id:
        print("ERROR: Could not create test project")
        return False
    
    # Test backlog generation
    success = start_and_monitor_backlog_generation(project_id)
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Parallel processing test completed successfully!")
        print("\nTo verify parallel processing was used:")
        print("1. Check if generation was faster than expected")
        print("2. Review server logs for parallel processing messages")
        print("3. Monitor CPU usage during task generation")
    else:
        print("\n" + "=" * 60)
        print("WARNING: Test completed but with issues")
        print("Check server logs for details")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)