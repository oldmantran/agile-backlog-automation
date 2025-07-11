#!/usr/bin/env python3
"""Test the complete task formatting and validation system."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.developer_agent import DeveloperAgent
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from config.config_loader import Config

def test_complete_task_system():
    """Test the complete task formatting and validation system."""
    
    config = Config('config/settings_testing.yaml')
    developer_agent = DeveloperAgent(config)
    sweeper_agent = BacklogSweeperAgent(config)
    
    print('🧪 Testing complete task formatting and validation system...')
    print('=' * 80)
    
    # Sample data with various task formatting issues
    epics = [{
        'id': 'epic_1',
        'title': 'Vehicle Booking Platform',
        'features': [{
            'id': 'feature_1',
            'title': 'API Development',
            'user_stories': [{
                'id': 'story_1',
                'title': 'RESTful API for Vehicle Booking',
                'description': 'As a frontend developer, I want a RESTful API so that I can integrate vehicle booking functionality',
                'story_points': 8,
                'tasks': [
                    {
                        'id': 'task_1',
                        'title': 'Develop RESTful API Endpoints',
                        'description': 'Develop a RESTful API that accepts start and end locations, queries vehicle availability in real-time, and calculates dynamic pricing based on demand, distance, and time. Integrate ETA estimation logic and provide data structured for frontend consumption. **Definition of Done:** - Implementation completed - Code reviewed and approved - Unit tests written and passing - Documentation updated - Ready for integration testing',
                        'estimated_hours': 16
                    },
                    {
                        'id': 'task_2', 
                        'title': 'Implement Authentication Middleware',
                        'description': 'Create secure authentication middleware for API endpoints. Definition of Done: Implementation completed, Code reviewed and approved, Unit tests written and passing, Documentation updated, Ready for integration testing',
                        'estimated_hours': 8
                    },
                    {
                        'id': 'task_3',
                        'title': '',  # Missing title
                        'description': '',  # Missing description
                        # Missing estimation
                    }
                ]
            }]
        }]
    }]
    
    print('📋 Testing task formatting...')
    print('-' * 40)
    
    # Test formatting on the tasks
    for epic in epics:
        for feature in epic['features']:
            for user_story in feature['user_stories']:
                for i, task in enumerate(user_story['tasks']):
                    enhanced_task = developer_agent._enhance_single_task(task)
                    user_story['tasks'][i] = enhanced_task
                    
                    print(f'Task {i+1}: {enhanced_task.get("title", "No title")}')
                    print(f'Description:\n{enhanced_task.get("description", "No description")}')
                    print('-' * 30)
    
    print('\n📋 Testing task validation...')
    print('-' * 40)
    
    # Test validation
    discrepancies = sweeper_agent.validate_user_story_tasks(epics)
    
    print(f'Found {len(discrepancies)} task-related issues:')
    for i, issue in enumerate(discrepancies, 1):
        print(f'{i}. {issue.get("type")} - {issue.get("description")} (Severity: {issue.get("severity")})')
    
    print('\n✅ Task formatting and validation test completed!')

if __name__ == "__main__":
    test_complete_task_system()
