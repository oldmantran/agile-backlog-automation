"""
Test Plan Agent - Specialized agent for creating test plans at the feature level
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import BaseAgent


class TestPlanAgent(BaseAgent):
    """
    Specialized agent for creating test plans for features.
    
    Responsibilities:
    - Analyze feature requirements and user stories
    - Create comprehensive test plans
    - Determine test strategy and approach
    - Set area paths and iterations
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Test plan specific settings
        self.default_test_approach = "Risk-based testing with automated and manual coverage"
        self.test_types = [
            "Functional Testing",
            "Integration Testing", 
            "User Acceptance Testing",
            "Performance Testing",
            "Security Testing"
        ]
    
    def create_test_plan(self, 
                        epic: Dict[str, Any],
                        feature: Dict[str, Any], 
                        context: Dict[str, Any],
                        area_path: str) -> Dict[str, Any]:
        """
        Create a comprehensive test plan for a feature.
        
        Args:
            epic: Parent epic information
            feature: Feature to create test plan for
            context: Project context and configuration
            area_path: Azure DevOps area path
            
        Returns:
            Dictionary with test plan information and success status
        """
        try:
            feature_title = feature.get('title', 'Unknown Feature')
            self.logger.info(f"Creating test plan for feature: {feature_title}")
            
            # Generate test plan content using LLM
            test_plan_content = self._generate_test_plan_content(epic, feature, context)
            
            if not test_plan_content:
                return {
                    'success': False,
                    'error': 'Failed to generate test plan content'
                }
            
            # Create test plan structure
            test_plan = {
                'name': f"Test Plan - {feature_title}",
                'description': test_plan_content.get('description', ''),
                'area_path': area_path,
                'iteration_path': area_path,  # Use same as area path for now
                'test_approach': test_plan_content.get('test_approach', self.default_test_approach),
                'test_types': test_plan_content.get('test_types', self.test_types),
                'entry_criteria': test_plan_content.get('entry_criteria', []),
                'exit_criteria': test_plan_content.get('exit_criteria', []),
                'test_environment': test_plan_content.get('test_environment', {}),
                'risks_and_mitigations': test_plan_content.get('risks_and_mitigations', []),
                'feature_id': feature.get('id'),
                'epic_id': epic.get('id'),
                'user_stories_count': len(feature.get('user_stories', [])),
                'status': 'Active'
            }
            
            self.logger.info(f"Successfully created test plan for feature: {feature_title}")
            
            return {
                'success': True,
                'test_plan': test_plan
            }
            
        except Exception as e:
            self.logger.error(f"Error creating test plan for feature {feature.get('title', 'Unknown')}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_test_plan_content(self, 
                                   epic: Dict[str, Any],
                                   feature: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate test plan content using LLM."""
        try:
            # Prepare context for LLM
            feature_context = {
                'epic_title': epic.get('title', ''),
                'epic_description': epic.get('description', ''),
                'feature_title': feature.get('title', ''),
                'feature_description': feature.get('description', ''),
                'user_stories': feature.get('user_stories', []),
                'project_context': context.get('project_context', {}),
                'domain': context.get('project_context', {}).get('domain', ''),
                'project_type': context.get('project_context', {}).get('project_type', '')
            }
            
            # Create test plan generation prompt
            prompt = self._build_test_plan_prompt(feature_context)
            
            # Call LLM to generate test plan
            response = self.llm_client.generate_response(prompt, max_tokens=2000)
            
            if not response:
                self.logger.error("LLM returned empty response for test plan generation")
                return None
            
            # Parse the response to extract test plan components
            test_plan_content = self._parse_test_plan_response(response)
            
            return test_plan_content
            
        except Exception as e:
            self.logger.error(f"Error generating test plan content: {e}")
            return None
    
    def _build_test_plan_prompt(self, feature_context: Dict[str, Any]) -> str:
        """Build the prompt for test plan generation."""
        user_stories_text = ""
        for i, story in enumerate(feature_context.get('user_stories', []), 1):
            user_stories_text += f"{i}. {story.get('title', '')}\n"
            if story.get('description'):
                user_stories_text += f"   Description: {story.get('description')}\n"
            if story.get('acceptance_criteria'):
                user_stories_text += f"   Acceptance Criteria: {', '.join(story.get('acceptance_criteria', []))}\n"
            user_stories_text += "\n"
        
        prompt = f"""
You are a Senior Test Manager creating a comprehensive test plan for a software feature.

CONTEXT:
Epic: {feature_context.get('epic_title', '')}
Epic Description: {feature_context.get('epic_description', '')}

Feature: {feature_context.get('feature_title', '')}
Feature Description: {feature_context.get('feature_description', '')}

Domain: {feature_context.get('domain', '')}
Project Type: {feature_context.get('project_type', '')}

USER STORIES:
{user_stories_text}

Create a detailed test plan that includes:

1. DESCRIPTION: A comprehensive description of what will be tested and why
2. TEST_APPROACH: Overall testing strategy and methodology  
3. TEST_TYPES: Specific types of testing to be performed
4. ENTRY_CRITERIA: Conditions that must be met before testing can begin
5. EXIT_CRITERIA: Conditions that must be met before testing is complete
6. TEST_ENVIRONMENT: Description of required test environment and data
7. RISKS_AND_MITIGATIONS: Potential risks and how to mitigate them

Format your response as JSON with the following structure:
{{
    "description": "...",
    "test_approach": "...",
    "test_types": ["...", "..."],
    "entry_criteria": ["...", "..."],
    "exit_criteria": ["...", "..."],
    "test_environment": {{
        "description": "...",
        "data_requirements": "...",
        "tools_required": ["...", "..."]
    }},
    "risks_and_mitigations": [
        {{
            "risk": "...",
            "impact": "...",
            "mitigation": "..."
        }}
    ]
}}

Ensure the test plan is thorough, realistic, and aligned with industry best practices for the {feature_context.get('domain', '')} domain.
"""
        return prompt
    
    def _parse_test_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract test plan components."""
        try:
            # Try to extract JSON from response
            parsed_content = self._extract_json_from_response(response)
            
            if parsed_content:
                return parsed_content
            
            # If JSON extraction fails, create a basic structure
            self.logger.warning("Could not parse JSON from test plan response, creating basic structure")
            
            return {
                'description': f"Test plan generated from response: {response[:500]}...",
                'test_approach': self.default_test_approach,
                'test_types': self.test_types,
                'entry_criteria': [
                    "Feature development completed",
                    "Test environment prepared",
                    "Test data available"
                ],
                'exit_criteria': [
                    "All test cases executed",
                    "Critical defects resolved",
                    "Acceptance criteria verified"
                ],
                'test_environment': {
                    'description': 'Standard test environment with appropriate test data',
                    'data_requirements': 'Representative test data covering normal and edge cases',
                    'tools_required': ['Test management tool', 'Automation framework']
                },
                'risks_and_mitigations': [
                    {
                        'risk': 'Test environment unavailability',
                        'impact': 'High',
                        'mitigation': 'Prepare backup environment and early validation'
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing test plan response: {e}")
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
