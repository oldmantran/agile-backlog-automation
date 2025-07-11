#!/usr/bin/env python3
"""Direct test of UserStoryDecomposerAgent to identify quality issues."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
from config.config_loader import Config

def test_user_story_generation():
    """Test user story generation directly."""
    
    print('🧪 Loading configuration...')
    config = Config('config/settings_testing.yaml')
    
    print('🧪 Initializing UserStoryDecomposerAgent...')
    agent = UserStoryDecomposerAgent(config)
    
    # Simple test feature
    feature = {
        'title': 'Autonomous Ride Booking',
        'description': 'Enable users to book autonomous vehicle rides with real-time availability and dynamic pricing',
        'priority': 'High',
        'estimated_story_points': 13,
        'business_value': 'Increase user convenience and service revenue'
    }
    
    context = {
        'domain': 'Transportation Technology',
        'project_name': 'RideShare App',
        'target_users': 'riders and drivers',
        'platform': 'mobile and web application'
    }
    
    print('🧪 Testing user story generation...')
    print('=' * 60)
    print(f'Feature: {feature["title"]}')
    print(f'Description: {feature["description"]}')
    print('=' * 60)
    
    try:
        user_stories = agent.decompose_feature_to_user_stories(feature, context)
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
            issues = []
            
            if "As a" not in description and "As an" not in description:
                issues.append("Missing user story format")
            
            if "so that I can achieve my objectives" in description:
                issues.append("Generic fallback description")
            
            if len(description.split()) < 10:
                issues.append("Description too short")
                
            # Check for repetitive text
            words = description.split()
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            repeated_words = [word for word, count in word_counts.items() if count > 2 and len(word) > 3]
            if repeated_words:
                issues.append(f"Repeated words: {', '.join(repeated_words)}")
            
            # Check for duplicated phrases
            if description.count("As a") > 1:
                issues.append("Multiple 'As a' phrases")
            
            if issues:
                print(f'   ⚠️  Quality Issues: {"; ".join(issues)}')
            else:
                print(f'   ✅ Quality: Good')
            
            print('-' * 40)
        
    except Exception as e:
        print(f'❌ Error during generation: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_story_generation()
