import pytest
from supervisor.supervisor import WorkflowSupervisor

@pytest.fixture
def supervisor():
    # Limit each agent to create only one work item of each type for speed
    config = {
        'agent_limits': {
            'epics': 1,
            'features': 1,
            'user_stories': 1,
            'tasks': 1,
            'test_cases': 1
        }
    }
    return WorkflowSupervisor(config_path=None)

def test_epic_strategist_stage_invocation(monkeypatch, supervisor):
    def one_epic(*args, **kwargs):
        return [{
            'title': 'Epic 1',
            'description': 'desc',
            'business_value': 'value',
            'priority': 'High',
            'estimated_complexity': 'S',
            'dependencies': [],
            'success_criteria': ['Done'],
            'features': []
        }]
    monkeypatch.setattr(supervisor.agents['epic_strategist'], 'generate_epics', one_epic)
    supervisor.workflow_data = {
        'product_vision': 'Test vision',
        'epics': []
    }
    supervisor._execute_epic_generation()
    supervisor._validate_epics()
    assert supervisor.workflow_data['epics']

def test_decomposition_agent_stage_invocation(monkeypatch, supervisor):
    def one_feature(*args, **kwargs):
        return [{
            'title': 'Feature 1',
            'description': 'desc',
            'priority': 'High',
            'estimated_story_points': 1,
            'dependencies': [],
            'ui_ux_requirements': [],
            'technical_considerations': [],
            'business_value': 'value',
            'edge_cases': [],
            'user_stories': []
        }]
    monkeypatch.setattr(supervisor.agents['decomposition_agent'], 'decompose_epic', one_feature)
    supervisor.workflow_data = {
        'product_vision': 'Test vision',
        'epics': [{
            'title': 'Epic 1',
            'features': []
        }]
    }
    supervisor._execute_feature_decomposition()
    supervisor._validate_features()
    assert supervisor.workflow_data['epics'][0]['features']

def test_user_story_decomposer_stage_invocation(monkeypatch, supervisor):
    def one_user_story(*args, **kwargs):
        return [{
            'title': 'User Story 1',
            'description': 'desc',
            'acceptance_criteria': ['AC1'],
            'priority': 'Medium',
            'story_points': 1,
            'tags': [],
            'tasks': []
        }]
    monkeypatch.setattr(supervisor.agents['decomposition_agent'], 'decompose_feature_to_user_stories', one_user_story)
    supervisor.workflow_data = {
        'product_vision': 'Test vision',
        'epics': [{
            'title': 'Epic 1',
            'features': [{
                'title': 'Feature 1',
                'user_stories': []
            }]
        }]
    }
    supervisor._execute_user_story_decomposition()
    supervisor._validate_user_stories()
    assert supervisor.workflow_data['epics'][0]['features'][0]['user_stories']

def test_developer_agent_stage_invocation(monkeypatch, supervisor):
    def one_task(*args, **kwargs):
        return [{
            'title': 'Task 1',
            'description': 'desc'
        }]
    monkeypatch.setattr(supervisor.agents['developer_agent'], 'generate_tasks', one_task)
    supervisor.workflow_data = {
        'product_vision': 'Test vision',
        'epics': [{
            'title': 'Epic 1',
            'features': [{
                'title': 'Feature 1',
                'user_stories': [{
                    'title': 'User Story 1',
                    'description': 'desc',
                    'acceptance_criteria': ['AC1'],
                    'priority': 'Medium',
                    'story_points': 3,
                    'tags': []
                }]
            }]
        }]
    }
    supervisor._execute_task_generation()
    supervisor._validate_tasks_and_estimates()
    assert supervisor.workflow_data['epics'][0]['features'][0]['user_stories'][0]['tasks']

