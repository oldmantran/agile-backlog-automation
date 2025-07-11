#!/usr/bin/env python3
"""Test the improved formatting logic for acceptance criteria."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
from config.config_loader import Config

def test_formatting():
    """Test the improved formatting logic."""
    
    config = Config('config/settings_testing.yaml')
    agent = UserStoryDecomposerAgent(config)
    
    # Test data with formatting issues
    story_with_long_criteria = {
        'title': 'Test Story',
        'description': 'As a user, I want to test formatting so that criteria are readable',
        'acceptance_criteria': [
            'Given I am on the booking page, When I input valid locations, Then I see available vehicles, arrival times, and pricing. Given I have selected a vehicle, When vehicles are available, Then the booking is created. Given there are no vehicles available, When I attempt to book, Then I receive a clear notification.'
        ]
    }
    
    print('🧪 Testing acceptance criteria formatting...')
    print('=' * 80)
    print('Original criteria:')
    for i, criterion in enumerate(story_with_long_criteria['acceptance_criteria'], 1):
        print(f'{i}. {criterion}')
    
    enhanced_story = agent._enhance_single_user_story(story_with_long_criteria)
    
    print('\n' + '=' * 80)
    print('Formatted criteria:')
    for i, criterion in enumerate(enhanced_story['acceptance_criteria'], 1):
        print(f'{i}. {criterion}')
    
    print(f'\n✅ Split {len(story_with_long_criteria["acceptance_criteria"])} criteria into {len(enhanced_story["acceptance_criteria"])} separate items')

if __name__ == "__main__":
    test_formatting()
