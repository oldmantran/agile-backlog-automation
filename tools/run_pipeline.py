import os
import json
import yaml
import argparse
from datetime import datetime

from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.feature_decomposer import FeatureDecomposer
from agents.developer_agent import DeveloperAgent
from agents.qa_tester_agent import QATesterAgent

# Run full pipeline interactively
    #python tools/run_pipeline.py

# Run only the Developer Agent on a YAML file
    #python tools/run_pipeline.py --run developer --input output/backlog_20250701_153000.yaml

# Run only the QA Agent on a YAML file with features
    #python tools/run_pipeline.py --run qa --input output/backlog_20250701_153000.yaml

# Regenerate features only
    #python tools/run_pipeline.py --run feature --input my_epics.yaml

# Run Developer Agent on a YAML file with features
    #python tools/run_pipeline.py --run developer --input output/features_only.yaml

# Run Feature Decomposer on a YAML file with epics
    #python tools/run_pipeline.py --run feature --input output/epics_only.yaml

def load_input_from_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_pipeline(data: dict, run_stage: str):
    config = Config()
    epic_agent = EpicStrategist(config)
    feature_agent = FeatureDecomposer(config)
    dev_agent = DeveloperAgent(config)
    qa_agent = QATesterAgent(config)

    product_vision = data.get("product_vision", "")
    epics = data.get("epics", [])

    if run_stage == "epic":
        epics = epic_agent.generate_epics(product_vision)

    for epic in epics:
        if run_stage in ["all", "feature"]:
            features = feature_agent.decompose_epic(epic)
        else:
            features = epic.get("features", [])

        epic["features"] = []

        for feature in features:
            if run_stage in ["all", "developer"]:
                tasks = dev_agent.generate_tasks(feature)
            else:
                tasks = feature.get("tasks", [])

            if run_stage in ["all", "qa"]:
                test_cases = qa_agent.generate_test_cases(feature)
                edge_cases = qa_agent.generate_edge_cases(feature)
                validation = qa_agent.validate_acceptance_criteria(feature)
                
                feature["test_cases"] = test_cases
                feature["edge_cases"] = edge_cases
                feature["qa_validation"] = validation
            else:
                feature["test_cases"] = feature.get("test_cases", [])
                feature["edge_cases"] = feature.get("edge_cases", [])
                feature["qa_validation"] = feature.get("qa_validation", {})

            feature["tasks"] = tasks
            epic["features"].append(feature)

    output = {
        "product_vision": product_vision,
        "epics": epics
    }
    save_output(output)

def save_output(data: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)

    json_path = f"output/backlog_{timestamp}.json"
    yaml_path = f"output/backlog_{timestamp}.yaml"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    print(f"\n💾 JSON saved to: {json_path}")
    print(f"📝 YAML saved to: {yaml_path}")

def load_input_from_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run backlog automation pipeline.")
    parser.add_argument("--run", choices=["all", "epic", "feature", "developer", "qa"], default="all", help="Which stage(s) to run")
    parser.add_argument("--input", type=str, help="Path to YAML file with product_vision")

    args = parser.parse_args()

    if args.input:
        data = load_input_from_yaml(args.input)
    else:
        vision = input("🧠 Enter product vision: ")
        data = {"product_vision": vision, "epics": []}

    run_pipeline(data, args.run)