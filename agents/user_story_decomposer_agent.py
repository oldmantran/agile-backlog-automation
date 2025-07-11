import json
from agents.base_agent import Agent
from config.config_loader import Config

class UserStoryDecomposerAgent(Agent):
    """
    Agent responsible for decomposing features into user stories.
    Focuses on user journeys, acceptance criteria, and implementation details.
    """
    
    def __init__(self, config: Config):
        super().__init__("user_story_decomposer_agent", config)

    def decompose_feature_to_user_stories(self, feature: dict, context: dict = None) -> list[dict]:
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
            # Check for markdown code blocks and extract JSON
            if "```json" in response:
                print("🔍 Extracting JSON from markdown...")
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            
            user_stories = json.loads(response)
            
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
                    return self._validate_and_enhance_user_stories(extracted_stories)
                else:
                    # This looks like actual user stories - validate and enhance them
                    enhanced_stories = self._validate_and_enhance_user_stories(user_stories)
                    return enhanced_stories
            elif isinstance(user_stories, dict) and 'user_stories' in user_stories:
                return self._validate_and_enhance_user_stories(user_stories['user_stories'])
            else:
                print("⚠️ LLM response was not in expected format.")
                print("� Response structure:", type(user_stories))
                print("🔎 Response content:", user_stories)
                raise ValueError(f"LLM response was not in expected format. Expected list of user stories, got {type(user_stories)}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            print("� Response length:", len(response))
            print("🔎 First 500 chars:", response[:500])
            raise ValueError(f"Failed to parse JSON response from LLM: {e}")

    def _validate_and_enhance_user_stories(self, user_stories: list) -> list:
        """
        Format and clean user stories for better readability.
        Quality validation is handled by the Backlog Sweeper.
        """
        enhanced_stories = []
        
        for story in user_stories:
            # Format and clean user story structure
            enhanced_story = self._enhance_single_user_story(story)
            enhanced_stories.append(enhanced_story)
        
        return enhanced_stories

    def _enhance_single_user_story(self, story: dict) -> dict:
        """
        Format a single user story for better readability and structure.
        Quality validation is handled by the Backlog Sweeper.
        """
        enhanced_story = story.copy()
        
        # Store the original title and description with formatting improvements
        enhanced_story['title'] = story.get('title', '')
        
        # Format description for better readability
        description = story.get('description', '') or story.get('user_story', '')
        if description:
            # Add line breaks for better readability if description is very long
            if len(description) > 150 and '. ' in description and '\n' not in description:
                # Split long sentences at sentence boundaries for readability
                sentences = description.split('. ')
                if len(sentences) > 1:
                    description = '.\n'.join(sentences[:-1]) + '.' + sentences[-1] if sentences[-1] else '.\n'.join(sentences)
        enhanced_story['description'] = description
        
        # Format acceptance criteria for better readability
        criteria = story.get('acceptance_criteria', [])
        if criteria:
            # If criteria is a single string with numbered items, split it
            if isinstance(criteria, str):
                # First try to split on numbered patterns like "1. ", "2. ", etc.
                import re
                criteria_parts = re.split(r'(\d+\.\s+)', criteria)
                formatted_criteria = []
                for i in range(1, len(criteria_parts), 2):
                    if i + 1 < len(criteria_parts):
                        criterion = criteria_parts[i + 1].strip()
                        if criterion:
                            formatted_criteria.append(criterion)
                
                # If no numbered patterns found, try to split on Given-When-Then patterns
                if not formatted_criteria:
                    # Split on "Given" at the beginning of sentences (but not the first one)
                    criteria_parts = re.split(r'(?<=\.)\s+(?=Given)', criteria)
                    formatted_criteria = [part.strip() for part in criteria_parts if part.strip()]
                
                enhanced_story['acceptance_criteria'] = formatted_criteria
            elif isinstance(criteria, list):
                # Clean up each criterion and ensure proper formatting
                formatted_criteria = []
                for criterion in criteria:
                    if isinstance(criterion, str):
                        # Check if this criterion contains multiple Given-When-Then blocks
                        clean_criterion = criterion.strip()
                        if clean_criterion:
                            # Split long criteria with multiple Given-When-Then patterns
                            if clean_criterion.count('Given') > 1:
                                # Split on "Given" but keep the first occurrence
                                import re
                                parts = re.split(r'(?<=\.)\s+(?=Given)', clean_criterion)
                                for part in parts:
                                    part = part.strip()
                                    if part:
                                        formatted_criteria.append(part)
                            else:
                                # Add line breaks within long criteria for readability
                                if len(clean_criterion) > 120 and ', ' in clean_criterion and '\n' not in clean_criterion:
                                    # Break at logical points (commas) for very long criteria
                                    parts = clean_criterion.split(', ')
                                    if len(parts) > 2:
                                        mid_point = len(parts) // 2
                                        clean_criterion = ', '.join(parts[:mid_point]) + ',\n' + ', '.join(parts[mid_point:])
                                formatted_criteria.append(clean_criterion)
                enhanced_story['acceptance_criteria'] = formatted_criteria
            else:
                enhanced_story['acceptance_criteria'] = criteria
        else:
            enhanced_story['acceptance_criteria'] = []
        
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
