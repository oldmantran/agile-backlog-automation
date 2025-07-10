import json
from agents.base_agent import Agent
from config.config_loader import Config
from utils.quality_validator import WorkItemQualityValidator

class UserStoryDecomposerAgent(Agent):
    """
    Agent responsible for decomposing features into user stories.
    Focuses on user journeys, acceptance criteria, and implementation details.
    """
    
    def __init__(self, config: Config):
        super().__init__("user_story_decomposer_agent", config)
        # Initialize quality validator with current configuration
        self.quality_validator = WorkItemQualityValidator(config.settings if hasattr(config, 'settings') else None)

    def decompose_feature_to_user_stories(self, feature: dict, context: dict = None) -> list[dict]:
        """Break down a feature into detailed user stories with acceptance criteria and story points."""
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'platform': context.get('platform', 'web application') if context else 'web application',
            'team_velocity': context.get('team_velocity', '20-30 points per sprint') if context else '20-30 points per sprint'
        }
        
        user_input = f"""
Feature: {feature.get('title', 'Unknown Feature')}
Description: {feature.get('description', 'No description provided')}
Priority: {feature.get('priority', 'Medium')}
Estimated Story Points: {feature.get('estimated_story_points', 'Not specified')}
Business Value: {feature.get('business_value', 'Not specified')}
Dependencies: {feature.get('dependencies', [])}
UI/UX Requirements: {feature.get('ui_ux_requirements', [])}
Edge Cases: {feature.get('edge_cases', [])}
"""
        
        print(f"📝 [UserStoryDecomposerAgent] Decomposing feature to user stories: {feature.get('title', 'Unknown')}")
        
        # Use the user story decomposer template
        response = self.run_with_template(user_input, prompt_context, template_name="user_story_decomposer")

        try:
            # Check for markdown code blocks and extract JSON
            if "```json" in response:
                print("🔍 Extracting JSON from markdown...")
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            
            user_stories = json.loads(response)
            
            # Handle different response formats
            if isinstance(user_stories, list) and len(user_stories) > 0:
                # Check if these look like user stories or features
                first_item = user_stories[0]
                if 'user_stories' in first_item:
                    # This is actually a list of features, extract the user stories
                    print("🔄 Response contains features, extracting user stories...")
                    extracted_stories = []
                    for feature_item in user_stories:
                        stories = feature_item.get('user_stories', [])
                        if isinstance(stories, list):
                            for story_text in stories:
                                extracted_stories.append({
                                    'title': f"User Story from {feature_item.get('title', 'Feature')}",
                                    'user_story': story_text,
                                    'description': f"Extracted from feature: {feature_item.get('description', '')}",
                                    'story_points': feature_item.get('estimated_story_points', 5) // len(stories) if stories else 5,
                                    'priority': feature_item.get('priority', 'Medium'),
                                    'acceptance_criteria': []  # Will be populated during enhancement
                                })
                    return self._validate_and_enhance_user_stories(extracted_stories)
                else:
                    # This looks like actual user stories - validate and enhance them
                    enhanced_stories = self._validate_and_enhance_user_stories(user_stories)
                    return enhanced_stories
            elif isinstance(user_stories, dict) and 'user_stories' in user_stories:
                return self._validate_and_enhance_user_stories(user_stories['user_stories'])
            else:
                print("⚠️ LLM response was not in expected format.")
                print("� Response structure:", type(user_stories))
                print("🔎 Response content:", user_stories)
                raise ValueError(f"LLM response was not in expected format. Expected list of user stories, got {type(user_stories)}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            print("� Response length:", len(response))
            print("🔎 First 500 chars:", response[:500])
            raise ValueError(f"Failed to parse JSON response from LLM: {e}")

    def _validate_and_enhance_user_stories(self, user_stories: list) -> list:
        """
        Validate and enhance user stories to meet quality standards.
        Ensures compliance with Backlog Sweeper monitoring rules.
        """
        enhanced_stories = []
        
        for story in user_stories:
            # Validate and fix user story structure
            enhanced_story = self._enhance_single_user_story(story)
            enhanced_stories.append(enhanced_story)
        
        return enhanced_stories

    def _enhance_single_user_story(self, story: dict) -> dict:
        """
        Enhance a single user story to meet quality standards.
        """
        enhanced_story = story.copy()
        
        # Validate and fix title
        title = story.get('title', '')
        title_valid, title_issues = self.quality_validator.validate_work_item_title(title, "User Story")
        if not title_valid:
            print(f"⚠️ Story title issues: {', '.join(title_issues)}")
            if not title:
                enhanced_story['title'] = f"User Story: {story.get('description', 'Undefined')[:50]}..."
        
        # Validate and fix description
        description = story.get('description', '') or story.get('user_story', '')
        desc_valid, desc_issues = self.quality_validator.validate_user_story_description(description)
        if not desc_valid:
            print(f"⚠️ Story description issues: {', '.join(desc_issues)}")
            # Try to fix the description
            if 'As a' not in description and 'As an' not in description:
                user_type = story.get('user_type', 'user')
                goal = title.replace('User Story:', '').strip() if 'User Story:' in title else title
                enhanced_story['description'] = f"As a {user_type}, I want {goal} so that I can achieve my objectives"
            else:
                enhanced_story['description'] = description
        else:
            enhanced_story['description'] = description
        
        # Validate and enhance acceptance criteria
        criteria = story.get('acceptance_criteria', [])
        criteria_valid, criteria_issues = self.quality_validator.validate_acceptance_criteria(criteria, title)
        if not criteria_valid or criteria_issues:
            print(f"📋 Enhancing acceptance criteria: {', '.join(criteria_issues)}")
            enhanced_criteria = self.quality_validator.enhance_acceptance_criteria(
                criteria, 
                {'title': enhanced_story['title'], 'description': enhanced_story['description']}
            )
            enhanced_story['acceptance_criteria'] = enhanced_criteria
        
        # Ensure story points are set
        if not enhanced_story.get('story_points'):
            criteria_count = len(enhanced_story.get('acceptance_criteria', []))
            if criteria_count <= 3:
                enhanced_story['story_points'] = 2
            elif criteria_count <= 5:
                enhanced_story['story_points'] = 3
            elif criteria_count <= 7:
                enhanced_story['story_points'] = 5
            else:
                enhanced_story['story_points'] = 8
        
        # Add quality metadata
        enhanced_story['definition_of_ready'] = [
            'Acceptance criteria defined and reviewed',
            'Story points estimated',
            'Dependencies identified',
            'UI/UX requirements clarified'
        ]
        
        enhanced_story['definition_of_done'] = [
            'Code developed and reviewed',
            'Unit tests written and passing',
            'Integration tests passing',
            'Acceptance criteria validated',
            'Documentation updated'
        ]
        
        # Ensure other required fields
        if not enhanced_story.get('priority'):
            enhanced_story['priority'] = 'Medium'
        
        if not enhanced_story.get('user_type'):
            enhanced_story['user_type'] = 'general_user'
        
        if not enhanced_story.get('category'):
            enhanced_story['category'] = 'feature_implementation'
        
        return enhanced_story

    def run_with_template(self, user_input: str, context: dict, template_name: str = None) -> str:
        """Run with a specific prompt template (fallback to default if template doesn't exist)."""
        # Use the template name if provided, otherwise use the agent name
        template_to_use = template_name or "user_story_decomposer"
        
        try:
            # Import prompt manager
            from utils.prompt_manager import prompt_manager
            
            # Try to use the specific template
            prompt = prompt_manager.get_prompt(template_to_use, context)
            print(f"📤 Sending to {self.llm_provider.capitalize()} with {template_to_use} template...")
            
            # Direct API call since we have the processed prompt
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
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            print(f"⚠️ Template {template_to_use} failed: {e}")
            print("🔄 Falling back to default prompt...")
            return self.run(user_input, context)
