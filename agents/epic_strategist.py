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