def test_qa_tester_agent_stage_invocation(monkeypatch, supervisor):
    def one_test_case(*args, **kwargs):
        return [{
            'title': 'Test Case 1',
            'description': 'desc',
            'steps': ['step1'],
            'expected_result': 'result'
        }]
    def one_test_plan(*args, **kwargs):
        return {'plan': 'Test Plan 1'}
    monkeypatch.setattr(supervisor.agents['qa_tester_agent'], 'generate_user_story_test_cases', one_test_case)
    monkeypatch.setattr(supervisor.agents['qa_tester_agent'], 'create_test_plan_structure', one_test_plan)
    supervisor.workflow_data = {
        'product_vision': 'Test vision',
        'epics': [{
            'title': 'Epic 1',
            'features': [{
                'title': 'Feature 1',
                'user_stories': [{
                    'title': 'User Story 1',
                    'description': 'desc',
                    'acceptance_criteria': ['AC1'],
                    'priority': 'Medium',
                    'story_points': 3,
                    'tags': [],
                    'tasks': [{
                        'title': 'Task 1',
                        'description': 'desc'
                    }]
                }],
                'test_plan_structure': None
            }]
        }]
    }
    supervisor._execute_qa_generation()
    supervisor._validate_test_cases_and_plans()
    assert supervisor.workflow_data['epics'][0]['features'][0]['user_stories'][0]['test_cases']
    assert supervisor.workflow_data['epics'][0]['features'][0]['test_plan_structure']

def test_full_backlog_creation_minimal(monkeypatch, supervisor):
    """Test the full backlog creation workflow with each agent limited to one item per type."""
    # Patch agent methods to limit output to 1 item per type
    def one_epic(*args, **kwargs):
        return [{
            'title': 'Epic 1',
            'description': 'desc',
            'business_value': 'value',
            'priority': 'High',
            'estimated_complexity': 'S',
            'dependencies': [],
            'success_criteria': ['Done'],
            'features': []
        }]
    def one_feature(*args, **kwargs):
        # INCLUDE 'user_stories': [] so the workflow assigns to it
        return [{
            'title': 'Feature 1',
            'description': 'desc',
            'priority': 'High',
            'estimated_story_points': 1,
            'dependencies': [],
            'ui_ux_requirements': [],
            'technical_considerations': [],
            'business_value': 'value',
            'edge_cases': [],
            'user_stories': []
        }]
    def one_user_story(*args, **kwargs):
        return [{
            'title': 'User Story 1',
            'description': 'desc',
            'acceptance_criteria': ['AC1'],
            'priority': 'Medium',
            'story_points': 1,
            'tags': [],
            'tasks': []
        }]
    def one_task(*args, **kwargs):
        return [{
            'title': 'Task 1',
            'description': 'desc'
        }]
    def one_test_case(*args, **kwargs):
        return [{
            'title': 'Test Case 1',
            'description': 'desc',
            'steps': ['step1'],
            'expected_result': 'result'
        }]
    def one_test_plan(*args, **kwargs):
        return {'plan': 'Test Plan 1'}

    # Patch all agent methods
    monkeypatch.setattr(supervisor.agents['epic_strategist'], 'generate_epics', one_epic)
    monkeypatch.setattr(supervisor.agents['decomposition_agent'], 'decompose_epic', one_feature)
    monkeypatch.setattr(supervisor.agents['decomposition_agent'], 'decompose_feature_to_user_stories', one_user_story)
    monkeypatch.setattr(supervisor.agents['developer_agent'], 'generate_tasks', one_task)
    monkeypatch.setattr(supervisor.agents['qa_tester_agent'], 'generate_user_story_test_cases', one_test_case)
    monkeypatch.setattr(supervisor.agents['qa_tester_agent'], 'create_test_plan_structure', one_test_plan)
    monkeypatch.setattr(supervisor.agents['qa_tester_agent'], 'validate_user_story_testability', lambda *a, **k: {'testability_score': 1})

    # Run the full workflow
    result = supervisor.execute_workflow(
        product_vision='Minimal test vision',
        stages=None,
        human_review=False,
        save_outputs=False,
        integrate_azure=False
    )
    # Assertions: Only one of each type should be present
    epics = result['epics']
    assert len(epics) == 1
    features = epics[0]['features']
    assert len(features) == 1
    # Use .get to avoid KeyError and check structure
    user_stories = features[0].get('user_stories')
    assert isinstance(user_stories, list)
    assert len(user_stories) == 1
    tasks = user_stories[0]['tasks']
    assert len(tasks) == 1
    test_cases = user_stories[0]['test_cases']
    assert len(test_cases) == 1
    assert features[0]['test_plan_structure']
