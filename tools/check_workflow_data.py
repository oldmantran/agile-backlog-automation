#!/usr/bin/env python3
"""
Script to check current workflow data in memory and show generated tasks.
This helps verify what has been generated before Azure DevOps integration.
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_workflow_data():
    """Check the current workflow data and show generated artifacts."""
    print("🔍 Checking Current Workflow Data")
    print("=" * 60)
    
    # Check if there are any output files from recent runs
    output_dir = "output"
    if os.path.exists(output_dir):
        print(f"\n📁 Checking output directory: {output_dir}")
        files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
        
        if files:
            print(f"   Found {len(files)} output files:")
            for i, file in enumerate(files[:5]):  # Show last 5 files
                file_path = os.path.join(output_dir, file)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                size = os.path.getsize(file_path)
                print(f"   {i+1}. {file} ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # Try to load the most recent file
            latest_file = os.path.join(output_dir, files[0])
            print(f"\n📄 Loading most recent output: {files[0]}")
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                analyze_workflow_data(workflow_data, files[0])
                
            except Exception as e:
                print(f"   ❌ Error loading file: {e}")
        else:
            print("   ❌ No output files found")
    else:
        print("   ❌ Output directory not found")
    
    # Check for any temporary workflow data in memory (if we can access it)
    print(f"\n🧠 Checking for in-memory workflow data...")
    print("   Note: In-memory data is only available while the process is running")
    print("   Check the logs for current job status and progress")

def analyze_workflow_data(workflow_data, filename):
    """Analyze the workflow data and show statistics."""
    print(f"\n📊 Workflow Data Analysis: {filename}")
    print("=" * 60)
    
    # Basic structure check
    if not isinstance(workflow_data, dict):
        print("   ❌ Invalid workflow data format")
        return
    
    # Check for key sections
    sections = ['epics', 'metadata', 'product_vision']
    for section in sections:
        if section in workflow_data:
            print(f"   ✅ {section}: Found")
        else:
            print(f"   ❌ {section}: Missing")
    
    # Count artifacts
    epics = workflow_data.get('epics', [])
    print(f"\n📈 Artifact Counts:")
    print(f"   Epics: {len(epics)}")
    
    total_features = 0
    total_user_stories = 0
    total_tasks = 0
    total_test_cases = 0
    
    for epic in epics:
        features = epic.get('features', [])
        total_features += len(features)
        
        for feature in features:
            user_stories = feature.get('user_stories', [])
            total_user_stories += len(user_stories)
            
            for user_story in user_stories:
                tasks = user_story.get('tasks', [])
                test_cases = user_story.get('test_cases', [])
                total_tasks += len(tasks)
                total_test_cases += len(test_cases)
    
    print(f"   Features: {total_features}")
    print(f"   User Stories: {total_user_stories}")
    print(f"   Tasks: {total_tasks}")
    print(f"   Test Cases: {total_test_cases}")
    
    # Show execution metadata
    metadata = workflow_data.get('metadata', {})
    execution_summary = metadata.get('execution_summary', {})
    
    if execution_summary:
        print(f"\n⏱️ Execution Summary:")
        print(f"   Epics Generated: {execution_summary.get('epics_generated', 0)}")
        print(f"   Features Generated: {execution_summary.get('features_generated', 0)}")
        print(f"   User Stories Generated: {execution_summary.get('user_stories_generated', 0)}")
        print(f"   Tasks Generated: {execution_summary.get('tasks_generated', 0)}")
        print(f"   Test Cases Generated: {execution_summary.get('test_cases_generated', 0)}")
        
        execution_time = execution_summary.get('execution_time_seconds')
        if execution_time:
            minutes = execution_time / 60
            print(f"   Execution Time: {execution_time:.1f} seconds ({minutes:.1f} minutes)")
        
        print(f"   Stages Completed: {execution_summary.get('stages_completed', 0)}")
        print(f"   Errors Encountered: {execution_summary.get('errors_encountered', 0)}")
    
    # Show Azure integration status
    azure_integration = workflow_data.get('azure_integration', {})
    if azure_integration:
        print(f"\n🔗 Azure DevOps Integration:")
        status = azure_integration.get('status', 'Unknown')
        print(f"   Status: {status}")
        
        work_items_created = azure_integration.get('work_items_created', [])
        if work_items_created:
            print(f"   Work Items Created: {len(work_items_created)}")
            
            # Count by type
            type_counts = {}
            for item in work_items_created:
                item_type = item.get('type', 'Unknown')
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            print(f"   By Type:")
            for item_type, count in type_counts.items():
                print(f"     {item_type}: {count}")
    
    # Show sample tasks (first few)
    if total_tasks > 0:
        print(f"\n📋 Sample Tasks (showing first 5):")
        task_count = 0
        for epic in epics:
            for feature in epic.get('features', []):
                for user_story in feature.get('user_stories', []):
                    for task in user_story.get('tasks', []):
                        if task_count < 5:
                            title = task.get('title', 'Untitled Task')
                            priority = task.get('priority', 'Medium')
                            estimate = task.get('estimate_hours', 0)
                            print(f"   {task_count + 1}. {title}")
                            print(f"      Priority: {priority}, Estimate: {estimate}h")
                            task_count += 1
                        else:
                            break
                    if task_count >= 5:
                        break
                if task_count >= 5:
                    break
            if task_count >= 5:
                break
        
        if total_tasks > 5:
            print(f"   ... and {total_tasks - 5} more tasks")

def check_current_job_status():
    """Check the current job status from logs."""
    print(f"\n🔍 Checking Current Job Status")
    print("=" * 60)
    
    # Check recent logs for current job
    log_file = "logs/supervisor.log"
    if os.path.exists(log_file):
        print(f"📄 Checking recent logs: {log_file}")
        
        try:
            # Read last 50 lines
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines
            
            # Look for current job patterns
            current_job_patterns = [
                "job_20250719_090019",  # Your current job
                "Executing stage:",
                "Generated",
                "Creating",
                "Azure DevOps"
            ]
            
            found_relevant = False
            for line in recent_lines:
                if any(pattern in line for pattern in current_job_patterns):
                    print(f"   {line.strip()}")
                    found_relevant = True
            
            if not found_relevant:
                print("   No recent job activity found in logs")
                
        except Exception as e:
            print(f"   ❌ Error reading logs: {e}")
    else:
        print("   ❌ Log file not found")

if __name__ == "__main__":
    check_workflow_data()
    check_current_job_status()
    
    print(f"\n💡 Tips:")
    print("   - The workflow data is stored in memory during execution")
    print("   - Output files are saved to the 'output' directory")
    print("   - Azure DevOps integration happens at the very end")
    print("   - Check logs for real-time progress updates") 