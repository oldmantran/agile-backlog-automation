import json
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator

class UserStoryDecomposerAgent(Agent):
    """
    Agent responsible for decomposing features into user stories.
    Focuses on user journeys, acceptance criteria, and implementation details.
    """
    
    def __init__(self, config: Config):
        super().__init__("user_story_decomposer_agent", config)
        # Initialize quality validator with current configuration
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)

    def decompose_feature_to_user_stories(self, feature: dict, context: dict = None, max_user_stories: int = None) -> list[dict]:
        """Break down a feature into detailed user stories with acceptance criteria and story points."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
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
        
        print(f"📝 [UserStoryDecomposerAgent] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Use the user story decomposer template
        response = self.run_with_template(user_input, prompt_context, template_name="user_story_decomposer")

        try:
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            user_stories = json.loads(cleaned_response)
            
            # Handle different response formats
            if isinstance(user_stories, list) and len(user_stories) > 0:
                # Check if these look like user stories or features
                first_item = user_stories[0]
                if 'user_stories' in first_item:
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
                return self._extract_user_stories_from_any_format(user_stories, max_user_stories)
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            print("🔄 Attempting alternative parsing...")
            # Try to extract user stories from the raw response text
            return self._extract_user_stories_from_text(response, feature, max_user_stories)

    def _extract_user_stories_from_any_format(self, response_data: any, max_user_stories: int = None) -> list[dict]:
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
            # Create a basic user story to avoid empty results
            extracted_stories.append({
                'title': "Process Feature Requirements",
                'user_story': "As a user, I want to access the feature functionality so that I can complete my tasks",
                'description': f"Generated from unrecognized LLM response format",
                'story_points': 5,
                'priority': 'Medium',
                'acceptance_criteria': ["Feature should be accessible", "Feature should function as expected"]
            })
        
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
        elif isinstance(item, str):
            # Convert string to user story structure
            return {
                'title': item[:50] + '...' if len(item) > 50 else item,
                'user_story': item,
                'description': f"Converted from text: {item}",
                'story_points': 5,
                'priority': 'Medium',
                'acceptance_criteria': []
            }
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
        
        # If still no stories found, create one based on the feature
        if not extracted_stories:
            story = {
                'title': f"Implement {feature.get('title', 'Feature')}",
                'user_story': f"As a user, I want to use {feature.get('title', 'the feature')} so that I can {feature.get('description', 'accomplish my goals')}",
                'description': feature.get('description', f"Generated from feature: {feature.get('title', 'Unknown')}"),
                'story_points': feature.get('estimated_story_points', 8),
                'priority': feature.get('priority', 'Medium'),
                'acceptance_criteria': []
            }
            extracted_stories.append(story)
        
        print(f"� [UserStoryDecomposerAgent] Extracted {len(extracted_stories)} user stories from text")
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
            print(f"⚠️ Story title issues: {', '.join(title_issues)}")
            if not title:
                enhanced_story['title'] = f"User Story: {story.get('description', 'Undefined')[:50]}..."
        
        # Validate and fix description
        description = story.get('description', '') or story.get('user_story', '')
        desc_valid, desc_issues = self.quality_validator.validate_user_story_description(description)
        if not desc_valid:
            print(f"⚠️ Story description issues: {', '.join(desc_issues)}")
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
            print(f"📋 Enhancing acceptance criteria: {', '.join(criteria_issues)}")
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
            print(f"📤 Sending to {self.llm_provider.capitalize()} with {template_to_use} template...")
            
            # Direct API call since we have the processed prompt
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
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"⚠️ Template {template_to_use} failed: {e}")
            print("🔄 Falling back to default prompt...")
            return self.run(user_input, context)

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
