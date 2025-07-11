"""
Test Case Agent - Specialized agent for creating individual test cases
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import Agent


class TestCaseAgent(Agent):
    """
    Specialized agent for creating individual test cases.
    
    Responsibilities:
    - Generate detailed test cases from user stories
    - Format test cases in Gherkin or traditional format
    - Create positive, negative, and boundary test cases
    - Link test cases to appropriate test suites
    """
    
    def __init__(self, config):
        super().__init__("test_case_agent", config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Test case specific settings from configuration
        qa_config = config.get_setting('agents', 'qa_lead_agent') or {}
        sub_agents_config = qa_config.get('sub_agents', {})
        test_case_config = sub_agents_config.get('test_case_agent', {})
        
        self.test_case_format = test_case_config.get('test_case_format', 'gherkin')
        self.case_types = ['positive', 'negative', 'boundary', 'integration']
        self.max_cases_per_story = 10
    
    def create_test_cases(self, 
                         feature: Dict[str, Any],
                         user_story: Dict[str, Any], 
                         context: Dict[str, Any],
                         area_path: str) -> Dict[str, Any]:
        """
        Create comprehensive test cases for a user story using decomposed prompts.
        
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
            
            all_test_cases = []
            
            # Create test cases by category using smaller, focused prompts
            categories = ['positive', 'negative', 'boundary', 'integration']
            
            for category in categories:
                try:
                    category_cases = self._generate_test_cases_by_category(
                        feature, user_story, context, category
                    )
                    if category_cases:
                        all_test_cases.extend(category_cases)
                        self.logger.info(f"Generated {len(category_cases)} {category} test cases")
                except Exception as e:
                    self.logger.warning(f"Failed to generate {category} test cases: {e}")
                    # Continue with other categories
            
            if not all_test_cases:
                return {
                    'success': False,
                    'error': 'Failed to generate any test cases'
                }
            
            # Format test cases with area path and metadata
            formatted_test_cases = self._format_test_cases(all_test_cases, user_story, area_path)
            
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
            response = self.run(prompt)
            
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
    
    def _generate_test_cases_by_category(self, 
                                       feature: Dict[str, Any],
                                       user_story: Dict[str, Any], 
                                       context: Dict[str, Any],
                                       category: str) -> Optional[List[Dict[str, Any]]]:
        """Generate test cases for a specific category using a focused prompt."""
        try:
            # Use faster strategies for complex categories
            if category == 'boundary':
                return self._generate_fast_boundary_cases(feature, user_story, context)
            
            # Create a smaller, focused prompt for this category
            prompt = self._build_category_prompt(feature, user_story, context, category)
            
            # Call LLM with smaller prompt
            response = self.run(prompt)
            
            if not response:
                self.logger.warning(f"LLM returned empty response for {category} test cases")
                return None
            
            # Parse the response
            test_cases = self._parse_simple_test_cases_response(response, category)
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"Error generating {category} test cases: {e}")
            return None
    
    def _build_category_prompt(self, 
                              feature: Dict[str, Any],
                              user_story: Dict[str, Any], 
                              context: Dict[str, Any],
                              category: str) -> str:
        """Build a focused prompt for a specific test case category."""
        
        acceptance_criteria = user_story.get('acceptance_criteria', [])
        acceptance_criteria_text = "\n".join(f"{i+1}. {criteria}" for i, criteria in enumerate(acceptance_criteria))
        
        category_descriptions = {
            'positive': 'Happy path scenarios where everything works as expected',
            'negative': 'Error conditions, invalid inputs, and edge cases that should fail gracefully',
            'boundary': 'Simple edge cases: empty inputs, null values, minimum/maximum limits',
            'integration': 'Interaction with other components, APIs, or system dependencies'
        }
        
        category_examples = {
            'positive': 'Valid user inputs, successful workflows, expected outcomes',
            'negative': 'Invalid data, missing fields, unauthorized access, network failures',
            'boundary': 'Empty fields, null values, very long inputs, zero values, first/last items',
            'integration': 'API calls, database interactions, third-party service communication'
        }
        
        prompt = f"""You are a QA Engineer creating {category} test cases for a user story.

CONTEXT:
Feature: {feature.get('title', '')}
User Story: {user_story.get('title', '')}
Domain: {context.get('project_context', {}).get('domain', '')}

ACCEPTANCE CRITERIA:
{acceptance_criteria_text}

CATEGORY: {category.upper()} TEST CASES
Focus: {category_descriptions.get(category, '')}
Examples: {category_examples.get(category, '')}

Create 1-3 {category} test cases in simple JSON format:
[
    {{
        "title": "Clear, descriptive test title",
        "steps": ["Step 1: Action", "Step 2: Action", "Step 3: Verify result"],
        "expected": "Expected outcome",
        "priority": "High|Medium|Low"
    }}
]

Keep it simple and focused only on {category} scenarios. Each test should be executable and clearly validate the acceptance criteria."""
        
        return prompt
    
    def _parse_simple_test_cases_response(self, response: str, category: str) -> List[Dict[str, Any]]:
        """Parse simplified test case responses for faster generation."""
        try:
            # Clean the response
            clean_response = self._extract_json_from_response(response)
            
            if isinstance(clean_response, list):
                test_cases = []
                for item in clean_response:
                    if isinstance(item, dict):
                        # Ensure all required fields with defaults
                        test_case = {
                            'title': item.get('title', f'{category.title()} Test Case'),
                            'steps': item.get('steps', ['Execute test']),
                            'expected': item.get('expected', 'Expected behavior occurs'),
                            'priority': item.get('priority', 'Medium'),
                            'type': category
                        }
                        test_cases.append(test_case)
                
                return test_cases
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error parsing simplified test cases response: {e}")
            return []
    
    def _generate_boundary_cases_optimized(self, 
                                          feature: Dict[str, Any],
                                          user_story: Dict[str, Any], 
                                          context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Generate boundary test cases using an optimized, template-based approach."""
        try:
            # For simple cases like button clicks, use predefined boundary scenarios
            acceptance_criteria = user_story.get('acceptance_criteria', [])
            
            # Quick boundary test templates for common UI interactions
            boundary_templates = [
                {
                    "title": "Test button click at page load boundary",
                    "steps": ["Navigate to test page", "Click button immediately when page starts loading", "Verify response"],
                    "expected": "System handles early click gracefully (button disabled or loading state shown)",
                    "priority": "Medium"
                },
                {
                    "title": "Test rapid multiple button clicks (stress boundary)",
                    "steps": ["Navigate to test page", "Click test button rapidly 10 times in 1 second", "Verify only one success message appears"],
                    "expected": "Single success message displayed, subsequent clicks ignored or handled properly",
                    "priority": "Medium"
                }
            ]
            
            # Convert templates to full test case format
            formatted_cases = []
            for i, template in enumerate(boundary_templates):
                formatted_case = {
                    'title': template['title'],
                    'description': 'Boundary test case for user story validation',
                    'category': 'boundary',
                    'priority': template['priority'],
                    'preconditions': ['User story implementation is complete'],
                    'test_steps': template['steps'],
                    'expected_result': template['expected'],
                    'test_data': ['Standard test data']
                }
                formatted_cases.append(formatted_case)
            
            self.logger.info(f"Generated {len(formatted_cases)} boundary test cases using templates")
            return formatted_cases
            
        except Exception as e:
            self.logger.error(f"Error generating optimized boundary test cases: {e}")
            # Fallback to normal prompt-based generation
            return self._generate_boundary_cases_fallback(feature, user_story, context)
    
    def _generate_boundary_cases_fallback(self, 
                                        feature: Dict[str, Any],
                                        user_story: Dict[str, Any], 
                                        context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fallback method using a simplified boundary prompt."""
        try:
            # Ultra-simplified boundary prompt
            prompt = f"""Create 2 boundary test cases for: "{user_story.get('title', '')}"

Acceptance criteria: {', '.join(user_story.get('acceptance_criteria', []))}

JSON format:
[{{"title": "Test at minimum boundary", "steps": ["Step 1", "Step 2"], "expected": "Result", "priority": "Medium"}}]

Focus only on timing boundaries and input limits. Keep responses under 200 tokens."""
            
            response = self.run(prompt)
            
            if not response:
                return []
            
            return self._parse_simple_test_cases_response(response, 'boundary')
            
        except Exception as e:
            self.logger.error(f"Error in boundary fallback generation: {e}")
            return []
    
    def _generate_fast_boundary_cases(self, 
                                     feature: Dict[str, Any],
                                     user_story: Dict[str, Any], 
                                     context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Generate boundary test cases using a simplified, faster approach."""
        try:
            # Ultra-simplified prompt for boundary cases
            prompt = f"""Generate 2 boundary test cases for: "{user_story.get('title', '')}"

Acceptance Criteria: {', '.join(user_story.get('acceptance_criteria', []))}

Focus on:
- Empty/null inputs
- Maximum limits
- Timing boundaries

JSON format:
[{{"title": "...", "steps": ["...", "..."], "expected": "...", "priority": "Medium"}}]

Keep it minimal and fast."""

            # Call LLM with simplified prompt
            response = self.run(prompt)
            
            if not response:
                self.logger.warning("LLM returned empty response for fast boundary test cases")
                return None
            
            # Parse simplified response
            test_cases = self._parse_simple_test_cases_response(response, 'boundary')
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"Error generating fast boundary test cases: {e}")
            return None
