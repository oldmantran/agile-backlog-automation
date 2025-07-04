import os
import json
import yaml
from datetime import datetime
from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.decomposition_agent import DecompositionAgent

def main():
    config = Config()
    epic_agent = EpicStrategist(config)
    feature_agent = DecompositionAgent(config)

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
        epic["features"] = features
        output["epics"].append(epic)

        for j, feature in enumerate(features, 1):
            print(f"   🔹 Feature {j}: {feature['title']}")
            print(f"      {feature['description']}")

    # Save JSON to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/epics_and_features_{timestamp}.json"

    os.makedirs("output", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Output saved to: {filename}")

    # Save YAML version
    yaml_filename = filename.replace(".json", ".yaml")
    with open(yaml_filename, "w", encoding="utf-8") as f:
        yaml.dump(output, f, sort_keys=False, allow_unicode=True)

    print(f"📝 YAML output saved to: {yaml_filename}")

if __name__ == "__main__":
    main()