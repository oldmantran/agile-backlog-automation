"""
Debug script to isolate QA Lead Agent issues
"""

import logging
import json
from config.config_loader import Config
from agents.qa_lead_agent import QALeadAgent

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_qa_lead_agent():
    """Test QA Lead Agent in isolation"""
    try:
        # Load configuration
        config = Config()
        
        # Create QA Lead Agent
        qa_agent = QALeadAgent(config)
        logger.info("QA Lead Agent initialized successfully")
        
        # Test data - simplified version
        test_epics = [
            {
                'id': 'epic-1',
                'title': 'Test Epic',
                'description': 'Test epic for QA debugging',
                'features': [
                    {
                        'id': 'feature-1',
                        'title': 'Test Feature',
                        'description': 'Test feature for QA debugging',
                        'user_stories': [
                            {
                                'id': 'story-1',
                                'title': 'Test User Story',
                                'description': 'Test user story for QA debugging',
                                'acceptance_criteria': [
                                    'Given the user is on the test page',
                                    'When the user clicks the test button',
                                    'Then the system should display success message'
                                ],
                                'priority': 'High'
                            }
                        ]
                    }
                ]
            }
        ]
        
        test_context = {
            'project_context': {
                'domain': 'software_development',
                'project_type': 'web_application',
                'project_name': 'QA Debug Test'
            }
        }
        
        # Test QA Lead Agent
        logger.info("Testing QA Lead Agent with minimal data...")
        
        result = qa_agent.generate_quality_assurance(
            epics=test_epics,
            context=test_context,
            area_path='Test Area'
        )
        
        logger.info(f"QA Lead Agent result: {json.dumps(result, indent=2)}")
        
        # Check results
        qa_summary = result.get('qa_summary', {})
        logger.info(f"Test Plans Created: {qa_summary.get('test_plans_created', 0)}")
        logger.info(f"Test Suites Created: {qa_summary.get('test_suites_created', 0)}")
        logger.info(f"Test Cases Created: {qa_summary.get('test_cases_created', 0)}")
        
        if qa_summary.get('errors'):
            logger.error(f"Errors encountered: {qa_summary.get('errors')}")
        
        return result
        
    except Exception as e:
        logger.error(f"QA Lead Agent test failed: {e}")
        raise

if __name__ == "__main__":
    test_qa_lead_agent()
