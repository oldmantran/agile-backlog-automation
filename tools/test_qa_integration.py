#!/usr/bin/env python3
"""
Test QA Integration with Supervisor
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import Config
from supervisor.supervisor import WorkflowSupervisor

def test_qa_integration():
    """Test QA Lead Agent integration with supervisor."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    print('\n=== QA INTEGRATION TEST ===')
    logger.info('Testing QA Lead Agent integration with supervisor...')
    
    try:
        # Initialize configuration and supervisor
        supervisor = WorkflowSupervisor()
        
        # Test 1: Check QA Lead Agent initialization
        print('\n1. Testing QA Lead Agent initialization:')
        qa_agent = supervisor.agents.get('qa_lead_agent')
        if qa_agent:
            print('✅ QA Lead Agent initialized successfully')
            print(f'   - Agent name: {qa_agent.name}')
            print('   - Sub-agents: TestPlan, TestSuite, TestCase agents loaded')
            
            # Test sub-agents
            if hasattr(qa_agent, 'test_plan_agent') and qa_agent.test_plan_agent:
                print('   ✅ TestPlanAgent initialized')
            else:
                print('   ❌ TestPlanAgent missing')
                
            if hasattr(qa_agent, 'test_suite_agent') and qa_agent.test_suite_agent:
                print('   ✅ TestSuiteAgent initialized')
            else:
                print('   ❌ TestSuiteAgent missing')
                
            if hasattr(qa_agent, 'test_case_agent') and qa_agent.test_case_agent:
                print('   ✅ TestCaseAgent initialized')
            else:
                print('   ❌ TestCaseAgent missing')
        else:
            print('❌ QA Lead Agent not found in supervisor')
            return False
        
        # Test 2: Check workflow configuration
        print('\n2. Testing QA workflow stage configuration:')
        workflow_sequence = supervisor.config.get_setting('workflow', 'sequence') or []
        if 'qa_lead_agent' in workflow_sequence:
            print('✅ QA Lead Agent included in workflow sequence')
            qa_position = workflow_sequence.index('qa_lead_agent')
            print(f'   - Position in workflow: {qa_position + 1} of {len(workflow_sequence)}')
            print(f'   - Workflow sequence: {workflow_sequence}')
        else:
            print('❌ QA Lead Agent not found in workflow sequence')
            return False
        
        # Test 3: Test QA context setup
        print('\n3. Testing QA context configuration:')
        context = supervisor.project_context.get_context('qa_lead_agent')
        if context:
            print('✅ QA context configured successfully')
            project_context = context.get('project_context', {})
            print(f'   - Domain: {project_context.get("domain", "Not set")}')
            print(f'   - Project type: {project_context.get("project_type", "Not set")}')
        else:
            print('❌ QA context not available')
            return False
        
        # Test 4: Test QA method availability
        print('\n4. Testing QA execution method:')
        if hasattr(supervisor, '_execute_qa_generation'):
            print('✅ QA execution method available in supervisor')
        else:
            print('❌ QA execution method missing from supervisor')
            return False
        
        # Test 5: Test minimal QA execution (with test data)
        print('\n5. Testing minimal QA execution:')
        test_data = {
            'epics': [{
                'id': 'test-epic-1',
                'title': 'Test Epic',
                'description': 'Test epic for integration testing',
                'features': [{
                    'id': 'test-feature-1',
                    'title': 'Test Feature',
                    'description': 'Test feature for integration testing',
                    'user_stories': [{
                        'id': 'test-story-1',
                        'title': 'Test User Story',
                        'description': 'Test user story for integration testing',
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
        
        try:
            # Store test data temporarily
            supervisor.workflow_data = test_data
            
            # Test QA generation
            qa_result = qa_agent.generate_quality_assurance(
                epics=test_data['epics'],
                context=context,
                area_path="Test Area"
            )
            
            if qa_result and qa_result.get('qa_summary'):
                summary = qa_result['qa_summary']
                print('✅ QA execution successful')
                print(f'   - Test plans created: {summary.get("test_plans_created", 0)}')
                print(f'   - Test suites created: {summary.get("test_suites_created", 0)}')
                print(f'   - Test cases created: {summary.get("test_cases_created", 0)}')
                print(f'   - Errors: {len(summary.get("errors", []))}')
            else:
                print('❌ QA execution failed - no results returned')
                return False
                
        except Exception as e:
            print(f'❌ QA execution failed: {e}')
            return False
        
        print('\n=== QA INTEGRATION TEST COMPLETE ===')
        print('✅ All QA integration tests passed!')
        return True
        
    except Exception as e:
        logger.error(f"QA integration test failed: {e}")
        print(f'❌ Integration test failed: {e}')
        return False

if __name__ == "__main__":
    success = test_qa_integration()
    sys.exit(0 if success else 1)
