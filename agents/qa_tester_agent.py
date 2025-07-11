import json
import logging
import re
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

    # FEATURE-LEVEL METHODS REMOVED - QA Tester Agent now focuses exclusively on User Story testing
    # Use generate_user_story_test_cases() for all test case generation needs

    # FEATURE-LEVEL EDGE CASE GENERATION REMOVED - Use generate_user_story_test_cases() with comprehensive coverage

    # FEATURE-LEVEL ACCEPTANCE CRITERIA VALIDATION REMOVED - Use validate_user_story_testability() for comprehensive analysis

    def generate_user_story_test_cases(self, user_story: dict, context: dict = None) -> list[dict]:
        """
        Generate comprehensive test cases specifically for a user story following ADO best practices.
        Includes boundary conditions, failure scenarios, and acceptance criteria validation.
        """
        
        # Validate input
        if not user_story:
            self.logger.error("No user story provided for test case generation")
            return []
            
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'test_environment': context.get('test_environment', 'automated testing') if context else 'automated testing',
            'compliance_requirements': context.get('compliance_requirements', 'standard') if context else 'standard'
        }
        
        # First validate and enhance acceptance criteria if needed
        criteria_analysis = self._analyze_acceptance_criteria(user_story)
        enhanced_criteria = criteria_analysis.get('enhanced_criteria', user_story.get('acceptance_criteria', []))
        
        user_input = f"""
Generate comprehensive test cases for this User Story that will be organized in Azure DevOps Test Suites:

User Story: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', 'No description provided')}
Acceptance Criteria: {enhanced_criteria}
Priority: {user_story.get('priority', 'Medium')}
Story Points: {user_story.get('story_points', 'Not estimated')}

CRITICAL REQUIREMENTS - Generate test cases that include:

1. **Acceptance Criteria Coverage**: Create at least one test case per acceptance criterion
2. **Boundary/Edge Cases**: Test limits, maximum/minimum values, empty inputs, special characters
3. **Failure Scenarios**: Invalid inputs, error conditions, system failures, permission denials
4. **Integration Points**: API calls, database operations, external services
5. **Security Validation**: Input sanitization, authentication, authorization
6. **Performance Considerations**: Response times, resource usage for complex operations

QUALITY STANDARDS:
- Focus exclusively on this User Story's functionality (not broader feature functionality)
- Each test case must be executable independently
- Include both positive (happy path) and negative (error) scenarios
- Ensure test cases validate business rules and data integrity
- Consider the story priority ({user_story.get('priority', 'Medium')}) and complexity ({user_story.get('story_points', 'Unknown')} points) for coverage depth

TEST ORGANIZATION:
- Test cases will be linked to this specific User Story in Azure DevOps
- Organized in a dedicated Test Suite for this User Story
- Part of a broader Test Plan for the parent Feature
- Executable by QA engineers during story validation

COVERAGE DEPTH BASED ON STORY CHARACTERISTICS:
- Story Points: {user_story.get('story_points', 'Unknown')} - {'Comprehensive' if str(user_story.get('story_points', 0)).isdigit() and int(user_story.get('story_points', 0)) >= 8 else 'Standard' if str(user_story.get('story_points', 0)).isdigit() and int(user_story.get('story_points', 0)) >= 5 else 'Basic'} coverage needed
- Priority: {user_story.get('priority', 'Medium')} - {'High' if user_story.get('priority', '').lower() == 'high' else 'Medium' if user_story.get('priority', '').lower() == 'medium' else 'Standard'} test priority

ACCEPTANCE CRITERIA ANALYSIS:
{criteria_analysis.get('analysis_summary', 'Standard acceptance criteria validation required')}

Generate test cases covering:
- All acceptance criteria with dedicated test cases
- Boundary conditions and edge cases specific to this story
- Error handling and failure recovery scenarios
- Security and validation requirements
- Integration points and dependencies
- Performance considerations where applicable
"""
        
        print(f"🧪 [QATesterAgent] Generating comprehensive User Story test cases for: {user_story.get('title', 'Unknown')}")
        
        try:
            response = self.run(user_input, prompt_context)
            
            if not response:
                self.logger.warning("Empty response from AI model")
                return []
            
            # Extract JSON from markdown code blocks if present
            cleaned_response = self._extract_json_from_response(response)
            test_cases = json.loads(cleaned_response)
            
            if isinstance(test_cases, list):
                enhanced_test_cases = test_cases
            elif isinstance(test_cases, dict) and 'test_cases' in test_cases:
                enhanced_test_cases = test_cases['test_cases']
            else:
                self.logger.warning("Response was not in expected format")
                return []
                
            # Enhance test cases with User Story specific metadata and quality validation
            for test_case in enhanced_test_cases:
                test_case['user_story_id'] = user_story.get('id')
                test_case['user_story_title'] = user_story.get('title', 'Unknown')
                test_case['story_points'] = user_story.get('story_points')
                test_case['story_priority'] = user_story.get('priority', 'Medium')
                
                # Add coverage analysis metadata
                test_case['acceptance_criteria_validation'] = criteria_analysis.get('testability_score', 7)
                test_case['coverage_type'] = self._determine_coverage_type(test_case, user_story)
                
            # Apply formatting improvements for readability
            enhanced_test_cases = [self._format_test_case_content(tc) for tc in enhanced_test_cases]
            
            # Validate and enhance all test cases for quality compliance
            enhanced_test_cases = self._validate_and_enhance_test_cases(enhanced_test_cases)
            
            # Ensure we have comprehensive coverage
            coverage_validation = self._validate_test_coverage(enhanced_test_cases, user_story, enhanced_criteria)
            if coverage_validation.get('missing_coverage'):
                self.logger.warning(f"Missing test coverage detected: {coverage_validation['missing_coverage']}")
                
            print(f"✅ [QATesterAgent] Generated {len(enhanced_test_cases)} comprehensive test cases")
            return enhanced_test_cases
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            if 'response' in locals():
                self.logger.debug(f"Raw response: {response}")
            return []
        except Exception as e:
            self.logger.error(f"Error generating comprehensive test cases: {e}")
            return []

    def validate_user_story_testability(self, user_story: dict, context: dict = None) -> dict:
        """
        Comprehensive analysis of a user story for testability with enhanced acceptance criteria validation.
        Includes boundary/failure scenario analysis and improvement recommendations.
        """
        
        # Validate input
        if not user_story:
            self.logger.error("No user story provided for testability analysis")
            return {
                "testability_score": 0,
                "improvement_recommendations": ["No user story provided"],
                "missing_scenarios": [],
                "enhanced_criteria": [],
                "risk_assessment": "High - no user story data"
            }
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'quality_standards': context.get('quality_standards', 'industry standard') if context else 'industry standard'
        }
        
        # Perform initial acceptance criteria analysis
        criteria_analysis = self._analyze_acceptance_criteria(user_story)
        
        user_input = f"""
Perform comprehensive testability analysis for this User Story with focus on acceptance criteria enhancement and boundary/failure scenario identification:

User Story: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', 'No description provided')}
Acceptance Criteria: {user_story.get('acceptance_criteria', [])}
Priority: {user_story.get('priority', 'Medium')}
Story Points: {user_story.get('story_points', 'Not estimated')}

ENHANCED ACCEPTANCE CRITERIA ANALYSIS:
Current Criteria Analysis: {criteria_analysis.get('analysis_summary', 'Standard validation')}
Testability Score: {criteria_analysis.get('testability_score', 7)}/10
Missing Coverage: {criteria_analysis.get('missing_coverage', [])}

COMPREHENSIVE TESTABILITY EVALUATION:

1. **Acceptance Criteria Quality Assessment**:
   - Clarity and specificity of requirements
   - Measurable and verifiable outcomes
   - Completeness of functional coverage
   - Missing acceptance criteria identification

2. **Boundary and Edge Case Analysis**:
   - Input validation boundaries (min/max values, length limits)
   - Data type and format validations
   - System resource limitations
   - Concurrent access scenarios
   - Performance boundary conditions

3. **Failure Scenario Identification**:
   - Error handling requirements
   - Invalid input processing
   - System failure recovery
   - Network/connectivity issues
   - Permission and security failures
   - Integration point failures

4. **Risk Assessment for Testing**:
   - Business impact of story failure
   - Technical complexity and dependencies
   - Security and compliance considerations
   - Performance and scalability risks
   - Data integrity and consistency risks

5. **Test Automation Opportunities**:
   - Regression testing candidates
   - API/service testing potential
   - Data validation automation
   - Performance monitoring needs

6. **Missing Test Scenarios**:
   - Uncover gaps in current acceptance criteria
   - Identify boundary conditions not covered
   - Suggest failure scenarios to test
   - Recommend integration test points

STORY COMPLEXITY ANALYSIS:
- Story Points: {user_story.get('story_points', 'Unknown')} 
- Priority: {user_story.get('priority', 'Medium')}
- Expected Test Coverage: {'Comprehensive' if str(user_story.get('story_points', 0)).isdigit() and int(user_story.get('story_points', 0)) >= 8 else 'Standard' if str(user_story.get('story_points', 0)).isdigit() and int(user_story.get('story_points', 0)) >= 5 else 'Basic'}

Provide detailed analysis including:
1. Enhanced testability score (1-10) with justification
2. Specific improvement recommendations for acceptance criteria
3. Missing boundary and failure test scenarios
4. Enhanced acceptance criteria suggestions
5. Comprehensive risk assessment for testing
6. Test automation recommendations
7. Priority-based testing approach recommendations
"""
        
        print(f"✅ [QATesterAgent] Performing comprehensive testability analysis for: {user_story.get('title', 'Unknown')}")
        
        try:
            response = self.run(user_input, prompt_context)
            
            if not response:
                self.logger.warning("Empty response from AI model")
                return self._extract_analysis_from_any_format("", user_story, criteria_analysis)
                
            analysis = json.loads(response)
            
            # Enhance analysis with metadata and validation
            analysis['user_story_id'] = user_story.get('id')
            analysis['user_story_title'] = user_story.get('title', 'Unknown')
            analysis['story_points'] = user_story.get('story_points')
            analysis['story_priority'] = user_story.get('priority', 'Medium')
            
            # Combine with criteria analysis
            analysis['criteria_analysis'] = criteria_analysis
            analysis['enhanced_criteria'] = analysis.get('enhanced_criteria', criteria_analysis.get('enhanced_criteria', []))
            
            # Validate and enhance the analysis
            analysis = self._enhance_testability_analysis(analysis, user_story)
            
            print(f"✅ [QATesterAgent] Testability analysis complete - Score: {analysis.get('testability_score', 'Unknown')}/10")
            return analysis
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            if 'response' in locals():
                self.logger.debug(f"Raw response: {response}")
            return self._extract_analysis_from_any_format(response, user_story, criteria_analysis)
        except Exception as e:
            self.logger.error(f"Error performing testability analysis: {e}")
            return self._extract_analysis_from_any_format(response if 'response' in locals() else "", user_story, criteria_analysis)

    def create_test_plan_structure(self, feature: dict, context: dict = None) -> dict:
        """Create a recommended test plan structure for a feature with its user stories - USER STORY FOCUSED."""
        
        test_plan_structure = {
            "feature_title": feature.get('title', 'Unknown Feature'),
            "feature_description": feature.get('description', ''),
            "test_plan_name": f"Test Plan - {feature.get('title', 'Unknown Feature')}",
            "test_suites": [],
            "user_story_focus": True,  # Indicates focus on user story testing
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
                "recommended_test_types": [],
                "coverage_focus": "comprehensive_user_story"  # Focus on comprehensive user story coverage
            }
            
            # Analyze story complexity to recommend test types
            story_points = user_story.get('story_points', 0)
            if isinstance(story_points, str):
                try:
                    story_points = int(story_points)
                except:
                    story_points = 3  # Default medium complexity
            
            # Comprehensive test type recommendations based on story complexity
            if story_points >= 8:
                suite_structure["recommended_test_types"].extend([
                    "Functional Testing", "Boundary Testing", "Negative Testing", 
                    "Integration Testing", "Performance Testing", "Security Testing"
                ])
                suite_structure["coverage_depth"] = "comprehensive"
            elif story_points >= 5:
                suite_structure["recommended_test_types"].extend([
                    "Functional Testing", "Boundary Testing", "Negative Testing", "Integration Testing"
                ])
                suite_structure["coverage_depth"] = "standard"
            else:
                suite_structure["recommended_test_types"].extend([
                    "Functional Testing", "Basic Boundary Testing", "Basic Negative Testing"
                ])
                suite_structure["coverage_depth"] = "basic"
            
            # Add priority-based recommendations
            if user_story.get('priority', '').lower() == 'high':
                suite_structure["recommended_test_types"].append("Critical Path Testing")
                suite_structure["priority_notes"] = "High priority - requires comprehensive testing"
            
            test_plan_structure["test_suites"].append(suite_structure)
        
        # Add user story focused recommendations
        total_stories = len(user_stories)
        total_test_cases = sum(len(story.get('test_cases', [])) for story in user_stories)
        
        test_plan_structure["recommendations"] = [
            f"Organize {total_test_cases} test cases across {total_stories} user story test suites",
            "Execute test cases at the user story level for faster feedback during development",
            "Use test suite organization to track individual story completion status",
            "Prioritize testing based on user story priority and business value",
            "Focus on boundary conditions and failure scenarios for each user story",
            "Validate acceptance criteria comprehensively at the story level",
            "Consider automated testing for high-complexity user stories (8+ points)"
        ]
        
        if total_stories > 10:
            test_plan_structure["recommendations"].append(
                "Consider grouping related user stories into test suite categories for better organization"
            )
        
        # Add coverage analysis
        high_complexity_stories = sum(1 for story in user_stories 
                                    if isinstance(story.get('story_points', 0), int) and story.get('story_points', 0) >= 8)
        if high_complexity_stories > 0:
            test_plan_structure["recommendations"].append(
                f"{high_complexity_stories} high-complexity stories require comprehensive boundary and failure testing"
            )
        
        print(f"📋 [QATesterAgent] Created user story-focused test plan structure for feature: {feature.get('title', 'Unknown')}")
        return test_plan_structure

    def _format_test_case_content(self, test_case: dict) -> dict:
        """
        Format test case content for enhanced readability and structure.
        Applies line breaks and formatting to descriptions, test steps, and expected results.
        """
        formatted_test_case = test_case.copy()
        
        # Format test case description
        description = test_case.get('description', '')
        if description and len(description) > 120:
            formatted_test_case['description'] = self._format_long_description(description)
        
        # Format test steps for better readability
        test_steps = test_case.get('test_steps', [])
        if test_steps:
            formatted_steps = []
            for i, step in enumerate(test_steps):
                if isinstance(step, str) and len(step) > 80:
                    # Break long test steps into readable chunks
                    formatted_step = self._format_long_test_step(step)
                    formatted_steps.append(formatted_step)
                else:
                    formatted_steps.append(step)
            formatted_test_case['test_steps'] = formatted_steps
        
        # Format expected result for readability
        expected_result = test_case.get('expected_result', '')
        if expected_result and len(expected_result) > 100:
            formatted_test_case['expected_result'] = self._format_long_expected_result(expected_result)
        
        # Format acceptance criteria mapping if present
        acceptance_criteria = test_case.get('acceptance_criteria', '')
        if acceptance_criteria and len(acceptance_criteria) > 100:
            formatted_test_case['acceptance_criteria'] = self._format_acceptance_criteria_mapping(acceptance_criteria)
        
        return formatted_test_case
    
    def _format_long_description(self, description: str) -> str:
        """Format long test case descriptions with appropriate line breaks."""
        # Split at natural break points like 'and', 'when', 'then', 'that'
        break_patterns = [
            ' and ', ' when ', ' then ', ' that ', ' which ', ' while ', 
            ', and ', ', when ', ', then ', ', that ', ', which ', ', while '
        ]
        
        formatted = description
        for pattern in break_patterns:
            if pattern in formatted and len(formatted) > 120:
                parts = formatted.split(pattern)
                if len(parts) > 1:
                    # Only break if it results in reasonably sized chunks
                    if all(40 <= len(part.strip()) <= 100 for part in parts):
                        formatted = (pattern.strip() + '\n').join(parts)
                        break
        
        return formatted
    
    def _format_long_test_step(self, step: str) -> str:
        """Format long test steps with line breaks at logical points."""
        # Remove redundant "Step X:" prefixes if present
        step_clean = step
        if step.startswith('Step ') and ':' in step:
            parts = step.split(':', 1)
            if len(parts) > 1:
                step_clean = parts[1].strip()
        
        # Break at logical points for test actions
        if len(step_clean) > 80:
            break_patterns = [
                ' and verify ', ' and check ', ' and confirm ', ' and validate ',
                ' then verify ', ' then check ', ' then confirm ', ' then validate ',
                ' with ', ' containing ', ' including ', ' such as '
            ]
            
            for pattern in break_patterns:
                if pattern in step_clean:
                    parts = step_clean.split(pattern, 1)
                    if len(parts) == 2 and 30 <= len(parts[0]) <= 80:
                        return parts[0] + pattern.strip() + '\n   ' + parts[1]
                    break
        
        return step_clean
    
    def _format_long_expected_result(self, expected_result: str) -> str:
        """Format long expected results with line breaks for clarity."""
        # Break at natural points in expected results
        break_patterns = [
            ' and ', ' with ', ' showing ', ' displaying ', ' containing ',
            ', and ', ', with ', ', showing ', ', displaying ', ', containing '
        ]
        
        formatted = expected_result
        for pattern in break_patterns:
            if pattern in formatted and len(formatted) > 100:
                parts = formatted.split(pattern, 1)
                if len(parts) == 2 and 30 <= len(parts[0]) <= 80:
                    formatted = parts[0] + pattern.strip() + '\n' + parts[1]
                    break
        
        return formatted
    
    def _format_acceptance_criteria_mapping(self, criteria: str) -> str:
        """Format acceptance criteria mappings for better readability."""
        # Handle structured acceptance criteria text
        if '; ' in criteria:
            parts = criteria.split('; ')
            if len(parts) > 1:
                return ';\n\n'.join(parts)
        
        # Handle long single criteria
        if len(criteria) > 100:
            return self._format_long_description(criteria)
        
        return criteria

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
        Enhance a single test case to meet quality standards with focus on boundary/failure scenarios.
        """
        enhanced_test_case = test_case.copy()
        
        # Validate and fix title
        title = test_case.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "Test Case")
        if not title_valid:
            self.logger.warning(f"Test case title issues: {', '.join(title_issues)}")
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
        
        # Enhanced test case classification with focus on boundary/failure scenarios
        test_type = self._classify_test_type(enhanced_test_case)
        enhanced_test_case['test_type'] = test_type
        
        # Add coverage analysis
        coverage_type = enhanced_test_case.get('coverage_type', self._determine_coverage_type(enhanced_test_case, {}))
        enhanced_test_case['coverage_type'] = coverage_type
        
        # Add priority if missing
        if not enhanced_test_case.get('priority'):
            # Priority based on test type and coverage
            if coverage_type in ['security', 'negative', 'boundary']:
                enhanced_test_case['priority'] = 'High'
            elif coverage_type in ['integration', 'performance']:
                enhanced_test_case['priority'] = 'Medium'
            else:
                enhanced_test_case['priority'] = 'Medium'
        
        # Enhanced automation recommendation
        automation_score = self._calculate_automation_score(enhanced_test_case)
        enhanced_test_case['automation_candidate'] = automation_score >= 7
        enhanced_test_case['automation_score'] = automation_score
        enhanced_test_case['automation_reasoning'] = self._get_automation_reasoning(enhanced_test_case, automation_score)
        
        # Add risk assessment
        risk_level = self._assess_test_risk(enhanced_test_case)
        enhanced_test_case['risk_level'] = risk_level
        
        # Add boundary/failure scenario metadata
        scenario_analysis = self._analyze_test_scenario(enhanced_test_case)
        enhanced_test_case.update(scenario_analysis)
        
        # Add execution complexity estimate
        complexity = self._estimate_execution_complexity(enhanced_test_case)
        enhanced_test_case['execution_complexity'] = complexity
        enhanced_test_case['estimated_execution_time'] = self._estimate_execution_time(complexity, test_type)
        
        return enhanced_test_case
    
    def _classify_test_type(self, test_case: dict) -> str:
        """
        Enhanced test type classification with boundary/failure scenario focus.
        """
        title = test_case.get('title', '').lower()
        description = test_case.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Boundary testing indicators
        boundary_keywords = ['boundary', 'edge', 'limit', 'maximum', 'minimum', 'range', 'threshold']
        if any(word in combined_text for word in boundary_keywords):
            return 'boundary'
        
        # Security testing indicators
        security_keywords = ['security', 'auth', 'permission', 'access', 'privilege', 'injection', 'xss', 'csrf']
        if any(word in combined_text for word in security_keywords):
            return 'security'
        
        # Performance testing indicators
        performance_keywords = ['performance', 'load', 'stress', 'response', 'time', 'speed', 'scalability']
        if any(word in combined_text for word in performance_keywords):
            return 'performance'
        
        # Integration testing indicators
        integration_keywords = ['integration', 'api', 'service', 'database', 'external', 'interface']
        if any(word in combined_text for word in integration_keywords):
            return 'integration'
        
        # Negative/Error testing indicators
        negative_keywords = ['error', 'invalid', 'fail', 'exception', 'negative', 'reject', 'deny']
        if any(word in combined_text for word in negative_keywords):
            return 'negative'
        
        # UI/Usability testing indicators
        ui_keywords = ['ui', 'interface', 'usability', 'user experience', 'navigation', 'display']
        if any(word in combined_text for word in ui_keywords):
            return 'ui'
        
        # Default to functional
        return 'functional'
    
    def _calculate_automation_score(self, test_case: dict) -> int:
        """
        Calculate automation suitability score (1-10).
        """
        score = 5  # Base score
        
        title = test_case.get('title', '').lower()
        description = test_case.get('description', '').lower()
        test_type = test_case.get('test_type', 'functional')
        
        # Positive indicators for automation
        if any(word in title or word in description for word in ['api', 'regression', 'smoke', 'data', 'calculation']):
            score += 2
        
        if test_type in ['integration', 'performance', 'security']:
            score += 1
        
        if any(word in title or word in description for word in ['repetitive', 'frequent', 'bulk', 'batch']):
            score += 2
        
        # Negative indicators for automation
        if any(word in title or word in description for word in ['visual', 'usability', 'manual', 'exploratory']):
            score -= 2
        
        if test_type in ['ui', 'usability']:
            score -= 1
        
        if any(word in title or word in description for word in ['complex', 'judgment', 'subjective']):
            score -= 1
        
        return max(1, min(10, score))
    
    def _get_automation_reasoning(self, test_case: dict, score: int) -> str:
        """
        Provide reasoning for automation recommendation.
        """
        test_type = test_case.get('test_type', 'functional')
        
        if score >= 8:
            return f"High automation priority - {test_type} tests are ideal for automation"
        elif score >= 6:
            return f"Good automation candidate - {test_type} tests benefit from automation"
        elif score >= 4:
            return f"Consider automation - {test_type} tests may require manual validation"
        else:
            return f"Manual testing recommended - {test_type} tests require human judgment"
    
    def _assess_test_risk(self, test_case: dict) -> str:
        """
        Assess the risk level of the test case.
        """
        test_type = test_case.get('test_type', 'functional')
        coverage_type = test_case.get('coverage_type', 'functional')
        title = test_case.get('title', '').lower()
        description = test_case.get('description', '').lower()
        
        # High risk indicators
        high_risk_keywords = ['critical', 'payment', 'financial', 'security', 'data loss', 'corruption']
        if any(word in title or word in description for word in high_risk_keywords):
            return 'high'
        
        if test_type in ['security', 'performance'] or coverage_type in ['security', 'negative']:
            return 'high'
        
        # Medium risk indicators
        if test_type in ['integration', 'boundary'] or coverage_type in ['boundary', 'integration']:
            return 'medium'
        
        # Default to low risk
        return 'low'
    
    def _analyze_test_scenario(self, test_case: dict) -> dict:
        """
        Analyze test scenario for boundary/failure characteristics.
        """
        title = test_case.get('title', '').lower()
        description = test_case.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        analysis = {
            'has_boundary_conditions': False,
            'has_failure_scenarios': False,
            'boundary_types': [],
            'failure_types': [],
            'scenario_complexity': 'low'
        }
        
        # Check for boundary conditions
        boundary_indicators = {
            'input_validation': ['length', 'size', 'format', 'type'],
            'numeric_bounds': ['maximum', 'minimum', 'range', 'limit'],
            'capacity_limits': ['capacity', 'volume', 'count', 'quota'],
            'time_bounds': ['timeout', 'expiry', 'duration', 'deadline']
        }
        
        for boundary_type, keywords in boundary_indicators.items():
            if any(word in combined_text for word in keywords):
                analysis['has_boundary_conditions'] = True
                analysis['boundary_types'].append(boundary_type)
        
        # Check for failure scenarios
        failure_indicators = {
            'input_errors': ['invalid', 'malformed', 'incorrect', 'wrong'],
            'system_failures': ['unavailable', 'down', 'timeout', 'connection'],
            'permission_failures': ['unauthorized', 'forbidden', 'access denied'],
            'data_errors': ['missing', 'null', 'empty', 'corrupt']
        }
        
        for failure_type, keywords in failure_indicators.items():
            if any(word in combined_text for word in keywords):
                analysis['has_failure_scenarios'] = True
                analysis['failure_types'].append(failure_type)
        
        # Determine scenario complexity
        if len(analysis['boundary_types']) + len(analysis['failure_types']) >= 3:
            analysis['scenario_complexity'] = 'high'
        elif len(analysis['boundary_types']) + len(analysis['failure_types']) >= 1:
            analysis['scenario_complexity'] = 'medium'
        
        return analysis
    
    def _estimate_execution_complexity(self, test_case: dict) -> str:
        """
        Estimate test execution complexity.
        """
        test_type = test_case.get('test_type', 'functional')
        steps_count = len(test_case.get('test_steps', test_case.get('steps', [])))
        scenario_complexity = test_case.get('scenario_complexity', 'low')
        
        complexity_score = 0
        
        # Base complexity from test type
        type_complexity = {
            'functional': 1,
            'ui': 2,
            'integration': 3,
            'performance': 4,
            'security': 3,
            'boundary': 2,
            'negative': 2
        }
        complexity_score += type_complexity.get(test_type, 1)
        
        # Add complexity from steps
        if steps_count > 10:
            complexity_score += 3
        elif steps_count > 5:
            complexity_score += 2
        elif steps_count > 2:
            complexity_score += 1
        
        # Add complexity from scenario
        if scenario_complexity == 'high':
            complexity_score += 2
        elif scenario_complexity == 'medium':
            complexity_score += 1
        
        if complexity_score >= 6:
            return 'high'
        elif complexity_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_execution_time(self, complexity: str, test_type: str) -> int:
        """
        Estimate test execution time in minutes.
        """
        base_times = {
            'functional': 10,
            'ui': 15,
            'integration': 20,
            'performance': 30,
            'security': 25,
            'boundary': 15,
            'negative': 12
        }
        
        base_time = base_times.get(test_type, 10)
        
        complexity_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.5
        }
        
        return int(base_time * complexity_multipliers.get(complexity, 1.0))
    
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

    def _analyze_acceptance_criteria(self, user_story: dict) -> dict:
        """
        Analyze acceptance criteria for testability and enhancement needs.
        Returns enhanced criteria and analysis summary.
        """
        current_criteria = user_story.get('acceptance_criteria', [])
        story_title = user_story.get('title', '')
        story_description = user_story.get('description', '')
        
        analysis = {
            'enhanced_criteria': current_criteria,
            'testability_score': 7,  # Default score
            'missing_coverage': [],
            'analysis_summary': ''
        }
        
        if not current_criteria:
            analysis['enhanced_criteria'] = [
                "User can access the functionality described in the story",
                "System responds appropriately to user actions",
                "Data is processed and stored correctly",
                "Appropriate feedback is provided to the user"
            ]
            analysis['testability_score'] = 5
            analysis['missing_coverage'] = ['No original acceptance criteria provided']
            analysis['analysis_summary'] = 'Basic acceptance criteria generated - original criteria missing'
            return analysis
        
        # Analyze criteria for common issues
        vague_criteria = []
        missing_negative_scenarios = True
        missing_boundary_conditions = True
        
        for i, criteria in enumerate(current_criteria):
            criteria_lower = criteria.lower()
            
            # Check for vague language
            if any(word in criteria_lower for word in ['should work', 'properly', 'correctly', 'appropriately', 'good', 'nice']):
                vague_criteria.append(f"Criteria {i+1} is too vague for testing")
                
            # Check for negative scenarios
            if any(word in criteria_lower for word in ['cannot', 'error', 'invalid', 'fail', 'reject']):
                missing_negative_scenarios = False
                
            # Check for boundary conditions
            if any(word in criteria_lower for word in ['maximum', 'minimum', 'limit', 'boundary', 'edge', 'range']):
                missing_boundary_conditions = False
        
        # Build enhanced criteria if needed
        enhanced_criteria = list(current_criteria)
        
        if missing_negative_scenarios:
            enhanced_criteria.append("System handles invalid inputs gracefully with appropriate error messages")
            analysis['missing_coverage'].append('Negative test scenarios')
            
        if missing_boundary_conditions:
            enhanced_criteria.append("System enforces appropriate limits and boundaries for input values")
            analysis['missing_coverage'].append('Boundary condition testing')
        
        # Calculate testability score
        issues_count = len(vague_criteria) + (1 if missing_negative_scenarios else 0) + (1 if missing_boundary_conditions else 0)
        analysis['testability_score'] = max(3, 10 - issues_count)
        analysis['enhanced_criteria'] = enhanced_criteria
        
        # Generate analysis summary
        if issues_count == 0:
            analysis['analysis_summary'] = 'Acceptance criteria are well-defined and testable'
        else:
            analysis['analysis_summary'] = f'Acceptance criteria enhanced - {issues_count} issues addressed: {", ".join(analysis["missing_coverage"])}'
        
        return analysis
    
    def _determine_coverage_type(self, test_case: dict, user_story: dict) -> str:
        """
        Determine the type of coverage this test case provides.
        """
        title = test_case.get('title', '').lower()
        description = test_case.get('description', '').lower()
        
        # Check for different coverage types
        if any(word in title or word in description for word in ['boundary', 'edge', 'limit', 'maximum', 'minimum']):
            return 'boundary'
        elif any(word in title or word in description for word in ['error', 'invalid', 'fail', 'exception', 'negative']):
            return 'negative'
        elif any(word in title or word in description for word in ['security', 'auth', 'permission', 'access']):
            return 'security'
        elif any(word in title or word in description for word in ['performance', 'load', 'response', 'time']):
            return 'performance'
        elif any(word in title or word in description for word in ['integration', 'api', 'service', 'database']):
            return 'integration'
        else:
            return 'functional'
    
    def _validate_test_coverage(self, test_cases: list, user_story: dict, acceptance_criteria: list) -> dict:
        """
        Validate that test cases provide comprehensive coverage for the user story.
        """
        coverage_validation = {
            'missing_coverage': [],
            'coverage_score': 0,
            'recommendations': []
        }
        
        if not test_cases:
            coverage_validation['missing_coverage'] = ['No test cases generated']
            return coverage_validation

        # Check coverage types
        coverage_types = set()
        for test_case in test_cases:
            coverage_types.add(test_case.get('coverage_type', 'functional'))

        expected_coverage = {'functional'}
        story_points = user_story.get('story_points', 0)

        # Determine expected coverage based on story complexity
        if isinstance(story_points, str) and story_points.isdigit():
            story_points = int(story_points)
        elif not isinstance(story_points, int):
            story_points = 3  # Default complexity

        if story_points >= 8:  # High complexity
            expected_coverage.update(['negative', 'boundary', 'integration', 'security'])
        elif story_points >= 5:  # Medium complexity
            expected_coverage.update(['negative', 'boundary', 'integration'])
        else:  # Low complexity
            expected_coverage.update(['negative'])

        # Check for missing coverage
        missing_coverage = expected_coverage - coverage_types
        if missing_coverage:
            coverage_validation['missing_coverage'] = [f"Missing {coverage_type} test coverage" for coverage_type in missing_coverage]

        # Check acceptance criteria coverage
        if len(test_cases) < len(acceptance_criteria):
            coverage_validation['missing_coverage'].append(f"Insufficient test cases for acceptance criteria ({len(test_cases)} test cases for {len(acceptance_criteria)} criteria)")

        # Calculate coverage score
        coverage_score = (len(coverage_types) / len(expected_coverage)) * 100
        coverage_validation['coverage_score'] = min(100, coverage_score)

        # Generate recommendations
        if coverage_validation['coverage_score'] < 80:
            coverage_validation['recommendations'].append("Consider adding more comprehensive test coverage")

        return coverage_validation
    
    def _extract_analysis_from_any_format(self, response: str, user_story: dict, criteria_analysis: dict) -> dict:
        """Extract testability analysis from LLM response in any format using intelligent parsing."""
        if not response or not response.strip():
            self.logger.error("Empty response received for testability analysis")
            return self._create_minimal_analysis(user_story, criteria_analysis)
        
        # Try to extract analysis from text format
        extracted_analysis = self._extract_analysis_from_text(response, user_story, criteria_analysis)
        
        if extracted_analysis:
            self.logger.info("Successfully extracted testability analysis from response")
            return self._enhance_testability_analysis(extracted_analysis, user_story)
        else:
            self.logger.warning("Could not extract analysis from response, creating minimal analysis")
            return self._create_minimal_analysis(user_story, criteria_analysis)

    def _extract_analysis_from_text(self, text: str, user_story: dict, criteria_analysis: dict) -> dict:
        """Extract testability analysis from unstructured text using pattern matching."""
        analysis = {}
        
        # Extract testability score
        score_patterns = [
            r"testability[_\s]*score[:\s]*(\d+)",
            r"score[:\s]*(\d+)",
            r"rating[:\s]*(\d+)"
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                analysis['testability_score'] = min(10, max(1, int(match.group(1))))
                break
        else:
            # Default score based on story complexity
            story_points = user_story.get('story_points', 3)
            analysis['testability_score'] = max(1, min(10, 8 - (story_points // 2)))
        
        # Extract recommendations
        analysis['improvement_recommendations'] = self._extract_recommendations_from_text(text)
        analysis['missing_scenarios'] = self._extract_scenarios_from_text(text)
        
        # Add metadata
        analysis.update({
            'enhanced_criteria': criteria_analysis.get('enhanced_criteria', user_story.get('acceptance_criteria', [])),
            'risk_assessment': f"Medium - Extracted from AI response, score: {analysis['testability_score']}",
            'user_story_id': user_story.get('id'),
            'user_story_title': user_story.get('title', 'Unknown'),
            'criteria_analysis': criteria_analysis,
            'story_points': user_story.get('story_points'),
            'story_priority': user_story.get('priority', 'Medium'),
            'automation_opportunities': ["Review extracted analysis"],
            'boundary_scenarios': ["Validate extracted scenarios"],
            'failure_scenarios': ["Include error handling tests"]
        })
        
        return analysis

    def _extract_recommendations_from_text(self, text: str) -> list:
        """Extract improvement recommendations from text."""
        recommendations = []
        
        # Common recommendation patterns
        rec_patterns = [
            r"recommend(?:ation)?[s]?[:\s]*(.+?)(?=\n|$)",
            r"suggest(?:ion)?[s]?[:\s]*(.+?)(?=\n|$)",
            r"improve[:\s]*(.+?)(?=\n|$)",
            r"consider[:\s]*(.+?)(?=\n|$)"
        ]
        
        for pattern in rec_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                rec = match.strip()
                if len(rec) > 10 and len(rec) < 200:
                    recommendations.append(rec)
        
        if not recommendations:
            recommendations = [
                "Review acceptance criteria for completeness",
                "Add boundary condition tests",
                "Include error handling scenarios"
            ]
        
        return recommendations[:5]  # Limit to 5 recommendations

    def _extract_scenarios_from_text(self, text: str) -> list:
        """Extract missing scenarios from text."""
        scenarios = []
        
        # Common scenario patterns
        scenario_patterns = [
            r"missing[:\s]*(.+?)(?=\n|$)",
            r"scenario[s]?[:\s]*(.+?)(?=\n|$)",
            r"test[:\s]*(.+?)(?=\n|$)"
        ]
        
        for pattern in scenario_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                scenario = match.strip()
                if len(scenario) > 5 and len(scenario) < 100:
                    scenarios.append(scenario)
        
        if not scenarios:
            scenarios = [
                "Boundary condition testing",
                "Error handling scenarios",
                "Integration testing"
            ]
        
        return scenarios[:5]  # Limit to 5 scenarios

    def _create_minimal_analysis(self, user_story: dict, criteria_analysis: dict) -> dict:
        """Create a minimal testability analysis when extraction fails."""
        story_points = user_story.get('story_points', 3)
        
        return {
            "testability_score": max(1, min(10, 8 - (story_points // 2))),
            "improvement_recommendations": [
                "Review acceptance criteria for completeness",
                "Add boundary condition tests", 
                "Include error handling scenarios"
            ],
            "missing_scenarios": [
                "Boundary condition testing",
                "Error handling scenarios",
                "Integration testing"
            ],
            "enhanced_criteria": criteria_analysis.get('enhanced_criteria', user_story.get('acceptance_criteria', [])),
            "risk_assessment": f"Medium - Story complexity: {story_points} points",
            "user_story_id": user_story.get('id'),
            "user_story_title": user_story.get('title', 'Unknown'),
            "criteria_analysis": criteria_analysis,
            "story_points": story_points,
            "story_priority": user_story.get('priority', 'Medium'),
            "automation_opportunities": ["Manual review needed"],
            "boundary_scenarios": ["Define based on story requirements"],
            "failure_scenarios": ["Include error handling tests"]
        }

    def _enhance_testability_analysis(self, analysis: dict, user_story: dict) -> dict:
        """
        Enhance and validate the testability analysis with additional quality checks.
        """
        # Ensure required fields exist
        required_fields = [
            'testability_score', 'improvement_recommendations', 'missing_scenarios',
            'enhanced_criteria', 'risk_assessment'
        ]
        
        for field in required_fields:
            if field not in analysis:
                analysis[field] = self._get_default_field_value(field, user_story)
        
        # Validate testability score
        score = analysis.get('testability_score')
        if not isinstance(score, (int, float)) or score < 1 or score > 10:
            analysis['testability_score'] = 5
            analysis['improvement_recommendations'].append("Testability score validation failed - using default")
        
        # Ensure recommendations are actionable
        if not analysis.get('improvement_recommendations'):
            analysis['improvement_recommendations'] = [
                "Review acceptance criteria for clarity and completeness",
                "Add boundary condition testing scenarios",
                "Include error handling test cases"
            ]
        
        # Add story-specific insights
        story_points = user_story.get('story_points', 0)
        if isinstance(story_points, str) and story_points.isdigit():
            story_points = int(story_points)
        
        if story_points >= 8:
            analysis['complexity_recommendations'] = [
                "High complexity story - requires comprehensive test coverage",
                "Consider performance testing for complex operations",
                "Security testing recommended for high-complexity features",
                "Integration testing across multiple system components"
            ]
        elif story_points >= 5:
            analysis['complexity_recommendations'] = [
                "Medium complexity story - standard test coverage recommended",
                "Include integration testing for external dependencies",
                "Consider boundary condition testing"
            ]
        else:
            analysis['complexity_recommendations'] = [
                "Low complexity story - basic functional testing sufficient",
                "Focus on acceptance criteria validation"
            ]
        
        return analysis
    
    def _get_default_field_value(self, field: str, user_story: dict):
        """
        Get default value for a missing analysis field.
        """
        defaults = {
            'testability_score': 5,
            'improvement_recommendations': ["Review acceptance criteria", "Add boundary tests", "Include error scenarios"],
            'missing_scenarios': ["Boundary testing", "Error handling", "Integration testing"],
            'enhanced_criteria': user_story.get('acceptance_criteria', []),
            'risk_assessment': f"Medium - {user_story.get('story_points', 'Unknown')} story points, requires validation",
            'automation_opportunities': ["API testing", "Regression testing"],
            'boundary_scenarios': ["Input validation", "Data limits"],
            'failure_scenarios': ["Error handling", "System failures"]
        }
        return defaults.get(field, [])

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from AI response with improved bracket counting and validation.
        
        Args:
            response: Raw response from AI model
            
        Returns:
            Cleaned JSON string
        """
        if not response:
            return "[]"
        
        import re
        
        # Look for JSON inside ```json blocks
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, response, re.IGNORECASE)
        
        if json_match:
            return json_match.group(1).strip()
        
        # Look for JSON inside ``` blocks (without language specifier)
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        code_match = re.search(code_pattern, response)
        
        if code_match:
            content = code_match.group(1).strip()
            # Check if it looks like JSON (starts with { or [)
            if content.startswith(('{', '[')):
                return content
        
        # Enhanced JSON extraction with proper bracket counting
        # Find the start of JSON array
        start_idx = response.find('[')
        if start_idx == -1:
            start_idx = response.find('{')
            if start_idx == -1:
                self.logger.warning("No JSON found in response")
                return "[]"
        
        # Count brackets/braces to find the complete JSON structure
        if response[start_idx] == '[':
            bracket_count = 0
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            # Found the end of the JSON array
                            return response[start_idx:i+1]
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
        
        else:  # Starting with '{'
            brace_count = 0
            bracket_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found the end of the JSON object
                            return response[start_idx:i+1]
                    elif char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
        
        # Fallback: return everything from start to end of response
        self.logger.warning("Could not find complete JSON structure, attempting full response")
        return response[start_idx:].strip()
    
    def _convert_markdown_to_json(self, markdown_response: str) -> str:
        """
        Convert markdown-formatted test cases to JSON format.
        
        Args:
            markdown_response: Markdown formatted response with test cases
            
        Returns:
            JSON string with parsed test cases
        """
        import re
        
        test_cases = []
        
        try:
            # Pattern to match test case sections - flexible for different formats  
            patterns = [
                r'#### \*\*Test Case \d+:.*?\*\*\n(.*?)(?=\n---\n\n#### \*\*Test Case|\n---\n\n##|\Z)',
                r'### \*\*Test Case \d+:.*?\*\*\n(.*?)(?=\n---\n\n### \*\*Test Case|\n---\n\n##|\Z)',  
                r'## \d+\. .*?\n\n### \*\*Test Case \d+:.*?\*\*\n(.*?)(?=\n---\n\n## \d+\.|\n---\n\n##|\Z)'
            ]
            
            matches = []
            for pattern in patterns:
                matches = re.findall(pattern, markdown_response, re.DOTALL)
                if matches:
                    break
            
            for i, test_case_content in enumerate(matches):
                test_case = self._parse_single_test_case(test_case_content, i + 1)
                if test_case:
                    test_cases.append(test_case)
            
            # If no matches with the above pattern, try a simpler approach
            if not test_cases:
                self.logger.info("Trying alternative markdown parsing...")
                test_cases = self._parse_markdown_alternative(markdown_response)
            
        except Exception as e:
            self.logger.error(f"Failed to parse markdown test cases: {e}")
            # Return empty list instead of fallback content
            test_cases = []
        
        return json.dumps(test_cases)
    
    def _parse_single_test_case(self, content: str, case_number: int) -> dict:
        """
        Parse a single test case from markdown content.
        
        Args:
            content: Raw content of a single test case
            case_number: Test case number for fallback naming
            
        Returns:
            Dictionary representing the test case
        """
        test_case = {}
        
        try:
            lines = content.strip().split('\n')
            
            # Extract basic information
            title = None
            description = None
            test_steps = []
            expected_result = None
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for field markers
                if line.startswith('- **Test Case ID:**'):
                    test_case['test_id'] = line.split(':', 1)[1].strip()
                elif line.startswith('- **Title:**'):
                    title = line.split(':', 1)[1].strip()
                elif line.startswith('- **Description:**'):
                    description = line.split(':', 1)[1].strip()
                elif line.startswith('- **Test Steps:**'):
                    current_section = 'steps'
                elif line.startswith('- **Expected Results:**'):
                    current_section = 'expected'
                elif line.startswith('- **Acceptance Criteria Covered:**'):
                    test_case['acceptance_criteria'] = line.split(':', 1)[1].strip()
                elif line.startswith('- **Security:**'):
                    test_case['coverage_type'] = 'security'
                elif line.startswith('- **Performance**'):
                    test_case['coverage_type'] = 'performance'
                elif line.startswith('- **Integration:**'):
                    test_case['coverage_type'] = 'integration'
                elif current_section == 'steps' and line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    test_steps.append(line[2:].strip())
                elif current_section == 'expected':
                    if line.startswith('- '):
                        if not expected_result:
                            expected_result = line[2:].strip()
                        else:
                            expected_result += "; " + line[2:].strip()
            
            # Build the test case
            test_case['title'] = title or f"Test Case {case_number}"
            test_case['description'] = description or f"Test case {case_number} description"
            test_case['test_steps'] = test_steps if test_steps else ["Execute test case"]
            test_case['expected_result'] = expected_result or "Test passes successfully"
            
            if 'coverage_type' not in test_case:
                test_case['coverage_type'] = 'functional'
            
            test_case['priority'] = 'Medium'
            test_case['automation_candidate'] = False
            
        except Exception as e:
            self.logger.error(f"Error parsing test case {case_number}: {e}")
            test_case = {
                'title': f"Test Case {case_number} (Parse Error)",
                'description': "Failed to parse test case details",
                'test_steps': ["Review manually"],
                'expected_result': "Manual review required",
                'coverage_type': 'functional',
                'priority': 'Medium'
            }
        
        return test_case
    
    def _parse_markdown_alternative(self, markdown_response: str) -> list:
        """
        Alternative markdown parsing approach for different formats.
        
        Args:
            markdown_response: Markdown response text
            
        Returns:
            List of test case dictionaries
        """
        test_cases = []
        
        import re  # Ensure re is imported
        
        # Try multiple patterns to match test cases
        patterns = [
            # Pattern 1: ### **Test Case 1: Title** (most common AI format)
            r'### \*\*Test Case \d+: (.+?)\*\*\n(.*?)(?=\n---\n|### \*\*Test Case|\n##|\Z)',
            # Pattern 2: #### **Test Case 1: Title** 
            r'#### \*\*Test Case \d+: (.+?)\*\*\n(.*?)(?=\n---\n|#### \*\*Test Case|\n##|\Z)',
            # Pattern 3: #### TC01 - Title format
            r'#### (TC\d+) - (.+?)\n(.*?)(?=\n#### TC\d+|\n---|\n##|\Z)',
            # Pattern 4: **Test Case 1:** (without ###)
            r'\*\*Test Case \d+:\s*(.+?)\*\*\n(.*?)(?=\n\*\*Test Case|\n---|\n##|\Z)',
            # Pattern 5: Simple numbered format
            r'(\d+)\. (.+?)\n(.*?)(?=\n\d+\.|\n---|\n##|\Z)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, markdown_response, re.DOTALL | re.IGNORECASE)
            if matches:
                self.logger.info(f"Found {len(matches)} test cases with pattern")
                for i, match in enumerate(matches):
                    if len(match) == 3:  # TC_ID, Title, Content
                        tc_id, title, content = match
                        test_case = self._parse_test_case_content(title, content, i + 1)
                        if test_case:
                            test_cases.append(test_case)
                    elif len(match) == 2:  # Title, Content
                        title, content = match
                        test_case = self._parse_test_case_content(title, content, i + 1)
                        if test_case:
                            test_cases.append(test_case)
                break
        
        # If still no test cases found, create a basic one from the content
        if not test_cases:
            test_cases = [{
                'title': 'Comprehensive Test Coverage',
                'description': 'AI generated comprehensive test cases - manual extraction needed',
                'test_steps': ['Review AI response', 'Extract specific test cases', 'Implement test procedures'],
                'expected_result': 'All test scenarios covered as per AI recommendations',
                'coverage_type': 'comprehensive',
                'priority': 'High'
            }]
        
        return test_cases
    
    def _parse_test_case_content(self, title: str, content: str, case_number: int) -> dict:
        """
        Parse test case content from different markdown formats.
        
        Args:
            title: Test case title
            content: Test case content 
            case_number: Test case number for fallback
            
        Returns:
            Dictionary representing the test case
        """
        test_case = {
            'title': title.strip(),
            'description': '',
            'test_steps': [],
            'expected_result': 'Test passes successfully',
            'coverage_type': 'functional',
            'priority': 'Medium'
        }
        
        try:
            lines = content.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for different section markers
                if any(marker in line.lower() for marker in ['precondition', 'setup']):
                    current_section = 'preconditions'
                elif any(marker in line.lower() for marker in ['step', 'action']):
                    current_section = 'steps'
                elif any(marker in line.lower() for marker in ['expected', 'result']):
                    current_section = 'expected'
                elif any(marker in line.lower() for marker in ['title:', 'description:']):
                    if 'description:' in line.lower():
                        test_case['description'] = line.split(':', 1)[-1].strip()
                elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    # Numbered steps
                    test_case['test_steps'].append(line[2:].strip())
                elif line.startswith('- ') and current_section == 'steps':
                    # Bullet point steps
                    test_case['test_steps'].append(line[2:].strip())
                elif current_section == 'expected' and line.startswith('- '):
                    # Expected results
                    if test_case['expected_result'] == 'Test passes successfully':
                        test_case['expected_result'] = line[2:].strip()
                    else:
                        test_case['expected_result'] += "; " + line[2:].strip()
            
            # If no explicit steps found, try to extract from content
            if not test_case['test_steps']:
                # Look for action words in content
                action_lines = []
                for line in lines:
                    if any(word in line.lower() for word in ['submit', 'enter', 'click', 'verify', 'check', 'navigate', 'access']):
                        action_lines.append(line.strip())
                
                if action_lines:
                    test_case['test_steps'] = action_lines[:5]  # Limit to 5 steps
                else:
                    test_case['test_steps'] = ['Execute test case steps', 'Verify expected behavior']
            
            # Determine coverage type from title and content
            combined_text = f"{title} {content}".lower()
            if any(word in combined_text for word in ['boundary', 'edge', 'limit', 'max', 'min']):
                test_case['coverage_type'] = 'boundary'
            elif any(word in combined_text for word in ['security', 'auth', 'permission', 'access']):
                test_case['coverage_type'] = 'security'
            elif any(word in combined_text for word in ['performance', 'load', 'scale', 'concurrent']):
                test_case['coverage_type'] = 'performance'
            elif any(word in combined_text for word in ['integration', 'api', 'database', 'service']):
                test_case['coverage_type'] = 'integration'
            elif any(word in combined_text for word in ['error', 'fail', 'invalid', 'exception']):
                test_case['coverage_type'] = 'negative'
                
            # Set priority based on content
            if any(word in combined_text for word in ['critical', 'high', 'important']):
                test_case['priority'] = 'High'
            elif any(word in combined_text for word in ['low', 'minor']):
                test_case['priority'] = 'Low'
                
        except Exception as e:
            self.logger.error(f"Error parsing test case content: {e}")
            # Return basic fallback
            test_case['test_steps'] = ['Execute test procedure', 'Verify results']
        
        return test_case
