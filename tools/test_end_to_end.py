#!/usr/bin/env python3
"""
End-to-end supervisor test with ADO integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from supervisor.supervisor import WorkflowSupervisor

def main():
    print("🚀 End-to-End Supervisor Test with ADO Integration")
    print("=" * 60)
    
    try:
        # Initialize supervisor
        print("🔧 Initializing Supervisor...")
        supervisor = WorkflowSupervisor()
        print("✅ Supervisor initialized successfully")
        
        # Simple product vision for testing
        vision = """
Create a basic personal task management application that allows users to:
- Create and manage personal tasks
- Set task priorities (High, Medium, Low)
- Mark tasks as complete or incomplete
- View task lists organized by priority

This should be a simple, focused MVP for individual productivity.
"""
        
        print(f"\\n📋 Product Vision:")
        print(vision.strip())
        
        # Configure project context
        print(f"\\n⚙️ Configuring Project Context...")
        supervisor.configure_project_context('productivity', {
            'domain': 'productivity software',
            'project_name': 'Simple Task Manager',
            'methodology': 'Agile/Scrum',
            'target_users': 'individual users',
            'platform': 'web application',
            'team_velocity': '20-25 points per sprint'
        })
        print("✅ Project context configured")
        
        # Execute workflow with ADO integration
        print(f"\\n🔄 Executing Workflow with ADO Integration...")
        
        # Run with shorter stages for faster testing
        test_stages = [
            'epic_strategist',
            'decomposition_agent', 
            'user_story_decomposer'
        ]
        
        result = supervisor.execute_workflow(
            product_vision=vision,
            stages=test_stages,
            human_review=False,  # No human prompts
            save_outputs=True,
            integrate_azure=True  # Enable ADO integration
        )
        
        print(f"\\n📊 Workflow Results:")
        
        if result and 'epics' in result:
            epics = result['epics']
            print(f"  Epics Generated: {len(epics)}")
            
            total_features = sum(len(epic.get('features', [])) for epic in epics)
            print(f"  Features Generated: {total_features}")
            
            total_stories = 0
            for epic in epics:
                for feature in epic.get('features', []):
                    total_stories += len(feature.get('user_stories', []))
            print(f"  User Stories Generated: {total_stories}")
            
            # Check ADO integration results
            ado_results = result.get('azure_integration', {})
            if ado_results.get('status') == 'success':
                work_items = ado_results.get('work_items_created', [])
                print(f"  ✅ ADO Work Items Created: {len(work_items)}")
                
                # Show created work items
                print(f"\\n📋 Created Work Items in ADO:")
                for item in work_items[:10]:  # Show first 10
                    work_type = item.get('type', 'Unknown')
                    title = item.get('title', 'No title')
                    item_id = item.get('id', 'No ID')
                    print(f"    {work_type} #{item_id}: {title}")
                
                if len(work_items) > 10:
                    print(f"    ... and {len(work_items) - 10} more")
                
                print(f"\\n🎉 End-to-end test PASSED!")
                print(f"✅ Vision → Epics → Features → User Stories → ADO Work Items")
                return True
            else:
                print(f"  ❌ ADO Integration Failed: {ado_results}")
                return False
        else:
            print("  ❌ No workflow results generated")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\\n🎉 All systems working! Backlog automation is ready for production use.")
    else:
        print("\\n🔧 Issues found. Check logs and fix before production use.")
