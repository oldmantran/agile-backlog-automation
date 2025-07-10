#!/usr/bin/env python3
"""
Toggle between test mode (small quantities) and production mode (normal quantities)
"""

import os
import sys

# Configuration mappings
CONFIGS = {
    "test": {
        "epic_strategist.txt": {
            "search": "Create **exactly 2 epics** that together deliver the complete vision (testing mode)",
            "production": "Create **3-7 epics** that together deliver the complete vision"
        },
        "feature_decomposer_agent.txt": {
            "search": "Create **exactly 2 features** per epic that together fulfill the epic's objectives (testing mode)",
            "production": "Create **4-8 features** per epic that together fulfill the epic's objectives"
        },
        "user_story_decomposer_agent.txt": {
            "search": "Break down features into 2-3 focused user stories following best practices (testing mode)",
            "production": "Break down features into 3-6 focused user stories following best practices"
        },
        "user_story_decomposer.txt": {
            "search": "Create **2-3 user stories** per feature, covering main flows and key edge cases (testing mode)",
            "production": "Create **3–6 user stories** per feature, covering main flows, edge cases, error handling, and different user types"
        },
        "developer_agent.txt": {
            "search": "Create **3 tasks maximum** per user story for fast testing",
            "production": "Create **5-12 tasks** per feature that cover the complete implementation"
        },
        "qa_tester_agent.txt": {
            "search": "Estimated Test Cases**: 3 test cases maximum per story (test mode)",
            "production": "Estimated Test Cases**: 8-15 test cases per story"
        }
    }
}

def toggle_mode(target_mode):
    """Toggle between test and production modes."""
    if target_mode not in ["test", "production"]:
        print("❌ Invalid mode. Use 'test' or 'production'")
        return False
    
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
    
    if target_mode == "production":
        # Switch from test to production
        for filename, config in CONFIGS["test"].items():
            file_path = os.path.join(prompts_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if config["search"] in content:
                    content = content.replace(config["search"], config["production"])
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ {filename}: Switched to production mode")
                else:
                    print(f"⚠️  {filename}: Already in production mode or pattern not found")
            else:
                print(f"❌ {filename}: File not found")
    
    elif target_mode == "test":
        # Switch from production to test
        for filename, config in CONFIGS["test"].items():
            file_path = os.path.join(prompts_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if config["production"] in content:
                    content = content.replace(config["production"], config["search"])
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ {filename}: Switched to test mode")
                else:
                    print(f"⚠️  {filename}: Already in test mode or pattern not found")
            else:
                print(f"❌ {filename}: File not found")
    
    return True

def check_current_mode():
    """Check which mode the system is currently in."""
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
    
    test_mode_count = 0
    production_mode_count = 0
    
    for filename, config in CONFIGS["test"].items():
        file_path = os.path.join(prompts_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            if config["search"] in content:
                test_mode_count += 1
            elif config["production"] in content:
                production_mode_count += 1
    
    total_files = len(CONFIGS["test"])
    
    if test_mode_count == total_files:
        return "test"
    elif production_mode_count == total_files:
        return "production"
    else:
        return "mixed"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        current_mode = check_current_mode()
        print(f"🔍 Current mode: {current_mode}")
        print("\nUsage: python toggle_test_mode.py [test|production|status]")
        print("\nModes:")
        print("  test       - 2 epics, 2 features per epic, 2-3 user stories per feature, 3 tasks max per story, 3 test cases max per story")
        print("  production - 3-7 epics, 4-8 features per epic, 3-6 user stories per feature, 5-12 tasks per feature, 8-15 test cases per story")
        print("  status     - Check current mode")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "status":
        current_mode = check_current_mode()
        print(f"🔍 Current mode: {current_mode}")
        
        if current_mode == "test":
            print("📊 Expected output: 2 epics → 4 features → 8-12 user stories → 24-36 tasks → 24-36 test cases")
        elif current_mode == "production":
            print("📊 Expected output: 3-7 epics → 12-56 features → 36-336 user stories → much larger quantities")
        else:
            print("⚠️  Mixed mode detected - some files may not be synchronized")
    
    elif mode in ["test", "production"]:
        current_mode = check_current_mode()
        
        if current_mode == mode:
            print(f"✅ Already in {mode} mode")
        else:
            print(f"🔄 Switching from {current_mode} to {mode} mode...")
            if toggle_mode(mode):
                new_mode = check_current_mode()
                if new_mode == mode:
                    print(f"✅ Successfully switched to {mode} mode")
                    if mode == "test":
                        print("📊 Expected output: 2 epics → 4 features → 8-12 user stories → 24-36 tasks → 24-36 test cases")
                    else:
                        print("📊 Expected output: 3-7 epics → 12-56 features → 36-336 user stories")
                else:
                    print(f"❌ Switch failed. Current mode: {new_mode}")
    else:
        print("❌ Invalid mode. Use 'test', 'production', or 'status'")
        sys.exit(1)
