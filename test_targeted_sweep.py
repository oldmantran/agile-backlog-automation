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
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
from agents.backlog_sweeper_agent import BacklogSweeperAgent
from supervisor.supervisor import WorkflowSupervisor
from utils.logger import setup_logger
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
                - "missing_test_cases": Find user stories without test cases
                - "orphaned_work_items": Find work items without proper parents
                - "missing_acceptance_criteria": Find user stories without acceptance criteria
                - "missing_story_points": Find user stories without story points
                - "incomplete_work_items": Find work items that are incomplete or stale
                - "inconsistent_estimates": Find work items with inconsistent estimates
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
            elif sweep_type == "missing_test_cases":
                discrepancies = self._sweep_missing_test_cases(**kwargs)
            elif sweep_type == "incomplete_work_items":
                discrepancies = self._sweep_incomplete_work_items(**kwargs)
            elif sweep_type == "inconsistent_estimates":
                discrepancies = self._sweep_inconsistent_estimates(**kwargs)
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

    def _sweep_missing_test_cases(self, **kwargs):
        """Targeted sweep for user stories missing test cases."""
        discrepancies = []
        
        # Get specific work item IDs if provided, otherwise scan all user stories
        target_ids = kwargs.get('work_item_ids', None)
        area_path = kwargs.get('area_path', None)
        
        if target_ids:
            user_story_ids = [wi_id for wi_id in target_ids]
            self.logger.info(f"Checking specific work items for test cases: {target_ids}")
        else:
            user_story_ids = self.ado_client.query_work_items("User Story", area_path=area_path)
            self.logger.info(f"Found {len(user_story_ids)} user stories to check for test cases")
        
        for story_id in user_story_ids:
            try:
                relations = self.ado_client.get_work_item_relations(story_id)
                children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
                
                # Check if this story has any Test Case children
                has_test_cases = False
                for child in children:
                    child_id = int(child['url'].split('/')[-1])
                    child_details = self.ado_client.get_work_item_details([child_id])
                    if child_details:
                        child_type = child_details[0].get('fields', {}).get('System.WorkItemType', '')
                        if child_type == 'Test Case':
                            has_test_cases = True
                            break
                
                if not has_test_cases:
                    story_details = self.ado_client.get_work_item_details([story_id])
                    story_title = story_details[0].get('fields', {}).get('System.Title', '') if story_details else ''
                    
                    discrepancies.append({
                        'type': 'user_story_missing_test_cases',
                        'work_item_id': story_id,
                        'work_item_type': 'User Story',
                        'title': story_title,
                        'description': 'User Story has no child test cases.',
                        'severity': 'high',
                        'suggested_agent': self.agent_assignments.get('user_story_missing_test_cases', 'qa_tester_agent')
                    })
                    
            except Exception as e:
                self.logger.error(f"Error checking user story {story_id} for test cases: {e}")
        
        return discrepancies

    def _sweep_incomplete_work_items(self, **kwargs):
        """Targeted sweep for work items with incomplete information."""
        discrepancies = []
        
        # Query work items by state - look for items that should be "Done" but aren't
        types = kwargs.get('work_item_types', ["User Story", "Task", "Feature"])
        target_states = kwargs.get('target_states', ["Active", "New", "Committed"])
        
        for wi_type in types:
            work_item_ids = self.ado_client.query_work_items(wi_type)
            work_items = self.ado_client.get_work_item_details(work_item_ids)
            
            for wi in work_items:
                wi_id = wi['id']
                title = wi.get('fields', {}).get('System.Title', '')
                state = wi.get('fields', {}).get('System.State', '')
                assigned_to = wi.get('fields', {}).get('System.AssignedTo', {})
                
                # Check for various incomplete scenarios
                issues = []
                
                # No assignee for active work
                if state in ["Active", "Committed"] and not assigned_to:
                    issues.append("No assignee for active work item")
                
                # Old active items (created more than 30 days ago and still active)
                created_date = wi.get('fields', {}).get('System.CreatedDate', '')
                if created_date and state in target_states:
                    from datetime import datetime, timedelta
                    try:
                        created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        if datetime.now().replace(tzinfo=created.tzinfo) - created > timedelta(days=30):
                            issues.append("Work item active for more than 30 days")
                    except:
                        pass
                
                if issues:
                    discrepancies.append({
                        'type': 'incomplete_work_item',
                        'work_item_id': wi_id,
                        'work_item_type': wi_type,
                        'title': title,
                        'description': f'{wi_type} incomplete: {"; ".join(issues)}',
                        'severity': 'medium',
                        'suggested_agent': 'developer_agent'
                    })
        
        return discrepancies

    def _sweep_inconsistent_estimates(self, **kwargs):
        """Targeted sweep for work items with inconsistent or missing estimates."""
        discrepancies = []
        
        user_story_ids = self.ado_client.query_work_items("User Story")
        work_items = self.ado_client.get_work_item_details(user_story_ids)
        
        for wi in work_items:
            wi_id = wi['id']
            title = wi.get('fields', {}).get('System.Title', '')
            story_points = wi.get('fields', {}).get('Microsoft.VSTS.Scheduling.StoryPoints', '')
            
            # Get child tasks and their estimates
            relations = self.ado_client.get_work_item_relations(wi_id)
            children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            
            total_task_hours = 0
            task_count = 0
            
            for child in children:
                child_id = int(child['url'].split('/')[-1])
                child_details = self.ado_client.get_work_item_details([child_id])
                if child_details:
                    child_type = child_details[0].get('fields', {}).get('System.WorkItemType', '')
                    if child_type == 'Task':
                        task_count += 1
                        # Get task estimate (Original Estimate or Remaining Work)
                        original_estimate = child_details[0].get('fields', {}).get('Microsoft.VSTS.Scheduling.OriginalEstimate', 0)
                        if original_estimate:
                            total_task_hours += float(original_estimate)
            
            # Check for inconsistencies
            issues = []
            
            # Story points vs task hours inconsistency (rough rule: 1 story point = 4-8 hours)
            if story_points and task_count > 0:
                expected_hours_min = float(story_points) * 4
                expected_hours_max = float(story_points) * 8
                
                if total_task_hours < expected_hours_min * 0.5 or total_task_hours > expected_hours_max * 1.5:
                    issues.append(f"Story points ({story_points}) inconsistent with task hours ({total_task_hours})")
            
            # Tasks without estimates
            if task_count > 0 and total_task_hours == 0:
                issues.append(f"Has {task_count} tasks but no time estimates")
            
            if issues:
                discrepancies.append({
                    'type': 'inconsistent_estimates',
                    'work_item_id': wi_id,
                    'work_item_type': 'User Story',
                    'title': title,
                    'description': f'Estimation issues: {"; ".join(issues)}',
                    'severity': 'medium',
                    'suggested_agent': 'developer_agent'
                })
        
        return discrepancies

    def generate_test_case_coverage_report(self):
        """
        Generate a comprehensive report showing user story IDs and their test case counts,
        ordered ascending by number of test cases.
        """
        print("\n" + "="*80)
        print("TEST CASE COVERAGE REPORT BY USER STORY")
        print("="*80)
        
        try:
            # Load configuration
            config = Config()
            ado_client = AzureDevOpsIntegrator(config)
            
            print(f"\n🔍 Querying all user stories in the project...")
            
            # Query all user stories in the project
            user_story_ids = ado_client.query_work_items("User Story")
            print(f"   Found {len(user_story_ids)} user stories total")
            
            if not user_story_ids:
                print("   ❌ No user stories found in the project!")
                return []
            
            # Get details for all user stories
            print(f"\n📊 Analyzing test case coverage for {len(user_story_ids)} user stories...")
            user_stories = self.ado_client.get_work_item_details(user_story_ids)
            
            coverage_report = []
            
            # Process each user story to count test cases
            for i, story in enumerate(user_stories, 1):
                if i % 10 == 0:  # Progress indicator
                    print(f"   Processing... {i}/{len(user_stories)}")
                
                story_id = story['id']
                title = story.get('fields', {}).get('System.Title', 'Unknown Title')
                state = story.get('fields', {}).get('System.State', 'Unknown')
                area_path = story.get('fields', {}).get('System.AreaPath', 'Unknown')
                story_points = story.get('fields', {}).get('Microsoft.VSTS.Scheduling.StoryPoints', None)
                
                # Get child work items
                try:
                    relations = self.ado_client.get_work_item_relations(story_id)
                    children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
                    
                    # Count test cases and other children
                    test_case_count = 0
                    task_count = 0
                    other_count = 0
                    
                    for child in children:
                        child_id = int(child['url'].split('/')[-1])
                        child_info = self.ado_client.get_work_item_details([child_id])
                        if child_info:
                            child_type = child_info[0].get('fields', {}).get('System.WorkItemType', 'Unknown')
                            if child_type == 'Test Case':
                                test_case_count += 1
                            elif child_type == 'Task':
                                task_count += 1
                            else:
                                other_count += 1
                    
                    coverage_report.append({
                        'story_id': story_id,
                        'title': title,
                        'state': state,
                        'area_path': area_path,
                        'story_points': story_points,
                        'test_case_count': test_case_count,
                        'task_count': task_count,
                        'other_children_count': other_count,
                        'total_children': test_case_count + task_count + other_count
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing User Story {story_id}: {e}")
                    coverage_report.append({
                        'story_id': story_id,
                        'title': title,
                        'state': state,
                        'area_path': area_path,
                        'story_points': story_points,
                        'test_case_count': 0,
                        'task_count': 0,
                        'other_children_count': 0,
                        'total_children': 0,
                        'error': str(e)
                    })
            
            # Sort by test case count (ascending) then by story ID
            coverage_report.sort(key=lambda x: (x['test_case_count'], x['story_id']))
            
            # Generate summary statistics
            total_stories = len(coverage_report)
            stories_with_no_tests = len([s for s in coverage_report if s['test_case_count'] == 0])
            stories_with_tests = total_stories - stories_with_no_tests
            total_test_cases = sum(s['test_case_count'] for s in coverage_report)
            avg_test_cases = total_test_cases / total_stories if total_stories > 0 else 0
            
            print(f"\n📈 SUMMARY STATISTICS:")
            print(f"   Total User Stories: {total_stories}")
            print(f"   Stories with Test Cases: {stories_with_tests}")
            print(f"   Stories without Test Cases: {stories_with_no_tests}")
            print(f"   Total Test Cases: {total_test_cases}")
            print(f"   Average Test Cases per Story: {avg_test_cases:.1f}")
            print(f"   Test Coverage Rate: {(stories_with_tests/total_stories)*100:.1f}%")
            
            # Display detailed report
            print(f"\n📋 DETAILED REPORT (Ordered by Test Case Count):")
            print(f"{'Story ID':<10} {'Test Cases':<12} {'Tasks':<8} {'Total':<8} {'Points':<8} {'State':<12} {'Title':<50}")
            print("-" * 120)
            
            for story in coverage_report:
                story_id = story['story_id']
                test_cases = story['test_case_count']
                tasks = story['task_count']
                total = story['total_children']
                points = story['story_points'] if story['story_points'] is not None else 'N/A'
                state = story['state']
                title = story['title'][:47] + "..." if len(story['title']) > 50 else story['title']
                
                # Color coding for test case count
                if test_cases == 0:
                    status_icon = "❌"
                elif test_cases < 5:
                    status_icon = "⚠️ "
                else:
                    status_icon = "✅"
                
                print(f"{story_id:<10} {status_icon}{test_cases:<10} {tasks:<8} {total:<8} {points:<8} {state:<12} {title:<50}")
            
            # Show stories with most test cases
            print(f"\n🏆 TOP 10 STORIES WITH MOST TEST CASES:")
            top_stories = sorted(coverage_report, key=lambda x: x['test_case_count'], reverse=True)[:10]
            for i, story in enumerate(top_stories, 1):
                if story['test_case_count'] > 0:
                    print(f"   {i}. Story {story['story_id']}: {story['test_case_count']} test cases - {story['title'][:60]}")
            
            # Show stories without test cases (first 20)
            print(f"\n❌ STORIES WITHOUT TEST CASES (First 20):")
            no_test_stories = [s for s in coverage_report if s['test_case_count'] == 0][:20]
            for i, story in enumerate(no_test_stories, 1):
                area = story['area_path'].split('\\')[-1] if '\\' in story['area_path'] else story['area_path']
                print(f"   {i}. Story {story['story_id']} ({area}): {story['title'][:60]}")
            
            if len(no_test_stories) > 20:
                print(f"   ... and {len(no_test_stories) - 20} more stories without test cases")
            
            # Save detailed report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"output/test_case_coverage_report_{timestamp}.json"
            
            os.makedirs("output", exist_ok=True)
            
            report_data = {
                'timestamp': timestamp,
                'summary': {
                    'total_stories': total_stories,
                    'stories_with_tests': stories_with_tests,
                    'stories_without_tests': stories_with_no_tests,
                    'total_test_cases': total_test_cases,
                    'average_test_cases_per_story': avg_test_cases,
                    'test_coverage_rate_percent': (stories_with_tests/total_stories)*100 if total_stories > 0 else 0
                },
                'detailed_report': coverage_report
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"\n📄 Detailed report saved to: {report_file}")
            
            # Also save a CSV version for easy analysis
            csv_file = f"output/test_case_coverage_report_{timestamp}.csv"
            
            import csv
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['story_id', 'title', 'state', 'area_path', 'story_points', 
                             'test_case_count', 'task_count', 'other_children_count', 'total_children']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for story in coverage_report:
                    row = {k: v for k, v in story.items() if k in fieldnames}
                    writer.writerow(row)
            
            print(f"📊 CSV report saved to: {csv_file}")
            
            return coverage_report
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return []


def test_targeted_sweep_for_work_item_1508():
    """
    Test targeted sweep specifically for work item 1508 that had JSON parsing issues.
    This will help us see if the JSON parsing issue can be reproduced and fixed.
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
        print("TARGETED SWEEP: TESTING WORK ITEM 1508 JSON PARSING ISSUE")
        print("="*80)
        
        # Test 1: Check specific work item 1508 (the one that failed)
        print(f"\n🎯 Test 1: Checking specific work item 1508 (JSON parsing issue)")
        report1 = sweeper.run_targeted_sweep(
            sweep_type="missing_user_story_tasks",
            work_item_ids=[1508]
        )
        
        print(f"   Found {report1['summary']['total_discrepancies']} discrepancies for work item 1508")
        
        if report1['summary']['total_discrepancies'] > 0:
            print(f"   ✅ Work item 1508 was flagged for missing tasks!")
            discrepancy = report1['discrepancies_by_priority']['medium'][0] if report1['discrepancies_by_priority']['medium'] else None
            if discrepancy:
                print(f"   📋 Details: {discrepancy['description']}")
                print(f"   🤖 Suggested Agent: {discrepancy['suggested_agent']}")
        else:
            print(f"   ❌ Work item 1508 was NOT flagged - it may already have tasks or not exist")
        
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
        
        # Test 3: Run a second sweep to see if auto-remediation worked for 1508
        print(f"\n🎯 Test 3: Running second sweep to check auto-remediation results for 1508")
        
        # Wait a moment for any auto-remediation to complete
        import time
        time.sleep(2)
        
        report3 = sweeper.run_targeted_sweep(
            sweep_type="missing_user_story_tasks", 
            work_item_ids=[1508]
        )
        
        print(f"   Second sweep found {report3['summary']['total_discrepancies']} discrepancies for work item 1508")
        
        if report3['summary']['total_discrepancies'] == 0:
            print(f"   ✅ Success! Work item 1508 now has child tasks (auto-remediation worked)")
        elif report3['summary']['total_discrepancies'] < report1['summary']['total_discrepancies']:
            print(f"   🔄 Partial success! Some issues were resolved by auto-remediation")
        else:
            print(f"   ❓ Same issues found - this indicates JSON parsing issues in developer agent")
            print(f"      Check logs for 'Failed to parse JSON' or 'WARNING - No tasks generated'")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"output/targeted_sweep_1508_issue_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        
        # Prepare results data
        results_data = {
            'timestamp': timestamp,
            'sweep_type': 'targeted_missing_user_story_tasks_1508',
            'test_results': {
                'test1_specific_work_item_1508': report1,
                'test2_data_visualization_area': report2,
                'test3_second_sweep_1508': report3
            },
            'analysis': {
                'work_item_1508_flagged_first_time': report1['summary']['total_discrepancies'] > 0,
                'work_item_1508_resolved_second_time': report3['summary']['total_discrepancies'] == 0,
                'auto_remediation_successful': report3['summary']['total_discrepancies'] < report1['summary']['total_discrepancies'],
                'total_area_issues': report2['summary']['total_discrepancies'],
                'json_parsing_issue_suspected': report1['summary']['total_discrepancies'] > 0 and report3['summary']['total_discrepancies'] >= report1['summary']['total_discrepancies']
            }
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to: {results_file}")
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        print(f"\n" + "="*80)
        print("TARGETED SWEEP TEST FOR WORK ITEM 1508 COMPLETED")
        print("="*80)
        
        return results_data
        
    except Exception as e:
        logger.error(f"Targeted sweep test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        raise


def test_work_item_1508():
    """
    Simple test to check work item 1508 that failed JSON parsing.
    """
    print("\n" + "="*80)
    print("TESTING WORK ITEM 1508 - JSON PARSING ISSUE")
    print("="*80)
    
    try:
        # Load configuration
        config = Config()
        ado_client = AzureDevOpsIntegrator(config)
        supervisor = WorkflowSupervisor()
        
        # Initialize targeted sweeper
        sweeper = TargetedSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=supervisor.receive_sweeper_report,
            config=config.settings
        )
        
        # Test work item 1508 specifically
        print(f"\n🎯 Testing work item 1508...")
        report = sweeper.run_targeted_sweep(
            sweep_type="missing_user_story_tasks",
            work_item_ids=[1508]
        )
        
        print(f"   Found {report['summary']['total_discrepancies']} discrepancies")
        if report['summary']['total_discrepancies'] > 0:
            print(f"   ✅ Work item 1508 flagged - auto-remediation should trigger")
        else:
            print(f"   ❌ Work item 1508 NOT flagged - may already have tasks")
        
        return report
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


def test_missing_test_cases():
    """
    Test to check which user stories are missing test cases.
    """
    print("\n" + "="*80)
    print("TESTING USER STORIES MISSING TEST CASES")
    print("="*80)
    
    try:
        # Load configuration
        config = Config()
        ado_client = AzureDevOpsIntegrator(config)
        
        # Verify project and organization settings
        print(f"\n🔍 Configuration verification:")
        print(f"   Organization: {config.get_env('AZURE_DEVOPS_ORG')}")
        print(f"   Project: {config.get_env('AZURE_DEVOPS_PROJECT')}")
        print(f"   Default Area Path: {config.settings.get('project', {}).get('default_area_path', 'Not set')}")
        
        supervisor = WorkflowSupervisor()
        
        # Initialize targeted sweeper
        sweeper = TargetedSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=supervisor.receive_sweeper_report,
            config=config.settings
        )
        
        # Test for missing test cases with specific area path
        area_path = "Backlog Automation\\Data Visualization"
        print(f"\n🎯 Checking for user stories missing test cases in area: {area_path}")
        
        # First, let's directly query to see how many user stories we get
        print(f"   📊 Querying user stories directly...")
        user_story_ids = ado_client.query_work_items("User Story", area_path=area_path)
        print(f"   Found {len(user_story_ids)} user stories in {area_path}")
        
        if len(user_story_ids) > 0:
            print(f"   First 10 user story IDs: {user_story_ids[:10]}")
            
            # Get some details to verify we're in the right project
            sample_details = ado_client.get_work_item_details(user_story_ids[:3])
            for detail in sample_details:
                area = detail.get('fields', {}).get('System.AreaPath', '')
                title = detail.get('fields', {}).get('System.Title', '')
                print(f"   Sample: {detail['id']} - {title} (Area: {area})")
        
        # Now run the targeted sweep
        report = sweeper.run_targeted_sweep(
            sweep_type="missing_test_cases",
            area_path=area_path
        )
        
        print(f"\n📋 Sweep Results:")
        print(f"   Found {report['summary']['total_discrepancies']} user stories missing test cases")
        
        if report['summary']['total_discrepancies'] > 0:
            print(f"   📋 User stories needing test cases:")
            high_priority = report['discrepancies_by_priority']['high']
            for i, disc in enumerate(high_priority[:10], 1):  # Show first 10
                print(f"     {i}. Work Item {disc['work_item_id']}: {disc['title']}")
                
            if len(high_priority) > 10:
                print(f"     ... and {len(high_priority) - 10} more")
        else:
            print(f"   ✅ All user stories have test cases!")
        
        return report
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_all_sweep_types():
    """
    Test all available targeted sweep types to see current backlog state.
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE TARGETED SWEEP - ALL TYPES")
    print("="*80)
    
    try:
        # Load configuration
        config = Config()
        ado_client = AzureDevOpsIntegrator(config)
        supervisor = WorkflowSupervisor()
        
        # Initialize targeted sweeper
        sweeper = TargetedSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=supervisor.receive_sweeper_report,
            config=config.settings
        )
        
        sweep_types = [
            "missing_user_story_tasks",
            "missing_test_cases", 
            "orphaned_work_items",
            "missing_acceptance_criteria",
            "missing_story_points"
        ]
        
        results = {}
        
        for sweep_type in sweep_types:
            print(f"\n🎯 Running sweep: {sweep_type}")
            try:
                report = sweeper.run_targeted_sweep(sweep_type=sweep_type)
                results[sweep_type] = report
                
                total = report['summary']['total_discrepancies']
                print(f"   Found {total} discrepancies")
                
                if total > 0:
                    for priority in ['high', 'medium', 'low']:
                        count = report['summary'][f'{priority}_priority_count']
                        if count > 0:
                            print(f"     - {priority.title()}: {count}")
                            
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results[sweep_type] = {'error': str(e)}
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"output/comprehensive_targeted_sweep_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Comprehensive results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        return None


def delete_data_visualization_test_cases():
    """
    Delete all existing test cases in the Data Visualization area path.
    This will clean up test cases that were incorrectly created as children of Features
    so we can start fresh with properly structured test cases under User Stories.
    """
    print("\n" + "="*80)
    print("DELETING ALL TEST CASES IN DATA VISUALIZATION AREA")
    print("="*80)
    
    # Setup logging
    logger = setup_logger("delete_test_cases", "logs/delete_test_cases.log")
    logger.info("Starting deletion of Data Visualization test cases")
    
    try:
        # Load configuration
        config = Config()
        ado_client = AzureDevOpsIntegrator(config)
        
        # Query all test cases in the Data Visualization area
        area_path = "Backlog Automation\\Data Visualization"
        print(f"\n🔍 Searching for test cases in area: {area_path}")
        
        test_case_ids = ado_client.query_work_items("Test Case", area_path=area_path)
        print(f"   Found {len(test_case_ids)} test cases to evaluate")
        
        if not test_case_ids:
            print("   ✅ No test cases found in the Data Visualization area!")
            return []
        
        # Get details for all test cases
        test_cases = ado_client.get_work_item_details(test_case_ids)
        
        deleted_cases = []
        skipped_cases = []
        
        print(f"\n🗑️  Processing {len(test_cases)} test cases for deletion...")
        
        for i, test_case in enumerate(test_cases, 1):
            test_id = test_case['id']
            title = test_case.get('fields', {}).get('System.Title', 'Unknown Title')
            state = test_case.get('fields', {}).get('System.State', 'Unknown')
            
            print(f"\n   {i}. Test Case {test_id}: {title}")
            print(f"      State: {state}")
            
            # Check if this test case has any important relationships we should preserve
            relations = ado_client.get_work_item_relations(test_id)
            parents = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Reverse']
            
            if parents:
                parent_details = []
                for parent in parents:
                    parent_id = int(parent['url'].split('/')[-1])
                    parent_info = ado_client.get_work_item_details([parent_id])
                    if parent_info:
                        parent_type = parent_info[0].get('fields', {}).get('System.WorkItemType', '')
                        parent_title = parent_info[0].get('fields', {}).get('System.Title', '')
                        parent_details.append(f"{parent_type} {parent_id}: {parent_title}")
                
                print(f"      Parent(s): {', '.join(parent_details)}")
            
            # Skip if test case is in a critical state or has important data
            if state in ['Active', 'Design']:
                print(f"      ⚠️  SKIPPING - Test case is in '{state}' state")
                skipped_cases.append({
                    'id': test_id,
                    'title': title,
                    'state': state,
                    'reason': f"Active state: {state}"
                })
                continue
            
            # Confirm deletion
            try:
                print(f"      🗑️  DELETING test case {test_id}...")
                
                # Use the Azure DevOps API to delete the work item
                # Note: This will move it to the Recycle Bin, not permanently delete
                success = ado_client.delete_work_item(test_id)
                
                if success:
                    print(f"      ✅ Successfully deleted test case {test_id}")
                    deleted_cases.append({
                        'id': test_id,
                        'title': title,
                        'state': state
                    })
                    logger.info(f"Deleted test case {test_id}: {title}")
                else:
                    print(f"      ❌ Failed to delete test case {test_id}")
                    skipped_cases.append({
                        'id': test_id,
                        'title': title,
                        'state': state,
                        'reason': 'Deletion failed'
                    })
                
            except Exception as e:
                print(f"      ❌ Error deleting test case {test_id}: {e}")
                logger.error(f"Error deleting test case {test_id}: {e}")
                skipped_cases.append({
                    'id': test_id,
                    'title': title,
                    'state': state,
                    'reason': f'Exception: {str(e)}'
                })
        
        # Summary
        print(f"\n" + "="*60)
        print("DELETION SUMMARY")
        print("="*60)
        print(f"✅ Successfully deleted: {len(deleted_cases)} test cases")
        print(f"⚠️  Skipped: {len(skipped_cases)} test cases")
        
        if deleted_cases:
            print(f"\n🗑️  Deleted test cases:")
            for case in deleted_cases:
                print(f"   - {case['id']}: {case['title']}")
        
        if skipped_cases:
            print(f"\n⚠️  Skipped test cases:")
            for case in skipped_cases:
                print(f"   - {case['id']}: {case['title']} ({case['reason']})")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"output/deleted_test_cases_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        
        results_data = {
            'timestamp': timestamp,
            'area_path': area_path,
            'total_found': len(test_cases),
            'deleted_count': len(deleted_cases),
            'skipped_count': len(skipped_cases),
            'deleted_cases': deleted_cases,
            'skipped_cases': skipped_cases
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        logger.info(f"Deletion completed. Results saved to: {results_file}")
        
        return deleted_cases
        
    except Exception as e:
        logger.error(f"Test case deletion failed: {e}")
        print(f"\n❌ Deletion failed: {e}")
        raise


def validate_test_case_creation():
    """
    Validate if test cases were actually created in Azure DevOps.
    Check specific user stories that should have gotten test cases.
    """
    print("\n" + "="*80)
    print("VALIDATING TEST CASE CREATION IN AZURE DEVOPS")
    print("="*80)
    
    try:
        # Load configuration
        config = Config()
        ado_client = AzureDevOpsIntegrator(config)
        
        # Test specific user stories that should have gotten test cases
        test_user_stories = [
            1285,  # User specifically mentioned this one
            1386,  # From the log - should have 9 test cases
            1374,  # From the log - should have 8 test cases
            1330,  # From the log - should have 10 test cases
        ]
        
        print(f"\n🔍 Checking {len(test_user_stories)} user stories for test cases...")
        
        for story_id in test_user_stories:
            print(f"\n📋 Checking User Story {story_id}:")
            
            try:
                # Get the user story details
                story_details = ado_client.get_work_item_details([story_id])
                if not story_details:
                    print(f"   ❌ User Story {story_id} not found!")
                    continue
                    
                story = story_details[0]
                title = story.get('fields', {}).get('System.Title', 'Unknown Title')
                state = story.get('fields', {}).get('System.State', 'Unknown')
                
                print(f"   Title: {title}")
                print(f"   State: {state}")
                
                # Get child work items (should include test cases)
                relations = ado_client.get_work_item_relations(story_id)
                children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
                
                print(f"   Total child items: {len(children)}")
                
                # Categorize children by type
                child_details = []
                test_cases = []
                tasks = []
                other_children = []
                
                for child in children:
                    child_id = int(child['url'].split('/')[-1])
                    child_info = ado_client.get_work_item_details([child_id])
                    if child_info:
                        child_detail = child_info[0]
                        child_type = child_detail.get('fields', {}).get('System.WorkItemType', 'Unknown')
                        child_title = child_detail.get('fields', {}).get('System.Title', 'Unknown Title')
                        
                        child_details.append({
                            'id': child_id,
                            'type': child_type,
                            'title': child_title
                        })
                        
                        if child_type == 'Test Case':
                            test_cases.append(child_detail)
                        elif child_type == 'Task':
                            tasks.append(child_detail)
                        else:
                            other_children.append(child_detail)
                
                # Report findings
                print(f"   📝 Tasks: {len(tasks)}")
                print(f"   🧪 Test Cases: {len(test_cases)}")
                print(f"   🔄 Other children: {len(other_children)}")
                
                if test_cases:
                    print(f"   ✅ Test cases found!")
                    for i, tc in enumerate(test_cases[:5], 1):  # Show first 5
                        tc_title = tc.get('fields', {}).get('System.Title', 'Unknown')
                        tc_state = tc.get('fields', {}).get('System.State', 'Unknown')
                        print(f"      {i}. {tc['id']}: {tc_title} ({tc_state})")
                    if len(test_cases) > 5:
                        print(f"      ... and {len(test_cases) - 5} more test cases")
                else:
                    print(f"   ❌ NO TEST CASES FOUND!")
                    
                if tasks:
                    print(f"   📝 Tasks found:")
                    for i, task in enumerate(tasks[:3], 1):  # Show first 3
                        task_title = task.get('fields', {}).get('System.Title', 'Unknown')
                        task_state = task.get('fields', {}).get('System.State', 'Unknown')
                        print(f"      {i}. {task['id']}: {task_title} ({task_state})")
                    if len(tasks) > 3:
                        print(f"      ... and {len(tasks) - 3} more tasks")
                
            except Exception as e:
                print(f"   ❌ Error checking User Story {story_id}: {e}")
        
        # Also check if there are any recent test cases created in the project
        print(f"\n🔍 Checking for recently created test cases in the project...")
        
        # Query all test cases and see if any were created recently
        all_test_case_ids = ado_client.query_work_items("Test Case")
        print(f"   Total test cases in project: {len(all_test_case_ids)}")
        
        if all_test_case_ids:
            # Get details for the most recent test cases
            recent_test_cases = ado_client.get_work_item_details(all_test_case_ids[-20:])  # Last 20
            
            print(f"   🕒 Recent test cases (last 20):")
            for tc in recent_test_cases[-10:]:  # Show last 10
                tc_id = tc['id']
                tc_title = tc.get('fields', {}).get('System.Title', 'Unknown')
                tc_created = tc.get('fields', {}).get('System.CreatedDate', 'Unknown')
                tc_created_by = tc.get('fields', {}).get('System.CreatedBy', {}).get('displayName', 'Unknown')
                
                print(f"      {tc_id}: {tc_title}")
                print(f"         Created: {tc_created} by {tc_created_by}")
        
        # Check test plans and test suites
        print(f"\n🔍 Checking for test plans and test suites...")
        
        try:
            # Note: Azure DevOps REST API requires specific endpoints for test plans
            # This might not work with the basic work item API
            test_plan_ids = ado_client.query_work_items("Test Plan")
            test_suite_ids = ado_client.query_work_items("Test Suite")
            
            print(f"   Test Plans: {len(test_plan_ids)}")
            print(f"   Test Suites: {len(test_suite_ids)}")
            
        except Exception as e:
            print(f"   ⚠️  Could not query test plans/suites: {e}")
            print(f"      (This may require different API endpoints)")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def debug_missing_test_cases():
    """
    Debug why test cases aren't being created by running the targeted sweep
    and checking the actual Azure DevOps API responses.
    """
    print("\n" + "="*80)
    print("DEBUGGING MISSING TEST CASES ISSUE")
    print("="*80)
    
    # Setup logging with debug level
    logger = setup_logger("debug_missing_test_cases", "logs/debug_missing_test_cases.log")
    logger.info("Starting debug session for missing test cases")
    
    try:
        # Load configuration
        config = Config()
        ado_client = AzureDevOpsIntegrator(config)
        supervisor = WorkflowSupervisor()
        
        # Initialize targeted sweeper
        sweeper = TargetedSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=supervisor.receive_sweeper_report,
            config=config.settings
        )
        
        # Test User Story 1285 specifically (the one user mentioned)
        target_story = 1285
        print(f"\n🎯 Testing User Story {target_story} specifically...")
        
        # First, verify the user story exists and get its current state
        print(f"\n1️⃣  Verifying User Story {target_story} exists...")
        story_details = ado_client.get_work_item_details([target_story])
        
        if not story_details:
            print(f"   ❌ User Story {target_story} not found!")
            return False
            
        story = story_details[0]
        title = story.get('fields', {}).get('System.Title', 'Unknown')
        state = story.get('fields', {}).get('System.State', 'Unknown')
        area_path = story.get('fields', {}).get('System.AreaPath', 'Unknown')
        
        print(f"   ✅ Found: {title}")
        print(f"   📍 Area Path: {area_path}")
        print(f"   📊 State: {state}")
        
        # Check current children
        relations = ado_client.get_work_item_relations(target_story)
        children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
        test_cases_before = []
        
        for child in children:
            child_id = int(child['url'].split('/')[-1])
            child_info = ado_client.get_work_item_details([child_id])
            if child_info:
                child_detail = child_info[0]
                child_type = child_detail.get('fields', {}).get('System.WorkItemType', 'Unknown')
                if child_type == 'Test Case':
                    test_cases_before.append(child_detail)
        
        print(f"   🧪 Current test cases: {len(test_cases_before)}")
        
        # Now run the targeted sweep to see if it detects this as missing test cases
        print(f"\n2️⃣  Running targeted sweep for missing test cases...")
        
        report = sweeper.run_targeted_sweep(
            sweep_type="missing_test_cases",
            work_item_ids=[target_story]
        )
        
        print(f"   📋 Sweep found {report['summary']['total_discrepancies']} discrepancies")
        
        if report['summary']['total_discrepancies'] > 0:
            discrepancy = report['discrepancies_by_priority']['high'][0] if report['discrepancies_by_priority']['high'] else None
            if discrepancy:
                print(f"   ✅ User Story {target_story} was flagged for missing test cases")
                print(f"   📝 Description: {discrepancy['description']}")
                print(f"   🤖 Suggested agent: {discrepancy['suggested_agent']}")
                
                # Check if supervisor received and is processing this
                print(f"\n3️⃣  Checking if supervisor is processing the discrepancy...")
                
                # Wait a moment for processing
                import time
                time.sleep(5)
                
                # Check if test cases were created
                print(f"\n4️⃣  Checking if test cases were created after sweep...")
                updated_relations = ado_client.get_work_item_relations(target_story)
                updated_children = [r for r in updated_relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
                test_cases_after = []
                
                for child in updated_children:
                    child_id = int(child['url'].split('/')[-1])
                    child_info = ado_client.get_work_item_details([child_id])
                    if child_info:
                        child_detail = child_info[0]
                        child_type = child_detail.get('fields', {}).get('System.WorkItemType', 'Unknown')
                        if child_type == 'Test Case':
                            test_cases_after.append(child_detail)
                
                print(f"   🧪 Test cases after sweep: {len(test_cases_after)}")
                
                if len(test_cases_after) > len(test_cases_before):
                    print(f"   ✅ SUCCESS! {len(test_cases_after) - len(test_cases_before)} new test cases created!")
                    
                    # Show the new test cases
                    for tc in test_cases_after[len(test_cases_before):]:
                        tc_title = tc.get('fields', {}).get('System.Title', 'Unknown')
                        print(f"      📝 New: {tc['id']}: {tc_title}")
                        
                else:
                    print(f"   ❌ NO NEW TEST CASES CREATED!")
                    print(f"      This indicates the QA Tester Agent is not working properly")
                    print(f"      Check logs for QA Tester Agent errors or JSON parsing issues")
            else:
                print(f"   ⚠️  Discrepancy found but no details available")
        else:
            print(f"   ❌ User Story {target_story} was NOT flagged as missing test cases")
            if len(test_cases_before) > 0:
                print(f"      This might be correct if it already has {len(test_cases_before)} test cases")
            else:
                print(f"      This is unexpected - it has no test cases but wasn't flagged")
        
        # Save debug results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"output/debug_missing_test_cases_{timestamp}.json"
        
        os.makedirs("output", exist_ok=True)
        
        debug_data = {
            'timestamp': timestamp,
            'target_user_story': target_story,
            'user_story_details': {
                'title': title,
                'state': state,
                'area_path': area_path
            },
            'test_cases_before_sweep': len(test_cases_before),
            'test_cases_after_sweep': len(test_cases_after) if 'test_cases_after' in locals() else 'Not checked',
            'sweep_report': report,
            'flagged_for_missing_test_cases': report['summary']['total_discrepancies'] > 0,
            'auto_remediation_successful': len(test_cases_after) > len(test_cases_before) if 'test_cases_after' in locals() else False
        }
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, default=str)
        
        print(f"\n📄 Debug results saved to: {debug_file}")
        logger.info(f"Debug session completed. Results saved to: {debug_file}")
        
        return debug_data
        
    except Exception as e:
        logger.error(f"Debug session failed: {e}")
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test-missing-test-cases":
            test_missing_test_cases()
        elif command == "test-1508":
            test_work_item_1508()
        elif command == "test-all-sweeps":
            test_all_sweep_types()
        elif command == "validate-test-cases":
            validate_test_case_creation()
        elif command == "generate-coverage-report":
            generate_test_case_coverage_report()
        elif command == "debug-missing":
            debug_missing_test_cases()
        elif command == "delete-test-cases":
            delete_data_visualization_test_cases()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands:")
            print("  test-missing-test-cases")
            print("  test-1508") 
            print("  test-all-sweeps")
            print("  validate-test-cases")
            print("  generate-coverage-report")
            print("  debug-missing")
            print("  delete-test-cases")
    else:
        print("Usage: python test_targeted_sweep.py <command>")
        print("Available commands:")
        print("  test-missing-test-cases")
        print("  test-1508")
        print("  test-all-sweeps") 
        print("  validate-test-cases")
        print("  generate-coverage-report")
        print("  debug-missing")
        print("  delete-test-cases")
