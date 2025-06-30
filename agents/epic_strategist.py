from agents.base_agent import Agent
from config.config_loader import Config

print("🚀 Starting Epic Strategist test...")
class EpicStrategist(Agent):
    def __init__(self, config: Config):
        super().__init__("epic_strategist", config)

    def generate_epics(self, product_vision: str) -> str:
        """Generate epics from a product vision statement."""
        print(f"🧠 [EpicStrategist] Generating epics for: {product_vision}")
        return self.run(product_vision)