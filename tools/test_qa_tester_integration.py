#!/usr/bin/env python3
"""
Test Azure DevOps Test Management API integration for QA Tester Agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config.config_loader import Config
from agents.qa_tester_agent import QATesterAgent
from integrators.azure_devops_api import AzureDevOpsIntegrator

def test_qa_tester_test_plan_creation():
    """Test QA Tester Agent's test plan and test suite creation functionality."""
    print("🧪 Testing QA Tester Agent - Test Plan & Suite Creation")
    print("=" * 60)
    
    try:
        # Initialize config and agent (adjust path for running from tools directory)
        config = Config(env_path="../.env", settings_path="../config/settings.yaml")
        print("✅ Config loaded")
        
        # Debug prompt template loading
        from utils.prompt_manager import prompt_manager
        print(f"🔍 Available prompt templates: {list(prompt_manager.templates.keys())}")
        print(f"🔍 QA Tester template exists: {'qa_tester_agent' in prompt_manager.templates}")
        
        qa_agent = QATesterAgent(config)
        print("✅ QA Tester Agent initialized")
        
        # Check if Azure DevOps integration is available
        ado_settings = config.settings.get('azure_devops', {})
        if not ado_settings.get('organization'):
            print("⚠️  Azure DevOps integration not configured - testing with mock data")
            test_with_mock_data(qa_agent)
            return
        
        print(f"🔗 Azure DevOps Organization: {ado_settings.get('organization')}")
        print(f"📋 Project: {ado_settings.get('project')}")
        
        # Initialize Azure DevOps integrator
        try:
            ado_integrator = AzureDevOpsIntegrator(
                organization_url=f"https://dev.azure.com/{ado_settings['organization']}",
                project=ado_settings['project'],
                personal_access_token=ado_settings.get('personal_access_token', ''),
                area_path=ado_settings.get('area_path', ''),
                iteration_path=ado_settings.get('iteration_path', '')
            )
            print("✅ Azure DevOps integrator initialized")
            
            # Set the ADO client in the QA agent
            qa_agent.ado_client = ado_integrator
            
        except Exception as e:
            print(f"❌ Failed to initialize Azure DevOps integrator: {e}")
            print("⚠️  Testing with mock data instead")
            test_with_mock_data(qa_agent)
            return
        
        # Test data - mock feature with user stories
        test_feature = {
            'id': 99901,  # Use high ID to avoid conflicts
            'title': 'Test Feature for Validation',
            'description': 'A test feature to validate test plan creation',
            'user_stories': [
                {
                    'id': 99902,
                    'title': 'Test User Story 1',
                    'user_story': 'As a tester, I want to validate test plan creation so that I can ensure quality',
                    'acceptance_criteria': [
                        'Given a feature, when test plan is created, then it appears in Azure DevOps',
                        'Given test plan exists, when test suite is created, then it contains user stories',
                        'Given test suite exists, when test cases are added, then they are properly organized'
                    ],
                    'story_points': 5,
                    'priority': 'High'
                },
                {
                    'id': 99903,
                    'title': 'Test User Story 2', 
                    'user_story': 'As a user, I want comprehensive test coverage so that the system is reliable',
                    'acceptance_criteria': [
                        'Given user story, when test cases are generated, then they cover all scenarios',
                        'Given test cases exist, when executed, then results are properly tracked'
                    ],
                    'story_points': 3,
                    'priority': 'Medium'
                }
            ]
        }
        
        test_context = {
            'project_name': 'Agile Backlog Automation Test',
            'domain': 'test automation',
            'platform': 'web application'
        }
        
        print("\\n🔍 Testing Test Plan Structure Creation...")
        
        # Test 1: Create test plan structure
        test_plan_structure = qa_agent.create_test_plan_structure(test_feature, test_context)
        print(f"✅ Test plan structure created: {test_plan_structure['test_plan_name']}")
        print(f"   📝 Test suites planned: {len(test_plan_structure['test_suites'])}")
        
        for suite in test_plan_structure['test_suites']:
            print(f"   📋 Suite: {suite['suite_name']} (Story ID: {suite['user_story_id']})")
        
        print("\\n🔗 Testing Azure DevOps Integration...")
        
        # Test 2: Test the ADO integration methods directly
        if hasattr(ado_integrator, 'test_client') and ado_integrator.test_client:
            print("🧪 Testing Test Plan Creation in Azure DevOps...")
            
            try:
                # Test getting existing test plans
                existing_plans = ado_integrator.test_client._get_test_plans()
                print(f"✅ Retrieved existing test plans: {len(existing_plans.get('value', []))} found")
                
                # Test creating test plan
                test_plan = ado_integrator.test_client.ensure_test_plan_exists(
                    feature_id=test_feature['id'],
                    feature_name=test_feature['title']
                )
                
                if test_plan:
                    print(f"✅ Test plan created/found: {test_plan.get('name')} (ID: {test_plan.get('id')})")
                    
                    # Test creating test suite
                    for user_story in test_feature['user_stories']:
                        test_suite = ado_integrator.test_client.ensure_test_suite_exists(
                            test_plan_id=test_plan['id'],
                            user_story_id=user_story['id'],
                            user_story_name=user_story['title']
                        )
                        
                        if test_suite:
                            print(f"✅ Test suite created/found: {test_suite.get('name')} (ID: {test_suite.get('id')})")
                        else:
                            print(f"❌ Failed to create test suite for user story: {user_story['title']}")
                            
                else:
                    print("❌ Failed to create test plan")
                    
            except Exception as e:
                print(f"❌ Azure DevOps API error: {e}")
                print("📝 This suggests an issue with the Test Management API integration")
        else:
            print("❌ Test client not available - Azure DevOps Test Management API not properly initialized")
        
        print("\\n📋 Diagnostic Information:")
        print(f"   🔗 API Base URL: {ado_integrator.test_client.base_url if hasattr(ado_integrator, 'test_client') and ado_integrator.test_client else 'Not available'}")
        print(f"   🔑 Headers configured: {bool(ado_integrator.test_client.headers if hasattr(ado_integrator, 'test_client') and ado_integrator.test_client else False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_mock_data(qa_agent):
    """Test QA agent functionality with mock data when Azure DevOps is not available."""
    print("\\n🎭 Testing with Mock Data (No Azure DevOps Connection)")
    
    test_feature = {
        'id': 1,
        'title': 'Mock Feature',
        'description': 'A mock feature for testing',
        'user_stories': [
            {
                'id': 2,
                'title': 'Mock User Story',
                'user_story': 'As a user, I want mock functionality',
                'acceptance_criteria': ['Given mock, when tested, then passes'],
                'story_points': 3
            }
        ]
    }
    
    # Test structure creation
    structure = qa_agent.create_test_plan_structure(test_feature)
    print(f"✅ Mock test plan structure created: {structure['test_plan_name']}")
    
    # Test user story test case generation
    test_cases = qa_agent.generate_user_story_test_cases(test_feature['user_stories'][0])
    print(f"✅ Mock test cases generated: {len(test_cases)} test cases")
    
    print("✅ Mock testing completed successfully")

if __name__ == "__main__":
    success = test_qa_tester_test_plan_creation()
    exit(0 if success else 1)
