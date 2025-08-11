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
    def __init__(self, config: Config, user_id: str = None):
        super().__init__("developer_agent", config, user_id)
        
        # Initialize quality validator and task quality assessor
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)
        self.task_quality_assessor = TaskQualityAssessor()
        self.max_quality_retries = 3  # Maximum attempts to achieve GOOD or better rating
        
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
            'feature_context': feature_context,  # CASCADE FEATURE CONTEXT
            'user_story': user_story,  # Pass entire user story object
            'max_tasks': max_tasks  # Pass max tasks if specified
        }
        
        # Flatten user story object for template access (Template class doesn't support dots in variable names)
        if user_story:
            for key, value in user_story.items():
                # Handle lists by converting to string
                if isinstance(value, list):
                    if key == 'acceptance_criteria':
                        # Format acceptance criteria as numbered list
                        formatted_criteria = '\n'.join(f"{i+1}. {criterion}" for i, criterion in enumerate(value))
                        prompt_context[f'user_story_{key}'] = formatted_criteria
                    else:
                        prompt_context[f'user_story_{key}'] = str(value)
                else:
                    prompt_context[f'user_story_{key}'] = value
        
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
        """Assess task quality and retry generation if not GOOD or better."""
        if not tasks:
            return []
        
        domain = context.get('domain', 'general') if context else 'general'
        approved_tasks = []
        task_limit = len(tasks)  # Track original target count
        failed_task_count = 0  # Track failed tasks for replacement
        
        print(f"\nStarting task quality assessment for {len(tasks)} tasks (target: {task_limit})...")
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
                
                if assessment.rating in ["EXCELLENT", "GOOD"]:
                    print(f"+ Task approved with {assessment.rating} rating on attempt {attempt}")
                    approved_tasks.append(current_task)
                    break
                
                if attempt == self.max_quality_retries:
                    failed_task_count += 1
                    task_title = current_task.get('title', f'Task {i+1}')
                    print(f"- Task failed to reach GOOD or better rating after {self.max_quality_retries} attempts")
                    print(f"   Final rating: {assessment.rating} ({assessment.score}/100)")
                    print("   Task REJECTED - GOOD or better rating required")
                    print(f"[REPLACEMENT NEEDED] Will generate {failed_task_count} replacement task(s) to maintain target of {task_limit}")
                    # Do NOT add to approved_tasks - only GOOD+ tasks allowed
                    break
                
                # Generate improvement prompt
                improvement_prompt = self._create_task_improvement_prompt(
                    current_task, assessment, user_story, product_vision, context
                )
                
                print(f"Attempting to improve task (attempt {attempt + 1}/{self.max_quality_retries})")
                
                try:
                    # Re-generate the task with improvement guidance
                    improved_response = self._generate_improved_task(improvement_prompt, context, user_story)
                    if improved_response:
                        current_task = improved_response
                    else:
                        print("Failed to generate improvement - using current version")
                        break
                        
                except Exception as e:
                    print(f"Error during task improvement: {e}")
                    break
                
                attempt += 1
        
        # Generate replacement tasks if we have failures and haven't reached target count
        if failed_task_count > 0 and len(approved_tasks) < task_limit:
            replacements_needed = min(failed_task_count, task_limit - len(approved_tasks))
            print(f"\n[REPLACEMENT] Generating {replacements_needed} replacement tasks to reach target of {task_limit}")
            
            try:
                # Build user input for replacement generation
                user_input = f"""
User Story: {user_story.get('title', 'Unknown User Story')}
Description: {user_story.get('description', user_story.get('user_story', 'No description provided'))}
Acceptance Criteria: {user_story.get('acceptance_criteria', [])}
Story Points: {user_story.get('story_points', 'Not specified')}
Priority: {user_story.get('priority', 'Medium')}
User Type: {user_story.get('user_type', 'user')}

Generate a maximum of {replacements_needed} tasks only.
"""
                
                # Build context similar to main generation
                prompt_context = {
                    'domain': context.get('domain', 'dynamic') if context else 'dynamic',
                    'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
                    'tech_stack': context.get('tech_stack', 'Modern Web Stack') if context else 'Modern Web Stack',
                    'architecture_pattern': context.get('architecture_pattern', 'MVC') if context else 'MVC',
                    'database_type': context.get('database_type', 'SQL Database') if context else 'SQL Database',
                    'cloud_platform': context.get('cloud_platform', 'Cloud Platform') if context else 'Cloud Platform',
                    'team_size': context.get('team_size', '5-8 developers') if context else '5-8 developers',
                    'sprint_duration': context.get('sprint_duration', '2 weeks') if context else '2 weeks',
                    'product_vision': context.get('product_vision', '') if context else '',
                    'epic_context': context.get('epic_context', '') if context else '',
                    'feature_context': context.get('feature_context', '') if context else '',
                    'user_story': user_story,  # Pass entire user story object
                    'max_tasks': replacements_needed
                }
                
                # Flatten user story object for template access
                if user_story:
                    for key, value in user_story.items():
                        # Handle lists by converting to string
                        if isinstance(value, list):
                            if key == 'acceptance_criteria':
                                # Format acceptance criteria as numbered list
                                formatted_criteria = '\n'.join(f"{i+1}. {criterion}" for i, criterion in enumerate(value))
                                prompt_context[f'user_story_{key}'] = formatted_criteria
                            else:
                                prompt_context[f'user_story_{key}'] = str(value)
                        else:
                            prompt_context[f'user_story_{key}'] = value
                
                # Generate replacement tasks
                replacement_response = self.run_with_template(user_input, prompt_context, "developer_agent")
                
                if replacement_response:
                    # Parse replacement tasks
                    from utils.json_extractor import JSONExtractor
                    cleaned_response = JSONExtractor.extract_json_from_response(replacement_response)
                    replacement_tasks = json.loads(cleaned_response) if cleaned_response else []
                    
                    # Quick quality check for replacements (1 attempt only)
                    for i, replacement_task in enumerate(replacement_tasks):
                        task_title = replacement_task.get('title', f'Replacement Task {i+1}')
                        
                        assessment = self.task_quality_assessor.assess_task(
                            replacement_task, user_story, domain, product_vision
                        )
                        
                        if assessment.rating in ["EXCELLENT", "GOOD"]:
                            approved_tasks.append(replacement_task)
                            print(f"[REPLACEMENT SUCCESS] Added replacement task '{task_title}' with {assessment.rating} rating")
                            
                            # Stop when we reach target count
                            if len(approved_tasks) >= task_limit:
                                break
                        else:
                            print(f"[REPLACEMENT SKIP] Replacement task '{task_title}' also failed ({assessment.rating})")
                            
            except Exception as replacement_error:
                print(f"[REPLACEMENT FAILED] Could not generate replacement tasks: {replacement_error}")
        
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
    
    def _generate_improved_task(self, improvement_prompt: str, context: dict, user_story: dict = None) -> dict:
        """Generate an improved version of the task."""
        try:
            # Build proper context for template including user story
            improvement_context = context.copy() if context else {}
            if user_story:
                improvement_context['user_story'] = user_story
                # Flatten user story object for template access
                for key, value in user_story.items():
                    # Handle lists by converting to string
                    if isinstance(value, list):
                        if key == 'acceptance_criteria':
                            # Format acceptance criteria as numbered list
                            formatted_criteria = '\n'.join(f"{i+1}. {criterion}" for i, criterion in enumerate(value))
                            improvement_context[f'user_story_{key}'] = formatted_criteria
                        else:
                            improvement_context[f'user_story_{key}'] = str(value)
                    else:
                        improvement_context[f'user_story_{key}'] = value
            
            # Call LLM directly with improvement prompt (not using template)
            if self.llm_provider == "ollama":
                response = self.ollama_provider.generate_response(
                    system_prompt="You are a senior developer improving a technical task.",
                    user_input=improvement_prompt,
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
                        {"role": "system", "content": "You are a senior developer improving a technical task."},
                        {"role": "user", "content": improvement_prompt}
                    ]
                }
                
                import requests
                timeout = 60  # 1 minute for improvement
                api_response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                api_response.raise_for_status()
                data = api_response.json()
                
                response = data["choices"][0]["message"]["content"].strip()
            
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
            import traceback
            traceback.print_exc()
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
                timeout = 600  # 10 minutes for all models
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"Template {template_to_use} failed: {e}")
            print("Falling back to default prompt...")
            return ""