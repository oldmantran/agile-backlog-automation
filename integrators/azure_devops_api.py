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
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
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
        """Get all available iteration paths in the project. Stub returns empty list if not implemented."""
        return []

    def _ensure_area_and_iteration_paths(self):
        """Ensure area and iteration paths exist in Azure DevOps, create if missing."""
        # Area Path
        area_paths = self.get_available_area_paths()
        # Accept both direct area name and full path for matching
        area_path_valid = self.area_path in area_paths or any(
            ap.split('\\')[-1] == self.area_path for ap in area_paths
        )
        if not area_path_valid:
            self.logger.info(f"Area path '{self.area_path}' not found. Creating...")
            # If area_path contains backslashes, split to get parent and child
            if '\\' in self.area_path:
                parent_path, area_name = self.area_path.rsplit('\\', 1)
                self.create_area_path(area_name, parent_path)
            else:
                self.create_area_path(self.area_path)
        # Iteration Path
        iteration_paths = [it['path'] for it in self.get_available_iteration_paths()]
        if self.iteration_path not in iteration_paths:
            self.logger.info(f"Iteration path '{self.iteration_path}' not found. Creating...")
            self.create_iteration_path(self.iteration_path, start_date=None, end_date=None)

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
        
        # Use test client for better test step formatting
        if self.test_client:
            steps = self._format_test_steps_for_test_client(test_case_data.get('steps', []))
            test_case_wi = self.test_client.create_test_case_work_item(
                title=test_case_data.get('title', 'Untitled Test Case'),
                description=test_case_data.get('description', ''),
                steps=steps
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
        test_plan = self.test_client.ensure_test_plan_exists(feature_id, feature_name)
        
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
        """Format feature description focusing on business value and high-level functionality."""
        description = feature_data.get('description', '')
        
        # Add business value if available
        if feature_data.get('business_value'):
            description += f"\n\n**Business Value:**\n{feature_data['business_value']}"
        
        # Add UI/UX requirements if available
        if feature_data.get('ui_ux_requirements'):
            description += "\n\n**UI/UX Requirements:**"
            for requirement in feature_data['ui_ux_requirements']:
                description += f"\n- {requirement}"
        
        # Add technical considerations if available
        if feature_data.get('technical_considerations'):
            description += "\n\n**Technical Considerations:**"
            for consideration in feature_data['technical_considerations']:
                description += f"\n- {consideration}"
        
        # Add dependencies if available
        if feature_data.get('dependencies'):
            description += "\n\n**Dependencies:**"
            for dependency in feature_data['dependencies']:
                description += f"\n- {dependency}"
        
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
    
    def _format_acceptance_criteria_for_ado(self, acceptance_criteria: List[str]) -> str:
        """Format acceptance criteria for Azure DevOps Acceptance Criteria field."""
        if not acceptance_criteria:
            return ""
        
        # Format as a numbered list for ADO
        formatted_criteria = []
        for i, criterion in enumerate(acceptance_criteria, 1):
            formatted_criteria.append(f"{i}. {criterion}")
        
        return "\n".join(formatted_criteria)

    def _format_user_story_description(self, story_data: Dict[str, Any]) -> str:
        """Format user story description without acceptance criteria (they go in dedicated field)."""
        description = story_data.get('description', '')
        
        # Add user story format if available
        if story_data.get('user_story'):
            description = f"**User Story:**\n{story_data['user_story']}\n\n{description}"
        
        # Add definition of ready if available
        if story_data.get('definition_of_ready'):
            description += "\n\n**Definition of Ready:**"
            for item in story_data['definition_of_ready']:
                description += f"\n- {item}"
        
        # Add definition of done if available
        if story_data.get('definition_of_done'):
            description += "\n\n**Definition of Done:**"
            for item in story_data['definition_of_done']:
                description += f"\n- {item}"
        
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
        
        return self.test_client.create_test_case_work_item(title, description, steps)

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
            response = requests.patch(
                url,
                json=patch_document,
                auth=self.auth,
                headers=self.headers
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
        # If parent_path is None, create under the project root
        if parent_path:
            url = f"{self.project_base_url}/wit/classificationnodes/areas/{parent_path}?api-version=7.0"
        else:
            url = f"{self.project_base_url}/wit/classificationnodes/areas?api-version=7.0"
        
        data = {"name": area_name}
        self.logger.info(f"Creating area path '{area_name}' under '{parent_path or self.project}' (URL: {url})")
        try:
            response = requests.post(url, json=data, auth=self.auth, headers=self.headers)
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
        # TODO: Implement iteration path creation with date ranges
        pass
    
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
