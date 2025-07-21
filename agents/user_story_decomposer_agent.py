import json
import re
import threading
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

class UserStoryDecomposerAgent(Agent):
    """
    Agent responsible for decomposing features into user stories.
    Focuses on user journeys, acceptance criteria, and implementation details.
    """
    
    def __init__(self, config: Config):
        super().__init__("user_story_decomposer_agent", config)
        # Initialize quality validator with current configuration
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)

    def decompose_feature_to_user_stories(self, feature: dict, context: dict = None, max_user_stories: int = 5) -> list[dict]:
        """Decompose a feature into user stories."""
        # Remove redundant print - supervisor already logs this
        # print(f"📝 [UserStoryDecomposerAgent] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Get the feature description and title
        feature_description = feature.get('description', '')
        feature_title = feature.get('title', 'Feature')
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'team_velocity': context.get('team_velocity', '20-30 points per sprint') if context else '20-30 points per sprint'
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
            models_to_try = [(self.model, 120)]
        elif self.model and ("34b" in self.model.lower()):
            # 34B model with standard timeout
            models_to_try = [(self.model, 60)]
        else:
            # 8B or other models with standard timeout
            models_to_try = [(self.model, 60)]
        
        # Try each model until one succeeds
        for model_name, timeout in models_to_try:
            try:
                print(f"🔄 Trying {model_name} for user stories with {timeout}s timeout...")
                
                # Temporarily switch to this model
                original_model = self.model
                self.model = model_name
                
                # Update Ollama provider if needed
                if hasattr(self, 'ollama_provider') and self.llm_provider == "ollama":
                    try:
                        from utils.ollama_client import create_ollama_provider
                        self.ollama_provider = create_ollama_provider(preset='balanced')
                    except Exception as e:
                        print(f"⚠️ Failed to switch to {model_name}: {e}")
                        continue
                
                response = self._run_with_timeout(user_input, prompt_context, timeout=timeout, template_name="user_story_decomposer")
                
                # Restore original model
                self.model = original_model
                
                print(f"✅ Successfully generated user stories using {model_name}")
                break
                
            except TimeoutError:
                print(f"⏱️ {model_name} timed out after {timeout}s, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
            except Exception as e:
                print(f"❌ {model_name} failed: {e}, trying next model...")
                # Restore original model before continuing
                self.model = original_model
                continue
        else:
            # All models failed
            print("❌ All models failed for user story generation")
            return []

        try:
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            print(f"🔍 [UserStoryDecomposerAgent] Raw response: {response[:200]}...")
            print(f"🔍 [UserStoryDecomposerAgent] Cleaned response: {cleaned_response[:200]}...")
            
            # Safety check for empty or invalid JSON
            if not cleaned_response or cleaned_response.strip() == "[]":
                print("⚠️ Empty or invalid JSON response")
                return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            try:
                user_stories = json.loads(cleaned_response)
            except (json.JSONDecodeError, TypeError):
                print("⚠️ Failed to parse JSON response")
                return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            # Safety check for None or empty user_stories
            if not user_stories:
                print("⚠️ Empty or None user_stories after JSON parsing")
                return self._extract_user_stories_from_text(response, feature, max_user_stories)
            
            # Handle different response formats
            if isinstance(user_stories, list) and len(user_stories) > 0:
                # Check if these look like user stories or features
                first_item = user_stories[0]
                if first_item and isinstance(first_item, dict) and 'user_stories' in first_item:
                    # This is actually a list of features, extract the user stories
                    print("🔄 Response contains features, extracting user stories...")
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
                    return self._validate_and_enhance_user_stories(extracted_stories, max_user_stories)
                else:
                    # This looks like actual user stories - validate and enhance them
                    enhanced_stories = self._validate_and_enhance_user_stories(user_stories, max_user_stories)
                    return enhanced_stories
            elif isinstance(user_stories, dict) and 'user_stories' in user_stories:
                return self._validate_and_enhance_user_stories(user_stories['user_stories'], max_user_stories)
            else:
                print("⚠️ LLM response was not in expected format. Attempting to extract user stories from response...")
                # Try to extract any user story-like content from the response
                return self._extract_user_stories_from_any_format(user_stories, feature, max_user_stories)
                
        except json.JSONDecodeError as e:
            # Try to extract user stories from the raw response text
            return self._extract_user_stories_from_text(response, feature, max_user_stories)

    def _extract_user_stories_from_any_format(self, response_data: any, feature: dict = None, max_user_stories: int = None) -> list[dict]:
        """Extract user stories from any response format the LLM provides."""
        print("🔍 [UserStoryDecomposerAgent] Extracting user stories from unexpected format...")
        
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
            print("🔍 [UserStoryDecomposerAgent] No user stories extracted, returning empty list")
            return []
        
        print(f"🔍 [UserStoryDecomposerAgent] Extracted {len(extracted_stories)} user stories from format")
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
        print("🔍 [UserStoryDecomposerAgent] Extracting user stories from raw text...")
        
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
            print("🔍 [UserStoryDecomposerAgent] No user stories found in text, returning empty list")
            return []
        
        print(f"🔍 [UserStoryDecomposerAgent] Extracted {len(extracted_stories)} user stories from text")
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
            enhanced_stories.append(enhanced_story)
        
        return enhanced_stories

    def _enhance_single_user_story(self, story: dict) -> dict:
        """
        Enhance a single user story to meet quality standards.
        """
        enhanced_story = story.copy()
        
        # Validate and fix title
        title = story.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "User Story")
        if not title_valid:
            # Only show critical title issues
            if not title or len(title.strip()) < 5:
                print(f"⚠️ Critical story title issue: {', '.join(title_issues)}")
            if not title:
                enhanced_story['title'] = f"User Story: {story.get('description', 'Undefined')[:50]}..."
        
        # Validate and fix description
        description = story.get('description', '') or story.get('user_story', '')
        desc_valid, desc_issues = self.quality_validator.validate_user_story_description(description)
        if not desc_valid:
            # Only show critical description issues
            if not description or len(description.strip()) < 20:
                print(f"⚠️ Critical story description issue: {', '.join(desc_issues)}")
            # Try to fix the description
            if 'As a' not in description and 'As an' not in description:
                user_type = story.get('user_type', 'user')
                goal = title.replace('User Story:', '').strip() if 'User Story:' in title else title
                enhanced_story['description'] = f"As a {user_type}, I want {goal} so that I can achieve my objectives"
            else:
                enhanced_story['description'] = description
        else:
            enhanced_story['description'] = description
        
        # Validate and enhance acceptance criteria
        criteria = story.get('acceptance_criteria', [])
        criteria_valid, criteria_issues = self.quality_validator.validate_acceptance_criteria(criteria, title)
        if not criteria_valid or criteria_issues:
            # Only show critical criteria issues
            if len(criteria) < 2:
                print(f"📋 Critical acceptance criteria issue: {', '.join(criteria_issues)}")
            enhanced_criteria = self.quality_validator.enhance_acceptance_criteria(
                criteria, 
                {'title': enhanced_story['title'], 'description': enhanced_story['description']}
            )
            enhanced_story['acceptance_criteria'] = enhanced_criteria
        
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
                    max_tokens=4000
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
            print(f"⚠️ Template {template_to_use} failed: {e}")
            print("🔄 Falling back to default prompt...")
            # Use timeout protection for fallback call
            try:
                timeout = 180 if self.model and "70b" in self.model.lower() else 60
                return self._run_with_timeout(user_input, context, timeout=timeout)
            except TimeoutError:
                print("⚠️ Fallback generation timed out")
                return ""
            except Exception as fallback_e:
                print(f"❌ Fallback generation failed: {fallback_e}")
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
            return json_match.group(1).strip()
        
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

    def _run_with_timeout(self, user_input: str, context: dict, timeout: int = 60, template_name: str = None):
        """Run the agent with a timeout to prevent hanging."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                if template_name:
                    result[0] = self.run_with_template(user_input, context, template_name)
                else:
                    result[0] = self.run(user_input, context)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"⚠️ User story generation timed out after {timeout} seconds")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]
