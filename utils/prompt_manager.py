import os
import json
from typing import Dict, Any
from string import Template

class PromptTemplateManager:
    """Manages modular, template-based prompts with dynamic context injection."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates from the prompts directory."""
        if not os.path.exists(self.prompts_dir):
            return
            
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.txt'):
                agent_name = filename.replace('.txt', '')
                template_path = os.path.join(self.prompts_dir, filename)
                
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.templates[agent_name] = Template(content)
                except Exception as e:
                    print(f"⚠️ Failed to load template {filename}: {e}")
    
    def get_prompt(self, agent_name: str, context: Dict[str, Any] = None) -> str:
        """
        Generate a prompt for the specified agent with dynamic context.
        
        Args:
            agent_name: Name of the agent (matches template filename without .txt)
            context: Dictionary of variables to substitute in the template
            
        Returns:
            Fully rendered prompt string
        """
        if agent_name not in self.templates:
            raise ValueError(f"Template not found for agent: {agent_name}")
        
        template = self.templates[agent_name]
        context = context or {}
        
        # Add default context variables
        default_context = {
            'timestamp': self._get_timestamp(),
            'project_name': context.get('project_name', 'Unknown Project'),
            'domain': context.get('domain', 'software development'),
            'output_format': context.get('output_format', 'JSON')
        }
        
        # Merge contexts (user context takes precedence)
        merged_context = {**default_context, **context}
        
        try:
            return template.safe_substitute(**merged_context)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Missing required context variable: {missing_var}")
    
    def validate_template(self, agent_name: str) -> Dict[str, Any]:
        """
        Validate a template and return information about required variables.
        
        Returns:
            Dictionary with validation results and required variables
        """
        if agent_name not in self.templates:
            return {"valid": False, "error": f"Template not found: {agent_name}"}
        
        template = self.templates[agent_name]
        template_str = template.template
        
        # Extract placeholders using Template's internal method
        from string import Template
        import re
        
        # Find all placeholders in the format ${variable} or $variable
        placeholders = re.findall(r'\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)', template_str)
        variables = []
        for match in placeholders:
            variables.extend([var for var in match if var])
        
        return {
            "valid": True,
            "required_variables": list(set(variables)),
            "template_length": len(template_str),
            "agent_name": agent_name
        }
    
    def list_templates(self) -> Dict[str, Dict]:
        """List all available templates with their validation info."""
        templates_info = {}
        for agent_name in self.templates.keys():
            templates_info[agent_name] = self.validate_template(agent_name)
        return templates_info
    
    def reload_templates(self):
        """Reload all templates from disk."""
        self.templates.clear()
        self._load_templates()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for default context."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Global instance for easy access
prompt_manager = PromptTemplateManager()
