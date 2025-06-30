import json
from agents.base_agent import Agent
from config.config_loader import Config

class DeveloperAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("developer_agent", config)

    def generate_tasks(self, feature: dict) -> list[dict]:
        """Generate technical tasks from a feature description."""
        user_input = f"Feature: {feature['title']}\nDescription: {feature['description']}"
        print(f"💻 [DeveloperAgent] Generating tasks for: {feature['title']}")
        response = self.run(user_input)

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