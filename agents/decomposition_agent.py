import json
from agents.base_agent import Agent
from config.config_loader import Config

class DecompositionAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("decomposition_agent", config)

    def decompose_epic(self, epic: dict, context: dict = None) -> list[dict]:
        """Break down an epic into detailed features with contextual information."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'integrations': context.get('integrations', 'standard APIs') if context else 'standard APIs'
        }
        
        user_input = f"""
Epic: {epic.get('title', 'Unknown Epic')}
Description: {epic.get('description', 'No description provided')}
Priority: {epic.get('priority', 'Medium')}
Business Value: {epic.get('business_value', 'Not specified')}
"""
        
        print(f"🔧 [DecompositionAgent] Decomposing epic: {epic.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

        try:
            # Handle empty response
            if not response or not response.strip():
                print("⚠️ Empty response from Grok")
                return []
            
            # Check for markdown code blocks
            if "```json" in response:
                print("🔍 Extracting JSON from markdown...")
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            
            features = json.loads(response)
            if isinstance(features, list):
                return features
            else:
                print("⚠️ Grok response was not a list.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []

    def decompose_feature_to_user_stories(self, feature: dict, context: dict = None) -> list[dict]:
        """Break down a feature into detailed user stories with story points."""
        
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
User Stories: {feature.get('user_stories', [])}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}
Priority: {feature.get('priority', 'Medium')}
Estimated Story Points: {feature.get('estimated_story_points', 'Not specified')}
"""
        
        print(f"📱 [DecompositionAgent] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Use a new prompt template for user story decomposition
        response = self.run_with_template(user_input, prompt_context, template_name="user_story_decomposer")

        try:
            user_stories = json.loads(response)
            
            # Handle if the response is a list of features instead of user stories
            if isinstance(user_stories, list) and len(user_stories) > 0:
                # Check if these look like user stories or features
                first_item = user_stories[0]
                if 'user_stories' in first_item:
                    # This is actually a list of features, extract the user stories
                    print("🔄 Response contains features, extracting user stories...")
                    extracted_stories = []
                    for feature in user_stories:
                        stories = feature.get('user_stories', [])
                        if isinstance(stories, list):
                            for story_text in stories:
                                extracted_stories.append({
                                    'title': f"User Story from {feature.get('title', 'Feature')}",
                                    'user_story': story_text,
                                    'description': f"Extracted from feature: {feature.get('description', '')}",
                                    'story_points': feature.get('estimated_story_points', 5) // len(stories) if stories else 5,
                                    'priority': feature.get('priority', 'Medium'),
                                    'acceptance_criteria': feature.get('acceptance_criteria', [])
                                })
                    return extracted_stories
                else:
                    # This looks like actual user stories
                    return user_stories
            elif isinstance(user_stories, dict) and 'user_stories' in user_stories:
                return user_stories['user_stories']
            else:
                print("⚠️ Grok response was not in expected format.")
                print("🔄 Using fallback user story generation...")
                return self._create_fallback_user_stories(feature)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            print("🔄 Using fallback user story generation...")
            return self._create_fallback_user_stories(feature)

    def run_with_template(self, user_input: str, context: dict, template_name: str) -> str:
        """Run with a specific prompt template (fallback to default if template doesn't exist)."""
        try:
            # Import prompt manager
            from utils.prompt_manager import prompt_manager
            
            # Try to get the specific template prompt
            system_prompt = prompt_manager.get_prompt(template_name, context)
            
            # Make the API call with the specific template
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    { "role": "system", "content": system_prompt },
                    { "role": "user", "content": user_input }
                ]
            }

            print(f"📤 Sending to Grok with {template_name} template...")
            
            import requests
            response = requests.post(url, headers=headers, json=payload, timeout=60)  # Increased timeout
            response.raise_for_status()
            data = response.json()

            print(f"📥 Response received from {template_name} template")
            return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"⚠️ Template {template_name} failed: {e}, using default template")
            return self.run(user_input, context)

    def _create_fallback_user_stories(self, feature: dict) -> list[dict]:
        """Create basic user stories as fallback when template fails."""
        print("🔄 Creating fallback user stories...")
        
        title = feature.get('title', 'Feature')
        description = feature.get('description', 'No description')
        acceptance_criteria = feature.get('acceptance_criteria', [])
        priority = feature.get('priority', 'Medium')
        story_points = feature.get('estimated_story_points', 8)
        
        # Create 2-3 basic user stories based on acceptance criteria
        user_stories = []
        
        if acceptance_criteria:
            for i, criterion in enumerate(acceptance_criteria[:3]):  # Max 3 stories
                story = {
                    'title': f"{title} - {criterion[:50]}...",
                    'user_story': f"As a user, I want to {criterion.lower()} so that I can effectively use the {title.lower()} feature",
                    'description': f"This user story covers: {criterion}. {description[:100]}...",
                    'story_points': max(1, story_points // len(acceptance_criteria[:3])),
                    'priority': priority,
                    'acceptance_criteria': [criterion],
                    'dependencies': [],
                    'definition_of_ready': ['Requirements clarified', 'UI mockups available'],
                    'definition_of_done': ['Code complete', 'Tests passing', 'Code reviewed'],
                    'category': 'feature_implementation',
                    'user_type': 'general_user'
                }
                user_stories.append(story)
        else:
            # Create a single basic user story
            story = {
                'title': f"{title} Implementation",
                'user_story': f"As a user, I want to use {title.lower()} so that I can benefit from its functionality",
                'description': description,
                'story_points': story_points,
                'priority': priority,
                'acceptance_criteria': [f"User can access {title.lower()}", f"User can use {title.lower()} effectively"],
                'dependencies': [],
                'definition_of_ready': ['Requirements clarified', 'UI mockups available'],
                'definition_of_done': ['Code complete', 'Tests passing', 'Code reviewed'],
                'category': 'feature_implementation',
                'user_type': 'general_user'
            }
            user_stories.append(story)
        
        return user_stories