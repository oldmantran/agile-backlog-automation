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
from utils.project_context import ProjectContext

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

def run_pipeline(data: dict, run_stage: str, project_type: str = None, custom_context: dict = None):
    config = Config()
    
    # Initialize project context
    project_context = ProjectContext(config)
    
    # Apply project type if specified
    if project_type:
        project_context.set_project_type(project_type)
        print(f"🏗️ Applied {project_type} project context")
    
    # Apply custom context if specified
    if custom_context:
        project_context.update_context(custom_context)
        print(f"🔧 Applied custom context: {list(custom_context.keys())}")
    
    # Print context summary
    print("\n" + project_context.get_context_summary())
    print()
    
    # Initialize agents
    epic_agent = EpicStrategist(config)
    feature_agent = FeatureDecomposer(config)
    dev_agent = DeveloperAgent(config)
    qa_agent = QATesterAgent(config)

    product_vision = data.get("product_vision", "")
    epics = data.get("epics", [])

    if run_stage == "epic":
        print("🎯 Generating epics with strategic context...")
        context = project_context.get_context('epic_strategist')
        epics = epic_agent.generate_epics(product_vision, context)

    for epic in epics:
        if run_stage in ["all", "feature"]:
            print(f"🔍 Decomposing epic: {epic.get('title', 'Untitled Epic')}")
            context = project_context.get_context('feature_decomposer')
            features = feature_agent.decompose_epic(epic, context)
        else:
            features = epic.get("features", [])

        epic["features"] = []

        for feature in features:
            if run_stage in ["all", "developer"]:
                print(f"⚙️ Generating tasks for feature: {feature.get('title', 'Untitled Feature')}")
                context = project_context.get_context('developer_agent')
                tasks = dev_agent.generate_tasks(feature, context)
            else:
                tasks = feature.get("tasks", [])

            if run_stage in ["all", "qa"]:
                print(f"🧪 Generating QA deliverables for feature: {feature.get('title', 'Untitled Feature')}")
                context = project_context.get_context('qa_tester_agent')
                test_cases = qa_agent.generate_test_cases(feature, context)
                edge_cases = qa_agent.generate_edge_cases(feature, context)
                validation = qa_agent.validate_acceptance_criteria(feature, context)
                
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
    parser.add_argument("--project-type", choices=["fintech", "healthcare", "ecommerce", "education", "mobile_app", "saas"], help="Apply predefined project context")
    parser.add_argument("--project-name", type=str, help="Override project name")
    parser.add_argument("--domain", type=str, help="Override project domain")
    parser.add_argument("--tech-stack", type=str, help="Override technology stack")
    parser.add_argument("--team-size", type=str, help="Override team size")
    parser.add_argument("--timeline", type=str, help="Override project timeline")

    args = parser.parse_args()
    
    # Build custom context from CLI arguments
    custom_context = {}
    if args.project_name:
        custom_context['project_name'] = args.project_name
    if args.domain:
        custom_context['domain'] = args.domain
    if args.tech_stack:
        custom_context['tech_stack'] = args.tech_stack
    if args.team_size:
        custom_context['team_size'] = args.team_size
    if args.timeline:
        custom_context['timeline'] = args.timeline

    if args.input:
        data = load_input_from_yaml(args.input)
    else:
        vision = input("🧠 Enter product vision: ")
        data = {"product_vision": vision, "epics": []}

    run_pipeline(data, args.run, args.project_type, custom_context if custom_context else None)