import json
from agents.base_agent import Agent
from config.config_loader import Config

class FeatureDecomposer(Agent):
    def __init__(self, config: Config):
        super().__init__("feature_decomposer", config)

    def decompose_epic(self, epic: dict) -> list[dict]:
        """Break down an epic into a list of features."""
        user_input = f"Epic: {epic['title']}\nDescription: {epic['description']}"
        print(f"🧩 [FeatureDecomposer] Decomposing epic: {epic['title']}")
        response = self.run(user_input)

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