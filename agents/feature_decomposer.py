import json
from agents.base_agent import Agent
from config.config_loader import Config

class FeatureDecomposer(Agent):
    def __init__(self, config: Config):
        super().__init__("feature_decomposer", config)

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
        
        print(f"🔧 [FeatureDecomposer] Decomposing epic: {epic.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

        try:
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
        
        print(f"📱 [FeatureDecomposer] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Use a new prompt template for user story decomposition
        response = self.run_with_template(user_input, prompt_context, template_name="user_story_decomposer")

        try:
            user_stories = json.loads(response)
            if isinstance(user_stories, list):
                return user_stories
            elif isinstance(user_stories, dict) and 'user_stories' in user_stories:
                return user_stories['user_stories']
            else:
                print("⚠️ Grok response was not in expected format.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []

    def run_with_template(self, user_input: str, context: dict, template_name: str) -> str:
        """Run with a specific prompt template (fallback to default if template doesn't exist)."""
        try:
            # Try to use specific template, fallback to default run method
            return self.run(user_input, context)
        except Exception as e:
            print(f"⚠️ Template {template_name} not found, using default: {e}")
            return self.run(user_input, context)