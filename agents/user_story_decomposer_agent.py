import json
import re
import threading
from typing import Optional
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator
from utils.json_extractor import JSONExtractor
from utils.user_story_quality_assessor import UserStoryQualityAssessor

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

class UserStoryDecomposerAgent(Agent):
    """
    Agent responsible for decomposing features into user stories.
    Focuses on user journeys, acceptance criteria, and implementation details.
    """
    
    def __init__(self, config: Config):
        super().__init__("user_story_decomposer", config)
        # Initialize quality validator with current configuration
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)
        self.user_story_quality_assessor = UserStoryQualityAssessor()
        self.max_quality_retries = 3  # Maximum attempts to achieve EXCELLENT rating

    def decompose_feature_to_user_stories(self, feature: dict, context: dict = None, max_user_stories: int = 5) -> list[dict]:
        """Decompose a feature into user stories."""
        # Remove redundant print - supervisor already logs this
        # print(f"📝 [UserStoryDecomposerAgent] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Get the feature description and title
        feature_description = feature.get('description', '')
        feature_title = feature.get('title', 'Feature')
        
        # Extract full context for cascading
        product_vision = context.get('product_vision', '') if context else ''
        epic_context = context.get('epic_context', '') if context else ''
        
        # Build context for prompt template - CASCADE FULL CONTEXT
        prompt_context = {
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'team_velocity': context.get('team_velocity', '20-30 points per sprint') if context else '20-30 points per sprint',
            'product_vision': product_vision,  # CASCADE PRODUCT VISION
            'epic_context': epic_context  # CASCADE EPIC CONTEXT
        }
        
        user_input = f"""
Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Priority: {feature.get('priority', 'Medium')}
Estimated Story Points: {feature.get('estimated_story_points', 'Not specified')}
Business Value: {feature.get('business_value', 'Not specified')}
Dependencies: {feature.get('dependencies', [])}
UI/UX Requirements: {feature.get('ui_ux_requirements', [])}
Edge Cases: {feature.get('edge_cases', [])}
"""
        
        # print(f"📝 [UserStoryDecomposerAgent] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Use configured model with appropriate timeout
        models_to_try = []
        
        if self.model and ("70b" in self.model.lower()):
            # 70B model needs longer timeout
            models_to_try = [(self.model, 180)]
        elif self.model and ("32b" in self.model.lower()):
            # 32B model is actually quite fast - reduced timeout
            models_to_try = [(self.model, 45)]
        elif self.model and ("34b" in self.model.lower()):
            # 34B model needs more time - increased from 60 to 120 seconds
            models_to_try = [(self.model, 120)]
        else:
            # 8B or other models with standard timeout
            models_to_try = [(self.model, 60)]
        
        # Try each model until one succeeds
        response = None
        for model_name, timeout in models_to_try:
            try:
                print(f"Trying {model_name} for user stories with {timeout}s timeout...")
                
                # Temporarily switch to this model
                original_model = self.model
                self.model = model_name
                
                # Update Ollama provider if needed
                if hasattr(self, 'ollama_provider') and self.llm_provider == "ollama":
                    try:
                        from utils.ollama_client import create_ollama_provider
                        self.ollama_provider = create_ollama_provider(preset='balanced')
                    except Exception as e:
                        print(f"WARNING: Failed to switch to {model_name}: {e}")
                        continue
                
                # Use lower temperature for better instruction following
                original_temperature = getattr(self, 'temperature', 0.7)
                self.temperature = 0.3  # Lower temperature for more structured output
                
                # Try normal prompt first
                response = self._run_with_timeout(user_input, prompt_context, timeout=timeout, template_name="user_story_decomposer")
                
                # If response doesn't look like JSON, try strict prompt
                if response and not (response.strip().startswith('[') or response.strip().startswith('{')):
                    print("Response not JSON format, trying strict prompt...")
                    strict_context = {
                        'feature_title': feature.get('title', 'Unknown Feature'),
                        'feature_description': feature.get('description', 'No description')
                    }
                    response = self._run_with_timeout(user_input, strict_context, timeout=timeout, template_name="user_story_decomposer_strict")
                
                # If we still have empty response, try direct call without timeout
                if not response or len(response.strip()) == 0:
                    print("Empty response from timeout method, trying direct call...")
                    try:
                        response = self.run_with_template(user_input, prompt_context, "user_story_decomposer")
                        print(f"Direct call successful, response length: {len(response) if response else 0}")
                    except Exception as e:
                        print(f"Direct call also failed: {e}")
                        response = ""
                
                # Restore original temperature
                self.temperature = original_temperature
                
                # Restore original model
                self.model = original_model
                
                # Only claim success if we actually have a response
                if response and len(response.strip()) > 0:
                    print(f"SUCCESS: Generated user stories using {model_name}")
                    break
                else:
                    print(f"WARNING: {model_name} returned empty response, trying next model...")
                    continue
                
            except TimeoutError:
                print(f"TIMEOUT {model_name} timed out after {timeout}s, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
            except Exception as e:
                print(f"ERROR {model_name} failed: {e}, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
        else:
            # All models failed
            print("ERROR: All models failed for user story generation")
            return []

        # Safety check for None response (timeout case)
        if response is None:
            print("WARNING: Response is None, falling back to text extraction")
            return self._extract_user_stories_from_text("", feature, max_user_stories)

        try:
            # Debug: Show response info
            print(f"[UserStoryDecomposerAgent] Response type: {type(response)}")
            print(f"[UserStoryDecomposerAgent] Response length: {len(response) if response else 0}")
            if response:
                print(f"[UserStoryDecomposerAgent] Raw response (first 500 chars): {response[:500]}")
                print(f"[UserStoryDecomposerAgent] Raw response (last 200 chars): {response[-200:]}")
            else:
                print("[UserStoryDecomposerAgent] Response is empty or None!")
            
            # Extract JSON with robust parsing
            cleaned_response = JSONExtractor.extract_json_from_response(response)
            if cleaned_response:
                try:
                    parsed_preview = json.loads(cleaned_response)
                    if isinstance(parsed_preview, list):
                        print(f"[UserStoryDecomposerAgent] Extracted {len(parsed_preview)} user stories")
                        if parsed_preview:
                            criteria_count = len(parsed_preview[0].get('acceptance_criteria', []))
                            print(f"[UserStoryDecomposerAgent] First story has {criteria_count} acceptance criteria")
                    else:
                        print(f"[UserStoryDecomposerAgent] Cleaned response is not a list: {type(parsed_preview)}")
                except:
                    print(f"[UserStoryDecomposerAgent] Cleaned response (first 200): {cleaned_response[:200]}")
            else:
                print("[UserStoryDecomposerAgent] Cleaned response: None")
            
            # Safety check for empty or invalid JSON
            if not cleaned_response or cleaned_response.strip() == "[]":
                print("WARNING: Empty or invalid JSON response, trying manual extraction")
                # Try one more manual extraction approach
                manual_json = self._manual_json_extraction(response)
                if manual_json:
                    cleaned_response = manual_json
                    print(f"Manual extraction successful: {cleaned_response[:100]}...")
                else:
                    print("WARNING: Manual extraction failed, attempting text extraction")
                    return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            try:
                user_stories = json.loads(cleaned_response)
            except (json.JSONDecodeError, TypeError):
                print("WARNING: Failed to parse JSON response")
                return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            # Safety check for None or empty user_stories
            if not user_stories:
                print("WARNING: Empty or None user_stories after JSON parsing")
                return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            # Additional safety check - ensure user_stories is not None
            if user_stories is None:
                print("WARNING: user_stories is None after JSON parsing")
                return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            # Debug: Check what we actually parsed
            print(f"[DEBUG] user_stories type after JSON parsing: {type(user_stories)}")
            if isinstance(user_stories, list):
                print(f"[DEBUG] List length: {len(user_stories)}")
                for i, item in enumerate(user_stories):
                    print(f"[DEBUG] Item {i} type: {type(item)}")
                    if isinstance(item, dict):
                        print(f"[DEBUG] Item {i} keys: {list(item.keys())}")
                    elif isinstance(item, str):
                        print(f"[DEBUG] Item {i} string value: {item[:100]}...")
                        
            # Handle different response formats
            if isinstance(user_stories, list) and len(user_stories) > 0:
                # Check if these look like user stories or features
                first_item = user_stories[0]
                if first_item is not None and isinstance(first_item, dict) and 'user_stories' in first_item:
                    # This is actually a list of features, extract the user stories
                    print("Response contains features, extracting user stories...")
                    extracted_stories = []
                    for feature_item in user_stories:
                        stories = feature_item.get('user_stories', [])
                        if isinstance(stories, list):
                            for story_text in stories:
                                extracted_stories.append({
                                    'title': f"User Story from {feature_item.get('title', 'Feature')}",
                                    'user_story': story_text,
                                    'description': f"Extracted from feature: {feature_item.get('description', '')}",
                                    'story_points': feature_item.get('estimated_story_points', 5) // len(stories) if stories else 5,
                                    'priority': feature_item.get('priority', 'Medium'),
                                    'acceptance_criteria': []  # Will be populated during enhancement
                                })
                    # Apply quality assessment to extracted stories
                    return self._assess_and_improve_user_story_quality(extracted_stories, feature, context, product_vision, max_user_stories)
                else:
                    # This looks like actual user stories - apply quality assessment
                    return self._assess_and_improve_user_story_quality(user_stories, feature, context, product_vision, max_user_stories)
            elif isinstance(user_stories, dict) and 'user_stories' in user_stories:
                return self._assess_and_improve_user_story_quality(user_stories['user_stories'], feature, context, product_vision, max_user_stories)
            elif isinstance(user_stories, dict):
                # Check if this is a single user story object (LLM returned object instead of array)
                if self._looks_like_user_story(user_stories):
                    print("INFO: LLM returned single user story object instead of array, wrapping in array...")
                    return self._assess_and_improve_user_story_quality([user_stories], feature, context, product_vision, max_user_stories)
                else:
                    print("WARNING: LLM response was not in expected format. Attempting to extract user stories from response...")
                    # Try to extract any user story-like content from the response
                    fallback_stories = self._extract_user_stories_from_any_format(user_stories, feature, max_user_stories)
                    if fallback_stories:
                        return self._assess_and_improve_user_story_quality(fallback_stories, feature, context, product_vision, max_user_stories)
                    return fallback_stories
            else:
                print("WARNING: LLM response was not in expected format. Attempting to extract user stories from response...")
                # Try to extract any user story-like content from the response
                fallback_stories = self._extract_user_stories_from_any_format(user_stories, feature, max_user_stories)
                if fallback_stories:
                    return self._assess_and_improve_user_story_quality(fallback_stories, feature, context, product_vision, max_user_stories)
                return fallback_stories
                
        except json.JSONDecodeError as e:
            # Try to extract user stories from the raw response text
            return self._extract_user_stories_from_text(response, feature, max_user_stories)
    
    def _looks_like_user_story(self, obj: dict) -> bool:
        """Check if a dictionary object looks like a user story."""
        if not isinstance(obj, dict):
            return False
        
        # Check for common user story fields
        user_story_fields = ['title', 'user_story', 'description', 'acceptance_criteria']
        has_user_story_fields = sum(1 for field in user_story_fields if field in obj) >= 2
        
        # Check if title or user_story contains "As a" pattern
        title = obj.get('title', '')
        user_story = obj.get('user_story', '')
        has_user_story_pattern = ('As a' in title or 'As a' in user_story)
        
        return has_user_story_fields or has_user_story_pattern

    def _extract_user_stories_from_any_format(self, response_data: any, feature: dict = None, max_user_stories: int = None) -> list[dict]:
        """Extract user stories from any response format the LLM provides."""
        print("[UserStoryDecomposerAgent] Extracting user stories from unexpected format...")
        
        extracted_stories = []
        
        # Try to find user story-like content in any nested structure
        if isinstance(response_data, dict):
            # Look for user stories in various possible keys
            for key in ['user_stories', 'stories', 'items', 'tasks', 'requirements']:
                if key in response_data and isinstance(response_data[key], list):
                    for item in response_data[key]:
                        story = self._convert_to_user_story_format(item)
                        if story:
                            extracted_stories.append(story)
        elif isinstance(response_data, list):
            # Process each item in the list
            for item in response_data:
                story = self._convert_to_user_story_format(item)
                if story:
                    extracted_stories.append(story)
        elif isinstance(response_data, str):
            # Try to create a basic user story from string
            story = {
                'title': response_data[:100] + '...' if len(response_data) > 100 else response_data,
                'user_story': response_data,
                'description': f"Extracted from text response",
                'story_points': 5,
                'priority': 'Medium',
                'acceptance_criteria': []
            }
            extracted_stories.append(story)
        
        if not extracted_stories:
            # No fallback - return empty list instead of creating generic work items
            print("[UserStoryDecomposerAgent] No user stories extracted, returning empty list")
            return []
        
        print(f"[UserStoryDecomposerAgent] Extracted {len(extracted_stories)} user stories from format")
        return self._validate_and_enhance_user_stories(extracted_stories, max_user_stories)

    def _convert_to_user_story_format(self, item: any) -> dict:
        """Convert any item to user story format."""
        if isinstance(item, dict):
            # Already a structured item, ensure it has required fields
            return {
                'title': item.get('title', item.get('name', item.get('summary', 'User Story'))),
                'user_story': item.get('user_story', item.get('description', item.get('story', item.get('title', '')))),
                'description': item.get('description', item.get('details', '')),
                'story_points': item.get('story_points', item.get('points', item.get('effort', 5))),
                'priority': item.get('priority', 'Medium'),
                'acceptance_criteria': item.get('acceptance_criteria', item.get('criteria', []))
            }
        # No fallback for strings or other types - return None
        return None

    def _extract_user_stories_from_text(self, response_text: str, feature: dict, max_user_stories: int = None) -> list[dict]:
        """Extract user stories from raw text when JSON parsing fails."""
        print("[UserStoryDecomposerAgent] Extracting user stories from raw text...")
        
        extracted_stories = []
        
        # Try to find user story patterns in the text
        import re
        
        # Pattern 1: Look for "As a ... I want ... so that ..." patterns
        user_story_pattern = r"As a[n]?\s+([^,]+),?\s+I want\s+([^,]+),?\s+so that\s+([^.]+)"
        matches = re.findall(user_story_pattern, response_text, re.IGNORECASE)
        
        for i, (user, want, goal) in enumerate(matches):
            story = {
                'title': f"User Story {i+1}: {want.strip()}",
                'user_story': f"As a {user.strip()}, I want {want.strip()} so that {goal.strip()}",
                'description': f"Extracted from text response for feature: {feature.get('title', 'Unknown')}",
                'story_points': 5,
                'priority': 'Medium',
                'acceptance_criteria': []
            }
            extracted_stories.append(story)
        
        # Pattern 2: Look for numbered lists that might be user stories
        if not extracted_stories:
            numbered_pattern = r"^\s*\d+\.?\s*(.+)$"
            lines = response_text.split('\n')
            for line in lines:
                match = re.match(numbered_pattern, line.strip())
                if match and len(match.group(1)) > 10:  # Reasonable length for a user story
                    story_text = match.group(1).strip()
                    story = {
                        'title': story_text[:50] + '...' if len(story_text) > 50 else story_text,
                        'user_story': story_text,
                        'description': f"Extracted from numbered list for feature: {feature.get('title', 'Unknown')}",
                        'story_points': 5,
                        'priority': 'Medium',
                        'acceptance_criteria': []
                    }
                    extracted_stories.append(story)
        
        # If still no stories found, return empty list instead of creating generic work items
        if not extracted_stories:
            print("[UserStoryDecomposerAgent] No user stories found in text, returning empty list")
            return []
        
        print(f"[UserStoryDecomposerAgent] Extracted {len(extracted_stories)} user stories from text")
        return self._validate_and_enhance_user_stories(extracted_stories, max_user_stories)

    def _validate_and_enhance_user_stories(self, user_stories: list, max_user_stories: int = None) -> list:
        """
        Validate and enhance user stories to meet quality standards.
        Ensures compliance with Backlog Sweeper monitoring rules.
        """
        # Apply limit if specified
        if max_user_stories and len(user_stories) > max_user_stories:
            user_stories = user_stories[:max_user_stories]
            
        enhanced_stories = []
        
        for story in user_stories:
            # Validate and fix user story structure
            enhanced_story = self._enhance_single_user_story(story)
            if enhanced_story is not None:  # Skip stories that couldn't be enhanced
                enhanced_stories.append(enhanced_story)
            else:
                print(f"WARNING: Skipping invalid user story that couldn't be enhanced")
        
        return enhanced_stories

    def _enhance_single_user_story(self, story: dict) -> dict:
        """
        Enhance a single user story to meet quality standards.
        """
        # Handle case where story might be a string instead of dict
        if isinstance(story, str):
            # Convert string to basic user story structure
            story = {
                'title': story[:50] + '...' if len(story) > 50 else story,
                'user_story': story,
                'description': story,
                'story_points': 5,
                'priority': 'Medium',
                'acceptance_criteria': []
            }
        elif not isinstance(story, dict):
            # Convert other types to string then to dict
            story_text = str(story)
            story = {
                'title': story_text[:50] + '...' if len(story_text) > 50 else story_text,
                'user_story': story_text,
                'description': story_text,
                'story_points': 5,
                'priority': 'Medium',
                'acceptance_criteria': []
            }
        
        enhanced_story = story.copy()
        
        # Validate and fix title
        title = story.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "User Story")
        if not title_valid:
            # Only show critical title issues
            if not title or len(title.strip()) < 5:
                print(f"WARNING: Critical story title issue: {', '.join(title_issues)}")
            if not title or len(title.strip()) < 5:
                # Generate a meaningful title from description or user_story field
                description = story.get('description', '') or story.get('user_story', '')
                if description and len(description.strip()) > 10:
                    enhanced_story['title'] = f"User Story: {description[:50]}..."
                else:
                    # CRITICAL: Do NOT create generic titles - skip invalid stories
                    print(f"ERROR: User story has no valid title or description - skipping")
                    return None  # Signal to skip this story entirely
        
        # Validate and fix description
        description = story.get('description', '') or story.get('user_story', '')
        desc_valid, desc_issues = self.quality_validator.validate_user_story_description(description)
        if not desc_valid:
            # Only show critical description issues
            if not description or len(description.strip()) < 20:
                print(f"WARNING: Critical story description issue: {', '.join(desc_issues)}")
            # CRITICAL: Do NOT create generic descriptions
            if not description or len(description.strip()) < 20:
                print(f"ERROR: User story has no valid description - skipping")
                return None  # Skip stories without proper descriptions
            else:
                enhanced_story['description'] = description
        else:
            enhanced_story['description'] = description
        
        # Validate and enhance acceptance criteria
        criteria = story.get('acceptance_criteria', [])
        criteria_valid, criteria_issues = self.quality_validator.validate_acceptance_criteria(criteria, enhanced_story.get('title', ''))
        if not criteria_valid or criteria_issues:
            # Only show critical criteria issues
            if not criteria or len(criteria) < 2:
                print(f"WARNING: Critical acceptance criteria issue: {', '.join(criteria_issues)}")
            # CRITICAL: Do NOT generate generic acceptance criteria
            # If the LLM didn't provide good criteria, fail cleanly
            if not criteria or len(criteria) < 1:
                print(f"ERROR: User story has no valid acceptance criteria - skipping")
                return None  # Skip stories without proper acceptance criteria
            enhanced_story['acceptance_criteria'] = criteria  # Use original criteria, don't enhance
        else:
            enhanced_story['acceptance_criteria'] = criteria
        
        # Ensure story points are set
        if not enhanced_story.get('story_points'):
            criteria_count = len(enhanced_story.get('acceptance_criteria', []))
            if criteria_count <= 3:
                enhanced_story['story_points'] = 2
            elif criteria_count <= 5:
                enhanced_story['story_points'] = 3
            elif criteria_count <= 7:
                enhanced_story['story_points'] = 5
            else:
                enhanced_story['story_points'] = 8
        
        # Add quality metadata
        enhanced_story['definition_of_ready'] = [
            'Acceptance criteria defined and reviewed',
            'Story points estimated',
            'Dependencies identified',
            'UI/UX requirements clarified'
        ]
        
        enhanced_story['definition_of_done'] = [
            'Code developed and reviewed',
            'Unit tests written and passing',
            'Integration tests passing',
            'Acceptance criteria validated',
            'Documentation updated'
        ]
        
        # Ensure other required fields
        if not enhanced_story.get('priority'):
            enhanced_story['priority'] = 'Medium'
        
        if not enhanced_story.get('user_type'):
            enhanced_story['user_type'] = 'general_user'
        
        if not enhanced_story.get('category'):
            enhanced_story['category'] = 'feature_implementation'
        
        return enhanced_story

    def run_with_template(self, user_input: str, context: dict, template_name: str = None) -> str:
        """Run with a specific prompt template (fallback to default if template doesn't exist)."""
        # Use the template name if provided, otherwise use the agent name
        template_to_use = template_name or "user_story_decomposer"
        
        try:
            # Import prompt manager
            from utils.prompt_manager import prompt_manager
            
            # Try to use the specific template
            prompt = prompt_manager.get_prompt(template_to_use, context)
            # Use the proper method based on provider
            if self.llm_provider == "ollama":
                # Use the Ollama provider for local inference
                return self.ollama_provider.generate_response(
                    system_prompt=prompt,
                    user_input=user_input,
                    temperature=0.7,
                    max_tokens=8000
                )
            else:
                # Use direct API call for cloud providers
                url = self.api_url
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_input}
                    ]
                }
                
                import requests
                # Use longer timeout for 70B models
                timeout = 300 if self.model and "70b" in self.model.lower() else 60
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"WARNING: Template {template_to_use} failed: {e}")
            print("Falling back to default prompt...")
            # Use timeout protection for fallback call
            try:
                timeout = 180 if self.model and "70b" in self.model.lower() else 60
                return self._run_with_timeout(user_input, context, timeout=timeout)
            except TimeoutError:
                print("WARNING: Fallback generation timed out")
                return ""
            except Exception as fallback_e:
                print(f"ERROR: Fallback generation failed: {fallback_e}")
                return ""

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from AI response with improved bracket counting and validation.
        
        Args:
            response: Raw response from AI model
            
        Returns:
            Cleaned JSON string
        """
        if not response:
            return "[]"
        
        import re
        
        # Look for JSON inside ```json blocks
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, response, re.IGNORECASE)
        
        if json_match:
            content = json_match.group(1).strip()
            # Try to clean and validate the JSON
            try:
                json.loads(content)
                return content
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                cleaned = self._fix_json_syntax(content)
                try:
                    json.loads(cleaned)
                    return cleaned
                except json.JSONDecodeError:
                    pass
        
        # Look for JSON inside ``` blocks (without language specifier)
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        code_match = re.search(code_pattern, response)
        
        if code_match:
            content = code_match.group(1).strip()
            # Check if it looks like JSON (starts with { or [)
            if content.startswith(('{', '[')):
                return content
        
        # Enhanced JSON extraction with proper bracket counting
        # Find the start of JSON array
        start_idx = response.find('[')
        if start_idx == -1:
            start_idx = response.find('{')
            if start_idx == -1:
                return "[]"
        
        # Count brackets/braces to find the complete JSON structure
        if response[start_idx] == '[':
            bracket_count = 0
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if char == "'" and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            # Found the end of the JSON array
                            return response[start_idx:i+1]
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
        
        else:  # Starting with '{'
            brace_count = 0
            bracket_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if char == "'" and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found the end of the JSON object
                            return response[start_idx:i+1]
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
        
        # Fallback: return everything from start to end of response
        return response[start_idx:].strip()
    
    def _fix_json_syntax(self, json_str: str) -> str:
        """
        Fix common JSON syntax issues that LLMs often produce.
        """
        if not json_str:
            return "[]"
        
        import re
        
        # Remove comments and extra text
        lines = json_str.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip comment lines and empty lines
            if line.startswith('#') or line.startswith('//') or not line:
                continue
            # Remove inline comments
            if '#' in line:
                line = line.split('#')[0].strip()
            if '//' in line:
                line = line.split('//')[0].strip()
            if line:
                cleaned_lines.append(line)
        
        cleaned_json = '\n'.join(cleaned_lines)
        
        # Fix common issues
        cleaned_json = re.sub(r',\s*}', '}', cleaned_json)  # Remove trailing commas
        cleaned_json = re.sub(r',\s*]', ']', cleaned_json)  # Remove trailing commas in arrays
        
        # Fix unquoted property names
        cleaned_json = re.sub(r'(\w+):', r'"\1":', cleaned_json)
        
        # Fix single quotes to double quotes
        cleaned_json = cleaned_json.replace("'", '"')
        
        return cleaned_json

    def _run_with_timeout(self, user_input: str, context: dict, timeout: int = 60, template_name: str = None):
        """Run the agent with a timeout to prevent hanging."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                print(f"Starting LLM call with template: {template_name}")
                if template_name:
                    result[0] = self.run_with_template(user_input, context, template_name)
                else:
                    result[0] = self.run(user_input, context)
                print(f"LLM call completed, response length: {len(result[0]) if result[0] else 0}")
            except Exception as e:
                print(f"LLM call failed with exception: {e}")
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"WARNING: User story generation timed out after {timeout} seconds")
            # Return empty response instead of None to prevent NoneType errors
            return ""
        
        if exception[0]:
            raise exception[0]
        
        # Ensure we never return None - return empty string if result is None
        return result[0] if result[0] is not None else ""
    
    def _manual_json_extraction(self, response: str) -> Optional[str]:
        """Manual JSON extraction as final fallback for CodeLlama responses."""
        if not response:
            return None
            
        try:
            # Strategy 1: Look for JSON after explanatory text
            # CodeLlama often explains then provides JSON
            lines = response.split('\n')
            json_start = -1
            json_end = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('[') and '{' in line:
                    json_start = i
                    break
                elif line.strip().startswith('{') and '"title"' in line:
                    json_start = i
                    break
            
            if json_start >= 0:
                # Find the end of JSON
                bracket_count = 0
                json_lines = []
                for i in range(json_start, len(lines)):
                    line = lines[i]
                    json_lines.append(line)
                    
                    # Count brackets to find end
                    for char in line:
                        if char == '[' or char == '{':
                            bracket_count += 1
                        elif char == ']' or char == '}':
                            bracket_count -= 1
                    
                    if bracket_count == 0 and (']' in line or '}' in line):
                        json_end = i
                        break
                
                if json_end >= 0:
                    json_text = '\n'.join(json_lines)
                    
                    # Clean up the JSON
                    json_text = json_text.strip()
                    
                    # If it's a single object, wrap in array
                    if json_text.startswith('{') and json_text.endswith('}'):
                        json_text = f'[{json_text}]'
                    
                    # Try to parse it
                    try:
                        json.loads(json_text)
                        return json_text
                    except:
                        pass
            
            # Strategy 2: Extract any JSON-like content using regex
            import re
            
            # Look for array patterns
            array_match = re.search(r'\[[\s\S]*?\]', response)
            if array_match:
                potential_json = array_match.group(0)
                try:
                    json.loads(potential_json)
                    return potential_json
                except:
                    pass
            
            # Strategy 3: Look for object patterns and wrap in array
            object_matches = re.findall(r'\{[^{}]*"title"[^{}]*:[^{}]*\}', response, re.DOTALL)
            if object_matches:
                json_text = '[' + ','.join(object_matches) + ']'
                try:
                    json.loads(json_text)
                    return json_text
                except:
                    pass
            
            return None
            
        except Exception as e:
            print(f"ERROR: Manual JSON extraction error: {e}")
            return None

    def _assess_and_improve_user_story_quality(self, user_stories: list, feature: dict, context: dict, 
                                             product_vision: str, max_user_stories: int = None) -> list:
        """Assess user story quality and retry generation if not EXCELLENT."""
        if not user_stories:
            return []
        
        # Apply limit first if specified
        if max_user_stories and len(user_stories) > max_user_stories:
            user_stories = user_stories[:max_user_stories]
        
        domain = context.get('domain', 'general') if context else 'general'
        approved_stories = []
        
        print(f"\nStarting user story quality assessment for {len(user_stories)} stories...")
        print(f"Feature Context: {feature.get('title', 'Unknown Feature')}")
        print(f"Domain: {domain}")
        
        for i, story in enumerate(user_stories):
            print(f"\n{'='*60}")
            print(f"ASSESSING USER STORY {i+1}/{len(user_stories)}")
            print(f"{'='*60}")
            
            attempt = 1
            current_story = story
            
            while attempt <= self.max_quality_retries:
                # Debug: Check current_story type before assessment
                print(f"[DEBUG] Attempt {attempt}: current_story type = {type(current_story)}")
                if isinstance(current_story, dict):
                    print(f"[DEBUG] Story keys: {list(current_story.keys())}")
                elif isinstance(current_story, str):
                    print(f"[DEBUG] Story string: {current_story[:100]}...")
                
                # Assess current story quality
                assessment = self.user_story_quality_assessor.assess_user_story(
                    current_story, feature, domain, product_vision
                )
                
                # Log assessment
                log_output = self.user_story_quality_assessor.format_assessment_log(
                    current_story, assessment, attempt
                )
                print(log_output)
                
                if assessment.rating == "EXCELLENT":
                    print(f"SUCCESS: User story approved with EXCELLENT rating on attempt {attempt}")
                    approved_stories.append(current_story)
                    break
                
                if attempt == self.max_quality_retries:
                    print(f"- User story failed to reach EXCELLENT rating after {self.max_quality_retries} attempts")
                    print(f"   Final rating: {assessment.rating} ({assessment.score}/100)")
                    print("   Story REJECTED - EXCELLENT rating required")
                    # Do NOT add to approved_stories - only EXCELLENT stories allowed
                    break
                
                # Generate improvement prompt
                improvement_prompt = self._create_user_story_improvement_prompt(
                    current_story, assessment, feature, product_vision, context
                )
                
                print(f"Attempting to improve user story (attempt {attempt + 1}/{self.max_quality_retries})")
                
                try:
                    # Re-generate the story with improvement guidance
                    improved_response = self._generate_improved_user_story(improvement_prompt, context)
                    print(f"[DEBUG] Improved response type: {type(improved_response)}")
                    if improved_response and isinstance(improved_response, dict):
                        print("[DEBUG] Using improved story")
                        current_story = improved_response
                    elif improved_response:
                        print(f"[DEBUG] Improved response is not a dict: {type(improved_response)}")
                        print(f"[DEBUG] Response value: {str(improved_response)[:200]}...")
                        print("WARNING: Improvement response is not a proper story object - using current version")
                        break
                    else:
                        print("WARNING: Failed to generate improvement - using current version")
                        break
                        
                except Exception as e:
                    print(f"WARNING: Error during user story improvement: {e}")
                    break
                
                attempt += 1
        
        print(f"\nSUCCESS: User story quality assessment complete: {len(approved_stories)} stories approved")
        return approved_stories
    
    def _create_user_story_improvement_prompt(self, story: dict, assessment, feature: dict, 
                                            product_vision: str, context: dict) -> str:
        """Create a prompt to improve the user story based on quality assessment."""
        title = story.get('title', '')
        description = story.get('description', story.get('user_story', ''))
        acceptance_criteria = story.get('acceptance_criteria', [])
        feature_title = feature.get('title', '')
        feature_description = feature.get('description', '')
        
        improvement_text = f"""USER STORY IMPROVEMENT REQUEST

Current User Story:
Title: {title}
Description: {description}
Acceptance Criteria: {acceptance_criteria}

Parent Feature Context:
Title: {feature_title}
Description: {feature_description}

Product Vision Context:
{product_vision}

Quality Issues Identified:
{chr(10).join('• ' + issue for issue in assessment.specific_issues)}

Improvement Suggestions:
{chr(10).join('• ' + suggestion for suggestion in assessment.improvement_suggestions)}

CRITICAL REQUIREMENTS:
1. Do NOT create separate user stories for Given/When/Then components
2. Include 3-5 complete acceptance criteria within ONE story
3. Each acceptance criterion should be a complete test scenario
4. Use proper "Given/When/Then" format within each criterion

INSTRUCTIONS:
Rewrite this user story to address the quality issues above. Focus on:
1. Creating ONE complete user story with proper "As a [user], I want [goal] so that [benefit]" format
2. Including 3-5 complete acceptance criteria (NOT separate stories)
3. Each criterion should be testable and include Given/When/Then components
4. Strong alignment with feature "{feature_title}"
5. Domain-specific terminology and context
6. Clear user value and benefit

Return only a single improved user story in this JSON format:
{{
  "title": "As a [specific user role], I want [specific goal] so that [clear benefit]",
  "user_story": "Same as title - the complete user story statement",
  "description": "Detailed explanation of the functionality and implementation requirements",
  "acceptance_criteria": [
    "Given [context], When [action], Then [expected result]",
    "Given [context], When [action], Then [expected result]", 
    "Given [context], When [action], Then [expected result]"
  ],
  "story_points": 1|2|3|5|8|13,
  "priority": "High|Medium|Low",
  "category": "authentication|data_management|ui_ux|integration|security|performance|administration",
  "user_type": "new_user|existing_user|admin|power_user|casual_user"
}}"""
        return improvement_text.strip()
    
    def _generate_improved_user_story(self, improvement_prompt: str, context: dict) -> dict:
        """Generate an improved version of the user story."""
        try:
            print("[DEBUG] Attempting to improve user story using improvement prompt")
            
            # Build proper context for template (similar to user story generation)
            prompt_context = {
                'product_vision': context.get('product_vision', '') if context else '',
                'domain': context.get('domain', 'dynamic') if context else 'dynamic',
                'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
                'target_users': context.get('target_users', 'end users') if context else 'end users',
                'timeline': context.get('timeline', 'not specified') if context else 'not specified',
                'budget_constraints': context.get('budget_constraints', 'standard budget') if context else 'standard budget',
                'epic_context': context.get('epic_context', '') if context else '',
                'feature_context': context.get('feature_context', '') if context else ''
            }
            
            # Use the base agent run method to generate improvement
            response = self.run(improvement_prompt, prompt_context)
            print(f"[DEBUG] Improvement response received: {len(response) if response else 0} characters")
            
            if not response:
                return None
            
            # Extract and parse JSON
            cleaned_response = JSONExtractor.extract_json_from_response(response)
            print(f"[DEBUG] Improvement response cleaned: {cleaned_response[:200] if cleaned_response else 'None'}")
            
            if not cleaned_response:
                print("[DEBUG] No JSON extracted from improvement response")
                return None
                
            improved_story = json.loads(cleaned_response)
            print(f"[DEBUG] Improved story type: {type(improved_story)}")
            if isinstance(improved_story, dict):
                print(f"[DEBUG] Improved story keys: {list(improved_story.keys())}")
            elif isinstance(improved_story, list):
                print(f"[DEBUG] Improved story list length: {len(improved_story)}")
                if improved_story and isinstance(improved_story[0], dict):
                    print(f"[DEBUG] First story keys: {list(improved_story[0].keys())}")
            
            # Validate that we got a single story object
            if isinstance(improved_story, dict):
                return improved_story
            elif isinstance(improved_story, list) and len(improved_story) > 0:
                return improved_story[0]  # Take first story if array returned
            else:
                return None
                
        except Exception as e:
            print(f"Error generating improved user story: {e}")
            import traceback
            traceback.print_exc()
            print(f"Raw response that caused error: {response[:500] if response else 'None'}")
            print(f"Cleaned response: {cleaned_response[:200] if 'cleaned_response' in locals() else 'Not extracted'}")
            return None
