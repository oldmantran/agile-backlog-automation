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

    def generate_user_story_test_cases(self, user_story: dict, context: dict = None) -> list[dict]:
        """Generate test cases specifically for a user story following ADO best practices."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'test_environment': context.get('test_environment', 'automated testing') if context else 'automated testing',
            'compliance_requirements': context.get('compliance_requirements', 'standard') if context else 'standard'
        }
        
        user_input = f"""
Generate comprehensive test cases for this User Story that will be organized in Azure DevOps Test Suites:

User Story: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', 'No description provided')}
Acceptance Criteria: {user_story.get('acceptance_criteria', [])}
Priority: {user_story.get('priority', 'Medium')}
Story Points: {user_story.get('story_points', 'Not estimated')}

Focus on:
1. Testing the specific user story functionality (not broader feature functionality)
2. Validating each acceptance criterion with dedicated test cases
3. Creating test cases that can be executed independently
4. Including both positive and negative scenarios for the story
5. Considering the story priority and complexity for test coverage depth

Generate test cases that will be:
- Linked to this specific User Story in Azure DevOps
- Organized in a dedicated Test Suite for this User Story
- Part of a broader Test Plan for the parent Feature
- Executable by QA engineers during story validation
"""
        print(f"🧪 [QATesterAgent] Generating User Story test cases for: {user_story.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

        try:
            test_cases = json.loads(response)
            if isinstance(test_cases, list):
                # Enhance test cases with User Story specific metadata
                for test_case in test_cases:
                    test_case['user_story_id'] = user_story.get('id')
                    test_case['user_story_title'] = user_story.get('title', 'Unknown')
                    test_case['story_points'] = user_story.get('story_points')
                return test_cases
            elif isinstance(test_cases, dict) and 'test_cases' in test_cases:
                # Enhance test cases with User Story specific metadata
                for test_case in test_cases['test_cases']:
                    test_case['user_story_id'] = user_story.get('id')
                    test_case['user_story_title'] = user_story.get('title', 'Unknown')
                    test_case['story_points'] = user_story.get('story_points')
                return test_cases['test_cases']
            else:
                print("⚠️ Grok response was not in expected format.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []

    def validate_user_story_testability(self, user_story: dict, context: dict = None) -> dict:
        """Analyze a user story for testability and suggest improvements."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'quality_standards': context.get('quality_standards', 'industry standard') if context else 'industry standard'
        }
        
        user_input = f"""
Analyze this User Story for testability and provide improvement recommendations:

User Story: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', 'No description provided')}
Acceptance Criteria: {user_story.get('acceptance_criteria', [])}
Priority: {user_story.get('priority', 'Medium')}
Story Points: {user_story.get('story_points', 'Not estimated')}

Evaluate:
1. Clarity of the user story requirements
2. Completeness and testability of acceptance criteria
3. Missing scenarios or edge cases
4. Dependencies that might affect testing
5. Potential test automation opportunities
6. Risk areas requiring additional test coverage

Provide:
1. Testability score (1-10)
2. Specific improvement recommendations
3. Missing test scenarios
4. Suggested acceptance criteria enhancements
5. Risk assessment for the story
"""
        print(f"✅ [QATesterAgent] Analyzing testability for: {user_story.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

        try:
            analysis = json.loads(response)
            # Add metadata
            analysis['user_story_id'] = user_story.get('id')
            analysis['user_story_title'] = user_story.get('title', 'Unknown')
            return analysis
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return {
                "testability_score": 5,
                "improvement_recommendations": ["Manual review required due to parsing error"],
                "missing_scenarios": [],
                "enhanced_criteria": user_story.get('acceptance_criteria', []),
                "risk_assessment": "Medium - requires manual review",
                "user_story_id": user_story.get('id'),
                "user_story_title": user_story.get('title', 'Unknown')
            }

    def create_test_plan_structure(self, feature: dict, context: dict = None) -> dict:
        """Create a recommended test plan structure for a feature with its user stories."""
        
        test_plan_structure = {
            "feature_title": feature.get('title', 'Unknown Feature'),
            "feature_description": feature.get('description', ''),
            "test_plan_name": f"Test Plan - {feature.get('title', 'Unknown Feature')}",
            "test_suites": [],
            "feature_level_tests": [],
            "recommendations": []
        }
        
        # Process user stories to create test suite structure
        user_stories = feature.get('user_stories', [])
        
        for user_story in user_stories:
            suite_structure = {
                "suite_name": f"User Story: {user_story.get('title', 'Unknown')}",
                "user_story_id": user_story.get('id'),
                "user_story_title": user_story.get('title', 'Unknown'),
                "priority": user_story.get('priority', 'Medium'),
                "story_points": user_story.get('story_points'),
                "test_cases_count": len(user_story.get('test_cases', [])),
                "acceptance_criteria_count": len(user_story.get('acceptance_criteria', [])),
                "recommended_test_types": []
            }
            
            # Analyze story complexity to recommend test types
            story_points = user_story.get('story_points', 0)
            if isinstance(story_points, str):
                try:
                    story_points = int(story_points)
                except:
                    story_points = 3  # Default medium complexity
            
            if story_points >= 8:
                suite_structure["recommended_test_types"].extend([
                    "Functional Testing", "Integration Testing", "Performance Testing", "Security Testing"
                ])
            elif story_points >= 5:
                suite_structure["recommended_test_types"].extend([
                    "Functional Testing", "Integration Testing", "Edge Case Testing"
                ])
            else:
                suite_structure["recommended_test_types"].extend([
                    "Functional Testing", "Basic Validation"
                ])
            
            test_plan_structure["test_suites"].append(suite_structure)
        
        # Add feature-level test recommendations
        if feature.get('test_cases'):
            test_plan_structure["feature_level_tests"] = [
                {
                    "suite_name": f"Feature Tests: {feature.get('title', 'Unknown')}",
                    "description": "Cross-story integration and feature-level validation tests",
                    "test_cases_count": len(feature.get('test_cases', [])),
                    "recommended_test_types": ["Integration Testing", "End-to-End Testing", "Feature Validation"]
                }
            ]
        
        # Add general recommendations
        total_stories = len(user_stories)
        total_test_cases = sum(len(story.get('test_cases', [])) for story in user_stories)
        
        test_plan_structure["recommendations"] = [
            f"Organize {total_test_cases} test cases across {total_stories} user story test suites",
            "Execute test cases at the user story level for faster feedback",
            "Use test suite organization to track story completion status",
            "Prioritize testing based on user story priority and business value",
            "Consider automated testing for high-complexity user stories"
        ]
        
        if total_stories > 10:
            test_plan_structure["recommendations"].append(
                "Consider grouping related user stories into test suite categories"
            )
        
        print(f"📋 [QATesterAgent] Created test plan structure for feature: {feature.get('title', 'Unknown')}")
        return test_plan_structure
