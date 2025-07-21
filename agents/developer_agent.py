import json
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator
from integrators.azure_devops_api import AzureDevOpsIntegrator

class DeveloperAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("developer_agent", config)
        
        # Initialize quality validator
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)
        
        # Azure DevOps integration will be set by supervisor when needed
        self.azure_api = None
    
    def set_azure_integrator(self, azure_integrator):
        """Set the Azure DevOps integrator for this agent."""
        self.azure_api = azure_integrator

    def generate_tasks(self, user_story: dict, context: dict = None) -> list[dict]:
        """Generate technical tasks from a user story with contextual information."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'tech_stack': context.get('tech_stack', 'Modern Web Stack') if context else 'Modern Web Stack',
            'architecture_pattern': context.get('architecture_pattern', 'MVC') if context else 'MVC',
            'database_type': context.get('database_type', 'SQL Database') if context else 'SQL Database',
            'cloud_platform': context.get('cloud_platform', 'Cloud Platform') if context else 'Cloud Platform',
            'team_size': context.get('team_size', '5-8 developers') if context else '5-8 developers',
            'sprint_duration': context.get('sprint_duration', '2 weeks') if context else '2 weeks'
        }
        
        # Format acceptance criteria for better prompt
        acceptance_criteria = user_story.get('acceptance_criteria', [])
        if isinstance(acceptance_criteria, list):
            criteria_text = '\n'.join([f"- {criterion}" for criterion in acceptance_criteria])
        else:
            criteria_text = str(acceptance_criteria)
        
        user_input = f"""
You are a technical developer tasked with breaking down a user story into specific, actionable development tasks.

USER STORY:
Title: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', user_story.get('user_story', 'No description provided'))}
Acceptance Criteria:
{criteria_text}
Story Points: {user_story.get('story_points', 'Not specified')}
Priority: {user_story.get('priority', 'Medium')}
User Type: {user_story.get('user_type', 'user')}

REQUIREMENTS:
- Generate exactly 3-8 technical tasks
- Each task must be specific and actionable
- Include estimated hours (1-8 hours per task)
- Include the type of work (frontend, backend, database, testing, devops, etc.)
- Include acceptance criteria for each task

RESPONSE FORMAT:
You MUST respond with ONLY a valid JSON array. No markdown, no explanations, no additional text.

REQUIRED JSON STRUCTURE:
[
  {{
    "title": "Task title",
    "description": "Detailed task description",
    "estimated_hours": 4,
    "category": "frontend|backend|database|testing|devops",
    "priority": "High|Medium|Low",
    "acceptance_criteria": ["Criteria 1", "Criteria 2", "Criteria 3"]
  }}
]

EXAMPLE RESPONSE:
[
  {{
    "title": "Design user interface components",
    "description": "Create wireframes and mockups for the user interface",
    "estimated_hours": 6,
    "category": "frontend",
    "priority": "High",
    "acceptance_criteria": [
      "Wireframes created for all user flows",
      "Mockups approved by stakeholders",
      "Design system components documented"
    ]
  }},
  {{
    "title": "Implement API endpoints",
    "description": "Develop REST API endpoints for data operations",
    "estimated_hours": 8,
    "category": "backend",
    "priority": "High",
    "acceptance_criteria": [
      "All endpoints return correct HTTP status codes",
      "Input validation implemented",
      "Error handling covers all edge cases"
    ]
  }}
]

