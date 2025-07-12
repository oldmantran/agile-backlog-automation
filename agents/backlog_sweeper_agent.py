import os
import sys
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrators.azure_devops_api import AzureDevOpsIntegrator

class BacklogSweeperAgent:
    """
    Agent responsible for monitoring the backlog and reporting discrepancies to the supervisor.
    This agent NEVER modifies work items - it only observes and reports findings.
    
    Key Responsibilities:
    1. Monitor work items for quality, completeness, and compliance
    2. Validate acceptance criteria using INVEST, SMART, BDD principles
    3. Check hierarchical relationships and dependencies
    4. Report specific discrepancies with agent assignment suggestions
    5. Track project metrics and dashboard requirements
    
    The supervisor receives reports and routes remediation to appropriate agents.
    """

    def __init__(self, ado_client, supervisor_callback=None, config=None):
        self.ado_client = ado_client
        self.supervisor_callback = supervisor_callback
        self.config = config
        
        # Load configuration settings
        if config:
            sweeper_config = config.get('agents', {}).get('backlog_sweeper_agent', {})
            acceptance_config = sweeper_config.get('acceptance_criteria', {})
            
            self.min_criteria_count = acceptance_config.get('min_criteria_count', 3)
            self.max_criteria_count = acceptance_config.get('max_criteria_count', 8)
            self.require_bdd_format = acceptance_config.get('require_bdd_format', True)
            self.require_functional_and_nonfunctional = acceptance_config.get('require_functional_and_nonfunctional', True)
            
            severity_config = sweeper_config.get('severity_thresholds', {})
            self.critical_notification_count = severity_config.get('critical_notification_count', 5)
            self.max_discrepancies_per_run = severity_config.get('max_discrepancies_per_run', 100)
            
            # QA-specific validation settings
            self.qa_validation_enabled = sweeper_config.get('qa_validation_enabled', True)
            self.test_organization_validation = sweeper_config.get('test_organization_validation', True)
        else:
            # Default values if no config provided
            self.min_criteria_count = 3
            self.max_criteria_count = 8
            self.require_bdd_format = True
            self.require_functional_and_nonfunctional = True
            self.critical_notification_count = 5
            self.max_discrepancies_per_run = 100
            
            # QA-specific validation defaults
            self.qa_validation_enabled = True
            self.test_organization_validation = True
        
        # Agent assignment mappings for different discrepancy types
        self.agent_assignments = {
            # Epic/Feature level issues
            'missing_epic_title': 'epic_strategist',
            'missing_epic_description': 'epic_strategist', 
            'missing_child_feature': 'epic_strategist',
            'invalid_epic_child': 'epic_strategist',
            'missing_feature_title': 'feature_decomposer_agent',
            'missing_feature_description': 'feature_decomposer_agent',
            'missing_child_user_story': 'user_story_decomposer_agent',
            'invalid_feature_child': 'feature_decomposer_agent',
            
            # User Story level issues
            'missing_story_title': 'user_story_decomposer_agent',
            'missing_or_invalid_story_description': 'user_story_decomposer_agent',
            'missing_acceptance_criteria': 'qa_lead_agent',
            'invalid_acceptance_criteria': 'qa_lead_agent',
            'missing_story_points': 'developer_agent',
            'missing_child_task': 'developer_agent',
            'missing_child_test_case': 'qa_lead_agent',
            
            # Task/Test level issues
            'missing_task_title': 'developer_agent',
            'missing_task_description': 'developer_agent',
            'task_has_children': 'developer_agent',
            'invalid_task_parent': 'developer_agent',
            'missing_test_case_title': 'qa_lead_agent',
            'invalid_test_case_parent': 'qa_lead_agent',
            'missing_test_plan': 'qa_lead_agent',
            'missing_test_suite': 'qa_lead_agent',
            'test_plan_suite_mismatch': 'qa_lead_agent',
            'test_case_suite_mismatch': 'qa_lead_agent',
            
            # Relationship issues
            'relationship_issue': 'feature_decomposer_agent',
            'user_story_missing_tasks': 'developer_agent',
            'orphaned_work_item': 'feature_decomposer_agent',
            
            # Backward compatibility mappings
            'decomposition_agent': 'feature_decomposer_agent'
        }

        # Initialize QA completeness validator if available
        if self.qa_validation_enabled:
            try:
                from utils.qa_completeness_validator import QACompletenessValidator
                self.qa_validator = QACompletenessValidator(config)
            except ImportError:
                self.qa_validator = None

    def report_to_supervisor(self, report):
        """Send structured report to supervisor with agent assignment suggestions."""
        if self.supervisor_callback:
            self.supervisor_callback(report)
        else:
            print("[SUPERVISOR REPORT]")
            import json
            print(json.dumps(report, indent=2))

    def _validate_acceptance_criteria(self, criteria_text: str, wi_id: int, title: str) -> List[Dict[str, Any]]:
        """
        Advanced validation of acceptance criteria using INVEST, SMART, and BDD principles.
        
        Requirements:
        - INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable
        - SMART: Specific, Measurable, Achievable, Relevant, Time-bound
        - BDD: Given-When-Then format where applicable
        - Mix of functional and non-functional criteria
        - 3-8 criteria per story (optimal range)
        
        Returns list of discrepancies found.
        """
        discrepancies = []
        
        if not criteria_text or not criteria_text.strip():
            return [{
                'type': 'missing_acceptance_criteria',
                'work_item_id': wi_id,
                'work_item_type': 'User Story',
                'title': title,
                'description': 'User Story missing acceptance criteria.',
                'severity': 'high',
                'suggested_agent': 'qa_lead_agent'
            }]
        
        # Split criteria into individual items (assuming line breaks or bullet points)
        criteria_lines = [line.strip() for line in criteria_text.split('\n') if line.strip()]
        criteria_items = []
        
        for line in criteria_lines:
            # Handle various bullet formats
            cleaned = re.sub(r'^[-*•]\s*', '', line)
            cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
            if cleaned:
                criteria_items.append(cleaned)
        
        # Check quantity (configurable criteria count)
        if len(criteria_items) < self.min_criteria_count:
            discrepancies.append({
                'type': 'insufficient_acceptance_criteria',
                'work_item_id': wi_id,
                'work_item_type': 'User Story',
                'title': title,
                'description': f'Only {len(criteria_items)} acceptance criteria found. Recommend {self.min_criteria_count}-{self.max_criteria_count} criteria for proper coverage.',
                'severity': 'medium',
                'suggested_agent': 'qa_lead_agent'
            })
        elif len(criteria_items) > self.max_criteria_count:
            discrepancies.append({
                'type': 'excessive_acceptance_criteria',
                'work_item_id': wi_id,
                'work_item_type': 'User Story',
                'title': title,
                'description': f'{len(criteria_items)} acceptance criteria found. Consider breaking story down - recommend {self.min_criteria_count}-{self.max_criteria_count} criteria max.',
                'suggested_agent': 'user_story_decomposer_agent'
            })
        
        # Check for BDD format (if required by configuration)
        if self.require_bdd_format:
            bdd_count = 0
            for criteria in criteria_items:
                if re.search(r'\b(given|when|then)\b', criteria.lower()):
                    bdd_count += 1
            
            if bdd_count == 0 and len(criteria_items) > 0:
                discrepancies.append({
                    'type': 'missing_bdd_format',
                    'work_item_id': wi_id,
                    'work_item_type': 'User Story',
                    'title': title,
                    'description': 'No Given-When-Then format found in acceptance criteria. Consider using BDD format for clarity.',
                    'severity': 'low',
                    'suggested_agent': 'qa_lead_agent'
                })
        
        # Check for functional vs non-functional criteria mix (if required)
        if self.require_functional_and_nonfunctional:
            functional_indicators = ['user can', 'system shall', 'application will', 'feature allows', 'button click', 'form submit']
            nonfunctional_indicators = ['performance', 'response time', 'security', 'usability', 'accessibility', 'reliability', 'scalability']
            
            has_functional = any(any(indicator in criteria.lower() for indicator in functional_indicators) for criteria in criteria_items)
            has_nonfunctional = any(any(indicator in criteria.lower() for indicator in nonfunctional_indicators) for criteria in criteria_items)
            
            if has_functional and not has_nonfunctional:
                discrepancies.append({
                    'type': 'missing_nonfunctional_criteria',
                    'work_item_id': wi_id,
                    'work_item_type': 'User Story',
                    'title': title,
                    'description': 'Consider adding non-functional acceptance criteria (performance, security, usability).',
                    'severity': 'low',
                    'suggested_agent': 'qa_lead_agent'
                })
        
        # Check for vague or unmeasurable criteria
        vague_words = ['better', 'faster', 'easier', 'improved', 'enhanced', 'good', 'bad', 'nice']
        for i, criteria in enumerate(criteria_items):
            if any(vague_word in criteria.lower() for vague_word in vague_words):
                if not re.search(r'\d+|specific|exact|precise', criteria.lower()):
                    discrepancies.append({
                        'type': 'vague_acceptance_criteria',
                        'work_item_id': wi_id,
                        'work_item_type': 'User Story',
                        'title': title,
                        'description': f'Criteria {i+1} contains vague language: "{criteria[:50]}...". Make it more specific and measurable.',
                        'severity': 'medium',
                        'suggested_agent': 'qa_lead_agent'
                    })
        
        return discrepancies

    def scrape_and_validate_work_items(self):
        """
        Monitor all work items for quality, completeness, and compliance.
        Returns structured discrepancies with agent assignment suggestions.
        """
        discrepancies = []
        types = ["Epic", "Feature", "User Story", "Task", "Test Case"]
        all_ids = []
        
        for t in types:
            all_ids.extend(self.ado_client.query_work_items(t))
        
        work_items = self.ado_client.get_work_item_details(all_ids)
        work_items_by_id = {wi['id']: wi for wi in work_items}

        def get_field(wi, field):
            return wi.get('fields', {}).get(field, '')

        for wi in work_items:
            wi_id = wi['id']
            wi_type = get_field(wi, 'System.WorkItemType')
            title = get_field(wi, 'System.Title')
            description = get_field(wi, 'System.Description')
            relations = self.ado_client.get_work_item_relations(wi_id)
            children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            parents = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Reverse']

            # Epic validation rules
            if wi_type == "Epic":
                if not title:
                    discrepancies.append({
                        'type': 'missing_epic_title',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Epic missing title.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_epic_title', 'epic_strategist')
                    })
                    
                if not description:
                    discrepancies.append({
                        'type': 'missing_epic_description',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Epic missing description.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_epic_description', 'epic_strategist')
                    })
                
                # Validate Epic children (should only have Features)
                child_ids = [int(r['url'].split('/')[-1]) for r in children]
                child_types = [get_field(work_items_by_id.get(cid, {}), 'System.WorkItemType') for cid in child_ids]
                
                if not any(ct == 'Feature' for ct in child_types):
                    discrepancies.append({
                        'type': 'missing_child_feature',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Epic missing child Feature.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_child_feature', 'epic_strategist')
                    })
                
                for cid, ct in zip(child_ids, child_types):
                    if ct and ct != 'Feature':
                        discrepancies.append({
                            'type': 'invalid_epic_child',
                            'work_item_id': wi_id,
                            'work_item_type': wi_type,
                            'title': title,
                            'description': f'Epic has invalid child type: {ct} (ID {cid})',
                            'severity': 'medium',
                            'suggested_agent': self.agent_assignments.get('invalid_epic_child', 'epic_strategist')
                        })

            # Feature validation rules
            elif wi_type == "Feature":
                if not title:
                    discrepancies.append({
                        'type': 'missing_feature_title',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Feature missing title.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_feature_title', 'feature_decomposer_agent')
                    })
                    
                if not description:
                    discrepancies.append({
                        'type': 'missing_feature_description',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Feature missing description.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_feature_description', 'feature_decomposer_agent')
                    })
                
                child_ids = [int(r['url'].split('/')[-1]) for r in children]
                child_types = [get_field(work_items_by_id.get(cid, {}), 'System.WorkItemType') for cid in child_ids]
                
                if not any(ct == 'User Story' for ct in child_types):
                    discrepancies.append({
                        'type': 'missing_child_user_story',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Feature missing child User Story.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_child_user_story', 'feature_decomposer_agent')
                    })
                
                for cid, ct in zip(child_ids, child_types):
                    if ct and ct != 'User Story':
                        discrepancies.append({
                            'type': 'invalid_feature_child',
                            'work_item_id': wi_id,
                            'work_item_type': wi_type,
                            'title': title,
                            'description': f'Feature has invalid child type: {ct} (ID {cid})',
                            'severity': 'medium',
                            'suggested_agent': self.agent_assignments.get('invalid_feature_child', 'feature_decomposer_agent')
                        })

            # User Story validation rules (with advanced acceptance criteria validation)
            elif wi_type == "User Story":
                if not title:
                    discrepancies.append({
                        'type': 'missing_story_title',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'User Story missing title.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_story_title', 'user_story_decomposer_agent')
                    })
                
                if not description or 'As a' not in description:
                    discrepancies.append({
                        'type': 'missing_or_invalid_story_description',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'User Story missing or invalid description (should follow "As a..." format).',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_or_invalid_story_description', 'user_story_decomposer_agent')
                    })
                
                # Advanced acceptance criteria validation
                acceptance_criteria = get_field(wi, 'Microsoft.VSTS.Common.AcceptanceCriteria')
                criteria_discrepancies = self._validate_acceptance_criteria(acceptance_criteria, wi_id, title)
                discrepancies.extend(criteria_discrepancies)
                
                # Story points validation
                story_points = get_field(wi, 'Microsoft.VSTS.Scheduling.StoryPoints')
                if not story_points:
                    discrepancies.append({
                        'type': 'missing_story_points',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'User Story missing story points.',
                        'severity': 'medium',
                        'suggested_agent': self.agent_assignments.get('missing_story_points', 'developer_agent')
                    })
                
                # Child validation
                child_ids = [int(r['url'].split('/')[-1]) for r in children]
                child_types = [get_field(work_items_by_id.get(cid, {}), 'System.WorkItemType') for cid in child_ids]
                
                if not any(ct == 'Task' for ct in child_types):
                    discrepancies.append({
                        'type': 'missing_child_task',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'User Story missing child Task.',
                        'severity': 'medium',
                        'suggested_agent': self.agent_assignments.get('missing_child_task', 'developer_agent')
                    })
                
                if not any(ct == 'Test Case' for ct in child_types):
                    discrepancies.append({
                        'type': 'missing_child_test_case',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'User Story missing child Test Case.',
                        'severity': 'medium',
                        'suggested_agent': self.agent_assignments.get('missing_child_test_case', 'qa_lead_agent')
                    })

            # Task validation rules
            elif wi_type == "Task":
                if not title:
                    discrepancies.append({
                        'type': 'missing_task_title',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Task missing title.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_task_title', 'developer_agent')
                    })
                    
                if not description:
                    discrepancies.append({
                        'type': 'missing_task_description',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Task missing description.',
                        'severity': 'medium',
                        'suggested_agent': self.agent_assignments.get('missing_task_description', 'developer_agent')
                    })
                
                if children:
                    discrepancies.append({
                        'type': 'task_has_children',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Task should not have children.',
                        'severity': 'medium',
                        'suggested_agent': self.agent_assignments.get('task_has_children', 'developer_agent')
                    })
                
                if parents:
                    parent_id = int(parents[0]['url'].split('/')[-1])
                    parent_type = get_field(work_items_by_id.get(parent_id, {}), 'System.WorkItemType')
                    if parent_type not in ['User Story', 'Product Backlog Item']:
                        discrepancies.append({
                            'type': 'invalid_task_parent',
                            'work_item_id': wi_id,
                            'work_item_type': wi_type,
                            'title': title,
                            'description': f'Task has invalid parent type: {parent_type} (ID {parent_id})',
                            'severity': 'medium',
                            'suggested_agent': self.agent_assignments.get('invalid_task_parent', 'developer_agent')
                        })

            # Test Case validation rules
            elif wi_type == "Test Case":
                if not title:
                    discrepancies.append({
                        'type': 'missing_test_case_title',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Test Case missing title.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_test_case_title', 'qa_lead_agent')
                    })
                
                if parents:
                    parent_id = int(parents[0]['url'].split('/')[-1])
                    parent_type = get_field(work_items_by_id.get(parent_id, {}), 'System.WorkItemType')
                    if parent_type != 'User Story':
                        discrepancies.append({
                            'type': 'invalid_test_case_parent',
                            'work_item_id': wi_id,
                            'work_item_type': wi_type,
                            'title': title,
                            'description': f'Test Case has invalid parent type: {parent_type} (ID {parent_id})',
                            'severity': 'medium',
                            'suggested_agent': self.agent_assignments.get('invalid_test_case_parent', 'qa_lead_agent')
                        })

        return discrepancies

    def validate_relationships(self):
        """Monitor parent/child links, hierarchy, dependencies, and test case assignments."""
        discrepancies = []
        
        # Query all work items and their relationships
        types = ["Epic", "Feature", "User Story", "Task", "Test Case"]
        all_ids = []
        for t in types:
            all_ids.extend(self.ado_client.query_work_items(t))
        
        work_items = self.ado_client.get_work_item_details(all_ids)
        
        for wi in work_items:
            wi_id = wi['id']
            wi_type = wi.get('fields', {}).get('System.WorkItemType', '')
            title = wi.get('fields', {}).get('System.Title', '')
            
            relations = self.ado_client.get_work_item_relations(wi_id)
            parents = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Reverse']
            
            # Check for orphaned work items (except Epics)
            if wi_type in ['Feature', 'User Story', 'Task', 'Test Case'] and not parents:
                discrepancies.append({
                    'type': 'orphaned_work_item',
                    'work_item_id': wi_id,
                    'work_item_type': wi_type,
                    'title': title,
                    'description': f'{wi_type} has no parent work item.',
                    'severity': 'high',
                    'suggested_agent': self.agent_assignments.get('orphaned_work_item', 'feature_decomposer_agent')
                })
        
        return discrepancies

    def monitor_for_decomposition(self):
        """Monitor work items that require further decomposition."""
        discrepancies = []
        
        # Check for User Stories without Tasks
        user_story_ids = self.ado_client.query_work_items("User Story")
        
        for story_id in user_story_ids:
            relations = self.ado_client.get_work_item_relations(story_id)
            children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            
            # Check if this story has any Task children
            has_tasks = False
            for child in children:
                child_id = int(child['url'].split('/')[-1])
                child_details = self.ado_client.get_work_item_details([child_id])
                if child_details:
                    child_type = child_details[0].get('fields', {}).get('System.WorkItemType', '')
                    if child_type == 'Task':
                        has_tasks = True
                        break
            
            if not has_tasks:
                story_details = self.ado_client.get_work_item_details([story_id])
                story_title = story_details[0].get('fields', {}).get('System.Title', '') if story_details else ''
                
                discrepancies.append({
                    'type': 'user_story_missing_tasks',
                    'work_item_id': story_id,
                    'work_item_type': 'User Story',
                    'title': story_title,
                    'description': 'User Story has no child tasks.',
                    'severity': 'medium',
                    'suggested_agent': self.agent_assignments.get('user_story_missing_tasks', 'developer_agent')
                })
        
        return discrepancies

    def validate_dashboard_requirements(self):
        """Monitor dashboard and reporting requirements."""
        requirements = []
        
        # Check if standard project dashboards exist
        requirements.append({
            'type': 'dashboard_requirement',
            'component': 'burndown_chart',
            'description': 'Verify burndown chart configuration and data freshness',
            'priority': 'medium',
            'suggested_agent': 'developer_agent'
        })
        
        requirements.append({
            'type': 'dashboard_requirement',
            'component': 'cumulative_flow_diagram',
            'description': 'Verify cumulative flow diagram for sprint tracking',
            'priority': 'medium',
            'suggested_agent': 'developer_agent'
        })
        
        requirements.append({
            'type': 'dashboard_requirement',
            'component': 'team_velocity',
            'description': 'Verify team velocity calculations and trending',
            'priority': 'low',
            'suggested_agent': 'developer_agent'
        })
        
        return requirements

    def run_sweep(self):
        """
        Run a comprehensive backlog monitoring sweep and report findings to supervisor.
        This method NEVER modifies work items - only observes and reports.
        """
        discrepancies = []
        dashboard_requirements = []
        
        try:
            # Monitor work item quality and compliance
            self.logger.info("Starting work item validation sweep...")
            work_item_discrepancies = self.scrape_and_validate_work_items()
            discrepancies.extend(work_item_discrepancies)
            
            # Monitor relationships and hierarchy
            self.logger.info("Validating work item relationships...")
            relationship_discrepancies = self.validate_relationships()
            discrepancies.extend(relationship_discrepancies)
            
            # Monitor decomposition needs
            self.logger.info("Monitoring decomposition requirements...")
            decomposition_discrepancies = self.monitor_for_decomposition()
            discrepancies.extend(decomposition_discrepancies)
            
            # Monitor dashboard requirements
            self.logger.info("Checking dashboard requirements...")
            dashboard_requirements = self.validate_dashboard_requirements()
            
        except Exception as e:
            error_discrepancy = {
                'type': 'sweep_error',
                'work_item_id': None,
                'work_item_type': 'System',
                'title': 'Backlog Sweep Error',
                'description': f'Error during backlog sweep: {str(e)}',
                'severity': 'high',
                'suggested_agent': 'supervisor'
            }
            discrepancies.append(error_discrepancy)
        
        # Categorize discrepancies by severity and agent
        high_priority = [d for d in discrepancies if d.get('severity') == 'high']
        medium_priority = [d for d in discrepancies if d.get('severity') == 'medium']
        low_priority = [d for d in discrepancies if d.get('severity') == 'low']
        
        # Group by suggested agent for efficient assignment
        agent_assignments = {}
        for discrepancy in discrepancies:
            agent = discrepancy.get('suggested_agent', 'supervisor')
            if agent not in agent_assignments:
                agent_assignments[agent] = []
            agent_assignments[agent].append(discrepancy)
        
        # Create comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'sweep_type': 'comprehensive_backlog_monitoring',
            'summary': {
                'total_discrepancies': len(discrepancies),
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'low_priority_count': len(low_priority),
                'agents_with_assignments': len(agent_assignments),
                'dashboard_requirements': len(dashboard_requirements)
            },
            'discrepancies_by_priority': {
                'high': high_priority,
                'medium': medium_priority,
                'low': low_priority
            },
            'agent_assignments': agent_assignments,
            'dashboard_requirements': dashboard_requirements,
            'recommended_actions': self._generate_action_recommendations(discrepancies, dashboard_requirements)
        }
        
        # Report findings to supervisor
        self.report_to_supervisor(report)
        
        return report
    
    def _generate_action_recommendations(self, discrepancies: List[Dict], dashboard_requirements: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on sweep findings."""
        recommendations = []
        
        # Count discrepancies by type
        type_counts = {}
        for d in discrepancies:
            d_type = d.get('type', 'unknown')
            type_counts[d_type] = type_counts.get(d_type, 0) + 1
        
        # Generate specific recommendations
        if type_counts.get('missing_acceptance_criteria', 0) > 0:
            recommendations.append(f"Priority: Review {type_counts['missing_acceptance_criteria']} user stories missing acceptance criteria with QA Tester Agent")
        
        if type_counts.get('missing_story_points', 0) > 0:
            recommendations.append(f"Estimation: Have Developer Agent estimate {type_counts['missing_story_points']} user stories missing story points")
        
        if type_counts.get('user_story_missing_tasks', 0) > 0:
            recommendations.append(f"Decomposition: Have Developer Agent break down {type_counts['user_story_missing_tasks']} user stories into tasks")
        
        if type_counts.get('orphaned_work_item', 0) > 0:
            recommendations.append(f"Hierarchy: Have Decomposition Agent link {type_counts['orphaned_work_item']} orphaned work items to appropriate parents")
        
        if dashboard_requirements:
            recommendations.append(f"Monitoring: Review {len(dashboard_requirements)} dashboard/reporting requirements")
        
        return recommendations

    def get_logger(self):
        """Get or create logger for this agent."""
        if not hasattr(self, '_logger'):
            import logging
            self._logger = logging.getLogger('backlog_sweeper')
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self._logger.addHandler(handler)
                self._logger.setLevel(logging.INFO)
        return self._logger
    
    @property
    def logger(self):
        """Lazy logger property."""
        return self.get_logger()

    def validate_epics(self, epics: list) -> list:
        """Validate that all epics have required fields (title, description)."""
        discrepancies = []
        for epic in epics:
            if not epic.get('title'):
                discrepancies.append({
                    'type': 'missing_epic_title',
                    'work_item_id': epic.get('id'),
                    'work_item_type': 'Epic',
                    'title': '',
                    'description': 'Epic missing title.',
                    'severity': 'high',
                    'suggested_agent': 'epic_strategist'
                })
            if not epic.get('description'):
                discrepancies.append({
                    'type': 'missing_epic_description',
                    'work_item_id': epic.get('id'),
                    'work_item_type': 'Epic',
                    'title': epic.get('title', ''),
                    'description': 'Epic missing description.',
                    'severity': 'high',
                    'suggested_agent': 'epic_strategist'
                })
        return discrepancies

    def validate_epic_feature_relationships(self, epics: list) -> list:
        """Validate that every epic has at least one feature with a title."""
        discrepancies = []
        for epic in epics:
            features = epic.get('features', [])
            if not features:
                discrepancies.append({
                    'type': 'missing_child_feature',
                    'work_item_id': epic.get('id'),
                    'work_item_type': 'Epic',
                    'title': epic.get('title', ''),
                    'description': 'Epic missing child Feature.',
                    'severity': 'high',
                    'suggested_agent': 'epic_strategist'
                })
            for feature in features:
                if not feature.get('title'):
                    discrepancies.append({
                        'type': 'missing_feature_title',
                        'work_item_id': feature.get('id'),
                        'work_item_type': 'Feature',
                        'title': '',
                        'description': f"Feature under epic '{epic.get('title','')}' missing title.",
                        'severity': 'high',
                        'suggested_agent': 'feature_decomposer_agent'
                    })
        return discrepancies

    def validate_feature_user_story_relationships(self, epics: list) -> list:
        """Validate that every feature has 3–6 user stories, each with a title, for thoroughness and completeness."""
        discrepancies = []
        for epic in epics:
            for feature in epic.get('features', []):
                user_stories = feature.get('user_stories', [])
                # Check for missing or too few/many user stories
                if not user_stories:
                    discrepancies.append({
                        'type': 'missing_child_user_story',
                        'work_item_id': feature.get('id'),
                        'work_item_type': 'Feature',
                        'title': feature.get('title', ''),
                        'description': 'Feature missing child User Story.',
                        'severity': 'high',
                        'suggested_agent': 'feature_decomposer_agent'
                    })
                elif len(user_stories) < 3:
                    discrepancies.append({
                        'type': 'insufficient_user_stories',
                        'work_item_id': feature.get('id'),
                        'work_item_type': 'Feature',
                        'title': feature.get('title', ''),
                        'description': f"Feature has only {len(user_stories)} user stories (should have 3–6 for completeness).",
                        'severity': 'medium',
                        'suggested_agent': 'feature_decomposer_agent'
                    })
                elif len(user_stories) > 6:
                    discrepancies.append({
                        'type': 'excessive_user_stories',
                        'work_item_id': feature.get('id'),
                        'work_item_type': 'Feature',
                        'title': feature.get('title', ''),
                        'description': f"Feature has {len(user_stories)} user stories (should have 3–6 for focus and clarity).",
                        'severity': 'low',
                        'suggested_agent': 'feature_decomposer_agent'
                    })
                for us in user_stories:
                    if not us.get('title'):
                        discrepancies.append({
                            'type': 'missing_story_title',
                            'work_item_id': us.get('id'),
                            'work_item_type': 'User Story',
                            'title': '',
                            'description': f"User Story under feature '{feature.get('title','')}' missing title.",
                            'severity': 'high',
                            'suggested_agent': 'user_story_decomposer_agent'
                        })
        return discrepancies

    def validate_user_story_tasks(self, epics: list) -> list:
        """Validate that every user story has tasks and story points."""
        discrepancies = []
        for epic in epics:
            for feature in epic.get('features', []):
                for us in feature.get('user_stories', []):
                    tasks = us.get('tasks', [])
                    if not tasks:
                        discrepancies.append({
                            'type': 'missing_child_task',
                            'work_item_id': us.get('id'),
                            'work_item_type': 'User Story',
                            'title': us.get('title', ''),
                            'description': 'User Story missing child Task.',
                            'severity': 'medium',
                            'suggested_agent': 'developer_agent'
                        })
                    if us.get('story_points') is None:
                        discrepancies.append({
                            'type': 'missing_story_points',
                            'work_item_id': us.get('id'),
                            'work_item_type': 'User Story',
                            'title': us.get('title', ''),
                            'description': 'User Story missing story points.',
                            'severity': 'medium',
                            'suggested_agent': 'developer_agent'
                        })
        return discrepancies

    def validate_test_artifacts(self, epics: list) -> list:
        """Validate QA hierarchy: test plans for features, test suites for user stories, and test cases."""
        discrepancies = []
        for epic in epics:
            for feature in epic.get('features', []):
                # Check for test plan at feature level
                if not feature.get('test_plan') and not feature.get('test_plan_structure'):
                    discrepancies.append({
                        'type': 'missing_test_plan',
                        'work_item_id': feature.get('id'),
                        'work_item_type': 'Feature',
                        'title': feature.get('title', ''),
                        'description': 'Feature missing test plan.',
                        'severity': 'high',
                        'suggested_agent': 'qa_lead_agent'
                    })
                
                for us in feature.get('user_stories', []):
                    # Check for test suite at user story level
                    if not us.get('test_suite'):
                        discrepancies.append({
                            'type': 'missing_test_suite',
                            'work_item_id': us.get('id'),
                            'work_item_type': 'User Story',
                            'title': us.get('title', ''),
                            'description': 'User Story missing test suite.',
                            'severity': 'high',
                            'suggested_agent': 'qa_lead_agent'
                        })
                    
                    # Check for test cases at user story level
                    test_cases = us.get('test_cases', [])
                    if not test_cases:
                        discrepancies.append({
                            'type': 'missing_child_test_case',
                            'work_item_id': us.get('id'),
                            'work_item_type': 'User Story',
                            'title': us.get('title', ''),
                            'description': 'User Story missing test cases.',
                            'severity': 'high',
                            'suggested_agent': 'qa_lead_agent'
                        })
                    else:
                        # Validate test case structure
                        for test_case in test_cases:
                            if not test_case.get('title'):
                                discrepancies.append({
                                    'type': 'missing_test_case_title',
                                    'work_item_id': us.get('id'),
                                    'work_item_type': 'Test Case',
                                    'title': f"Test case in {us.get('title', '')}",
                                    'description': 'Test case missing title.',
                                    'severity': 'medium',
                                    'suggested_agent': 'qa_lead_agent'
                                })
                    
                    # Validate test suite and test plan relationship
                    test_suite = us.get('test_suite', {})
                    test_plan = feature.get('test_plan', {})
                    if test_suite and test_plan:
                        if test_suite.get('feature_id') != feature.get('id'):
                            discrepancies.append({
                                'type': 'test_plan_suite_mismatch',
                                'work_item_id': us.get('id'),
                                'work_item_type': 'User Story',
                                'title': us.get('title', ''),
                                'description': 'Test suite not properly linked to feature test plan.',
                                'severity': 'medium',
                                'suggested_agent': 'qa_lead_agent'
                            })
        return discrepancies

    def run_targeted_sweep(self, stage: str, workflow_data: dict, immediate_callback: bool = True) -> List[Dict[str, Any]]:
        """
        Run a targeted sweep for a specific workflow stage.
        Used by supervisor for immediate validation after agent execution.
        
        Args:
            stage: The workflow stage to validate ('epic_strategist', 'feature_decomposer_agent', etc.)
            workflow_data: Current workflow data containing epics, features, user stories
            immediate_callback: Whether to immediately report to supervisor (default: True)
            
        Returns:
            List of discrepancies found for the specific stage
        """
        epics = workflow_data.get('epics', [])
        discrepancies = []
        
        try:
            if stage == 'epic_strategist':
                discrepancies = self.validate_epics(epics)
            elif stage == 'feature_decomposer_agent':
                discrepancies = self.validate_epic_feature_relationships(epics)
            elif stage == 'user_story_decomposer_agent':
                discrepancies = self.validate_feature_user_story_relationships(epics)
            elif stage == 'decomposition_agent':
                # Backward compatibility - validate both epic-feature and feature-user story
                discrepancies = (self.validate_epic_feature_relationships(epics) + 
                               self.validate_feature_user_story_relationships(epics))
            elif stage == 'developer_agent':
                discrepancies = self.validate_user_story_tasks(epics)
            elif stage == 'qa_tester_agent' or stage == 'qa_lead_agent':
                discrepancies = self.validate_test_artifacts(epics)
            else:
                self.logger.warning(f"Unknown stage for targeted sweep: {stage}")
                return []
            
            # Create targeted report if discrepancies found and callback requested
            if discrepancies and immediate_callback and self.supervisor_callback:
                # Group by suggested agent for efficient routing
                agent_assignments = {}
                for discrepancy in discrepancies:
                    agent = discrepancy.get('suggested_agent', 'supervisor')
                    if agent not in agent_assignments:
                        agent_assignments[agent] = []
                    agent_assignments[agent].append(discrepancy)
                
                # Create targeted report
                targeted_report = {
                    'timestamp': datetime.now().isoformat(),
                    'sweep_type': 'targeted_stage_validation',
                    'stage': stage,
                    'summary': {
                        'total_discrepancies': len(discrepancies),
                        'high_priority_count': len([d for d in discrepancies if d.get('severity') == 'high']),
                        'agents_with_assignments': len(agent_assignments)
                    },
                    'agent_assignments': agent_assignments,
                    'immediate_remediation_requested': True,
                    'recommended_actions': [f"Remediate {len(discrepancies)} issues found in {stage} stage"]
                }
                
                # Report immediately to supervisor
                self.report_to_supervisor(targeted_report)
            
            return discrepancies
            
        except Exception as e:
            self.logger.error(f"Error in targeted sweep for stage {stage}: {e}")
            return []

    def validate_pre_integration(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive quality check before Azure DevOps integration.
        
        Validates:
        - Data structure integrity
        - Required fields for ADO work items
        - Hierarchical relationships
        - Content quality and completeness
        - ADO-specific requirements
        
        Args:
            workflow_data: Complete workflow data ready for ADO integration
            
        Returns:
            Validation report with issues found and recommendations
        """
        validation_start = datetime.now()
        self.logger.info("Starting pre-integration validation for ADO upload")
        
        validation_report = {
            'timestamp': validation_start.isoformat(),
            'validation_type': 'pre_integration_quality_check',
            'status': 'passed',  # Will be changed to 'failed' if critical issues found
            'summary': {
                'total_issues': 0,
                'critical_issues': 0,
                'warning_issues': 0,
                'info_issues': 0
            },
            'issues': [],
            'structure_check': {},
            'content_quality': {},
            'ado_compatibility': {},
            'recommendations': []
        }
        
        try:
            epics = workflow_data.get('epics', [])
            
            # 1. Structure Validation
            structure_issues = self._validate_structure_integrity(epics)
            validation_report['issues'].extend(structure_issues)
            validation_report['structure_check'] = {
                'epic_count': len(epics),
                'total_features': sum(len(epic.get('features', [])) for epic in epics),
                'total_user_stories': sum(len(feature.get('user_stories', [])) 
                                        for epic in epics 
                                        for feature in epic.get('features', [])),
                'total_tasks': sum(len(story.get('tasks', [])) 
                                 for epic in epics 
                                 for feature in epic.get('features', [])
                                 for story in feature.get('user_stories', [])),
                'total_test_cases': sum(len(story.get('test_cases', [])) 
                                      for epic in epics 
                                      for feature in epic.get('features', [])
                                      for story in feature.get('user_stories', []))
            }
            
            # 2. ADO Field Validation
            ado_issues = self._validate_ado_required_fields(epics)
            validation_report['issues'].extend(ado_issues)
            
            # 3. Content Quality Validation
            content_issues = self._validate_content_quality(epics)
            validation_report['issues'].extend(content_issues)
            
            # 4. Relationship Validation
            relationship_issues = self._validate_integration_relationships(epics)
            validation_report['issues'].extend(relationship_issues)
            
            # 5. Test Plan Structure Validation
            test_issues = self._validate_test_plan_structure(epics)
            validation_report['issues'].extend(test_issues)
            
            # Categorize issues by severity
            for issue in validation_report['issues']:
                severity = issue.get('severity', 'info')
                if severity == 'critical':
                    validation_report['summary']['critical_issues'] += 1
                elif severity == 'warning':
                    validation_report['summary']['warning_issues'] += 1
                else:
                    validation_report['summary']['info_issues'] += 1
            
            validation_report['summary']['total_issues'] = len(validation_report['issues'])
            
            # Determine overall status
            if validation_report['summary']['critical_issues'] > 0:
                validation_report['status'] = 'failed'
                validation_report['recommendations'].append(
                    "CRITICAL: Fix critical issues before attempting ADO integration"
                )
            elif validation_report['summary']['warning_issues'] > 5:
                validation_report['status'] = 'warning'
                validation_report['recommendations'].append(
                    "WARNING: Consider fixing warning issues for better ADO integration"
                )
            
            # Add specific recommendations
            if validation_report['summary']['critical_issues'] == 0:
                validation_report['recommendations'].append(
                    "✅ Structure validation passed - ready for ADO integration"
                )
            
            validation_end = datetime.now()
            validation_duration = (validation_end - validation_start).total_seconds()
            
            self.logger.info(f"Pre-integration validation completed in {validation_duration:.2f}s")
            self.logger.info(f"Status: {validation_report['status']}")
            self.logger.info(f"Issues found: {validation_report['summary']['total_issues']} "
                           f"(Critical: {validation_report['summary']['critical_issues']}, "
                           f"Warning: {validation_report['summary']['warning_issues']})")
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"Pre-integration validation failed: {e}")
            validation_report['status'] = 'error'
            validation_report['issues'].append({
                'severity': 'critical',
                'category': 'validation_error',
                'description': f"Validation process failed: {str(e)}",
                'suggested_action': 'Check logs and fix validation process'
            })
            return validation_report

    def _validate_structure_integrity(self, epics: List[Dict]) -> List[Dict]:
        """Validate basic structure integrity for ADO integration."""
        issues = []
        
        if not epics:
            issues.append({
                'severity': 'critical',
                'category': 'structure',
                'description': 'No epics found in workflow data',
                'suggested_action': 'Ensure epic strategist generated at least one epic'
            })
            return issues
        
        for epic_idx, epic in enumerate(epics):
            # Check epic has required structure
            if not epic.get('title'):
                issues.append({
                    'severity': 'critical',
                    'category': 'structure',
                    'description': f'Epic {epic_idx + 1} missing title',
                    'suggested_action': 'Ensure epic strategist provides titles for all epics'
                })
            
            features = epic.get('features', [])
            if not features:
                issues.append({
                    'severity': 'warning',
                    'category': 'structure',
                    'description': f'Epic "{epic.get("title", "Unknown")}" has no features',
                    'suggested_action': 'Ensure feature decomposer creates features for each epic'
                })
                continue
            
            for feature_idx, feature in enumerate(features):
                if not feature.get('title'):
                    issues.append({
                        'severity': 'critical',
                        'category': 'structure',
                        'description': f'Feature {feature_idx + 1} in epic "{epic.get("title")}" missing title',
                        'suggested_action': 'Ensure feature decomposer provides titles for all features'
                    })
                
                user_stories = feature.get('user_stories', [])
                if not user_stories:
                    issues.append({
                        'severity': 'warning',
                        'category': 'structure',
                        'description': f'Feature "{feature.get("title", "Unknown")}" has no user stories',
                        'suggested_action': 'Ensure user story decomposer creates stories for each feature'
                    })
        
        return issues

    def _validate_ado_required_fields(self, epics: List[Dict]) -> List[Dict]:
        """Validate all required fields for ADO work item creation."""
        issues = []
        
        for epic in epics:
            # Epic validation
            if not epic.get('description'):
                issues.append({
                    'severity': 'warning',
                    'category': 'ado_fields',
                    'description': f'Epic "{epic.get("title")}" missing description',
                    'suggested_action': 'Add epic description for better ADO work item quality'
                })
            
            for feature in epic.get('features', []):
                # Feature validation
                if not feature.get('description'):
                    issues.append({
                        'severity': 'warning',
                        'category': 'ado_fields',
                        'description': f'Feature "{feature.get("title")}" missing description',
                        'suggested_action': 'Add feature description for better ADO work item quality'
                    })
                
                for user_story in feature.get('user_stories', []):
                    # User story validation
                    if not user_story.get('acceptance_criteria'):
                        issues.append({
                            'severity': 'critical',
                            'category': 'ado_fields',
                            'description': f'User story "{user_story.get("title")}" missing acceptance criteria',
                            'suggested_action': 'Ensure QA tester agent generates acceptance criteria for all user stories'
                        })
                    
                    for task in user_story.get('tasks', []):
                        # Task validation
                        if not task.get('description'):
                            issues.append({
                                'severity': 'warning',
                                'category': 'ado_fields',
                                'description': f'Task "{task.get("title")}" missing description',
                                'suggested_action': 'Add task descriptions for better ADO work item quality'
                            })
        
        return issues

    def _validate_content_quality(self, epics: List[Dict]) -> List[Dict]:
        """Validate content quality for ADO integration."""
        issues = []
        
        for epic in epics:
            # Check for reasonable content length
            if epic.get('description') and len(epic['description']) < 50:
                issues.append({
                    'severity': 'info',
                    'category': 'content_quality',
                    'description': f'Epic "{epic.get("title")}" has very short description ({len(epic["description"])} chars)',
                    'suggested_action': 'Consider enhancing epic description for better context'
                })
            
            for feature in epic.get('features', []):
                for user_story in feature.get('user_stories', []):
                    acceptance_criteria = user_story.get('acceptance_criteria', [])
                    if isinstance(acceptance_criteria, list) and len(acceptance_criteria) < 2:
                        issues.append({
                            'severity': 'warning',
                            'category': 'content_quality',
                            'description': f'User story "{user_story.get("title")}" has too few acceptance criteria ({len(acceptance_criteria)})',
                            'suggested_action': 'Ensure user stories have sufficient acceptance criteria (minimum 2-3)'
                        })
        
        return issues

    def _validate_integration_relationships(self, epics: List[Dict]) -> List[Dict]:
        """Validate hierarchical relationships for ADO integration."""
        issues = []
        
        # This reuses existing relationship validation but focuses on ADO integration concerns
        relationship_issues = self.validate_epic_feature_relationships(epics)
        relationship_issues.extend(self.validate_feature_user_story_relationships(epics))
        
        # Convert to integration-focused format
        for issue in relationship_issues:
            issues.append({
                'severity': 'warning',
                'category': 'relationships',
                'description': issue.get('description', 'Relationship issue detected'),
                'suggested_action': 'Fix relationship issues to ensure proper ADO work item hierarchy'
            })
        
        return issues

    def _validate_test_plan_structure(self, epics: List[Dict]) -> List[Dict]:
        """Validate test plan structure for ADO test management integration."""
        issues = []
        
        for epic in epics:
            for feature in epic.get('features', []):
                has_test_cases = False
                
                # Check feature-level test cases
                if feature.get('test_cases'):
                    has_test_cases = True
                
                # Check user story-level test cases
                for user_story in feature.get('user_stories', []):
                    if user_story.get('test_cases'):
                        has_test_cases = True
                        
                        # Validate test case structure
                        for test_case in user_story.get('test_cases', []):
                            if not test_case.get('title'):
                                issues.append({
                                    'severity': 'warning',
                                    'category': 'test_structure',
                                    'description': f'Test case in user story "{user_story.get("title")}" missing title',
                                    'suggested_action': 'Ensure all test cases have descriptive titles'
                                })
                            
                            if not test_case.get('steps'):
                                issues.append({
                                    'severity': 'warning',
                                    'category': 'test_structure',
                                    'description': f'Test case "{test_case.get("title")}" missing test steps',
                                    'suggested_action': 'Ensure all test cases have detailed test steps'
                                })
                
                if not has_test_cases:
                    issues.append({
                        'severity': 'info',
                        'category': 'test_coverage',
                        'description': f'Feature "{feature.get("title")}" has no test cases',
                        'suggested_action': 'Consider adding test cases for better quality assurance'
                    })
        
        return issues