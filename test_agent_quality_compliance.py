#!/usr/bin/env python3
"""
Test script to verify that all agents create work items that comply with
Backlog Sweeper Agent quality standards.
"""

import sys
import os
import json
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.decomposition_agent import DecompositionAgent
from agents.developer_agent import DeveloperAgent
from agents.qa_tester_agent import QATesterAgent
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator


def test_decomposition_agent_quality():
    """Test that Decomposition Agent creates compliant user stories."""
    print("🔧 Testing Decomposition Agent Quality Compliance")
    print("=" * 60)
    
    config = Config()
    agent = DecompositionAgent(config)
    validator = WorkItemQualityValidator(config.settings)
    
    # Test feature to decompose
    test_feature = {
        'title': 'User Authentication',
        'description': 'Enable users to securely log into the application',
        'acceptance_criteria': [
            'Users can log in with valid credentials',
            'System rejects invalid credentials'
        ],
        'priority': 'High',
        'estimated_story_points': 8
    }
    
    # Create user stories
    user_stories = agent.decompose_feature_to_user_stories(test_feature)
    
    print(f"✅ Created {len(user_stories)} user stories")
    
    # Validate each user story
    total_issues = 0
    for i, story in enumerate(user_stories):
        print(f"\n📋 Validating User Story {i+1}: {story.get('title', 'No title')}")
        
        # Check title
        title_valid, title_issues = validator.validate_work_item_title(story.get('title', ''), "User Story")
        if not title_valid:
            print(f"   ❌ Title issues: {', '.join(title_issues)}")
            total_issues += len(title_issues)
        else:
            print(f"   ✅ Title: Valid")
        
        # Check description
        desc_valid, desc_issues = validator.validate_user_story_description(story.get('description', ''))
        if not desc_valid:
            print(f"   ❌ Description issues: {', '.join(desc_issues)}")
            total_issues += len(desc_issues)
        else:
            print(f"   ✅ Description: Valid")
        
        # Check acceptance criteria
        criteria = story.get('acceptance_criteria', [])
        criteria_valid, criteria_issues = validator.validate_acceptance_criteria(criteria, story.get('title', ''))
        if not criteria_valid or criteria_issues:
            print(f"   ❌ Acceptance criteria issues: {', '.join(criteria_issues)}")
            total_issues += len(criteria_issues)
        else:
            print(f"   ✅ Acceptance criteria: Valid ({len(criteria)} criteria)")
        
        # Check story points
        if not story.get('story_points'):
            print(f"   ❌ Missing story points")
            total_issues += 1
        else:
            print(f"   ✅ Story points: {story.get('story_points')}")
    
    print(f"\n📊 Decomposition Agent Results:")
    print(f"   Total issues found: {total_issues}")
    print(f"   Quality compliance: {'✅ PASS' if total_issues == 0 else '❌ FAIL'}")
    
    return total_issues == 0, user_stories


def test_developer_agent_quality():
    """Test that Developer Agent creates compliant tasks."""
    print("\n💻 Testing Developer Agent Quality Compliance")
    print("=" * 60)
    
    config = Config()
    agent = DeveloperAgent(config)
    validator = WorkItemQualityValidator(config.settings)
    
    # Test feature to create tasks for
    test_feature = {
        'title': 'Login Form Implementation',
        'description': 'Implement the user login form with validation',
        'acceptance_criteria': [
            'Form validates email format',
            'Form validates password requirements',
            'Form submits to authentication API'
        ],
        'priority': 'High',
        'estimated_story_points': 5
    }
    
    # Create tasks
    tasks = agent.generate_tasks(test_feature)
    
    print(f"✅ Created {len(tasks)} tasks")
    
    # Validate each task
    total_issues = 0
    for i, task in enumerate(tasks):
        print(f"\n🔨 Validating Task {i+1}: {task.get('title', 'No title')}")
        
        # Use validator's task structure validation
        task_valid, task_issues = validator.validate_task_structure(task)
        if not task_valid:
            print(f"   ❌ Task issues: {', '.join(task_issues)}")
            total_issues += len(task_issues)
        else:
            print(f"   ✅ Task structure: Valid")
            print(f"   ✅ Estimated hours: {task.get('estimated_hours', 'N/A')}")
            print(f"   ✅ Category: {task.get('category', 'N/A')}")
    
    # Test story points estimation
    test_story = {
        'title': 'Complex User Authentication',
        'description': 'As a user, I want to log in using multi-factor authentication so that my account is secure',
        'acceptance_criteria': [
            'User enters username and password',
            'System sends SMS verification code',
            'User enters verification code',
            'System authenticates and grants access',
            'Response time is under 3 seconds',
            'Security audit trail is maintained'
        ]
    }
    
    estimated_points = agent.estimate_story_points(test_story)
    print(f"\n🎯 Story Points Estimation Test:")
    print(f"   Story: {test_story['title']}")
    print(f"   Criteria count: {len(test_story['acceptance_criteria'])}")
    print(f"   Estimated points: {estimated_points}")
    
    print(f"\n📊 Developer Agent Results:")
    print(f"   Total issues found: {total_issues}")
    print(f"   Quality compliance: {'✅ PASS' if total_issues == 0 else '❌ FAIL'}")
    
    return total_issues == 0, tasks


