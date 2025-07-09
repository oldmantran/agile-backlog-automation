import base64
import json
import logging
import requests
from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class TestPlanConfig:
    """Configuration for Azure DevOps Test Plans"""
    name: str
    description: str
    area_path: str
    iteration_path: str
    state: str = 'Active'


@dataclass
class TestSuiteConfig:
    """Configuration for Azure DevOps Test Suites"""
    name: str
    description: str
    suite_type: str = 'StaticTestSuite'
    parent_suite_id: Optional[int] = None


class AzureDevOpsTestClient:
    """
    Azure DevOps Test Management API Client
    Handles Test Plans, Test Suites, and Test Case organization
    """
    
    def __init__(self, organization: str, project: str, personal_access_token: str):
        """
        Initialize the Azure DevOps Test Management client
        
        Args:
            organization: Azure DevOps organization name
            project: Project name
            personal_access_token: PAT with Test Management permissions
        """
        self.organization = organization
        self.project = project
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        
        # Encode PAT for authentication
        auth_string = base64.b64encode(f":{personal_access_token}".encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def ensure_test_plan_exists(self, feature_id: int, feature_name: str) -> Optional[Dict]:
        """
        Create or find test plan for a feature using Test Management API
        
        Args:
            feature_id: Feature work item ID
            feature_name: Feature name for test plan naming
            
        Returns:
            Test plan dictionary or None if creation fails
        """
        try:
            # Check if test plan exists
            existing_plans = self._get_test_plans()
            plan_name = f"Test Plan - {feature_name}"
            
            for plan in existing_plans.get('value', []):
                if plan['name'] == plan_name:
                    self.logger.info(f"Found existing test plan: {plan_name}")
                    return plan
            
            # Create new test plan
            plan_config = TestPlanConfig(
                name=plan_name,
                description=f'Test plan for feature: {feature_name} (ID: {feature_id})',
                area_path=self.project,
                iteration_path=self.project
            )
            
            plan_data = {
                'name': plan_config.name,
                'description': plan_config.description,
                'areaPath': plan_config.area_path,
                'iterationPath': plan_config.iteration_path,
                'state': plan_config.state
            }
            
            response = requests.post(
                f"{self.base_url}/testplan/plans?api-version=7.1-preview.1",
                headers=self.headers,
                json=plan_data,
                timeout=30
            )
            
            if response.status_code == 200:
                test_plan = response.json()
                self.logger.info(f"Created test plan: {plan_name} (ID: {test_plan['id']})")
                return test_plan
            else:
                self.logger.error(f"Failed to create test plan: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error ensuring test plan exists: {e}")
            return None
    
    def ensure_test_suite_exists(self, test_plan_id: int, user_story_id: int, user_story_name: str) -> Optional[Dict]:
        """
        Create or find test suite for a user story using Test Management API
        
        Args:
            test_plan_id: Test plan ID
            user_story_id: User story work item ID
            user_story_name: User story name for test suite naming
            
        Returns:
            Test suite dictionary or None if creation fails
        """
        try:
            # Check if test suite exists
            existing_suites = self._get_test_suites(test_plan_id)
            suite_name = f"User Story: {user_story_name}"
            
            for suite in existing_suites.get('value', []):
                if suite['name'] == suite_name:
                    self.logger.info(f"Found existing test suite: {suite_name}")
                    return suite
            
            # Get root suite for parent reference
            root_suite = None
            for suite in existing_suites.get('value', []):
                if suite.get('suiteType') == 'StaticTestSuite' and suite.get('parentSuite') is None:
                    root_suite = suite
                    break
            
            # Create new test suite
            suite_config = TestSuiteConfig(
                name=suite_name,
                description=f'Test suite for user story: {user_story_name} (ID: {user_story_id})',
                parent_suite_id=root_suite['id'] if root_suite else None
            )
            
            suite_data = {
                'name': suite_config.name,
                'description': suite_config.description,
                'suiteType': suite_config.suite_type
            }
            
            if suite_config.parent_suite_id:
                suite_data['parentSuite'] = {'id': suite_config.parent_suite_id}
            
            response = requests.post(
                f"{self.base_url}/testplan/Plans/{test_plan_id}/suites?api-version=7.1-preview.1",
                headers=self.headers,
                json=suite_data,
                timeout=30
            )
            
            if response.status_code == 200:
                test_suite = response.json()
                self.logger.info(f"Created test suite: {suite_name} (ID: {test_suite['id']})")
                return test_suite
            else:
                self.logger.error(f"Failed to create test suite: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error ensuring test suite exists: {e}")
            return None
    
    def add_test_case_to_suite(self, test_plan_id: int, test_suite_id: int, test_case_id: int) -> bool:
        """
        Add test case to test suite using Test Management API
        
        Args:
            test_plan_id: Test plan ID
            test_suite_id: Test suite ID
            test_case_id: Test case work item ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/testplan/Plans/{test_plan_id}/Suites/{test_suite_id}/TestCase/{test_case_id}?api-version=7.1-preview.3",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Added test case {test_case_id} to test suite {test_suite_id}")
                return True
            else:
                self.logger.error(f"Failed to add test case to suite: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding test case to suite: {e}")
            return False
    
    def create_test_case_work_item(self, title: str, description: str, steps: List[Dict]) -> Optional[Dict]:
        """
        Create test case work item using Work Items API
        
        Args:
            title: Test case title
            description: Test case description
            steps: List of test steps with action and expectedResult
            
        Returns:
            Test case work item dictionary or None if creation fails
        """
        try:
            # Format steps for Azure DevOps
            formatted_steps = self._format_test_steps_for_ado(steps)
            
            # Create work item fields
            fields = [
                {
                    "op": "add",
                    "path": "/fields/System.Title",
                    "value": title
                },
                {
                    "op": "add",
                    "path": "/fields/System.Description",
                    "value": description
                },
                {
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.TCM.Steps",
                    "value": formatted_steps
                }
            ]
            
            response = requests.post(
                f"{self.base_url}/wit/workitems/$Test%20Case?api-version=7.1-preview.3",
                headers={**self.headers, 'Content-Type': 'application/json-patch+json'},
                json=fields,
                timeout=30
            )
            
            if response.status_code == 200:
                test_case = response.json()
                self.logger.info(f"Created test case work item: {title} (ID: {test_case['id']})")
                return test_case
            else:
                self.logger.error(f"Failed to create test case work item: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating test case work item: {e}")
            return None
    
    def _get_test_plans(self) -> Dict:
        """Get all test plans for the project"""
        try:
            response = requests.get(
                f"{self.base_url}/testplan/plans?api-version=7.1-preview.1",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get test plans: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            self.logger.error(f"Error getting test plans: {e}")
            return {'value': []}
    
    def _get_test_suites(self, test_plan_id: int) -> Dict:
        """Get all test suites for a test plan"""
        try:
            response = requests.get(
                f"{self.base_url}/testplan/Plans/{test_plan_id}/suites?api-version=7.1-preview.1",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get test suites: {response.status_code} - {response.text}")
                return {'value': []}
                
        except Exception as e:
            self.logger.error(f"Error getting test suites: {e}")
            return {'value': []}
    
    def _format_test_steps_for_ado(self, steps: List[Dict]) -> str:
        """Format test steps for Azure DevOps Test Case work item"""
        if not steps:
            return "<steps><step><parameterizedString isformatted=\"true\"><DIV><P>Execute test case</P></DIV></parameterizedString><parameterizedString isformatted=\"true\"><DIV><P>Test passes successfully</P></DIV></parameterizedString><description/></step></steps>"
        
        formatted_steps = "<steps>"
        
        for step in steps:
            action = step.get('action', 'Execute step')
            expected_result = step.get('expectedResult', 'Step completes successfully')
            
            formatted_steps += f"""<step>
                <parameterizedString isformatted="true"><DIV><P>{action}</P></DIV></parameterizedString>
                <parameterizedString isformatted="true"><DIV><P>{expected_result}</P></DIV></parameterizedString>
                <description/>
            </step>"""
        
        formatted_steps += "</steps>"
        return formatted_steps

    def get_test_plan_by_name(self, plan_name: str) -> Optional[Dict]:
        """Get test plan by name"""
        try:
            plans = self._get_test_plans()
            for plan in plans.get('value', []):
                if plan['name'] == plan_name:
                    return plan
            return None
        except Exception as e:
            self.logger.error(f"Error getting test plan by name: {e}")
            return None

    def get_test_suite_by_name(self, test_plan_id: int, suite_name: str) -> Optional[Dict]:
        """Get test suite by name within a test plan"""
        try:
            suites = self._get_test_suites(test_plan_id)
            for suite in suites.get('value', []):
                if suite['name'] == suite_name:
                    return suite
            return None
        except Exception as e:
            self.logger.error(f"Error getting test suite by name: {e}")
            return None