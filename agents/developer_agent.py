import json
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator

class DeveloperAgent(Agent):
    def __init__(self, config: Config):
        super().__init__("developer_agent", config)
        # Initialize quality validator
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)

    def generate_tasks(self, feature: dict, context: dict = None) -> list[dict]:
        """Generate technical tasks from a feature description with contextual information."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'tech_stack': context.get('tech_stack', 'Modern Web Stack') if context else 'Modern Web Stack',
            'architecture_pattern': context.get('architecture_pattern', 'MVC') if context else 'MVC',
            'database_type': context.get('database_type', 'SQL Database') if context else 'SQL Database',
            'cloud_platform': context.get('cloud_platform', 'Cloud Platform') if context else 'Cloud Platform',
            'team_size': context.get('team_size', '5-8 developers') if context else '5-8 developers',
            'sprint_duration': context.get('sprint_duration', '2 weeks') if context else '2 weeks'
        }
        
        user_input = f"""
Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Acceptance Criteria: {feature.get('acceptance_criteria', [])}
Priority: {feature.get('priority', 'Medium')}
Estimated Story Points: {feature.get('estimated_story_points', 'Not specified')}
"""
        
        print(f"💻 [DeveloperAgent] Generating tasks for: {feature.get('title', 'Unknown')}")
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
                print("⚠️ Grok response was not a list.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from a response that might be wrapped in text or code blocks.
        """
        import re
        
        print("🔍 Extracting JSON from markdown...")
        
        # Try to find JSON in markdown code blocks first
        json_block_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_block_pattern, response, re.DOTALL)
        if match:
            print("✅ Found JSON in markdown block")
            return match.group(1).strip()
        
        # Try to find JSON in generic code blocks
        code_block_pattern = r'```\s*(.*?)\s*```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Check if it looks like JSON (starts with [ or {)
            if content.strip().startswith(('[', '{')):
                print("✅ Found JSON in generic code block")
                return content
        
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
            print("✅ Found JSON using pattern matching")
            return best_match[0].strip()
        
        # If all else fails, return the original response
        print("⚠️ No JSON found, returning original response")
        return response.strip()

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
        Enhance a single task to meet quality standards and improve formatting.
        """
        enhanced_task = task.copy()
        
        # Validate and fix title
        title = task.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "Task")
        if not title_valid:
            print(f"⚠️ Task title issues: {', '.join(title_issues)}")
            if not title:
                enhanced_task['title'] = f"Task: {task.get('description', 'Implementation task')[:50]}..."
        
        # Format description for better readability
        description = task.get('description', '')
        if description:
            enhanced_task['description'] = self._format_task_description(description)
        elif not description:
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
    
    def _format_task_description(self, description: str) -> str:
        """
        Format task description for better readability, especially Definition of Done sections.
        """
        if not description:
            return description
        
        formatted_description = description.strip()
        
        # Check if description contains "Definition of Done" or similar patterns
        import re
        
        # Pattern to find "Definition of Done" followed by a list of items
        dod_patterns = [
            r'(\*\*Definition of Done:\*\*)\s*(.*?)(?=\n\n|\n\*\*|$)',
            r'(Definition of Done:)\s*(.*?)(?=\n\n|\n\*\*|$)',
            r'(\*\*DoD:\*\*)\s*(.*?)(?=\n\n|\n\*\*|$)',
            r'(DoD:)\s*(.*?)(?=\n\n|\n\*\*|$)'
        ]
        
        for pattern in dod_patterns:
            match = re.search(pattern, formatted_description, re.DOTALL | re.IGNORECASE)
            if match:
                header = match.group(1)
                content = match.group(2).strip()
                
                # Format the content as a bulleted list if it's not already
                if content:
                    # Split on common separators and clean up
                    items = []
                    
                    # Try splitting on various patterns
                    if ' - ' in content:
                        items = [item.strip() for item in content.split(' - ') if item.strip()]
                        # Remove leading dashes if they exist
                        items = [item.lstrip('- ').strip() for item in items]
                    elif content.count('- ') > 1:
                        # Already has bullet points, just clean up spacing
                        lines = content.split('\n')
                        items = []
                        for line in lines:
                            line = line.strip()
                            if line.startswith('- '):
                                items.append(line[2:].strip())
                            elif line and not line.startswith('-'):
                                # Line without bullet, add it
                                items.append(line)
                    else:
                        # Try to split on sentence patterns or commas
                        if '. ' in content and len(content.split('. ')) > 1:
                            items = [item.strip() for item in content.split('. ') if item.strip()]
                            # Add periods back to items that don't end with punctuation
                            items = [item if item.endswith(('.', '!', '?')) else item + '.' for item in items]
                        elif ', ' in content and len(content.split(', ')) > 2:
                            items = [item.strip() for item in content.split(', ') if item.strip()]
                        else:
                            # Single item or can't split, keep as is
                            items = [content]
                    
                    # Format as bulleted list with proper line breaks
                    if items:
                        formatted_items = '\n'.join([f'- {item}' for item in items])
                        formatted_dod = f'\n\n**Definition of Done:**\n{formatted_items}'
                        
                        # Replace the original DoD section with the formatted version
                        formatted_description = re.sub(pattern, formatted_dod, formatted_description, flags=re.DOTALL | re.IGNORECASE)
                
                break
        
        # Add line breaks for better readability in long descriptions
        if len(formatted_description) > 200 and '. ' in formatted_description and '\n' not in formatted_description:
            # Split long sentences at sentence boundaries for readability
            sentences = formatted_description.split('. ')
            if len(sentences) > 2:
                mid_point = len(sentences) // 2
                formatted_description = '. '.join(sentences[:mid_point]) + '.\n\n' + '. '.join(sentences[mid_point:])
        
        return formatted_description
    
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