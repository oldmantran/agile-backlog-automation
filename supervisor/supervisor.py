"""
Supervisor Module - Orchestrates the multi-agent backlog automation workflow.

The Supervisor manages the complete pipeline from product vision to Azure DevOps work items,
coordinating between agents, managing data flow, and handling integrations.
"""

import os
import json
import yaml
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import re

from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.decomposition_agent import DecompositionAgent
from agents.feature_decomposer_agent import FeatureDecomposerAgent
from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
from agents.developer_agent import DeveloperAgent
from agents.qa_tester_agent import QATesterAgent
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from utils.project_context import ProjectContext
from utils.logger import setup_logger
from utils.notifier import Notifier
from integrators.azure_devops_api import AzureDevOpsIntegrator


class WorkflowSupervisor:
    """
    Orchestrates the multi-agent workflow for transforming product visions into structured backlogs.
    
    Responsibilities:
    - Load configuration and initialize agents
    - Manage project context and prompt customization
    - Coordinate agent execution in sequence
    - Handle data flow between agents
    - Integrate with Azure DevOps
    - Send notifications and generate reports
    - Provide human-in-the-loop capabilities
    """
    
    def __init__(self, config_path: str = None, organization_url: str = None, project: str = None, personal_access_token: str = None, area_path: str = None, iteration_path: str = None, job_id: str = None):
        """Initialize the supervisor with configuration and agents."""
        # Load configuration
        self.config = Config(config_path) if config_path else Config()
        
        # Setup logging
        self.logger = setup_logger("supervisor", "logs/supervisor.log")
        self.logger.info(f"Initializing WorkflowSupervisor for job_id={job_id}")
        if organization_url or project or area_path or iteration_path:
            self.logger.info(f"Azure DevOps config for job_id={job_id}: org_url={organization_url}, project={project}, area_path={area_path}, iteration_path={iteration_path}")
        
        # Initialize project context
        self.project_context = ProjectContext(self.config)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Store area/iteration path for Azure DevOps
        self.area_path = area_path
        self.iteration_path = iteration_path
        
        # Initialize integrators and notifiers
        self.organization_url = organization_url
        self.project = project
        self.personal_access_token = personal_access_token
        self.job_id = job_id
        if all([self.organization_url, self.project, self.personal_access_token, self.area_path, self.iteration_path]):
            self.azure_integrator = AzureDevOpsIntegrator(
                organization_url=self.organization_url,
                project=self.project,
                personal_access_token=self.personal_access_token,
                area_path=self.area_path,
                iteration_path=self.iteration_path
            )
        else:
            self.azure_integrator = None
        self.notifier = Notifier(self.config)
        
        # Workflow state
        self.workflow_data = {}
        self.execution_metadata = {
            'start_time': None,
            'end_time': None,
            'stages_completed': [],
            'errors': [],
            'outputs_generated': []
        }
        self.sweeper_agent = None  # Will be initialized as needed
        self.sweeper_retry_tracker = {}  # {stage: {item_id: retry_count}}
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with configuration."""
        agents = {}
        
        try:
            agents['epic_strategist'] = EpicStrategist(self.config)
            agents['feature_decomposer_agent'] = FeatureDecomposerAgent(self.config)
            agents['user_story_decomposer_agent'] = UserStoryDecomposerAgent(self.config)
            agents['developer_agent'] = DeveloperAgent(self.config)
            agents['qa_tester_agent'] = QATesterAgent(self.config)
            
            # Keep backward compatibility with old decomposition_agent reference
            agents['decomposition_agent'] = agents['feature_decomposer_agent']
            
            self.logger.info(f"Initialized {len(agents)} agents successfully")
            return agents
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def configure_project_context(self, project_type: str = None, custom_context: Dict[str, Any] = None):
        """Configure project context for domain-aware prompt generation."""
        try:
            if project_type:
                self.project_context.set_project_type(project_type)
                self.logger.info(f"Applied project type: {project_type}")
            
            if custom_context:
                self.project_context.update_context(custom_context)
                self.logger.info(f"Applied custom context: {list(custom_context.keys())}")
            
            # Log context summary
            context_summary = self.project_context.get_context_summary()
            self.logger.info(f"Project context configured:\\n{context_summary}")
            
        except Exception as e:
            self.logger.error(f"Failed to configure project context: {e}")
            raise
    
    def _validate_epics(self):
        """Validate that epics have been generated and meet minimum requirements."""
        epics = self.workflow_data.get('epics', [])
        errors = []
        if not epics or not all('title' in e and e['title'] for e in epics):
            self.logger.error("Epic Strategist did not generate valid epics. Skipping invalid epics.")
            errors.append("No valid epics generated.")
        self.logger.info(f"Validation completed: {len(epics)} epics checked, {len(errors)} errors.")

    def _validate_features(self):
        """Validate that every epic has at least one feature."""
        epics = self.workflow_data.get('epics', [])
        errors = []
        for epic in epics:
            features = epic.get('features', [])
            if not features or not all('title' in f and f['title'] for f in features):
                self.logger.error(f"Decomposition Agent did not generate valid features for epic '{epic.get('title', 'Untitled')}'. Skipping invalid features.")
                errors.append(f"Epic '{epic.get('title', 'Untitled')}' missing valid features.")
        self.logger.info(f"Validation completed: All epics checked for features, {len(errors)} errors.")

    def _validate_user_stories(self):
        """Validate that every feature has at least one user story."""
        epics = self.workflow_data.get('epics', [])
        errors = []
        for epic in epics:
            for feature in epic.get('features', []):
                user_stories = feature.get('user_stories', [])
                if not user_stories or not all('title' in us and us['title'] for us in user_stories):
                    self.logger.error(f"Decomposition Agent did not generate valid user stories for feature '{feature.get('title', 'Untitled')}'. Skipping invalid user stories.")
                    errors.append(f"Feature '{feature.get('title', 'Untitled')}' missing valid user stories.")
        self.logger.info(f"Validation completed: All features checked for user stories, {len(errors)} errors.")

    def _validate_tasks_and_estimates(self):
        """Validate that every user story has tasks and an estimate (story points)."""
        epics = self.workflow_data.get('epics', [])
        errors = []
        for epic in epics:
            for feature in epic.get('features', []):
                for user_story in feature.get('user_stories', []):
                    tasks = user_story.get('tasks', [])
                    if not tasks or not all('title' in t and t['title'] for t in tasks):
                        self.logger.error(f"Developer Agent did not generate valid tasks for user story '{user_story.get('title', 'Untitled')}'. Skipping this user story.")
                        errors.append(f"User story '{user_story.get('title', 'Untitled')}' missing valid tasks.")
                        continue
                    if 'story_points' not in user_story or user_story['story_points'] is None:
                        self.logger.error(f"Developer Agent did not estimate story points for user story '{user_story.get('title', 'Untitled')}'. Skipping this user story.")
                        errors.append(f"User story '{user_story.get('title', 'Untitled')}' missing story points.")
                        continue
        if errors:
            self.logger.warning(f"Validation completed with {len(errors)} user story errors.")
        else:
            self.logger.info("Validation passed: All user stories have tasks and estimates.")

    def _validate_test_cases_and_plans(self):
        """Validate that every user story has test cases and every feature has a test plan structure."""
        epics = self.workflow_data.get('epics', [])
        errors = []
        for epic in epics:
            for feature in epic.get('features', []):
                if 'test_plan_structure' not in feature or not feature['test_plan_structure']:
                    self.logger.error(f"QA Tester Agent did not generate a test plan for feature '{feature.get('title', 'Untitled')}'. Skipping invalid test plan.")
                    errors.append(f"Feature '{feature.get('title', 'Untitled')}' missing test plan structure.")
                for user_story in feature.get('user_stories', []):
                    test_cases = user_story.get('test_cases', [])
                    if not test_cases or not all('title' in tc and tc['title'] for tc in test_cases):
                        self.logger.error(f"QA Tester Agent did not generate valid test cases for user story '{user_story.get('title', 'Untitled')}'. Skipping this user story.")
                        errors.append(f"User story '{user_story.get('title', 'Untitled')}' missing valid test cases.")
        if errors:
            self.logger.warning(f"Validation completed with {len(errors)} test case errors.")
        else:
            self.logger.info("Validation passed: All user stories have test cases and all features have test plans.")

    def _get_sweeper_agent(self):
        if not self.sweeper_agent:
            # Use AzureDevOpsIntegrator if available, else pass None
            ado_client = getattr(self, 'azure_integrator', None)
            # Pass supervisor callback so sweeper can report discrepancies back to supervisor
            self.sweeper_agent = BacklogSweeperAgent(
                ado_client=ado_client, 
                config=self.config.settings,
                supervisor_callback=self.receive_sweeper_report
            )
        return self.sweeper_agent

    def _sweeper_validate_and_get_incomplete(self, stage: str) -> list:
        """Invoke the Backlog Sweeper agent and return a list of incomplete work items for the given stage."""
        sweeper = self._get_sweeper_agent()
        epics = self.workflow_data.get('epics', [])
        if stage == 'epic_strategist':
            return sweeper.validate_epics(epics)
        elif stage == 'feature_decomposer_agent':
            return sweeper.validate_epic_feature_relationships(epics)
        elif stage == 'user_story_decomposer_agent':
            return sweeper.validate_feature_user_story_relationships(epics)
        elif stage == 'decomposition_agent':
            # Backward compatibility - validate both epic-feature and feature-user story relationships
            return sweeper.validate_epic_feature_relationships(epics) + sweeper.validate_feature_user_story_relationships(epics)
        elif stage == 'user_story_decomposer':
            return sweeper.validate_feature_user_story_relationships(epics)
        elif stage == 'developer_agent':
            return sweeper.validate_user_story_tasks(epics)
        elif stage == 'qa_tester_agent':
            return sweeper.validate_test_artifacts(epics)
        else:
            return []

    def execute_workflow(self, 
                        product_vision: str,
                        stages: List[str] = None,
                        human_review: bool = False,
                        save_outputs: bool = True,
                        integrate_azure: bool = False,
                        progress_callback: callable = None) -> Dict[str, Any]:
        """
        Execute the complete workflow or specific stages.
        
        Args:
            product_vision: The product vision to transform
            stages: List of stages to execute (default: all)
            human_review: Whether to pause for human review between stages
            save_outputs: Whether to save intermediate outputs
            integrate_azure: Whether to create Azure DevOps work items
            progress_callback: Optional callback function to report progress (stage_index, total_stages, stage_name)
            
        Returns:
            Complete workflow results including all generated artifacts
        """
        
        self.execution_metadata['start_time'] = datetime.now()
        self.logger.info("Starting workflow execution")
        
        try:
            # Initialize workflow data
            self.workflow_data = {
                'product_vision': product_vision,
                'epics': [],
                'metadata': {
                    'project_context': self.project_context.get_context(),
                    'execution_config': {
                        'stages': stages or self._get_default_stages(),
                        'human_review': human_review,
                        'save_outputs': save_outputs,
                        'integrate_azure': integrate_azure
                    }
                }
            }
            # Execute stages in sequence
            stages_to_run = stages or self._get_default_stages()
            total_stages = len(stages_to_run)
            self.sweeper_retry_tracker = {}
            
            for stage_index, stage in enumerate(stages_to_run):
                self.logger.info(f"Executing stage: {stage} ({stage_index + 1}/{total_stages})")
                
                # Report progress at start of stage
                if progress_callback:
                    progress_callback(stage_index, total_stages, stage, "starting")
                
                self.sweeper_retry_tracker[stage] = {}
                max_retries = 5
                completed = False
                while not completed:
                    try:
                        # Run the agent stage as before
                        if stage == 'epic_strategist':
                            self._execute_epic_generation()
                            self._validate_epics()
                        elif stage == 'feature_decomposer_agent':
                            self._execute_feature_decomposition()
                            self._validate_features()
                        elif stage == 'user_story_decomposer_agent':
                            self._execute_user_story_decomposition()
                            self._validate_user_stories()
                        elif stage == 'decomposition_agent':
                            # Backward compatibility - run both feature and user story decomposition
                            self._execute_feature_decomposition()
                            self._validate_features()
                            self._execute_user_story_decomposition()
                            self._validate_user_stories()
                        elif stage == 'user_story_decomposer':
                            self._execute_user_story_decomposition()
                            self._validate_user_stories()
                        elif stage == 'developer_agent':
                            self._execute_task_generation()
                            self._validate_tasks_and_estimates()
                        elif stage == 'qa_tester_agent':
                            self._execute_qa_generation()
                            self._validate_test_cases_and_plans()
                        else:
                            self.logger.warning(f"Unknown stage: {stage}")
                            break
                        # After agent stage, run sweeper to validate outputs
                        incomplete_items = self._sweeper_validate_and_get_incomplete(stage)
                        if not incomplete_items:
                            completed = True
                            # Report progress at completion of stage
                            if progress_callback:
                                progress_callback(stage_index, total_stages, stage, "completed")
                            break
                        # Targeted retry logic
                        still_incomplete = []
                        for item in incomplete_items:
                            item_id = item.get('work_item_id')
                            if item_id is None:
                                continue
                            retry_count = self.sweeper_retry_tracker[stage].get(item_id, 0)
                            if retry_count < max_retries:
                                self.logger.info(f"Retrying incomplete item {item_id} for stage {stage} (attempt {retry_count+1}/{max_retries})")
                                # Here, you would call the appropriate agent's remediation method if implemented
                                self.sweeper_retry_tracker[stage][item_id] = retry_count + 1
                            else:
                                self.logger.error(f"Item {item_id} in stage {stage} failed after {max_retries} attempts. Logging and notifying.")
                                self.notifier.send_error_notification(
                                    Exception(f"Item {item_id} in stage {stage} incomplete after {max_retries} retries: {item.get('description','')}"),
                                    self.execution_metadata
                                )
                                # Log persistent failure
                                self.execution_metadata['errors'].append(f"Item {item_id} in {stage} failed after {max_retries} retries: {item.get('description','')}")
                            # Only retry items that have not hit max_retries
                            if self.sweeper_retry_tracker[stage].get(item_id, 0) < max_retries:
                                still_incomplete.append(item)
                        if not still_incomplete:
                            completed = True
                            # Report progress at completion of stage
                            if progress_callback:
                                progress_callback(stage_index, total_stages, stage, "completed")
                        else:
                            self.logger.info(f"{len(still_incomplete)} items remain incomplete after this retry round in stage {stage}.")
                    except Exception as e:
                        self.logger.error(f"{stage} failed with exception: {e}")
                        self.execution_metadata['errors'].append(f"{stage} failed: {e}")
                        self._send_error_notifications(e)
                        completed = True  # Move to next stage even on error
                        # Report progress at completion of stage (even if failed)
                        if progress_callback:
                            progress_callback(stage_index, total_stages, stage, "failed")
            # Final processing
            self._finalize_workflow_data()
            # Azure DevOps integration
            if integrate_azure:
                self._integrate_with_azure_devops()
            # Send notifications
            self._send_completion_notifications()
            # Save final output
            if save_outputs:
                self._save_final_output()
            self.execution_metadata['end_time'] = datetime.now()
            self.logger.info("Workflow execution completed successfully")
            
            return self.workflow_data
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            self.execution_metadata['errors'].append(str(e))
            self.execution_metadata['end_time'] = datetime.now()
            
            # Send error notifications
            self._send_error_notifications(e)
            raise
    
    def _execute_epic_generation(self):
        """Execute epic generation stage."""
        self.logger.info("Generating epics from product vision")
        
        try:
            agent = self.agents['epic_strategist']
            context = self.project_context.get_context('epic_strategist')
            
            # Get limits from configuration (null = unlimited)
            max_epics = self.config.settings.get('workflow', {}).get('limits', {}).get('max_epics')
            epics = agent.generate_epics(self.workflow_data['product_vision'], context, max_epics=max_epics)
            
            if not epics:
                raise ValueError("Epic generation failed - no epics returned")
            
            self.workflow_data['epics'] = epics
            if max_epics:
                self.logger.info(f"Generated {len(epics)} epics (limited to {max_epics} for testing)")
            else:
                self.logger.info(f"Generated {len(epics)} epics")
            
        except Exception as e:
            self.logger.error(f"Epic generation failed: {e}")
            raise
    
    def _execute_feature_decomposition(self):
        """Execute feature decomposition stage."""
        self.logger.info("Decomposing epics into features")
        
        try:
            agent = self.agents['feature_decomposer_agent']
            context = self.project_context.get_context('feature_decomposer_agent')
            
            # Get limits from configuration (null = unlimited)
            max_features = self.config.settings.get('workflow', {}).get('limits', {}).get('max_features_per_epic')
            
            for epic in self.workflow_data['epics']:
                self.logger.info(f"Decomposing epic: {epic.get('title', 'Untitled')}")
                
                features = agent.decompose_epic(epic, context, max_features=max_features)
                epic['features'] = features
                
                if max_features:
                    self.logger.info(f"Generated {len(features)} features for epic (limited to {max_features} for testing)")
                else:
                    self.logger.info(f"Generated {len(features)} features for epic")
                
        except Exception as e:
            self.logger.error(f"Feature decomposition failed: {e}")
            raise
    
    def _execute_user_story_decomposition(self):
        """Execute user story decomposition stage."""
        self.logger.info("Decomposing features into user stories")
        
        try:
            agent = self.agents['user_story_decomposer_agent']
            context = self.project_context.get_context('user_story_decomposer_agent')
            
            for epic in self.workflow_data['epics']:
                for feature in epic.get('features', []):
                    self.logger.info(f"Decomposing feature to user stories: {feature.get('title', 'Untitled')}")
                    
                    user_stories = agent.decompose_feature_to_user_stories(feature, context)
                    feature['user_stories'] = user_stories
                    
                    self.logger.info(f"Generated {len(user_stories)} user stories for feature")
                    
        except Exception as e:
            self.logger.error(f"User story decomposition failed: {e}")
            raise
    
    def _execute_task_generation(self):
        """Execute developer task generation stage."""
        self.logger.info("Generating developer tasks")
        
        try:
            agent = self.agents['developer_agent']
            context = self.project_context.get_context('developer_agent')
            
            for epic in self.workflow_data['epics']:
                for feature in epic.get('features', []):
                    user_stories = feature.get('user_stories', [])
                    if user_stories:
                        # With updated prompt, user_stories are now structured objects
                        processed_stories = []
                        for i, story_item in enumerate(user_stories):
                            if isinstance(story_item, dict):
                                # New structured format - already has all needed fields
                                story_dict = {
                                    'title': story_item.get('title', f"User Story {i+1} for {feature.get('title', 'Feature')}"),
                                    'user_story': story_item.get('description', ''),
                                    'description': story_item.get('description', ''),
                                    'acceptance_criteria': story_item.get('acceptance_criteria', []),
                                    'priority': story_item.get('priority', 'Medium'),
                                    'story_points': story_item.get('story_points', 3),
                                    'tags': story_item.get('tags', [])
                                }
                                processed_stories.append(story_dict)
                            elif isinstance(story_item, str):
                                # Legacy string format - convert to dict format for task generation
                                story_dict = {
                                    'title': f"User Story {i+1} for {feature.get('title', 'Feature')}",
                                    'user_story': story_item,
                                    'description': f"From feature: {feature.get('title', 'Unknown Feature')}",
                                    'acceptance_criteria': [],  # User stories should define their own acceptance criteria
                                    'priority': feature.get('priority', 'Medium'),
                                    'story_points': feature.get('estimated_story_points', 5)
                                }
                                processed_stories.append(story_dict)
                        
                        feature['user_stories'] = processed_stories
                        
                        for user_story in processed_stories:
                            self.logger.info(f"Generating tasks for user story: {user_story.get('title', 'Untitled')}")
                            
                            tasks = agent.generate_tasks(user_story, context)
                            user_story['tasks'] = tasks
                            
                            self.logger.info(f"Generated {len(tasks)} tasks for user story")
                    
        except Exception as e:
            self.logger.error(f"Task generation failed: {e}")
            raise
    
    def _execute_qa_generation(self):
        """Execute QA test case generation stage."""
        self.logger.info("Generating QA test cases and validation")
        
        try:
            agent = self.agents['qa_tester_agent']
            context = self.project_context.get_context('qa_tester_agent')
            
            for epic in self.workflow_data['epics']:
                for feature in epic.get('features', []):
                    self.logger.info(f"Generating QA artifacts for feature: {feature.get('title', 'Untitled')}")
                    
                    # Process each user story within the feature for QA activities
                    for user_story in feature.get('user_stories', []):
                        self.logger.info(f"Generating QA artifacts for user story: {user_story.get('title', 'Untitled')}")
                        
                        # Generate user story test cases (replaces feature-level test generation)
                        test_cases = agent.generate_user_story_test_cases(user_story, context)
                        user_story['test_cases'] = test_cases
                        
                        # Validate user story testability (replaces feature-level acceptance criteria validation)
                        validation = agent.validate_user_story_testability(user_story, context)
                        user_story['qa_validation'] = validation
                        
                        self.logger.info(f"Generated QA artifacts for user story: {len(test_cases)} test cases, testability score: {validation.get('testability_score', 'N/A')}")
                    
                    # Create test plan structure for the feature (organizational level)
                    test_plan_structure = agent.create_test_plan_structure(feature, context)
                    feature['test_plan_structure'] = test_plan_structure
                    
                    self.logger.info(f"Created test plan structure for feature: {feature.get('title', 'Untitled')}")
                    
        except Exception as e:
            self.logger.error(f"QA generation failed: {e}")
            raise
    
    def _human_review_checkpoint(self, stage: str):
        """Pause for human review and approval."""
        self.logger.info(f"Human review checkpoint for stage: {stage}")
        
        # Display current results
        print(f"\\n{'='*60}")
        print(f"HUMAN REVIEW - {stage.upper()}")
        print(f"{'='*60}")
        
        if stage == 'epic_strategist':
            epics = self.workflow_data.get('epics', [])
            print(f"Generated {len(epics)} epics:")
            for i, epic in enumerate(epics, 1):
                print(f"{i}. {epic.get('title', 'Untitled Epic')}")
                print(f"   Priority: {epic.get('priority', 'N/A')}")
                print(f"   Complexity: {epic.get('estimated_complexity', 'N/A')}")
                print()
        
        # Get user approval
        while True:
            response = input("Approve and continue? [y/n/view]: ")

            if response == 'y':
                self.logger.info(f"Stage {stage} approved by user")
                break
            elif response == 'n':
                self.logger.info(f"Stage {stage} rejected by user")
                raise ValueError(f"Workflow stopped by user at stage: {stage}")
            elif response == 'view':
                # Show detailed view
                self._show_detailed_view(stage)
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'view' for details")
    
    def _show_detailed_view(self, stage: str):
        """Show detailed view of current stage results."""
        if stage == 'epic_strategist':
            for epic in self.workflow_data.get('epics', []):
                print(f"\\nEpic: {epic.get('title', 'Untitled')}")
                print(f"Description: {epic.get('description', 'No description')}")
                print(f"Business Value: {epic.get('business_value', 'Not specified')}")
                print(f"Dependencies: {epic.get('dependencies', [])}")
        # Add more detailed views for other stages as needed
    
    def _integrate_with_azure_devops(self):
        """Integrate generated backlog with Azure DevOps with pre-integration validation."""
        self.logger.info("Preparing for Azure DevOps integration")
        
        # Check if Azure integration is enabled
        if self.azure_integrator is None:
            self.logger.info("🚫 Azure DevOps integration disabled (no Azure config provided)")
            self.logger.info("✅ Content generation completed - skipping Azure upload")
            
            # Store integration results as skipped
            self.workflow_data['azure_integration'] = {
                'status': 'skipped',
                'reason': 'No Azure DevOps configuration provided',
                'timestamp': datetime.now().isoformat()
            }
            return
        
        try:
            # Perform pre-integration quality check using backlog sweeper
            self.logger.info("🔍 Running pre-integration validation...")
            validation_report = self.backlog_sweeper.validate_pre_integration(self.workflow_data)
            
            # Store validation results
            self.workflow_data['pre_integration_validation'] = validation_report
            
            # Check validation status
            if validation_report['status'] == 'failed':
                critical_count = validation_report['summary']['critical_issues']
                self.logger.error(f"❌ Pre-integration validation failed with {critical_count} critical issues")
                
                # Store failed integration attempt
                self.workflow_data['azure_integration'] = {
                    'status': 'validation_failed',
                    'validation_issues': critical_count,
                    'timestamp': datetime.now().isoformat(),
                    'error': f"Pre-integration validation failed with {critical_count} critical issues"
                }
                
                # Log critical issues for debugging
                for issue in validation_report['issues']:
                    if issue.get('severity') == 'critical':
                        self.logger.error(f"CRITICAL: {issue.get('description')} - {issue.get('suggested_action')}")
                
                raise ValueError(f"Pre-integration validation failed with {critical_count} critical issues. Check validation report for details.")
            
            elif validation_report['status'] == 'warning':
                warning_count = validation_report['summary']['warning_issues']
                self.logger.warning(f"⚠️ Pre-integration validation passed with {warning_count} warnings")
                
                # Log warnings but continue
                for issue in validation_report['issues']:
                    if issue.get('severity') == 'warning':
                        self.logger.warning(f"WARNING: {issue.get('description')}")
            
            else:
                self.logger.info("✅ Pre-integration validation passed successfully")
            
            # Proceed with ADO integration
            self.logger.info("🚀 Starting Azure DevOps work item creation...")
            results = self.azure_integrator.create_work_items(self.workflow_data)
            
            # Store integration results
            self.workflow_data['azure_integration'] = {
                'status': 'success',
                'work_items_created': results,
                'timestamp': datetime.now().isoformat()
            }
            self.logger.info(f"Successfully created {len(results)} work items in Azure DevOps")

            # --- BEGIN WORKFLOW CHECKS ---
            # Check for missing artifacts
            missing = []
            epic_count = len(self.workflow_data.get('epics', []))
            feature_count = sum(len(e.get('features', [])) for e in self.workflow_data.get('epics', []))
            user_story_count = sum(len(f.get('user_stories', [])) for e in self.workflow_data.get('epics', []) for f in e.get('features', []))
            task_count = sum(len(s.get('tasks', [])) for e in self.workflow_data.get('epics', []) for f in e.get('features', []) for s in f.get('user_stories', []))
            test_case_count = sum(len(s.get('test_cases', [])) for e in self.workflow_data.get('epics', []) for f in e.get('features', []) for s in f.get('user_stories', []))
            test_plan_count = sum(1 for e in self.workflow_data.get('epics', []) for f in e.get('features', []) if f.get('test_cases') or any(s.get('test_cases') for s in f.get('user_stories', [])))

            if user_story_count == 0:
                missing.append('user stories')
            if task_count == 0:
                missing.append('tasks')
            if test_case_count == 0:
                missing.append('test cases')
            if test_plan_count == 0:
                missing.append('test plans')

            if missing:
                msg = f"WARNING: The following artifact types were not created in this run: {', '.join(missing)}. Please check agent outputs and integration logic."
                self.logger.warning(msg)
                self.workflow_data['azure_integration']['missing_artifacts'] = missing
                self.workflow_data['azure_integration']['warning'] = msg
            # --- END WORKFLOW CHECKS ---
            
        except Exception as e:
            self.logger.error(f"Azure DevOps integration failed: {e}")
            
            self.workflow_data['azure_integration'] = {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            raise
    
    def _send_completion_notifications(self):
        """Send workflow completion notifications."""
        try:
            # Calculate summary statistics
            stats = self._calculate_workflow_stats()
            
            # Send notifications
            self.notifier.send_completion_notification(self.workflow_data, stats)
            
            self.logger.info("Completion notifications sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send completion notifications: {e}")
    
    def _send_error_notifications(self, error: Exception):
        """Send error notifications."""
        try:
            self.notifier.send_error_notification(error, self.execution_metadata)
            self.logger.info("Error notifications sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send error notifications: {e}")
    
    def _calculate_workflow_stats(self) -> Dict[str, Any]:
        """Calculate workflow execution statistics."""
        epics_count = len(self.workflow_data.get('epics', []))
        features_count = sum(len(epic.get('features', [])) for epic in self.workflow_data.get('epics', []))
        tasks_count = sum(
            len(feature.get('tasks', []))
            for epic in self.workflow_data.get('epics', [])
            for feature in epic.get('features', [])
        )
        
        execution_time = None
        if self.execution_metadata['start_time'] and self.execution_metadata['end_time']:
            execution_time = (self.execution_metadata['end_time'] - self.execution_metadata['start_time']).total_seconds()
        
        return {
            'epics_generated': epics_count,
            'features_generated': features_count,
            'tasks_generated': tasks_count,
            'execution_time_seconds': execution_time,
            'stages_completed': len(self.execution_metadata['stages_completed']),
            'errors_encountered': len(self.execution_metadata['errors'])
        }
    
    def _finalize_workflow_data(self):
        """Add final metadata and processing to workflow data."""
        self.workflow_data['metadata'].update({
            'execution_summary': self._calculate_workflow_stats(),
            'completion_timestamp': datetime.now().isoformat(),
            'stages_executed': self.execution_metadata['stages_completed']
        })
    
    def _save_intermediate_output(self, stage: str):
        """Save intermediate output after each stage."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intermediate_{stage}_{timestamp}"
        
        self._save_output(self.workflow_data, filename)
        self.execution_metadata['outputs_generated'].append(f"{filename}.json")
    
    def _save_final_output(self):
        """Save final workflow output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backlog_{timestamp}"
        
        self._save_output(self.workflow_data, filename)
        self.execution_metadata['outputs_generated'].append(f"{filename}.json")
    
    def _save_output(self, data: Dict[str, Any], filename: str):
        """Save data to JSON and YAML files."""
        os.makedirs("output", exist_ok=True)
        
        # Save JSON
        json_path = f"output/{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save YAML
        yaml_path = f"output/{filename}.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        
        self.logger.info(f"Output saved: {json_path}, {yaml_path}")
    
    def _get_default_stages(self) -> List[str]:
        """Get default workflow stages from configuration."""
        return self.config.settings.get('workflow', {}).get('sequence', [
            'epic_strategist',
            'feature_decomposer_agent',
            'user_story_decomposer_agent',
            'developer_agent',
            'qa_tester_agent'
        ])
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status and metadata."""
        return {
            'metadata': self.execution_metadata,
            'workflow_data': self.workflow_data,
            'project_context': self.project_context.get_context_summary()
        }
    
    def resume_workflow_from_stage(self, stage: str, input_data: Dict[str, Any]):
        """Resume workflow execution from a specific stage with existing data."""
        self.logger.info(f"Resuming workflow from stage: {stage}")
        
        # Load existing data
        self.workflow_data = input_data
        
        # Get remaining stages
        all_stages = self._get_default_stages()
        if stage not in all_stages:
            raise ValueError(f"Unknown stage: {stage}")
        
        stage_index = all_stages.index(stage)
        remaining_stages = all_stages[stage_index:]
        
        # Execute remaining stages
        return self.execute_workflow(
            product_vision=input_data.get('product_vision', ''),
            stages=remaining_stages
        )

    def receive_sweeper_report(self, report):
        """
        Process backlog sweeper reports and route discrepancies to appropriate agents.
        
        Args:
            report: Structured report from BacklogSweeperAgent containing:
                - discrepancies_by_priority: High/medium/low priority issues
                - agent_assignments: Discrepancies grouped by suggested agent
                - dashboard_requirements: Dashboard and reporting needs
                - recommended_actions: Actionable recommendations
        """
        self.logger.info("Received backlog sweeper report")
        
        try:
            # Log report summary
            summary = report.get('summary', {})
            self.logger.info(f"Sweep Summary: {summary.get('total_discrepancies', 0)} discrepancies found")
            self.logger.info(f"Priority breakdown - High: {summary.get('high_priority_count', 0)}, "
                           f"Medium: {summary.get('medium_priority_count', 0)}, "
                           f"Low: {summary.get('low_priority_count', 0)}")
            
            # Process agent assignments
            agent_assignments = report.get('agent_assignments', {})
            
            for agent_name, discrepancies in agent_assignments.items():
                if discrepancies:
                    self.logger.info(f"Routing {len(discrepancies)} discrepancies to {agent_name}")
                    self._route_discrepancies_to_agent(agent_name, discrepancies)
            
            # Handle dashboard requirements
            dashboard_requirements = report.get('dashboard_requirements', [])
            if dashboard_requirements:
                self.logger.info(f"Processing {len(dashboard_requirements)} dashboard requirements")
                self._handle_dashboard_requirements(dashboard_requirements)
            
            # Process recommendations
            recommendations = report.get('recommended_actions', [])
            if recommendations:
                self.logger.info("Action Recommendations:")
                for rec in recommendations:
                    self.logger.info(f"  - {rec}")
            
            # Send notifications if critical issues found
            high_priority_count = summary.get('high_priority_count', 0)
            if high_priority_count > 0:
                self._send_critical_issue_notification(report)
                
        except Exception as e:
            self.logger.error(f"Error processing sweeper report: {e}")
            import json
            self.logger.debug(f"Report content: {json.dumps(report, indent=2)}")
    
    def _route_discrepancies_to_agent(self, agent_name: str, discrepancies: List[Dict[str, Any]]):
        """Route specific discrepancies to the appropriate agent for remediation."""
        
        # Group discrepancies by work item for efficient processing
        work_item_groups = {}
        for discrepancy in discrepancies:
            wi_id = discrepancy.get('work_item_id')
            if wi_id not in work_item_groups:
                work_item_groups[wi_id] = []
            work_item_groups[wi_id].append(discrepancy)
        
        self.logger.info(f"Routing to {agent_name}: {len(discrepancies)} discrepancies across {len(work_item_groups)} work items")
        
        # Route to appropriate agent
        if agent_name == 'epic_strategist' and hasattr(self, 'agents'):
            self._handle_epic_strategist_discrepancies(work_item_groups)
        elif agent_name == 'feature_decomposer_agent' and hasattr(self, 'agents'):
            self._handle_feature_decomposer_discrepancies(work_item_groups)
        elif agent_name == 'user_story_decomposer_agent' and hasattr(self, 'agents'):
            self._handle_user_story_decomposer_discrepancies(work_item_groups)
        elif agent_name == 'decomposition_agent' and hasattr(self, 'agents'):
            # Backward compatibility - handle as feature decomposer
            self._handle_feature_decomposer_discrepancies(work_item_groups)
        elif agent_name == 'developer_agent' and hasattr(self, 'agents'):
            self._handle_developer_discrepancies(work_item_groups)
        elif agent_name == 'qa_tester_agent' and hasattr(self, 'agents'):
            self._handle_qa_tester_discrepancies(work_item_groups)
        else:
            self.logger.warning(f"Unknown agent '{agent_name}' or agent not available. Logging discrepancies for manual review.")
            for wi_id, wi_discrepancies in work_item_groups.items():
                for disc in wi_discrepancies:
                    self.logger.warning(f"Manual Review Required - Work Item {wi_id}: {disc.get('description', 'No description')}")
    
    def _handle_epic_strategist_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require Epic Strategist intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"Epic Strategist: Reviewing work item {wi_id}")
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # In a full implementation, you would call:
                # self.agents['epic_strategist'].remediate_discrepancy(disc)
    
    def _handle_feature_decomposer_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require Feature Decomposer Agent intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"Feature Decomposer Agent: Reviewing work item {wi_id}")
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # In a full implementation, you would call:
                # self.agents['feature_decomposer_agent'].remediate_discrepancy(disc)
    
    def _handle_user_story_decomposer_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require User Story Decomposer Agent intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"User Story Decomposer Agent: Reviewing work item {wi_id}")
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # In a full implementation, you would call:
                # self.agents['user_story_decomposer_agent'].remediate_discrepancy(disc)
    
    def _handle_decomposition_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require Decomposition Agent intervention (backward compatibility)."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"Decomposition Agent (Legacy): Reviewing work item {wi_id}")
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # Route to appropriate new agent based on discrepancy type
                if disc.get('type') in ['missing_feature_title', 'missing_feature_description', 'invalid_feature_child']:
                    self.logger.info(f"    → Routing to Feature Decomposer Agent")
                    self._handle_feature_decomposer_discrepancies({wi_id: [disc]})
                elif disc.get('type') in ['missing_story_title', 'missing_or_invalid_story_description', 'missing_child_user_story']:
                    self.logger.info(f"    → Routing to User Story Decomposer Agent")
                    self._handle_user_story_decomposer_discrepancies({wi_id: [disc]})
                else:
                    # Default to feature decomposer for unknown types
                    self._handle_feature_decomposer_discrepancies({wi_id: [disc]})
    
    def _handle_developer_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require Developer Agent intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"Developer Agent: Reviewing work item {wi_id}")
            
            # Check for specific discrepancy types that can be auto-remediated
            missing_tasks = [d for d in discrepancies if d.get('type') in ['missing_child_task', 'user_story_missing_tasks']]
            missing_story_points = [d for d in discrepancies if d.get('type') == 'missing_story_points']
            
            # Auto-create missing tasks for user stories
            if missing_tasks and hasattr(self, 'agents'):
                try:
                    self._auto_create_missing_tasks(wi_id, missing_tasks[0])
                except Exception as e:
                    self.logger.error(f"Failed to auto-create tasks for work item {wi_id}: {e}")
            
            # Auto-estimate missing story points
            if missing_story_points and hasattr(self, 'agents'):
                try:
                    self._auto_estimate_story_points(wi_id, missing_story_points[0])
                except Exception as e:
                    self.logger.error(f"Failed to auto-estimate story points for work item {wi_id}: {e}")
            
            # Log other discrepancies for manual review
            other_discrepancies = [d for d in discrepancies if d.get('type') not in ['missing_child_task', 'user_story_missing_tasks', 'missing_story_points']]
            for disc in other_discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")

    def _handle_qa_tester_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require QA Tester Agent intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"QA Tester Agent: Reviewing work item {wi_id}")
            
            # Check for specific discrepancy types that can be auto-remediated
            missing_test_cases = [d for d in discrepancies if d.get('type') in ['missing_child_test_case', 'user_story_missing_test_cases']]
            missing_criteria = [d for d in discrepancies if d.get('type') in ['missing_acceptance_criteria', 'invalid_acceptance_criteria']]
            
            # Auto-create missing test cases for user stories
            if missing_test_cases and hasattr(self, 'agents'):
                try:
                    self._auto_create_missing_test_cases(wi_id, missing_test_cases[0])
                except Exception as e:
                    self.logger.error(f"Failed to auto-create test cases for work item {wi_id}: {e}")
            
            # Auto-enhance missing or invalid acceptance criteria
            if missing_criteria and hasattr(self, 'agents'):
                try:
                    self._auto_enhance_acceptance_criteria(wi_id, missing_criteria[0])
                except Exception as e:
                    self.logger.error(f"Failed to auto-enhance acceptance criteria for work item {wi_id}: {e}")
            
            # Log other discrepancies for manual review
            other_discrepancies = [d for d in discrepancies if d.get('type') not in ['missing_child_test_case', 'missing_acceptance_criteria', 'invalid_acceptance_criteria']]
            for disc in other_discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")

    def _auto_create_missing_tasks(self, user_story_id: int, discrepancy: Dict[str, Any]):
        """Automatically create missing tasks for a user story."""
        self.logger.info(f"Auto-creating missing tasks for User Story {user_story_id}")
        
        # Get user story details
        user_story_details = self.azure_integrator.get_work_item_details([user_story_id])
        if not user_story_details:
            self.logger.error(f"Could not retrieve details for User Story {user_story_id}")
            return
        
        user_story = user_story_details[0]
        story_fields = user_story.get('fields', {})
        
        # Prepare feature data for developer agent
        feature_data = {
            'title': story_fields.get('System.Title', 'Unknown User Story'),
            'description': story_fields.get('System.Description', ''),
            'acceptance_criteria': self._extract_acceptance_criteria(story_fields),
            'priority': story_fields.get('Microsoft.VSTS.Common.Priority', 2),
            'estimated_story_points': story_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0)
        }
        
        # Generate tasks using developer agent
        context = self.project_context.get_context()
        tasks = self.agents['developer_agent'].generate_tasks(feature_data, context)
        
        if tasks:
            self.logger.info(f"Generated {len(tasks)} tasks for User Story {user_story_id}")
            
            # Create tasks in Azure DevOps with proper parent link
            for task in tasks:
                try:
                    task_item = self.azure_integrator._create_task(task, user_story_id)
                    self.logger.info(f"Created Task {task_item['id']}: {task.get('title', 'Untitled')}")
                except Exception as e:
                    self.logger.error(f"Failed to create task '{task.get('title', 'Unknown')}': {e}")
        else:
            self.logger.warning(f"No tasks generated for User Story {user_story_id}")

    def _auto_create_missing_test_cases(self, user_story_id: int, discrepancy: Dict[str, Any]):
        """Automatically create missing test cases for a user story."""
        self.logger.info(f"Auto-creating missing test cases for User Story {user_story_id}")
        
        # Get user story details
        user_story_details = self.azure_integrator.get_work_item_details([user_story_id])
        if not user_story_details:
            self.logger.error(f"Could not retrieve details for User Story {user_story_id}")
            return
        
        user_story = user_story_details[0]
        story_fields = user_story.get('fields', {})
        
        # Prepare user story data for test case generation
        user_story_data = {
            'id': user_story_id,
            'title': story_fields.get('System.Title', 'Unknown User Story'),
            'description': story_fields.get('System.Description', ''),
            'acceptance_criteria': self._extract_acceptance_criteria(story_fields),
            'priority': story_fields.get('Microsoft.VSTS.Common.Priority', 2),
            'story_points': story_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0)
        }
        
        # Generate test cases using QA tester agent
        context = self.project_context.get_context()
        test_cases = self.agents['qa_tester_agent'].generate_user_story_test_cases(user_story_data, context)
        
        if test_cases:
            self.logger.info(f"Generated {len(test_cases)} test cases for User Story {user_story_id}")
            
            # Create test cases in Azure DevOps with proper parent link
            for test_case in test_cases:
                try:
                    test_item = self.azure_integrator._create_test_case(test_case, user_story_id)
                    self.logger.info(f"Created Test Case {test_item['id']}: {test_case.get('title', 'Untitled')}")
                except Exception as e:
                    self.logger.error(f"Failed to create test case '{test_case.get('title', 'Unknown')}': {e}")
        else:
            self.logger.warning(f"No test cases generated for User Story {user_story_id}")

    def _auto_estimate_story_points(self, user_story_id: int, discrepancy: Dict[str, Any]):
        """Automatically estimate story points for a user story."""
        self.logger.info(f"Auto-estimating story points for User Story {user_story_id}")
        
        # Get user story details
        user_story_details = self.azure_integrator.get_work_item_details([user_story_id])
        if not user_story_details:
            self.logger.error(f"Could not retrieve details for User Story {user_story_id}")
            return
        
        user_story = user_story_details[0]
        story_fields = user_story.get('fields', {})
        
        # Prepare user story data for estimation
        user_story_data = {
            'title': story_fields.get('System.Title', 'Unknown User Story'),
            'description': story_fields.get('System.Description', ''),
            'acceptance_criteria': self._extract_acceptance_criteria(story_fields)
        }
        
        # Estimate using developer agent
        context = self.project_context.get_context()
        estimated_points = self.agents['developer_agent'].estimate_story_points(user_story_data, context)
        
        if estimated_points:
            try:
                # Update the work item with estimated story points
                fields = {
                    '/fields/Microsoft.VSTS.Scheduling.StoryPoints': estimated_points
                }
                self.azure_integrator._update_work_item(user_story_id, fields)
                self.logger.info(f"Updated User Story {user_story_id} with {estimated_points} story points")
            except Exception as e:
                self.logger.error(f"Failed to update story points for User Story {user_story_id}: {e}")
        else:
            self.logger.warning(f"Could not estimate story points for User Story {user_story_id}")

    def _auto_enhance_acceptance_criteria(self, user_story_id: int, discrepancy: Dict[str, Any]):
        """Automatically enhance acceptance criteria for a user story."""
        self.logger.info(f"Auto-enhancing acceptance criteria for User Story {user_story_id}")
        
        # Get user story details
        user_story_details = self.azure_integrator.get_work_item_details([user_story_id])
        if not user_story_details:
            self.logger.error(f"Could not retrieve details for User Story {user_story_id}")
            return
        
        user_story = user_story_details[0]
        story_fields = user_story.get('fields', {})
        
        # Prepare user story data for enhancement
        user_story_data = {
            'title': story_fields.get('System.Title', 'Unknown User Story'),
            'description': story_fields.get('System.Description', ''),
            'acceptance_criteria': self._extract_acceptance_criteria(story_fields),
            'priority': story_fields.get('Microsoft.VSTS.Common.Priority', 2)
        }
        
        # Enhance acceptance criteria using QA tester agent
        context = self.project_context.get_context()
        enhanced_criteria = self.agents['qa_tester_agent'].enhance_acceptance_criteria(user_story_data, context)
        
        if enhanced_criteria:
            try:
                # Format criteria for Azure DevOps
                criteria_text = self._format_acceptance_criteria(enhanced_criteria)
                
                # Update the work item with enhanced acceptance criteria
                fields = {
                    '/fields/Microsoft.VSTS.Common.AcceptanceCriteria': criteria_text
                }
                self.azure_integrator._update_work_item(user_story_id, fields)
                self.logger.info(f"Updated User Story {user_story_id} with enhanced acceptance criteria ({len(enhanced_criteria)} criteria)")
            except Exception as e:
                self.logger.error(f"Failed to update acceptance criteria for User Story {user_story_id}: {e}")
        else:
            self.logger.warning(f"Could not enhance acceptance criteria for User Story {user_story_id}")

    def _extract_acceptance_criteria(self, story_fields: Dict[str, Any]) -> List[str]:
        """Extract acceptance criteria from work item fields."""
        criteria_text = story_fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', '')
        if not criteria_text:
            return []
        
        # Split by lines and clean up
        criteria_lines = [line.strip() for line in criteria_text.split('\n') if line.strip()]
        criteria_items = []
        
        for line in criteria_lines:
            # Handle various bullet formats
            cleaned = re.sub(r'^[-*â€¢]\s*', '', line)
            cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
            if cleaned:
                criteria_items.append(cleaned)
        
        return criteria_items

    def _format_acceptance_criteria(self, criteria: List[str]) -> str:
        """Format acceptance criteria for Azure DevOps."""
        if not criteria:
            return ""
        
        # Format as numbered list
        formatted_lines = []
        for i, criterion in enumerate(criteria, 1):
            formatted_lines.append(f"{i}. {criterion}")
        
        return '\n'.join(formatted_lines)

    def create_complete_user_story_with_children(self, user_story_data: Dict[str, Any], parent_feature_id: int = None) -> Dict[str, Any]:
        """
        Create a complete user story with all required child work items to ensure compliance.
        This method coordinates between agents to create a fully compliant work item hierarchy.
        
        Args:
            user_story_data: User story data with title, description, acceptance criteria, etc.
            parent_feature_id: Optional parent feature ID for linking
            
        Returns:
            Dictionary containing the created user story and all child work items
        """
        self.logger.info(f"Creating complete user story with children: {user_story_data.get('title', 'Unknown')}")
        
        try:
            # Step 1: Validate and enhance user story using quality validator
            if hasattr(self.agents['decomposition_agent'], 'quality_validator'):
                validator = self.agents['decomposition_agent'].quality_validator
                enhanced_story = validator.generate_quality_compliant_user_story(
                    title=user_story_data.get('title', ''),
                    user_type=user_story_data.get('user_type', 'user'),
                    goal=user_story_data.get('goal', user_story_data.get('title', '')),
                    benefit=user_story_data.get('benefit', 'achieve objectives'),
                    acceptance_criteria=user_story_data.get('acceptance_criteria', []),
                    story_points=user_story_data.get('story_points')
                )
                user_story_data.update(enhanced_story)
            
            # Step 2: Create the user story in Azure DevOps
            if hasattr(self, 'azure_integrator'):
                user_story_item = self.azure_integrator._create_user_story(user_story_data, parent_feature_id)
                user_story_id = user_story_item['id']
                self.logger.info(f"Created User Story {user_story_id}: {user_story_data.get('title', '')}")
            else:
                # For testing, simulate work item creation
                user_story_id = 12345  # Mock ID
                user_story_item = {
                    'id': user_story_id,
                    'fields': {
                        'System.Title': user_story_data.get('title', ''),
                        'System.WorkItemType': 'User Story'
                    }
                }
                self.logger.info(f"Mock created User Story {user_story_id}: {user_story_data.get('title', '')}")
            
            # Step 3: Generate and create child tasks using Developer Agent
            tasks_created = []
            if hasattr(self.agents, 'developer_agent') and 'developer_agent' in self.agents:
                context = self.project_context.get_context() if hasattr(self, 'project_context') else {}
                
                # Prepare feature data for task generation
                feature_data = {
                    'title': user_story_data.get('title', ''),
                    'description': user_story_data.get('description', ''),
                    'acceptance_criteria': user_story_data.get('acceptance_criteria', []),
                    'priority': user_story_data.get('priority', 'Medium'),
                    'estimated_story_points': user_story_data.get('story_points', 3)
                }
                
                tasks = self.agents['developer_agent'].generate_tasks(feature_data, context)
                
                for task in tasks:
                    if hasattr(self, 'azure_integrator'):
                        task_item = self.azure_integrator._create_task(task, user_story_id)
                        tasks_created.append(task_item)
                        self.logger.info(f"Created Task {task_item['id']}: {task.get('title', '')}")
                    else:
                        # For testing, simulate task creation
                        task_item = {
                            'id': len(tasks_created) + 20000,  # Mock ID
                            'fields': {
                                'System.Title': task.get('title', ''),
                                'System.WorkItemType': 'Task'
                            }
                        }
                        tasks_created.append(task_item)
                        self.logger.info(f"Mock created Task {task_item['id']}: {task.get('title', '')}")
            
            # Step 4: Generate and create child test cases using QA Tester Agent
            test_cases_created = []
            if hasattr(self.agents, 'qa_tester_agent') and 'qa_tester_agent' in self.agents:
                context = self.project_context.get_context() if hasattr(self, 'project_context') else {}
                
                # Prepare user story data for test case generation
                story_for_testing = {
                    'id': user_story_id,
                    'title': user_story_data.get('title', ''),
                    'description': user_story_data.get('description', ''),
                    'acceptance_criteria': user_story_data.get('acceptance_criteria', []),
                    'priority': user_story_data.get('priority', 'Medium'),
                    'story_points': user_story_data.get('story_points', 3)
                }
                
                test_cases = self.agents['qa_tester_agent'].generate_user_story_test_cases(story_for_testing, context)
                
                for test_case in test_cases:
                    if hasattr(self, 'azure_integrator'):
                        test_item = self.azure_integrator._create_test_case(test_case, user_story_id)
                        test_cases_created.append(test_item)
                        self.logger.info(f"Created Test Case {test_item['id']}: {test_case.get('title', '')}")
                    else:
                        # For testing, simulate test case creation
                        test_item = {
                            'id': len(test_cases_created) + 30000,  # Mock ID
                            'fields': {
                                'System.Title': test_case.get('title', ''),
                                'System.WorkItemType': 'Test Case'
                            }
                        }
                        test_cases_created.append(test_item)
                        self.logger.info(f"Mock created Test Case {test_item['id']}: {test_case.get('title', '')}")
            
            # Step 5: Return complete work item hierarchy
            result = {
                'user_story': user_story_item,
                'tasks': tasks_created,
                'test_cases': test_cases_created,
                'compliance_status': 'compliant',
                'created_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully created complete user story hierarchy: "
                           f"1 story, {len(tasks_created)} tasks, {len(test_cases_created)} test cases")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create complete user story with children: {e}")
            raise

    def _handle_dashboard_requirements(self, dashboard_requirements: List[Dict[str, Any]]):
        """Handle dashboard and reporting requirements identified by the sweeper."""
        self.logger.info(f"Processing {len(dashboard_requirements)} dashboard requirements")
        
        for req in dashboard_requirements:
            req_type = req.get('type', 'unknown')
            priority = req.get('priority', 'medium')
            description = req.get('description', 'No description')
            
            self.logger.info(f"Dashboard requirement ({priority}): {req_type} - {description}")
            
            # Log specific dashboard requirements
            if req_type == 'velocity_tracking':
                self.logger.info("  Recommendation: Set up velocity tracking charts for team performance monitoring")
            elif req_type == 'burndown_chart':
                self.logger.info("  Recommendation: Configure sprint burndown charts for iteration tracking")
            elif req_type == 'quality_metrics':
                self.logger.info("  Recommendation: Establish quality metrics dashboard with defect rates and test coverage")
            elif req_type == 'backlog_health':
                self.logger.info("  Recommendation: Create backlog health dashboard showing completeness and compliance")
            else:
                self.logger.info(f"  Recommendation: Review and implement {req_type} dashboard requirements")

    def _send_critical_issue_notification(self, report: Dict[str, Any]):
        """Send notifications for critical issues found in the sweep."""
        try:
            summary = report.get('summary', {})
            high_priority_count = summary.get('high_priority_count', 0)
            
            self.logger.warning(f"Critical issues detected: {high_priority_count} high-priority discrepancies")
            
            if hasattr(self, 'notifier'):
                # Send critical issue notification
                notification_data = {
                    'type': 'critical_backlog_issues',
                    'high_priority_count': high_priority_count,
                    'total_discrepancies': summary.get('total_discrepancies', 0),
                    'timestamp': datetime.now().isoformat(),
                    'report_summary': summary
                }
                
                self.notifier.send_critical_notification(notification_data)
                self.logger.info("Critical issue notification sent")
            else:
                self.logger.warning("No notifier configured - critical issues logged only")
                
        except Exception as e:
            self.logger.error(f"Failed to send critical issue notification: {e}")
    
    def _execute_stage_with_validation(self, stage: str, enable_immediate_remediation: bool = True):
        """
        Execute a workflow stage and perform immediate validation and remediation.
        
        Args:
            stage: The workflow stage to execute
            enable_immediate_remediation: Whether to immediately remediate found issues
        """
        self.logger.info(f"Executing stage with validation: {stage}")
        
        # Execute the core stage logic
        if stage == 'epic_strategist':
            self._execute_epic_generation()
            self._validate_epics()
        elif stage == 'feature_decomposer_agent':
            self._execute_feature_decomposition()
            self._validate_features()
        elif stage == 'user_story_decomposer_agent':
            self._execute_user_story_decomposition()
            self._validate_user_stories()
        elif stage == 'decomposition_agent':
            # Backward compatibility - run both feature and user story decomposition
            self._execute_feature_decomposition()
            self._validate_features()
            self._execute_user_story_decomposition()
            self._validate_user_stories()
        elif stage == 'user_story_decomposer':
            self._execute_user_story_decomposition()
            self._validate_user_stories()
        elif stage == 'developer_agent':
            self._execute_task_generation()
            self._validate_tasks_and_estimates()
        elif stage == 'qa_tester_agent':
            self._execute_qa_generation()
            self._validate_test_cases_and_plans()
        else:
            self.logger.warning(f"Unknown stage: {stage}")
            return False
        
        # Run targeted sweep for immediate validation
        if enable_immediate_remediation:
            sweeper = self._get_sweeper_agent()
            discrepancies = sweeper.run_targeted_sweep(
                stage=stage, 
                workflow_data=self.workflow_data, 
                immediate_callback=True
            )
            
            # If discrepancies found, they will be automatically reported to supervisor
            # via the callback and routed to appropriate agents
            if discrepancies:
                self.logger.info(f"Found {len(discrepancies)} issues in {stage}, routing for immediate remediation")
                return False  # Indicate stage needs remediation
            else:
                self.logger.info(f"Stage {stage} completed successfully with no issues")
                return True
        else:
            # Use legacy validation method
            incomplete_items = self._sweeper_validate_and_get_incomplete(stage)
            return len(incomplete_items) == 0
