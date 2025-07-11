"""
Test Case Agent - Specialized agent for creating individual test cases
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import BaseAgent


class TestCaseAgent(BaseAgent):
    """
    Specialized agent for creating individual test cases.
    
    Responsibilities:
    - Generate detailed test cases from user stories
    - Format test cases in Gherkin or traditional format
    - Create positive, negative, and boundary test cases
    - Link test cases to appropriate test suites
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Test case specific settings
        self.test_case_format = config.get('test_case_format', 'gherkin')
        self.case_types = ['positive', 'negative', 'boundary', 'integration']
        self.max_cases_per_story = 10
    
    def create_test_cases(self, 
                         feature: Dict[str, Any],
                         user_story: Dict[str, Any], 
                         context: Dict[str, Any],
                         area_path: str) -> Dict[str, Any]:
        """
        Create comprehensive test cases for a user story.
        
        Args:
            feature: Parent feature information
            user_story: User story to create test cases for
            context: Project context and configuration
            area_path: Azure DevOps area path
            
        Returns:
            Dictionary with test cases and success status
        """
        try:
            user_story_title = user_story.get('title', 'Unknown User Story')
            self.logger.info(f"Creating test cases for user story: {user_story_title}")
            
            # Generate test cases using LLM
            test_cases_content = self._generate_test_cases_content(feature, user_story, context)
            
            if not test_cases_content:
                return {
                    'success': False,
                    'error': 'Failed to generate test cases content'
                }
            
            # Process and format test cases
            formatted_test_cases = self._format_test_cases(test_cases_content, user_story, area_path)
            
            self.logger.info(f"Successfully created {len(formatted_test_cases)} test cases for user story: {user_story_title}")
            
            return {
                'success': True,
                'test_cases': formatted_test_cases,
                'cases_created': len(formatted_test_cases)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating test cases for user story {user_story.get('title', 'Unknown')}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_test_cases_content(self, 
                                   feature: Dict[str, Any],
                                   user_story: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Generate test cases content using LLM."""
        try:
            # Prepare context for LLM
            test_context = {
                'feature_title': feature.get('title', ''),
                'feature_description': feature.get('description', ''),
                'user_story_title': user_story.get('title', ''),
                'user_story_description': user_story.get('description', ''),
                'acceptance_criteria': user_story.get('acceptance_criteria', []),
                'priority': user_story.get('priority', 'Medium'),
                'project_context': context.get('project_context', {}),
                'domain': context.get('project_context', {}).get('domain', ''),
                'project_type': context.get('project_context', {}).get('project_type', ''),
                'test_case_format': self.test_case_format
            }
            
            # Create test case generation prompt
            prompt = self._build_test_cases_prompt(test_context)
            
            # Call LLM to generate test cases
            response = self.llm_client.generate_response(prompt, max_tokens=3000)
            
            if not response:
                self.logger.error("LLM returned empty response for test cases generation")
                return None
            
            # Parse the response to extract test cases
            test_cases = self._parse_test_cases_response(response)
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"Error generating test cases content: {e}")
            return None
    
    def _build_test_cases_prompt(self, test_context: Dict[str, Any]) -> str:
        """Build the prompt for test cases generation."""
        acceptance_criteria_text = ""
        for i, criteria in enumerate(test_context.get('acceptance_criteria', []), 1):
            acceptance_criteria_text += f"{i}. {criteria}\n"
        
        format_instructions = ""
        if test_context.get('test_case_format') == 'gherkin':
            format_instructions = """
Use Gherkin format (Given-When-Then) for test steps:
- Given: Initial state/preconditions
- When: Action performed
- Then: Expected result
- And: Additional conditions or actions
"""
        else:
            format_instructions = """
Use traditional format with:
- Test Steps: Clear numbered steps
- Expected Results: Expected outcome for each step
"""
        
        prompt = f"""
You are a Senior QA Engineer creating comprehensive test cases for a user story.

CONTEXT:
Feature: {test_context.get('feature_title', '')}
Feature Description: {test_context.get('feature_description', '')}

User Story: {test_context.get('user_story_title', '')}
User Story Description: {test_context.get('user_story_description', '')}
Priority: {test_context.get('priority', 'Medium')}

Domain: {test_context.get('domain', '')}
Project Type: {test_context.get('project_type', '')}

ACCEPTANCE CRITERIA:
{acceptance_criteria_text}

Create comprehensive test cases that cover:
1. POSITIVE TEST CASES: Happy path scenarios
2. NEGATIVE TEST CASES: Error conditions and invalid inputs
3. BOUNDARY TEST CASES: Edge cases and limits
4. INTEGRATION TEST CASES: Interaction with other components

{format_instructions}

For each test case, include:
- title: Clear, descriptive title
- description: Brief description of what is being tested
- category: Type of test (positive, negative, boundary, integration)
- priority: Test case priority (High, Medium, Low)
- preconditions: What must be true before executing
- test_steps: Detailed steps to execute
- expected_result: Expected outcome
- test_data: Any specific data needed

Format your response as JSON array:
[
    {{
        "title": "...",
        "description": "...",
        "category": "positive|negative|boundary|integration",
        "priority": "High|Medium|Low",
        "preconditions": ["...", "..."],
        "test_steps": ["...", "..."],
        "expected_result": "...",
        "test_data": ["...", "..."]
    }}
]

Create 3-8 test cases that thoroughly validate the user story while being practical to execute.
Ensure coverage of all acceptance criteria and consider real-world scenarios in the {test_context.get('domain', '')} domain.
"""
        return prompt
    
    def _parse_test_cases_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract test cases."""
        try:
            # Try to extract JSON from response
            parsed_content = self._extract_json_from_response(response)
            
            if parsed_content and isinstance(parsed_content, list):
                return parsed_content
            elif parsed_content and isinstance(parsed_content, dict):
                # If single test case returned as dict, wrap in list
                return [parsed_content]
            
            # If JSON extraction fails, create basic test cases
            self.logger.warning("Could not parse JSON from test cases response, creating basic test cases")
            
            return self._create_fallback_test_cases()
            
        except Exception as e:
            self.logger.error(f"Error parsing test cases response: {e}")
            return self._create_fallback_test_cases()
    
    def _create_fallback_test_cases(self) -> List[Dict[str, Any]]:
        """Create fallback test cases when parsing fails."""
        return [
            {
                'title': 'Verify basic functionality',
                'description': 'Test the main functionality of the user story',
                'category': 'positive',
                'priority': 'High',
                'preconditions': ['System is available', 'User is authenticated'],
                'test_steps': [
                    'Navigate to the feature',
                    'Perform the main action',
                    'Verify the result'
                ],
                'expected_result': 'Feature works as expected',
                'test_data': ['Valid user account', 'Sample data']
            },
            {
                'title': 'Verify error handling',
                'description': 'Test error conditions and validation',
                'category': 'negative',
                'priority': 'Medium',
                'preconditions': ['System is available'],
                'test_steps': [
                    'Navigate to the feature',
                    'Provide invalid input',
                    'Verify error message'
                ],
                'expected_result': 'Appropriate error message displayed',
                'test_data': ['Invalid input data']
            }
        ]
    
    def _format_test_cases(self, 
                          test_cases: List[Dict[str, Any]], 
                          user_story: Dict[str, Any],
                          area_path: str) -> List[Dict[str, Any]]:
        """Format test cases with additional metadata."""
        formatted_cases = []
        
        for i, test_case in enumerate(test_cases):
            try:
                formatted_case = {
                    'id': f"TC_{user_story.get('id', 'US')}_{i+1:03d}",
                    'title': test_case.get('title', f'Test Case {i+1}'),
                    'description': test_case.get('description', ''),
                    'category': test_case.get('category', 'positive'),
                    'priority': test_case.get('priority', 'Medium'),
                    'area_path': area_path,
                    'user_story_id': user_story.get('id'),
                    'preconditions': test_case.get('preconditions', []),
                    'test_steps': self._format_test_steps(test_case.get('test_steps', [])),
                    'expected_result': test_case.get('expected_result', ''),
                    'test_data': test_case.get('test_data', []),
                    'status': 'Active',
                    'automation_candidate': self._assess_automation_candidate(test_case)
                }
                
                formatted_cases.append(formatted_case)
                
            except Exception as e:
                self.logger.error(f"Error formatting test case {i+1}: {e}")
                continue
        
        return formatted_cases
    
    def _format_test_steps(self, steps: List[str]) -> List[Dict[str, Any]]:
        """Format test steps with proper structure."""
        formatted_steps = []
        
        for i, step in enumerate(steps):
            formatted_step = {
                'step_number': i + 1,
                'action': step,
                'expected_result': ''  # Can be enhanced later
            }
            formatted_steps.append(formatted_step)
        
        return formatted_steps
    
    def _assess_automation_candidate(self, test_case: Dict[str, Any]) -> bool:
        """Assess if test case is a good candidate for automation."""
        category = test_case.get('category', '').lower()
        priority = test_case.get('priority', '').lower()
        
        # Simple heuristics for automation assessment
        if category in ['positive', 'boundary'] and priority in ['high', 'medium']:
            return True
        
        # Check if test steps suggest UI automation challenges
        steps = test_case.get('test_steps', [])
        ui_intensive_keywords = ['click', 'navigate', 'visual', 'display', 'appearance']
        
        steps_text = ' '.join(steps).lower()
        ui_intensive = any(keyword in steps_text for keyword in ui_intensive_keywords)
        
        return not ui_intensive  # Less UI-intensive tests are better automation candidates
    
    def _extract_json_from_response(self, response: str) -> Optional[Any]:
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
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except:
            pass
        
        try:
            # Look for JSON array content
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        
        try:
            # Look for JSON object content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        
        return None
