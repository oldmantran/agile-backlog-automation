#!/usr/bin/env python3
"""
Test work item structure validation without API calls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_sample_data():
    """Create sample work item data to test the structure."""
    return {
        'epics': [{
            'title': 'Task Management Core',
            'description': 'Enable users to create, organize, and manage personal tasks with due dates and priorities.',
            'business_value': 'Increases user productivity by 30% through organized task management',
            'priority': 'High',
            'estimated_complexity': 'L',
            'dependencies': [],
            'success_criteria': ['Users can create tasks', 'Users can set priorities', 'Users can track completion'],
            'features': [{
                'title': 'Task Creation and Management',
                'description': 'Allow users to create, edit, and delete tasks with basic information.',
                'priority': 'High',
                'estimated_story_points': 8,
                'acceptance_criteria': [
                    'Users can create new tasks',
                    'Users can edit existing tasks',
                    'Users can delete tasks'
                ],
                'user_stories': [{
                    'title': 'User can create new tasks',
                    'user_story': 'As a user, I want to create new tasks so that I can track what I need to do',
                    'description': 'Users can add new tasks with title, description, and basic details.',
                    'story_points': 3,
                    'priority': 'High',
                    'acceptance_criteria': [
                        'Given I am on the tasks page, When I click create task, Then I see a task creation form',
                        'Given I am on the task creation form, When I enter title and save, Then the task is created'
                    ],
                    'dependencies': [],
                    'definition_of_ready': ['UI mockups available'],
                    'definition_of_done': ['Code complete', 'Tests passing'],
                    'category': 'core_functionality',
                    'user_type': 'general_user',
                    'tasks': [{
                        'title': 'Create task creation form UI',
                        'description': 'Design and implement the user interface for creating new tasks.',
                        'estimated_hours': 4,
                        'priority': 'High',
                        'assigned_to': '',
                        'acceptance_criteria': [
                            'Form includes title and description fields',
                            'Form has save and cancel buttons',
                            'Form validates required fields'
                        ]
                    }, {
                        'title': 'Implement task creation API',
                        'description': 'Create backend API endpoint to handle task creation requests.',
                        'estimated_hours': 3,
                        'priority': 'High',
                        'assigned_to': '',
                        'acceptance_criteria': [
                            'API accepts POST requests with task data',
                            'API validates input data',
                            'API returns created task with ID'
                        ]
                    }]
                }],
                'test_cases': [{
                    'title': 'Verify task creation functionality',
                    'description': 'Test that users can successfully create tasks through the UI.',
                    'priority': 'High',
                    'test_steps': [
                        'Navigate to tasks page',
                        'Click create new task button',
                        'Fill in task details',
                        'Save the task'
                    ],
                    'expected_results': [
                        'Task creation form opens',
                        'Task is saved successfully',
                        'Task appears in task list'
                    ]
                }]
            }]
        }]
    }

def validate_ado_structure(data):
    """Validate the data structure for ADO integration."""
    print("🔍 Validating ADO Work Item Structure")
    print("=" * 40)
    
    issues = []
    
    # Validate epics
    epics = data.get('epics', [])
    print(f"\\n📋 Epics: {len(epics)}")
    
    for i, epic in enumerate(epics):
        epic_required = ['title', 'description', 'business_value', 'priority']
        missing = [f for f in epic_required if f not in epic]
        if missing:
            issues.append(f"Epic {i+1} missing: {missing}")
        else:
            print(f"  ✅ Epic {i+1}: {epic['title']}")
        
        # Validate features
        features = epic.get('features', [])
        print(f"    Features: {len(features)}")
        
        for j, feature in enumerate(features):
            feature_required = ['title', 'description', 'priority']
            missing = [f for f in feature_required if f not in feature]
            if missing:
                issues.append(f"Feature {j+1} in Epic {i+1} missing: {missing}")
            else:
                print(f"      ✅ Feature {j+1}: {feature['title']}")
            
            # Validate user stories
            user_stories = feature.get('user_stories', [])
            print(f"        User Stories: {len(user_stories)}")
            
            for k, story in enumerate(user_stories):
                story_required = ['title', 'user_story', 'story_points', 'acceptance_criteria']
                missing = [f for f in story_required if f not in story]
                if missing:
                    issues.append(f"User Story {k+1} in Feature {j+1} missing: {missing}")
                else:
                    print(f"          ✅ User Story {k+1}: {story['title']}")
                
                # Validate tasks
                tasks = story.get('tasks', [])
                print(f"            Tasks: {len(tasks)}")
                
                for l, task in enumerate(tasks):
                    task_required = ['title', 'description']
                    missing = [f for f in task_required if f not in task]
                    if missing:
                        issues.append(f"Task {l+1} in User Story {k+1} missing: {missing}")
                    else:
                        print(f"              ✅ Task {l+1}: {task['title']}")
            
            # Validate test cases
            test_cases = feature.get('test_cases', [])
            if test_cases:
                print(f"        Test Cases: {len(test_cases)}")
                for tc in test_cases:
                    print(f"          ✅ Test: {tc.get('title', 'No title')}")
    
    # Summary
    print(f"\\n📊 Structure Summary:")
    print(f"  Total Epics: {len(epics)}")
    
    total_features = sum(len(epic.get('features', [])) for epic in epics)
    print(f"  Total Features: {total_features}")
    
    total_stories = sum(
        len(feature.get('user_stories', []))
        for epic in epics
        for feature in epic.get('features', [])
    )
    print(f"  Total User Stories: {total_stories}")
    
    total_tasks = sum(
        len(story.get('tasks', []))
        for epic in epics
        for feature in epic.get('features', [])
        for story in feature.get('user_stories', [])
    )
    print(f"  Total Tasks: {total_tasks}")
    
    total_tests = sum(
        len(feature.get('test_cases', []))
        for epic in epics
        for feature in epic.get('features', [])
    )
    print(f"  Total Test Cases: {total_tests}")
    
    # Validation results
    print(f"\\n🎯 Validation Results:")
    if issues:
        print(f"  ❌ {len(issues)} issues found:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print("  ✅ All structures valid for ADO integration!")
        print("  ✅ Hierarchy: Epic → Feature → User Story → Task")
        print("  ✅ Test Cases linked to Features")
        return True

def main():
    """Test the work item structure validation."""
    print("🧪 Work Item Structure Validation Test")
    print("=" * 50)
    
    # Create sample data
    sample_data = create_sample_data()
    
    # Validate structure
    is_valid = validate_ado_structure(sample_data)
    
    if is_valid:
        print("\\n🎉 Structure validation PASSED!")
        print("\\n🚀 Ready for end-to-end ADO integration test!")
    else:
        print("\\n❌ Structure validation FAILED!")
        print("\\n🔧 Fix structure issues before ADO testing.")

if __name__ == "__main__":
    main()