CRITICAL: Respond with ONLY the JSON array. No markdown formatting, no code blocks, no explanations.
"""
        
        print(f"💻 [DeveloperAgent] Generating tasks for user story: {user_story.get('title', 'Unknown')}")
        response = self.run(user_input, prompt_context)

        try:
            # Extract JSON from response if it's wrapped in text/code blocks
            json_content = self._extract_json_from_response(response)
            tasks = json.loads(json_content)
            if isinstance(tasks, list):
                # Validate and enhance tasks for quality compliance
                enhanced_tasks = self._validate_and_enhance_tasks(tasks)
                return enhanced_tasks
            else:
                print("⚠️ Response was not a list.")
                print("🔎 Raw response:")
                print(response)
                raise ValueError("LLM response was not a valid JSON array")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            raise ValueError(f"LLM returned invalid JSON: {e}")



    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from a response that might be wrapped in text or code blocks.
        """
        import re
        import json
        
        print("🔍 Extracting JSON from markdown...")
        
        # Try to find JSON in markdown code blocks first
        json_block_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_block_pattern, response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Try to parse and validate the JSON
            try:
                json.loads(content)
                print("✅ Found valid JSON in markdown block")
                return content
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON in markdown block has syntax error: {e}")
                # Try to fix common JSON issues
                fixed_content = self._fix_json_syntax(content)
                try:
                    json.loads(fixed_content)
                    print("✅ Fixed JSON syntax in markdown block")
                    return fixed_content
                except json.JSONDecodeError:
                    print("❌ Could not fix JSON syntax in markdown block")
        
        # Try to find JSON in generic code blocks
        code_block_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Check if it looks like JSON (starts with [ or {)
            if content.strip().startswith(('[', '{')):
                try:
                    json.loads(content)
                    print("✅ Found valid JSON in generic code block")
                    return content
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON in generic code block has syntax error: {e}")
                    # Try to fix common JSON issues
                    fixed_content = self._fix_json_syntax(content)
                    try:
                        json.loads(fixed_content)
                        print("✅ Fixed JSON syntax in generic code block")
                        return fixed_content
                    except json.JSONDecodeError:
                        print("❌ Could not fix JSON syntax in generic code block")
        
        # If no code blocks, try to find JSON by looking for array/object patterns
        # Look for the largest JSON structure in the response
        json_array_pattern = r'\[(?:[^[\]]*(?:\[(?:[^[\]]*(?:\[(?:[^[\]]*(?:\[[^\[\]]*\][^[\]]*)*)*\][^[\]]*)*)*\][^[\]]*)*)*\]'
        json_object_pattern = r'\{(?:[^{}]*(?:\{(?:[^{}]*(?:\{(?:[^{}]*(?:\{[^{}]*\}[^{}]*)*)*\}[^{}]*)*)*\}[^{}]*)*)*\}'
        
        array_matches = re.findall(json_array_pattern, response, re.DOTALL)
        object_matches = re.findall(json_object_pattern, response, re.DOTALL)
        
        # Prefer arrays over objects, and longer matches over shorter ones
        all_matches = [(match, len(match)) for match in array_matches + object_matches]
        if all_matches:
            best_match = max(all_matches, key=lambda x: x[1])
            try:
                json.loads(best_match[0])
                print("✅ Found valid JSON using pattern matching")
                return best_match[0].strip()
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON from pattern matching has syntax error: {e}")
                # Try to fix common JSON issues
                fixed_content = self._fix_json_syntax(best_match[0])
                try:
                    json.loads(fixed_content)
                    print("✅ Fixed JSON syntax from pattern matching")
                    return fixed_content
                except json.JSONDecodeError:
                    print("❌ Could not fix JSON syntax from pattern matching")
        
        # If all else fails, raise an error - the LLM should return valid JSON
        print("❌ No valid JSON found in LLM response")
        print("🔎 Raw response:")
        print(response)
        raise ValueError("LLM did not return valid JSON. Expected JSON array format.")

    def _fix_json_syntax(self, json_str: str) -> str:
        """
        Attempt to fix common JSON syntax errors.
        """
        # Remove trailing commas before closing brackets/braces
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing commas between objects in arrays
        json_str = re.sub(r'}(\s*){', r'},\1{', json_str)
        
        # Fix missing quotes around property names
        json_str = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_str)
        
        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')
        
        # Remove comments (JSON doesn't support comments)
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        return json_str

    def _create_fallback_tasks(self, user_story: dict) -> list[dict]:
        """Create basic fallback tasks when JSON parsing fails."""
        title = user_story.get('title', 'Unknown User Story')
        description = user_story.get('description', user_story.get('user_story', ''))
        
        # Create basic tasks based on the user story
        fallback_tasks = [
            {
                'title': f'Analyze requirements for {title}',
                'description': f'Review and understand the requirements for: {description}',
                'estimated_hours': 2,
                'category': 'analysis',
                'priority': 'High'
            },
            {
                'title': f'Design solution for {title}',
                'description': f'Create technical design and architecture for: {description}',
                'estimated_hours': 4,
                'category': 'design',
                'priority': 'High'
            },
            {
                'title': f'Implement {title}',
                'description': f'Develop the core functionality for: {description}',
                'estimated_hours': 8,
                'category': 'development',
                'priority': 'High'
            },
            {
                'title': f'Test {title}',
                'description': f'Create and execute tests for: {description}',
                'estimated_hours': 4,
                'category': 'testing',
                'priority': 'Medium'
            }
        ]
        
        print(f"📋 Created {len(fallback_tasks)} fallback tasks for: {title}")
        return self._validate_and_enhance_tasks(fallback_tasks)

    def _create_fallback_tasks_from_response(self, response: str) -> str:
        """Create fallback JSON when no valid JSON is found in response."""
        # Return a basic task structure as JSON string
        fallback_json = '''[
            {
                "title": "Analyze requirements",
                "description": "Review and understand the user story requirements",
                "estimated_hours": 2,
                "category": "analysis",
                "priority": "High"
            },
            {
                "title": "Design solution",
                "description": "Create technical design and architecture",
                "estimated_hours": 4,
                "category": "design",
                "priority": "High"
            },
            {
                "title": "Implement functionality",
                "description": "Develop the core functionality",
                "estimated_hours": 8,
                "category": "development",
                "priority": "High"
            },
            {
                "title": "Test implementation",
                "description": "Create and execute tests",
                "estimated_hours": 4,
                "category": "testing",
                "priority": "Medium"
            }
        ]'''
        return fallback_json

    def _validate_and_enhance_tasks(self, tasks: list) -> list:
        """
        Validate and enhance tasks to meet quality standards.
        Ensures compliance with Backlog Sweeper monitoring rules.
        """
        enhanced_tasks = []
        
        for task in tasks:
            enhanced_task = self._enhance_single_task(task)
            enhanced_tasks.append(enhanced_task)
        
        return enhanced_tasks
    
    def _enhance_single_task(self, task: dict) -> dict:
        """
        Enhance a single task to meet quality standards.
        """
        enhanced_task = task.copy()
        
        # Validate and fix title
        title = task.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "Task")
        if not title_valid:
            print(f"⚠️ Task title issues: {', '.join(title_issues)}")
            if not title:
                enhanced_task['title'] = f"Task: {task.get('description', 'Implementation task')[:50]}..."
        
        # Ensure description exists
        if not enhanced_task.get('description'):
            enhanced_task['description'] = f"Implement {enhanced_task.get('title', 'task functionality')}"
        
        # Ensure effort estimation
        if not enhanced_task.get('estimated_hours') and not enhanced_task.get('story_points'):
            # Estimate based on task complexity indicators
            description = enhanced_task.get('description', '').lower()
            if any(word in description for word in ['implement', 'create', 'build', 'develop']):
                enhanced_task['estimated_hours'] = 8  # Full day for implementation
            elif any(word in description for word in ['test', 'validate', 'verify']):
                enhanced_task['estimated_hours'] = 4  # Half day for testing
            elif any(word in description for word in ['design', 'plan', 'research']):
                enhanced_task['estimated_hours'] = 6  # Most of day for design
            else:
                enhanced_task['estimated_hours'] = 4  # Default half day
        
        # Add standard task metadata
        if not enhanced_task.get('category'):
            description = enhanced_task.get('description', '').lower()
            if any(word in description for word in ['frontend', 'ui', 'interface', 'component']):
                enhanced_task['category'] = 'frontend'
            elif any(word in description for word in ['backend', 'api', 'server', 'database']):
                enhanced_task['category'] = 'backend'
            elif any(word in description for word in ['test', 'testing', 'validation']):
                enhanced_task['category'] = 'testing'
            elif any(word in description for word in ['deploy', 'infrastructure', 'config']):
                enhanced_task['category'] = 'devops'
            else:
                enhanced_task['category'] = 'development'
        
        # Add definition of done for tasks
        enhanced_task['definition_of_done'] = [
            'Implementation completed',
            'Code reviewed and approved',
            'Unit tests written and passing',
            'Documentation updated',
            'Ready for integration testing'
        ]
        
        # Ensure priority is set
        if not enhanced_task.get('priority'):
            enhanced_task['priority'] = 'Medium'
        
        return enhanced_task
    
    def estimate_story_points(self, user_story: dict, context: dict = None) -> int:
        """
        Estimate story points for a user story based on acceptance criteria and complexity.
        Used by Backlog Sweeper Agent when stories are missing estimates.
        """
        criteria_count = len(user_story.get('acceptance_criteria', []))
        description = user_story.get('description', '').lower()
        title = user_story.get('title', '').lower()
        
        # Base estimation on acceptance criteria count
        if criteria_count <= 2:
            base_points = 1
        elif criteria_count <= 3:
            base_points = 2
        elif criteria_count <= 5:
            base_points = 3
        elif criteria_count <= 7:
            base_points = 5
        else:
            base_points = 8
        
        # Adjust based on complexity indicators
        complexity_factors = 0
        
        # Check for complexity indicators in description/title
        if any(word in description or word in title for word in ['integrate', 'complex', 'multiple', 'advanced']):
            complexity_factors += 1
        
        if any(word in description or word in title for word in ['database', 'migration', 'schema']):
            complexity_factors += 1
        
        if any(word in description or word in title for word in ['api', 'external', 'third-party']):
            complexity_factors += 1
        
        if any(word in description or word in title for word in ['security', 'authentication', 'authorization']):
            complexity_factors += 1
        
        # Adjust points based on complexity
        if complexity_factors >= 3:
            base_points = min(base_points * 2, 13)  # Double but cap at 13
        elif complexity_factors >= 2:
            base_points = min(base_points + 3, 13)  # Add 3 but cap at 13
        elif complexity_factors >= 1:
            base_points = min(base_points + 1, 8)   # Add 1 but cap at 8
        
        return base_points

    def update_story_points(self, work_item_id: int, estimated_points: int) -> bool:
        """
        Update story points for a work item in Azure DevOps.
        Used when supervisor assigns story point estimation tasks.
        """
        try:
            fields = {'/fields/Microsoft.VSTS.Scheduling.StoryPoints': estimated_points}
            self.azure_api.update_work_item(work_item_id, fields)
            print(f"✅ Updated work item {work_item_id} with {estimated_points} story points")
            return True
        except Exception as e:
            print(f"❌ Failed to update story points for work item {work_item_id}: {e}")
            return False

    def estimate_and_update_story_points(self, work_item_id: int, user_story: dict, context: dict = None) -> bool:
        """
        Estimate and update story points for a user story in one operation.
        This method combines estimation logic with Azure DevOps updates.
        """
        estimated_points = self.estimate_story_points(user_story, context)
        print(f"📊 Estimated {estimated_points} story points for user story: {user_story.get('title', 'Unknown')}")
        return self.update_story_points(work_item_id, estimated_points)

    def decompose_user_story(self, work_item_id: int, user_story: dict, context: dict = None) -> list:
        """
        Decompose a user story into tasks and create them in Azure DevOps.
        Used when supervisor assigns decomposition tasks from Backlog Sweeper findings.
        """
        try:
            # Generate tasks using existing method
            tasks = self.generate_tasks(user_story, context)
            
            created_tasks = []
            for task in tasks:
                # Create task in Azure DevOps
                task_data = {
                    'title': task.get('title', 'Implementation Task'),
                    'description': task.get('description', ''),
                    'work_item_type': 'Task',
                    'parent_id': work_item_id,
                    'estimated_hours': task.get('estimated_hours', 4),
                    'priority': task.get('priority', 'Medium'),
                    'category': task.get('category', 'development')
                }
                
                created_task = self.azure_api.create_task(task_data)
                if created_task:
                    created_tasks.append(created_task)
                    print(f"✅ Created task: {task_data['title']}")
                else:
                    print(f"❌ Failed to create task: {task_data['title']}")
            
            print(f"📋 Decomposed user story {work_item_id} into {len(created_tasks)} tasks")
            return created_tasks
            
        except Exception as e:
            print(f"❌ Failed to decompose user story {work_item_id}: {e}")
            return []

    def update_work_item_field(self, work_item_id: int, field_path: str, value: any) -> bool:
        """
        Generic method to update any field in a work item.
        Used for various work item modifications as directed by supervisor.
        """
        try:
            fields = {field_path: value}
            self.azure_api.update_work_item(work_item_id, fields)
            print(f"✅ Updated work item {work_item_id} field {field_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to update work item {work_item_id} field {field_path}: {e}")
            return False