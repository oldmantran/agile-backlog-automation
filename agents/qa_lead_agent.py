"""
QA Lead Agent - Orchestrates test planning, suite creation, and test case generation
"""

import logging
from typing import Dict, List, Any, Optional
from agents.base_agent import Agent
from agents.qa.test_plan_agent import TestPlanAgent
from agents.qa.test_suite_agent import TestSuiteAgent
from agents.qa.test_case_agent import TestCaseAgent
from utils.qa_completeness_validator import QACompletenessValidator
from integrators.azure_devops_api import AzureDevOpsIntegrator


class QALeadAgent(Agent):
    """
    QA Lead Agent that orchestrates the quality assurance process.
    
    Manages three specialized sub-agents:
    - TestPlanAgent: Creates test plans for features
    - TestSuiteAgent: Creates test suites for user stories
    - TestCaseAgent: Creates individual test cases
    """
    
    def __init__(self, config):
        super().__init__("qa_lead_agent", config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Get QA Lead Agent specific configuration
        qa_config = config.get_setting('agents', 'qa_lead_agent') or {}
        sub_agents_config = qa_config.get('sub_agents', {})
        
        # Initialize sub-agents with their specific configurations
        self.test_plan_agent = TestPlanAgent(config)
        self.test_suite_agent = TestSuiteAgent(config)
        self.test_case_agent = TestCaseAgent(config)
        
        # Initialize completeness validator
        self.completeness_validator = QACompletenessValidator(config)
        
        # Initialize Azure DevOps integration
        try:
            if hasattr(config, 'env') and config.env.get("AZURE_DEVOPS_ORG"):
                paths = config.get_project_paths()
                self.azure_api = AzureDevOpsIntegrator(
                    organization_url=config.env.get("AZURE_DEVOPS_ORG", ""),
                    project=config.env.get("AZURE_DEVOPS_PROJECT", ""),
                    personal_access_token=config.env.get("AZURE_DEVOPS_PAT", ""),
                    area_path=paths.get("area", ""),
                    iteration_path=paths.get("iteration", "")
                )
            else:
                self.azure_api = None
        except Exception as e:
            self.logger.warning(f"Azure DevOps integration not available: {e}")
            self.azure_api = None
        
        # QA strategy settings
        self.max_retries = 3
        self.area_path_strategy = "feature_based"  # Options: feature_based, epic_based, global
        
        # Test organization requirements
        self.test_organization_config = qa_config.get('test_organization', {})
        self.enforce_completeness = self.test_organization_config.get('enforce_completeness', True)
        self.ado_integration_config = qa_config.get('ado_integration', {})
        self.auto_remediate = self.ado_integration_config.get('auto_create_test_plans', True)
        
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
            
            # Post-processing: Validate completeness and auto-remediate if needed
            if self.enforce_completeness:
                self.logger.info("Validating test organization completeness")
                completeness_report = self.completeness_validator.validate_test_organization(epics)
                
                # Add completeness info to summary
                qa_summary['completeness_score'] = completeness_report.completeness_score
                qa_summary['completeness_report'] = self.completeness_validator.generate_completeness_report(completeness_report)
                
                # Auto-remediate if configured and completeness is low
                if (self.auto_remediate and completeness_report.completeness_score < 0.8 and 
                    hasattr(self, 'ado_client') and self.ado_client):
                    self.logger.info("Auto-remediating test organization gaps")
                    remediation_result = self.completeness_validator.auto_remediate_test_organization(epics, self.ado_client)
                    qa_summary['remediation_result'] = remediation_result
                    
                    # Re-validate after remediation
                    updated_report = self.completeness_validator.validate_test_organization(epics)
                    qa_summary['final_completeness_score'] = updated_report.completeness_score
            
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
            self.logger.info(f"Creating test plan for feature: {feature_name}")
            test_plan_result = self._create_feature_test_plan(
                epic, feature, context, area_path
            )
            
            if test_plan_result.get('success'):
                result['test_plans_created'] = 1
                feature['test_plan'] = test_plan_result['test_plan']
                self.logger.info(f"Generated test plan for feature: {feature_name}")
                
                # Step 2: Create test suites for each user story
                self.logger.info(f"Creating test suites for feature: {feature_name}")
                suites_result = self._create_user_story_suites(
                    feature, context, area_path
                )
                result['test_suites_created'] = suites_result.get('suites_created', 0)
                result['errors'].extend(suites_result.get('errors', []))
                
                # Step 3: Create test cases for each user story
                self.logger.info(f"Creating test cases for feature: {feature_name}")
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
            story_name = user_story.get('title', 'Unknown User Story')
            try:
                self.logger.info(f"Creating test suite for user story: {story_name}")
                suite_result = self.test_suite_agent.create_test_suite(
                    feature=feature,
                    user_story=user_story,
                    context=context,
                    area_path=area_path
                )
                
                if suite_result.get('success'):
                    suites_created += 1
                    user_story['test_suite'] = suite_result['test_suite']
                    self.logger.info(f"Created test suite for user story: {story_name}")
                else:
                    error_msg = f"Failed to create test suite for user story: {story_name}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error creating test suite for user story {story_name}: {e}"
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
            story_name = user_story.get('title', 'Unknown User Story')
            try:
                self.logger.info(f"Creating test cases for user story: {story_name}")
                cases_result = self.test_case_agent.create_test_cases(
                    feature=feature,
                    user_story=user_story,
                    context=context,
                    area_path=area_path
                )
                
                if cases_result.get('success'):
                    cases_created += cases_result.get('cases_created', 0)
                    test_cases = cases_result.get('test_cases', [])
                    
                    # Ensure test cases are properly linked to their test suite
                    if user_story.get('test_suite'):
                        for test_case in test_cases:
                            if not test_case.get('test_suite_id'):
                                test_case['test_suite_id'] = user_story['test_suite'].get('id')
                                test_case['linked_to_suite'] = True
                    
                    user_story['test_cases'] = test_cases
                    self.logger.info(f"Created {len(test_cases)} test cases for user story: {story_name}")
                else:
                    error_msg = f"Failed to create test cases for user story: {story_name}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error creating test cases for user story {story_name}: {e}"
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
        
        # Try to derive from project name, domain, or description
        project_name = project_context.get('project_name', '')
        domain = project_context.get('domain', '')
        description = project_context.get('description', '')
        vision = project_context.get('vision', {}).get('visionStatement', '')
        
        # Check all text fields for ride sharing indicators
        all_text = f"{project_name} {domain} {description} {vision}".lower()
        
        # Enhanced area path logic with better pattern matching
        if any(keyword in all_text for keyword in ['ride', 'ridesharing', 'ride-sharing', 'transport', 'mobility', 'vehicle', 'autonomous']):
            return "Ride Sharing"
        elif any(keyword in all_text for keyword in ['oil', 'gas', 'petroleum', 'drilling', 'refinery']):
            return "Oil and Gas Operations"
        elif any(keyword in all_text for keyword in ['fintech', 'banking', 'finance', 'payment']):
            return "Financial Services"
        elif any(keyword in all_text for keyword in ['ecommerce', 'e-commerce', 'retail', 'shopping']):
            return "E-Commerce"
        elif any(keyword in all_text for keyword in ['healthcare', 'medical', 'health', 'patient']):
            return "Healthcare"
        else:
            # Use project name as area path, fallback to "Project"
            return project_name or "Project"
    
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

    def correct_area_path_mismatch(self, test_case_id: int, correct_area_path: str, parent_user_story_id: int = None) -> bool:
        """
        Correct area path mismatch for a test case as identified by Backlog Sweeper.
        Used when agent-created test cases have incorrect area paths that don't match parent user stories.
        """
        try:
            # Get current test case details to verify the issue
            test_case = self.azure_api.get_work_item_details(test_case_id)
            if not test_case:
                self.logger.error(f"Test case {test_case_id} not found")
                return False
            
            current_area_path = test_case.get('fields', {}).get('System.AreaPath', '')
            
            # Verify this is actually a mismatch that needs correction
            if current_area_path == correct_area_path:
                self.logger.info(f"Test case {test_case_id} already has correct area path: {correct_area_path}")
                return True
            
            # Update the area path
            fields = {'/fields/System.AreaPath': correct_area_path}
            self.azure_api.update_work_item(test_case_id, fields)
            
            self.logger.info(f"✅ Corrected area path for test case {test_case_id}: '{current_area_path}' → '{correct_area_path}'")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to correct area path for test case {test_case_id}: {e}")
            return False

    def bulk_correct_area_path_mismatches(self, area_path_corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Correct multiple area path mismatches in bulk.
        
        Args:
            area_path_corrections: List of dicts with keys: test_case_id, correct_area_path, parent_user_story_id
            
        Returns:
            Summary of correction results
        """
        results = {'successful': 0, 'failed': 0, 'errors': []}
        
        for correction in area_path_corrections:
            test_case_id = correction.get('test_case_id')
            correct_area_path = correction.get('correct_area_path')
            parent_user_story_id = correction.get('parent_user_story_id')
            
            try:
                if self.correct_area_path_mismatch(test_case_id, correct_area_path, parent_user_story_id):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to correct area path for test case {test_case_id}")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error correcting test case {test_case_id}: {e}")
        
        self.logger.info(f"Bulk area path correction complete: {results['successful']} successful, {results['failed']} failed")
        return results

    def assign_orphaned_test_case_to_suite(self, test_case_id: int, parent_user_story_id: int = None) -> bool:
        """
        Assign an orphaned test case to the appropriate test suite.
        Delegates to TestSuiteAgent for proper suite organization.
        """
        try:
            return self.test_suite_agent.assign_orphaned_test_case(test_case_id, parent_user_story_id)
        except Exception as e:
            self.logger.error(f"❌ Failed to assign orphaned test case {test_case_id}: {e}")
            return False
