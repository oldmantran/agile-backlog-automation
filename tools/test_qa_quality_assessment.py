import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from agents.qa_tester_agent import QATesterAgent
import json

def assess_test_case_quality(test_cases: list) -> dict:
    """Assess the quality of generated test cases."""
    
    assessment = {
        "total_test_cases": len(test_cases),
        "functional_tests": 0,
        "edge_cases": 0,
        "gherkin_quality": {"well_formed": 0, "incomplete": 0},
        "priority_distribution": {"High": 0, "Medium": 0, "Low": 0, "N/A": 0},
        "coverage_areas": {
            "happy_path": 0,
            "error_handling": 0,
            "boundary_conditions": 0,
            "security": 0,
            "performance": 0,
            "usability": 0,
            "integration": 0
        },
        "gherkin_structure": {
            "complete_scenarios": 0,
            "has_given": 0,
            "has_when": 0,
            "has_then": 0,
            "realistic_steps": 0
        },
        "test_data_quality": {
            "has_test_data": 0,
            "realistic_data": 0,
            "edge_case_data": 0
        }
    }
    
    for test_case in test_cases:
        # Count test types
        test_type = test_case.get("type", "unknown")
        if test_type == "functional":
            assessment["functional_tests"] += 1
        elif test_type == "edge_case":
            assessment["edge_cases"] += 1
            
        # Priority distribution
        priority = test_case.get("priority", "N/A")
        if priority in assessment["priority_distribution"]:
            assessment["priority_distribution"][priority] += 1
        else:
            assessment["priority_distribution"]["N/A"] += 1
            
        # Gherkin quality analysis
        if "gherkin" in test_case:
            gherkin = test_case["gherkin"]
            if all(key in gherkin for key in ["given", "when", "then"]):
                assessment["gherkin_quality"]["well_formed"] += 1
                assessment["gherkin_structure"]["complete_scenarios"] += 1
                
                if gherkin.get("given"):
                    assessment["gherkin_structure"]["has_given"] += 1
                if gherkin.get("when"):
                    assessment["gherkin_structure"]["has_when"] += 1
                if gherkin.get("then"):
                    assessment["gherkin_structure"]["has_then"] += 1
                    
                # Check for realistic steps
                all_steps = []
                all_steps.extend(gherkin.get("given", []))
                all_steps.extend(gherkin.get("when", []))
                all_steps.extend(gherkin.get("then", []))
                
                if any("User" in step for step in all_steps):
                    assessment["gherkin_structure"]["realistic_steps"] += 1
            else:
                assessment["gherkin_quality"]["incomplete"] += 1
                
        # Test data quality
        if "test_data" in test_case:
            assessment["test_data_quality"]["has_test_data"] += 1
            test_data = test_case["test_data"]
            
            # Check for realistic data
            if any(isinstance(v, str) and len(v) > 3 for v in test_data.values()):
                assessment["test_data_quality"]["realistic_data"] += 1
                
        # Coverage area analysis based on test content
        title = test_case.get("title", "").lower()
        description = test_case.get("description", "").lower()
        content = f"{title} {description}".lower()
        
        if any(word in content for word in ["success", "valid", "correct", "create", "select"]):
            assessment["coverage_areas"]["happy_path"] += 1
        if any(word in content for word in ["error", "invalid", "fail", "prevent", "cannot"]):
            assessment["coverage_areas"]["error_handling"] += 1
        if any(word in content for word in ["maximum", "minimum", "boundary", "limit", "empty"]):
            assessment["coverage_areas"]["boundary_conditions"] += 1
        if any(word in content for word in ["sql", "xss", "injection", "security", "unauthorized"]):
            assessment["coverage_areas"]["security"] += 1
        if any(word in content for word in ["performance", "load", "concurrent", "timeout"]):
            assessment["coverage_areas"]["performance"] += 1
        if any(word in content for word in ["accessibility", "usability", "user experience"]):
            assessment["coverage_areas"]["usability"] += 1
        if any(word in content for word in ["database", "api", "integration", "connection"]):
            assessment["coverage_areas"]["integration"] += 1
            
    return assessment

