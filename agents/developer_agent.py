import json
from agents.base_agent import Agent
from config.config_loader import Config

class DeveloperAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("developer_agent", config)

    def generate_tasks(self, feature: dict, context: dict = None) -> list[dict]:
        """Generate technical tasks from a feature description with contextual information."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'tech_stack': context.get('tech_stack', 'Modern Web Stack') if context else 'Modern Web Stack',
            'architecture_pattern': context.get('architecture_pattern', 'MVC') if context else 'MVC',
            'database_type': context.get('database_type', 'SQL Database') if context else 'SQL Database',
            'cloud_platform': context.get('cloud_platform', 'Cloud Platform') if context else 'Cloud Platform',
            'team_size': context.get('team_size', '5-8 developers') if context else '5-8 developers',
            'sprint_duration': context.get('sprint_duration', '2 weeks') if context else '2 weeks'
        }
        
        user_input = f"""
Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}
Priority: {feature.get('priority', 'Medium')}
Estimated Story Points: {feature.get('estimated_story_points', 'Not specified')}
"""
        
        print(f"💻 [DeveloperAgent] Generating tasks for: {feature.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

        try:
            tasks = json.loads(response)
            if isinstance(tasks, list):
                return tasks
            else:
                print("⚠️ Grok response was not a list.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []