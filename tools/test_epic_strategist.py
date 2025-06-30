from config.config_loader import Config
from agents.epic_strategist import EpicStrategist

config = Config()
agent = EpicStrategist(config)

vision = "Build a secure, mobile-first banking app for freelancers to manage invoices, taxes, and savings."
epics = agent.generate_epics(vision)

print("\n📦 Epics:")
print(epics)