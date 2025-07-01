import json
from agents.base_agent import Agent
from config.config_loader import Config

class QATesterAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("qa_tester_agent", config)

    def generate_test_cases(self, feature: dict, context: dict = None) -> list[dict]:
        """Generate test cases and potential bugs from a feature description."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'test_environment': context.get('test_environment', 'automated testing') if context else 'automated testing',
            'compliance_requirements': context.get('compliance_requirements', 'standard') if context else 'standard'
        }
        
        user_input = f"""
Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}
Priority: {feature.get('priority', 'Medium')}
"""
        print(f"🧪 [QATesterAgent] Generating test cases for: {feature.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

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

    def generate_edge_cases(self, feature: dict, context: dict = None) -> list[dict]:
        """Generate edge cases and potential failure scenarios."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'security_requirements': context.get('security_requirements', 'standard') if context else 'standard'
        }
        
        user_input = f"""
Analyze this feature for edge cases and potential failure scenarios:

Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}

Focus on:
1. Boundary conditions
2. Error handling scenarios
3. Performance edge cases
4. Security vulnerabilities
5. Integration failure points
"""
        print(f"⚠️ [QATesterAgent] Generating edge cases for: {feature.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

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

    def validate_acceptance_criteria(self, feature: dict, context: dict = None) -> dict:
        """Validate and enhance acceptance criteria for testability."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'quality_standards': context.get('quality_standards', 'industry standard') if context else 'industry standard'
        }
        
        user_input = f"""
Review and enhance these acceptance criteria for testability:

Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Current Acceptance Criteria: {feature.get('acceptance_criteria', [])}

Provide:
1. Enhanced acceptance criteria (if needed)
2. Testability score (1-10)
3. Recommendations for improvement
4. Missing test scenarios
"""
        print(f"✅ [QATesterAgent] Validating acceptance criteria for: {feature.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

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
