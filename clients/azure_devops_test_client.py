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
    suite_type: str = 'RequirementTestSuite'  # Changed to requirement-based for autonomous testing
    parent_suite_id: Optional[int] = None
    requirement_id: Optional[int] = None  # User story work item ID for linking


class AzureDevOpsTestClient:
    """
    Azure DevOps Test Management API Client
    Handles Test Plans, Test Suites, and Test Case organization
    Fixed for proper parent suite handling
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
        
    def ensure_test_plan_exists(self, feature_id: int, feature_name: str, area_path: str = None) -> Optional[Dict]:
        """
        Create or find test plan for a feature using Test Management API
        
        Args:
            feature_id: Feature work item ID
            feature_name: Feature name for test plan naming
            area_path: Area path for the test plan (optional)
            
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
            
            # Use provided area path or default to project
            effective_area_path = area_path or self.project
            
            # Create new test plan
            plan_config = TestPlanConfig(
                name=plan_name,
                description=f'Test plan for feature: {feature_name} (ID: {feature_id})',
                area_path=effective_area_path,
                iteration_path=self.project
            )
            
            self.logger.info(f"Creating test plan '{plan_name}' with area path: {effective_area_path}")
            
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
        Create or find requirement-based test suite for a user story using Test Management API
        
        Args:
            test_plan_id: Test plan ID
            user_story_id: User story work item ID for requirement linking
            user_story_name: User story name for suite naming
            
        Returns:
            Test suite dictionary or None if creation fails
        """
        try:
            # Check if requirement-based test suite exists for this user story
            existing_suites = self._get_test_suites(test_plan_id)
            suite_name = f"User Story: {user_story_name}"
            
            # Look for existing requirement-based suite linked to this user story
            for suite in existing_suites.get('value', []):
                if (suite.get('name') == suite_name and 
                    suite.get('suiteType') == 'RequirementTestSuite' and
                    suite.get('requirementId') == user_story_id):
                    self.logger.info(f"Found existing requirement-based test suite: {suite_name}")
                    return suite
            
            # Find the root test suite (required as parent for requirement-based suites)
            # Azure DevOps creates a default root suite for every test plan
            root_suite = None
            
            # Strategy 1: Look for a StaticTestSuite with no parent
            for suite in existing_suites.get('value', []):
                if (suite.get('suiteType') == 'StaticTestSuite' and 
                    suite.get('parentSuite') is None):
                    root_suite = suite
                    self.logger.info(f"Found root suite via parentSuite=None: {suite.get('name')} (ID: {suite.get('id')})")
                    break
            
            # Strategy 2: If no luck, look for suite with no parent attribute or parent=None
            if not root_suite:
                for suite in existing_suites.get('value', []):
                    parent_suite = suite.get('parentSuite')
                    if parent_suite is None or (isinstance(parent_suite, dict) and not parent_suite):
                        root_suite = suite
                        self.logger.info(f"Found root suite via empty parent: {suite.get('name')} (ID: {suite.get('id')})")
                        break
            
            # Strategy 3: Fall back to the first StaticTestSuite
            if not root_suite:
                for suite in existing_suites.get('value', []):
                    if suite.get('suiteType') == 'StaticTestSuite':
                        root_suite = suite
                        self.logger.info(f"Found root suite via first StaticTestSuite: {suite.get('name')} (ID: {suite.get('id')})")
                        break
            
            # Strategy 4: Last resort - use the first suite
            if not root_suite and existing_suites.get('value'):
                root_suite = existing_suites['value'][0]
                self.logger.warning(f"Using first suite as root (last resort): {root_suite.get('name')} (ID: {root_suite.get('id')})")
            
            if not root_suite:
                self.logger.error(f"Could not find any test suite to use as parent for test plan {test_plan_id}")
                self.logger.debug(f"Available suites: {[s.get('name') + ' (' + s.get('suiteType', 'Unknown') + ')' for s in existing_suites.get('value', [])]}")
                return None
            
            # Create new requirement-based test suite
            suite_config = TestSuiteConfig(
                name=suite_name,
                description=f'Requirement-based test suite for user story: {user_story_name} (ID: {user_story_id})',
                suite_type='RequirementTestSuite',
                parent_suite_id=root_suite['id'],
                requirement_id=user_story_id
            )
            
            self.logger.info(f"Creating requirement-based test suite '{suite_name}' linked to user story {user_story_id} under root suite {root_suite['id']}")
            
            suite_data = {
                'name': suite_config.name,
                'description': suite_config.description,
                'suiteType': suite_config.suite_type,
                'requirementId': suite_config.requirement_id,  # Link to user story for autonomous discovery
                'parentSuite': {'id': suite_config.parent_suite_id}  # Required for requirement-based suites
            }
            
            response = requests.post(
                f"{self.base_url}/testplan/Plans/{test_plan_id}/suites?api-version=7.1-preview.1",
                headers=self.headers,
                json=suite_data,
                timeout=30
            )
            
            if response.status_code == 200:
                test_suite = response.json()
                self.logger.info(f"Created requirement-based test suite: {suite_name} (ID: {test_suite['id']}) linked to user story {user_story_id}")
                return test_suite
            else:
                self.logger.error(f"Failed to create requirement-based test suite: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error ensuring requirement-based test suite exists: {e}")
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
    
    def create_test_case_work_item(self, title: str, description: str, steps: List[Dict], 
                                   tags: List[str] = None, priority: int = 2, 
                                   component: str = None, preconditions: str = None,
                                   automation_status: str = "Not Automated",
                                   area_path: str = None) -> Optional[Dict]:
        """
        Create test case work item with comprehensive metadata for autonomous testing
        
        Args:
            title: Test case title with descriptive verb and expected result
            description: Test case description
            steps: List of test steps with action and expectedResult
            tags: List of tags (e.g., Regression, UI, API) for filtering
            priority: Test case priority (1=High, 2=Normal, 3=Low)
            component: Component or feature area being tested
            preconditions: Clear preconditions for test execution
            automation_status: Automation readiness status
            area_path: Area path for the test case (uses configured area if not provided)
            
        Returns:
            Test case work item dictionary or None if creation fails
        """
        try:
            # Format steps for Azure DevOps
            formatted_steps = self._format_test_steps_for_ado(steps)
            
            # Prepare tags for Azure DevOps format
            tag_string = ";".join(tags) if tags else ""
            
            # Create work item fields with comprehensive metadata
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
                },
                {
                    "op": "add",
                    "path": "/fields/System.Tags",
                    "value": tag_string
                },
                {
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Common.Priority",
                    "value": priority
                },
                {
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.TCM.AutomationStatus", 
                    "value": automation_status
                }
            ]
            
            # Add area path if provided (otherwise uses project default)
            if area_path:
                fields.append({
                    "op": "add",
                    "path": "/fields/System.AreaPath",
                    "value": area_path
                })
            
            # Add optional fields if provided
            if preconditions:
                fields.append({
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.TCM.LocalDataSource",
                    "value": f"Preconditions: {preconditions}"
                })
            
            self.logger.info(f"Creating autonomous test case: {title} with tags: {tag_string}")
            
            response = requests.post(
                f"{self.base_url}/wit/workitems/$Test%20Case?api-version=7.1-preview.3",
                headers={**self.headers, 'Content-Type': 'application/json-patch+json'},
                json=fields,
                timeout=30
            )
            
            if response.status_code == 200:
                test_case = response.json()
                self.logger.info(f"Created autonomous test case work item: {title} (ID: {test_case['id']})")
                return test_case
            else:
                self.logger.error(f"Failed to create test case work item: {response.status_code} - {response.text}")
                return None
                
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
    
    def create_test_case(self, title: str, description: str, steps: List[Dict], 
                        tags: List[str] = None, priority: int = 2, area_path: str = None) -> Optional[Dict]:
        """
        Convenience method for creating test cases with autonomous testing metadata.
        Automatically generates appropriate tags and metadata based on test case content.
        """
        # Auto-generate tags based on test case content
        auto_tags = []
        title_lower = title.lower()
        description_lower = description.lower()
        
        # Determine test type tags
        if any(keyword in title_lower for keyword in ['ui', 'interface', 'button', 'screen', 'page']):
            auto_tags.append('UI')
        if any(keyword in title_lower for keyword in ['api', 'endpoint', 'service', 'request']):
            auto_tags.append('API')
        if any(keyword in title_lower for keyword in ['verify', 'validate', 'check', 'ensure']):
            auto_tags.append('Functional')
        if any(keyword in description_lower for keyword in ['regression', 'existing', 'previous']):
            auto_tags.append('Regression')
        if any(keyword in title_lower for keyword in ['invalid', 'error', 'fail', 'negative']):
            auto_tags.append('Negative')
        else:
            auto_tags.append('Positive')
        
        # Combine auto-generated and provided tags
        all_tags = list(set((tags or []) + auto_tags))
        
        # Extract preconditions from description if present
        preconditions = None
        if 'precondition' in description_lower or 'given' in description_lower:
            # Try to extract preconditions from Gherkin-style scenarios
            lines = description.split('\n')
            for line in lines:
                if line.strip().lower().startswith(('given', 'precondition')):
                    preconditions = line.strip()
                    break
        
        # Determine automation status
        automation_status = "Planned" if any(tag in ['API', 'Functional'] for tag in all_tags) else "Not Automated"
        
        return self.create_test_case_work_item(
            title=title,
            description=description, 
            steps=steps,
            tags=all_tags,
            priority=priority,
            preconditions=preconditions,
            automation_status=automation_status,
            area_path=area_path
        )