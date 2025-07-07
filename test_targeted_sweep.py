"""
Test script for running targeted sweeping tasks.

This script demonstrates how to run specific sweep tasks like:
- "sweep for missing user story tasks"
- "sweep for orphaned work items"
- "sweep for missing acceptance criteria"
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from supervisor.supervisor import WorkflowSupervisor
from utils.logger import setup_logger

class TargetedSweeperAgent(BacklogSweeperAgent):
    """
    Extended BacklogSweeperAgent with targeted sweep capabilities.
    """
    
    def run_targeted_sweep(self, sweep_type: str = "missing_user_story_tasks", **kwargs):
        """
        Run a targeted sweep for specific types of discrepancies.
        
        Args:
            sweep_type: Type of sweep to run:
                - "missing_user_story_tasks": Find user stories without child tasks
                - "orphaned_work_items": Find work items without proper parents
                - "missing_acceptance_criteria": Find user stories without acceptance criteria
                - "missing_story_points": Find user stories without story points
            **kwargs: Additional parameters for the sweep
        """
        self.logger.info(f"Starting targeted sweep: {sweep_type}")
        
        discrepancies = []
        dashboard_requirements = []
        
        try:
            if sweep_type == "missing_user_story_tasks":
                discrepancies = self._sweep_missing_user_story_tasks(**kwargs)
            elif sweep_type == "orphaned_work_items":
                discrepancies = self._sweep_orphaned_work_items(**kwargs)
            elif sweep_type == "missing_acceptance_criteria":
                discrepancies = self._sweep_missing_acceptance_criteria(**kwargs)
            elif sweep_type == "missing_story_points":
                discrepancies = self._sweep_missing_story_points(**kwargs)
            else:
                raise ValueError(f"Unknown sweep type: {sweep_type}")
                
        except Exception as e:
            error_discrepancy = {
                'type': 'sweep_error',
                'work_item_id': None,
                'work_item_type': 'System',
                'title': f'Targeted Sweep Error ({sweep_type})',
                'description': f'Error during targeted sweep: {str(e)}',
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
            'sweep_type': f'targeted_{sweep_type}',
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

    def _sweep_missing_user_story_tasks(self, **kwargs):
        """Targeted sweep for user stories missing child tasks."""
        discrepancies = []
        
        # Get specific work item IDs if provided, otherwise scan all user stories
        target_ids = kwargs.get('work_item_ids', None)
        area_path = kwargs.get('area_path', None)
        
        if target_ids:
            user_story_ids = [wi_id for wi_id in target_ids]
            self.logger.info(f"Checking specific work items: {target_ids}")
        else:
            user_story_ids = self.ado_client.query_work_items("User Story", area_path=area_path)
            self.logger.info(f"Found {len(user_story_ids)} user stories to check")
        
        for story_id in user_story_ids:
            try:
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
                    
            except Exception as e:
                self.logger.error(f"Error checking user story {story_id}: {e}")
        
        return discrepancies

    def _sweep_orphaned_work_items(self, **kwargs):
        """Targeted sweep for orphaned work items."""
        discrepancies = []
        
        # Query all work items and their relationships
        types = kwargs.get('work_item_types', ["Feature", "User Story", "Task", "Test Case"])
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

    def _sweep_missing_acceptance_criteria(self, **kwargs):
        """Targeted sweep for user stories missing acceptance criteria."""
        discrepancies = []
        
        user_story_ids = self.ado_client.query_work_items("User Story")
        work_items = self.ado_client.get_work_item_details(user_story_ids)
        
        for wi in work_items:
            wi_id = wi['id']
            title = wi.get('fields', {}).get('System.Title', '')
            criteria = wi.get('fields', {}).get('Microsoft.VSTS.Common.AcceptanceCriteria', '')
            
            if not criteria or len(criteria.strip()) < 10:
                discrepancies.append({
                    'type': 'missing_acceptance_criteria',
                    'work_item_id': wi_id,
                    'work_item_type': 'User Story',
                    'title': title,
                    'description': 'User Story missing or insufficient acceptance criteria.',
                    'severity': 'high',
                    'suggested_agent': 'qa_tester_agent'
                })
        
        return discrepancies

    def _sweep_missing_story_points(self, **kwargs):
        """Targeted sweep for user stories missing story points."""
        discrepancies = []
        
        user_story_ids = self.ado_client.query_work_items("User Story")
        work_items = self.ado_client.get_work_item_details(user_story_ids)
        
        for wi in work_items:
            wi_id = wi['id']
            title = wi.get('fields', {}).get('System.Title', '')
            story_points = wi.get('fields', {}).get('Microsoft.VSTS.Scheduling.StoryPoints', '')
            
            if not story_points:
                discrepancies.append({
                    'type': 'missing_story_points',
                    'work_item_id': wi_id,
                    'work_item_type': 'User Story',
                    'title': title,
                    'description': 'User Story missing story points estimation.',
                    'severity': 'medium',
                    'suggested_agent': 'developer_agent'
                })
        
        return discrepancies


def test_targeted_sweep_for_missing_tasks():
    """
    Test targeted sweep specifically for user stories missing tasks.
    This will help us see if work item 1308 gets properly processed on a second run.
    """
    
    # Setup logging
    logger = setup_logger("test_targeted_sweep", "logs/test_targeted_sweep.log")
    logger.info("Starting targeted sweep test for missing user story tasks")
    
    try:
        # Load configuration
        config = Config()
        
        # Initialize Azure DevOps integrator
        ado_client = AzureDevOpsIntegrator(config)
        
        # Initialize supervisor (to receive and process sweeper reports)
        supervisor = WorkflowSupervisor()
        
        # Create a callback function for the sweeper to send reports to supervisor
        captured_report = None
        
        def sweeper_callback(report):
            nonlocal captured_report
            logger.info("Targeted sweeper report received - forwarding to supervisor")
            captured_report = report
            supervisor.receive_sweeper_report(report)
        
        # Initialize targeted backlog sweeper with supervisor callback
        sweeper = TargetedSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=sweeper_callback,
            config=config.settings
        )
        
        print("\n" + "="*80)
        print("TARGETED SWEEP: MISSING USER STORY TASKS")
        print("="*80)
        
        # Test 1: Check specific work item 1308
        print(f"\n🎯 Test 1: Checking specific work item 1308")
        report1 = sweeper.run_targeted_sweep(
            sweep_type="missing_user_story_tasks",
            work_item_ids=[1308]
        )
        
        print(f"   Found {report1['summary']['total_discrepancies']} discrepancies for work item 1308")
        
        if report1['summary']['total_discrepancies'] > 0:
            print(f"   ✅ Work item 1308 was flagged for missing tasks!")
            discrepancy = report1['discrepancies_by_priority']['medium'][0] if report1['discrepancies_by_priority']['medium'] else None
            if discrepancy:
                print(f"   📋 Details: {discrepancy['description']}")
                print(f"   🤖 Suggested Agent: {discrepancy['suggested_agent']}")
        else:
            print(f"   ❌ Work item 1308 was NOT flagged - it may already have tasks or not exist")
        
        # Test 2: Check all user stories in Data Visualization area
        print(f"\n🎯 Test 2: Checking all user stories in Data Visualization area")
        report2 = sweeper.run_targeted_sweep(
            sweep_type="missing_user_story_tasks",
            area_path="Backlog Automation\\Data Visualization"
        )
        
        print(f"   Found {report2['summary']['total_discrepancies']} total discrepancies")
        
        if report2['summary']['total_discrepancies'] > 0:
            print(f"   Agent assignments:")
            for agent, discs in report2['agent_assignments'].items():
                print(f"     - {agent}: {len(discs)} discrepancies")
            
            # Show first few work items that need tasks
            medium_priority = report2['discrepancies_by_priority']['medium']
            if medium_priority:
                print(f"   \n📋 First 5 user stories missing tasks:")
                for i, disc in enumerate(medium_priority[:5], 1):
                    print(f"     {i}. Work Item {disc['work_item_id']}: {disc['title']}")
        else:
            print(f"   ✅ All user stories in the Data Visualization area have tasks!")
        
        # Test 3: Run a second sweep to see if auto-remediation worked
        print(f"\n🎯 Test 3: Running second sweep to check auto-remediation results")
        
        # Wait a moment for any auto-remediation to complete
        import time
        time.sleep(2)
        
        report3 = sweeper.run_targeted_sweep(
            sweep_type="missing_user_story_tasks", 
            work_item_ids=[1308]
        )
        
        print(f"   Second sweep found {report3['summary']['total_discrepancies']} discrepancies for work item 1308")
        
        if report3['summary']['total_discrepancies'] == 0:
            print(f"   ✅ Success! Work item 1308 now has child tasks (auto-remediation worked)")
        elif report3['summary']['total_discrepancies'] < report1['summary']['total_discrepancies']:
            print(f"   🔄 Partial success! Some issues were resolved by auto-remediation")
        else:
            print(f"   ❓ Same issues found - this may indicate:")
            print(f"      - Auto-remediation failed (check logs)")
            print(f"      - JSON parsing issues in developer agent")
            print(f"      - Work item 1308 may not exist or be in different area")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"output/targeted_sweep_missing_tasks_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        
        # Prepare results data
        results_data = {
            'timestamp': timestamp,
            'sweep_type': 'targeted_missing_user_story_tasks',
            'test_results': {
                'test1_specific_work_item_1308': report1,
                'test2_data_visualization_area': report2,
                'test3_second_sweep_1308': report3
            },
            'analysis': {
                'work_item_1308_flagged_first_time': report1['summary']['total_discrepancies'] > 0,
                'work_item_1308_resolved_second_time': report3['summary']['total_discrepancies'] == 0,
                'auto_remediation_successful': report3['summary']['total_discrepancies'] < report1['summary']['total_discrepancies'],
                'total_area_issues': report2['summary']['total_discrepancies']
            }
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to: {results_file}")
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        print(f"\n" + "="*80)
        print("TARGETED SWEEP TEST COMPLETED")
        print("="*80)
        
        return results_data
        
    except Exception as e:
        logger.error(f"Targeted sweep test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    test_targeted_sweep_for_missing_tasks()