def assess_edge_cases_quality(edge_cases: list) -> dict:
    """Assess the quality of generated edge cases."""
    
    assessment = {
        "total_edge_cases": len(edge_cases),
        "categories": {
            "boundary_condition": 0,
            "error_handling": 0,
            "security": 0,
            "performance": 0,
            "integration": 0,
            "usability": 0
        },
        "risk_levels": {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        },
        "completeness": {
            "has_description": 0,
            "has_test_scenario": 0,
            "has_expected_behavior": 0,
            "has_risk_level": 0
        },
        "security_coverage": {
            "sql_injection": False,
            "xss": False,
            "unauthorized_access": False
        },
        "boundary_coverage": {
            "max_length": False,
            "min_length": False,
            "max_count": False,
            "empty_input": False
        }
    }
    
    for edge_case in edge_cases:
        # Category distribution
        category = edge_case.get("category", "unknown")
        if category in assessment["categories"]:
            assessment["categories"][category] += 1
            
        # Risk level distribution
        risk_level = edge_case.get("risk_level", "Unknown")
        if risk_level in assessment["risk_levels"]:
            assessment["risk_levels"][risk_level] += 1
            
        # Completeness check
        if edge_case.get("description"):
            assessment["completeness"]["has_description"] += 1
        if edge_case.get("test_scenario"):
            assessment["completeness"]["has_test_scenario"] += 1
        if edge_case.get("expected_behavior"):
            assessment["completeness"]["has_expected_behavior"] += 1
        if edge_case.get("risk_level"):
            assessment["completeness"]["has_risk_level"] += 1
            
        # Security coverage analysis
        content = f"{edge_case.get('title', '')} {edge_case.get('description', '')}".lower()
        if "sql" in content and "injection" in content:
            assessment["security_coverage"]["sql_injection"] = True
        if "xss" in content or "script" in content:
            assessment["security_coverage"]["xss"] = True
        if "unauthorized" in content or "access" in content:
            assessment["security_coverage"]["unauthorized_access"] = True
            
        # Boundary coverage analysis
        if "maximum" in content and "length" in content:
            assessment["boundary_coverage"]["max_length"] = True
        if "minimum" in content or "empty" in content:
            assessment["boundary_coverage"]["min_length"] = True
        if "maximum" in content and ("number" in content or "count" in content):
            assessment["boundary_coverage"]["max_count"] = True
        if "empty" in content:
            assessment["boundary_coverage"]["empty_input"] = True
            
    return assessment

def assess_acceptance_criteria_validation(validation: dict) -> dict:
    """Assess the quality of acceptance criteria validation."""
    
    assessment = {
        "validation_completeness": {
            "has_testability_score": "testability_score" in validation,
            "has_recommendations": "recommendations" in validation and len(validation.get("recommendations", [])) > 0,
            "has_missing_scenarios": "missing_scenarios" in validation,
            "has_enhanced_criteria": "enhanced_criteria" in validation
        },
        "score_analysis": {
            "original_score": validation.get("testability_score", {}).get("original", 0) if isinstance(validation.get("testability_score"), dict) else 0,
            "enhanced_score": validation.get("testability_score", {}).get("enhanced", 0) if isinstance(validation.get("testability_score"), dict) else 0,
            "improvement": 0
        },
        "recommendations_quality": {
            "count": len(validation.get("recommendations", [])),
            "addresses_constraints": False,
            "addresses_error_handling": False,
            "addresses_performance": False,
            "addresses_accessibility": False
        },
        "missing_scenarios_coverage": {
            "count": len(validation.get("missing_scenarios", [])),
            "covers_security": False,
            "covers_boundary": False,
            "covers_performance": False,
            "covers_usability": False
        }
    }
    
    # Calculate improvement
    if isinstance(validation.get("testability_score"), dict):
        original = validation["testability_score"].get("original", 0)
        enhanced = validation["testability_score"].get("enhanced", 0)
        assessment["score_analysis"]["improvement"] = enhanced - original
    
    # Analyze recommendations quality
    recommendations = validation.get("recommendations", [])
    if isinstance(recommendations, list):
        recommendations_text = " ".join(str(rec) for rec in recommendations).lower()
        assessment["recommendations_quality"]["addresses_constraints"] = "constraint" in recommendations_text or "validation" in recommendations_text
        assessment["recommendations_quality"]["addresses_error_handling"] = "error" in recommendations_text or "message" in recommendations_text
        assessment["recommendations_quality"]["addresses_performance"] = "performance" in recommendations_text or "load" in recommendations_text
        assessment["recommendations_quality"]["addresses_accessibility"] = "accessibility" in recommendations_text or "wcag" in recommendations_text
        
    # Analyze missing scenarios coverage
    missing_scenarios = validation.get("missing_scenarios", [])
    if isinstance(missing_scenarios, list):
        scenarios_text = " ".join(str(scenario) for scenario in missing_scenarios).lower()
        assessment["missing_scenarios_coverage"]["covers_security"] = "security" in scenarios_text or "xss" in scenarios_text or "sql" in scenarios_text
        assessment["missing_scenarios_coverage"]["covers_boundary"] = "boundary" in scenarios_text or "maximum" in scenarios_text or "minimum" in scenarios_text
        assessment["missing_scenarios_coverage"]["covers_performance"] = "performance" in scenarios_text or "load" in scenarios_text
        assessment["missing_scenarios_coverage"]["covers_usability"] = "usability" in scenarios_text or "accessibility" in scenarios_text
        
    return assessment

