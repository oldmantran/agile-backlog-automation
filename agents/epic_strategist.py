import json
from agents.base_agent import Agent
from config.config_loader import Config

class EpicStrategist(Agent):
    def __init__(self, config: Config):
        super().__init__("epic_strategist", config)

    def generate_epics(self, product_vision: str, context: dict = None, max_epics: int = None) -> list[dict]:
        """Generate epics from a product vision with contextual information."""
        
        # Apply max_epics constraint if specified (null = unlimited)
        epic_limit = max_epics if max_epics is not None else None  # None = unlimited
        
        # Build context for prompt template
        prompt_context = {
            'domain': context.get('domain', 'software development') if context else 'software development',
            'project_name': context.get('project_name', 'Agile Project') if context else 'Agile Project',
            'target_users': context.get('target_users', 'end users') if context else 'end users',
            'timeline': context.get('timeline', 'not specified') if context else 'not specified',
            'budget_constraints': context.get('budget_constraints', 'standard budget') if context else 'standard budget',
            'methodology': context.get('methodology', 'Agile/Scrum') if context else 'Agile/Scrum',
            'max_epics': epic_limit if epic_limit else "unlimited"
        }
        
        if epic_limit:
            user_input = f"Product Vision: {product_vision}\n\nIMPORTANT: Generate a maximum of {epic_limit} epics only."
        else:
            user_input = f"Product Vision: {product_vision}"
        print(f"📊 [EpicStrategist] Generating epics for: {product_vision[:100]}...")
        
        response = self.run(user_input, prompt_context)

        try:
            if not response:
                print("⚠️ Empty response from Grok")
                return []
            
            # Check for markdown code blocks
            if "```json" in response:
                print("🔍 Extracting JSON from markdown...")
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            
            epics = json.loads(response)
            if isinstance(epics, list):
                # Format epics for better readability
                formatted_epics = [self._format_epic(epic) for epic in epics]
                
                # Apply the epic limit constraint if specified
                if epic_limit:
                    limited_epics = formatted_epics[:epic_limit]
                    if len(formatted_epics) > epic_limit:
                        print(f"🔧 [EpicStrategist] Limited output from {len(formatted_epics)} to {len(limited_epics)} epics (configuration limit)")
                    return limited_epics
                else:
                    return formatted_epics
            else:
                print("⚠️ Grok response was not a list.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []
    
    def _format_epic(self, epic: dict) -> dict:
        """
        Format epic description for better readability with proper section breaks.
        """
        formatted_epic = epic.copy()
        
        # Format description
        description = epic.get('description', '')
        if description:
            formatted_epic['description'] = self._format_structured_description(description)
        
        return formatted_epic
    
    def _format_structured_description(self, description: str) -> str:
        """
        Format structured descriptions with proper line breaks for sections.
        """
        if not description:
            return description
        
        formatted_description = description.strip()
        
        import re
        
        # First, handle section headers - add line breaks before them
        section_patterns = [
            r'(\*\*Business Value:\*\*)',
            r'(\*\*Success Criteria:\*\*)',
            r'(\*\*Risks:\*\*)',
            r'(\*\*Acceptance Criteria:\*\*)',
            r'(\*\*Technical Considerations:\*\*)',
            r'(\*\*Dependencies:\*\*)',
            r'(\*\*UI/UX Requirements:\*\*)'
        ]
        
        for pattern in section_patterns:
            formatted_description = re.sub(pattern, r'\n\n\1', formatted_description)
        
        # Handle bullet lists after section headers
        # Pattern: **Header:** - item1 - item2 - item3
        bullet_pattern = r'(\*\*[^*]+\*\*)\s*-\s*([^*]+?)(?=\n\n\*\*|\Z)'
        
        def format_bullets(match):
            header = match.group(1)
            content = match.group(2).strip()
            
            # Split on ' - ' pattern
            if ' - ' in content:
                items = content.split(' - ')
                items = [item.strip() for item in items if item.strip()]
                
                if len(items) > 1:
                    bullet_list = '\n'.join([f'- {item}' for item in items])
                    return f'{header}\n{bullet_list}'
            
            # If no splitting needed, still format as single bullet
            return f'{header}\n- {content}'
        
        formatted_description = re.sub(bullet_pattern, format_bullets, formatted_description, flags=re.DOTALL)
        
        # Add line breaks for very long main descriptions (before any sections)
        if len(formatted_description) > 300:
            # Split on the first section to separate main description
            first_section_match = re.search(r'\n\n\*\*', formatted_description)
            if first_section_match:
                main_desc = formatted_description[:first_section_match.start()]
                sections = formatted_description[first_section_match.start():]
                
                # Format main description with line breaks
                if len(main_desc) > 200 and '. ' in main_desc:
                    sentences = main_desc.split('. ')
                    if len(sentences) > 2:
                        mid_point = len(sentences) // 2
                        main_desc = '. '.join(sentences[:mid_point]) + '.\n\n' + '. '.join(sentences[mid_point:])
                
                formatted_description = main_desc + sections
        
        return formatted_description