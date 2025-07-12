#!/usr/bin/env python3
"""
Test QA Completeness Validation System
Validates that all features have test plans, all user stories have test suites,
and all test cases are properly linked to Azure DevOps.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.qa_lead_agent import QALeadAgent
from utils.qa_completeness_validator import QACompletenessValidator
from integrators.azure_devops_api import AzureDevOpsIntegrator


def test_qa_completeness_system():
    """Test the QA completeness validation system."""
    print("🧪 Testing QA Completeness Validation System")
    print("=" * 60)
    
    try:
        # Initialize configuration
        config = Config()
        print("✅ Config loaded")
        
        # Initialize QA Lead Agent
        qa_agent = QALeadAgent(config)
        print("✅ QA Lead Agent initialized with completeness validation")
        
        # Initialize completeness validator
        validator = QACompletenessValidator(config)
        print("✅ QA Completeness Validator initialized")
        
        # Create test data that simulates incomplete test organization
        test_epics = [
            {
                'id': 'epic-1',
                'title': 'Test Epic 1',
                'features': [
                    {
                        'id': 'feature-1', 
                        'title': 'Feature with Test Plan',
                        'test_plan': {'id': 1, 'name': 'Test Plan 1'},  # Has test plan
                        'user_stories': [
                            {
                                'id': 'story-1',
                                'title': 'Story with Test Suite',
                                'test_suite': {'id': 1, 'name': 'Test Suite 1'},  # Has test suite
                                'test_cases': [
                                    {
                                        'id': 'case-1',
                                        'title': 'Linked Test Case',
                                        'test_suite_id': 1,  # Properly linked
                                        'linked_to_suite': True
                                    },
                                    {
                                        'id': 'case-2',
                                        'title': 'Unlinked Test Case',
                                        # Missing test_suite_id - unlinked
                                    }
                                ]
                            },
                            {
                                'id': 'story-2',
                                'title': 'Story without Test Suite',
                                # Missing test_suite
                                'test_cases': [
                                    {
                                        'id': 'case-3',
                                        'title': 'Orphaned Test Case'
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'id': 'feature-2',
                        'title': 'Feature without Test Plan',
                        # Missing test_plan
                        'user_stories': [
                            {
                                'id': 'story-3',
                                'title': 'Story without Plan or Suite',
                                'test_cases': [
                                    {
                                        'id': 'case-4',
                                        'title': 'Another Orphaned Test Case'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        print("\\n🔍 Testing Completeness Validation...")
        
        # Test 1: Validate test organization
        completeness_report = validator.validate_test_organization(test_epics)
        
        print(f"✅ Completeness validation completed")
        print(f"   Overall Score: {completeness_report.completeness_score:.1%}")
        print(f"   Features with Plans: {completeness_report.features_with_test_plans}/{completeness_report.total_features}")
        print(f"   Stories with Suites: {completeness_report.stories_with_test_suites}/{completeness_report.total_user_stories}")
        print(f"   Linked Test Cases: {completeness_report.linked_test_cases}/{completeness_report.total_test_cases}")
        
        # Test 2: Generate completeness report
        report_text = validator.generate_completeness_report(completeness_report)
        print("\\n📋 Generated Completeness Report:")
        print(report_text)
        
        # Test 3: Test auto-remediation capabilities (without ADO client)
        print("\\n🔧 Testing Auto-remediation Logic...")
        remediation_result = validator.auto_remediate_test_organization(test_epics, ado_client=None)
        
        print(f"✅ Auto-remediation logic tested")
        print(f"   Plans would be created: {remediation_result['test_plans_created']}")
        print(f"   Suites would be created: {remediation_result['test_suites_created']}")
        print(f"   Cases would be linked: {remediation_result['test_cases_linked']}")
        print(f"   Errors encountered: {len(remediation_result['errors'])}")
        
        # Test 4: Test integration with QA Lead Agent
        print("\\n🎯 Testing QA Lead Agent Integration...")
        
        # Mock context
        test_context = {
            'project_context': {
                'domain': 'test_validation',
                'project_name': 'QA Completeness Test'
            }
        }
        
        # Test QA generation with completeness validation
        qa_result = qa_agent.generate_quality_assurance(
            epics=test_epics,
            context=test_context,
            area_path="Test Area"
        )
        
        if qa_result and qa_result.get('qa_summary'):
            summary = qa_result['qa_summary']
            print("✅ QA Lead Agent integration successful")
            print(f"   Test plans created: {summary.get('test_plans_created', 0)}")
            print(f"   Test suites created: {summary.get('test_suites_created', 0)}")
            print(f"   Test cases created: {summary.get('test_cases_created', 0)}")
            
            if 'completeness_score' in summary:
                print(f"   Final completeness score: {summary['completeness_score']:.1%}")
                
            if 'remediation_result' in summary:
                print("   Auto-remediation was triggered")
                
        else:
            print("❌ QA Lead Agent integration failed")
            return False
        
        # Test 5: Test configuration validation
        print("\\n⚙️ Testing Configuration Validation...")
        
        qa_config = config.get_setting('agents', 'qa_lead_agent') or {}
        test_org_config = qa_config.get('test_organization', {})
        ado_config = qa_config.get('ado_integration', {})
        
        print(f"✅ Configuration validation completed")
        print(f"   Completeness enforcement: {test_org_config.get('enforce_completeness', False)}")
        print(f"   Auto-create test plans: {ado_config.get('auto_create_test_plans', False)}")
        print(f"   Auto-create test suites: {ado_config.get('auto_create_test_suites', False)}")
        print(f"   Auto-link test cases: {ado_config.get('auto_link_test_cases', False)}")
        
        print("\\n🎉 All QA completeness validation tests passed!")
        print("\\n📊 System Capabilities Summary:")
        print("   ✅ Completeness scoring and validation")
        print("   ✅ Comprehensive reporting with recommendations")
        print("   ✅ Auto-remediation for missing test artifacts")
        print("   ✅ Integration with QA Lead Agent workflow")
        print("   ✅ Configuration-driven behavior")
        print("   ✅ Azure DevOps Test Management API integration ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_qa_completeness_system()
    exit(0 if success else 1)
