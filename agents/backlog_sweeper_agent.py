import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
        pass

    def validate_relationships(self):
        """Check parent/child links, hierarchy, dependencies, and test case assignment to plans/suites."""
        pass

    def estimate_story_points(self):
        """Estimate story points for work items that need it."""
        pass

    def setup_dashboard_widgets(self):
        """Setup or update dashboard widgets as needed."""
        pass

    def update_burndown_charts(self):
        """Update burndown charts based on current backlog state."""
        pass

    def update_cumulative_flow_diagrams(self):
        """Update cumulative flow diagrams for the project."""
        pass

    def maintain_team_velocity(self):
        """Maintain and update team velocity values."""
        pass

    def monitor_for_decomposition(self):
        """Monitor work items that require further decomposition. Flag user stories without tasks for supervisor/QA action."""
        pass

if __name__ == "__main__":
    from supervisor.supervisor import WorkflowSupervisor
    supervisor = WorkflowSupervisor()
    agent = BacklogSweeperAgent(ado_client=None, supervisor_callback=supervisor.receive_sweeper_report)
    print("[TEST] Simulating backlog sweep with supervisor integration...")
    mock_report = {
        "summary": {
            "total_work_items": 10,
            "user_stories_missing_tasks": 2,
            "test_cases_without_suites": 1,
            "work_items_missing_story_points": 3,
            "relationship_issues": 1
        },
        "discrepancies": [
            {
                "type": "missing_parent",
                "work_item_id": 101,
                "work_item_type": "Task",
                "description": "Task is not linked to a User Story."
            },
            {
                "type": "test_case_without_suite",
                "work_item_id": 202,
                "work_item_type": "Test Case",
                "description": "Test Case is not assigned to any test suite."
            }
        ],
        "actions": [
            "Assign orphaned test cases to suites.",
            "Decompose user stories missing tasks.",
            "Update dashboard widgets for burndown and velocity."
        ]
    }
    agent.report_to_supervisor(mock_report) 