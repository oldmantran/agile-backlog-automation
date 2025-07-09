import json
import logging
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator

class QATesterAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("qa_tester_agent", config)
        # Initialize quality validator
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize ADO client if available
        self.ado_client = None
        if hasattr(config, 'ado_client'):
            self.ado_client = config.ado_client

    def generate_test_cases(self, feature: dict, context: dict = None) -> list[dict]:
        """Generate test cases and potential bugs from a feature description."""
        
        # Validate input
        if not feature:
            self.logger.error("No feature provided for test case generation")
            return []
            
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
        
        try:
            response = self.run(user_input, prompt_context)
            
            if not response:
                self.logger.warning("Empty response from AI model")
                return []
                
            test_cases = json.loads(response)
            
            if isinstance(test_cases, list):
                # Validate and enhance test cases for quality compliance
                enhanced_test_cases = self._validate_and_enhance_test_cases(test_cases)
                return enhanced_test_cases
            elif isinstance(test_cases, dict) and 'test_cases' in test_cases:
                enhanced_test_cases = self._validate_and_enhance_test_cases(test_cases['test_cases'])
                return enhanced_test_cases
            else:
                self.logger.warning("Response was not in expected format")
                return []
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            if 'response' in locals():
                self.logger.debug(f"Raw response: {response}")
            return []
        except Exception as e:
            self.logger.error(f"Error generating test cases: {e}")
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

    def _validate_and_enhance_test_cases(self, test_cases: list) -> list:
        """
        Validate and enhance test cases to meet quality standards.
        Ensures compliance with Backlog Sweeper monitoring rules.
        """
        if not test_cases:
            return []
            
        enhanced_test_cases = []
        
        for test_case in test_cases:
            if not isinstance(test_case, dict):
                self.logger.warning(f"Skipping invalid test case: {test_case}")
                continue
                
            enhanced_test_case = self._enhance_single_test_case(test_case)
            enhanced_test_cases.append(enhanced_test_case)
        
        return enhanced_test_cases
    
    def _enhance_single_test_case(self, test_case: dict) -> dict:
        """
        Enhance a single test case to meet quality standards.
        """
        enhanced_test_case = test_case.copy()
        
        # Validate and fix title
        title = test_case.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "Test Case")
        if not title_valid:
            print(f"⚠️ Test case title issues: {', '.join(title_issues)}")
            if not title:
                enhanced_test_case['title'] = f"Test Case: {test_case.get('description', 'Validation test')[:50]}..."
        
        # Ensure test steps exist
        if not enhanced_test_case.get('steps') and not enhanced_test_case.get('test_steps'):
            # Create basic test steps if missing
            enhanced_test_case['test_steps'] = [
                "Navigate to the application",
                "Perform the required action",
                "Verify the expected outcome"
            ]
        
        # Ensure expected result exists
        if not enhanced_test_case.get('expected_result') and not enhanced_test_case.get('expected_outcome'):
            enhanced_test_case['expected_result'] = "System behaves as specified in acceptance criteria"
        
        # Add test case metadata
        if not enhanced_test_case.get('test_type'):
            description = enhanced_test_case.get('description', '').lower()
            title_lower = title.lower()
            
            if any(word in description or word in title_lower for word in ['functional', 'feature', 'user']):
                enhanced_test_case['test_type'] = 'functional'
            elif any(word in description or word in title_lower for word in ['performance', 'load', 'stress']):
                enhanced_test_case['test_type'] = 'performance'
            elif any(word in description or word in title_lower for word in ['security', 'auth', 'permission']):
                enhanced_test_case['test_type'] = 'security'
            elif any(word in description or word in title_lower for word in ['ui', 'interface', 'usability']):
                enhanced_test_case['test_type'] = 'ui'
            else:
                enhanced_test_case['test_type'] = 'functional'
        
        # Add priority if missing
        if not enhanced_test_case.get('priority'):
            enhanced_test_case['priority'] = 'Medium'
        
        # Add automation recommendation
        if not enhanced_test_case.get('automation_candidate'):
            title_lower = title.lower()
            if any(word in title_lower for word in ['regression', 'smoke', 'api', 'data']):
                enhanced_test_case['automation_candidate'] = True
            else:
                enhanced_test_case['automation_candidate'] = False
        
        return enhanced_test_case
    
    def enhance_acceptance_criteria(self, user_story: dict, context: dict = None) -> list:
        """
        Enhance acceptance criteria for a user story to meet quality standards.
        Used by Backlog Sweeper Agent when criteria need improvement.
        """
        current_criteria = user_story.get('acceptance_criteria', [])
        story_title = user_story.get('title', '')
        story_description = user_story.get('description', '')
        
        # Use quality validator to enhance criteria
        enhanced_criteria = self.quality_validator.enhance_acceptance_criteria(
            current_criteria,
            {'title': story_title, 'description': story_description}
        )
        
        print(f"📋 [QATesterAgent] Enhanced acceptance criteria for: {story_title}")
        print(f"   Original criteria count: {len(current_criteria)}")
        print(f"   Enhanced criteria count: {len(enhanced_criteria)}")
        
        return enhanced_criteria
    
    def validate_acceptance_criteria_quality(self, acceptance_criteria: list, story_context: dict = None) -> dict:
        """
        Validate acceptance criteria quality and provide improvement suggestions.
        Used by Backlog Sweeper Agent for quality assessment.
        """
        story_title = story_context.get('title', '') if story_context else ''
        
        # Use quality validator
        is_valid, issues = self.quality_validator.validate_acceptance_criteria(acceptance_criteria, story_title)
        
        # Additional QA-specific checks
        qa_recommendations = []
        
        # Check for testability
        untestable_criteria = []
        for i, criteria in enumerate(acceptance_criteria):
            if any(word in criteria.lower() for word in ['should work', 'properly', 'correctly', 'appropriately']):
                untestable_criteria.append(f"Criteria {i+1}: '{criteria[:50]}...' - Too vague for testing")
        
        if untestable_criteria:
            qa_recommendations.extend(untestable_criteria)
        
        # Check for missing test scenarios
        has_positive_test = any('successfully' in criteria.lower() or 'can' in criteria.lower() for criteria in acceptance_criteria)
        has_negative_test = any('cannot' in criteria.lower() or 'error' in criteria.lower() or 'invalid' in criteria.lower() for criteria in acceptance_criteria)
        
        if has_positive_test and not has_negative_test:
            qa_recommendations.append("Consider adding negative test scenarios (error cases, invalid inputs)")
        
        # Check for boundary conditions
        has_boundary_test = any(word in ' '.join(acceptance_criteria).lower() for word in ['maximum', 'minimum', 'limit', 'boundary', 'edge'])
        if not has_boundary_test:
            qa_recommendations.append("Consider adding boundary condition tests (min/max values, limits)")
        
        return {
            'is_valid': is_valid and len(qa_recommendations) == 0,
            'issues': issues,
            'qa_recommendations': qa_recommendations,
            'enhanced_criteria': self.quality_validator.enhance_acceptance_criteria(acceptance_criteria, story_context) if not is_valid else acceptance_criteria
        }

    def ensure_test_organization(self, user_story: dict, required: bool = True) -> dict:
        """Ensure proper test organization exists for a user story."""
        
        if not self.ado_client:
            self.logger.warning("ADO client not available - cannot create test organization")
            return None if required else {'test_plan': None, 'test_suite': None, 'feature_id': None}
            
        # Validate input
        if not user_story or not user_story.get('id'):
            self.logger.error("Invalid user story provided - missing ID")
            return None if required else {'test_plan': None, 'test_suite': None, 'feature_id': None}
            
        try:
            # Get the feature this user story belongs to
            relations = self.ado_client.get_work_item_relations(user_story['id'])
            feature_rel = next((r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Reverse'), None)
            
            if not feature_rel:
                self.logger.warning(f"No parent feature found for user story {user_story['id']}")
                return None if required else {'test_plan': None, 'test_suite': None, 'feature_id': None}
                
            feature_id = int(feature_rel['url'].split('/')[-1])
            feature_details = self.ado_client.get_work_item_details([feature_id])
            
            if not feature_details:
                self.logger.error(f"Could not retrieve feature details for ID {feature_id}")
                return None if required else {'test_plan': None, 'test_suite': None, 'feature_id': feature_id}
                
            feature = feature_details[0]
            
            # Try to ensure test plan exists for the feature
            test_plan = self.ado_client.ensure_test_plan_exists(
                feature_id=feature_id,
                feature_name=feature.get('fields', {}).get('System.Title', 'Unknown Feature')
            )
            
            if not test_plan:
                self.logger.warning(f"Failed to create/find test plan for feature {feature_id}")
                if required:
                    return None
                test_plan = None
            
            # Try to ensure test suite exists for the user story
            test_suite = None
            if test_plan:  # Only try to create test suite if we have a test plan
                test_suite = self.ado_client.ensure_test_suite_exists(
                    test_plan_id=test_plan['id'],
                    user_story_id=user_story['id'],
                    user_story_name=user_story.get('fields', {}).get('System.Title', user_story.get('title', 'Unknown User Story'))
                )
                
                if not test_suite:
                    self.logger.warning(f"Failed to create/find test suite for user story {user_story['id']}")
                    if required:
                        return None
            
            return {
                'test_plan': test_plan,
                'test_suite': test_suite,
                'feature_id': feature_id
            }
            
        except Exception as e:
            self.logger.error(f"Error ensuring test organization: {e}")
            return None if required else {'test_plan': None, 'test_suite': None, 'feature_id': None}

    def create_test_cases(self, user_story: dict, test_cases: list, require_organization: bool = False) -> list:
        """Create test cases and organize them in proper test suite if possible."""
        
        if not self.ado_client:
            self.logger.warning("ADO client not available - cannot create test cases in ADO")
            return []
            
        created_test_cases = []
        
        try:
            # Try to ensure we have proper test organization (but don't fail if we can't)
            test_org = self.ensure_test_organization(user_story, required=require_organization)
            
            if not test_org and require_organization:
                self.logger.error(f"Failed to create test organization for user story {user_story.get('id', 'Unknown')}")
                return []
            
            test_plan = test_org.get('test_plan') if test_org else None
            test_suite = test_org.get('test_suite') if test_org else None
            
            # Create each test case
            for test_case in test_cases:
                try:
                    # Validate test case has required fields
                    if not test_case.get('title'):
                        self.logger.warning(f"Skipping test case without title: {test_case}")
                        continue
                        
                    # Create the test case work item
                    test_case_wi = self.ado_client.create_test_case(
                        title=test_case['title'],
                        description=json.dumps(test_case, indent=2),
                        steps=self._format_test_steps(test_case)
                    )
                    
                    if test_case_wi:
                        # Add test case to test suite if we have proper organization
                        if test_plan and test_suite:
                            try:
                                self.ado_client.add_test_case_to_suite(
                                    test_plan_id=test_plan['id'],
                                    test_suite_id=test_suite['id'],
                                    test_case_id=test_case_wi['id']
                                )
                                self.logger.info(f"Added test case to test suite: {test_case['title']}")
                            except Exception as e:
                                self.logger.warning(f"Failed to add test case to test suite: {e}")
                        else:
                            self.logger.info(f"Created test case without test suite organization: {test_case['title']}")
                        
                        # Link test case to user story if possible
                        try:
                            self.ado_client.create_work_item_relation(
                                test_case_wi['id'],
                                user_story.get('id'),
                                "Microsoft.VSTS.Common.TestedBy-Reverse"
                            )
                        except Exception as e:
                            self.logger.warning(f"Failed to link test case to user story: {e}")
                        
                        created_test_cases.append(test_case_wi)
                        self.logger.info(f"Created test case: {test_case['title']}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to create test case '{test_case.get('title', 'Unknown')}': {e}")
                    continue
                    
            self.logger.info(f"Successfully created {len(created_test_cases)} test cases for user story {user_story.get('id', 'Unknown')}")
            if not test_plan or not test_suite:
                self.logger.warning("Test cases created but may not be properly organized in test suites")
            
            return created_test_cases
            
        except Exception as e:
            self.logger.error(f"Error creating test cases: {e}")
            return []
        
    def create_test_cases_with_fallback(self, user_story: dict, test_cases: list) -> dict:
        """
        Create test cases with fallback options if test organization fails.
        Returns detailed results about what was created and what failed.
        """
        result = {
            'test_cases_created': [],
            'test_organization_created': False,
            'test_plan': None,
            'test_suite': None,
            'warnings': [],
            'errors': []
        }
        
        try:
            # First, try to create test cases with full organization
            created_test_cases = self.create_test_cases(user_story, test_cases, require_organization=False)
            result['test_cases_created'] = created_test_cases
            
            # Check if we got proper organization
            test_org = self.ensure_test_organization(user_story, required=False)
            if test_org:
                result['test_plan'] = test_org.get('test_plan')
                result['test_suite'] = test_org.get('test_suite')
                result['test_organization_created'] = bool(test_org.get('test_plan') and test_org.get('test_suite'))
                
                if not result['test_organization_created']:
                    result['warnings'].append("Test cases created but test organization is incomplete")
            else:
                result['warnings'].append("Test cases created without test organization")
                
            return result
            
        except Exception as e:
            result['errors'].append(f"Failed to create test cases: {e}")
            return result

    def _format_test_steps(self, test_case: dict) -> list:
        """Format test case into steps for Azure DevOps."""
        steps = []
        
        try:
            # Check for Gherkin format first
            if 'gherkin' in test_case and isinstance(test_case['gherkin'], dict):
                gherkin = test_case['gherkin']
                
                # Add Given conditions
                for given in gherkin.get('given', []):
                    steps.append({
                        'action': f"GIVEN {given}",
                        'expectedResult': "Precondition is satisfied"
                    })
                    
                # Add When actions
                for when in gherkin.get('when', []):
                    steps.append({
                        'action': f"WHEN {when}",
                        'expectedResult': "Action is performed successfully"
                    })
                    
                # Add Then verifications
                for then in gherkin.get('then', []):
                    steps.append({
                        'action': f"THEN {then}",
                        'expectedResult': then
                    })
                    
            # Check for explicit test steps
            elif 'test_steps' in test_case and test_case['test_steps']:
                for i, step in enumerate(test_case['test_steps']):
                    if isinstance(step, dict):
                        steps.append({
                            'action': step.get('action', f"Step {i+1}"),
                            'expectedResult': step.get('expectedResult', step.get('expected_result', 'Step completes successfully'))
                        })
                    else:
                        steps.append({
                            'action': str(step),
                            'expectedResult': test_case.get('expected_result', 'Step completes successfully')
                        })
                        
            # Check for steps field
            elif 'steps' in test_case and test_case['steps']:
                for i, step in enumerate(test_case['steps']):
                    if isinstance(step, dict):
                        steps.append({
                            'action': step.get('action', f"Step {i+1}"),
                            'expectedResult': step.get('expectedResult', step.get('expected_result', 'Step completes successfully'))
                        })
                    else:
                        steps.append({
                            'action': str(step),
                            'expectedResult': test_case.get('expected_result', 'Step completes successfully')
                        })
            else:
                # Fallback to basic steps if no explicit steps
                steps.append({
                    'action': test_case.get('description', 'Execute test case'),
                    'expectedResult': test_case.get('expected_result', test_case.get('expected_outcome', 'Test passes successfully'))
                })
                
            # Ensure we have at least one step
            if not steps:
                steps = [{
                    'action': 'Execute test case',
                    'expectedResult': 'Test passes successfully'
                }]
                
        except Exception as e:
            self.logger.error(f"Error formatting test steps: {e}")
            # Provide minimal fallback
            steps = [{
                'action': 'Execute test case',
                'expectedResult': 'Test passes successfully'
            }]
                
        return steps
