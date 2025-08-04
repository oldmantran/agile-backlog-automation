"""
Azure DevOps API Integration Module

Handles creation and management of work items in Azure DevOps based on
generated backlog artifacts (epics, features, tasks, test cases).
Includes comprehensive test plan management following ADO best practices.
"""

import os
import json
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
import base64
import logging
import urllib.parse
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.config_loader import Config
from clients.azure_devops_test_client import AzureDevOpsTestClient

class AzureDevOpsIntegrator:
    """
    Integrates with Azure DevOps to create work items from generated backlog data.
    
    Supports:
    - Epic creation with business value and high-level strategic goals
    - Feature creation with business value and technical considerations (NO acceptance criteria)
    - User Story creation with acceptance criteria and detailed requirements
    - Task creation with estimates and technical details
    - Test Plan creation with organized test suites
    - Test Suite creation for user story grouping
    - Test Case creation with steps and expected results
    - Hierarchical work item relationships (Epic -> Feature -> User Story -> Task)
    - Test organization (Test Plan -> Test Suite -> Test Case)
    """
    
    def __init__(self, organization_url: str, project: str, personal_access_token: str = None, area_path: str = None, iteration_path: str = None):
        """Initialize Azure DevOps integration with configuration and explicit area/iteration paths."""
        # Parse organization from URL
        if organization_url.startswith("https://dev.azure.com/"):
            self.organization = organization_url.replace("https://dev.azure.com/", "")
        else:
            self.organization = organization_url
        self.project = project
        
        # Use the provided PAT, or fallback to .env if not provided
        if not personal_access_token:
            import os
            self.pat = os.getenv("AZURE_DEVOPS_PAT")
        else:
            self.pat = personal_access_token
        self.logger = logging.getLogger("azure_devops_integrator")

        if not all([self.organization, self.project, self.pat]):
            self.logger.warning("Azure DevOps credentials not configured. Integration will be disabled.")
            self.enabled = False
        else:
            self.enabled = True

        # URL-encode the project name for all API URLs
        import urllib.parse
        self.project_encoded = urllib.parse.quote(self.project)
        self.org_base_url = f"https://dev.azure.com/{self.organization}/_apis"
        
        # Configure robust HTTP session with retry logic and timeouts
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # Maximum number of retries
            status_forcelist=[408, 429, 500, 502, 503, 504],  # HTTP status codes to retry
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST", "PATCH"],
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.base_url = f"https://dev.azure.com/{self.organization}/{self.project_encoded}/_apis"
        self.project_base_url = f"https://dev.azure.com/{self.organization}/{self.project_encoded}/_apis"
        self.work_items_url = f"{self.base_url}/wit/workitems"
        self.test_plans_url = f"{self.base_url}/testplan/plans"
        self.test_suites_url = f"{self.base_url}/testplan/suites"
        
        # Initialize test management client
        if self.enabled:
            self.test_client = AzureDevOpsTestClient(
                organization=self.organization,
                project=self.project,
                personal_access_token=self.pat
            )
        else:
            self.test_client = None
        
        # Set up authentication
        self.auth = HTTPBasicAuth('', self.pat)
        self.headers = {
            'Content-Type': 'application/json-patch+json',
            'Accept': 'application/json'
        }
        # Headers for WIQL queries (different content type)
        self.wiql_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Area/iteration path must be provided by API payload
        if not area_path or not iteration_path:
            raise ValueError("Area path and iteration path must be provided by the frontend/API payload.")
        self.area_path = area_path
        self.iteration_path = iteration_path
        
        # Always prepend project name to area/iteration path if not already present
        if self.area_path and not self.area_path.startswith(self.project + "\\"):
            self.area_path = f"{self.project}\\{self.area_path}"
        if self.iteration_path and not self.iteration_path.startswith(self.project + "\\"):
            self.iteration_path = f"{self.project}\\{self.iteration_path}"
        
        # Ensure area/iteration path exists in ADO, create if missing
        self._ensure_area_and_iteration_paths()
        
        # Cache for created test plans and suites
        self.test_plans_cache = {}
        self.test_suites_cache = {}

        # Debug: Log the PAT (masked) to confirm it is loaded
        if self.pat:
            masked_pat = self.pat[:4] + '...' + self.pat[-4:]
            self.logger.info(f"Loaded Azure DevOps PAT: {masked_pat}")
        else:
            self.logger.warning("Azure DevOps PAT is missing or not loaded!")

    def get_available_area_paths(self) -> list:
        """Get all available area paths in the project."""
        url = f"{self.project_base_url}/wit/classificationnodes/areas?$depth=10&api-version=7.0"
        
        # Use correct headers for classification nodes API
        classification_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = self.session.get(url, auth=self.auth, headers=classification_headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Recursively collect all area paths
            def collect_paths(node, prefix=None):
                paths = []
                name = node['name']
                path = f"{prefix}\\{name}" if prefix else name
                paths.append(path)
                for child in node.get('children', []):
                    paths.extend(collect_paths(child, path))
                return paths
            return collect_paths(data)
        except Exception as e:
            self.logger.error(f"Failed to fetch area paths: {e}")
            return []

    def get_available_iteration_paths(self) -> list:
        """Get all available iteration paths in the project."""
        url = f"{self.project_base_url}/wit/classificationnodes/iterations?$depth=10&api-version=7.0"
        
        # Use correct headers for classification nodes API
        classification_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = self.session.get(url, auth=self.auth, headers=classification_headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Recursively collect all iteration paths
            def collect_paths(node, prefix=None):
                paths = []
                name = node['name']
                path = f"{prefix}\\{name}" if prefix else name
                paths.append({"path": path, "name": name})
                for child in node.get('children', []):
                    paths.extend(collect_paths(child, path))
                return paths
            return collect_paths(data)
        except Exception as e:
            self.logger.error(f"Failed to fetch iteration paths: {e}")
            return []

    def _ensure_area_and_iteration_paths(self):
        """Ensure area and iteration paths exist in Azure DevOps, create if missing."""
        # Area Path
        area_paths = self.get_available_area_paths()
        self.logger.info(f"Available area paths: {area_paths}")
        self.logger.info(f"Checking for area path: {self.area_path}")
        
        # Accept both direct area name and full path for matching
        area_path_valid = self.area_path in area_paths or any(
            ap.split('\\')[-1] == self.area_path for ap in area_paths
        )
        
        if not area_path_valid:
            self.logger.info(f"Area path '{self.area_path}' not found. Creating...")
            # If area_path contains backslashes, split to get parent and child
            if '\\' in self.area_path:
                parent_path, area_name = self.area_path.rsplit('\\', 1)
                self.logger.info(f"Creating area '{area_name}' under parent '{parent_path}'")
                
                # Check if parent exists and is not the root project
                if parent_path == self.project:
                    # Parent is the root project, create directly under root
                    self.logger.info(f"Parent is root project, creating '{area_name}' under project root")
                    self.create_area_path(area_name)
                elif parent_path not in area_paths:
                    self.logger.warning(f"Parent path '{parent_path}' not found. Creating under project root instead.")
                    self.create_area_path(area_name)
                else:
                    self.create_area_path(area_name, parent_path)
            else:
                self.logger.info(f"Creating area '{self.area_path}' under project root")
                self.create_area_path(self.area_path)
        else:
            self.logger.info(f"Area path '{self.area_path}' already exists")
            
        # Iteration Path
        iteration_paths = [it['path'] for it in self.get_available_iteration_paths()]
        self.logger.info(f"Available iteration paths: {iteration_paths}")
        self.logger.info(f"Checking for iteration path: {self.iteration_path}")
        
        if self.iteration_path not in iteration_paths:
            self.logger.info(f"Iteration path '{self.iteration_path}' not found. Creating...")
            # For now, create a simple iteration without date ranges
            # In a real implementation, you'd want to provide proper dates
            iteration_name = self.iteration_path.split('\\')[-1]
            self.logger.info(f"Creating iteration '{iteration_name}'")
            # Skip iteration creation for now as it requires date ranges
            self.logger.warning(f"Iteration path creation not fully implemented - skipping")
        else:
            self.logger.info(f"Iteration path '{self.iteration_path}' already exists")

    def create_work_items(self, backlog_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create all work items from backlog data in Azure DevOps with proper test plan organization.
        
        Args:
            backlog_data: Complete backlog with epics, features, user stories, tasks, and test cases
            
        Returns:
            List of created work item details with IDs and URLs
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        created_items = []
        
        try:
            self.logger.info("Starting Azure DevOps work item creation with test plan organization")
            
            # Create epics first
            for epic_data in backlog_data.get('epics', []):
                epic_item = self._create_epic(epic_data)
                created_items.append(epic_item)
                
                # Create features for this epic
                for feature_data in epic_data.get('features', []):
                    feature_item = self._create_feature(feature_data, epic_item['id'])
                    created_items.append(feature_item)
                    
                    # Create test plan for this feature (following ADO best practices)
                    test_plan = None
                    if feature_data.get('test_cases') or any(story.get('test_cases') for story in feature_data.get('user_stories', [])):
                        test_plan = self._create_test_plan(feature_data, feature_item['id'])
                        created_items.append(test_plan)
                    
                    # Create user stories for this feature
                    for user_story_data in feature_data.get('user_stories', []):
                        user_story_item = self._create_user_story(user_story_data, feature_item['id'])
                        created_items.append(user_story_item)
                        
                        # Create tasks for this user story
                        for task_data in user_story_data.get('tasks', []):
                            task_item = self._create_task(task_data, user_story_item['id'])
                            created_items.append(task_item)
                        
                        # Create test suite and test cases for this user story (improved organization)
                        if user_story_data.get('test_cases') and test_plan:
                            test_suite = self._create_test_suite(user_story_data, test_plan['id'], user_story_item['id'])
                            if test_suite:  # Only proceed if test suite was created successfully
                                created_items.append(test_suite)
                                
                                for test_case_data in user_story_data.get('test_cases', []):
                                    test_item = self._create_test_case(test_case_data, user_story_item['id'], test_suite['id'])
                                    if test_item:  # Only add if test case was created successfully
                                        created_items.append(test_item)
                            else:
                                self.logger.warning(f"Failed to create test suite for user story: {user_story_data.get('title', 'Unknown')}")
                    
                    # Handle feature-level test cases (create default suite if needed)
                    if feature_data.get('test_cases') and test_plan:
                        default_suite = self._create_default_test_suite(feature_data, test_plan['id'], feature_item['id'])
                        if default_suite:  # Only proceed if default suite was created successfully
                            created_items.append(default_suite)
                            
                            for test_case_data in feature_data.get('test_cases', []):
                                test_item = self._create_test_case(test_case_data, feature_item['id'], default_suite['id'])
                                if test_item:  # Only add if test case was created successfully
                                    created_items.append(test_item)
                        else:
                            self.logger.warning(f"Failed to create default test suite for feature: {feature_data.get('title', 'Unknown')}")
            
            self.logger.info(f"Successfully created {len(created_items)} work items with organized test plans")
            return created_items
            
        except Exception as e:
            self.logger.error(f"Failed to create work items: {e}")
            raise
    
    def create_epic(self, epic_data: Dict[str, Any]) -> int:
        """Create an Epic work item and return its ID."""
        epic_item = self._create_epic(epic_data)
        return epic_item['id']
    
    def _create_epic(self, epic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an Epic work item."""
        fields = {
            '/fields/System.Title': epic_data.get('title', 'Untitled Epic'),
            '/fields/System.Description': self._format_epic_description(epic_data),
            '/fields/Microsoft.VSTS.Common.Priority': self._map_priority(epic_data.get('priority', 'Medium')),
            '/fields/Microsoft.VSTS.Common.ValueArea': 'Business',  # Required for Agile process
        }
        
        # Add business value if provided (must be numeric)
        business_value = epic_data.get('business_value')
        if business_value:
            # Try to convert to numeric value, default to 100 if it's descriptive text
            try:
                if isinstance(business_value, (int, float)):
                    fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = business_value
                elif isinstance(business_value, str) and business_value.strip():
                    # Try to parse as number, otherwise default to 100
                    try:
                        fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = float(business_value)
                    except ValueError:
                        # If it's descriptive text, assign a default numeric value
                        fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = 100
            except:
                fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = 100
        
        # Add area and iteration paths if configured
        if self.area_path:
            fields['/fields/System.AreaPath'] = self.area_path
        if self.iteration_path:
            fields['/fields/System.IterationPath'] = self.iteration_path
        
        return self._create_work_item('Epic', fields)
    
    def create_feature(self, feature_data: Dict[str, Any], parent_epic_id: int) -> int:
        """Create a Feature work item and return its ID."""
        feature_item = self._create_feature(feature_data, parent_epic_id)
        return feature_item['id']
    
    def _create_feature(self, feature_data: Dict[str, Any], parent_epic_id: int) -> Dict[str, Any]:
        """Create a Feature work item."""
        fields = {
            '/fields/System.Title': feature_data.get('title', 'Untitled Feature'),
            '/fields/System.Description': self._format_feature_description(feature_data),
            '/fields/Microsoft.VSTS.Common.Priority': self._map_priority(feature_data.get('priority', 'Medium')),
            '/fields/Microsoft.VSTS.Common.ValueArea': 'Business',  # Required for Agile process
        }
        
        # Add business value if provided (must be numeric)
        business_value = feature_data.get('business_value')
        if business_value:
            # Try to convert to numeric value, default to 50 if it's descriptive text
            try:
                if isinstance(business_value, (int, float)):
                    fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = business_value
                elif isinstance(business_value, str) and business_value.strip():
                    # Try to parse as number, otherwise default to 50
                    try:
                        fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = float(business_value)
                    except ValueError:
                        # If it's descriptive text, assign a default numeric value
                        fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = 50
            except:
                fields['/fields/Microsoft.VSTS.Common.BusinessValue'] = 50
        
        # Add area and iteration paths if configured
        if self.area_path:
            fields['/fields/System.AreaPath'] = self.area_path
        if self.iteration_path:
            fields['/fields/System.IterationPath'] = self.iteration_path
        
        feature_item = self._create_work_item('Feature', fields)
        
        # Link to parent epic
        self._create_parent_link(feature_item['id'], parent_epic_id)
        
        return feature_item
    
    def create_user_story(self, story_data: Dict[str, Any], parent_feature_id: int) -> int:
        """Create a User Story work item and return its ID."""
        story_item = self._create_user_story(story_data, parent_feature_id)
        return story_item['id']
    
    def _create_task(self, task_data: Dict[str, Any], parent_user_story_id: int) -> Dict[str, Any]:
        """Create a Task work item under a User Story."""
        fields = {
            '/fields/System.Title': task_data.get('title', 'Untitled Task'),
            '/fields/System.Description': self._format_task_description(task_data),
            '/fields/Microsoft.VSTS.Common.Priority': self._map_priority(task_data.get('priority', 'Medium')),
            '/fields/Microsoft.VSTS.Scheduling.OriginalEstimate': task_data.get('estimate_hours', 0),
        }
        
        # Add area and iteration paths if configured
        if self.area_path:
            fields['/fields/System.AreaPath'] = self.area_path
        if self.iteration_path:
            fields['/fields/System.IterationPath'] = self.iteration_path
        
        task_item = self._create_work_item('Task', fields)
        
        # Link to parent user story
        self._create_parent_link(task_item['id'], parent_user_story_id)
        
        return task_item
    
    def create_task(self, task_data: Dict[str, Any], parent_user_story_id: int) -> int:
        """Create a Task work item and return its ID."""
        task_item = self._create_task(task_data, parent_user_story_id)
        return task_item['id']
    
    def _create_test_case(self, test_case_data: Dict[str, Any], parent_id: int, suite_id: int = None) -> Dict[str, Any]:
        """Create a Test Case work item and optionally assign to a test suite."""
        
        # Use test client for better test step formatting
        if self.test_client:
            steps = self._format_test_steps_for_test_client(test_case_data.get('steps', []))
            test_case_wi = self.test_client.create_test_case_work_item(
                title=test_case_data.get('title', 'Untitled Test Case'),
                description=test_case_data.get('description', ''),
                steps=steps,
                area_path=self.area_path  # Pass the configured area path
            )
            
            if not test_case_wi:
                # Fallback to original method if test client fails
                return self._create_test_case_fallback(test_case_data, parent_id, suite_id)
            
            # Convert test client response to match expected format
            result = {
                'id': test_case_wi['id'],
                'type': 'Test Case',
                'title': test_case_wi['fields']['System.Title'],
                'url': test_case_wi['_links']['html']['href'],
                'state': test_case_wi['fields']['System.State']
            }
            
        else:
            # Fallback to original work item creation
            result = self._create_test_case_fallback(test_case_data, parent_id, suite_id)
        
        # Link to parent (User Story or Feature)
        self._create_parent_link(result['id'], parent_id)
        
        # Add to test suite if specified using test client
        if suite_id and self.test_client:
            try:
                # Get test plan ID from suite (you'll need to implement this)
                test_plan_id = self._get_test_plan_id_from_suite(suite_id)
                if test_plan_id:
                    success = self.test_client.add_test_case_to_suite(test_plan_id, suite_id, result['id'])
                    if success:
                        result['suite_id'] = suite_id
                        self.logger.info(f"Test case {result['id']} added to test suite {suite_id}")
                    else:
                        self.logger.warning(f"Failed to add test case to suite {suite_id}")
            except Exception as e:
                self.logger.warning(f"Failed to add test case to suite: {e}")
        
        return result

    def _create_test_case_fallback(self, test_case_data: Dict[str, Any], parent_id: int, suite_id: int = None) -> Dict[str, Any]:
        """Fallback method using direct work item API when test client is unavailable."""
        fields = {
            '/fields/System.Title': test_case_data.get('title', 'Untitled Test Case'),
            '/fields/System.Description': test_case_data.get('description', ''),
            '/fields/Microsoft.VSTS.Common.Priority': self._map_priority(test_case_data.get('priority', 'Medium')),
            '/fields/Microsoft.VSTS.TCM.Steps': self._format_test_steps(test_case_data.get('steps', [])),
        }
        
        # Add area and iteration paths if configured
        if self.area_path:
            fields['/fields/System.AreaPath'] = self.area_path
        if self.iteration_path:
            fields['/fields/System.IterationPath'] = self.iteration_path
        
        return self._create_work_item('Test Case', fields)

    def _format_test_steps_for_test_client(self, steps: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format test steps for the test client."""
        if not steps:
            return [{'action': 'Execute test case', 'expectedResult': 'Test passes successfully'}]
        
        formatted_steps = []
        for step in steps:
            formatted_steps.append({
                'action': step.get('action', 'Execute step'),
                'expectedResult': step.get('expected_result', step.get('expectedResult', 'Step completes successfully'))
            })
        
        return formatted_steps

    def _get_test_plan_id_from_suite(self, suite_id: int) -> Optional[int]:
        """Get test plan ID from a test suite ID."""
        # This would need to be implemented based on your test suite caching or API call
        # For now, you could maintain a mapping in your test_suites_cache
        for plan_id, suites in self.test_suites_cache.items():
            if suite_id in [s.get('id') for s in suites]:
                return plan_id
        return None
    
    def _create_test_plan(self, feature_data: Dict[str, Any], feature_id: int) -> Dict[str, Any]:
        """Create a test plan for a feature using the dedicated test client."""
        if not self.test_client:
            self.logger.warning("Test client not available - skipping test plan creation")
            return None
        
        feature_name = feature_data.get('title', 'Unknown Feature')
        # Pass the configured area path to ensure test plan is created in correct area
        test_plan = self.test_client.ensure_test_plan_exists(feature_id, feature_name, self.area_path)
        
        if test_plan:
            # Cache the test plan for later use
            self.test_plans_cache[feature_id] = test_plan
            
            return {
                'id': test_plan['id'],
                'type': 'Test Plan',
                'title': test_plan['name'],
                'url': f"https://dev.azure.com/{self.organization}/{self.project}/_testPlans/execute?planId={test_plan['id']}",
                'state': test_plan.get('state', 'Active')
            }
        return None

    def _create_test_suite(self, user_story_data: Dict[str, Any], test_plan_id: int, user_story_id: int) -> Dict[str, Any]:
        """Create a test suite for a user story using the dedicated test client."""
        if not self.test_client:
            self.logger.warning("Test client not available - skipping test suite creation")
            return None
        
        user_story_name = user_story_data.get('title', 'Unknown User Story')
        test_suite = self.test_client.ensure_test_suite_exists(test_plan_id, user_story_id, user_story_name)
        
        if test_suite:
            # Cache the test suite for later use
            if test_plan_id not in self.test_suites_cache:
                self.test_suites_cache[test_plan_id] = []
            self.test_suites_cache[test_plan_id].append(test_suite)
            
            return {
                'id': test_suite['id'],
                'type': 'Test Suite',
                'title': test_suite['name'],
                'url': f"https://dev.azure.com/{self.organization}/{self.project}/_testPlans/execute?planId={test_plan_id}&suiteId={test_suite['id']}",
                'state': 'Active'
            }
        return None

    def _create_default_test_suite(self, feature_data: Dict[str, Any], test_plan_id: int, feature_id: int) -> Dict[str, Any]:
        """Create a default test suite for feature-level test cases."""
        if not self.test_client:
            self.logger.warning("Test client not available - skipping default test suite creation")
            return None
        
        feature_name = feature_data.get('title', 'Unknown Feature')
        suite_name = f"Feature Tests: {feature_name}"
        
        # Create a generic test suite for feature-level tests
        test_suite = self.test_client.ensure_test_suite_exists(test_plan_id, feature_id, suite_name)
        
        if test_suite:
            # Cache the test suite for later use
            if test_plan_id not in self.test_suites_cache:
                self.test_suites_cache[test_plan_id] = []
            self.test_suites_cache[test_plan_id].append(test_suite)
            
            return {
                'id': test_suite['id'],
                'type': 'Test Suite',
                'title': test_suite['name'],
                'url': f"https://dev.azure.com/{self.organization}/{self.project}/_testPlans/execute?planId={test_plan_id}&suiteId={test_suite['id']}",
                'state': 'Active'
            }
        return None

    def _create_user_story(self, story_data: Dict[str, Any], parent_feature_id: int) -> Dict[str, Any]:
        """Create a User Story work item with proper acceptance criteria field mapping."""
        fields = {
            '/fields/System.Title': story_data.get('title', 'Untitled User Story'),
            '/fields/System.Description': self._format_user_story_description(story_data),
            '/fields/Microsoft.VSTS.Common.Priority': self._map_priority(story_data.get('priority', 'Medium')),
            '/fields/Microsoft.VSTS.Common.ValueArea': 'Business',
            '/fields/Microsoft.VSTS.Scheduling.StoryPoints': story_data.get('story_points', 0),
        }
        
        # Add acceptance criteria to the dedicated ADO field if available
        if story_data.get('acceptance_criteria'):
            # Format acceptance criteria for the dedicated ADO field
            acceptance_criteria_text = self._format_acceptance_criteria_for_ado(story_data['acceptance_criteria'])
            fields['/fields/Microsoft.VSTS.Common.AcceptanceCriteria'] = acceptance_criteria_text
        
        # Add area and iteration paths if configured
        if self.area_path:
            fields['/fields/System.AreaPath'] = self.area_path
        if self.iteration_path:
            fields['/fields/System.IterationPath'] = self.iteration_path
        
        user_story_item = self._create_work_item('User Story', fields)
        
        # Link to parent feature
        self._create_parent_link(user_story_item['id'], parent_feature_id)
        
        return user_story_item
    
    def _create_work_item(self, work_item_type: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create a work item with specified type and fields."""
        # URL encode the work item type to handle spaces
        encoded_type = urllib.parse.quote(work_item_type)
        url = f"{self.project_base_url}/wit/workitems/${encoded_type}?api-version=7.0"
        
        # Build patch document
        patch_document = []
        for field_path, value in fields.items():
            patch_document.append({
                'op': 'add',
                'path': field_path,
                'value': value
            })
        
        # Debug logging
        self.logger.info(f"Creating work item: {work_item_type}")
        self.logger.info(f"URL: {url}")
        self.logger.info(f"Fields: {patch_document}")
        
        # Debug: Log the patch document for work item creation
        self.logger.info(f"Work item PATCH payload: {json.dumps(patch_document, indent=2)}")
        
        try:
            response = self.session.post(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers,
                timeout=60  # 60 seconds timeout for work item creation
            )
            
            # Log response details for debugging
            self.logger.info(f"Response status: {response.status_code}")
            if response.status_code >= 400:
                self.logger.error(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            work_item = response.json()
            
            result = {
                'id': work_item['id'],
                'type': work_item_type,
                'title': fields.get('/fields/System.Title', 'Untitled'),
                'url': work_item['_links']['html']['href'],
                'state': work_item['fields']['System.State']
            }
            
            self.logger.info(f"Created {work_item_type}: {result['title']} (ID: {result['id']})")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create {work_item_type}: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def _create_parent_link(self, child_id: int, parent_id: int):
        """Create a parent-child relationship between work items."""
        url = f"{self.project_base_url}/wit/workitems/{child_id}?api-version=7.0"
        
        patch_document = [{
            'op': 'add',
            'path': '/relations/-',
            'value': {
                'rel': 'System.LinkTypes.Hierarchy-Reverse',
                'url': f"{self.project_base_url}/wit/workitems/{parent_id}"
            }
        }]
        
        try:
            response = self.session.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers,
                timeout=30  # 30 seconds timeout for linking operations
            )
            response.raise_for_status()
            
            self.logger.debug(f"Linked work item {child_id} to parent {parent_id}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create parent link: {e}")
            # Don't raise here, as the work item was created successfully
    
    def _format_epic_description(self, epic_data: Dict[str, Any]) -> str:
        """Format epic description with all relevant details using proper HTML formatting."""
        description = epic_data.get('description', '')
        
        # Add business value
        if epic_data.get('business_value'):
            description += f"<p><strong>Business Value:</strong><br>{epic_data['business_value']}</p>"
        
        # Add success criteria
        if epic_data.get('success_criteria'):
            description += "<p><strong>Success Criteria:</strong></p>"
            for criterion in epic_data['success_criteria']:
                description += f"<p>• {criterion}</p>"
        
        # Add dependencies
        if epic_data.get('dependencies'):
            description += "<p><strong>Dependencies:</strong></p>"
            for dependency in epic_data['dependencies']:
                description += f"<p>• {dependency}</p>"
        
        # Add risks
        if epic_data.get('risks'):
            description += "<p><strong>Risks:</strong></p>"
            for risk in epic_data['risks']:
                description += f"<p>• {risk}</p>"
        
        return description
    
    def _format_feature_description(self, feature_data: Dict[str, Any]) -> str:
        """Format feature description focusing on business value and high-level functionality using proper HTML formatting."""
        description = feature_data.get('description', '')
        
        # Add business value if available
        if feature_data.get('business_value'):
            description += f"<p><strong>Business Value:</strong><br>{feature_data['business_value']}</p>"
        
        # Add UI/UX requirements if available
        if feature_data.get('ui_ux_requirements'):
            description += "<p><strong>UI/UX Requirements:</strong></p>"
            for requirement in feature_data['ui_ux_requirements']:
                description += f"<p>• {requirement}</p>"
        
        # Add technical considerations if available
        if feature_data.get('technical_considerations'):
            description += "<p><strong>Technical Considerations:</strong></p>"
            for consideration in feature_data['technical_considerations']:
                description += f"<p>• {consideration}</p>"
        
        # Add dependencies if available
        if feature_data.get('dependencies'):
            description += "<p><strong>Dependencies:</strong></p>"
            for dependency in feature_data['dependencies']:
                description += f"<p>• {dependency}</p>"
        
        return description
    
    def _format_task_description(self, task_data: Dict[str, Any]) -> str:
        """Format task description with technical details using proper HTML formatting."""
        description = task_data.get('description', '')
        
        # Add technical requirements
        if task_data.get('technical_requirements'):
            description += "<p><strong>Technical Requirements:</strong></p>"
            for req in task_data['technical_requirements']:
                description += f"<p>• {req}</p>"
        
        # Add definition of done
        if task_data.get('definition_of_done'):
            description += "<p><strong>Definition of Done:</strong></p>"
            for item in task_data['definition_of_done']:
                description += f"<p>• {item}</p>"
        
        return description
    
    def _format_acceptance_criteria_for_ado(self, acceptance_criteria: List[str]) -> str:
        """Format acceptance criteria for Azure DevOps Acceptance Criteria field with proper HTML formatting."""
        if not acceptance_criteria:
            return ""
        
        # Format as a numbered list with HTML formatting for better readability
        formatted_criteria = []
        for i, criterion in enumerate(acceptance_criteria, 1):
            formatted_criteria.append(f"<p>{i}. {criterion}</p>")
        
        # Join with empty line for proper HTML spacing
        return "".join(formatted_criteria)

    def _format_user_story_description(self, story_data: Dict[str, Any]) -> str:
        """Format user story description without acceptance criteria (they go in dedicated field) using proper HTML formatting."""
        description = story_data.get('description', '')
        
        # Don't duplicate user story in description - it's already in the title
        # The user_story field is used for the title, description should contain implementation details
        
        # Add definition of ready if available
        if story_data.get('definition_of_ready'):
            description += "<p><strong>Definition of Ready:</strong></p>"
            for item in story_data['definition_of_ready']:
                description += f"<p>• {item}</p>"
        
        # Add definition of done if available
        if story_data.get('definition_of_done'):
            description += "<p><strong>Definition of Done:</strong></p>"
            for item in story_data['definition_of_done']:
                description += f"<p>• {item}</p>"
        
        # Note: Acceptance criteria are now stored in the dedicated ADO field
        
        return description
    
    def _format_test_steps(self, steps: List[Dict[str, Any]]) -> str:
        """Format test steps for Azure DevOps test case."""
        if not steps:
            return ""
        
        # Azure DevOps expects XML format for test steps
        steps_xml = "<steps>"
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'No action specified')
            expected = step.get('expected_result', 'No expected result specified')
            
            steps_xml += f"""
            <step id="{i}">
                <parameterizedString isformatted="true">
                    <DIV><P>{action}</P></DIV>
                </parameterizedString>
                <parameterizedString isformatted="true">
                    <DIV><P>{expected}</P></DIV>
                </parameterizedString>
                <description/>
            </step>"""
        
        steps_xml += "</steps>"
        return steps_xml
    
    def _map_priority(self, priority: str) -> int:
        """Map priority string to Azure DevOps priority number."""
        priority_mapping = {
            'high': 1,
            'medium': 2,
            'low': 3,
            'critical': 1,
            'normal': 2
        }
        
        return priority_mapping.get(priority.lower(), 2)  # Default to Medium
    
    # Delegation methods for test management (replace duplicate public methods)
    def ensure_test_plan_exists(self, feature_id: int, feature_name: str) -> Dict:
        """Ensure a test plan exists for a feature, create if it doesn't."""
        if not self.test_client:
            raise ValueError("Test client not available - Azure DevOps integration disabled")
        
        return self.test_client.ensure_test_plan_exists(feature_id, feature_name)

    def ensure_test_suite_exists(self, test_plan_id: int, user_story_id: int, user_story_name: str) -> Dict:
        """Ensure a test suite exists for a user story in a test plan, create if it doesn't."""
        if not self.test_client:
            raise ValueError("Test client not available - Azure DevOps integration disabled")
        
        return self.test_client.ensure_test_suite_exists(test_plan_id, user_story_id, user_story_name)

    def add_test_case_to_suite(self, test_plan_id: int, test_suite_id: int, test_case_id: int) -> bool:
        """Add a test case to a test suite."""
        if not self.test_client:
            raise ValueError("Test client not available - Azure DevOps integration disabled")
        
        return self.test_client.add_test_case_to_suite(test_plan_id, test_suite_id, test_case_id)

    def create_test_case(self, title: str, description: str, steps: list) -> Optional[Dict]:
        """Create a test case work item."""
        if not self.test_client:
            raise ValueError("Test client not available - Azure DevOps integration disabled")
        
        return self.test_client.create_test_case_work_item(title, description, steps, area_path=self.area_path)
    
    def create_test_case_with_data(self, test_case_data: Dict[str, Any], parent_id: int, suite_id: int = None) -> int:
        """Create a Test Case work item from data and return its ID."""
        test_case_item = self._create_test_case(test_case_data, parent_id, suite_id)
        return test_case_item['id']

    # Helper methods for Azure DevOps API operations
    def _get_auth(self) -> HTTPBasicAuth:
        """Get authentication for Azure DevOps requests."""
        return HTTPBasicAuth('', self.pat)

    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle Azure DevOps API response."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Azure DevOps API error: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise

    def get_work_item_relations(self, work_item_id: int) -> List[Dict]:
        """Get work item relations."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        url = f"{self.project_base_url}/wit/workitems/{work_item_id}?$expand=relations&api-version=7.0"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            work_item = response.json()
            return work_item.get('relations', [])
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get work item relations for {work_item_id}: {e}")
            return []

    def get_work_item_details(self, work_item_ids: List[int]) -> List[Dict]:
        """Get detailed work item information for multiple IDs."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        if not work_item_ids:
            return []
        
        # Azure DevOps API supports batch requests for up to 200 work items
        batch_size = 200
        all_work_items = []
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            ids_param = ','.join(str(id) for id in batch_ids)
            
            url = f"{self.project_base_url}/wit/workitems?ids={ids_param}&api-version=7.0"
            
            try:
                response = requests.get(url, auth=self.auth)
                response.raise_for_status()
                batch_result = response.json()
                all_work_items.extend(batch_result.get('value', []))
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Failed to get work item details for batch {batch_ids}: {e}")
                continue
        
        return all_work_items

    def create_work_item_relation(self, source_id: int, target_id: int, relation_type: str) -> bool:
        """Create a relation between two work items."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        url = f"{self.project_base_url}/wit/workitems/{source_id}?api-version=7.0"
        
        patch_document = [{
            'op': 'add',
            'path': '/relations/-',
            'value': {
                'rel': relation_type,
                'url': f"{self.project_base_url}/wit/workitems/{target_id}"
            }
        }]
        
        try:
            response = self.session.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers,
                timeout=30  # 30 seconds timeout for linking operations
            )
            response.raise_for_status()
            
            self.logger.info(f"Created relation {relation_type} between {source_id} and {target_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create work item relation: {e}")
            return False
    
    def get_work_item(self, work_item_id: int) -> Dict[str, Any]:
        """Retrieve a work item by ID."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        url = f"{self.project_base_url}/wit/workitems/{work_item_id}?api-version=7.0"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve work item {work_item_id}: {e}")
            raise
    
    def update_work_item(self, work_item_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing work item."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        url = f"{self.project_base_url}/wit/workitems/{work_item_id}?api-version=7.0"
        
        # Build patch document
        patch_document = []
        for field_path, value in fields.items():
            patch_document.append({
                'op': 'replace',
                'path': field_path,
                'value': value
            })
        
        try:
            response = self.session.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers,
                timeout=30  # 30 seconds timeout for linking operations
            )
            response.raise_for_status()
            
            self.logger.info(f"Updated work item {work_item_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update work item {work_item_id}: {e}")
            raise
    
    def delete_work_item(self, work_item_id: int) -> bool:
        """
        Delete a work item by ID.
        
        Args:
            work_item_id: The ID of the work item to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        url = f"{self.project_base_url}/wit/workitems/{work_item_id}?api-version=7.0"
        
        try:
            response = requests.delete(url, auth=self.auth)
            
            # Azure DevOps returns 200 for successful deletion
            if response.status_code == 200:
                self.logger.info(f"Successfully deleted work item {work_item_id}")
                return True
            else:
                self.logger.warning(f"Unexpected response code {response.status_code} when deleting work item {work_item_id}")
                self.logger.warning(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to delete work item {work_item_id}: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            return False
    
    def test_connection(self) -> bool:
        """Test the Azure DevOps connection."""
        if not self.enabled:
            return False
        
        # Test organization-level access first
        url = f"{self.org_base_url}/projects?api-version=7.0"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            
            # Verify the specific project exists
            projects = response.json()
            project_names = [p['name'] for p in projects.get('value', [])]
            
            if self.project not in project_names:
                self.logger.error(f"Project '{self.project}' not found in organization '{self.organization}'")
                self.logger.info(f"Available projects: {project_names}")
                return False
            
            self.logger.info("Azure DevOps connection test successful")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Azure DevOps connection test failed: {e}")
            return False
    
    def create_area_path(self, area_name: str, parent_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new area path in the project."""
        import urllib.parse
        
        # If parent_path is None, create under the project root
        if parent_path:
            # URL encode the parent path for the API
            encoded_parent = urllib.parse.quote(parent_path, safe='')
            url = f"{self.project_base_url}/wit/classificationnodes/areas/{encoded_parent}?api-version=7.0"
        else:
            url = f"{self.project_base_url}/wit/classificationnodes/areas?api-version=7.0"
        
        # Use correct headers for classification nodes API
        classification_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        data = {"name": area_name}
        self.logger.info(f"Creating area path '{area_name}' under '{parent_path or self.project}' (URL: {url})")
        try:
            response = requests.post(url, json=data, auth=self.auth, headers=classification_headers)
            if response.status_code == 409:
                self.logger.info(f"Area path '{area_name}' already exists.")
                return {"status": "exists"}
            response.raise_for_status()
            self.logger.info(f"Area path '{area_name}' created successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create area path '{area_name}': {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def create_iteration_path(self, iteration_name: str, start_date: str, end_date: str, 
                            parent_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new iteration path (sprint) in the project."""
        # If parent_path is None, create under the project root
        if parent_path:
            url = f"{self.project_base_url}/wit/classificationnodes/iterations/{parent_path}?api-version=7.0"
        else:
            url = f"{self.project_base_url}/wit/classificationnodes/iterations?api-version=7.0"
        
        # Use correct headers for classification nodes API
        classification_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        data = {
            "name": iteration_name,
            "attributes": {
                "startDate": start_date,
                "finishDate": end_date
            }
        }
        
        self.logger.info(f"Creating iteration path '{iteration_name}' under '{parent_path or self.project}' (URL: {url})")
        try:
            response = requests.post(url, json=data, auth=self.auth, headers=classification_headers)
            if response.status_code == 409:
                self.logger.info(f"Iteration path '{iteration_name}' already exists.")
                return {"status": "exists"}
            response.raise_for_status()
            self.logger.info(f"Iteration path '{iteration_name}' created successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create iteration path '{iteration_name}': {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    # Legacy test management methods - use delegation methods above instead
    def create_test_plan_legacy(self, name: str, area_path: str = None, iteration_path: str = None, description: str = None) -> Dict:
        """Create a new test plan in Azure DevOps (legacy method - use ensure_test_plan_exists instead)."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/testplan/plans?api-version=7.1-preview.1"
        
        data = {
            "name": name,
            "area": {"name": area_path} if area_path else None,
            "iteration": {"name": iteration_path} if iteration_path else None,
            "description": description
        }
        
        response = requests.post(url, json=data, auth=self._get_auth())
        return self._handle_response(response)

    def create_test_suite_legacy(self, test_plan_id: int, name: str, parent_suite_id: int = None) -> Dict:
        """Create a test suite in a test plan (legacy method - use ensure_test_suite_exists instead)."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/testplan/Plans/{test_plan_id}/suites?api-version=7.1-preview.1"
        
        data = {
            "name": name,
            "parentSuite": {"id": parent_suite_id} if parent_suite_id else None,
            "suiteType": "StaticTestSuite"
        }
        
        response = requests.post(url, json=data, auth=self._get_auth())
        return self._handle_response(response)

    def get_test_plans(self) -> List[Dict]:
        """Get all test plans in the project."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/testplan/plans?api-version=7.1-preview.1"
        response = requests.get(url, auth=self._get_auth())
        result = self._handle_response(response)
        return result.get("value", [])

    def get_test_suites(self, test_plan_id: int) -> List[Dict]:
        """Get all test suites in a test plan."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/testplan/Plans/{test_plan_id}/suites?api-version=7.1-preview.1"
        response = requests.get(url, auth=self._get_auth())
        result = self._handle_response(response)
        return result.get("value", [])

    def get_test_cases_in_suite(self, test_plan_id: int, test_suite_id: int) -> List[Dict]:
        """Get all test cases in a test suite."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/testplan/Plans/{test_plan_id}/Suites/{test_suite_id}/TestCases?api-version=7.1-preview.1"
        response = requests.get(url, auth=self._get_auth())
        result = self._handle_response(response)
        return result.get("value", [])

    def get_feature_test_plan(self, feature_id: int) -> Optional[Dict]:
        """Get the test plan associated with a feature work item."""
        test_plans = self.get_test_plans()
        for plan in test_plans:
            # Check if this plan is linked to our feature
            links = self.get_work_item_relations(plan["id"])
            for link in links:
                if link.get("rel") == "Microsoft.VSTS.TestCase.SharedParameterReferencedBy-Forward" and \
                   str(feature_id) in link.get("url", ""):
                    return plan
        return None

    def get_user_story_test_suite(self, test_plan_id: int, user_story_id: int) -> Optional[Dict]:
        """Get the test suite associated with a user story in a test plan."""
        suites = self.get_test_suites(test_plan_id)
        for suite in suites:
            # Check if this suite is linked to our user story
            links = self.get_work_item_relations(suite["id"])
            for link in links:
                if link.get("rel") == "Microsoft.VSTS.TestCase.SharedParameterReferencedBy-Forward" and \
                   str(user_story_id) in link.get("url", ""):
                    return suite
        return None

    def get_features(self) -> List[Dict]:
        """Get all features in the project."""
        wiql = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Feature'
        AND [System.TeamProject] = @project
        ORDER BY [System.Id]
        """
        
        # Get work item IDs
        ids = self.run_wiql(wiql)
        if not ids:
            return []
            
        # Get full work items
        return self.get_work_item_details(ids)

    def get_user_stories(self) -> List[Dict]:
        """Get all user stories in the project."""
        wiql = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'User Story'
        AND [System.TeamProject] = @project
        ORDER BY [System.Id]
        """
        
        # Get work item IDs
        ids = self.run_wiql(wiql)
        if not ids:
            return []
            
        # Get full work items
        return self.get_work_item_details(ids)
    
    def run_wiql(self, wiql: str) -> List[int]:
        """Run a WIQL query and return work item IDs."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit/wiql?api-version=7.1-preview.2"
        
        data = {
            "query": wiql
        }
        
        response = requests.post(url, json=data, auth=self._get_auth())
        result = self._handle_response(response)
        
        # Extract work item IDs
        return [int(item['id']) for item in result.get('workItems', [])]
    
    def get_work_item_revisions(self, work_item_id: int) -> List[Dict[str, Any]]:
        """Get all revisions/activity history for a work item to analyze changes."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit/workItems/{work_item_id}/revisions"
        
        try:
            response = requests.get(url, auth=self.auth, params={'api-version': '7.0'})
            response.raise_for_status()
            
            data = response.json()
            revisions = data.get('value', [])
            
            # Extract relevant change information
            revision_details = []
            for revision in revisions:
                revision_info = {
                    'rev': revision.get('rev'),
                    'id': revision.get('id'),
                    'changedDate': revision.get('fields', {}).get('System.ChangedDate'),
                    'changedBy': revision.get('fields', {}).get('System.ChangedBy', {}).get('displayName'),
                    'changedByEmail': revision.get('fields', {}).get('System.ChangedBy', {}).get('uniqueName'),
                    'areaPath': revision.get('fields', {}).get('System.AreaPath'),
                    'iterationPath': revision.get('fields', {}).get('System.IterationPath'),
                    'state': revision.get('fields', {}).get('System.State'),
                    'title': revision.get('fields', {}).get('System.Title'),
                    'workItemType': revision.get('fields', {}).get('System.WorkItemType')
                }
                revision_details.append(revision_info)
            
            return revision_details
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get work item revisions for {work_item_id}: {e}")
            return []

    def get_work_item_updates(self, work_item_id: int) -> List[Dict[str, Any]]:
        """Get work item updates showing field changes with old/new values."""
        url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/wit/workItems/{work_item_id}/updates"
        
        try:
            response = requests.get(url, auth=self.auth, params={'api-version': '7.0'})
            response.raise_for_status()
            
            data = response.json()
            updates = data.get('value', [])
            
            # Extract change details
            update_details = []
            for update in updates:
                fields = update.get('fields', {})
                update_info = {
                    'id': update.get('id'),
                    'rev': update.get('rev'),
                    'revisedDate': update.get('revisedDate'),
                    'revisedBy': update.get('revisedBy', {}).get('displayName'),
                    'revisedByEmail': update.get('revisedBy', {}).get('uniqueName'),
                    'fields_changed': {}
                }
                
                # Capture specific field changes we care about
                for field_name, field_data in fields.items():
                    if field_name in ['System.AreaPath', 'System.IterationPath', 'System.State', 'System.Title']:
                        update_info['fields_changed'][field_name] = {
                            'oldValue': field_data.get('oldValue'),
                            'newValue': field_data.get('newValue')
                        }
                
                if update_info['fields_changed']:  # Only include updates with relevant field changes
                    update_details.append(update_info)
            
            return update_details
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get work item updates for {work_item_id}: {e}")
            return []

    def analyze_work_item_change_attribution(self, work_item_id: int, field_name: str = 'System.AreaPath') -> Dict[str, Any]:
        """
        Analyze who made changes to a specific field to determine if it was human or automated.
        Returns attribution analysis for the most recent change to the specified field.
        """
        updates = self.get_work_item_updates(work_item_id)
        
        # Find the most recent change to the specified field
        for update in reversed(updates):  # Start from most recent
            if field_name in update.get('fields_changed', {}):
                change_info = update['fields_changed'][field_name]
                changed_by = update.get('revisedByEmail', '').lower()
                
                # Determine if this was an automated change
                automated_indicators = [
                    'system', 'service', 'automation', 'bot', 'agent',
                    'noreply', 'devops', 'pipeline', 'build'
                ]
                
                is_automated = any(indicator in changed_by for indicator in automated_indicators)
                
                return {
                    'work_item_id': work_item_id,
                    'field_name': field_name,
                    'old_value': change_info.get('oldValue'),
                    'new_value': change_info.get('newValue'),
                    'changed_by': update.get('revisedBy'),
                    'changed_by_email': update.get('revisedByEmail'),
                    'change_date': update.get('revisedDate'),
                    'is_automated': is_automated,
                    'attribution': 'agent_automated' if is_automated else 'human_override'
                }
        
        return {
            'work_item_id': work_item_id,
            'field_name': field_name,
            'attribution': 'unknown',
            'message': f'No changes found for field {field_name}'
        }
    
    def get_work_items_by_type(self, work_item_type: str) -> List[Dict[str, Any]]:
        """Retrieve all work items of a specific type."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Use WIQL (Work Item Query Language) to query work items by type
        wiql_query = {
            "query": f"SELECT [System.Id], [System.Title], [System.AreaPath], [System.WorkItemType] FROM workitems WHERE [System.TeamProject] = '{self.project}' AND [System.WorkItemType] = '{work_item_type}'"
        }
        
        url = f"{self.project_base_url}/wit/wiql?api-version=7.0"
        
        try:
            # Execute the query
            response = requests.post(url, json=wiql_query, auth=self.auth, headers=self.wiql_headers)
            response.raise_for_status()
            query_result = response.json()
            
            work_items = []
            if 'workItems' in query_result:
                # Extract work item IDs
                work_item_ids = [item['id'] for item in query_result['workItems']]
                
                if work_item_ids:
                    # Get detailed work item information
                    work_items = self.get_work_item_details(work_item_ids)
            
            return work_items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve work items of type {work_item_type}: {e}")
            raise

    def query_work_items(self, work_item_type: str, area_path: str = None) -> List[int]:
        """
        Query work items by type and optionally filter by area path.
        Returns a list of work item IDs.
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Build WIQL query
        query_parts = [
            f"SELECT [System.Id] FROM workitems",
            f"WHERE [System.TeamProject] = '{self.project}'",
            f"AND [System.WorkItemType] = '{work_item_type}'"
        ]
        
        # Add area path filter if specified
        if area_path:
            # Ensure area path includes project name
            if not area_path.startswith(self.project + "\\"):
                area_path = f"{self.project}\\{area_path}"
            query_parts.append(f"AND [System.AreaPath] = '{area_path}'")
        
        wiql_query = {
            "query": " ".join(query_parts)
        }
        
        url = f"{self.project_base_url}/wit/wiql?api-version=7.0"
        
        try:
            # Execute the query
            response = requests.post(url, json=wiql_query, auth=self.auth, headers=self.wiql_headers)
            response.raise_for_status()
            query_result = response.json()
            
            # Extract work item IDs
            work_item_ids = []
            if 'workItems' in query_result:
                work_item_ids = [item['id'] for item in query_result['workItems']]
            
            return work_item_ids
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to query work items of type {work_item_type}: {e}")
            return []

    def get_work_item_parent(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the parent work item using the relations field.
        Returns the parent work item details or None if no parent found.
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        relations = self.get_work_item_relations(work_item_id)
        
        for relation in relations:
            if relation.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
                # Extract parent ID from the URL
                parent_url = relation.get('url', '')
                if parent_url:
                    try:
                        parent_id = int(parent_url.split('/')[-1])
                        parent_work_item = self.get_work_item(parent_id)
                        return parent_work_item
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Failed to extract parent ID from URL {parent_url}: {e}")
                        continue
        
        return None

    def find_potential_parents_for_orphaned_work_item(self, work_item: Dict[str, Any], 
                                                     search_strategy: str = 'comprehensive') -> List[Dict[str, Any]]:
        """
        Find potential parents for an orphaned work item using multiple strategies.
        
        Args:
            work_item: The orphaned work item
            search_strategy: 'comprehensive', 'title_similarity', 'area_path', or 'recent_activity'
        
        Returns:
            List of potential parent work items with confidence scores
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        work_item_type = work_item.get('fields', {}).get('System.WorkItemType', '')
        work_item_title = work_item.get('fields', {}).get('System.Title', '')
        work_item_area_path = work_item.get('fields', {}).get('System.AreaPath', '')
        
        potential_parents = []
        
        # Determine expected parent type based on work item type
        expected_parent_type = self._get_expected_parent_type(work_item_type)
        if not expected_parent_type:
            return []
        
        if search_strategy in ['comprehensive', 'title_similarity']:
            # Strategy 1: Title similarity search
            title_similarity_parents = self._find_parents_by_title_similarity(
                work_item_title, expected_parent_type, work_item_area_path
            )
            potential_parents.extend(title_similarity_parents)
        
        if search_strategy in ['comprehensive', 'area_path']:
            # Strategy 2: Area path matching
            area_path_parents = self._find_parents_by_area_path(
                work_item_area_path, expected_parent_type
            )
            potential_parents.extend(area_path_parents)
        
        if search_strategy in ['comprehensive', 'recent_activity']:
            # Strategy 3: Recent activity and state
            recent_parents = self._find_parents_by_recent_activity(
                expected_parent_type, work_item_area_path
            )
            potential_parents.extend(recent_parents)
        
        # Remove duplicates and sort by confidence score
        unique_parents = self._deduplicate_and_rank_parents(potential_parents)
        
        return unique_parents[:10]  # Return top 10 candidates

    def _get_expected_parent_type(self, work_item_type: str) -> Optional[str]:
        """Get the expected parent work item type for a given work item type."""
        parent_type_mapping = {
            'Test Case': 'User Story',
            'Task': 'User Story', 
            'User Story': 'Feature',
            'Feature': 'Epic',
            'Bug': 'User Story',
            'Issue': 'User Story'
        }
        return parent_type_mapping.get(work_item_type)

    def _find_parents_by_title_similarity(self, work_item_title: str, parent_type: str, 
                                        area_path: str = None) -> List[Dict[str, Any]]:
        """Find potential parents by title similarity using semantic matching."""
        try:
            # Get all work items of the parent type
            parent_work_items = self.get_work_items_by_type(parent_type)
            
            candidates = []
            for parent in parent_work_items:
                parent_title = parent.get('fields', {}).get('System.Title', '')
                parent_area_path = parent.get('fields', {}).get('System.AreaPath', '')
                
                # Calculate similarity score
                similarity_score = self._calculate_title_similarity(work_item_title, parent_title)
                
                # Area path bonus
                area_bonus = 0.3 if area_path and parent_area_path and area_path in parent_area_path else 0
                
                total_score = similarity_score + area_bonus
                
                if total_score > 0.2:  # Minimum threshold
                    candidates.append({
                        'work_item': parent,
                        'confidence_score': total_score,
                        'match_reason': f'Title similarity: {similarity_score:.2f}, Area path bonus: {area_bonus:.2f}'
                    })
            
            return sorted(candidates, key=lambda x: x['confidence_score'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error in title similarity search: {e}")
            return []

    def _find_parents_by_area_path(self, work_item_area_path: str, parent_type: str) -> List[Dict[str, Any]]:
        """Find potential parents by area path matching."""
        try:
            # Get all work items of the parent type in the same area path
            parent_work_items = self.get_work_items_by_type(parent_type)
            
            candidates = []
            for parent in parent_work_items:
                parent_area_path = parent.get('fields', {}).get('System.AreaPath', '')
                
                # Check if area paths match or are related
                if work_item_area_path and parent_area_path:
                    if work_item_area_path == parent_area_path:
                        score = 0.8  # Exact match
                    elif work_item_area_path in parent_area_path:
                        score = 0.6  # Work item is in a sub-area of parent
                    elif parent_area_path in work_item_area_path:
                        score = 0.4  # Parent is in a sub-area of work item
                    else:
                        # Check for common parent area
                        common_parent = self._find_common_parent_area(work_item_area_path, parent_area_path)
                        score = 0.3 if common_parent else 0.0
                    
                    if score > 0:
                        candidates.append({
                            'work_item': parent,
                            'confidence_score': score,
                            'match_reason': f'Area path match: {score:.2f}'
                        })
            
            return sorted(candidates, key=lambda x: x['confidence_score'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error in area path search: {e}")
            return []

    def _find_parents_by_recent_activity(self, parent_type: str, area_path: str = None) -> List[Dict[str, Any]]:
        """Find potential parents by recent activity and state."""
        try:
            # Get recent work items of the parent type
            parent_work_items = self.get_work_items_by_type(parent_type)
            
            candidates = []
            for parent in parent_work_items:
                parent_state = parent.get('fields', {}).get('System.State', '')
                parent_area_path = parent.get('fields', {}).get('System.AreaPath', '')
                parent_priority = parent.get('fields', {}).get('Microsoft.VSTS.Common.Priority', 2)
                
                # Score based on state and priority
                state_score = self._get_state_score(parent_state)
                priority_score = self._get_priority_score(parent_priority)
                area_score = 0.2 if area_path and parent_area_path and area_path in parent_area_path else 0
                
                total_score = state_score + priority_score + area_score
                
                if total_score > 0.3:  # Minimum threshold
                    candidates.append({
                        'work_item': parent,
                        'confidence_score': total_score,
                        'match_reason': f'Recent activity: State={state_score:.2f}, Priority={priority_score:.2f}, Area={area_score:.2f}'
                    })
            
            return sorted(candidates, key=lambda x: x['confidence_score'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error in recent activity search: {e}")
            return []

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles using simple string matching."""
        if not title1 or not title2:
            return 0.0
        
        # Convert to lowercase for comparison
        t1_lower = title1.lower()
        t2_lower = title2.lower()
        
        # Exact match
        if t1_lower == t2_lower:
            return 1.0
        
        # Check if one title contains the other
        if t1_lower in t2_lower or t2_lower in t1_lower:
            return 0.7
        
        # Word overlap
        words1 = set(t1_lower.split())
        words2 = set(t2_lower.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union)
        
        return jaccard_similarity

    def _find_common_parent_area(self, area_path1: str, area_path2: str) -> Optional[str]:
        """Find the common parent area path between two area paths."""
        if not area_path1 or not area_path2:
            return None
        
        parts1 = area_path1.split('\\')
        parts2 = area_path2.split('\\')
        
        common_parts = []
        for p1, p2 in zip(parts1, parts2):
            if p1 == p2:
                common_parts.append(p1)
            else:
                break
        
        return '\\'.join(common_parts) if common_parts else None

    def _get_state_score(self, state: str) -> float:
        """Get score based on work item state (active states get higher scores)."""
        state_scores = {
            'New': 0.8,
            'Active': 0.9,
            'In Progress': 0.8,
            'Ready': 0.7,
            'Resolved': 0.3,
            'Closed': 0.1,
            'Removed': 0.0
        }
        return state_scores.get(state, 0.5)

    def _get_priority_score(self, priority: int) -> float:
        """Get score based on priority (higher priority gets higher score)."""
        if priority == 1:
            return 0.8  # High priority
        elif priority == 2:
            return 0.6  # Medium priority
        elif priority == 3:
            return 0.4  # Low priority
        else:
            return 0.5  # Default

    def _deduplicate_and_rank_parents(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate parents and rank by confidence score."""
        seen_ids = set()
        unique_candidates = []
        
        for candidate in candidates:
            work_item_id = candidate['work_item']['id']
            if work_item_id not in seen_ids:
                seen_ids.add(work_item_id)
                unique_candidates.append(candidate)
        
        return sorted(unique_candidates, key=lambda x: x['confidence_score'], reverse=True)

    def link_orphaned_work_item_to_parent(self, orphaned_work_item_id: int, parent_work_item_id: int) -> bool:
        """
        Link an orphaned work item to its parent using the Azure DevOps API.
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        try:
            # Create the parent-child relationship
            success = self.create_work_item_relation(
                source_id=orphaned_work_item_id,
                target_id=parent_work_item_id,
                relation_type='System.LinkTypes.Hierarchy-Reverse'
            )
            
            if success:
                self.logger.info(f"Successfully linked orphaned work item {orphaned_work_item_id} to parent {parent_work_item_id}")
            else:
                self.logger.error(f"Failed to link orphaned work item {orphaned_work_item_id} to parent {parent_work_item_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error linking orphaned work item {orphaned_work_item_id} to parent {parent_work_item_id}: {e}")
            return False

    def find_original_parent_from_history(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Find the original or last parent from work item revision history.
        This is more reliable than similarity-based guessing for orphaned work items.
        
        Returns the parent work item details or None if no parent found in history.
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        try:
            # Get work item revisions to see history
            revisions = self.get_work_item_revisions(work_item_id)
            
            # Look through revisions in reverse order (newest first)
            for revision in reversed(revisions):
                # Check if this revision had parent relations
                relations = revision.get('relations', [])
                
                for relation in relations:
                    if relation.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
                        # Extract parent ID from the URL
                        parent_url = relation.get('url', '')
                        if parent_url:
                            try:
                                parent_id = int(parent_url.split('/')[-1])
                                # Verify the parent still exists
                                parent_work_item = self.get_work_item(parent_id)
                                if parent_work_item:
                                    self.logger.info(f"Found original parent {parent_id} for work item {work_item_id} from revision history")
                                    return parent_work_item
                            except (ValueError, IndexError) as e:
                                self.logger.warning(f"Failed to extract parent ID from URL {parent_url}: {e}")
                                continue
            
            self.logger.info(f"No parent found in revision history for work item {work_item_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding original parent from history for work item {work_item_id}: {e}")
            return None

    def find_last_parent_from_history(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Find the most recent parent from work item revision history.
        Useful when the original parent was removed but there was a more recent parent.
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        try:
            # Get work item revisions
            revisions = self.get_work_item_revisions(work_item_id)
            
            last_parent_id = None
            last_parent_revision_date = None
            
            # Look through all revisions to find the most recent parent
            for revision in revisions:
                relations = revision.get('relations', [])
                
                for relation in relations:
                    if relation.get('rel') == 'System.LinkTypes.Hierarchy-Reverse':
                        parent_url = relation.get('url', '')
                        if parent_url:
                            try:
                                parent_id = int(parent_url.split('/')[-1])
                                revision_date = revision.get('revisedDate')
                                
                                # Track the most recent parent
                                if not last_parent_revision_date or revision_date > last_parent_revision_date:
                                    last_parent_id = parent_id
                                    last_parent_revision_date = revision_date
                                    
                            except (ValueError, IndexError) as e:
                                continue
            
            # Return the most recent parent if found
            if last_parent_id:
                try:
                    parent_work_item = self.get_work_item(last_parent_id)
                    if parent_work_item:
                        self.logger.info(f"Found last parent {last_parent_id} for work item {work_item_id} from revision history")
                        return parent_work_item
                except Exception as e:
                    self.logger.warning(f"Last parent {last_parent_id} no longer exists: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding last parent from history for work item {work_item_id}: {e}")
            return None

    def restore_parent_from_history(self, work_item_id: int, prefer_original: bool = True) -> bool:
        """
        Restore the parent relationship for an orphaned work item from its history.
        
        Args:
            work_item_id: The orphaned work item ID
            prefer_original: If True, prefer the original parent; if False, prefer the most recent parent
        
        Returns:
            True if parent was restored, False otherwise
        """
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        try:
            # Try to find parent from history
            if prefer_original:
                parent = self.find_original_parent_from_history(work_item_id)
                if not parent:
                    parent = self.find_last_parent_from_history(work_item_id)
            else:
                parent = self.find_last_parent_from_history(work_item_id)
                if not parent:
                    parent = self.find_original_parent_from_history(work_item_id)
            
            if parent:
                # Restore the parent relationship
                success = self.link_orphaned_work_item_to_parent(work_item_id, parent['id'])
                if success:
                    self.logger.info(f"Successfully restored parent {parent['id']} for work item {work_item_id}")
                return success
            else:
                self.logger.warning(f"No parent found in history for work item {work_item_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring parent from history for work item {work_item_id}: {e}")
            return False
