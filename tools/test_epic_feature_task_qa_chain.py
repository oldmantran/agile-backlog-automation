import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.feature_decomposer_agent import FeatureDecomposerAgent
from agents.developer_agent import DeveloperAgent
from agents.qa_tester_agent import QATesterAgent

def test_epic_feature_task_qa_chain():
    """Test the full chain: Epic → Features → Tasks → QA Test Cases"""
    
    print("🔗 Testing Epic → Feature → Task → QA Chain")
    print("=" * 60)
    
    # Initialize agents
    config = Config()
    epic_agent = EpicStrategist(config)
    feature_agent = FeatureDecomposerAgent(config)
    dev_agent = DeveloperAgent(config)
    qa_agent = QATesterAgent(config)
    
    # Sample product vision
    product_vision = "Build a personal finance management app that helps college students track expenses, create budgets, and save money through intelligent insights and goal setting."
    
    print(f"🧠 Product Vision: {product_vision}")
    print()
    
    # Step 1: Generate epics
    print("📊 Step 1: Generating epics...")
    epics = epic_agent.generate_epics(product_vision)
    
    if not epics:
        print("❌ No epics generated, stopping test")
        return
    
    print(f"✅ Generated {len(epics)} epic(s)")
    
    # Take the first epic for testing
    epic = epics[0]
    print(f"🎯 Using epic: {epic.get('title', 'Unknown')}")
    print()
    
    # Step 2: Generate features
    print("🔧 Step 2: Generating features...")
    features = feature_agent.decompose_epic(epic)
    
    if not features:
        print("❌ No features generated, stopping test")
        return
        
    print(f"✅ Generated {len(features)} feature(s)")
    
    # Take the first feature for testing
    feature = features[0]
    print(f"📝 Using feature: {feature.get('title', 'Unknown')}")
    print()
    
    # Step 3: Generate developer tasks
    print("💻 Step 3: Generating developer tasks...")
    tasks = dev_agent.generate_tasks(feature)
    
    print(f"✅ Generated {len(tasks)} task(s)")
    if tasks:
        print("📋 Sample task:")
        task = tasks[0]
        print(f"   Title: {task.get('title', 'N/A')}")
        print(f"   Type: {task.get('type', 'N/A')}")
        print(f"   Estimated Hours: {task.get('estimated_hours', 'N/A')}")
    print()
    
    # Step 4: Generate QA test cases
    print("🧪 Step 4: Generating QA test cases...")
    test_cases = qa_agent.generate_test_cases(feature)
    
    print(f"✅ Generated {len(test_cases)} test case(s)")
    if test_cases:
        print("🔬 Sample test case:")
        test_case = test_cases[0]
        print(f"   Title: {test_case.get('title', 'N/A')}")
        print(f"   Type: {test_case.get('type', 'N/A')}")
        print(f"   Priority: {test_case.get('priority', 'N/A')}")
        if 'gherkin' in test_case:
            gherkin = test_case['gherkin']
            print(f"   Scenario: {gherkin.get('scenario', 'N/A')}")
    print()
    
    # Step 5: Generate edge cases
    print("⚠️ Step 5: Generating edge cases...")
    edge_cases = qa_agent.generate_edge_cases(feature)
    
    print(f"✅ Generated {len(edge_cases)} edge case(s)")
    if edge_cases:
        print("⚠️ Sample edge case:")
        edge_case = edge_cases[0]
        print(f"   Title: {edge_case.get('title', 'N/A')}")
        print(f"   Category: {edge_case.get('category', 'N/A')}")
        print(f"   Risk Level: {edge_case.get('risk_level', 'N/A')}")
    print()
    
    # Step 6: Validate acceptance criteria
    print("✅ Step 6: Validating acceptance criteria...")
    validation = qa_agent.validate_acceptance_criteria(feature)
    
    if validation:
        print("✅ Validation completed")
        print(f"   Testability Score: {validation.get('testability_score', 'N/A')}/10")
        recommendations = validation.get('recommendations', [])
        if recommendations:
            print(f"   Recommendations: {recommendations[:2]}...")  # Show first 2
    
    print("\n" + "=" * 60)
    print("🎉 Full chain test completed successfully!")
    print("\n📊 Summary:")
    print(f"   Epic: {epic.get('title', 'Unknown')}")
    print(f"   Feature: {feature.get('title', 'Unknown')}")
    print(f"   Tasks: {len(tasks)}")
    print(f"   Test Cases: {len(test_cases)}")
    print(f"   Edge Cases: {len(edge_cases)}")
    print(f"   Testability Score: {validation.get('testability_score', 'N/A')}/10")

if __name__ == "__main__":
    test_epic_feature_task_qa_chain()
