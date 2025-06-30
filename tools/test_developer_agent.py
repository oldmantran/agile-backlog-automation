from config.config_loader import Config
from agents.developer_agent import DeveloperAgent

config = Config()
agent = DeveloperAgent(config)

feature = {
    "title": "Energy Usage and Cost Correlation",
    "description": "Correlate energy usage data with real-time pricing to show users the cost of their consumption patterns. This feature offers visual insights through charts or reports for better understanding of spending."
}

tasks = agent.generate_tasks(feature)

print("\n🛠️ Developer Tasks:")
for t in tasks:
    print(f"- {t['title']}: {t['description']}")