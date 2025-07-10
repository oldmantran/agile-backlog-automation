#!/usr/bin/env python3
"""
Debug the feature decomposer with real epic data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config.config_loader import Config
from agents.feature_decomposer_agent import FeatureDecomposerAgent

def test_feature_decomposition_agent():
    """Test feature decomposer with a sample epic."""
    print("🔍 Debug Feature Decomposer")
    print("=" * 40)
    
    try:
        # Initialize
        config = Config()
        agent = FeatureDecomposerAgent(config)
        print("✅ FeatureDecomposerAgent initialized")
        
        # Sample epic (matching epic strategist output format)
        epic = {
            "title": "Core Task Creation and Management",
            "description": "Enable users to create, edit, and delete tasks with essential details like title, description, and due dates. This forms the foundation of personal productivity by allowing users to organize their responsibilities efficiently.",
            "business_value": "Establishes the primary functionality, targeting 80% user adoption for basic task management needs",
            "priority": "High",
            "estimated_complexity": "M",
            "dependencies": ["None"],
            "success_criteria": ["Users can create a task in under 30 seconds", "90% of tasks saved without errors"],
            "target_personas": ["Individual users seeking basic task organization"],
            "risks": ["Over-complicating the UI could reduce usability", "Performance issues with large task lists"]
        }
        
        context = {
            "domain": "productivity software",
            "project_name": "Simple Task Manager",
            "methodology": "Agile/Scrum",
            "target_users": "individual users",
            "platform": "web application",
            "integrations": "standard APIs"
        }
        
        print(f"\\n📋 Test Epic: {epic['title']}")
        print(f"\\n🔄 Decomposing epic to features...")
        
        # Test epic decomposition
        features = agent.decompose_epic(epic, context)
        
        print(f"\\n📊 Epic Decomposition Results:")
        print(f"  Generated features: {len(features)}")
        
        if features:
            print(f"\\n📝 Features:")
            for i, feature in enumerate(features, 1):
                print(f"\\n{i}. {feature.get('title', 'No title')}")
                print(f"   Description: {feature.get('description', 'No description')[:100]}...")
                print(f"   Priority: {feature.get('priority', 'N/A')}")
                print(f"   Story Points: {feature.get('estimated_story_points', 'N/A')}")
            
            # Now test user story decomposition on first feature
            if features:
                test_feature = features[0]
                print(f"\\n🔄 Testing user story decomposition on first feature...")
                print(f"Feature: {test_feature.get('title', 'No title')}")
                
                user_stories = agent.decompose_feature_to_user_stories(test_feature, context)
                
                print(f"\\n📊 User Story Decomposition Results:")
                print(f"  Generated user stories: {len(user_stories)}")
                
                if user_stories:
                    print(f"\\n📝 User Stories:")
                    for i, story in enumerate(user_stories, 1):
                        print(f"\\n{i}. {story.get('title', 'No title')}")
                        print(f"   Story: {story.get('user_story', 'No story')}")
                        print(f"   Points: {story.get('story_points', 'N/A')}")
                        print(f"   Priority: {story.get('priority', 'N/A')}")
                    
                    print(f"\\n✅ Feature decomposer working correctly!")
                    return True
                else:
                    print(f"\\n❌ No user stories generated")
                    return False
        else:
            print(f"\\n❌ No features generated")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_feature_decomposition_agent()
    
    if success:
        print(f"\\n🎉 Feature decomposer test passed!")
    else:
        print(f"\\n❌ Feature decomposer test failed!")

if __name__ == "__main__":
    main()
