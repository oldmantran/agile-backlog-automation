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