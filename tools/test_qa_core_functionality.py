#!/usr/bin/env python3
"""
Test QA Tester Agent's core functionality without requiring Azure DevOps
Focus on JSON parsing, test case generation, and structure creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config.config_loader import Config
from agents.qa_tester_agent import QATesterAgent

def test_qa_core_functionality():
    """Test QA Tester Agent's core functionality without Azure DevOps dependency."""
    print("🧪 Testing QA Tester Agent - Core Functionality")
    print("=" * 60)
    
    try:
        # Initialize config and agent (handle path correctly)
        try:
            config = Config()
        except FileNotFoundError:
            # Running from tools directory, adjust path
            config = Config(settings_path="../config/settings.yaml")
        print("✅ Config loaded")
        
        qa_agent = QATesterAgent(config)
        print("✅ QA Tester Agent initialized")
        
        # Test data - realistic user story for oil & gas domain
        test_user_story = {
            'id': 12345,
            'title': 'Well Data Validation Dashboard',
            'description': 'As a field engineer, I want to view real-time well data validation status so that I can quickly identify and address data quality issues.',
            'acceptance_criteria': [
                'Given well data is received, when validation rules are applied, then validation status is displayed',
                'Given invalid data is detected, when engineer views dashboard, then specific errors are highlighted',
                'Given validation is complete, when engineer requests report, then summary report is generated'
            ],
            'story_points': 5,
            'priority': 'High'
        }
        
        test_context = {
            'project_name': 'Oil & Gas Data Management',
            'domain': 'oil_gas',
            'platform': 'web dashboard'
        }
        
        print(f"\n🎯 Testing User Story: {test_user_story['title']}")
        print(f"   Story Points: {test_user_story['story_points']}")
        print(f"   Priority: {test_user_story['priority']}")
        print(f"   Acceptance Criteria: {len(test_user_story['acceptance_criteria'])}")
        
        # Test 1: Generate test cases
        print("\n🔍 Test 1: Generate Test Cases")
        test_cases = qa_agent.generate_user_story_test_cases(test_user_story, test_context)
        
        if test_cases:
            print(f"✅ Generated {len(test_cases)} test cases")
            
            # Analyze test case quality
            coverage_types = set()
            automation_candidates = 0
            high_priority_tests = 0
            
            for test_case in test_cases:
                coverage_types.add(test_case.get('coverage_type', 'unknown'))
                if test_case.get('automation_candidate', False):
                    automation_candidates += 1
                if test_case.get('priority', '').lower() == 'high':
                    high_priority_tests += 1
            
            print(f"   📊 Coverage types: {', '.join(coverage_types)}")
            print(f"   🤖 Automation candidates: {automation_candidates}")
            print(f"   🔥 High priority tests: {high_priority_tests}")
            
            # Show sample test case
            if test_cases:
                sample = test_cases[0]
                print(f"\n📋 Sample Test Case:")
                print(f"   Title: {sample.get('title', 'N/A')}")
                print(f"   Coverage: {sample.get('coverage_type', 'N/A')}")
                print(f"   Steps: {len(sample.get('test_steps', []))}")
                print(f"   Priority: {sample.get('priority', 'N/A')}")
        else:
            print("❌ No test cases generated")
            return False
            
        # Test 2: Validate testability
        print("\n🔍 Test 2: Validate User Story Testability")
        testability = qa_agent.validate_user_story_testability(test_user_story, test_context)
        
        if testability:
            print(f"✅ Testability analysis completed")
            print(f"   Score: {testability.get('testability_score', 'N/A')}/10")
            print(f"   Recommendations: {len(testability.get('improvement_recommendations', []))}")
            print(f"   Missing scenarios: {len(testability.get('missing_scenarios', []))}")
        else:
            print("❌ Testability validation failed")
            return False
        
        # Test 3: Create test plan structure
        print("\n🔍 Test 3: Create Test Plan Structure")
        test_feature = {
            'id': 11111,
            'title': 'Well Data Management Feature',
            'description': 'Comprehensive well data management capabilities',
            'user_stories': [test_user_story]
        }
        
        test_plan_structure = qa_agent.create_test_plan_structure(test_feature, test_context)
        
        if test_plan_structure:
            print(f"✅ Test plan structure created")
            print(f"   Plan name: {test_plan_structure.get('test_plan_name', 'N/A')}")
            print(f"   Test suites: {len(test_plan_structure.get('test_suites', []))}")
            print(f"   Recommendations: {len(test_plan_structure.get('recommendations', []))}")
            
            # Show test suite details
            for suite in test_plan_structure.get('test_suites', []):
                print(f"   📋 Suite: {suite.get('suite_name', 'N/A')}")
                print(f"      User Story: {suite.get('user_story_id', 'N/A')}")
                print(f"      Test Cases: {len(suite.get('test_cases', []))}")
        else:
            print("❌ Test plan structure creation failed")
            return False
            
        # Test 4: JSON parsing robustness
        print("\n🔍 Test 4: JSON Parsing Robustness")
        
        # Test markdown response (simulating AI response)
        markdown_response = """
        ### **Test Case 1: Validate Dashboard Display**
        - **Title:** Dashboard loads with well data
        - **Description:** Verify dashboard displays current well data
        - **Test Steps:**
          1. Navigate to dashboard
          2. Verify data display
        - **Expected Result:** Data is visible
        
        ### **Test Case 2: Error Handling**
        - **Title:** Invalid data handling
        - **Description:** System handles invalid well data
        - **Test Steps:**
          1. Submit invalid data
          2. Check error handling
        - **Expected Result:** Error message displayed
        """
        
        json_result = qa_agent._extract_json_from_response(markdown_response)
        
        try:
            parsed_cases = json.loads(json_result)
            print(f"✅ JSON parsing successful: {len(parsed_cases)} test cases extracted")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            return False
        
        print("\n🎉 All core functionality tests passed!")
        print("\n📊 Summary:")
        print(f"   ✅ Test case generation: {len(test_cases)} cases")
        print(f"   ✅ Testability analysis: {testability.get('testability_score', 0)}/10 score")
        print(f"   ✅ Test plan structure: {len(test_plan_structure.get('test_suites', []))} suites")
        print(f"   ✅ JSON parsing: Robust markdown handling")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qa_core_functionality()
    exit(0 if success else 1)
