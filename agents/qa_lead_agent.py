"""
QA Lead Agent - Orchestrates test planning, suite creation, and test case generation
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import BaseAgent
from agents.qa.test_plan_agent import TestPlanAgent
from agents.qa.test_suite_agent import TestSuiteAgent
from agents.qa.test_case_agent import TestCaseAgent


class QALeadAgent(BaseAgent):
    """
    QA Lead Agent that orchestrates the quality assurance process.
    
    Manages three specialized sub-agents:
    - TestPlanAgent: Creates test plans for features
    - TestSuiteAgent: Creates test suites for user stories
    - TestCaseAgent: Creates individual test cases
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize sub-agents
        self.test_plan_agent = TestPlanAgent(config.get('sub_agents', {}).get('test_plan_agent', {}))
        self.test_suite_agent = TestSuiteAgent(config.get('sub_agents', {}).get('test_suite_agent', {}))
        self.test_case_agent = TestCaseAgent(config.get('sub_agents', {}).get('test_case_agent', {}))
        
        # QA strategy settings
        self.max_retries = 3
        self.area_path_strategy = "feature_based"  # Options: feature_based, epic_based, global
        
    def generate_quality_assurance(self, 
                                 epics: List[Dict[str, Any]], 
                                 context: Dict[str, Any],
                                 area_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Orchestrate complete QA process for all epics and features.
        
        Args:
            epics: List of epic dictionaries with features and user stories
            context: Project context and configuration
            area_path: Optional area path override
            
        Returns:
            Updated epics with test plans, suites, and cases
        """
        self.logger.info("Starting QA orchestration process")
        
        try:
            # Set default area path if not provided
            if not area_path:
                area_path = self._determine_area_path(context)
            
            qa_summary = {
                'test_plans_created': 0,
                'test_suites_created': 0,
                'test_cases_created': 0,
                'errors': []
            }
            
            # Process each epic
            for epic_idx, epic in enumerate(epics):
                self.logger.info(f"Processing QA for epic: {epic.get('title', f'Epic {epic_idx + 1}')}")
                
                # Process each feature in the epic
                for feature_idx, feature in enumerate(epic.get('features', [])):
                    feature_result = self._process_feature_qa(
                        epic, feature, context, area_path, epic_idx, feature_idx
                    )
                    
                    # Update summary
                    qa_summary['test_plans_created'] += feature_result.get('test_plans_created', 0)
                    qa_summary['test_suites_created'] += feature_result.get('test_suites_created', 0)
                    qa_summary['test_cases_created'] += feature_result.get('test_cases_created', 0)
                    qa_summary['errors'].extend(feature_result.get('errors', []))
            
            self.logger.info(f"QA orchestration completed. Summary: {qa_summary}")
            return {'epics': epics, 'qa_summary': qa_summary}
            
        except Exception as e:
            self.logger.error(f"QA orchestration failed: {e}")
            raise
    
    def _process_feature_qa(self, 
                           epic: Dict[str, Any], 
                           feature: Dict[str, Any], 
                           context: Dict[str, Any],
                           area_path: str,
                           epic_idx: int,
                           feature_idx: int) -> Dict[str, Any]:
        """Process QA for a single feature."""
        feature_name = feature.get('title', f'Feature {feature_idx + 1}')
        self.logger.info(f"Processing QA for feature: {feature_name}")
        
        result = {
            'test_plans_created': 0,
            'test_suites_created': 0,
            'test_cases_created': 0,
            'errors': []
        }
        
        try:
            # Step 1: Create test plan for the feature
            test_plan_result = self._create_feature_test_plan(
                epic, feature, context, area_path
            )
            
            if test_plan_result.get('success'):
                result['test_plans_created'] = 1
                feature['test_plan'] = test_plan_result['test_plan']
                
                # Step 2: Create test suites for each user story
                suites_result = self._create_user_story_suites(
                    feature, context, area_path
                )
                result['test_suites_created'] = suites_result.get('suites_created', 0)
                result['errors'].extend(suites_result.get('errors', []))
                
                # Step 3: Create test cases for each user story
                cases_result = self._create_user_story_test_cases(
                    feature, context, area_path
                )
                result['test_cases_created'] = cases_result.get('cases_created', 0)
                result['errors'].extend(cases_result.get('errors', []))
                
            else:
                error_msg = f"Failed to create test plan for feature: {feature_name}"
                self.logger.error(error_msg)
                result['errors'].append(error_msg)
                
        except Exception as e:
            error_msg = f"Error processing feature QA for {feature_name}: {e}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _create_feature_test_plan(self, 
                                 epic: Dict[str, Any], 
                                 feature: Dict[str, Any], 
                                 context: Dict[str, Any],
                                 area_path: str) -> Dict[str, Any]:
        """Create test plan for a feature using TestPlanAgent."""
        try:
            return self.test_plan_agent.create_test_plan(
                epic=epic,
                feature=feature,
                context=context,
                area_path=area_path
            )
        except Exception as e:
            self.logger.error(f"Test plan creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_user_story_suites(self, 
                                 feature: Dict[str, Any], 
                                 context: Dict[str, Any],
                                 area_path: str) -> Dict[str, Any]:
        """Create test suites for all user stories in a feature."""
        suites_created = 0
        errors = []
        
        for user_story in feature.get('user_stories', []):
            try:
                suite_result = self.test_suite_agent.create_test_suite(
                    feature=feature,
                    user_story=user_story,
                    context=context,
                    area_path=area_path
                )
                
                if suite_result.get('success'):
                    suites_created += 1
                    user_story['test_suite'] = suite_result['test_suite']
                else:
                    errors.append(f"Failed to create test suite for user story: {user_story.get('title', 'Unknown')}")
                    
            except Exception as e:
                error_msg = f"Error creating test suite for user story {user_story.get('title', 'Unknown')}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            'suites_created': suites_created,
            'errors': errors
        }
    
    def _create_user_story_test_cases(self, 
                                     feature: Dict[str, Any], 
                                     context: Dict[str, Any],
                                     area_path: str) -> Dict[str, Any]:
        """Create test cases for all user stories in a feature."""
        cases_created = 0
        errors = []
        
        for user_story in feature.get('user_stories', []):
            try:
                cases_result = self.test_case_agent.create_test_cases(
                    feature=feature,
                    user_story=user_story,
                    context=context,
                    area_path=area_path
                )
                
                if cases_result.get('success'):
                    cases_created += cases_result.get('cases_created', 0)
                    user_story['test_cases'] = cases_result.get('test_cases', [])
                else:
                    errors.append(f"Failed to create test cases for user story: {user_story.get('title', 'Unknown')}")
                    
            except Exception as e:
                error_msg = f"Error creating test cases for user story {user_story.get('title', 'Unknown')}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            'cases_created': cases_created,
            'errors': errors
        }
    
    def _determine_area_path(self, context: Dict[str, Any]) -> str:
        """Determine area path based on context and strategy."""
        # Try to get area path from context
        project_context = context.get('project_context', {})
        
        # Look for explicit area path setting
        if 'area_path' in project_context:
            return project_context['area_path']
        
        # Try to derive from project name or domain
        project_name = project_context.get('project_name', '')
        domain = project_context.get('domain', '')
        
        # Default area path logic
        if 'ride' in project_name.lower() or 'transport' in domain.lower():
            return "Ride Sharing"
        elif 'oil' in domain.lower() or 'gas' in domain.lower():
            return "Oil and Gas Operations"
        else:
            # Use project name as area path
            return project_name or "Backlog Automation"
    
    def validate_qa_output(self, epics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the QA output for completeness and consistency."""
        validation_result = {
            'valid': True,
            'issues': [],
            'summary': {
                'features_with_test_plans': 0,
                'user_stories_with_suites': 0,
                'user_stories_with_test_cases': 0,
                'total_features': 0,
                'total_user_stories': 0
            }
        }
        
        for epic in epics:
            for feature in epic.get('features', []):
                validation_result['summary']['total_features'] += 1
                
                # Check for test plan
                if 'test_plan' in feature:
                    validation_result['summary']['features_with_test_plans'] += 1
                else:
                    validation_result['issues'].append(f"Feature '{feature.get('title', 'Unknown')}' missing test plan")
                    validation_result['valid'] = False
                
                # Check user stories
                for user_story in feature.get('user_stories', []):
                    validation_result['summary']['total_user_stories'] += 1
                    
                    # Check for test suite
                    if 'test_suite' in user_story:
                        validation_result['summary']['user_stories_with_suites'] += 1
                    else:
                        validation_result['issues'].append(f"User story '{user_story.get('title', 'Unknown')}' missing test suite")
                        validation_result['valid'] = False
                    
                    # Check for test cases
                    if user_story.get('test_cases'):
                        validation_result['summary']['user_stories_with_test_cases'] += 1
                    else:
                        validation_result['issues'].append(f"User story '{user_story.get('title', 'Unknown')}' missing test cases")
                        validation_result['valid'] = False
        
        return validation_result
