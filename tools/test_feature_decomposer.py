from config.config_loader import Config
from agents.decomposition_agent import DecompositionAgent

config = Config()
agent = DecompositionAgent(config)

epic = {
    "title": "Invoice Management",
    "description": "Allow freelancers to create, send, and track invoices from their mobile devices."
}

features = agent.decompose_epic(epic)

print("\n🧱 Features:")
for f in features:
    print(f"- {f['title']}: {f['description']}")