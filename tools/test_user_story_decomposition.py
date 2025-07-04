#!/usr/bin/env python3
"""
Test the Feature Decomposer user story functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config.config_loader import Config
from agents.decomposition_agent import DecompositionAgent

def test_user_story_decomposition():
    """Test decomposing a feature into user stories."""
    print("🧪 Testing Feature to User Story Decomposition")
    print("=" * 50)
    
    try:
        # Initialize
        config = Config()
        agent = DecompositionAgent(config)
        print("✅ DecompositionAgent initialized")
        
        # Test feature data
        test_feature = {
            "title": "User Account Management",
            "description": "Allow users to create, update, and manage their account profiles including personal information, preferences, and security settings.",
            "acceptance_criteria": [
                "Users can register with email and password",
                "Users can update their profile information",
                "Users can change their password",
                "Users can delete their account"
            ],
            "priority": "High",
            "estimated_story_points": 13
        }
        
        # Test context
        test_context = {
            "domain": "web application",
            "project_name": "Task Management App",
            "methodology": "Agile/Scrum",
            "target_users": "individual users and team members",
            "platform": "web application",
            "team_velocity": "25-30 points per sprint"
        }
        
        print(f"\\n📋 Test Feature:")
        print(f"Title: {test_feature['title']}")
        print(f"Description: {test_feature['description']}")
        print(f"Story Points: {test_feature['estimated_story_points']}")
        
        print(f"\\n🔄 Decomposing feature into user stories...")
        
        # Test the decomposition
        user_stories = agent.decompose_feature_to_user_stories(test_feature, test_context)
        
        print(f"\\n📊 Results:")
        print(f"Generated {len(user_stories)} user stories")
        
        if user_stories:
            print(f"\\n📝 User Stories:")
            for i, story in enumerate(user_stories, 1):
                print(f"\\n{i}. {story.get('title', 'No title')}")
                print(f"   Story: {story.get('user_story', 'No story')}")
                print(f"   Points: {story.get('story_points', 'N/A')}")
                print(f"   Priority: {story.get('priority', 'N/A')}")
                
                # Show acceptance criteria
                criteria = story.get('acceptance_criteria', [])
                if criteria:
                    print(f"   Acceptance Criteria:")
                    for criterion in criteria[:2]:  # Show first 2
                        print(f"     - {criterion}")
                    if len(criteria) > 2:
                        print(f"     ... and {len(criteria) - 2} more")
            
            # Validate structure
            print(f"\\n🔍 Validation:")
            valid_count = 0
            for story in user_stories:
                required_fields = ['title', 'user_story', 'story_points', 'priority', 'acceptance_criteria']
                if all(field in story for field in required_fields):
                    valid_count += 1
            
            print(f"   Valid user stories: {valid_count}/{len(user_stories)}")
            
            if valid_count == len(user_stories):
                print("   ✅ All user stories have required fields")
            else:
                print(f"   ⚠️  {len(user_stories) - valid_count} user stories missing required fields")
            
            return True
        else:
            print("❌ No user stories generated")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    success = test_user_story_decomposition()
    
    if success:
        print("\\n🎉 User story decomposition test passed!")
    else:
        print("\\n❌ User story decomposition test failed!")

if __name__ == "__main__":
    main()
