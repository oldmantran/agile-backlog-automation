import json
from agents.base_agent import Agent
from config.config_loader import Config

class QATesterAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("qa_tester_agent", config)

    def generate_test_cases(self, feature: dict) -> list[dict]:
        """Generate test cases and potential bugs from a feature description."""
        user_input = f"""
Feature: {feature['title']}
Description: {feature['description']}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}
Priority: {feature.get('priority', 'Medium')}
"""
        print(f"🧪 [QATesterAgent] Generating test cases for: {feature['title']}")
        response = self.run(user_input)

        try:
            test_cases = json.loads(response)
            if isinstance(test_cases, list):
                return test_cases
            elif isinstance(test_cases, dict) and 'test_cases' in test_cases:
                return test_cases['test_cases']
            else:
                print("⚠️ Grok response was not in expected format.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []

    def generate_edge_cases(self, feature: dict) -> list[dict]:
        """Generate edge cases and potential failure scenarios."""
        user_input = f"""
Analyze this feature for edge cases and potential failure scenarios:

Feature: {feature['title']}
Description: {feature['description']}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}

Focus on:
1. Boundary conditions
2. Error handling scenarios
3. Performance edge cases
4. Security vulnerabilities
5. Integration failure points
"""
        print(f"⚠️ [QATesterAgent] Generating edge cases for: {feature['title']}")
        response = self.run(user_input)

        try:
            edge_cases = json.loads(response)
            if isinstance(edge_cases, list):
                return edge_cases
            elif isinstance(edge_cases, dict) and 'edge_cases' in edge_cases:
                return edge_cases['edge_cases']
            else:
                print("⚠️ Grok response was not in expected format.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []

    def validate_acceptance_criteria(self, feature: dict) -> dict:
        """Validate and enhance acceptance criteria for testability."""
        user_input = f"""
Review and enhance these acceptance criteria for testability:

Feature: {feature['title']}
Description: {feature['description']}
Current Acceptance Criteria: {feature.get('acceptance_criteria', [])}

Provide:
1. Enhanced acceptance criteria (if needed)
2. Testability score (1-10)
3. Recommendations for improvement
4. Missing test scenarios
"""
        print(f"✅ [QATesterAgent] Validating acceptance criteria for: {feature['title']}")
        response = self.run(user_input)

        try:
            validation = json.loads(response)
            return validation
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return {
                "enhanced_criteria": feature.get('acceptance_criteria', []),
                "testability_score": 5,
                "recommendations": ["Manual review required due to parsing error"],
                "missing_scenarios": []
            }
