import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.qa_tester_agent import QATesterAgent

def test_qa_tester_agent():
    """Test QA Tester Agent with a sample feature."""
    
    print("🧪 Testing QA Tester Agent")
    print("=" * 50)
    
    # Initialize
    config = Config()
    qa_agent = QATesterAgent(config)
    
    # Sample feature for testing
    sample_feature = {
        "title": "Expense Categorization",
        "description": "Allow users to categorize their expenses into predefined and custom categories for better budget tracking and analysis.",
        "acceptance_criteria": [
            "User can select from predefined expense categories (Food, Transportation, Entertainment, etc.)",
            "User can create custom expense categories with name and color",
            "User can assign categories to individual expenses",
            "User can view expenses grouped by category",
            "User can edit or delete custom categories",
            "System prevents deletion of categories that have associated expenses"
        ],
        "priority": "High",
        "estimated_story_points": 8
    }
    
    print(f"📋 Testing feature: {sample_feature['title']}")
    print(f"📝 Description: {sample_feature['description']}")
    print()
    
    # Test 1: Generate test cases
    print("🔬 Test 1: Generating test cases...")
    test_cases = qa_agent.generate_test_cases(sample_feature)
    
    if test_cases:
        print(f"✅ Generated {len(test_cases)} test case(s)")
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test Case {i}:")
            print(f"   Title: {test_case.get('title', 'N/A')}")
            print(f"   Type: {test_case.get('type', 'N/A')}")
            print(f"   Priority: {test_case.get('priority', 'N/A')}")
            if 'gherkin' in test_case:
                gherkin = test_case['gherkin']
                print(f"   Scenario: {gherkin.get('scenario', 'N/A')}")
                print(f"   Given: {gherkin.get('given', [])}")
                print(f"   When: {gherkin.get('when', [])}")
                print(f"   Then: {gherkin.get('then', [])}")
    else:
        print("❌ No test cases generated")
    
    print("\n" + "=" * 50)
    
    # Test 2: Generate edge cases
    print("⚠️ Test 2: Generating edge cases...")
    edge_cases = qa_agent.generate_edge_cases(sample_feature)
    
    if edge_cases:
        print(f"✅ Generated {len(edge_cases)} edge case(s)")
        for i, edge_case in enumerate(edge_cases, 1):
            print(f"\n⚠️ Edge Case {i}:")
            print(f"   Title: {edge_case.get('title', 'N/A')}")
            print(f"   Category: {edge_case.get('category', 'N/A')}")
            print(f"   Description: {edge_case.get('description', 'N/A')}")
            print(f"   Risk Level: {edge_case.get('risk_level', 'N/A')}")
    else:
        print("❌ No edge cases generated")
    
    print("\n" + "=" * 50)
    
    # Test 3: Validate acceptance criteria
    print("✅ Test 3: Validating acceptance criteria...")
    validation = qa_agent.validate_acceptance_criteria(sample_feature)
    
    if validation:
        print("✅ Acceptance criteria validation completed")
        print(f"   Testability Score: {validation.get('testability_score', 'N/A')}/10")
        print(f"   Recommendations: {validation.get('recommendations', [])}")
        print(f"   Missing Scenarios: {validation.get('missing_scenarios', [])}")
        
        enhanced_criteria = validation.get('enhanced_criteria', [])
        if enhanced_criteria and enhanced_criteria != sample_feature.get('acceptance_criteria', []):
            print("   Enhanced Criteria:")
            for criterion in enhanced_criteria:
                print(f"     - {criterion}")
    else:
        print("❌ Acceptance criteria validation failed")

if __name__ == "__main__":
    test_qa_tester_agent()
