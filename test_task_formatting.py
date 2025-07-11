#!/usr/bin/env python3
"""Test the improved task description formatting logic."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.developer_agent import DeveloperAgent
from config.config_loader import Config

def test_task_formatting():
    """Test the improved task description formatting logic."""
    
    config = Config('config/settings_testing.yaml')
    agent = DeveloperAgent(config)
    
    # Test data with formatting issues
    task_with_unformatted_dod = {
        'title': 'Develop RESTful API for Vehicle Booking',
        'description': 'Develop a RESTful API that accepts start and end locations, queries vehicle availability in real-time, and calculates dynamic pricing based on demand, distance, and time. Integrate ETA estimation logic and provide data structured for frontend consumption. **Definition of Done:** - Implementation completed - Code reviewed and approved - Unit tests written and passing - Documentation updated - Ready for integration testing',
        'estimated_hours': 16
    }
    
    print('🧪 Testing task description formatting...')
    print('=' * 80)
    print('Original description:')
    print(task_with_unformatted_dod['description'])
    
    enhanced_task = agent._enhance_single_task(task_with_unformatted_dod)
    
    print('\n' + '=' * 80)
    print('Formatted description:')
    print(enhanced_task['description'])
    
    # Test another format
    task_with_inline_dod = {
        'title': 'Implement User Authentication',
        'description': 'Create secure user authentication system with password hashing and session management. Definition of Done: Implementation completed, Code reviewed and approved, Unit tests written and passing, Documentation updated, Ready for integration testing',
        'estimated_hours': 12
    }
    
    print('\n' + '=' * 80)
    print('Original description (inline format):')
    print(task_with_inline_dod['description'])
    
    enhanced_task2 = agent._enhance_single_task(task_with_inline_dod)
    
    print('\n' + '=' * 80)
    print('Formatted description (inline format):')
    print(enhanced_task2['description'])

if __name__ == "__main__":
    test_task_formatting()
