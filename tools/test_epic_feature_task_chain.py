import os
import json
import yaml
from datetime import datetime

from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.decomposition_agent import DecompositionAgent
from agents.developer_agent import DeveloperAgent

def main():
    config = Config()
    epic_agent = EpicStrategist(config)
    feature_agent = DecompositionAgent(config)
    dev_agent = DeveloperAgent(config)

    product_vision = (
        "Create a smart home energy dashboard that helps users monitor, optimize, "
        "and reduce their electricity usage across multiple devices and rooms."
    )

    print(f"\n🚀 Product Vision:\n{product_vision}\n")

    epics = epic_agent.generate_epics(product_vision)
    output = {
        "product_vision": product_vision,
        "epics": []
    }

    for i, epic in enumerate(epics, 1):
        print(f"\n📦 Epic {i}: {epic['title']}")
        print(f"   {epic['description']}")

        features = feature_agent.decompose_epic(epic)
        epic["features"] = []

        for j, feature in enumerate(features, 1):
            print(f"   🔹 Feature {j}: {feature['title']}")
            print(f"      {feature['description']}")

            tasks = dev_agent.generate_tasks(feature)
            feature["tasks"] = tasks

            for k, task in enumerate(tasks, 1):
                print(f"      🛠️ Task {k}: {task['title']}")
                print(f"         {task['description']}")

            epic["features"].append(feature)

        output["epics"].append(epic)

    # Save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)

    json_path = f"output/backlog_{timestamp}.json"
    yaml_path = f"output/backlog_{timestamp}.yaml"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, sort_keys=False, allow_unicode=True)

    print(f"\n💾 JSON saved to: {json_path}")
    print(f"📝 YAML saved to: {yaml_path}")

if __name__ == "__main__":
    main()