import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.qa_tester_agent import QATesterAgent
import json

def test_qa_agent_individual_capabilities():
    """Test each QA agent capability individually to identify strengths and weaknesses."""
    
    print("🔬 QA Tester Agent - Individual Capability Assessment")
    print("=" * 70)
    
    # Initialize
    config = Config()
    qa_agent = QATesterAgent(config)
    
    # Sample feature for testing
    sample_feature = {
        "title": "User Authentication",
        "description": "Allow users to securely log in and log out of the application using email and password.",
        "acceptance_criteria": [
            "User can log in with valid credentials",
            "User sees error for invalid credentials",
            "User can log out successfully",
            "User session expires after inactivity"
        ],
        "priority": "High"
    }
    
    print(f"📋 Testing Feature: {sample_feature['title']}")
    print(f"📝 Description: {sample_feature['description']}")
    
    # Test 1: Detailed Test Case Analysis
    print(f"\n🧪 Test Case Generation Analysis")
    print("=" * 50)
    
    test_cases = qa_agent.generate_test_cases(sample_feature)
    
    if test_cases:
        print(f"✅ Generated {len(test_cases)} test cases")
        
        # Analyze functional vs non-functional
        functional_count = sum(1 for tc in test_cases if tc.get("type") == "functional")
        edge_count = sum(1 for tc in test_cases if tc.get("type") == "edge_case")
        
        print(f"📊 Breakdown:")
        print(f"   - Functional Tests: {functional_count}")
        print(f"   - Edge Cases: {edge_count}")
        
        # Check Gherkin quality
        well_formed_gherkin = 0
        for tc in test_cases:
            if "gherkin" in tc:
                gherkin = tc["gherkin"]
                if all(key in gherkin for key in ["given", "when", "then"]):
                    well_formed_gherkin += 1
                    
        print(f"   - Well-formed Gherkin: {well_formed_gherkin}/{len(test_cases)}")
        
        # Show sample test case
        if test_cases and "gherkin" in test_cases[0]:
            print(f"\n📝 Sample Test Case:")
            sample_tc = test_cases[0]
            print(f"   Title: {sample_tc.get('title', 'N/A')}")
            print(f"   Type: {sample_tc.get('type', 'N/A')}")
            if "gherkin" in sample_tc:
                gherkin = sample_tc["gherkin"]
                print(f"   Given: {gherkin.get('given', [])}")
                print(f"   When: {gherkin.get('when', [])}")
                print(f"   Then: {gherkin.get('then', [])}")
    else:
        print("❌ No test cases generated")
    
    # Test 2: Edge Case Analysis
    print(f"\n⚠️ Edge Case Generation Analysis")
    print("=" * 50)
    
    edge_cases = qa_agent.generate_edge_cases(sample_feature)
    
    if edge_cases:
        print(f"✅ Generated {len(edge_cases)} edge cases")
        
        # Categorize edge cases
        categories = {}
        risk_levels = {}
        
        for edge_case in edge_cases:
            category = edge_case.get("category", "unknown")
            risk = edge_case.get("risk_level", "unknown")
            
            categories[category] = categories.get(category, 0) + 1
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
            
        print(f"📊 Categories:")
        for category, count in categories.items():
            print(f"   - {category}: {count}")
            
        print(f"⚠️ Risk Levels:")
        for risk, count in risk_levels.items():
            print(f"   - {risk}: {count}")
            
        # Show high-risk edge cases
        high_risk_cases = [ec for ec in edge_cases if ec.get("risk_level") in ["Critical", "High"]]
        if high_risk_cases:
            print(f"\n🚨 High-Risk Edge Cases ({len(high_risk_cases)}):")
            for i, case in enumerate(high_risk_cases[:3], 1):  # Show first 3
                print(f"   {i}. {case.get('title', 'N/A')} (Risk: {case.get('risk_level', 'N/A')})")
                print(f"      {case.get('description', 'N/A')[:80]}...")
                
    else:
        print("❌ No edge cases generated")
    
    # Test 3: Acceptance Criteria Validation Analysis
    print(f"\n✅ Acceptance Criteria Validation Analysis")
    print("=" * 50)
    
    validation = qa_agent.validate_acceptance_criteria(sample_feature)
    
    print(f"🔍 Raw validation response:")
    print(json.dumps(validation, indent=2)[:500] + "..." if len(str(validation)) > 500 else json.dumps(validation, indent=2))
    
    if validation:
        print(f"✅ Validation completed")
        
        # Check structure
        has_score = "testability_score" in validation
        has_recommendations = "recommendations" in validation
        has_missing = "missing_scenarios" in validation
        has_enhanced = "enhanced_criteria" in validation
        
        print(f"📊 Response Structure:")
        print(f"   - Has testability score: {'✅' if has_score else '❌'}")
        print(f"   - Has recommendations: {'✅' if has_recommendations else '❌'}")
        print(f"   - Has missing scenarios: {'✅' if has_missing else '❌'}")
        print(f"   - Has enhanced criteria: {'✅' if has_enhanced else '❌'}")
        
        # Try to extract score
        if isinstance(validation, dict):
            # Check different possible score locations
            score_locations = [
                validation.get("testability_score"),
                validation.get("score"),
                validation.get("response", {}).get("testability_score") if isinstance(validation.get("response"), dict) else None
            ]
            
            score_found = False
            for score in score_locations:
                if score is not None:
                    print(f"📊 Testability Score Found: {score}")
                    score_found = True
                    break
                    
            if not score_found:
                print("⚠️ No testability score found in expected locations")
                
            # Check for recommendations
            recommendations = (
                validation.get("recommendations") or
                validation.get("response", {}).get("recommendations_for_improvement", []) if isinstance(validation.get("response"), dict) else []
            )
            
            if recommendations:
                print(f"💡 Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                    rec_text = str(rec)[:100] + "..." if len(str(rec)) > 100 else str(rec)
                    print(f"   {i}. {rec_text}")
            else:
                print("⚠️ No recommendations found")
                
    else:
        print("❌ Validation failed completely")
    
    # Overall Assessment
    print(f"\n🏆 Capability Summary")
    print("=" * 50)
    
    test_case_quality = "Good" if test_cases and len(test_cases) >= 5 else "Needs Improvement"
    edge_case_quality = "Good" if edge_cases and len(edge_cases) >= 8 else "Needs Improvement"
    validation_quality = "Good" if validation and len(str(validation)) > 100 else "Needs Improvement"
    
    print(f"🧪 Test Case Generation: {test_case_quality}")
    print(f"⚠️ Edge Case Identification: {edge_case_quality}")
    print(f"✅ Acceptance Criteria Validation: {validation_quality}")
    
    return {
        "test_cases": test_cases,
        "edge_cases": edge_cases,
        "validation": validation,
        "test_case_count": len(test_cases) if test_cases else 0,
        "edge_case_count": len(edge_cases) if edge_cases else 0,
        "validation_success": validation is not None and len(str(validation)) > 50
    }

if __name__ == "__main__":
    results = test_qa_agent_individual_capabilities()
    
    print(f"\n📈 Final Quality Metrics:")
    print(f"   Test Cases Generated: {results['test_case_count']}")
    print(f"   Edge Cases Generated: {results['edge_case_count']}")
    print(f"   Validation Success: {'✅' if results['validation_success'] else '❌'}")
