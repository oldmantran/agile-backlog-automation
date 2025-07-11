"""
Test Suite Agent - Specialized agent for creating test suites at the user story level
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import Agent


class TestSuiteAgent(Agent):
    """
    Specialized agent for creating test suites for user stories.
    
    Responsibilities:
    - Create test suites for each user story
    - Organize test cases within suites
    - Link suites to appropriate test plans
    - Maintain suite hierarchy and relationships
    """
    
    def __init__(self, config):
        super().__init__("test_suite_agent", config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Test suite specific settings
        self.suite_types = {
            'functional': 'Functional Test Suite',
            'integration': 'Integration Test Suite',
            'acceptance': 'User Acceptance Test Suite',
            'regression': 'Regression Test Suite'
        }
    
    def create_test_suite(self, 
                         feature: Dict[str, Any],
                         user_story: Dict[str, Any], 
                         context: Dict[str, Any],
                         area_path: str) -> Dict[str, Any]:
        """
        Create a test suite for a user story.
        
        Args:
            feature: Parent feature information
            user_story: User story to create test suite for
            context: Project context and configuration
            area_path: Azure DevOps area path
            
        Returns:
            Dictionary with test suite information and success status
        """
        try:
            user_story_title = user_story.get('title', 'Unknown User Story')
            self.logger.info(f"Creating test suite for user story: {user_story_title}")
            
            # Generate test suite content using LLM
            test_suite_content = self._generate_test_suite_content(feature, user_story, context)
            
            if not test_suite_content:
                return {
                    'success': False,
                    'error': 'Failed to generate test suite content'
                }
            
            # Create test suite structure
            test_suite = {
                'name': f"User Story: {user_story_title}",
                'description': test_suite_content.get('description', ''),
                'suite_type': 'StaticTestSuite',
                'area_path': area_path,
                'test_categories': test_suite_content.get('test_categories', []),
                'test_objectives': test_suite_content.get('test_objectives', []),
                'prerequisites': test_suite_content.get('prerequisites', []),
                'test_data_requirements': test_suite_content.get('test_data_requirements', []),
                'user_story_id': user_story.get('id'),
                'feature_id': feature.get('id'),
                'expected_test_cases': test_suite_content.get('expected_test_cases', 0),
                'priority': user_story.get('priority', 'Medium'),
                'status': 'Active'
            }
            
            self.logger.info(f"Successfully created test suite for user story: {user_story_title}")
            
            return {
                'success': True,
                'test_suite': test_suite
            }
            
        except Exception as e:
            self.logger.error(f"Error creating test suite for user story {user_story.get('title', 'Unknown')}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_test_suite_content(self, 
                                   feature: Dict[str, Any],
                                   user_story: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate test suite content using LLM."""
        try:
            # Prepare context for LLM
            suite_context = {
                'feature_title': feature.get('title', ''),
                'feature_description': feature.get('description', ''),
                'user_story_title': user_story.get('title', ''),
                'user_story_description': user_story.get('description', ''),
                'acceptance_criteria': user_story.get('acceptance_criteria', []),
                'priority': user_story.get('priority', 'Medium'),
                'project_context': context.get('project_context', {}),
                'domain': context.get('project_context', {}).get('domain', ''),
                'project_type': context.get('project_context', {}).get('project_type', '')
            }
            
            # Create test suite generation prompt
            prompt = self._build_test_suite_prompt(suite_context)
            
            # Call LLM to generate test suite
            response = self.llm_client.generate_response(prompt, max_tokens=1500)
            
            if not response:
                self.logger.error("LLM returned empty response for test suite generation")
                return None
            
            # Parse the response to extract test suite components
            test_suite_content = self._parse_test_suite_response(response)
            
            return test_suite_content
            
        except Exception as e:
            self.logger.error(f"Error generating test suite content: {e}")
            return None
    
    def _build_test_suite_prompt(self, suite_context: Dict[str, Any]) -> str:
        """Build the prompt for test suite generation."""
        acceptance_criteria_text = ""
        for i, criteria in enumerate(suite_context.get('acceptance_criteria', []), 1):
            acceptance_criteria_text += f"{i}. {criteria}\n"
        
        prompt = f"""
You are a Senior Test Analyst creating a test suite for a specific user story.

CONTEXT:
Feature: {suite_context.get('feature_title', '')}
Feature Description: {suite_context.get('feature_description', '')}

User Story: {suite_context.get('user_story_title', '')}
User Story Description: {suite_context.get('user_story_description', '')}
Priority: {suite_context.get('priority', 'Medium')}

Domain: {suite_context.get('domain', '')}
Project Type: {suite_context.get('project_type', '')}

ACCEPTANCE CRITERIA:
{acceptance_criteria_text}

Create a comprehensive test suite that includes:

1. DESCRIPTION: Clear description of what this test suite will verify
2. TEST_CATEGORIES: Types of testing to be performed (e.g., functional, boundary, negative)
3. TEST_OBJECTIVES: Specific objectives this test suite aims to achieve
4. PREREQUISITES: What needs to be in place before running these tests
5. TEST_DATA_REQUIREMENTS: Specific data needed for testing
6. EXPECTED_TEST_CASES: Estimated number of test cases needed

Format your response as JSON with the following structure:
{{
    "description": "...",
    "test_categories": ["...", "..."],
    "test_objectives": ["...", "..."],
    "prerequisites": ["...", "..."],
    "test_data_requirements": ["...", "..."],
    "expected_test_cases": number
}}

Focus on comprehensive coverage of the acceptance criteria while ensuring the test suite is practical and executable.
The test suite should validate all aspects of the user story from the perspective of the {suite_context.get('domain', '')} domain.
"""
        return prompt
    
    def _parse_test_suite_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract test suite components."""
        try:
            # Try to extract JSON from response
            parsed_content = self._extract_json_from_response(response)
            
            if parsed_content:
                return parsed_content
            
            # If JSON extraction fails, create a basic structure
            self.logger.warning("Could not parse JSON from test suite response, creating basic structure")
            
            return {
                'description': f"Test suite generated from response: {response[:300]}...",
                'test_categories': ['Functional Testing', 'Boundary Testing', 'Negative Testing'],
                'test_objectives': [
                    'Verify user story functionality',
                    'Validate acceptance criteria',
                    'Ensure error handling'
                ],
                'prerequisites': [
                    'Test environment available',
                    'Required test data prepared',
                    'Dependencies resolved'
                ],
                'test_data_requirements': [
                    'Valid user accounts',
                    'Sample data sets',
                    'Error condition data'
                ],
                'expected_test_cases': 5
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing test suite response: {e}")
            return {}
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON content from LLM response."""
        import json
        import re
        
        try:
            # First try to parse the entire response as JSON
            return json.loads(response)
        except:
            pass
        
        try:
            # Look for JSON blocks in markdown
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except:
            pass
        
        try:
            # Look for JSON content between curly braces
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        
        return None
    
    def organize_test_cases(self, 
                           test_suite: Dict[str, Any], 
                           test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize test cases within the test suite structure."""
        try:
            # Group test cases by category
            categorized_cases = {}
            
            for test_case in test_cases:
                category = test_case.get('category', 'General')
                if category not in categorized_cases:
                    categorized_cases[category] = []
                categorized_cases[category].append(test_case)
            
            # Update test suite with organized test cases
            test_suite['test_case_organization'] = categorized_cases
            test_suite['total_test_cases'] = len(test_cases)
            
            return {
                'success': True,
                'organized_suite': test_suite
            }
            
        except Exception as e:
            self.logger.error(f"Error organizing test cases: {e}")
            return {
                'success': False,
                'error': str(e)
            }
