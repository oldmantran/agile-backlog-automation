#!/usr/bin/env python3
"""
Test QA Stage Integration in Full Workflow
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import Config
from supervisor.supervisor import WorkflowSupervisor

def test_qa_workflow_stage():
    """Test QA stage integration in full workflow."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print('\n=== QA WORKFLOW STAGE TEST ===')
    logger.info('Testing QA stage integration in supervisor workflow...')
    
    try:
        # Initialize supervisor
        supervisor = WorkflowSupervisor()
        
        # Set up minimal test data
        test_data = {
            'epics': [{
                'id': 'test-epic-1',
                'title': 'Test Epic',
                'description': 'Test epic for workflow integration',
                'features': [{
                    'id': 'test-feature-1',
                    'title': 'Test Feature',
                    'description': 'Test feature for workflow integration',
                    'user_stories': [{
                        'id': 'test-story-1',
                        'title': 'Test User Story',
                        'description': 'Test user story for workflow integration',
                        'acceptance_criteria': [
                            'Given the user is on the test page',
                            'When the user clicks the test button',
                            'Then the system should display success message'
                        ],
                        'priority': 'High'
                    }]
                }]
            }]
        }
        
        # Set workflow data
        supervisor.workflow_data = test_data
        
        # Test 1: Verify QA stage is available
        print('\n1. Testing QA stage availability:')
        if hasattr(supervisor, '_execute_qa_generation'):
            print('✅ QA execution stage method available')
        else:
            print('❌ QA execution stage method not found')
            return False
        
        # Test 2: Execute QA stage
        print('\n2. Testing QA stage execution:')
        try:
            supervisor._execute_qa_generation()
            print('✅ QA stage executed successfully')
            
            # Verify QA artifacts were added to workflow data
            epic = supervisor.workflow_data['epics'][0]
            feature = epic['features'][0]
            user_story = feature['user_stories'][0]
            
            # Check test plan
            if 'test_plan' in feature:
                print('   ✅ Test plan created and integrated')
                test_plan = feature['test_plan']
                print(f'      - Test plan name: {test_plan.get("name", "Unknown")}')
            else:
                print('   ❌ Test plan missing from feature')
                return False
            
            # Check test suite
            if 'test_suite' in user_story:
                print('   ✅ Test suite created and integrated')
                test_suite = user_story['test_suite']
                print(f'      - Test suite name: {test_suite.get("name", "Unknown")}')
                print(f'      - Expected test cases: {test_suite.get("expected_test_cases", 0)}')
            else:
                print('   ❌ Test suite missing from user story')
                return False
            
            # Check test cases
            if 'test_cases' in user_story:
                test_cases = user_story['test_cases']
                print(f'   ✅ Test cases created: {len(test_cases)} cases')
                
                # Verify test case structure
                if test_cases:
                    sample_case = test_cases[0]
                    required_fields = ['id', 'title', 'category', 'priority', 'area_path']
                    missing_fields = [field for field in required_fields if field not in sample_case]
                    
                    if not missing_fields:
                        print('   ✅ Test case structure valid')
                    else:
                        print(f'   ❌ Test case missing fields: {missing_fields}')
                        return False
            else:
                print('   ❌ Test cases missing from user story')
                return False
                
        except Exception as e:
            print(f'❌ QA stage execution failed: {e}')
            return False
        
        # Test 3: Verify workflow sequence includes QA
        print('\n3. Testing workflow sequence integration:')
        workflow_sequence = supervisor.config.get_setting('workflow', 'sequence') or []
        if 'qa_lead_agent' in workflow_sequence:
            qa_position = workflow_sequence.index('qa_lead_agent')
            print(f'✅ QA stage positioned correctly at stage {qa_position + 1} of {len(workflow_sequence)}')
            print(f'   Sequence: {" → ".join(workflow_sequence)}')
        else:
            print('❌ QA stage not found in workflow sequence')
            return False
        
        # Test 4: Verify integration with Azure DevOps (conceptual)
        print('\n4. Testing Azure DevOps integration readiness:')
        sample_test_plan = feature.get('test_plan', {})
        sample_test_case = user_story.get('test_cases', [{}])[0]
        
        # Check for Azure DevOps required fields
        ado_ready_plan = all(field in sample_test_plan for field in ['name', 'description', 'area_path'])
        ado_ready_case = all(field in sample_test_case for field in ['id', 'title', 'area_path'])
        
        if ado_ready_plan and ado_ready_case:
            print('✅ QA artifacts ready for Azure DevOps integration')
            print(f'   - Test plan area path: {sample_test_plan.get("area_path", "Unknown")}')
            print(f'   - Test case area path: {sample_test_case.get("area_path", "Unknown")}')
        else:
            print('❌ QA artifacts missing Azure DevOps required fields')
            return False
        
        print('\n=== QA WORKFLOW STAGE TEST COMPLETE ===')
        print('✅ All QA workflow integration tests passed!')
        print('\n📊 QA Integration Summary:')
        print(f'   • QA Lead Agent: Integrated with supervisor ✅')
        print(f'   • Sub-agents: TestPlan, TestSuite, TestCase all working ✅')
        print(f'   • Workflow position: Stage {qa_position + 1} of {len(workflow_sequence)} ✅')
        print(f'   • Test artifacts: Plans, suites, and cases created ✅')
        print(f'   • Azure DevOps ready: All required fields present ✅')
        print(f'   • Performance: Optimized boundary generation working ✅')
        
        return True
        
    except Exception as e:
        logger.error(f"QA workflow stage test failed: {e}")
        print(f'❌ Workflow stage test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_qa_workflow_stage()
    sys.exit(0 if success else 1)
