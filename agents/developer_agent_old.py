import json
import threading
from typing import Optional
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator
from utils.task_quality_assessor import TaskQualityAssessor
from utils.json_extractor import JSONExtractor

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass
from integrators.azure_devops_api import AzureDevOpsIntegrator

class DeveloperAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("developer_agent", config)
        
        # Initialize quality validator and task quality assessor
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)
        self.task_quality_assessor = TaskQualityAssessor()
        self.max_quality_retries = 3  # Maximum attempts to achieve EXCELLENT rating
        
        # Azure DevOps integration will be set by supervisor when needed
        self.azure_api = None
    
    def set_azure_integrator(self, azure_integrator):
        """Set the Azure DevOps integrator for this agent."""
        self.azure_api = azure_integrator

    def generate_tasks(self, user_story: dict, context: dict = None, max_tasks: int = None) -> list[dict]:
        """Generate technical tasks from a user story with full context cascading."""
        
        # Extract full context for cascading  
        product_vision = context.get('product_vision', '') if context else ''
        epic_context = context.get('epic_context', '') if context else ''
        feature_context = context.get('feature_context', '') if context else ''
        
        # Build context for prompt template - CASCADE FULL CONTEXT
        prompt_context = {
            'domain': context.get('domain', 'dynamic') if context else 'dynamic',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'tech_stack': context.get('tech_stack', 'Modern Web Stack') if context else 'Modern Web Stack',
            'architecture_pattern': context.get('architecture_pattern', 'MVC') if context else 'MVC',
            'database_type': context.get('database_type', 'SQL Database') if context else 'SQL Database',
            'cloud_platform': context.get('cloud_platform', 'Cloud Platform') if context else 'Cloud Platform',
            'team_size': context.get('team_size', '5-8 developers') if context else '5-8 developers',
            'sprint_duration': context.get('sprint_duration', '2 weeks') if context else '2 weeks',
            'product_vision': product_vision,  # CASCADE PRODUCT VISION
            'epic_context': epic_context,  # CASCADE EPIC CONTEXT
            'feature_context': feature_context  # CASCADE FEATURE CONTEXT
        }
        
        user_input = f"""
User Story: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', user_story.get('user_story', 'No description provided'))}
Acceptance Criteria: {user_story.get('acceptance_criteria', [])}
Story Points: {user_story.get('story_points', 'Not specified')}
Priority: {user_story.get('priority', 'Medium')}
User Type: {user_story.get('user_type', 'user')}

{f'Generate a maximum of {max_tasks} tasks only.' if max_tasks else ''}
"""
        
        # Use template-based approach
        try:
            response = self.run_with_template(user_input, prompt_context, "developer_agent")
            
            if not response or not response.strip():
                print("Empty response from LLM")
                return []
            
            # Extract and parse JSON
            cleaned_response = JSONExtractor.extract_json_from_response(response)
            tasks = json.loads(cleaned_response)
            
            # Apply task limit if specified
            if max_tasks and len(tasks) > max_tasks:
                tasks = tasks[:max_tasks]
                print(f"[DeveloperAgent] Limited output from {len(tasks)} to {max_tasks} tasks")
            
            # Apply quality assessment with full context
            quality_approved_tasks = self._assess_and_improve_task_quality(
                tasks, user_story, context, product_vision
            )
            return quality_approved_tasks
            
        except Exception as e:
            print(f"Task generation failed: {e}")
            return []
    
    def _assess_and_improve_task_quality(self, tasks: list, user_story: dict, context: dict, 
                                       product_vision: str) -> list:
        """Assess task quality and retry generation if not EXCELLENT."""
        if not tasks:
            return []
        
        domain = context.get('domain', 'general') if context else 'general'
        approved_tasks = []
        
        print(f"\nStarting task quality assessment for {len(tasks)} tasks...")
        print(f"User Story Context: {user_story.get('title', 'Unknown Story')}")
        print(f"Domain: {domain}")
        
        for i, task in enumerate(tasks):
            print(f"\n{'='*60}")
            print(f"ASSESSING TASK {i+1}/{len(tasks)}")
            print(f"{'='*60}")
            
            attempt = 1
            current_task = task
            
            while attempt <= self.max_quality_retries:
                # Assess current task quality
                assessment = self.task_quality_assessor.assess_task(
                    current_task, user_story, domain, product_vision
                )
                
                # Log assessment
                log_output = self.task_quality_assessor.format_assessment_log(
                    current_task, assessment, attempt
                )
                print(log_output)
                
                if assessment.rating == "EXCELLENT":
                    print(f"+ Task approved with EXCELLENT rating on attempt {attempt}")
                    approved_tasks.append(current_task)
                    break
                
                if attempt == self.max_quality_retries:
                    print(f"- Task failed to reach EXCELLENT rating after {self.max_quality_retries} attempts")
                    print(f"   Final rating: {assessment.rating} ({assessment.score}/100)")
                    print("   Task REJECTED - EXCELLENT rating required")
                    # Do NOT add to approved_tasks - only EXCELLENT tasks allowed
                    break
                
                # Generate improvement prompt
                improvement_prompt = self._create_task_improvement_prompt(
                    current_task, assessment, user_story, product_vision, context
                )
                
                print(f"Attempting to improve task (attempt {attempt + 1}/{self.max_quality_retries})")
                
                try:
                    # Re-generate the task with improvement guidance
                    improved_response = self._generate_improved_task(improvement_prompt, context)
                    if improved_response:
                        current_task = improved_response
                    else:
                        print("Failed to generate improvement - using current version")
                        break
                        
                except Exception as e:
                    print(f"Error during task improvement: {e}")
                    break
                
                attempt += 1
        
        print(f"\n+ Task quality assessment complete: {len(approved_tasks)} tasks approved")
        return approved_tasks
    
    def _create_task_improvement_prompt(self, task: dict, assessment, user_story: dict, 
                                      product_vision: str, context: dict) -> str:
        """Create a prompt to improve the task based on quality assessment."""
        title = task.get('title', '')
        description = task.get('description', '')
        story_title = user_story.get('title', '')
        story_description = user_story.get('description', user_story.get('user_story', ''))
        
        improvement_text = f"""TASK IMPROVEMENT REQUEST

Current Task:
Title: {title}
Description: {description}

Parent User Story Context:
Title: {story_title}
Description: {story_description}
Acceptance Criteria: {user_story.get('acceptance_criteria', [])}

Product Vision Context:
{product_vision}

Quality Issues Identified:
{chr(10).join('• ' + issue for issue in assessment.specific_issues)}

Improvement Suggestions:
{chr(10).join('• ' + suggestion for suggestion in assessment.improvement_suggestions)}

CRITICAL REQUIREMENTS:
1. Task must directly implement user story acceptance criteria
2. Include specific technical implementation details
3. Use domain-specific terminology and context
4. Provide realistic time estimates and complexity assessment
5. Include testable technical acceptance criteria

INSTRUCTIONS:
Rewrite this task to address the quality issues above. Focus on:
1. Strong alignment with user story "{story_title}"
2. Technical specificity with APIs, components, database details
3. Domain-specific terminology and requirements
4. Clear actionable implementation steps
5. Realistic estimation and effort assessment

Return only a single improved task in this JSON format:
{{
  "title": "Specific technical task title with domain context",
  "description": "Detailed technical implementation steps including specific APIs, components, database tables, validation rules, and business logic requirements",
  "time_estimate": 4.5,
  "complexity": "Low|Medium|High",
  "story_points": 1|2|3|5|8,
  "category": "frontend|backend|database|api|testing|deployment|configuration",
  "dependencies": ["Specific prerequisite tasks or external dependencies"],
  "acceptance_criteria": [
    "Testable technical validation criteria",
    "Specific implementation requirements",
    "Quality and performance requirements"
  ]
}}"""
        return improvement_text.strip()
    
    def _generate_improved_task(self, improvement_prompt: str, context: dict) -> dict:
        """Generate an improved version of the task."""
        try:
            # Use the existing run method to generate improvement
            response = self.run(improvement_prompt, context or {})
            
            if not response:
                return None
            
            # Extract and parse JSON
            cleaned_response = JSONExtractor.extract_json_from_response(response)
            improved_task = json.loads(cleaned_response)
            
            # Validate that we got a single task object
            if isinstance(improved_task, dict):
                return improved_task
            elif isinstance(improved_task, list) and len(improved_task) > 0:
                return improved_task[0]  # Take first task if array returned
            else:
                return None
                
        except Exception as e:
            print(f"Error generating improved task: {e}")
            return None
    
    def run_with_template(self, user_input: str, context: dict, template_name: str = None) -> str:
        """Run with a specific prompt template."""
        template_to_use = template_name or "developer_agent"
        
        try:
            # Import prompt manager
            from utils.prompt_manager import prompt_manager
            
            # Try to use the specific template
            prompt = prompt_manager.get_prompt(template_to_use, context)
            
            # Use the proper method based on provider
            if self.llm_provider == "ollama":
                return self.ollama_provider.generate_response(
                    system_prompt=prompt,
                    user_input=user_input,
                    temperature=0.7,
                    max_tokens=8000
                )
            else:
                # Use direct API call for cloud providers
                url = self.api_url
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_input}
                    ]
                }
                
                import requests
                timeout = 120 if self.model and "70b" in self.model.lower() else 60
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"Template {template_to_use} failed: {e}")
            print("Falling back to default prompt...")
            return ""
                print("⚠️ Empty or None tasks after JSON parsing")
                return self._create_fallback_tasks(user_story)
            
            if isinstance(tasks, list):
                # Validate and enhance tasks for quality compliance
                enhanced_tasks = self._validate_and_enhance_tasks(tasks)
                return enhanced_tasks
            else:
                print("⚠️ Response was not a list.")
                print("🔎 Raw response:")
                print(response)
                return self._create_fallback_tasks(user_story)
        except Exception as e:
            print(f"⚠️ Error processing response: {e}")
            return self._create_fallback_tasks(user_story)



    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from a response that might be wrapped in text or code blocks.
        """
        import re
        import json
        
        # Try to find JSON in markdown code blocks first
        json_block_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_block_pattern, response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Try to parse and validate the JSON
            try:
                json.loads(content)
                return content
            except json.JSONDecodeError as e:
                pass
                # Try to fix common JSON issues
                fixed_content = self._fix_json_syntax(content)
                try:
                    json.loads(fixed_content)
                    return fixed_content
                except json.JSONDecodeError:
                    pass
        
        # Try to find JSON in generic code blocks
        code_block_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Check if it looks like JSON (starts with [ or {)
            if content.strip().startswith(('[', '{')):
                try:
                    json.loads(content)
                    return content
                except json.JSONDecodeError as e:
                    pass
                    # Try to fix common JSON issues
                    fixed_content = self._fix_json_syntax(content)
                    try:
                        json.loads(fixed_content)
                        return fixed_content
                    except json.JSONDecodeError:
                        pass
        
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
                return best_match[0].strip()
            except json.JSONDecodeError as e:
                pass
                # Try to fix common JSON issues
                fixed_content = self._fix_json_syntax(best_match[0])
                try:
                    json.loads(fixed_content)
                    return fixed_content
                except json.JSONDecodeError:
                    pass
        
        # If all else fails, raise an error - the LLM should return valid JSON
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

    def _run_with_timeout(self, user_input: str, context: dict, timeout: int = 60):
        """Run the agent with a timeout to prevent hanging."""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = self.run(user_input, context)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"⚠️ Task generation timed out after {timeout} seconds")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]