def test_qa_tester_agent_quality():
    """Test that QA Tester Agent creates compliant test cases and enhances criteria."""
    print("\n🧪 Testing QA Tester Agent Quality Compliance")
    print("=" * 60)
    
    config = Config()
    agent = QATesterAgent(config)
    validator = WorkItemQualityValidator(config.settings)
    
    # Test feature to create test cases for
    test_feature = {
        'title': 'Password Reset Functionality',
        'description': 'Allow users to reset their password via email',
        'acceptance_criteria': [
            'User can request password reset',
            'System sends reset email',
            'User can set new password'
        ],
        'priority': 'High'
    }
    
    # Create test cases
    test_cases = agent.generate_test_cases(test_feature)
    
    print(f"✅ Created {len(test_cases)} test cases")
    
    # Validate each test case
    total_issues = 0
    for i, test_case in enumerate(test_cases):
        print(f"\n🔍 Validating Test Case {i+1}: {test_case.get('title', 'No title')}")
        
        # Use validator's test case structure validation
        test_valid, test_issues = validator.validate_test_case_structure(test_case)
        if not test_valid:
            print(f"   ❌ Test case issues: {', '.join(test_issues)}")
            total_issues += len(test_issues)
        else:
            print(f"   ✅ Test case structure: Valid")
            print(f"   ✅ Test type: {test_case.get('test_type', 'N/A')}")
            print(f"   ✅ Automation candidate: {test_case.get('automation_candidate', 'N/A')}")
    
    # Test acceptance criteria enhancement
    test_story = {
        'title': 'Poor Quality User Story',
        'description': 'As a user, I want better functionality',
        'acceptance_criteria': [
            'Make it work properly',
            'It should be good'
        ]
    }
    
    print(f"\n📋 Acceptance Criteria Enhancement Test:")
    print(f"   Original criteria: {test_story['acceptance_criteria']}")
    
    # Validate current criteria quality
    validation_result = agent.validate_acceptance_criteria_quality(
        test_story['acceptance_criteria'], 
        test_story
    )
    
    print(f"   Quality assessment: {'✅ Valid' if validation_result['is_valid'] else '❌ Issues found'}")
    if not validation_result['is_valid']:
        print(f"   Issues: {', '.join(validation_result['issues'])}")
        print(f"   QA Recommendations: {', '.join(validation_result['qa_recommendations'])}")
    
    # Enhance criteria
    enhanced_criteria = agent.enhance_acceptance_criteria(test_story)
    print(f"   Enhanced criteria count: {len(enhanced_criteria)}")
    print(f"   Enhanced criteria: {enhanced_criteria[:2]}...")  # Show first 2
    
    print(f"\n📊 QA Tester Agent Results:")
    print(f"   Total issues found: {total_issues}")
    print(f"   Quality compliance: {'✅ PASS' if total_issues == 0 else '❌ FAIL'}")
    
    return total_issues == 0, test_cases


