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

from config.config_loader import Config


class AzureDevOpsIntegrator:
    """
    Integrates with Azure DevOps to create work items from generated backlog data.
    
    Supports:
    - Epic creation with business value and acceptance criteria
    - Feature creation with user stories and test plans
    - User Story/Task creation with estimates and assignments
    - Test Plan creation with organized test suites
    - Test Suite creation for user story grouping
    - Test Case creation with steps and expected results
    - Hierarchical work item relationships (Epic -> Feature -> User Story -> Task)
    - Test organization (Test Plan -> Test Suite -> Test Case)
    """
    
    def __init__(self, config: Config):
        """Initialize Azure DevOps integration with configuration."""
        self.config = config
        self.logger = logging.getLogger("azure_devops_integrator")
        
        # Azure DevOps connection settings
        self.organization = config.get_env("AZURE_DEVOPS_ORG")
        self.project = config.get_env("AZURE_DEVOPS_PROJECT")
        self.pat = config.get_env("AZURE_DEVOPS_PAT")
        
        # Handle both full URL and organization name formats
        if self.organization and self.organization.startswith("https://dev.azure.com/"):
            self.organization = self.organization.replace("https://dev.azure.com/", "")
        
        if not all([self.organization, self.project, self.pat]):
            self.logger.warning("Azure DevOps credentials not configured. Integration will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            
        # Initialize API endpoints
        self.org_base_url = f"https://dev.azure.com/{self.organization}/_apis"
        self.base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        self.project_base_url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis"
        self.work_items_url = f"{self.base_url}/wit/workitems"
        self.test_plans_url = f"{self.base_url}/testplan/plans"
        self.test_suites_url = f"{self.base_url}/testplan/suites"
        
        # Set up authentication
        self.auth = HTTPBasicAuth('', self.pat)
        self.headers = {
            'Content-Type': 'application/json-patch+json',
            'Accept': 'application/json'
        }
        
        # Project configuration
        paths = config.get_project_paths()
        self.area_path = paths['area']
        self.iteration_path = paths['iteration']
        
        # Cache for created test plans and suites
        self.test_plans_cache = {}
        self.test_suites_cache = {}
        
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
                            created_items.append(test_suite)
                            
                            for test_case_data in user_story_data.get('test_cases', []):
                                test_item = self._create_test_case(test_case_data, user_story_item['id'], test_suite['id'])
                                created_items.append(test_item)
                    
                    # Handle feature-level test cases (create default suite if needed)
                    if feature_data.get('test_cases') and test_plan:
                        default_suite = self._create_default_test_suite(feature_data, test_plan['id'], feature_item['id'])
                        created_items.append(default_suite)
                        
                        for test_case_data in feature_data.get('test_cases', []):
                            test_item = self._create_test_case(test_case_data, feature_item['id'], default_suite['id'])
                            created_items.append(test_item)
            
            self.logger.info(f"Successfully created {len(created_items)} work items with organized test plans")
            return created_items
            
        except Exception as e:
            self.logger.error(f"Failed to create work items: {e}")
            raise
    
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
    
    def _create_test_case(self, test_case_data: Dict[str, Any], parent_id: int, suite_id: int = None) -> Dict[str, Any]:
        """Create a Test Case work item and optionally assign to a test suite."""
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
        
        test_item = self._create_work_item('Test Case', fields)
        
        # Link to parent (User Story or Feature)
        self._create_parent_link(test_item['id'], parent_id)
        
        # Add to test suite if specified
        if suite_id:
            try:
                self.add_test_cases_to_suite(suite_id, [test_item['id']])
                test_item['suite_id'] = suite_id
                self.logger.info(f"Test case {test_item['id']} added to test suite {suite_id}")
            except Exception as e:
                self.logger.warning(f"Failed to add test case to suite: {e}")
        
        return test_item
    
    def _create_user_story(self, story_data: Dict[str, Any], parent_feature_id: int) -> Dict[str, Any]:
        """Create a User Story work item."""
        fields = {
            '/fields/System.Title': story_data.get('title', 'Untitled User Story'),
            '/fields/System.Description': self._format_user_story_description(story_data),
            '/fields/Microsoft.VSTS.Common.Priority': self._map_priority(story_data.get('priority', 'Medium')),
            '/fields/Microsoft.VSTS.Common.ValueArea': 'Business',
            '/fields/Microsoft.VSTS.Scheduling.StoryPoints': story_data.get('story_points', 0),
        }
        
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
        import urllib.parse
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
        
        try:
            response = requests.post(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers
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
            response = requests.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            self.logger.debug(f"Linked work item {child_id} to parent {parent_id}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create parent link: {e}")
            # Don't raise here, as the work item was created successfully
    
    def _format_epic_description(self, epic_data: Dict[str, Any]) -> str:
        """Format epic description with all relevant details."""
        description = epic_data.get('description', '')
        
        # Add business value
        if epic_data.get('business_value'):
            description += f"\n\n**Business Value:**\n{epic_data['business_value']}"
        
        # Add success criteria
        if epic_data.get('success_criteria'):
            description += "\n\n**Success Criteria:**"
            for criterion in epic_data['success_criteria']:
                description += f"\n- {criterion}"
        
        # Add dependencies
        if epic_data.get('dependencies'):
            description += "\n\n**Dependencies:**"
            for dependency in epic_data['dependencies']:
                description += f"\n- {dependency}"
        
        # Add risks
        if epic_data.get('risks'):
            description += "\n\n**Risks:**"
            for risk in epic_data['risks']:
                description += f"\n- {risk}"
        
        return description
    
    def _format_feature_description(self, feature_data: Dict[str, Any]) -> str:
        """Format feature description with acceptance criteria."""
        description = feature_data.get('description', '')
        
        # Add user story format if available
        if feature_data.get('user_story'):
            description = f"**User Story:**\n{feature_data['user_story']}\n\n{description}"
        
        # Add acceptance criteria
        if feature_data.get('acceptance_criteria'):
            description += "\n\n**Acceptance Criteria:**"
            for criterion in feature_data['acceptance_criteria']:
                description += f"\n- {criterion}"
        
        return description
    
    def _format_task_description(self, task_data: Dict[str, Any]) -> str:
        """Format task description with technical details."""
        description = task_data.get('description', '')
        
        # Add technical requirements
        if task_data.get('technical_requirements'):
            description += "\n\n**Technical Requirements:**"
            for req in task_data['technical_requirements']:
                description += f"\n- {req}"
        
        # Add definition of done
        if task_data.get('definition_of_done'):
            description += "\n\n**Definition of Done:**"
            for item in task_data['definition_of_done']:
                description += f"\n- {item}"
        
        return description
    
    def _format_user_story_description(self, story_data: Dict[str, Any]) -> str:
        """Format user story description with acceptance criteria."""
        description = story_data.get('description', '')
        
        # Add acceptance criteria
        if story_data.get('acceptance_criteria'):
            description += "\n\n**Acceptance Criteria:**"
            for criterion in story_data['acceptance_criteria']:
                description += f"\n- {criterion}"
        
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
            response = requests.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            self.logger.info(f"Updated work item {work_item_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update work item {work_item_id}: {e}")
            raise
    
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
        # TODO: Implement area path creation
        pass
    
    def create_iteration_path(self, iteration_name: str, start_date: str, end_date: str, 
                            parent_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new iteration path (sprint) in the project."""
        # TODO: Implement iteration path creation with date ranges
        pass
    
    def get_available_area_paths(self) -> List[str]:
        """Get all available area paths in the project."""
        # TODO: Implement area path retrieval
        pass
    
    def get_available_iteration_paths(self) -> List[Dict[str, Any]]:
        """Get all available iteration paths in the project."""
        # TODO: Implement iteration path retrieval
        pass
    
    def create_test_plan(self, plan_name: str, description: str = '', area_path: str = '', 
                        iteration_path: str = '', is_default: bool = False) -> Dict[str, Any]:
        """Create a new test plan in Azure DevOps."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Check if the test plan already exists
        existing_plan = self._find_test_plan_by_name(plan_name)
        if existing_plan:
            self.logger.info(f"Test plan '{plan_name}' already exists (ID: {existing_plan['id']})")
            return existing_plan
        
        url = f"{self.test_plans_url}?api-version=7.0"
        
        # Test plans require a specific JSON structure
        plan_data = {
            "name": plan_name,
            "description": description,
            "areaPath": area_path or self.area_path,
            "iterationPath": iteration_path or self.iteration_path,
            "isDefault": is_default
        }
        
        # Remove empty values
        plan_data = {k: v for k, v in plan_data.items() if v is not None}
        
        try:
            response = requests.post(
                url,
                json=plan_data,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            test_plan = response.json()
            
            # Cache the created test plan
            self.test_plans_cache[test_plan['id']] = test_plan
            
            self.logger.info(f"Created test plan: {test_plan['name']} (ID: {test_plan['id']})")
            return test_plan
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create test plan: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def _find_test_plan_by_name(self, plan_name: str) -> Optional[Dict[str, Any]]:
        """Find an existing test plan by name."""
        url = f"{self.test_plans_url}?api-version=7.0&$filter=name eq '{plan_name}'"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            
            plans = response.json().get('value', [])
            if plans:
                return plans[0]  # Return the first matching plan
            
            return None
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve test plans: {e}")
            raise
    
    def create_test_suite(self, suite_name: str, plan_id: int, 
                        parent_suite_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new test suite under a test plan."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Check if the test suite already exists
        existing_suite = self._find_test_suite_by_name(suite_name, plan_id)
        if existing_suite:
            self.logger.info(f"Test suite '{suite_name}' already exists (ID: {existing_suite['id']})")
            return existing_suite
        
        url = f"{self.test_suites_url}?api-version=7.0"
        
        # Test suites require a specific JSON structure
        suite_data = {
            "name": suite_name,
            "planId": plan_id,
            "parentSuiteId": parent_suite_id
        }
        
        # Remove empty values
        suite_data = {k: v for k, v in suite_data.items() if v is not None}
        
        try:
            response = requests.post(
                url,
                json=suite_data,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            test_suite = response.json()
            
            # Cache the created test suite
            self.test_suites_cache[test_suite['id']] = test_suite
            
            self.logger.info(f"Created test suite: {test_suite['name']} (ID: {test_suite['id']})")
            return test_suite
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create test suite: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def _find_test_suite_by_name(self, suite_name: str, plan_id: int) -> Optional[Dict[str, Any]]:
        """Find an existing test suite by name within a test plan."""
        url = f"{self.test_suites_url}?api-version=7.0&$filter=name eq '{suite_name}' and planId eq {plan_id}"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            
            suites = response.json().get('value', [])
            if suites:
                return suites[0]  # Return the first matching suite
            
            return None
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve test suites: {e}")
            raise
    
    def add_test_cases_to_suite(self, suite_id: int, test_case_ids: List[int]):
        """Add existing test cases to a test suite."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        url = f"{self.test_suites_url}/{suite_id}?api-version=7.0"
        
        # Test suites require a specific JSON structure for adding test cases
        suite_update_data = {
            "testCaseIds": test_case_ids
        }
        
        try:
            response = requests.patch(
                url,
                json=suite_update_data,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            
            self.logger.info(f"Added test cases to suite ID: {suite_id}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to add test cases to suite: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def _create_test_plan(self, feature_data: Dict[str, Any], feature_id: int) -> Dict[str, Any]:
        """Create a Test Plan for a feature following ADO best practices."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Check cache first
        cache_key = f"feature_{feature_id}"
        if cache_key in self.test_plans_cache:
            return self.test_plans_cache[cache_key]
        
        plan_name = f"Test Plan - {feature_data.get('title', 'Unknown Feature')}"
        plan_description = f"Test plan for feature: {feature_data.get('title', 'Unknown Feature')}\n\n"
        
        if feature_data.get('description'):
            plan_description += f"Feature Description:\n{feature_data['description']}\n\n"
        
        if feature_data.get('acceptance_criteria'):
            plan_description += "Acceptance Criteria:\n"
            for criterion in feature_data['acceptance_criteria']:
                plan_description += f"- {criterion}\n"
        
        plan_data = {
            "name": plan_name,
            "description": plan_description,
            "areaPath": self.area_path if self.area_path else f"{self.project}",
            "iteration": self.iteration_path if self.iteration_path else f"{self.project}",
            "state": "Active"
        }
        
        url = f"{self.test_plans_url}?api-version=7.0"
        
        try:
            response = requests.post(
                url,
                json=plan_data,
                auth=self.auth,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            test_plan = response.json()
            
            # Cache the test plan
            self.test_plans_cache[cache_key] = test_plan
            
            self.logger.info(f"Created test plan: {plan_name} (ID: {test_plan['id']})")
            
            return test_plan
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create test plan: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def _create_test_suite(self, user_story_data: Dict[str, Any], test_plan_id: int, user_story_id: int) -> Dict[str, Any]:
        """Create a Test Suite for a user story within a test plan."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Check cache first
        cache_key = f"plan_{test_plan_id}_story_{user_story_id}"
        if cache_key in self.test_suites_cache:
            return self.test_suites_cache[cache_key]
        
        suite_name = f"User Story: {user_story_data.get('title', 'Unknown User Story')}"
        suite_description = f"Test suite for user story: {user_story_data.get('title', 'Unknown User Story')}"
        
        if user_story_data.get('description'):
            suite_description += f"\n\nUser Story Description:\n{user_story_data['description']}"
        
        if user_story_data.get('acceptance_criteria'):
            suite_description += "\n\nAcceptance Criteria:\n"
            for criterion in user_story_data['acceptance_criteria']:
                suite_description += f"- {criterion}\n"
        
        suite_data = {
            "name": suite_name,
            "description": suite_description,
            "suiteType": "StaticTestSuite",  # Static test suite for organized test cases
            "parentSuite": {
                "id": 1  # Root suite ID (typically 1 for the plan's root suite)
            }
        }
        
        url = f"{self.test_plans_url}/{test_plan_id}/suites?api-version=7.0"
        
        try:
            response = requests.post(
                url,
                json=suite_data,
                auth=self.auth,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            test_suite = response.json()
            
            # Cache the test suite
            self.test_suites_cache[cache_key] = test_suite
            
            self.logger.info(f"Created test suite: {suite_name} (ID: {test_suite['id']}) in plan {test_plan_id}")
            
            return test_suite
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create test suite: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def _create_default_test_suite(self, feature_data: Dict[str, Any], test_plan_id: int, feature_id: int) -> Dict[str, Any]:
        """Create a default Test Suite for feature-level test cases."""
        if not self.enabled:
            raise ValueError("Azure DevOps integration not configured")
        
        # Check cache first
        cache_key = f"plan_{test_plan_id}_feature_{feature_id}_default"
        if cache_key in self.test_suites_cache:
            return self.test_suites_cache[cache_key]
        
        suite_name = f"Feature Tests: {feature_data.get('title', 'Unknown Feature')}"
        suite_description = f"Default test suite for feature-level test cases: {feature_data.get('title', 'Unknown Feature')}"
        
        if feature_data.get('description'):
            suite_description += f"\n\nFeature Description:\n{feature_data['description']}"
        
        suite_data = {
            "name": suite_name,
            "description": suite_description,
            "suiteType": "StaticTestSuite",
            "parentSuite": {
                "id": 1  # Root suite ID
            }
        }
        
        url = f"{self.test_plans_url}/{test_plan_id}/suites?api-version=7.0"
        
        try:
            response = requests.post(
                url,
                json=suite_data,
                auth=self.auth,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            test_suite = response.json()
            
            # Cache the test suite
            self.test_suites_cache[cache_key] = test_suite
            
            self.logger.info(f"Created default test suite: {suite_name} (ID: {test_suite['id']}) in plan {test_plan_id}")
            
            return test_suite
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to create default test suite: {e}")
            if hasattr(e, 'response') and e.response:
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def query_work_items(self, work_item_type: str, area_path: str = None, max_items: int = 100) -> List[int]:
        """
        Query work items by type and optionally filter by area path.
        
        Args:
            work_item_type: Type of work items to query (Epic, Feature, User Story, Task, Test Case)
            area_path: Optional area path to filter by
            max_items: Maximum number of items to return
            
        Returns:
            List of work item IDs
        """
        try:
            # Build WIQL query
            wiql_query = f"SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = '{work_item_type}'"
            
            if area_path:
                wiql_query += f" AND [System.AreaPath] UNDER '{area_path}'"
            
            # Add order and limit
            wiql_query += f" ORDER BY [System.ChangedDate] DESC"
            
            # Execute query
            url = f"{self.base_url}/wit/wiql"
            
            query_data = {
                "query": wiql_query
            }
            
            response = requests.post(
                url,
                json=query_data,
                auth=self.auth,
                params={'api-version': '7.0'}
            )
            
            if response.status_code == 200:
                result = response.json()
                work_items = result.get('workItems', [])
                
                # Extract IDs and limit results
                work_item_ids = [wi['id'] for wi in work_items[:max_items]]
                
                self.logger.info(f"Queried {len(work_item_ids)} {work_item_type} work items")
                return work_item_ids
            else:
                self.logger.error(f"Failed to query work items: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error querying work items: {e}")
            return []
    
    def get_work_item_details(self, work_item_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get detailed information for multiple work items.
        
        Args:
            work_item_ids: List of work item IDs to retrieve
            
        Returns:
            List of work item details with fields and relations
        """
        if not work_item_ids:
            return []
        
        try:
            # Batch request for multiple work items
            # Azure DevOps API supports up to 200 items per request
            batch_size = 200
            all_work_items = []
            
            for i in range(0, len(work_item_ids), batch_size):
                batch_ids = work_item_ids[i:i + batch_size]
                ids_string = ','.join(map(str, batch_ids))
                
                url = f"{self.base_url}/wit/workitems"
                
                params = {
                    'ids': ids_string,
                    'fields': 'System.Id,System.WorkItemType,System.Title,System.Description,System.State,System.AreaPath,System.IterationPath,Microsoft.VSTS.Common.AcceptanceCriteria,Microsoft.VSTS.Scheduling.StoryPoints,Microsoft.VSTS.Common.Priority,System.AssignedTo',
                    'api-version': '7.0'
                }
                
                response = requests.get(url, auth=self.auth, params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    batch_items = result.get('value', [])
                    all_work_items.extend(batch_items)
                else:
                    self.logger.error(f"Failed to get work item details for batch: {response.status_code} - {response.text}")
            
            self.logger.info(f"Retrieved details for {len(all_work_items)} work items")
            return all_work_items
            
        except Exception as e:
            self.logger.error(f"Error getting work item details: {e}")
            return []
    
    def get_work_item_relations(self, work_item_id: int) -> List[Dict[str, Any]]:
        """
        Get relations for a specific work item.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            List of relation objects
        """
        try:
            url = f"{self.project_base_url}/wit/workitems/{work_item_id}"
            
            params = {
                'api-version': '7.0',
                '$expand': 'Relations'
            }
            
            response = requests.get(url, auth=self.auth, params=params)
            
            if response.status_code == 200:
                result = response.json()
                relations = result.get('relations', [])
                return relations
            else:
                self.logger.error(f"Failed to get relations for work item {work_item_id}: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting work item relations: {e}")
            return []
    
    def _update_work_item(self, work_item_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update fields of an existing work item.
        
        Args:
            work_item_id: ID of the work item to update
            fields: Dictionary of fields to update
            
        Returns:
            Updated work item data
        """
        try:
            url = f"{self.project_base_url}/wit/workitems/{work_item_id}"
            
            # Prepare update operations
            update_ops = []
            for field_path, value in fields.items():
                update_ops.append({
                    "op": "add",
                    "path": field_path,
                    "value": value
                })
            
            response = requests.patch(
                url,
                json=update_ops,
                auth=self.auth,
                params={'api-version': '7.0'},
                headers={'Content-Type': 'application/json-patch+json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Successfully updated work item {work_item_id}")
                return result
            else:
                self.logger.error(f"Failed to update work item {work_item_id}: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error updating work item {work_item_id}: {e}")
            return {}
    
    def delete_work_item(self, work_item_id: int) -> bool:
        """
        Delete a work item (moves it to the Recycle Bin).
        Handles Test Cases specially using Test Management API.
        
        Args:
            work_item_id: The ID of the work item to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # First, get the work item details to check its type
            work_item_details = self.get_work_item_details([work_item_id])
            if not work_item_details:
                self.logger.error(f"Could not retrieve work item {work_item_id} for deletion")
                return False
            
            work_item_type = work_item_details[0].get('fields', {}).get('System.WorkItemType', '')
            
            # Test Cases require special handling with Test Management API
            if work_item_type == 'Test Case':
                return self._delete_test_case(work_item_id)
            else:
                # Use regular Work Item API for other types
                url = f"{self.project_base_url}/wit/workitems/{work_item_id}"
                
                response = requests.delete(
                    url,
                    auth=self.auth,
                    params={'api-version': '7.0'}
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully deleted work item {work_item_id}")
                    return True
                else:
                    self.logger.error(f"Failed to delete work item {work_item_id}: {response.status_code} - {response.text}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error deleting work item {work_item_id}: {e}")
            return False

    def _delete_test_case(self, test_case_id: int) -> bool:
        """
        Delete a Test Case using the Test Management API.
        
        Args:
            test_case_id: The ID of the test case to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # For Test Cases, we need to use the Test Management API
            # URL format: https://dev.azure.com/{organization}/{project}/_apis/test/testcases/{testCaseId}
            url = f"https://dev.azure.com/{self.organization}/{self.project}/_apis/test/testcases/{test_case_id}"
            
            response = requests.delete(
                url,
                auth=self.auth,
                params={'api-version': '7.0'}
            )
            
            if response.status_code in [200, 204]:
                self.logger.info(f"Successfully deleted test case {test_case_id}")
                return True
            else:
                self.logger.error(f"Failed to delete test case {test_case_id}: {response.status_code} - {response.text}")
                # Fall back to trying to set state to "Closed" if deletion fails
                return self._close_test_case(test_case_id)
                
        except Exception as e:
            self.logger.error(f"Error deleting test case {test_case_id}: {e}")
            # Fall back to trying to set state to "Closed" if deletion fails
            return self._close_test_case(test_case_id)

    def _close_test_case(self, test_case_id: int) -> bool:
        """
        Close a Test Case by setting its state to 'Closed' if deletion fails.
        
        Args:
            test_case_id: The ID of the test case to close
            
        Returns:
            True if closing was successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting to close test case {test_case_id} as fallback")
            
            # Try to set the test case state to "Closed"
            url = f"{self.project_base_url}/wit/workitems/{test_case_id}"
            
            patch_document = [{
                'op': 'replace',
                'path': '/fields/System.State',
                'value': 'Closed'
            }]
            
            response = requests.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers={'Content-Type': 'application/json-patch+json'},
                params={'api-version': '7.0'}
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully closed test case {test_case_id}")
                return True
            else:
                self.logger.error(f"Failed to close test case {test_case_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error closing test case {test_case_id}: {e}")
            return False

    def restore_work_item(self, work_item_id: int) -> bool:
        """
        Restore a work item from the Recycle Bin.
        
        Args:
            work_item_id: The ID of the work item to restore
            
        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            url = f"{self.project_base_url}/wit/recyclebin/{work_item_id}"
            
            # Prepare restore operation
            update_ops = [{
                "op": "add",
                "path": "/fields/System.State",
                "value": "New"
            }]
            
            response = requests.patch(
                url,
                json=update_ops,
                auth=self.auth,
                params={'api-version': '7.0'},
                headers={'Content-Type': 'application/json-patch+json'}
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully restored work item {work_item_id}")
                return True
            else:
                self.logger.error(f"Failed to restore work item {work_item_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring work item {work_item_id}: {e}")
            return False
