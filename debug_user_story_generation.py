#!/usr/bin/env python3
"""Debug script to test user story generation and identify quality issues."""

import sys
import json
from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config

def test_user_story_generation():
    """Test user story generation to identify quality issues."""
    
    config = Config('config/settings_testing.yaml')
    supervisor = WorkflowSupervisor(config)
    
    # Simple test feature
    feature = {
        'title': 'Autonomous Ride Booking',
        'description': 'Enable users to book autonomous vehicle rides with real-time availability',
        'priority': 'High',
        'estimated_story_points': 13
    }
    
    context = {
        'domain': 'Transportation',
        'project_name': 'RideShare App',
        'target_users': 'riders and drivers'
    }
    
    print('🧪 Testing user story generation...')
    print('=' * 60)
    
    try:
        user_stories = supervisor.user_story_decomposer.decompose_feature_to_user_stories(feature, context)
        print(f'✅ Generated {len(user_stories)} user stories')
        print('=' * 60)
        
        for i, story in enumerate(user_stories, 1):
            print(f'📋 User Story {i}:')
            print(f'   Title: {story.get("title", "No title")}')
            print(f'   Description: {story.get("description", "No description")}')
            print(f'   Story Points: {story.get("story_points", "Not set")}')
            print(f'   Priority: {story.get("priority", "Not set")}')
            
            # Check for quality issues
            description = story.get("description", "")
            if "As a" not in description and "As an" not in description:
                print(f'   ⚠️  Description missing user story format!')
            
            if "so that I can achieve my objectives" in description:
                print(f'   ⚠️  Generic fallback description detected!')
            
            if len(description.split()) < 10:
                print(f'   ⚠️  Description too short!')
            
            print('-' * 40)
        
    except Exception as e:
        print(f'❌ Error during generation: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_story_generation()
