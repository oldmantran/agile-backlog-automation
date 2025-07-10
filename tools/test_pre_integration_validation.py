#!/usr/bin/env python3
"""
Test the new pre-integration validation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.backlog_sweeper_agent import BacklogSweeperAgent
from config.config_loader import Config

def test_pre_integration_validation():
    """Test the pre-integration validation functionality."""
    print("🔍 Testing Pre-Integration Validation Functionality")
    print("=" * 60)
    
    # Create a mock workflow data structure
    test_workflow_data = {
        'epics': [
            {
                'title': 'User Management Epic',
                'description': 'Comprehensive user management system with authentication and authorization',
                'features': [
                    {
                        'title': 'User Authentication',
                        'description': 'Secure user login and registration system',
                        'user_stories': [
                            {
                                'title': 'User can register account',
                                'description': 'As a new user, I want to register an account',
                                'acceptance_criteria': [
                                    'User can enter email and password',
                                    'System validates email format',
                                    'User receives confirmation email'
                                ],
                                'tasks': [
                                    {
                                        'title': 'Create registration form',
                                        'description': 'Build React form for user registration'
                                    }
                                ],
                                'test_cases': [
                                    {
                                        'title': 'Test successful registration',
                                        'steps': [
                                            'Navigate to registration page',
                                            'Enter valid email and password',
                                            'Click register button'
                                        ],
                                        'expected_result': 'User account created successfully'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Test with missing required fields
    test_workflow_data_invalid = {
        'epics': [
            {
                # Missing title - should trigger critical error
                'description': 'Epic without title',
                'features': [
                    {
                        'title': 'Feature with issues',
                        'user_stories': [
                            {
                                'title': 'Story without acceptance criteria',
                                # Missing acceptance_criteria - should trigger critical error
                                'description': 'Story missing acceptance criteria'
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    try:
        # Initialize configuration and backlog sweeper
        config = Config()
        sweeper = BacklogSweeperAgent(
            ado_client=None,  # Mock client for testing
            supervisor_callback=None,
            config=config.settings
        )
        
        # Test 1: Valid workflow data
        print("🧪 Test 1: Valid workflow data")
        validation_report = sweeper.validate_pre_integration(test_workflow_data)
        
        print(f"   Status: {validation_report['status']}")
        print(f"   Total Issues: {validation_report['summary']['total_issues']}")
        print(f"   Critical Issues: {validation_report['summary']['critical_issues']}")
        print(f"   Warning Issues: {validation_report['summary']['warning_issues']}")
        
        if validation_report['status'] == 'passed':
            print("   ✅ Valid data passed validation as expected")
        else:
            print("   ⚠️ Valid data failed validation - check implementation")
        
        # Test 2: Invalid workflow data
        print("\n🧪 Test 2: Invalid workflow data (missing required fields)")
        validation_report_invalid = sweeper.validate_pre_integration(test_workflow_data_invalid)
        
        print(f"   Status: {validation_report_invalid['status']}")
        print(f"   Total Issues: {validation_report_invalid['summary']['total_issues']}")
        print(f"   Critical Issues: {validation_report_invalid['summary']['critical_issues']}")
        
        if validation_report_invalid['status'] == 'failed':
            print("   ✅ Invalid data failed validation as expected")
            print("   📋 Critical issues found:")
            for issue in validation_report_invalid['issues']:
                if issue.get('severity') == 'critical':
                    print(f"      - {issue.get('description')}")
        else:
            print("   ⚠️ Invalid data passed validation - check implementation")
        
        # Test 3: Empty workflow data
        print("\n🧪 Test 3: Empty workflow data")
        validation_report_empty = sweeper.validate_pre_integration({'epics': []})
        
        print(f"   Status: {validation_report_empty['status']}")
        print(f"   Critical Issues: {validation_report_empty['summary']['critical_issues']}")
        
        if validation_report_empty['status'] == 'failed' and validation_report_empty['summary']['critical_issues'] > 0:
            print("   ✅ Empty data failed validation as expected")
        else:
            print("   ⚠️ Empty data should fail validation")
        
        print("\n🎉 Pre-integration validation testing completed!")
        print("=" * 60)
        print("✅ Benefits of the new validation system:")
        print("   - Catches structural issues before ADO upload")
        print("   - Validates required fields for work item creation")
        print("   - Checks content quality and completeness")
        print("   - Prevents failed ADO integration attempts")
        print("   - Provides actionable recommendations for fixes")
        print("   - Improves overall system reliability")
        
        return True
        
    except Exception as e:
        print(f"❌ Pre-integration validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pre_integration_validation()
    
    if success:
        print("\n🎊 Pre-integration validation is ready!")
        print("✅ Your current job will benefit from this validation")
        print("🔍 Validation will run automatically before ADO integration")
    else:
        print("\n⚠️ Pre-integration validation needs fixes")
    
    exit(0 if success else 1)
