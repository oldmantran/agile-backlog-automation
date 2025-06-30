from agents.base_agent import Agent
from config.config_loader import Config
import json

print("🚀 Starting Epic Strategist test...")
import json

class EpicStrategist(Agent):
    def __init__(self, config: Config):
        super().__init__("epic_strategist", config)

    def generate_epics(self, product_vision: str) -> list[dict]:
        """Generate epics from a product vision statement."""
        print(f"🧠 [EpicStrategist] Generating epics for: {product_vision}")
        response = self.run(product_vision)

        try:
            epics = json.loads(response)
            if isinstance(epics, list):
                return epics
            else:
                print("⚠️ Grok response was not a list.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []