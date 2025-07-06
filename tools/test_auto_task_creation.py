#!/usr/bin/env python3
"""
Test the supervisor's auto task creation for missing tasks.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
from supervisor.supervisor import WorkflowSupervisor

def test_auto_task_creation():
    print("🔧 Testing Auto Task Creation...")
    
    # Initialize supervisor
    supervisor = WorkflowSupervisor()
    
    # Get a user story that needs tasks (from our recent sweep results)
    test_user_story_id = 1697  # "Handle Notification Failures and Warnings"
    
    print(f"📝 Testing with User Story ID: {test_user_story_id}")
    
    # Create a mock discrepancy
    mock_discrepancy = {
        'type': 'user_story_missing_tasks',
        'work_item_id': test_user_story_id,
        'work_item_type': 'User Story',
        'title': 'Handle Notification Failures and Warnings',
        'description': 'User Story has no child tasks.',
        'severity': 'medium',
        'suggested_agent': 'developer_agent'
    }
    
    print("🔍 Checking supervisor setup...")
    print(f"   Agents initialized: {hasattr(supervisor, 'agents') and supervisor.agents is not None}")
    if hasattr(supervisor, 'agents'):
        print(f"   Agent count: {len(supervisor.agents)}")
        print(f"   Developer agent available: {'developer_agent' in supervisor.agents}")
    
    print(f"   Azure integrator: {hasattr(supervisor, 'azure_integrator')}")
    
    # Test the task creation method directly
    print(f"\n🛠️ Testing auto task creation for User Story {test_user_story_id}...")
    
    try:
        # Get current child work items count
        current_relations = supervisor.azure_integrator.get_work_item_relations(test_user_story_id)
        current_children = [r for r in current_relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
        print(f"   Current child items: {len(current_children)}")
        
        # Call the auto-create method
        supervisor._auto_create_missing_tasks(test_user_story_id, mock_discrepancy)
        
        # Check if tasks were created
        updated_relations = supervisor.azure_integrator.get_work_item_relations(test_user_story_id)
        updated_children = [r for r in updated_relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
        new_task_count = len(updated_children) - len(current_children)
        
        print(f"   Tasks created: {new_task_count}")
        
        if new_task_count > 0:
            print(f"✅ Successfully created {new_task_count} tasks!")
            
            # Show the new tasks
            for i, rel in enumerate(updated_children[-new_task_count:], 1):
                task_url = rel.get('url', '')
                if 'workitems/' in task_url:
                    task_id = task_url.split('workitems/')[-1]
                    print(f"     {i}. New Task ID: {task_id}")
        else:
            print("❌ No tasks were created")
            
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auto_task_creation()