def print_quality_report(assessment_type: str, assessment: dict):
    """Print a formatted quality assessment report."""
    
    print(f"\n📊 {assessment_type} Quality Assessment")
    print("=" * 60)
    
    if assessment_type == "Test Cases":
        print(f"📈 Overall Statistics:")
        print(f"   Total Test Cases: {assessment['total_test_cases']}")
        print(f"   Functional Tests: {assessment['functional_tests']}")
        print(f"   Edge Cases: {assessment['edge_cases']}")
        
        print(f"\n🎯 Priority Distribution:")
        for priority, count in assessment['priority_distribution'].items():
            print(f"   {priority}: {count}")
            
        print(f"\n🧪 Gherkin Quality:")
        print(f"   Well-formed scenarios: {assessment['gherkin_quality']['well_formed']}")
        print(f"   Complete scenarios: {assessment['gherkin_structure']['complete_scenarios']}")
        print(f"   Realistic steps: {assessment['gherkin_structure']['realistic_steps']}")
        
        print(f"\n🎯 Coverage Areas:")
        for area, count in assessment['coverage_areas'].items():
            print(f"   {area.replace('_', ' ').title()}: {count}")
            
        print(f"\n📊 Test Data Quality:")
        print(f"   Has test data: {assessment['test_data_quality']['has_test_data']}")
        print(f"   Realistic data: {assessment['test_data_quality']['realistic_data']}")
        
    elif assessment_type == "Edge Cases":
        print(f"📈 Overall Statistics:")
        print(f"   Total Edge Cases: {assessment['total_edge_cases']}")
        
        print(f"\n🏷️ Category Distribution:")
        for category, count in assessment['categories'].items():
            print(f"   {category.replace('_', ' ').title()}: {count}")
            
        print(f"\n⚠️ Risk Level Distribution:")
        for risk, count in assessment['risk_levels'].items():
            print(f"   {risk}: {count}")
            
        print(f"\n✅ Completeness:")
        for aspect, count in assessment['completeness'].items():
            print(f"   {aspect.replace('_', ' ').title()}: {count}/{assessment['total_edge_cases']}")
            
        print(f"\n🔒 Security Coverage:")
        for security_type, covered in assessment['security_coverage'].items():
            status = "✅" if covered else "❌"
            print(f"   {security_type.replace('_', ' ').title()}: {status}")
            
        print(f"\n📏 Boundary Coverage:")
        for boundary_type, covered in assessment['boundary_coverage'].items():
            status = "✅" if covered else "❌"
            print(f"   {boundary_type.replace('_', ' ').title()}: {status}")
            
    elif assessment_type == "Acceptance Criteria Validation":
        print(f"📈 Validation Completeness:")
        for aspect, present in assessment['validation_completeness'].items():
            status = "✅" if present else "❌"
            print(f"   {aspect.replace('_', ' ').title()}: {status}")
            
        print(f"\n📊 Score Analysis:")
        print(f"   Original Score: {assessment['score_analysis']['original_score']}/10")
        print(f"   Enhanced Score: {assessment['score_analysis']['enhanced_score']}/10")
        print(f"   Improvement: +{assessment['score_analysis']['improvement']}")
        
        print(f"\n💡 Recommendations Quality:")
        print(f"   Count: {assessment['recommendations_quality']['count']}")
        for aspect, addresses in assessment['recommendations_quality'].items():
            if aspect != 'count':
                status = "✅" if addresses else "❌"
                print(f"   {aspect.replace('_', ' ').title()}: {status}")
                
        print(f"\n🔍 Missing Scenarios Coverage:")
        print(f"   Count: {assessment['missing_scenarios_coverage']['count']}")
        for area, covers in assessment['missing_scenarios_coverage'].items():
            if area != 'count':
                status = "✅" if covers else "❌"
                print(f"   {area.replace('_', ' ').title()}: {status}")

