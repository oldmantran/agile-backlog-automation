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
        else:
            # Default values if no config provided
            self.min_criteria_count = 3
            self.max_criteria_count = 8
            self.require_bdd_format = True
            self.require_functional_and_nonfunctional = True
            self.critical_notification_count = 5
            self.max_discrepancies_per_run = 100
        
        # Agent assignment mappings for different discrepancy types
        self.agent_assignments = {
            # Epic/Feature level issues
            'missing_epic_title': 'epic_strategist',
            'missing_epic_description': 'epic_strategist', 
            'missing_child_feature': 'epic_strategist',
            'invalid_epic_child': 'epic_strategist',
            'missing_feature_title': 'decomposition_agent',
            'missing_feature_description': 'decomposition_agent',
            'missing_child_user_story': 'decomposition_agent',
            'invalid_feature_child': 'decomposition_agent',
            
            # User Story level issues
            'missing_story_title': 'decomposition_agent',
            'missing_or_invalid_story_description': 'decomposition_agent',
            'missing_acceptance_criteria': 'qa_tester_agent',
            'invalid_acceptance_criteria': 'qa_tester_agent',
            'missing_story_points': 'developer_agent',
            'missing_child_task': 'developer_agent',
            'missing_child_test_case': 'qa_tester_agent',
            
            # Task/Test level issues
            'missing_task_title': 'developer_agent',
            'missing_task_description': 'developer_agent',
            'task_has_children': 'developer_agent',
            'invalid_task_parent': 'developer_agent',
            'missing_test_case_title': 'qa_tester_agent',
            'invalid_test_case_parent': 'qa_tester_agent',
            
            # Relationship issues
            'relationship_issue': 'decomposition_agent',
            'user_story_missing_tasks': 'developer_agent',
            'orphaned_work_item': 'decomposition_agent'
        }

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
                'suggested_agent': 'qa_tester_agent'
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
                'suggested_agent': 'qa_tester_agent'
            })
        elif len(criteria_items) > self.max_criteria_count:
            discrepancies.append({
                'type': 'excessive_acceptance_criteria',
                'work_item_id': wi_id,
                'work_item_type': 'User Story',
                'title': title,
                'description': f'{len(criteria_items)} acceptance criteria found. Consider breaking story down - recommend {self.min_criteria_count}-{self.max_criteria_count} criteria max.',
                'severity': 'medium',
                'suggested_agent': 'decomposition_agent'
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
                    'suggested_agent': 'qa_tester_agent'
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
                    'suggested_agent': 'qa_tester_agent'
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
                        'suggested_agent': 'qa_tester_agent'
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
                        'suggested_agent': self.agent_assignments.get('missing_feature_title', 'decomposition_agent')
                    })
                    
                if not description:
                    discrepancies.append({
                        'type': 'missing_feature_description',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'Feature missing description.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_feature_description', 'decomposition_agent')
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
                        'suggested_agent': self.agent_assignments.get('missing_child_user_story', 'decomposition_agent')
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
                            'suggested_agent': self.agent_assignments.get('invalid_feature_child', 'decomposition_agent')
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
                        'suggested_agent': self.agent_assignments.get('missing_story_title', 'decomposition_agent')
                    })
                
                if not description or 'As a' not in description:
                    discrepancies.append({
                        'type': 'missing_or_invalid_story_description',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': 'User Story missing or invalid description (should follow "As a..." format).',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('missing_or_invalid_story_description', 'decomposition_agent')
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
                        'suggested_agent': self.agent_assignments.get('missing_child_test_case', 'qa_tester_agent')
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
                        'suggested_agent': self.agent_assignments.get('missing_test_case_title', 'qa_tester_agent')
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
                            'suggested_agent': self.agent_assignments.get('invalid_test_case_parent', 'qa_tester_agent')
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
                    'suggested_agent': self.agent_assignments.get('orphaned_work_item', 'decomposition_agent')
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
        if not hasattr(self, 'logger'):
            import logging
            self.logger = logging.getLogger('backlog_sweeper')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        return self.logger
    
    @property
    def logger(self):
        """Lazy logger property."""
        return self.get_logger()

if __name__ == "__main__":
    from supervisor.supervisor import WorkflowSupervisor
    from config.config_loader import Config
    from integrators.azure_devops_api import AzureDevOpsIntegrator
    
    # Load configuration
    config = Config()
    
    # Initialize components
    supervisor = WorkflowSupervisor()
    ado_client = AzureDevOpsIntegrator(config)
    agent = BacklogSweeperAgent(
        ado_client=ado_client, 
        supervisor_callback=supervisor.receive_sweeper_report,
        config=config.config  # Pass the actual config dictionary
    )
    
    print("[INFO] Starting scheduled backlog sweeper...")

    def scheduled_sweep():
        print(f"[INFO] Running backlog sweep at {datetime.now().astimezone().isoformat()}")
        agent.run_sweep()

    # Check if sweeper is enabled in config
    sweeper_config = config.config.get('agents', {}).get('backlog_sweeper_agent', {})
    if not sweeper_config.get('enabled', True):
        print("[INFO] Backlog sweeper is disabled in configuration. Exiting.")
        exit(0)
    
    # Get schedule from config (default to daily at 12:00 UTC)
    schedule_cron = sweeper_config.get('schedule', '0 12 * * *')
    
    if APSCHEDULER_AVAILABLE:
        scheduler = BackgroundScheduler(timezone="UTC")
        
        # Parse cron format (minute hour day month dayofweek)
        # For simplicity, we'll handle the most common case: daily at specific hour
        parts = schedule_cron.split()
        if len(parts) >= 2:
            minute = int(parts[0]) if parts[0] != '*' else 0
            hour = int(parts[1]) if parts[1] != '*' else 12
        else:
            minute, hour = 0, 12
        
        scheduler.add_job(scheduled_sweep, 'cron', hour=hour, minute=minute)
        scheduler.start()
        print(f"[INFO] APScheduler started. Sweep will run daily at {hour:02d}:{minute:02d} UTC.")
        
        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
    else:
        print("[WARN] APScheduler not available. Using fallback loop.")
        last_run = None
        target_hour = 12  # Default to 12:00 UTC
        
        while True:
            now = datetime.now().astimezone()
            if now.hour == target_hour and (last_run is None or (now - last_run) > timedelta(hours=23)):
                scheduled_sweep()
                last_run = now
            time.sleep(60) 