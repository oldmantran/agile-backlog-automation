#!/usr/bin/env python3
"""Test the Backlog Sweeper quality validation on user stories."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.backlog_sweeper_agent import BacklogSweeperAgent
from config.config_loader import Config

def test_quality_validation():
    """Test Backlog Sweeper quality validation on sample data."""
    
    print('🧪 Loading configuration...')
    config = Config('config/settings_testing.yaml')
    
    print('🧪 Initializing BacklogSweeperAgent...')
    sweeper = BacklogSweeperAgent(config)
    
    # Sample data with quality issues
    epics = [{
        'id': 'epic_1',
        'title': 'Ride Booking Platform',
        'features': [{
            'id': 'feature_1',
            'title': 'Autonomous Vehicle Booking',
            'user_stories': [
                {
                    'id': 'story_1',
                    'title': 'User can view and select available autonomous vehicles',
                    'description': 'Displays a list or map of nearby available autonomous vehicles in real-time.',  # No "As a" format
                    'acceptance_criteria': [
                        'Given I am on the booking page, When I input valid locations, Then I see available vehicles, arrival times, and pricing. Given I have selected a vehicle, When vehicles are available, Then the booking is created. Given there are no vehicles available, When I attempt to book, Then I receive a clear notification.',  # Too long, needs formatting
                    ],
                    'story_points': 5
                },
                {
                    'id': 'story_2',
                    'title': 'User receives dynamic pricing',
                    'description': 'As a rider, I want to see real-time pricing for my ride so that I can make an informed booking decision',  # Good format
                    'acceptance_criteria': ['Price is shown before booking', 'Price updates in real-time'],  # Good format
                    'story_points': 3
                },
                {
                    'id': 'story_3',
                    'title': '',  # Missing title
                    'description': '',  # Missing description
                    'acceptance_criteria': [],  # Missing criteria
                    'story_points': None
                }
            ]
        }]
    }]
    
    print('🧪 Testing quality validation...')
    print('=' * 60)
    
    try:
        discrepancies = sweeper.validate_feature_user_story_relationships(epics)
        
        print(f'Found {len(discrepancies)} quality issues:')
        print('=' * 60)
        
        for i, issue in enumerate(discrepancies, 1):
            print(f'📋 Issue {i}:')
            print(f'   Type: {issue.get("type")}')
            print(f'   Severity: {issue.get("severity")}')
            print(f'   Work Item: {issue.get("work_item_type")} - {issue.get("title")}')
            print(f'   Description: {issue.get("description")}')
            print(f'   Suggested Agent: {issue.get("suggested_agent")}')
            print('-' * 40)
        
        # Test acceptance criteria formatting
        print('\n🧪 Testing acceptance criteria formatting...')
        story_with_long_criteria = epics[0]['features'][0]['user_stories'][0]
        print(f'Original criteria: {story_with_long_criteria["acceptance_criteria"][0][:100]}...')
        
        if 'Given' in story_with_long_criteria["acceptance_criteria"][0]:
            print('✅ Criteria contains Given-When-Then format')
        else:
            print('⚠️ Criteria missing Given-When-Then format')
        
    except Exception as e:
        print(f'❌ Error during validation: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quality_validation()