def test_integration_compliance():
    """Test that work items from all agents would pass Backlog Sweeper validation."""
    print("\n🔄 Testing Integration with Backlog Sweeper Standards")
    print("=" * 60)
    
    # Mock ADO client for sweeper
    class MockADOClient:
        def __init__(self, work_items):
            self.work_items = work_items
        
        def query_work_items(self, work_item_type):
            return [wi['id'] for wi in self.work_items if wi['fields'].get('System.WorkItemType') == work_item_type]
        
        def get_work_item_details(self, work_item_ids):
            return [wi for wi in self.work_items if wi['id'] in work_item_ids]
        
        def get_work_item_relations(self, work_item_id):
            return []  # Simplified for this test
    
    # Create sample work items from all agents
    config = Config()
    
    # Get user stories from decomposition agent
    decomp_agent = DecompositionAgent(config)
    test_feature = {
        'title': 'User Profile Management',
        'description': 'Enable users to manage their profile information',
        'acceptance_criteria': ['Users can update profile', 'Changes are saved'],
        'priority': 'Medium',
        'estimated_story_points': 5
    }
    user_stories = decomp_agent.decompose_feature_to_user_stories(test_feature)
    
    # Convert to mock ADO format
    mock_work_items = []
    for i, story in enumerate(user_stories):
        mock_work_items.append({
            'id': 2000 + i,
            'fields': {
                'System.WorkItemType': 'User Story',
                'System.Title': story.get('title', ''),
                'System.Description': story.get('description', ''),
                'Microsoft.VSTS.Common.AcceptanceCriteria': '\n'.join(story.get('acceptance_criteria', [])),
                'Microsoft.VSTS.Scheduling.StoryPoints': story.get('story_points')
            }
        })
    
    # Create Backlog Sweeper and test
    mock_ado = MockADOClient(mock_work_items)
    sweeper = BacklogSweeperAgent(ado_client=mock_ado, config=config.settings)
    
    # Run validation
    discrepancies = sweeper.scrape_and_validate_work_items()
    
    print(f"📊 Integration Test Results:")
    print(f"   Work items tested: {len(mock_work_items)}")
    print(f"   Discrepancies found: {len(discrepancies)}")
    
    if discrepancies:
        print(f"   ❌ INTEGRATION ISSUES FOUND:")
        for disc in discrepancies[:3]:  # Show first 3
            print(f"      • {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
    else:
        print(f"   ✅ ALL WORK ITEMS PASS SWEEPER VALIDATION")
    
    return len(discrepancies) == 0


if __name__ == "__main__":
    print("🚀 Agent Quality Compliance Testing")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    try:
        # Run all tests
        decomp_pass, user_stories = test_decomposition_agent_quality()
        dev_pass, tasks = test_developer_agent_quality()
        qa_pass, test_cases = test_qa_tester_agent_quality()
        integration_pass = test_integration_compliance()
        
        # Final results
        print("\n" + "=" * 60)
        print("🎯 FINAL RESULTS")
        print("=" * 60)
        print(f"Decomposition Agent: {'✅ PASS' if decomp_pass else '❌ FAIL'}")
        print(f"Developer Agent: {'✅ PASS' if dev_pass else '❌ FAIL'}")
        print(f"QA Tester Agent: {'✅ PASS' if qa_pass else '❌ FAIL'}")
        print(f"Integration Test: {'✅ PASS' if integration_pass else '❌ FAIL'}")
        
        all_passed = decomp_pass and dev_pass and qa_pass and integration_pass
        print(f"\nOVERALL COMPLIANCE: {'✅ ALL AGENTS COMPLIANT' if all_passed else '❌ ISSUES FOUND'}")
        
        # Save test results
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_results': {
                'decomposition_agent': decomp_pass,
                'developer_agent': dev_pass,
                'qa_tester_agent': qa_pass,
                'integration_test': integration_pass
            },
            'sample_outputs': {
                'user_stories': user_stories[:2] if user_stories else [],
                'tasks': tasks[:2] if tasks else [],
                'test_cases': test_cases[:2] if test_cases else []
            }
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/agent_quality_compliance_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Test results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
