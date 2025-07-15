import json
from agents.base_agent import Agent
from config.config_loader import Config
from utils.content_enhancer import ContentEnhancer

class EpicStrategist(Agent):
    def __init__(self, config: Config):
        super().__init__("epic_strategist", config)
        self.content_enhancer = ContentEnhancer()

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
            # Extract JSON with improved parsing
            cleaned_response = self._extract_json_from_response(response)
            epics = json.loads(cleaned_response)
            if isinstance(epics, list):
                # Apply the epic limit constraint if specified
                if epic_limit:
                    limited_epics = epics[:epic_limit]
                    if len(epics) > epic_limit:
                        print(f"🔧 [EpicStrategist] Limited output from {len(epics)} to {len(limited_epics)} epics (configuration limit)")
                    return limited_epics
                else:
                    return epics
            else:
                print("⚠️ Grok response was not a list.")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print("🔎 Raw response:")
            print(response)
            return []

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON content from AI response with improved bracket counting and validation."""
        if not response:
            return "[]"
        
        import re
        
        # Look for JSON inside ```json blocks
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, response, re.IGNORECASE)
        
        if json_match:
            return json_match.group(1).strip()
        
        # Look for JSON inside ``` blocks (without language specifier)
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        code_match = re.search(code_pattern, response)
        
        if code_match:
            content = code_match.group(1).strip()
            if content.startswith(('{', '[')):
                return content
        
        # Enhanced JSON extraction with proper bracket counting
        start_idx = response.find('[')
        if start_idx == -1:
            start_idx = response.find('{')
            if start_idx == -1:
                return "[]"
        
        # Count brackets/braces to find the complete JSON structure
        if response[start_idx] == '[':
            bracket_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            return response[start_idx:i+1]
        else:  # Starting with '{'
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(response[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return response[start_idx:i+1]
        
        return response[start_idx:].strip()