def test_qa_agent_comprehensive_quality():
    """Comprehensive quality test for QA Tester Agent."""
    
    print("🔬 QA Tester Agent - Comprehensive Quality Assessment")
    print("=" * 70)
    
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
    
    print(f"📋 Testing Feature: {sample_feature['title']}")
    print(f"📝 Description: {sample_feature['description'][:100]}...")
    
    # Test 1: Generate and assess test cases
    print(f"\n🧪 Phase 1: Generating Test Cases...")
    test_cases = qa_agent.generate_test_cases(sample_feature)
    test_case_assessment = assess_test_case_quality(test_cases)
    print_quality_report("Test Cases", test_case_assessment)
    
    # Test 2: Generate and assess edge cases
    print(f"\n⚠️ Phase 2: Generating Edge Cases...")
    edge_cases = qa_agent.generate_edge_cases(sample_feature)
    edge_case_assessment = assess_edge_cases_quality(edge_cases)
    print_quality_report("Edge Cases", edge_case_assessment)
    
    # Test 3: Validate and assess acceptance criteria
    print(f"\n✅ Phase 3: Validating Acceptance Criteria...")
    validation = qa_agent.validate_acceptance_criteria(sample_feature)
    validation_assessment = assess_acceptance_criteria_validation(validation)
    print_quality_report("Acceptance Criteria Validation", validation_assessment)
    
    # Overall Quality Score
    print(f"\n🏆 Overall Quality Assessment")
    print("=" * 60)
    
    # Calculate overall scores
    test_case_score = min(10, (test_case_assessment['gherkin_quality']['well_formed'] / max(1, test_case_assessment['total_test_cases'])) * 10)
    edge_case_score = min(10, (sum(edge_case_assessment['security_coverage'].values()) + sum(edge_case_assessment['boundary_coverage'].values())) * 1.25)
    validation_score = validation_assessment['score_analysis']['enhanced_score']
    
    overall_score = (test_case_score + edge_case_score + validation_score) / 3
    
    print(f"📊 Test Case Quality Score: {test_case_score:.1f}/10")
    print(f"⚠️ Edge Case Quality Score: {edge_case_score:.1f}/10")
    print(f"✅ Validation Quality Score: {validation_score}/10")
    print(f"🎯 Overall QA Agent Quality Score: {overall_score:.1f}/10")
    
    # Quality assessment
    if overall_score >= 8.5:
        quality_rating = "🌟 Excellent"
    elif overall_score >= 7.0:
        quality_rating = "✅ Good"
    elif overall_score >= 5.5:
        quality_rating = "⚠️ Acceptable"
    else:
        quality_rating = "❌ Needs Improvement"
        
    print(f"🏅 Quality Rating: {quality_rating}")
    
    # Key strengths and areas for improvement
    print(f"\n💪 Key Strengths:")
    if test_case_assessment['gherkin_quality']['well_formed'] / max(1, test_case_assessment['total_test_cases']) > 0.8:
        print("   ✅ Well-structured Gherkin scenarios")
    if edge_case_assessment['risk_levels']['Critical'] > 0:
        print("   ✅ Identifies critical security risks")
    if validation_assessment['score_analysis']['improvement'] > 0:
        print("   ✅ Provides actionable acceptance criteria improvements")
    if sum(edge_case_assessment['categories'].values()) >= 6:
        print("   ✅ Comprehensive edge case coverage")
        
    print(f"\n🔧 Areas for Improvement:")
    if test_case_assessment['coverage_areas']['performance'] == 0:
        print("   ⚠️ Limited performance testing scenarios")
    if not edge_case_assessment['security_coverage']['unauthorized_access']:
        print("   ⚠️ Could expand unauthorized access testing")
    if validation_assessment['recommendations_quality']['count'] < 3:
        print("   ⚠️ Could provide more detailed recommendations")
        
    return {
        "overall_score": overall_score,
        "test_case_assessment": test_case_assessment,
        "edge_case_assessment": edge_case_assessment,
        "validation_assessment": validation_assessment
    }

if __name__ == "__main__":
    results = test_qa_agent_comprehensive_quality()
