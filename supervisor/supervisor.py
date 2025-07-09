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
from agents.developer_agent import DeveloperAgent
from agents.qa_tester_agent import QATesterAgent
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
    
    def __init__(self, config_path: str = None, area_path: str = None, iteration_path: str = None):
        """Initialize the supervisor with configuration and agents."""
        # Load configuration
        self.config = Config(config_path) if config_path else Config()
        
        # Setup logging
        self.logger = setup_logger("supervisor", "logs/supervisor.log")
        self.logger.info("Initializing WorkflowSupervisor")
        
        # Initialize project context
        self.project_context = ProjectContext(self.config)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Store area/iteration path for Azure DevOps
        self.area_path = area_path
        self.iteration_path = iteration_path
        
        # Initialize integrators and notifiers
        if self.area_path and self.iteration_path:
            self.azure_integrator = AzureDevOpsIntegrator(self.config, area_path=self.area_path, iteration_path=self.iteration_path)
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
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with configuration."""
        agents = {}
        
        try:
            agents['epic_strategist'] = EpicStrategist(self.config)
            agents['decomposition_agent'] = DecompositionAgent(self.config)
            agents['developer_agent'] = DeveloperAgent(self.config)
            agents['qa_tester_agent'] = QATesterAgent(self.config)
            
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
    
    def execute_workflow(self, 
                        product_vision: str,
                        stages: List[str] = None,
                        human_review: bool = False,
                        save_outputs: bool = True,
                        integrate_azure: bool = False) -> Dict[str, Any]:
        """
        Execute the complete workflow or specific stages.
        
        Args:
            product_vision: The product vision to transform
            stages: List of stages to execute (default: all)
            human_review: Whether to pause for human review between stages
            save_outputs: Whether to save intermediate outputs
            integrate_azure: Whether to create Azure DevOps work items
            
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
            
            for stage in stages_to_run:
                self.logger.info(f"Executing stage: {stage}")
                
                if stage == 'epic_strategist':
                    self._execute_epic_generation()
                elif stage == 'decomposition_agent':
                    self._execute_feature_decomposition()
                elif stage == 'user_story_decomposer':
                    self._execute_user_story_decomposition()
                elif stage == 'developer_agent':
                    self._execute_task_generation()
                elif stage == 'qa_tester_agent':
                    self._execute_qa_generation()
                else:
                    self.logger.warning(f"Unknown stage: {stage}")
                    continue
                
                # Mark stage as completed
                self.execution_metadata['stages_completed'].append(stage)
                
                # Human review checkpoint
                if human_review:
                    self._human_review_checkpoint(stage)
                
                # Save intermediate outputs
                if save_outputs:
                    self._save_intermediate_output(stage)
            
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
            
            epics = agent.generate_epics(self.workflow_data['product_vision'], context)
            
            if not epics:
                raise ValueError("Epic generation failed - no epics returned")
            
            self.workflow_data['epics'] = epics
            self.logger.info(f"Generated {len(epics)} epics")
            
        except Exception as e:
            self.logger.error(f"Epic generation failed: {e}")
            raise
    
    def _execute_feature_decomposition(self):
        """Execute feature decomposition stage."""
        self.logger.info("Decomposing epics into features")
        
        try:
            agent = self.agents['decomposition_agent']
            context = self.project_context.get_context('decomposition_agent')
            
            for epic in self.workflow_data['epics']:
                self.logger.info(f"Decomposing epic: {epic.get('title', 'Untitled')}")
                
                features = agent.decompose_epic(epic, context)
                epic['features'] = features
                
                self.logger.info(f"Generated {len(features)} features for epic")
                
        except Exception as e:
            self.logger.error(f"Feature decomposition failed: {e}")
            raise
    
    def _execute_user_story_decomposition(self):
        """Execute user story decomposition stage."""
        self.logger.info("Decomposing features into user stories")
        
        try:
            agent = self.agents['decomposition_agent']
            context = self.project_context.get_context('decomposition_agent')
            
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
        """Integrate generated backlog with Azure DevOps."""
        self.logger.info("Integrating with Azure DevOps")
        
        try:
            results = self.azure_integrator.create_work_items(self.workflow_data)
            
            # Store integration results
            self.workflow_data['azure_integration'] = {
                'status': 'success',
                'work_items_created': results,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully created {len(results)} work items in Azure DevOps")
            
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
            'decomposition_agent',
            'user_story_decomposer',
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
        elif agent_name == 'decomposition_agent' and hasattr(self, 'agents'):
            self._handle_decomposition_discrepancies(work_item_groups)
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
    
    def _handle_decomposition_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require Decomposition Agent intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"Decomposition Agent: Reviewing work item {wi_id}")
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # In a full implementation, you would call:
                # self.agents['decomposition_agent'].remediate_discrepancy(disc)
    
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
