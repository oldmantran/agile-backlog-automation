"""
Test Plan Agent - Specialized agent for creating test plans at the feature level
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import Agent


class TestPlanAgent(Agent):
    """
    Specialized agent for creating test plans for features.
    
    Responsibilities:
    - Analyze feature requirements and user stories
    - Create comprehensive test plans
    - Determine test strategy and approach
    - Set area paths and iterations
    """
    
    def __init__(self, config, user_id: str = None, parent_agent_name: str = None):
        # Use parent agent name for LLM config if provided, otherwise use own name
        agent_name = parent_agent_name or "test_plan_agent"
        super().__init__(agent_name, config, user_id)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Get timeout from QA lead agent sub-agents config
        qa_config = config.get_setting('agents', 'qa_lead_agent') or {}
        sub_agents_config = qa_config.get('sub_agents', {})
        test_plan_config = sub_agents_config.get('test_plan_agent', {})
        self.timeout_seconds = test_plan_config.get('timeout_seconds', 120)
        self.logger.info(f"TestPlanAgent initialized with timeout: {self.timeout_seconds}s")
        
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
            
            # Debug logging to understand what's happening
            self.logger.info(f"Test plan content generated: {test_plan_content is not None}")
            if test_plan_content:
                self.logger.info(f"Test plan content keys: {list(test_plan_content.keys())}")
            
            if not test_plan_content:
                self.logger.error("Failed to generate test plan content - this should not happen with fallback mechanisms")
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
            # Validate required data exists
            if not epic.get('title') or not epic.get('description'):
                self.logger.error(f"Epic missing required fields: title={epic.get('title')}, description={epic.get('description')}")
                return None
                
            if not feature.get('title') or not feature.get('description'):
                self.logger.error(f"Feature missing required fields: title={feature.get('title')}, description={feature.get('description')}")
                return None
            
            # Prepare context for LLM using the proper template system
            template_context = {
                'project_name': context.get('project_name', 'Unknown Project'),
                'domain': context.get('domain', 'dynamic'),
                'epic_title': epic['title'],
                'epic_description': epic['description'],
                'feature_title': feature['title'],
                'feature_description': feature['description'],
                'user_stories': feature.get('user_stories', []),
                'project_context': context.get('project_context', {}),
                'project_type': context.get('project_context', {}).get('project_type', '')
            }
            
            # Build user stories text for the prompt
            user_stories_text = ""
            for i, story in enumerate(feature.get('user_stories', []), 1):
                user_stories_text += f"{i}. {story.get('title', '')}\n"
                if story.get('description'):
                    user_stories_text += f"   Description: {story.get('description')}\n"
                if story.get('acceptance_criteria'):
                    user_stories_text += f"   Acceptance Criteria: {', '.join(story.get('acceptance_criteria', []))}\n"
                user_stories_text += "\n"
            
            # Add user stories to context
            template_context['user_stories_text'] = user_stories_text
            
            # Debug: Log key template variables
            self.logger.debug(f"Template context for {feature.get('title', 'Unknown')}: epic_title='{template_context.get('epic_title')}', feature_title='{template_context.get('feature_title')}'")
            
            # Call LLM to generate test plan with timeout handling
            # The run() method will internally call get_prompt(template_context)
            try:
                self.logger.info(f"Calling LLM for test plan generation for feature: {feature.get('title', 'Unknown')}")
                user_input = f"Create a comprehensive test plan for the feature: {feature.get('title', 'Unknown Feature')}"
                response = self.run(user_input, template_context)
                self.logger.info(f"LLM response received, length: {len(response) if response else 0}")
            except Exception as e:
                self.logger.warning(f"LLM call failed for test plan generation: {e}")
                self.logger.warning(f"Exception type: {type(e).__name__}")
                # Skip this item instead of creating fallback
                return None
            
            if not response:
                self.logger.warning("LLM returned empty response for test plan generation")
                # Skip this item instead of creating fallback
                return None
            
            # Parse the response to extract test plan components
            test_plan_content = self._parse_test_plan_response(response)
            
            # If parsing failed, skip this item
            if not test_plan_content:
                self.logger.warning("Failed to parse test plan response, skipping this feature")
                return None
            
            return test_plan_content
            
        except Exception as e:
            self.logger.error(f"Error generating test plan content: {e}")
            # Skip this item instead of creating fallback
            return None
    
    # Fallback methods removed - we now skip items instead of creating generic fallbacks
    
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
            
            if parsed_content and isinstance(parsed_content, dict):
                # Validate that we have the minimum required fields
                required_fields = ['description', 'test_approach', 'test_types']
                if all(field in parsed_content for field in required_fields):
                    self.logger.info("Successfully parsed valid test plan from LLM response")
                    return parsed_content
                else:
                    self.logger.warning("Parsed JSON missing required fields, using fallback")
            
            # If JSON extraction fails or is invalid, return None to skip
            self.logger.error("Could not parse valid JSON from test plan response, skipping test plan creation")
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing test plan response: {e}")
            # Skip test plan creation on parsing error
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON content from LLM response with improved parsing."""
        import json
        import re
        
        if not response or not isinstance(response, str):
            return None
        
        # Clean the response
        cleaned_response = response.strip()
        
        # Method 1: Try to parse the entire response as JSON
        try:
            return json.loads(cleaned_response)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Method 2: Look for JSON blocks in markdown
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', cleaned_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Method 3: Look for JSON blocks without language specifier
        try:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', cleaned_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Method 4: Look for JSON content between curly braces (more specific)
        try:
            # Find the outermost JSON object
            brace_count = 0
            start_idx = -1
            for i, char in enumerate(cleaned_response):
                if char == '{':
                    if brace_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        json_str = cleaned_response[start_idx:i+1]
                        return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
        
        # Method 5: Try to find JSON after common prefixes
        try:
            patterns = [
                r'response:\s*(\{.*\})',
                r'json:\s*(\{.*\})',
                r'result:\s*(\{.*\})',
                r'output:\s*(\{.*\})'
            ]
            for pattern in patterns:
                match = re.search(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
                if match:
                    return json.loads(match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return None
