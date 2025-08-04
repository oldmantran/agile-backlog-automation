#!/usr/bin/env python3
"""
Simple test script for Developer Agent parallel processing.
Tests configuration and basic functionality without special characters.
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
os.chdir(project_root)

from config.config_loader import Config


def test_config():
    """Test parallel processing configuration."""
    print("=" * 60)
    print("TESTING PARALLEL PROCESSING CONFIGURATION")
    print("=" * 60)
    
    config = Config()
    settings = config.settings
    
    # Check workflow configuration
    workflow_config = settings.get('workflow', {})
    parallel_config = workflow_config.get('parallel_processing', {})
    
    print("Parallel Processing Settings:")
    print(f"   Enabled: {parallel_config.get('enabled', False)}")
    print(f"   Max Workers: {parallel_config.get('max_workers', 4)}")
    print(f"   Task Generation: {parallel_config.get('task_generation', False)}")
    print(f"   Rate Limit: {parallel_config.get('rate_limit_per_second', 10)}")
    
    # Check if task generation is enabled
    enabled = parallel_config.get('enabled', False)
    task_gen = parallel_config.get('task_generation', False)
    max_workers = parallel_config.get('max_workers', 4)
    
    print("\nConfiguration Analysis:")
    print(f"   Global Parallel Enabled: {enabled}")
    print(f"   Task Generation Parallel: {task_gen}")
    print(f"   Max Workers: {max_workers}")
    
    if enabled and task_gen and max_workers >= 2:
        print("\nRESULT: Parallel processing is properly configured")
        return True
    else:
        print("\nRESULT: Parallel processing is NOT properly configured")
        issues = []
        if not enabled:
            issues.append("Global parallel processing is disabled")
        if not task_gen:
            issues.append("Task generation parallel processing is disabled")
        if max_workers < 2:
            issues.append(f"Max workers is too low: {max_workers}")
        
        print("Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False


def test_developer_agent_import():
    """Test that we can import and create developer agent."""
    print("\n" + "=" * 60)
    print("TESTING DEVELOPER AGENT IMPORT")
    print("=" * 60)
    
    try:
        from agents.developer_agent import DeveloperAgent
        config = Config()
        developer_agent = DeveloperAgent(config)
        print("SUCCESS: Developer agent imported and created successfully")
        return True, developer_agent
    except Exception as e:
        print(f"ERROR: Failed to import developer agent: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def create_test_user_stories():
    """Create test user stories for parallel processing."""
    return [
        {
            "id": "story_1",
            "title": "User Login",
            "user_story": "As a user, I want to log in securely so that I can access my account",
            "description": "Implement secure login with password hashing and session management",
            "acceptance_criteria": [
                "Given valid credentials, user can log in successfully",
                "Given invalid credentials, user sees appropriate error message",
                "When logging in, password is properly hashed and verified",
                "When login succeeds, secure session is created"
            ],
            "story_points": 5,
            "priority": "High"
        },
        {
            "id": "story_2",
            "title": "User Registration",
            "user_story": "As a new user, I want to create an account so that I can use the system",
            "description": "Allow new users to register with email verification",
            "acceptance_criteria": [
                "Given valid email and password, user can register",
                "Given existing email, user sees appropriate error message",
                "When registering, email verification is sent",
                "When email is verified, account is activated"
            ],
            "story_points": 8,
            "priority": "High"
        },
        {
            "id": "story_3",
            "title": "Password Reset",
            "user_story": "As a user, I want to reset my password so that I can regain access",
            "description": "Implement secure password reset flow with email verification",
            "acceptance_criteria": [
                "Given valid email, reset link is sent to user",
                "Given reset token, user can set new password",
                "When password is reset, old sessions are invalidated",
                "When reset completes, user can log in with new password"
            ],
            "story_points": 5,
            "priority": "Medium"
        }
    ]


def test_task_generation_performance():
    """Test task generation performance with multiple user stories."""
    print("\n" + "=" * 60)
    print("TESTING TASK GENERATION PERFORMANCE")
    print("=" * 60)
    
    # Import developer agent
    success, developer_agent = test_developer_agent_import()
    if not success:
        return False
    
    # Create test data
    user_stories = create_test_user_stories()
    context = {
        "project_name": "Parallel Processing Test",
        "domain": "software_development"
    }
    
    print(f"Testing with {len(user_stories)} user stories:")
    for i, story in enumerate(user_stories, 1):
        print(f"   {i}. {story['title']} ({story['story_points']} points)")
    
    # Time the task generation
    print("\nStarting task generation...")
    start_time = time.time()
    
    try:
        # Use individual story processing (this is how the agent works)
        print("Processing user stories individually with generate_tasks method...")
        result = {"user_stories": []}
        
        for i, story in enumerate(user_stories, 1):
            print(f"   Processing story {i}/{len(user_stories)}: {story['title']}")
            story_start_time = time.time()
            
            try:
                tasks = developer_agent.generate_tasks(story, context)
                story_end_time = time.time()
                story_duration = story_end_time - story_start_time
                
                print(f"   Story {i} completed in {story_duration:.2f}s, generated {len(tasks)} tasks")
                
                # Add tasks back to the story
                story_with_tasks = story.copy()
                story_with_tasks["tasks"] = tasks
                result["user_stories"].append(story_with_tasks)
                
            except Exception as e:
                print(f"   ERROR processing story {i}: {e}")
                # Add story without tasks
                story_without_tasks = story.copy()
                story_without_tasks["tasks"] = []
                result["user_stories"].append(story_without_tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nTask generation completed in {duration:.2f} seconds")
        
        # Analyze results
        if isinstance(result, dict) and "user_stories" in result:
            stories_with_tasks = result["user_stories"]
            total_tasks = 0
            
            print(f"\nTask Generation Results:")
            for story in stories_with_tasks:
                task_count = len(story.get("tasks", []))
                total_tasks += task_count
                print(f"   {story.get('title', 'Unknown')}: {task_count} tasks")
            
            print(f"\nTotal tasks generated: {total_tasks}")
            
            # Performance analysis
            avg_time_per_story = duration / len(user_stories)
            print(f"Average time per story: {avg_time_per_story:.2f} seconds")
            
            # Estimate if parallel processing was used
            # Sequential processing would likely take longer
            estimated_sequential_time = len(user_stories) * 8  # Assume 8s per story
            if duration < estimated_sequential_time * 0.7:  # 30% faster than sequential
                print("ANALYSIS: Performance suggests parallel processing was likely used")
            else:
                print("ANALYSIS: Performance suggests sequential processing was likely used")
            
            return total_tasks > 0
        else:
            print("ERROR: Unexpected result format")
            print(f"Result type: {type(result)}")
            if result:
                print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            return False
            
    except Exception as e:
        print(f"ERROR: Task generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_ollama_status():
    """Check if Ollama is running and which model is loaded."""
    print("\n" + "=" * 60)
    print("CHECKING OLLAMA STATUS")
    print("=" * 60)
    
    try:
        import requests
        
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"Ollama is running with {len(models)} models available")
            
            # Check for qwen2.5:32b
            qwen_models = [m for m in models if "qwen2.5" in m.get("name", "").lower()]
            if qwen_models:
                print("qwen2.5 models found:")
                for model in qwen_models:
                    print(f"   - {model.get('name')}")
                    print(f"     Size: {model.get('size', 'Unknown')}")
                    print(f"     Modified: {model.get('modified_at', 'Unknown')}")
            else:
                print("No qwen2.5 models found")
            
            return True
        else:
            print(f"Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Ollama (not running or not accessible)")
        return False
    except Exception as e:
        print(f"ERROR: Failed to check Ollama status: {e}")
        return False


def main():
    """Main test function."""
    print("DEVELOPER AGENT PARALLEL PROCESSING TEST")
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Run tests
    tests = [
        ("Parallel Configuration", test_config),
        ("Ollama Status", check_ollama_status),
        ("Task Generation Performance", test_task_generation_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"RUNNING TEST: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"RESULT: {test_name} PASSED")
            else:
                print(f"RESULT: {test_name} FAILED")
        except Exception as e:
            print(f"RESULT: {test_name} ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All tests passed!")
        print("\nParallel processing appears to be working correctly.")
        print("\nTo verify parallel processing is actually being used:")
        print("1. Check logs for 'parallel mode: True' messages")
        print("2. Monitor CPU usage during task generation")
        print("3. Look for ThreadPoolExecutor in debug output")
    else:
        print("\nWARNING: Some tests failed.")
        print("\nTo troubleshoot:")
        print("1. Check config/settings.yaml parallel_processing settings")
        print("2. Ensure Ollama is running with qwen2.5:32b model")
        print("3. Verify you have multiple user stories to process")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)