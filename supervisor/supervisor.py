"""
Supervisor Module - Orchestrates the multi-agent backlog automation workflow.

The Supervisor manages the complete pipeline from product vision to Azure DevOps work items,
coordinating between agents, managing data flow, and handling integrations.
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

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
    
    def __init__(self, config_path: str = None):
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
        
        # Initialize integrators and notifiers
        self.azure_integrator = AzureDevOpsIntegrator(self.config)
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
                                    'acceptance_criteria': feature.get('acceptance_criteria', []),
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
                    
                    # Generate test cases
                    test_cases = agent.generate_test_cases(feature, context)
                    feature['test_cases'] = test_cases
                    
                    # Generate edge cases
                    edge_cases = agent.generate_edge_cases(feature, context)
                    feature['edge_cases'] = edge_cases
                    
                    # Validate acceptance criteria
                    validation = agent.validate_acceptance_criteria(feature, context)
                    feature['qa_validation'] = validation
                    
                    self.logger.info(f"Generated QA artifacts: {len(test_cases)} test cases, {len(edge_cases)} edge cases")
                    
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
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # In a full implementation, you would call:
                # self.agents['developer_agent'].remediate_discrepancy(disc)
    
    def _handle_qa_tester_discrepancies(self, work_item_groups: Dict[int, List[Dict]]):
        """Handle discrepancies that require QA Tester Agent intervention."""
        for wi_id, discrepancies in work_item_groups.items():
            self.logger.info(f"QA Tester Agent: Reviewing work item {wi_id}")
            for disc in discrepancies:
                self.logger.info(f"  - {disc.get('type', 'unknown')}: {disc.get('description', 'No description')}")
                # In a full implementation, you would call:
                # self.agents['qa_tester_agent'].remediate_discrepancy(disc)
    
    def _handle_dashboard_requirements(self, requirements: List[Dict[str, Any]]):
        """Process dashboard and reporting requirements."""
        for req in requirements:
            component = req.get('component', 'unknown')
            description = req.get('description', 'No description')
            priority = req.get('priority', 'medium')
            self.logger.info(f"Dashboard Requirement ({priority}): {component} - {description}")
            
            # In a full implementation, you would:
            # - Check if dashboard component exists
            # - Update or create dashboard widgets as needed
            # - Schedule regular updates
    
    def _send_critical_issue_notification(self, report: Dict[str, Any]):
        """Send notification for critical issues found during sweep."""
        try:
            high_priority = report.get('discrepancies_by_priority', {}).get('high', [])
            if not high_priority:
                return
                
            # Create notification message
            message = f"🚨 Backlog Sweep Alert: {len(high_priority)} high-priority issues found\n\n"
            
            # Group by type for summary
            type_counts = {}
            for disc in high_priority:
                disc_type = disc.get('type', 'unknown')
                type_counts[disc_type] = type_counts.get(disc_type, 0) + 1
            
            message += "Issue Summary:\n"
            for issue_type, count in type_counts.items():
                message += f"  • {issue_type}: {count} items\n"
            
            message += f"\nTotal work items affected: {len(set(d.get('work_item_id') for d in high_priority if d.get('work_item_id')))}"
            
            # Send notification using existing notifier
            if hasattr(self, 'notifier'):
                self.notifier.send_alert("Backlog Critical Issues", message)
            else:
                self.logger.warning(f"Critical issues notification: {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to send critical issue notification: {e}")
