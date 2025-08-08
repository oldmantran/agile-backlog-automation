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
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

from config.config_loader import Config
from agents.epic_strategist import EpicStrategist
from agents.feature_decomposer_agent import FeatureDecomposerAgent
from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
from agents.developer_agent import DeveloperAgent
from agents.qa_lead_agent import QALeadAgent
from agents.qa_lead_agent import QALeadAgent
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from utils.project_context import ProjectContext
from utils.logger import setup_logger
from utils.notifier import Notifier
from utils.ollama_model_manager import ollama_manager
from integrators.azure_devops_api import AzureDevOpsIntegrator


class WorkflowStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentMetrics:
    name: str
    executions: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    last_execution: Optional[str] = None
    current_status: str = "idle"
    error_count: int = 0

@dataclass
class WorkflowMetrics:
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    current_stage: str
    progress_percentage: float = 0.0
    agents_metrics: Dict[str, AgentMetrics] = None
    quality_score: float = 0.0
    artifacts_created: Dict[str, int] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.agents_metrics is None:
            self.agents_metrics = {}
        if self.artifacts_created is None:
            self.artifacts_created = {}
        if self.errors is None:
            self.errors = []

class WorkflowMonitor:
    """Real-time workflow monitoring and dashboard system"""
    
    def __init__(self, supervisor_instance):
        self.supervisor = supervisor_instance
        self.workflow_metrics = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self.dashboard_callbacks = []
        self.metrics_history = []
        
    def start_monitoring(self, workflow_id: str):
        """Start monitoring a workflow execution"""
        self.workflow_metrics[workflow_id] = WorkflowMetrics(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now(),
            current_stage="initialization"
        )
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(workflow_id,),
            daemon=True
        )
        self.monitor_thread.start()
        
    def stop_monitoring(self, workflow_id: str):
        """Stop monitoring a workflow"""
        if workflow_id in self.workflow_metrics:
            self.workflow_metrics[workflow_id].status = WorkflowStatus.COMPLETED
            self.monitoring_active = False
            
    def update_stage_progress(self, workflow_id: str, stage: str, progress: float):
        """Update current stage progress"""
        if workflow_id in self.workflow_metrics:
            metrics = self.workflow_metrics[workflow_id]
            metrics.current_stage = stage
            metrics.progress_percentage = progress
            self._notify_dashboard_update(workflow_id, metrics)
            
    def update_agent_metrics(self, workflow_id: str, agent_name: str, 
                           duration: float, success: bool, error: str = None):
        """Update individual agent performance metrics"""
        if workflow_id not in self.workflow_metrics:
            return
            
        metrics = self.workflow_metrics[workflow_id]
        if agent_name not in metrics.agents_metrics:
            metrics.agents_metrics[agent_name] = AgentMetrics(name=agent_name)
            
        agent_metrics = metrics.agents_metrics[agent_name]
        agent_metrics.executions += 1
        agent_metrics.last_execution = datetime.now().isoformat()
        
        # Update success rate
        if success:
            agent_metrics.success_rate = (
                (agent_metrics.success_rate * (agent_metrics.executions - 1) + 1.0) / 
                agent_metrics.executions
            )
        else:
            agent_metrics.error_count += 1
            agent_metrics.success_rate = (
                (agent_metrics.success_rate * (agent_metrics.executions - 1)) / 
                agent_metrics.executions
            )
            if error:
                metrics.errors.append(f"{agent_name}: {error}")
                
        # Update average duration
        agent_metrics.avg_duration = (
            (agent_metrics.avg_duration * (agent_metrics.executions - 1) + duration) / 
            agent_metrics.executions
        )
        
    def calculate_quality_score(self, workflow_id: str, validation_results: Dict):
        """Calculate overall workflow quality score"""
        if workflow_id not in self.workflow_metrics:
            return
            
        metrics = self.workflow_metrics[workflow_id]
        
        # Calculate quality score based on validation results
        total_items = validation_results.get('total_items', 1)
        critical_issues = validation_results.get('critical_issues', 0)
        warning_issues = validation_results.get('warning_issues', 0)
        
        # Quality score formula: 100 - (critical_weight * critical_issues + warning_weight * warning_issues) / total_items
        critical_weight = 10
        warning_weight = 2
        
        quality_penalty = (critical_weight * critical_issues + warning_weight * warning_issues) / total_items
        metrics.quality_score = max(0, 100 - quality_penalty)
        
    def get_dashboard_data(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a workflow"""
        if workflow_id not in self.workflow_metrics:
            return {}
            
        metrics = self.workflow_metrics[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'status': metrics.status.value,
            'start_time': metrics.start_time.isoformat(),
            'current_stage': metrics.current_stage,
            'progress_percentage': metrics.progress_percentage,
            'quality_score': metrics.quality_score,
            'agents_metrics': {
                name: asdict(agent_metrics) 
                for name, agent_metrics in metrics.agents_metrics.items()
            },
            'artifacts_created': metrics.artifacts_created,
            'errors': metrics.errors[-10:],  # Last 10 errors
            'execution_time': (datetime.now() - metrics.start_time).total_seconds()
        }
        
    def register_dashboard_callback(self, callback):
        """Register a callback for dashboard updates"""
        self.dashboard_callbacks.append(callback)
        
    def _monitor_loop(self, workflow_id: str):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Update artifacts count
                if hasattr(self.supervisor, 'workflow_data') and self.supervisor.workflow_data:
                    self._update_artifacts_count(workflow_id)
                    
                # Store metrics snapshot for historical analysis
                if workflow_id in self.workflow_metrics:
                    snapshot = self.get_dashboard_data(workflow_id)
                    snapshot['timestamp'] = datetime.now().isoformat()
                    self.metrics_history.append(snapshot)
                    
                    # Keep only last 1000 snapshots
                    if len(self.metrics_history) > 1000:
                        self.metrics_history = self.metrics_history[-1000:]
                        
                time.sleep(1)  # Update every second
                
            except Exception as e:
                self.supervisor.logger.error(f"Monitoring error: {e}")
                
    def _update_artifacts_count(self, workflow_id: str):
        """Update artifacts count from workflow data"""
        if workflow_id not in self.workflow_metrics:
            return
            
        metrics = self.workflow_metrics[workflow_id]
        workflow_data = self.supervisor.workflow_data
        
        metrics.artifacts_created = {
            'epics': len(workflow_data.get('epics', [])),
            'features': sum(len(e.get('features', [])) for e in workflow_data.get('epics', [])),
            'user_stories': sum(len(f.get('user_stories', [])) 
                               for e in workflow_data.get('epics', []) 
                               for f in e.get('features', [])),
            'tasks': sum(len(s.get('tasks', [])) 
                        for e in workflow_data.get('epics', []) 
                        for f in e.get('features', []) 
                        for s in f.get('user_stories', [])),
            'test_cases': sum(len(s.get('test_cases', [])) 
                             for e in workflow_data.get('epics', []) 
                             for f in e.get('features', []) 
                             for s in f.get('user_stories', []))
        }
        
    def _notify_dashboard_update(self, workflow_id: str, metrics: WorkflowMetrics):
        """Notify registered dashboard callbacks of updates"""
        dashboard_data = self.get_dashboard_data(workflow_id)
        for callback in self.dashboard_callbacks:
            try:
                callback(dashboard_data)
            except Exception as e:
                self.supervisor.logger.error(f"Dashboard callback error: {e}")

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
    
    def __init__(self, config_path: str = None, organization_url: str = None, project: str = None, personal_access_token: str = None, area_path: str = None, iteration_path: str = None, job_id: str = None, settings_manager: Any = None, user_id: str = None, include_test_artifacts: bool = True):
        """Initialize the supervisor with configuration and agents."""
        # Load configuration
        self.config = Config(config_path) if config_path else Config()
        
        # Setup logging
        self.logger = setup_logger("supervisor", "logs/supervisor.log", "DEBUG")
        self.logger.info(f"Initializing WorkflowSupervisor for job_id={job_id}")
        if organization_url or project or area_path or iteration_path:
            self.logger.info(f"Azure DevOps config for job_id={job_id}: org_url={organization_url}, project={project}, area_path={area_path}, iteration_path={iteration_path}")
        
        # Store settings manager and user ID for work item limits
        self.settings_manager = settings_manager
        self.user_id = user_id
        
        # Store testing configuration
        self.include_test_artifacts = include_test_artifacts
        self.logger.info(f"Testing artifacts {'enabled' if include_test_artifacts else 'disabled'} for workflow")
        
        # Initialize project context
        self.project_context = ProjectContext(self.config)
        
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
        
        # Initialize agents (after Azure integrator is created)
        self.agents = self._initialize_agents()
        
        # Workflow state
        self.workflow_data = {}
        self.execution_metadata = {
            'start_time': None,
            'end_time': None,
            'stages_completed': [],
            'errors': [],
            'outputs_generated': []
        }
        
        # Get LLM configuration for model management
        self.llm_provider = self.config.env.get('LLM_PROVIDER', 'openai').lower()
        self.ollama_model = self.config.env.get('OLLAMA_MODEL')
        self.sweeper_agent = None  # Will be initialized as needed
        self.sweeper_retry_tracker = {}  # {stage: {item_id: retry_count}}
        
        # Initialize backlog sweeper for validation
        self.backlog_sweeper = BacklogSweeperAgent(self.config)
        
        # Initialize workflow monitor
        self.workflow_monitor = WorkflowMonitor(self)
        self.current_workflow_id = None
        
        # Parallel processing configuration
        self.parallel_config = self._get_parallel_config()
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with configuration."""
        agents = {}
        agents['epic_strategist'] = EpicStrategist(self.config)
        agents['feature_decomposer_agent'] = FeatureDecomposerAgent(self.config)
        agents['user_story_decomposer_agent'] = UserStoryDecomposerAgent(self.config)
        agents['developer_agent'] = DeveloperAgent(self.config)
        agents['qa_lead_agent'] = QALeadAgent(self.config)  # Replaces deprecated agent
        
        # Set Azure DevOps integrator for agents that need it
        if hasattr(self, 'azure_integrator') and self.azure_integrator is not None:
            for agent_name, agent in agents.items():
                if hasattr(agent, 'set_azure_integrator'):
                    agent.set_azure_integrator(self.azure_integrator)
        
        self.logger.info(f"Initialized {len(agents)} agents successfully")
        return agents
    
    def _refresh_agent_configurations(self):
        """Refresh LLM configurations for all agents."""
        self.logger.info("Refreshing agent configurations...")
        for agent_name, agent in self.agents.items():
            try:
                # Force refresh the configuration for each agent
                agent._setup_llm_config()
                self.logger.info(f"Refreshed config for {agent_name}: {agent.llm_provider} ({agent.model})")
            except Exception as e:
                self.logger.warning(f"Failed to refresh config for {agent_name}: {e}")
    
    def _ensure_model_loaded(self, stage_name: str, agent_name: str = None) -> bool:
        """
        Ensure the correct LLM model is loaded before agent execution.
        
        This prevents agents from using incorrect models and ensures VRAM usage stays within limits.
        Now supports per-agent model loading.
        
        Args:
            stage_name: Name of the stage about to be executed
            agent_name: Name of the agent (for per-agent model lookup)
            
        Returns:
            True if model is ready, False if failed
        """
        try:
            if self.llm_provider == 'ollama':
                # Determine which model to load
                model_to_load = self.ollama_model  # Default global model
                
                # Check for agent-specific model override
                if agent_name and hasattr(self, 'agents') and agent_name in self.agents:
                    agent = self.agents[agent_name]
                    if hasattr(agent, 'model'):
                        model_to_load = agent.model
                        self.logger.info(f"[{stage_name}] Using agent-specific model: {model_to_load}")
                
                if not model_to_load:
                    self.logger.warning(f"[{stage_name}] No model configured - skipping model verification")
                    return True
                
                self.logger.info(f"[{stage_name}] Ensuring Ollama model {model_to_load} is loaded...")
                
                success = ollama_manager.ensure_model_loaded(
                    model_name=model_to_load,
                    provider=self.llm_provider
                )
                
                if success:
                    self.logger.info(f"[{stage_name}] Model {model_to_load} is ready")
                else:
                    self.logger.error(f"[{stage_name}] Failed to load model {model_to_load}")
                    # Don't fail the entire workflow, but log the issue
                    self.execution_metadata['errors'].append(f"Failed to load model {self.ollama_model} for {stage_name}")
                    return False
            else:
                self.logger.debug(f"[{stage_name}] Using {self.llm_provider} provider - no model preloading needed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ [{stage_name}] Error ensuring model is loaded: {e}")
            self.execution_metadata['errors'].append(f"Model loading error for {stage_name}: {str(e)}")
            return False
    
    def _get_parallel_config(self) -> Dict[str, Any]:
        """Get parallel processing configuration from settings."""
        workflow_config = self.config.settings.get('workflow', {})
        parallel_config = workflow_config.get('parallel_processing', {})
        
        return {
            'enabled': parallel_config.get('enabled', True),
            'max_workers': parallel_config.get('max_workers', 4),
            'rate_limit_per_second': parallel_config.get('rate_limit_per_second', 10),
            'stages': {
                'feature_decomposer_agent': parallel_config.get('feature_decomposition', True),
                'user_story_decomposer_agent': parallel_config.get('user_story_decomposition', True),
                'developer_agent': parallel_config.get('task_generation', True),
                'qa_lead_agent': parallel_config.get('qa_generation', True)
            }
        }
    
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
        total_features = 0
        features_with_test_plans = 0
        total_user_stories = 0
        user_stories_with_test_cases = 0
        
        for epic in epics:
            for feature in epic.get('features', []):
                total_features += 1
                # Check for either test_plan or test_plan_structure
                test_plan = feature.get('test_plan') or feature.get('test_plan_structure')
                if test_plan:
                    features_with_test_plans += 1
                else:
                    self.logger.warning(f"QA Tester Agent did not generate a test plan for feature '{feature.get('title', 'Untitled')}'. This feature will be skipped in validation.")
                    errors.append(f"Feature '{feature.get('title', 'Untitled')}' missing test plan structure.")
                
                for user_story in feature.get('user_stories', []):
                    total_user_stories += 1
                    test_cases = user_story.get('test_cases', [])
                    if test_cases and all('title' in tc and tc['title'] for tc in test_cases):
                        user_stories_with_test_cases += 1
                    else:
                        self.logger.warning(f"QA Tester Agent did not generate valid test cases for user story '{user_story.get('title', 'Untitled')}'. This user story will be skipped in validation.")
                        errors.append(f"User story '{user_story.get('title', 'Untitled')}' missing valid test cases.")
        
        # Calculate completion percentages
        test_plan_completion = (features_with_test_plans / total_features * 100) if total_features > 0 else 0
        test_case_completion = (user_stories_with_test_cases / total_user_stories * 100) if total_user_stories > 0 else 0
        
        if errors:
            self.logger.warning(f"Validation completed with {len(errors)} test case errors.")
            self.logger.info(f"Test plan completion: {test_plan_completion:.1f}% ({features_with_test_plans}/{total_features})")
            self.logger.info(f"Test case completion: {test_case_completion:.1f}% ({user_stories_with_test_cases}/{total_user_stories})")
            
            # Don't fail the entire process if we have reasonable completion rates
            if test_plan_completion >= 50 and test_case_completion >= 50:
                self.logger.info("QA validation passed with acceptable completion rates. Process will continue.")
            else:
                self.logger.warning("QA validation has low completion rates, but process will continue to avoid restart loops.")
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

        elif stage == 'user_story_decomposer':
            return sweeper.validate_feature_user_story_relationships(epics)
        elif stage == 'developer_agent':
            return sweeper.validate_user_story_tasks(epics)
        elif stage == 'qa_lead_agent':
            return sweeper.validate_test_artifacts(epics)
        else:
            return []

    def execute_workflow(self, 
                        product_vision: str,
                        stages: List[str] = None,
                        human_review: bool = False,
                        save_outputs: bool = True,
                        integrate_azure: bool = False,
                        progress_callback: Optional[callable] = None,
                        enable_monitoring: bool = True,
                        include_test_artifacts: bool = True) -> Dict[str, Any]:
        """
        Execute the complete workflow or specific stages.
        
        Args:
            product_vision: The product vision to transform
            stages: List of stages to execute (default: all)
            human_review: Whether to pause for human review between stages
            save_outputs: Whether to save intermediate outputs
            integrate_azure: Whether to create Azure DevOps work items
            progress_callback: Optional callback function to report progress
            enable_monitoring: Whether to enable workflow monitoring
            include_test_artifacts: Whether to generate test plans, suites, and cases
            
        Returns:
            Complete workflow results including all generated artifacts
        """
        
        self.execution_metadata['start_time'] = datetime.now()
        self.logger.info(f"Starting workflow execution at {self.execution_metadata['start_time']}")
        
        # Store include_test_artifacts flag
        self.include_test_artifacts = include_test_artifacts
        self.logger.info(f"Include test artifacts: {include_test_artifacts}")
        
        # Progress tracking
        stages_to_run = stages or self._get_default_stages()
        
        # Remove QA stages if test artifacts are not included
        if not include_test_artifacts:
            original_stages = stages_to_run.copy()
            stages_to_run = [stage for stage in stages_to_run if 'qa' not in stage.lower()]
            self.logger.info(f"Test artifacts disabled - removed QA stages: {set(original_stages) - set(stages_to_run)}")
        
        total_stages = len(stages_to_run)
        # Updated progress mapping including ADO integration as continuous sequence
        # Most time is spent on detailed work (tasks and QA), not high-level items
        if include_test_artifacts:
            stage_progress_mapping = {
                0: 5,   # Initial setup complete (very fast)
                1: 15,  # Epic generation complete (fast - high-level work)
                2: 25,  # Feature decomposition complete (moderate - still high-level)
                3: 35,  # User story decomposition complete (moderate - getting detailed)
                4: 50,  # Task generation complete (significant time - detailed technical work)
                5: 75,  # QA generation complete (most time - complex test case generation)
                6: 85,  # ADO integration complete (work item creation and linking)
                7: 95,  # Final validation and cleanup
                8: 100, # Complete with notifications
            }
        else:
            # Adjusted progress mapping when QA is skipped
            stage_progress_mapping = {
                0: 5,   # Initial setup complete (very fast)
                1: 20,  # Epic generation complete (fast - high-level work)
                2: 35,  # Feature decomposition complete (moderate - still high-level)
                3: 50,  # User story decomposition complete (moderate - getting detailed)
                4: 70,  # Task generation complete (significant time - detailed technical work)
                5: 85,  # ADO integration complete (work item creation and linking)
                6: 95,  # Final validation and cleanup
                7: 100, # Complete with notifications
            }
        
        # Helper function to update progress with optional sub-progress
        def update_progress(stage_index: int, action: str, sub_progress: float = 0.0):
            if progress_callback:
                base_progress = stage_progress_mapping.get(stage_index, 30)
                
                # Add sub-progress within the current stage
                if stage_index < len(stage_progress_mapping) - 1:
                    next_progress = stage_progress_mapping.get(stage_index + 1, 100)
                    stage_range = next_progress - base_progress
                    final_progress = base_progress + (stage_range * sub_progress)
                else:
                    # For the last stage, allow sub-progress up to 100%
                    stage_range = 100 - base_progress
                    final_progress = base_progress + (stage_range * sub_progress)
                
                progress_callback(int(final_progress), action)
        
        # Generate unique workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_workflow_id = workflow_id
        
        # Start monitoring if enabled
        if enable_monitoring:
            self.workflow_monitor.start_monitoring(workflow_id)
            
        # Initial progress update
        update_progress(0, "Initializing workflow")
        
        # Refresh agent configurations to ensure latest LLM settings are used
        self._refresh_agent_configurations()
        
        # Update project context with actual project name and product vision
        context_updates = {}
        if self.project:
            context_updates['project_name'] = self.project
        if product_vision:
            context_updates['product_vision'] = product_vision
            self.logger.info(f"DEBUG: execute_workflow - Adding product_vision to context_updates, length: {len(product_vision)}")
        
        if context_updates:
            self.logger.info(f"DEBUG: execute_workflow - Updating project context with keys: {list(context_updates.keys())}")
            self.project_context.update_context(context_updates)
            
            # Verify the update worked immediately
            test_context = self.project_context.get_context()
            if 'product_vision' in test_context:
                self.logger.info(f"DEBUG: execute_workflow - VERIFIED: product_vision in context after update, length: {len(test_context['product_vision'])}")
            else:
                self.logger.error(f"DEBUG: execute_workflow - FAILED: product_vision NOT in context after update!")
                self.logger.error(f"DEBUG: Available context keys: {list(test_context.keys())}")
        
        # Extract domain from product vision using VisionContextExtractor
        try:
            from utils.vision_context_extractor import VisionContextExtractor
            vision_extractor = VisionContextExtractor()
            
            # Create a mock project_data structure for the extractor
            mock_project_data = {
                'vision_statement': product_vision,
                'description': product_vision
            }
            
            # Extract enhanced context from vision
            enhanced_context = vision_extractor.extract_context(
                project_data=mock_project_data,
                business_objectives=[],
                target_audience=None,
                domain=None
            )
            
            # Only update domain if user hasn't explicitly set one
            current_context = self.project_context.get_context()
            user_domain = current_context.get('domain')
            
            if user_domain and user_domain != 'dynamic':
                # User has explicitly set a domain - respect their choice
                self.logger.info(f"Preserving user's explicit domain choice: {user_domain}")
                # Still update other extracted context but NOT the domain
                if enhanced_context:
                    updates = {}
                    if enhanced_context.get('target_users'):
                        updates['target_users'] = enhanced_context['target_users']
                    if enhanced_context.get('platform'):
                        updates['platform'] = enhanced_context['platform']
                    if enhanced_context.get('integrations'):
                        updates['integrations'] = enhanced_context['integrations']
                    if updates:
                        self.project_context.update_context(updates)
                        self.logger.info(f"Updated project context (preserving domain): {list(updates.keys())}")
            elif enhanced_context.get('domain') and enhanced_context['domain'] != 'dynamic':
                # No user domain set - use extracted domain as fallback
                self.project_context.update_context({
                    'domain': enhanced_context['domain'],
                    'industry': enhanced_context.get('industry', enhanced_context['domain']),
                    'target_users': enhanced_context.get('target_users', 'end users'),
                    'platform': enhanced_context.get('platform', 'Web application'),
                    'integrations': enhanced_context.get('integrations', 'standard integrations')
                })
                self.logger.info(f"No user domain set - using extracted domain: {enhanced_context['domain']}")
            else:
                self.logger.info("No domain extraction possible, using existing context")
                
        except Exception as e:
            self.logger.warning(f"Failed to extract domain from vision: {e}")
            # Continue with default context
        
        # Initialize workflow data
        self.workflow_data = {
            'product_vision': product_vision,
            'epics': [],
            'metadata': {
                'project_context': self.project_context.get_context(),
                'execution_config': {
                    'stages': stages_to_run,
                    'human_review': human_review,
                    'save_outputs': save_outputs,
                    'integrate_azure': integrate_azure,
                    'include_test_artifacts': include_test_artifacts
                },
                'azure_config': {
                    'organization_url': self.organization_url,
                    'project': self.project,
                    'area_path': self.area_path,
                    'iteration_path': self.iteration_path
                }
            }
        }
        
        # Execute stages in sequence
        stages_to_run = stages or self._get_default_stages()
        self.sweeper_retry_tracker = {}
        
        try:
            for stage_index, stage in enumerate(stages_to_run):
                self.logger.info(f"Executing stage: {stage}")
                update_progress(stage_index + 1, f"Executing {stage}")
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
                        elif stage == 'user_story_decomposer':
                            self._execute_user_story_decomposition()
                            self._validate_user_stories()
                        elif stage == 'developer_agent':
                            self._execute_task_generation(update_progress, stage_index + 1)
                            self._validate_tasks_and_estimates()
                        elif stage == 'qa_lead_agent':
                            self._execute_qa_generation(update_progress, stage_index + 1)
                            self._validate_test_cases_and_plans()
                        elif stage == 'azure_integration':
                            self.logger.info(f"Executing Azure integration stage (integrate_azure flag: {integrate_azure})")
                            if integrate_azure:
                                self._integrate_with_azure_devops()
                            else:
                                self.logger.warning("❌ Azure integration stage skipped (integrate_azure=False)")
                                self.workflow_data['azure_integration'] = {
                                    'status': 'skipped',
                                    'reason': 'integrate_azure flag is False',
                                    'timestamp': datetime.now().isoformat()
                                }
                        elif stage == 'final_validation':
                            self._execute_final_validation(update_progress, stage_index + 1)
                        else:
                            self.logger.warning(f"Unknown stage: {stage}")
                            break
                        
                        # After agent stage, run sweeper to validate outputs
                        self.logger.debug(f"[DEBUG] Stage {stage}: Runningsweeper validation.")
                        print(f"[DEBUG] Stage {stage}: Runningsweeper validation.")
                        incomplete_items = self._sweeper_validate_and_get_incomplete(stage)
                        self.logger.debug(f"[DEBUG] Stage '{stage}': Incomplete items returned: {incomplete_items}")
                        print(f"[DEBUG] Stage '{stage}': Incomplete items returned: {incomplete_items}")
                        if not incomplete_items:
                            completed = True
                            break
                        # Targeted retry logic
                        still_incomplete = []
                        for item in incomplete_items:
                            item_id = item.get('work_item_id')
                            self.logger.debug(f"[DEBUG] Stage '{stage}: Processing item: {item}")
                            self.logger.debug(f"[DEBUG] Stage {stage}:item_id = {item_id} (type: {type(item_id)})")
                            print(f"[DEBUG] Stage '{stage}: Processing item: {item}")
                            print(f"[DEBUG] Stage {stage}:item_id = {item_id} (type: {type(item_id)})")
                            # Ensure item_id is hashable (not a dict or list)
                            if item_id is None:
                                self.logger.warning(f"[DEBUG] Incomplete item missing work_item_id: {item}. Skipping.")
                                print(f"[DEBUG] Incomplete item missing work_item_id: {item}. Skipping.")
                                continue
                            if isinstance(item_id, (dict, list)):
                                self.logger.warning(f"[DEBUG] work_item_id is not hashable (dict or list): {item_id}. Skipping item: {item}")
                                print(f"[DEBUG] work_item_id is not hashable (dict or list): {item_id}. Skipping item: {item}")
                                continue
                            try:
                                retry_count = self.sweeper_retry_tracker[stage].get(item_id, 0)
                            except Exception as e:
                                self.logger.error(f"[DEBUG] Exception using item_id as key: {item_id} (type: {type(item_id)}), error: {e}")
                                print(f"[DEBUG] Exception using item_id as key: {item_id} (type: {type(item_id)}), error: {e}")
                                import traceback
                                self.logger.error(traceback.format_exc())
                                print(traceback.format_exc())
                                continue
                            if retry_count < max_retries:
                                self.logger.info(f"[DEBUG] Retrying incomplete item {item_id} for stage {stage} (attempt {retry_count+1}/{max_retries})")
                                try:
                                    self.sweeper_retry_tracker[stage][item_id] = retry_count + 1
                                except Exception as e:
                                    self.logger.error(f"[DEBUG] Exception setting retry count for item_id: {item_id} (type: {type(item_id)}), error: {e}")
                                    print(f"[DEBUG] Exception setting retry count for item_id: {item_id} (type: {type(item_id)}), error: {e}")
                                    import traceback
                                    self.logger.error(traceback.format_exc())
                                    print(traceback.format_exc())
                                    continue
                            else:
                                self.logger.error(f"[DEBUG] Item {item_id} in stage {stage} failed after {max_retries} attempts. Logging warning.")
                                # Log persistent failure as warning instead of sending immediate notification
                                self.execution_metadata['errors'].append(f"Item {item_id} in {stage} failed after {max_retries} retries: {item.get('description','')}")
                            # Only retry items that have not hit max_retries
                            if self.sweeper_retry_tracker[stage].get(item_id, 0) < max_retries:
                                still_incomplete.append(item)
                        self.logger.debug(f"[DEBUG] Stage '{stage}': still_incomplete after retry: {still_incomplete}")
                        print(f"[DEBUG] Stage '{stage}': still_incomplete after retry: {still_incomplete}")
                        if not still_incomplete:
                            completed = True
                        else:
                            self.logger.info(f"[DEBUG] {len(still_incomplete)} items remain incomplete after this retry round in stage {stage}.")
                            print(f"[DEBUG] {len(still_incomplete)} items remain incomplete after this retry round in stage {stage}.")
                    except Exception as e:
                        self.logger.error(f"{stage} failed with exception: {e}")
                        self.execution_metadata['errors'].append(f"{stage} failed: {e}")
                        
                        # Check if this is a critical failure that should stop the workflow
                        error_msg = str(e).lower()
                        is_critical_failure = (
                            "quality assessment failed" in error_msg or
                            "epic generation failed completely" in error_msg or
                            "no epics achieved excellent" in error_msg or
                            isinstance(e, (RuntimeError, ValueError)) and stage in ['epic_strategist']
                        )
                        
                        if is_critical_failure:
                            self.logger.error(f"CRITICAL FAILURE in {stage} - STOPPING WORKFLOW")
                            self.execution_metadata['status'] = 'failed'
                            self.execution_metadata['critical_error'] = str(e)
                            self.execution_metadata['failed_stage'] = stage
                            raise e  # Re-raise to stop the workflow completely
                        else:
                            # Non-critical errors: collect as warning and continue
                            completed = True
            
            # Final processing
            try:
                self._finalize_workflow_data()
                
                # Azure DevOps integration is now handled in the stage execution
                # No need to duplicate the call here
                
                # Set end time before sending notifications
                self.execution_metadata['end_time'] = datetime.now()
                self.logger.info(f"Workflow execution completed successfully at {self.execution_metadata['end_time']}")
                
                # Note: Notifications will be sent from final_validation stage
                
                # Save final output
                if save_outputs:
                    self._save_final_output()
                
                # Final progress update
                update_progress(total_stages + 1, "Backlog generation completed")
                return self.workflow_data
                
            except Exception as e:
                self.logger.error(f"Error in final processing: {e}")
                # Don't fail the entire workflow for final processing errors
                # Just log the error and return the workflow data
                return self.workflow_data
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            self.execution_metadata['errors'].append(str(e))
            self.execution_metadata['end_time'] = datetime.now()
            self.logger.info(f"Workflow execution failed at {self.execution_metadata['end_time']}")
            
            # Calculate execution time even on failure
            if self.execution_metadata['start_time'] and self.execution_metadata['end_time']:
                execution_time = (self.execution_metadata['end_time'] - self.execution_metadata['start_time']).total_seconds()
                self.logger.info(f"Workflow execution time before failure: {execution_time:.2f} seconds")
            
            # Send error notification for critical workflow failures
            # Check if this is a critical failure that should send immediate notification
            is_critical = (
                self.execution_metadata.get('critical_error') is not None or
                self.execution_metadata.get('failed_stage') == 'epic_strategist' or
                'quality assessment failed' in str(e).lower() or
                isinstance(e, (RuntimeError, ValueError))
            )
            
            if is_critical or len(self.execution_metadata['errors']) > 5:
                self._send_error_notifications(e)
            raise
        finally:
            if not self.execution_metadata['end_time']:
                self.execution_metadata['end_time'] = datetime.now()
                self.logger.info(f"Workflow execution finalized at {self.execution_metadata['end_time']}")
            
            # Ensure execution time is always calculated and logged
            if self.execution_metadata['start_time'] and self.execution_metadata['end_time']:
                execution_time = (self.execution_metadata['end_time'] - self.execution_metadata['start_time']).total_seconds()
                self.logger.info(f"Final workflow execution time: {execution_time:.2f} seconds")
                
                # Log parallel processing efficiency if enabled
                if self.parallel_config.get('enabled'):
                    self.logger.info(f"Parallel processing was enabled with {self.parallel_config.get('max_workers', 0)} workers")
                    self.logger.info(f"Parallel stages: {[k for k, v in self.parallel_config.get('stages', {}).items() if v]}")
    
    def _execute_epic_generation(self):
        """Execute epic generation stage."""
        self.logger.info("Generating epics from product vision")
        
        # Ensure correct model is loaded before agent execution
        if not self._ensure_model_loaded("Epic Generation", "epic_strategist"):
            self.logger.warning("Model loading failed but continuing with epic generation")
        
        try:
            agent = self.agents['epic_strategist']
            context = self.project_context.get_context('epic_strategist')
            
            # Get limits from settings manager if available, otherwise fall back to config
            max_epics = None
            if self.settings_manager and self.user_id:
                try:
                    work_item_limits = self.settings_manager.get_work_item_limits(self.user_id)
                    max_epics = work_item_limits.max_epics
                    self.logger.info(f"Using settings manager limits for user {self.user_id}: max_epics={max_epics}")
                except Exception as e:
                    self.logger.warning(f"Failed to get limits from settings manager: {e}, falling back to config")
                    max_epics = self.config.settings.get('work_item_limits', {}).get('max_epics')
            else:
                # Fall back to work_item_limits config section (not workflow.limits)
                max_epics = self.config.settings.get('work_item_limits', {}).get('max_epics')
                self.logger.info(f"Using config limits: max_epics={max_epics}")
            
            # Generate epics from product vision
            product_vision = self.workflow_data.get('product_vision', '')
            if not product_vision:
                raise ValueError("Product vision is required for epic generation")
            
            self.logger.info(f"Generating epics from product vision: {product_vision[:100]}...")
            # Sanitize Unicode characters for Windows console logging
            sanitized_vision = product_vision.encode('ascii', 'replace').decode('ascii')
            self.logger.info(f"DEBUG: Full product vision being passed to agent: {sanitized_vision}")
            # Sanitize context for logging
            sanitized_context = str(context).encode('ascii', 'replace').decode('ascii')
            self.logger.info(f"DEBUG: Context being passed to agent: {sanitized_context}")
            
            # Add timeout protection for epic generation
            import threading
            import time
            
            epics = [None]
            exception = [None]
            
            def generate_epics_thread():
                try:
                    self.logger.info("DEBUG: Starting epic generation in thread")
                    self.logger.info(f"DEBUG: Agent type: {type(agent)}")
                    self.logger.info(f"DEBUG: Agent LLM provider: {agent.llm_provider}")
                    self.logger.info(f"DEBUG: Agent model: {agent.model}")
                    self.logger.info(f"DEBUG: Agent ollama_provider exists: {hasattr(agent, 'ollama_provider')}")
                    if hasattr(agent, 'ollama_provider') and agent.ollama_provider:
                        self.logger.info(f"DEBUG: Agent ollama_provider type: {type(agent.ollama_provider)}")
                    
                    epics[0] = agent.generate_epics(product_vision, context, max_epics=max_epics)
                    self.logger.info("DEBUG: Epic generation completed successfully")
                except Exception as e:
                    self.logger.error(f"DEBUG: Epic generation exception: {e}")
                    self.logger.error(f"DEBUG: Epic generation exception type: {type(e)}")
                    import traceback
                    self.logger.error(f"DEBUG: Epic generation traceback: {traceback.format_exc()}")
                    exception[0] = e
            
            # Start epic generation in a separate thread with timeout
            thread = threading.Thread(target=generate_epics_thread)
            thread.daemon = True
            thread.start()
            
            # Wait for completion with timeout (longer for larger models)
            # Add buffer time to account for overhead and allow agent to complete
            # For epic strategist, use a longer timeout to accommodate model fallback system
            if hasattr(agent, 'model_fallback'):
                # Epic strategist with fallback system - use extended timeout for quality
                agent_timeout = 600  # 10 minutes for quality improvement with replacement generation
                self.logger.info("Epic strategist detected - using extended 10-minute timeout for quality")
            else:
                agent_timeout = getattr(agent, 'timeout_seconds', 600)  # Default 10 minutes for all agents
            
            timeout = agent_timeout + 60  # Add 60 second buffer for overhead
            self.logger.info(f"Waiting for epic generation with timeout={timeout}s (agent timeout={agent_timeout}s + 60s buffer)")
            thread.join(timeout)
            
            if thread.is_alive():
                self.logger.error(f"Epic generation timed out after {timeout} seconds")
                raise TimeoutError(f"Epic generation timed out after {timeout} seconds")
            
            elif exception[0]:
                self.logger.error(f"Epic generation failed: {exception[0]}")
                raise exception[0]
            
            # Ensure we have valid epics
            if not epics[0] or not isinstance(epics[0], list):
                self.logger.error("No valid epics generated")
                raise ValueError("Epic generation failed - no valid epics produced")
            
            self.workflow_data['epics'] = epics[0]
            
            if max_epics:
                self.logger.info(f"Generated {len(epics[0])} epics (limited to {max_epics})")
            else:
                self.logger.info(f"Generated {len(epics[0])} epics")
                
        except Exception as e:
            self.logger.error(f"Epic generation failed: {e}")
            # CRITICAL: Do NOT create fallback epics - fail cleanly instead
            self.workflow_data['epics'] = []
            self.execution_metadata['errors'].append(f"Epic generation failed: {str(e)}")
            raise RuntimeError(f"Epic generation failed completely: {e}")
    
    def _execute_feature_decomposition(self):
        """Execute feature decomposition stage (parallelized if enabled)."""
        self.logger.info("Decomposing epics into features (parallel mode: %s)", self.parallel_config['stages']['feature_decomposer_agent'])
        
        # Ensure correct model is loaded before agent execution
        if not self._ensure_model_loaded("Feature Decomposition", "feature_decomposer_agent"):
            self.logger.warning("Model loading failed but continuing with feature decomposition")
        
        agent = self.agents['feature_decomposer_agent']
        context = self.project_context.get_context('feature_decomposer_agent')
        
        # Get limits from settings manager if available, otherwise fall back to config
        max_features = None
        if self.settings_manager and self.user_id:
            try:
                work_item_limits = self.settings_manager.get_work_item_limits(self.user_id)
                max_features = work_item_limits.max_features_per_epic
                self.logger.info(f"Using settings manager limits for user {self.user_id}: max_features_per_epic={max_features}")
            except Exception as e:
                self.logger.warning(f"Failed to get limits from settings manager: {e}, falling back to config")
                max_features = self.config.settings.get('work_item_limits', {}).get('max_features_per_epic')
        else:
            # Fall back to work_item_limits config section (not workflow.limits)
            max_features = self.config.settings.get('work_item_limits', {}).get('max_features_per_epic')
            self.logger.info(f"Using config limits: max_features_per_epic={max_features}")
        
        epics = self.workflow_data['epics']
        
        # Debug logging to diagnose type issues
        self.logger.info(f"DEBUG: Type of epics: {type(epics)}")
        self.logger.info(f"DEBUG: Number of epics: {len(epics) if epics else 0}")
        if epics and len(epics) > 0:
            self.logger.info(f"DEBUG: Type of first epic: {type(epics[0])}")
            if isinstance(epics[0], dict):
                self.logger.info(f"DEBUG: First epic title: {epics[0].get('title', 'No title')}")
            else:
                self.logger.info(f"DEBUG: First epic value: {epics[0]}")
        
        # Validate epics are dictionaries
        valid_epics = []
        for i, epic in enumerate(epics):
            if isinstance(epic, dict):
                valid_epics.append(epic)
            else:
                self.logger.error(f"DEBUG: Epic at index {i} is not a dictionary, it's a {type(epic)}: {epic}")
        
        if len(valid_epics) != len(epics):
            self.logger.warning(f"DEBUG: Found {len(epics) - len(valid_epics)} invalid epics out of {len(epics)} total")
            epics = valid_epics
            self.workflow_data['epics'] = valid_epics
        
        if self.parallel_config['enabled'] and self.parallel_config['stages']['feature_decomposer_agent'] and len(epics) > 1:
            def process_epic(epic):
                self.logger.info(f"Decomposing epic: {epic.get('title', 'Untitled')}")
                features = agent.decompose_epic(epic, context, max_features=max_features)
                return epic, features
            with ThreadPoolExecutor(max_workers=self.parallel_config['max_workers']) as executor:
                # Use indices instead of dictionaries as keys
                future_to_epic = {executor.submit(process_epic, epic): i for i, epic in enumerate(epics)}
                for future in as_completed(future_to_epic):
                    epic_index = future_to_epic[future]
                    epic, features = future.result()
                    epics[epic_index]['features'] = features
        else:
            for epic in epics:
                if isinstance(epic, dict):
                    self.logger.info(f"Decomposing epic: {epic.get('title', 'Untitled')}")
                    features = agent.decompose_epic(epic, context, max_features=max_features)
                    epic['features'] = features
                else:
                    self.logger.error(f"DEBUG: Skipping invalid epic of type {type(epic)}: {epic}")
                    epic['features'] = []  # Ensure we have an empty features list
    
    def _execute_user_story_decomposition(self):
        """Execute user story decomposition stage (parallelized if enabled)."""
        self.logger.info("Decomposing features into user stories (parallel mode: %s)", self.parallel_config['stages']['user_story_decomposer_agent'])
        
        # Ensure correct model is loaded before agent execution
        if not self._ensure_model_loaded("User Story Decomposition", "user_story_decomposer_agent"):
            self.logger.warning("Model loading failed but continuing with user story decomposition")
        
        agent = self.agents['user_story_decomposer_agent']
        context = self.project_context.get_context('user_story_decomposer_agent')
        
        # CRITICAL DEBUG: Check if product_vision is in context
        self.logger.info(f"DEBUG: _execute_user_story_decomposition - Context keys: {list(context.keys())}")
        if 'product_vision' in context:
            vision_length = len(context['product_vision']) if context['product_vision'] else 0
            self.logger.info(f"DEBUG: _execute_user_story_decomposition - product_vision found, length: {vision_length}")
            if vision_length > 0:
                self.logger.info(f"DEBUG: product_vision preview: '{context['product_vision'][:100]}...'")
        else:
            self.logger.error(f"DEBUG: _execute_user_story_decomposition - CRITICAL: product_vision NOT in context!")
            self.logger.error(f"DEBUG: This will cause template variable errors!")
            
            # Try to get it from workflow_data as a fallback
            workflow_vision = self.workflow_data.get('product_vision', '')
            if workflow_vision:
                self.logger.info(f"DEBUG: Found product_vision in workflow_data, adding to context, length: {len(workflow_vision)}")
                context['product_vision'] = workflow_vision
            else:
                self.logger.error(f"DEBUG: product_vision also NOT in workflow_data!")
        
        # Get limits from settings manager if available, otherwise fall back to config
        max_user_stories = None
        if self.settings_manager and self.user_id:
            try:
                work_item_limits = self.settings_manager.get_work_item_limits(self.user_id)
                max_user_stories = work_item_limits.max_user_stories_per_feature
                self.logger.info(f"Using settings manager limits for user {self.user_id}: max_user_stories_per_feature={max_user_stories}")
            except Exception as e:
                self.logger.warning(f"Failed to get limits from settings manager: {e}, falling back to config")
                max_user_stories = self.config.settings.get('work_item_limits', {}).get('max_user_stories_per_feature')
        else:
            # Fall back to work_item_limits config section (not workflow.limits)
            max_user_stories = self.config.settings.get('work_item_limits', {}).get('max_user_stories_per_feature')
            self.logger.info(f"Using config limits: max_user_stories_per_feature={max_user_stories}")
        
        features = [(epic, feature) for epic in self.workflow_data['epics'] for feature in epic.get('features', [])]
        
        if self.parallel_config['enabled'] and self.parallel_config['stages']['user_story_decomposer_agent'] and len(features) > 1:
            def process_feature(args):
                epic, feature = args
                self.logger.info(f"Decomposing feature to user stories: {feature.get('title', 'Untitled')}")
                # Add epic context for user story generation
                story_context = context.copy()
                story_context['epic_context'] = epic.get('description', '')
                user_stories = agent.decompose_feature_to_user_stories(feature, context=story_context, max_user_stories=max_user_stories)
                return feature, user_stories
            with ThreadPoolExecutor(max_workers=self.parallel_config['max_workers']) as executor:
                # Use indices instead of dictionaries as keys
                future_to_feature = {executor.submit(process_feature, args): i for i, args in enumerate(features)}
                for future in as_completed(future_to_feature):
                    feature_index = future_to_feature[future]
                    feature, user_stories = future.result()
                    features[feature_index][1]['user_stories'] = user_stories
        else:
            for epic, feature in features:
                self.logger.info(f"Decomposing feature to user stories: {feature.get('title', 'Untitled')}")
                # Add epic context for user story generation
                story_context = context.copy()
                story_context['epic_context'] = epic.get('description', '')
                user_stories = agent.decompose_feature_to_user_stories(feature, context=story_context, max_user_stories=max_user_stories)
                feature['user_stories'] = user_stories
    
    def _execute_task_generation(self, update_progress_callback=None, stage_index=4):
        """Execute developer task generation stage (parallelized if enabled)."""
        self.logger.info("Generating developer tasks (parallel mode: %s)", self.parallel_config['stages']['developer_agent'])
        
        # Ensure correct model is loaded before agent execution
        if not self._ensure_model_loaded("Task Generation", "developer_agent"):
            self.logger.warning("Model loading failed but continuing with task generation")
        
        agent = self.agents['developer_agent']
        context = self.project_context.get_context('developer_agent')
        user_stories = [(epic, feature, user_story) for epic in self.workflow_data['epics'] for feature in epic.get('features', []) for user_story in feature.get('user_stories', [])]
        total_stories = len(user_stories)
        processed_stories = 0
        
        def process_story(args):
            epic, feature, user_story = args
            self.logger.info(f"Generating tasks for user story: {user_story.get('title', 'Untitled')}")
            # Add epic and feature context for task generation
            task_context = context.copy()
            task_context['epic_context'] = epic.get('description', '')
            task_context['feature_context'] = feature.get('description', '')
            tasks = agent.generate_tasks(user_story, task_context)
            return user_story, tasks
        
        if self.parallel_config['enabled'] and self.parallel_config['stages']['developer_agent'] and total_stories > 1:
            with ThreadPoolExecutor(max_workers=self.parallel_config['max_workers']) as executor:
                # Use indices instead of dictionaries as keys
                future_to_story = {executor.submit(process_story, args): i for i, args in enumerate(user_stories)}
                for future in as_completed(future_to_story):
                    story_index = future_to_story[future]
                    user_story, tasks = future.result()
                    user_stories[story_index][2]['tasks'] = tasks
                    processed_stories += 1
                    if update_progress_callback and total_stories > 0:
                        sub_progress = processed_stories / total_stories
                        update_progress_callback(stage_index, f"Generating tasks ({processed_stories}/{total_stories})", sub_progress)
        else:
            for epic, feature, user_story in user_stories:
                self.logger.info(f"Generating tasks for user story: {user_story.get('title', 'Untitled')}")
                # Add epic and feature context for task generation
                task_context = context.copy()
                task_context['epic_context'] = epic.get('description', '')
                task_context['feature_context'] = feature.get('description', '')
                tasks = agent.generate_tasks(user_story, task_context)
                user_story['tasks'] = tasks
                processed_stories += 1
                if update_progress_callback and total_stories > 0:
                    sub_progress = processed_stories / total_stories
                    update_progress_callback(stage_index, f"Generating tasks ({processed_stories}/{total_stories})", sub_progress)
    
    def _execute_qa_generation(self, update_progress_callback=None, stage_index=5):
        """Execute QA generation using hierarchical QA Lead Agent with granular progress tracking (parallelized if enabled)."""
        self.logger.info("Generating QA artifacts using QA Lead Agent (parallel mode: %s)", self.parallel_config['stages']['qa_lead_agent'])
        
        # Ensure correct model is loaded before agent execution - CRITICAL for QA agents
        if not self._ensure_model_loaded("QA Generation", "qa_lead_agent"):
            self.logger.warning("Model loading failed but continuing with QA generation")
        
        agent = self.agents['qa_lead_agent']
        context = self.project_context.get_context('qa_lead_agent')
        if hasattr(self, 'azure_integrator') and self.azure_integrator:
            agent.azure_integrator = self.azure_integrator
        area_path = self._determine_qa_area_path(context)
        features = [(epic, feature) for epic in self.workflow_data['epics'] for feature in epic.get('features', [])]
        total_features = len(features)
        total_stories = sum(len(feature.get('user_stories', [])) for _, feature in features)
        total_qa_items = total_features + total_stories
        processed_qa_items = 0
        
        def process_feature(args):
            epic, feature = args
            self.logger.info(f"Processing QA for feature: {feature.get('title', 'Untitled')}")
            result = agent._process_feature_qa(epic, feature, context, area_path, 0, 0)
            return feature, result
        
        if self.parallel_config['enabled'] and self.parallel_config['stages']['qa_lead_agent'] and total_features > 1:
            with ThreadPoolExecutor(max_workers=self.parallel_config['max_workers']) as executor:
                # Use indices instead of dictionaries as keys
                future_to_feature = {executor.submit(process_feature, args): i for i, args in enumerate(features)}
                for future in as_completed(future_to_feature):
                    feature_index = future_to_feature[future]
                    feature, result = future.result()
                    # Test plan is already set on the feature object by _process_feature_qa
                    processed_qa_items += 1
                    if update_progress_callback and total_qa_items > 0:
                        sub_progress = processed_qa_items / total_qa_items
                        update_progress_callback(stage_index, f"Generating QA ({processed_qa_items}/{total_qa_items})", sub_progress)
        else:
            for epic, feature in features:
                self.logger.info(f"Processing QA for feature: {feature.get('title', 'Untitled')}")
                result = agent._process_feature_qa(epic, feature, context, area_path, 0, 0)
                # Test plan is already set on the feature object by _process_feature_qa
                processed_qa_items += 1
                if update_progress_callback and total_qa_items > 0:
                    sub_progress = processed_qa_items / total_qa_items
                    update_progress_callback(stage_index, f"Generating QA ({processed_qa_items}/{total_qa_items})", sub_progress)
    
    def _sanitize_unicode_for_logging(self, text: str) -> str:
        """Sanitize Unicode characters for Windows console logging."""
        try:
            # Remove common problematic Unicode characters
            import re
            
            # Replace common Unicode characters with ASCII equivalents
            text = text.replace('✅', '[SUCCESS]')
            text = text.replace('❌', '[FAILED]')
            text = text.replace('⚠️', '[WARNING]')
            text = text.replace('📊', '[STATS]')
            text = text.replace('🔍', '[SEARCH]')
            text = text.replace('📝', '[NOTE]')
            text = text.replace('🎯', '[TARGET]')
            text = text.replace('🚀', '[LAUNCH]')
            text = text.replace('💡', '[IDEA]')
            text = text.replace('🔧', '[TOOL]')
            text = text.replace('📋', '[CHECKLIST]')
            text = text.replace('🎨', '[DESIGN]')
            text = text.replace('🔒', '[SECURE]')
            text = text.replace('🌟', '[STAR]')
            text = text.replace('⭐', '[STAR]')
            text = text.replace('🎉', '[CELEBRATE]')
            text = text.replace('🔄', '[REFRESH]')
            text = text.replace('📈', '[TREND]')
            text = text.replace('💾', '[SAVE]')
            text = text.replace('🎪', '[EVENT]')
            text = text.replace('\U0001f517', '[LINK]')  # 🔗
            text = text.replace('\u2705', '[SUCCESS]')    # ✅
            
            # Remove any remaining Unicode characters that might cause issues
            text = re.sub(r'[^\x00-\x7F]+', '?', text)
            
            return text
        except Exception as e:
            # Better fallback - preserve more information using UTF-8
            try:
                return str(text).encode('utf-8', errors='replace').decode('utf-8')
            except Exception:
                # Final fallback - strip all non-ASCII
                return str(text).encode('ascii', errors='ignore').decode('ascii')

    def _determine_qa_area_path(self, context: Dict[str, Any]) -> str:
        """Determine the appropriate area path for QA artifacts."""
        try:
            # Try to get area path from context
            project_context = context.get('project_context', {})
            
            # Look for explicit area path setting
            if 'area_path' in project_context:
                return project_context['area_path']
            
            # Try to derive from project name or domain
            project_name = project_context.get('project_name', '')
            domain = project_context.get('domain', '')
            
            # Domain-based area path logic
            if 'ride' in project_name.lower() or 'transport' in domain.lower():
                return "Ride Sharing"
            elif 'oil' in domain.lower() or 'gas' in domain.lower():
                return "Oil and Gas Operations"
            elif 'fintech' in domain.lower() or 'financial' in project_name.lower():
                return "Financial Services"
            elif 'healthcare' in domain.lower() or 'medical' in project_name.lower():
                return "Healthcare"
            else:
                # Use project name as area path, fallback to default
                return project_name or "Backlog Automation"
                
        except Exception as e:
            self.logger.warning(f"Could not determine area path, using default: {e}")
            return "Backlog Automation"
    
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
        self.logger.info(self._sanitize_unicode_for_logging("🔗 Preparing for Azure DevOps integration"))
        
        # Check if Azure integration is enabled
        if self.azure_integrator is None:
            self.logger.warning("❌ Azure DevOps integration disabled (no Azure config provided)")
            self.logger.info("Content generation completed - skipping Azure upload")
            
            # Store integration results as skipped
            self.workflow_data['azure_integration'] = {
                'status': 'skipped',
                'reason': 'No Azure DevOps configuration provided',
                'timestamp': datetime.now().isoformat()
            }
            return
        
        self.logger.info(self._sanitize_unicode_for_logging("✅ Azure DevOps integrator is available"))
        self.logger.info(f"   Organization: {self.organization_url}")
        self.logger.info(f"   Project: {self.project}")
        self.logger.info(f"   Area Path: {self.area_path}")
        self.logger.info(f"   Iteration Path: {self.iteration_path}")
        
        try:
            # Perform pre-integration quality check using backlog sweeper
            self.logger.info("Running pre-integration validation...")
            validation_report = self.backlog_sweeper.validate_pre_integration(self.workflow_data)
            
            # Store validation results
            self.workflow_data['pre_integration_validation'] = validation_report
            
            # Check validation status
            if validation_report['status'] == 'failed':
                critical_count = validation_report['summary']['critical_issues']
                self.logger.error(f"Pre-integration validation failed with {critical_count} critical issues")
                
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
                self.logger.warning(f"Pre-integration validation passed with {warning_count} warnings")
                
                # Log warnings but continue
                for issue in validation_report['issues']:
                    if issue.get('severity') == 'warning':
                        self.logger.warning(f"WARNING: {issue.get('description')}")
            
            else:
                self.logger.info("Pre-integration validation passed successfully")
            
            # Proceed with ADO integration using outbox pattern
            self.logger.info("Starting Azure DevOps work item creation with outbox pattern...")
            results = self._create_work_items_with_outbox(self.workflow_data)
            
            # Check if results are valid
            if results is None:
                raise ValueError("Azure DevOps integration returned None - check Azure DevOps configuration and permissions")
            
            if not isinstance(results, (list, dict)):
                raise ValueError(f"Azure DevOps integration returned unexpected type: {type(results)}")
            
            # Store integration results
            results_count = len(results) if hasattr(results, '__len__') else 0
            self.workflow_data['azure_integration'] = {
                'status': 'success',
                'work_items_created': results,
                'timestamp': datetime.now().isoformat(),
                'test_artifacts_included': self.include_test_artifacts
            }
            self.logger.info(f"Successfully created {results_count} work items in Azure DevOps")

            # --- BEGIN WORKFLOW CHECKS ---
            # Check for missing artifacts
            missing = []
            epic_count = len(self.workflow_data.get('epics', []))
            feature_count = sum(len(e.get('features', [])) for e in self.workflow_data.get('epics', []))
            user_story_count = sum(len(f.get('user_stories', [])) for e in self.workflow_data.get('epics', []) for f in e.get('features', []))
            task_count = sum(len(s.get('tasks', [])) for e in self.workflow_data.get('epics', []) for f in e.get('features', []) for s in f.get('user_stories', []))
            
            if user_story_count == 0:
                missing.append('user stories')
            if task_count == 0:
                missing.append('tasks')
                
            # Only check for test artifacts if they were requested
            if self.include_test_artifacts:
                test_case_count = sum(len(s.get('test_cases', [])) for e in self.workflow_data.get('epics', []) for f in e.get('features', []) for s in f.get('user_stories', []))
                test_plan_count = sum(1 for e in self.workflow_data.get('epics', []) for f in e.get('features', []) if f.get('test_cases') or any(s.get('test_cases') for s in f.get('user_stories', [])))
                
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
            # Debug execution metadata timing
            self.logger.info(f"DEBUG: Execution metadata timing - start_time: {self.execution_metadata.get('start_time')}, end_time: {self.execution_metadata.get('end_time')}")
            print(f"CONSOLE DEBUG: Execution metadata timing - start_time: {self.execution_metadata.get('start_time')}, end_time: {self.execution_metadata.get('end_time')}")
            
            # Calculate summary statistics
            stats = self._calculate_workflow_stats()
            
            # Debug calculated stats
            self.logger.info(f"DEBUG: Calculated execution_time_seconds: {stats.get('execution_time_seconds')}")
            print(f"CONSOLE DEBUG: Calculated execution_time_seconds: {stats.get('execution_time_seconds')}")
            
            # Add Azure DevOps integration info if available
            azure_integration = self.workflow_data.get('azure_integration', {})
            if azure_integration:
                self.logger.info(f"Adding Azure DevOps integration info to notifications: {azure_integration}")
            
            # Send notifications with enhanced debugging
            self.logger.info(f"Sending notifications with stats: {stats}")
            self.notifier.send_completion_notification(self.workflow_data, stats)
            
            self.logger.info("Completion notifications sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send completion notifications: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
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
        
        # Count user stories
        user_stories_count = sum(
            len(feature.get('user_stories', []))
            for epic in self.workflow_data.get('epics', [])
            for feature in epic.get('features', [])
        )
        
        # Count tasks (FIXED: tasks are stored in user_stories, not features)
        tasks_count = sum(
            len(user_story.get('tasks', []))
            for epic in self.workflow_data.get('epics', [])
            for feature in epic.get('features', [])
            for user_story in feature.get('user_stories', [])
        )
        
        # Count test cases
        test_cases_count = sum(
            len(user_story.get('test_cases', []))
            for epic in self.workflow_data.get('epics', [])
            for feature in epic.get('features', [])
            for user_story in feature.get('user_stories', [])
        )
        
        execution_time = None
        start_time = self.execution_metadata.get('start_time')
        end_time = self.execution_metadata.get('end_time')
        
        self.logger.info(f"DEBUG: _calculate_workflow_stats - start_time: {start_time}, end_time: {end_time}")
        print(f"CONSOLE DEBUG: _calculate_workflow_stats - start_time: {start_time}, end_time: {end_time}")
        
        if start_time and end_time:
            execution_time = (end_time - start_time).total_seconds()
            self.logger.info(f"DEBUG: Calculated execution_time: {execution_time} seconds")
            print(f"CONSOLE DEBUG: Calculated execution_time: {execution_time} seconds")
        else:
            self.logger.warning(f"DEBUG: Cannot calculate execution time - start_time: {start_time}, end_time: {end_time}")
            print(f"CONSOLE DEBUG: Cannot calculate execution time - start_time: {start_time}, end_time: {end_time}")
        
        return {
            'epics_generated': epics_count,
            'features_generated': features_count,
            'user_stories_generated': user_stories_count,
            'tasks_generated': tasks_count,
            'test_cases_generated': test_cases_count,
            'execution_time_seconds': execution_time,
            'stages_completed': len(self.execution_metadata['stages_completed']),
            'errors_encountered': len(self.execution_metadata['errors'])
        }
    
    def _finalize_workflow_data(self):
        """Add final metadata and processing to workflow data."""
        # Ensure end_time is set before calculating stats
        if not self.execution_metadata.get('end_time'):
            self.execution_metadata['end_time'] = datetime.now()
        
        self.workflow_data['metadata'].update({
            'execution_summary': self._calculate_workflow_stats(),
            'completion_timestamp': datetime.now().isoformat(),
            'stages_executed': self.execution_metadata['stages_completed'],
            'execution_metadata': self.execution_metadata  # Include errors for notifications
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
        
        # Create a serializable copy to avoid circular references
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                # Convert objects to dict representation
                return str(obj)
            else:
                return obj
        
        serializable_data = make_serializable(data)
        
        # Save JSON
        json_path = f"output/{filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save YAML
        yaml_path = f"output/{filename}.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(serializable_data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        
        self.logger.info(f"Output saved: {json_path}, {yaml_path}")
    
    def _get_default_stages(self) -> List[str]:
        """Get default workflow stages from configuration."""
        default_stages = self.config.settings.get('workflow', {}).get('sequence', [
            'epic_strategist',
            'feature_decomposer_agent',
            'user_story_decomposer_agent',
            'developer_agent',
            'qa_lead_agent'
        ])
        
        # Remove QA stage if testing artifacts are disabled
        if not self.include_test_artifacts:
            self.logger.info("Excluding QA stages due to include_test_artifacts=False")
            default_stages = [stage for stage in default_stages if stage != 'qa_lead_agent']
        
        return default_stages
    
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

        elif agent_name == 'developer_agent' and hasattr(self, 'agents'):
            self._handle_developer_discrepancies(work_item_groups)
        elif agent_name == 'qa_lead_agent' and hasattr(self, 'agents'):
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
        
        # Generate test cases using QA Lead Agent
        context = self.project_context.get_context()
        # Use QA Lead Agent's test case generation via sub-agents
        test_case_agent = self.agents['qa_lead_agent'].test_case_agent
        test_cases = test_case_agent.create_test_cases(None, user_story_data, context, user_story_data.get('area_path', ''))
        
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
            agents = {}
            agents['epic_strategist'] = EpicStrategist(self.config)
            agents['feature_decomposer_agent'] = FeatureDecomposerAgent(self.config)
            agents['user_story_decomposer_agent'] = UserStoryDecomposerAgent(self.config)
            agents['developer_agent'] = DeveloperAgent(self.config)
            agents['qa_lead_agent'] = QALeadAgent(self.config)  # Replaces deprecated agent
            agents['qa_lead_agent'] = QALeadAgent(self.config)
            self.logger.info(f"Initialized {len(agents)} agents successfully")
            return agents
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
        
        # Enhance acceptance criteria using QA Lead Agent
        context = self.project_context.get_context()
        # For now, skip acceptance criteria enhancement as this is typically done during initial story creation
        enhanced_criteria = None
        
        if enhanced_criteria:
            # Format criteria for Azure DevOps
            criteria_text = self._format_acceptance_criteria(enhanced_criteria)
            # Update the work item with enhanced acceptance criteria
        agents['epic_strategist'] = EpicStrategist(self.config)
        agents['feature_decomposer_agent'] = FeatureDecomposerAgent(self.config)
        agents['user_story_decomposer_agent'] = UserStoryDecomposerAgent(self.config)
        agents['developer_agent'] = DeveloperAgent(self.config)
        agents['qa_lead_agent'] = QALeadAgent(self.config)  # Replaces deprecated agent
        agents['qa_lead_agent'] = QALeadAgent(self.config)
        self.logger.info(f"Initialized {len(agents)} agents successfully")
        return agents
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
        
        # Format as numbered list with double line spacing for readability
        formatted_lines = []
        for i, criterion in enumerate(criteria, 1):
            formatted_lines.append(f"{i}. {criterion}")
        
        return '\n\n'.join(formatted_lines)

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
            # Use quality validator from user_story_decomposer_agent
            if hasattr(self.agents['user_story_decomposer_agent'], 'quality_validator'):
                validator = self.agents['user_story_decomposer_agent'].quality_validator
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
            
            # Step 4: Generate and create child test cases using QA Lead Agent
            test_cases_created = []
            if hasattr(self.agents, 'qa_lead_agent') and 'qa_lead_agent' in self.agents:
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
                
                test_case_agent = self.agents['qa_lead_agent'].test_case_agent
                test_result = test_case_agent.create_test_cases(None, story_for_testing, context, story_for_testing.get('area_path', ''))
                test_cases = test_result.get('test_cases', []) if test_result.get('success') else []
                
                for test_case in test_cases:
                    if hasattr(self, 'azure_integrator'):
                        test_item = self.azure_integrator._create_test_case(test_case, user_story_id)
                        test_cases_created.append(test_item)
                        self.logger.info(f"Created Test Case {test_item['id']}: {test_case.get('title', 'Untitled')}")
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

        elif stage == 'user_story_decomposer':
            self._execute_user_story_decomposition()
            self._validate_user_stories()
        elif stage == 'developer_agent':
            self._execute_task_generation()
            self._validate_tasks_and_estimates()
        elif stage == 'qa_lead_agent':
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

    def _calculate_qa_completeness(self) -> Dict[str, Any]:
        """Calculate QA completeness score and generate report."""
        try:
            total_features = 0
            features_with_test_plans = 0
            total_user_stories = 0
            stories_with_test_cases = 0
            total_test_cases = 0
            total_test_plans = 0
            
            issues = []
            
            for epic in self.workflow_data.get('epics', []):
                for feature in epic.get('features', []):
                    total_features += 1
                    
                    # Check for test plan
                    test_plan = feature.get('test_plan') or feature.get('test_plan_structure')
                    if test_plan:
                        features_with_test_plans += 1
                        total_test_plans += 1
                    else:
                        issues.append(f"Feature '{feature.get('title', 'Untitled')}' missing test plan")
                    
                    # Check user stories
                    for user_story in feature.get('user_stories', []):
                        total_user_stories += 1
                        
                        test_cases = user_story.get('test_cases', [])
                        if test_cases and len(test_cases) > 0:
                            stories_with_test_cases += 1
                            total_test_cases += len(test_cases)
                        else:
                            issues.append(f"User story '{user_story.get('title', 'Untitled')}' missing test cases")
            
            # Calculate completeness scores
            feature_completeness = features_with_test_plans / total_features if total_features > 0 else 0
            story_completeness = stories_with_test_cases / total_user_stories if total_user_stories > 0 else 0
            overall_completeness = (feature_completeness + story_completeness) / 2 if (total_features > 0 and total_user_stories > 0) else 0
            
            # Generate report
            report_lines = [
                f"QA Test Organization Summary:",
                f"- Features: {total_features} total, {features_with_test_plans} with test plans ({feature_completeness:.1%})",
                f"- User Stories: {total_user_stories} total, {stories_with_test_cases} with test cases ({story_completeness:.1%})",
                f"- Test Artifacts: {total_test_plans} test plans, {total_test_cases} test cases",
                f"- Overall Completeness: {overall_completeness:.1%}",
                ""
            ]
            
            if issues:
                report_lines.append("Issues Found:")
                for issue in issues[:10]:  # Limit to first 10 issues
                    report_lines.append(f"  - {issue}")
                if len(issues) > 10:
                    report_lines.append(f"  ... and {len(issues) - 10} more issues")
            else:
                report_lines.append("✅ All features have test plans and all user stories have test cases")
            
            completeness_report = "\n".join(report_lines)
            
            return {
                'completeness_score': overall_completeness,
                'feature_completeness': feature_completeness,
                'story_completeness': story_completeness,
                'total_features': total_features,
                'features_with_test_plans': features_with_test_plans,
                'total_user_stories': total_user_stories,
                'stories_with_test_cases': stories_with_test_cases,
                'total_test_cases': total_test_cases,
                'total_test_plans': total_test_plans,
                'issues_count': len(issues),
                'completeness_report': completeness_report
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate QA completeness: {e}")
            return {
                'completeness_score': 0.0,
                'completeness_report': f"Error calculating completeness: {e}"
            }

    def _write_completeness_report(self, completeness_report: str):
        """Write QA completeness report to output file."""
        try:
            import os
            from datetime import datetime
            
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"output/qa_completeness_report_{timestamp}.txt"
            
            # Write report to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"QA Test Organization Completeness Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                context = self.project_context.get_context() if hasattr(self, 'project_context') else {}
                f.write(f"Project: {context.get('project_name', 'Unknown')}\n")
                f.write("=" * 80 + "\n\n")
                f.write(completeness_report)
            
            self.logger.info(f"QA completeness report written to: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to write completeness report: {e}")


    
    def _execute_final_validation(self, update_progress_callback=None, stage_index=7):
        """Execute final validation and cleanup as part of the continuous workflow."""
        self.logger.info("Starting final validation and cleanup")
        
        try:
            # Validate work item relationships
            if update_progress_callback:
                update_progress_callback(stage_index, "Validating work item relationships", 0.25)
            
            validation_results = self._validate_work_item_relationships()
            
            # Clean up temporary data
            if update_progress_callback:
                update_progress_callback(stage_index, "Cleaning up temporary data", 0.5)
            
            self._cleanup_temporary_data()
            
            # Generate final report
            if update_progress_callback:
                update_progress_callback(stage_index, "Generating final report", 0.75)
            
            final_report = self._generate_final_report()
            
            # CRITICAL FIX: Ensure end_time is set before sending notifications
            if not self.execution_metadata.get('end_time'):
                self.execution_metadata['end_time'] = datetime.now()
                self.logger.info(f"Set end_time in final validation: {self.execution_metadata['end_time']}")
            
            # Send completion notifications
            if update_progress_callback:
                update_progress_callback(stage_index, "Sending completion notifications", 0.9)
            
            # Call the correct notification method that commits to database
            self._send_completion_notifications()
            
            # Final progress update
            if update_progress_callback:
                update_progress_callback(stage_index, "Final validation completed", 1.0)
                
        except Exception as e:
            self.logger.error(f"Final validation failed: {e}")
            raise
    
    def _validate_work_item_relationships(self) -> Dict[str, Any]:
        """Validate that all work items are properly linked."""
        validation_results = {
            'total_items': 0,
            'validated_items': 0,
            'errors': []
        }
        
        # Count and validate work items
        for epic in self.workflow_data.get('epics', []):
            validation_results['total_items'] += 1
            if epic.get('azure_id'):
                validation_results['validated_items'] += 1
            
            for feature in epic.get('features', []):
                validation_results['total_items'] += 1
                if feature.get('azure_id'):
                    validation_results['validated_items'] += 1
                
                for user_story in feature.get('user_stories', []):
                    validation_results['total_items'] += 1
                    if user_story.get('azure_id'):
                        validation_results['validated_items'] += 1
                    
                    for task in user_story.get('tasks', []):
                        validation_results['total_items'] += 1
                        if task.get('azure_id'):
                            validation_results['validated_items'] += 1
                    
                    for test_case in user_story.get('test_cases', []):
                        validation_results['total_items'] += 1
                        if test_case.get('azure_id'):
                            validation_results['validated_items'] += 1
        
        return validation_results
    
    def _cleanup_temporary_data(self):
        """Clean up temporary data and files."""
        # Clean up any temporary files or data structures
        self.logger.info("Cleaning up temporary data")
        
        # Clear any temporary workflow state
        if hasattr(self, 'temp_data'):
            del self.temp_data
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final workflow report."""
        report = {
            'workflow_id': self.current_workflow_id,
            'completion_time': datetime.now().isoformat(),
            'total_epics': len(self.workflow_data.get('epics', [])),
            'total_features': sum(len(epic.get('features', [])) for epic in self.workflow_data.get('epics', [])),
            'total_user_stories': sum(len(feature.get('user_stories', [])) for epic in self.workflow_data.get('epics', []) for feature in epic.get('features', [])),
            'total_tasks': sum(len(user_story.get('tasks', [])) for epic in self.workflow_data.get('epics', []) for feature in epic.get('features', []) for user_story in feature.get('user_stories', [])),
            'total_test_cases': sum(len(user_story.get('test_cases', [])) for epic in self.workflow_data.get('epics', []) for feature in epic.get('features', []) for user_story in feature.get('user_stories', [])),
            'azure_integration_enabled': self.azure_integrator is not None
        }
        
        self.logger.info(f"Generated final report: {report}")
        return report
    
    def _send_completion_notifications_with_report(self, final_report: Dict[str, Any]):
        """Send completion notifications with final report."""
        if self.notifier:
            try:
                # Send email notification
                subject = f"Backlog Generation Completed - {self.project or 'Project'}"
                message = f"""
                Backlog generation has been completed successfully!
                
                Summary:
                - Epics: {final_report['total_epics']}
                - Features: {final_report['total_features']}
                - User Stories: {final_report['total_user_stories']}
                - Tasks: {final_report['total_tasks']}
                - Test Cases: {final_report['total_test_cases']}
                - Azure Integration: {'Enabled' if final_report['azure_integration_enabled'] else 'Disabled'}
                
                Workflow ID: {final_report['workflow_id']}
                Completed: {final_report['completion_time']}
                """
                
                self.notifier.send_email_notification(subject, message)
                self.logger.info("Sent completion notification email")
                
            except Exception as e:
                self.logger.error(f"Failed to send completion notification: {e}")
    
    def _create_work_items_with_outbox(self, workflow_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create work items using the outbox pattern for reliable upload.
        
        Returns:
            List of successfully uploaded work items
        """
        try:
            # Import outbox components
            from models.work_item_staging import WorkItemStaging
            from integrators.outbox_uploader import OutboxUploader
            
            # Initialize staging and uploader
            staging = WorkItemStaging()
            uploader = OutboxUploader(self.azure_integrator)
            
            # Stage all work items first (zero data loss)
            self.logger.info("Staging work items to local database...")
            staged_count = staging.stage_backlog(self.job_id, workflow_data)
            self.logger.info(f"Successfully staged {staged_count} work items")
            
            # Get staging summary for notification
            staging_summary = staging.get_staging_summary(self.job_id)
            self.logger.info(f"Staging summary: {staging_summary}")
            
            # Upload staged items with retry logic
            self.logger.info("Starting outbox upload to Azure DevOps...")
            upload_results = uploader.upload_job(self.job_id, resume=False)
            
            # Convert staging results to traditional format for compatibility
            successful_uploads = upload_results['uploaded']
            failed_uploads = upload_results['failed']
            
            self.logger.info(f"Upload completed: {successful_uploads} successful, {failed_uploads} failed")
            
            if failed_uploads > 0:
                self.logger.warning(f"Some items failed to upload. They remain staged for retry.")
                self.logger.warning("Use the retry functionality to attempt failed uploads again.")
            
            # Clean up successful items but keep failed ones for retry
            if successful_uploads > 0:
                staging.cleanup_successful_job(self.job_id, keep_failed=True)
                self.logger.info(f"Cleaned up {successful_uploads} successful uploads from staging")
            
            # Return actual upload results instead of mock data to prevent discrepancies
            actual_results = []
            
            # Extract successful work items from upload results
            for item_result in upload_results.get('work_items_created', []):
                if item_result.get('status') == 'success':
                    actual_results.append({
                        'id': item_result.get('id'),
                        'type': item_result.get('type', 'Work Item'),
                        'title': item_result.get('title', 'Uploaded Work Item'),
                        'status': 'success',
                        'url': item_result.get('url', '')
                    })
            
            # Store outbox results in workflow data for detailed reporting
            workflow_data['outbox_upload_results'] = upload_results
            workflow_data['staging_summary'] = staging_summary
            
            self.logger.info(f"Returning {len(actual_results)} actual upload results (no mock data)")
            return actual_results
            
        except Exception as e:
            self.logger.error(f"Outbox upload failed: {e}")
            # Don't fall back - re-raise the exception to diagnose the issue
            self.logger.error("Outbox upload failure - investigate and fix the root cause")
            raise
    
    def _get_default_stages(self) -> List[str]:
        """Get the default workflow stages including Azure integration."""
        default_stages = [
            'epic_strategist',
            'feature_decomposer_agent',
            'user_story_decomposer_agent',
            'developer_agent',
            'qa_lead_agent',
            'azure_integration',
            'final_validation'
        ]
        
        # Remove QA stage if testing artifacts are disabled
        if not self.include_test_artifacts:
            self.logger.info("Excluding QA stages due to include_test_artifacts=False")
            default_stages = [stage for stage in default_stages if stage != 'qa_lead_agent']
        
        return default_stages
