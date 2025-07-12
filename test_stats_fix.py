#!/usr/bin/env python3
"""
Test script to validate statistics calculation fix
"""

import sys
sys.path.append('.')

from supervisor.supervisor import WorkflowSupervisor

def test_statistics_calculation():
    """Test the fixed statistics calculation logic"""
    print('🔧 Testing statistics calculation fix...')
    
    # Create test workflow data that matches the real structure
    test_workflow_data = {
        'workflow_id': 'test_stats_fix',
        'epics': [
            {
                'id': 'EP001',
                'title': 'Test Epic 1',
                'features': [
                    {
                        'id': 'F001',
                        'title': 'Test Feature 1',
                        'user_stories': [
                            {
                                'id': 'US001',
                                'title': 'Test User Story 1',
                                'tasks': [
                                    {'id': 'T001', 'title': 'Task 1'},
                                    {'id': 'T002', 'title': 'Task 2'}
                                ],
                                'test_cases': [
                                    {'id': 'TC001', 'title': 'Test Case 1'},
                                    {'id': 'TC002', 'title': 'Test Case 2'},
                                    {'id': 'TC003', 'title': 'Test Case 3'}
                                ]
                            },
                            {
                                'id': 'US002', 
                                'title': 'Test User Story 2',
                                'tasks': [
                                    {'id': 'T003', 'title': 'Task 3'}
                                ],
                                'test_cases': [
                                    {'id': 'TC004', 'title': 'Test Case 4'}
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                'id': 'EP002',
                'title': 'Test Epic 2', 
                'features': [
                    {
                        'id': 'F002',
                        'title': 'Test Feature 2',
                        'user_stories': [
                            {
                                'id': 'US003',
                                'title': 'Test User Story 3',
                                'tasks': [
                                    {'id': 'T004', 'title': 'Task 4'},
                                    {'id': 'T005', 'title': 'Task 5'}
                                ],
                                'test_cases': [
                                    {'id': 'TC005', 'title': 'Test Case 5'}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Create a test supervisor to access the statistics calculation method
    supervisor = WorkflowSupervisor('test_project')
    supervisor.workflow_data = test_workflow_data
    
    # Calculate statistics using the fixed method
    print('📊 Calculating statistics with fixed logic...')
    stats = supervisor._calculate_workflow_stats()
    
    print(f'Statistics calculated: {stats}')
    
    # Verify the counts
    expected_counts = {
        'epics_generated': 2,
        'features_generated': 2,
        'user_stories_generated': 3, 
        'tasks_generated': 5,  # This was previously broken (counted 0)
        'test_cases_generated': 5
    }
    
    print('\n🔍 Validating counts...')
    all_correct = True
    for key, expected in expected_counts.items():
        actual = stats.get(key, 0)
        status = '✅' if actual == expected else '❌'
        print(f'{status} {key}: {actual} (expected {expected})')
        if actual != expected:
            all_correct = False
    
    if all_correct:
        print('\n✅ All statistics calculations are correct!')
    else:
        print('\n❌ Some statistics calculations are incorrect!')
    
    return all_correct

if __name__ == "__main__":
    test_statistics_calculation()
