#!/usr/bin/env python3
"""
Test the complete work item chain: Epic -> Feature -> User Story -> Task
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.decomposition_agent import DecompositionAgent
from agents.developer_agent import DeveloperAgent

def test_complete_chain():
    """Test the complete chain from product vision to tasks."""
    print("🔗 Testing Complete Work Item Chain")
    print("=" * 50)
    
    try:
        # Initialize agents
        config = Config()
        epic_agent = EpicStrategist(config)
        feature_agent = DecompositionAgent(config)
        dev_agent = DeveloperAgent(config)
        print("✅ All agents initialized")
        
        # Test vision
        vision = """
Create a simple personal task manager that allows users to:
- Create and organize tasks
- Set due dates and priorities
- Track progress and completion
- Manage personal productivity
"""
        
        context = {
            "domain": "productivity software",
            "project_name": "Personal Task Manager",
            "methodology": "Agile/Scrum",
            "target_users": "individual users",
            "platform": "web application"
        }
        
        print(f"\\n📋 Test Vision:")
        print(vision.strip())
        
        # Step 1: Generate Epic
        print(f"\\n🎯 Step 1: Generating Epic...")
        epics = epic_agent.generate_epics(vision, context)
        
        if not epics:
            print("❌ No epics generated")
            return False
        
        epic = epics[0]  # Use first epic
        print(f"✅ Epic: {epic.get('title', 'No title')}")
        
        # Step 2: Decompose Epic to Features
        print(f"\\n🔧 Step 2: Decomposing Epic to Features...")
        features = feature_agent.decompose_epic(epic, context)
        
        if not features:
            print("❌ No features generated")
            return False
        
        epic['features'] = features
        print(f"✅ Generated {len(features)} features")
        
        # Step 3: Decompose Features to User Stories
        print(f"\\n📱 Step 3: Decomposing Features to User Stories...")
        total_user_stories = 0
        
        for i, feature in enumerate(features[:2]):  # Test first 2 features
            print(f"  Feature {i+1}: {feature.get('title', 'No title')}")
            
            user_stories = feature_agent.decompose_feature_to_user_stories(feature, context)
            feature['user_stories'] = user_stories
            total_user_stories += len(user_stories)
            
            print(f"    ✅ Generated {len(user_stories)} user stories")
        
        # Step 4: Generate Tasks for User Stories  
        print(f"\\n⚙️ Step 4: Generating Tasks for User Stories...")
        total_tasks = 0
        
        for feature in features[:2]:  # Test first 2 features
            for j, user_story in enumerate(feature.get('user_stories', [])[:2]):  # First 2 user stories
                print(f"    User Story: {user_story.get('title', 'No title')}")
                
                tasks = dev_agent.generate_tasks(user_story, context)
                user_story['tasks'] = tasks
                total_tasks += len(tasks)
                
                print(f"      ✅ Generated {len(tasks)} tasks")
        
        # Summary
        print(f"\\n📊 Chain Summary:")
        print(f"  Epic: {epic.get('title', 'No title')}")
        print(f"  Features: {len(features)}")
        print(f"  User Stories: {total_user_stories}")
        print(f"  Tasks: {total_tasks}")
        
        # Validate structure for ADO integration
        print(f"\\n🔍 ADO Integration Validation:")
        
        ado_ready = True
        
        # Check epic structure
        epic_fields = ['title', 'description', 'business_value', 'priority']
        missing_epic = [f for f in epic_fields if f not in epic]
        if missing_epic:
            print(f"  ❌ Epic missing fields: {missing_epic}")
            ado_ready = False
        else:
            print("  ✅ Epic has required fields")
        
        # Check feature structures
        feature_issues = 0
        for feature in features:
            feature_fields = ['title', 'description', 'priority']
            if not all(f in feature for f in feature_fields):
                feature_issues += 1
        
        if feature_issues > 0:
            print(f"  ❌ {feature_issues} features missing required fields")
            ado_ready = False
        else:
            print("  ✅ All features have required fields")
        
        # Check user story structures  
        story_issues = 0
        for feature in features:
            for story in feature.get('user_stories', []):
                story_fields = ['title', 'user_story', 'story_points', 'acceptance_criteria']
                if not all(f in story for f in story_fields):
                    story_issues += 1
        
        if story_issues > 0:
            print(f"  ❌ {story_issues} user stories missing required fields")
            ado_ready = False
        else:
            print("  ✅ All user stories have required fields")
        
        # Check task structures
        task_issues = 0
        for feature in features:
            for story in feature.get('user_stories', []):
                for task in story.get('tasks', []):
                    task_fields = ['title', 'description']
                    if not all(f in task for f in task_fields):
                        task_issues += 1
        
        if task_issues > 0:
            print(f"  ❌ {task_issues} tasks missing required fields")
            ado_ready = False
        else:
            print("  ✅ All tasks have required fields")
        
        if ado_ready:
            print("\\n🎉 Complete chain test PASSED! Ready for ADO integration.")
            return True
        else:
            print("\\n❌ Complete chain test FAILED! ADO integration issues found.")
            return False
            
    except Exception as e:
        print(f"❌ Chain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete chain test."""
    success = test_complete_chain()
    
    if success:
        print("\\n🚀 Ready for end-to-end ADO testing!")
    else:
        print("\\n🔧 Fix issues before proceeding to ADO testing.")

if __name__ == "__main__":
    main()
