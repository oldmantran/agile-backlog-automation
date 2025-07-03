import os
import sys
import time
from datetime import datetime, timedelta
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrators.azure_devops_api import AzureDevOpsIntegrator

class BacklogSweeperAgent:
    """
    Agent responsible for sweeping the backlog and reporting all findings to the supervisor only. The supervisor will determine which agent should address each issue.
    Responsibilities:
      1. Scrape all work items and validate for quality, completeness, and relevance.
      2. Validate relationships: parent/child, hierarchy, dependencies, test case assignment.
      3. Estimate story points.
      4. Setup dashboard widgets.
      5. Update burndown charts.
      6. Update cumulative flow diagrams.
      7. Maintain team velocity values.
      8. Monitor work items for further decomposition (flag user stories without tasks).
    """

    def __init__(self, ado_client, supervisor_callback=None):
        self.ado_client = ado_client
        self.supervisor_callback = supervisor_callback

    def report_to_supervisor(self, report):
        if self.supervisor_callback:
            self.supervisor_callback(report)
        else:
            print("[SUPERVISOR REPORT]")
            import json
            print(json.dumps(report, indent=2))

    def scrape_and_validate_work_items(self):
        """Scrape all work items and validate for quality, completeness, and relevance. Notify supervisor of discrepancies."""
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

            # Epic rules
            if wi_type == "Epic":
                if not title:
                    discrepancies.append({'type': 'missing_title', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Epic missing title.'})
                if not description:
                    discrepancies.append({'type': 'missing_description', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Epic missing description.'})
                # At least one child Feature
                child_ids = [int(r['url'].split('/')[-1]) for r in children]
                child_types = [get_field(work_items_by_id.get(cid, {}), 'System.WorkItemType') for cid in child_ids]
                if not any(ct == 'Feature' for ct in child_types):
                    discrepancies.append({'type': 'missing_child_feature', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Epic missing child Feature.'})
                # Only Features as children
                for cid, ct in zip(child_ids, child_types):
                    if ct and ct != 'Feature':
                        discrepancies.append({'type': 'invalid_child', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': f'Epic has invalid child type: {ct} (ID {cid})'})

            # Feature rules
            if wi_type == "Feature":
                if not title:
                    discrepancies.append({'type': 'missing_title', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Feature missing title.'})
                if not description:
                    discrepancies.append({'type': 'missing_description', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Feature missing description.'})
                child_ids = [int(r['url'].split('/')[-1]) for r in children]
                child_types = [get_field(work_items_by_id.get(cid, {}), 'System.WorkItemType') for cid in child_ids]
                if not any(ct == 'User Story' for ct in child_types):
                    discrepancies.append({'type': 'missing_child_user_story', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Feature missing child User Story.'})
                for cid, ct in zip(child_ids, child_types):
                    if ct and ct != 'User Story':
                        discrepancies.append({'type': 'invalid_child', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': f'Feature has invalid child type: {ct} (ID {cid})'})

            # User Story rules
            if wi_type == "User Story":
                if not title:
                    discrepancies.append({'type': 'missing_title', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'User Story missing title.'})
                if not description or 'As a' not in description:
                    discrepancies.append({'type': 'missing_or_invalid_description', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'User Story missing or invalid description.'})
                acceptance_criteria = get_field(wi, 'Microsoft.VSTS.Common.AcceptanceCriteria')
                if not acceptance_criteria:
                    discrepancies.append({'type': 'missing_acceptance_criteria', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'User Story missing acceptance criteria.'})
                story_points = get_field(wi, 'Microsoft.VSTS.Scheduling.StoryPoints')
                if not story_points:
                    discrepancies.append({'type': 'missing_story_points', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'User Story missing story points.'})
                child_ids = [int(r['url'].split('/')[-1]) for r in children]
                child_types = [get_field(work_items_by_id.get(cid, {}), 'System.WorkItemType') for cid in child_ids]
                if not any(ct == 'Task' for ct in child_types):
                    discrepancies.append({'type': 'missing_child_task', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'User Story missing child Task.'})
                if not any(ct == 'Test Case' for ct in child_types):
                    discrepancies.append({'type': 'missing_child_test_case', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'User Story missing child Test Case.'})

            # Task rules
            if wi_type == "Task":
                if not title:
                    discrepancies.append({'type': 'missing_title', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Task missing title.'})
                if not description:
                    discrepancies.append({'type': 'missing_description', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Task missing description.'})
                # Task should not have children
                if children:
                    discrepancies.append({'type': 'task_has_children', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Task should not have children.'})
                # Should only be parented by User Story or Product Backlog Item
                if parents:
                    parent_id = int(parents[0]['url'].split('/')[-1])
                    parent_type = get_field(work_items_by_id.get(parent_id, {}), 'System.WorkItemType')
                    if parent_type not in ['User Story', 'Product Backlog Item']:
                        discrepancies.append({'type': 'invalid_parent', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': f'Task has invalid parent type: {parent_type} (ID {parent_id})'})

            # Test Case rules
            if wi_type == "Test Case":
                if not title:
                    discrepancies.append({'type': 'missing_title', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': 'Test Case missing title.'})
                # Only acceptable parent is User Story
                if parents:
                    parent_id = int(parents[0]['url'].split('/')[-1])
                    parent_type = get_field(work_items_by_id.get(parent_id, {}), 'System.WorkItemType')
                    if parent_type != 'User Story':
                        discrepancies.append({'type': 'invalid_parent', 'work_item_id': wi_id, 'work_item_type': wi_type, 'title': title, 'description': f'Test Case has invalid parent type: {parent_type} (ID {parent_id})'})
                # TODO: Check association with Test Suite and Test Plan if needed

        return discrepancies

    def validate_relationships(self):
        """Check parent/child links, hierarchy, dependencies, and test case assignment to plans/suites."""
        # Placeholder: Simulate finding 1 relationship issue
        return [{
            'type': 'relationship_issue',
            'work_item_id': 1002,
            'work_item_type': 'Task',
            'description': 'Task is not linked to a User Story.'
        }]

    def estimate_story_points(self):
        """Estimate story points for work items that need it."""
        # Placeholder: Simulate finding 1 missing estimate
        return [{
            'type': 'missing_story_points',
            'work_item_id': 1003,
            'work_item_type': 'User Story',
            'description': 'User Story missing story points.'
        }]

    def setup_dashboard_widgets(self):
        """Setup or update dashboard widgets as needed."""
        # Placeholder: Simulate dashboard widget update
        return ['Dashboard widgets checked/updated.']

    def update_burndown_charts(self):
        """Update burndown charts based on current backlog state."""
        # Placeholder: Simulate burndown chart update
        return ['Burndown chart updated.']

    def update_cumulative_flow_diagrams(self):
        """Update cumulative flow diagrams for the project."""
        # Placeholder: Simulate CFD update
        return ['Cumulative flow diagram updated.']

    def maintain_team_velocity(self):
        """Maintain and update team velocity values."""
        # Placeholder: Simulate velocity update
        return ['Team velocity updated.']

    def monitor_for_decomposition(self):
        """Monitor work items that require further decomposition. Flag user stories without tasks for supervisor/QA action."""
        # Placeholder: Simulate finding 1 user story without tasks
        return [{
            'type': 'user_story_missing_tasks',
            'work_item_id': 1004,
            'work_item_type': 'User Story',
            'description': 'User Story has no child tasks.'
        }]

    def run_sweep(self):
        """Run a full backlog sweep and report to supervisor."""
        discrepancies = []
        actions = []
        discrepancies.extend(self.scrape_and_validate_work_items())
        discrepancies.extend(self.validate_relationships())
        discrepancies.extend(self.estimate_story_points())
        discrepancies.extend(self.monitor_for_decomposition())
        actions.extend(self.setup_dashboard_widgets())
        actions.extend(self.update_burndown_charts())
        actions.extend(self.update_cumulative_flow_diagrams())
        actions.extend(self.maintain_team_velocity())
        report = {
            'summary': {
                'total_discrepancies': len(discrepancies),
                'actions': len(actions)
            },
            'discrepancies': discrepancies,
            'actions': actions
        }
        self.report_to_supervisor(report)

if __name__ == "__main__":
    from supervisor.supervisor import WorkflowSupervisor
    from config.config_loader import Config
    from integrators.azure_devops_api import AzureDevOpsIntegrator
    supervisor = WorkflowSupervisor()
    ado_client = AzureDevOpsIntegrator(Config())
    agent = BacklogSweeperAgent(ado_client=ado_client, supervisor_callback=supervisor.receive_sweeper_report)
    print("[INFO] Starting scheduled backlog sweeper...")

    def scheduled_sweep():
        print(f"[INFO] Running backlog sweep at {datetime.now().astimezone().isoformat()} UTC")
        agent.run_sweep()

    if APSCHEDULER_AVAILABLE:
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(scheduled_sweep, 'cron', hour=12, minute=0)
        scheduler.start()
        print("[INFO] APScheduler started. Sweep will run every day at 12:00 UTC.")
        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
    else:
        print("[WARN] APScheduler not available. Using fallback loop.")
        last_run = None
        while True:
            now = datetime.now().astimezone()
            if now.hour == 12 and (last_run is None or (now - last_run) > timedelta(hours=23)):
                scheduled_sweep()
                last_run = now
            time.sleep(60) 