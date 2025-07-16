import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from string import Template
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PromptTemplateManager:
    """Manages modular, template-based prompts with dynamic context injection and versioning."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self.templates = {}
        self.template_metadata = {}
        self.template_versions = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates from the prompts directory with metadata."""
        if not os.path.exists(self.prompts_dir):
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return
            
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.txt'):
                agent_name = filename.replace('.txt', '')
                template_path = os.path.join(self.prompts_dir, filename)
                
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Calculate template hash for versioning
                    template_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    
                    # Store template with metadata
                    self.templates[agent_name] = Template(content)
                    self.template_metadata[agent_name] = {
                        'filename': filename,
                        'path': template_path,
                        'hash': template_hash,
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(template_path)),
                        'size': len(content),
                        'required_variables': self._extract_required_variables(content)
                    }
                    
                    # Store version history
                    if agent_name not in self.template_versions:
                        self.template_versions[agent_name] = []
                    
                    self.template_versions[agent_name].append({
                        'hash': template_hash,
                        'timestamp': datetime.now(),
                        'content': content
                    })
                    
                    logger.info(f"Loaded template: {agent_name} (hash: {template_hash[:8]})")
                    
                except Exception as e:
                    logger.error(f"Failed to load template {filename}: {e}")
    
    def _extract_required_variables(self, content: str) -> List[str]:
        """Extract required variables from template content."""
        import re
        # Find all ${variable} patterns
        variables = re.findall(r'\$\{([^}]+)\}', content)
        # Remove duplicates and sort
        return sorted(list(set(variables)))
    
    def get_prompt(self, agent_name: str, context: Dict[str, Any] = None) -> str:
        """
        Generate a prompt for the specified agent with dynamic context.
        
        Args:
            agent_name: Name of the agent (matches template filename without .txt)
            context: Dictionary of variables to substitute in the template
            
        Returns:
            Fully rendered prompt string
            
        Raises:
            ValueError: If template not found or required variables missing
        """
        if agent_name not in self.templates:
            available_templates = list(self.templates.keys())
            raise ValueError(f"Template not found for agent: {agent_name}. Available templates: {available_templates}")
        
        template = self.templates[agent_name]
        context = context or {}
        
        # Add default context variables
        default_context = {
            'timestamp': self._get_timestamp(),
            'project_name': context.get('project_name', 'Unknown Project'),
            'domain': context.get('domain', 'software development'),
            'output_format': context.get('output_format', 'JSON'),
            'agent_name': agent_name,
            'template_version': self.template_metadata[agent_name]['hash'][:8] if agent_name in self.template_metadata else 'unknown'
        }
        
        # Merge contexts (user context takes precedence)
        merged_context = {**default_context, **context}
        
        # Validate required variables
        required_vars = self.template_metadata.get(agent_name, {}).get('required_variables', [])
        missing_vars = [var for var in required_vars if var not in merged_context]
        
        if missing_vars:
            logger.warning(f"Missing required variables for {agent_name}: {missing_vars}")
            # Provide fallback values for missing variables
            for var in missing_vars:
                merged_context[var] = self._get_fallback_value(var)
        
        try:
            result = template.safe_substitute(**merged_context)
            
            # Log template usage for debugging
            logger.debug(f"Generated prompt for {agent_name} with {len(merged_context)} context variables")
            
            return result
            
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Missing required context variable: {missing_var}")
        except Exception as e:
            logger.error(f"Error generating prompt for {agent_name}: {e}")
            raise ValueError(f"Failed to generate prompt for {agent_name}: {e}")
    
    def _get_fallback_value(self, variable: str) -> str:
        """Provide fallback values for missing template variables."""
        fallbacks = {
            'project_name': 'Project',
            'domain': 'software development',
            'target_users': 'end users',
            'timeline': 'not specified',
            'budget_constraints': 'standard budget',
            'methodology': 'Agile/Scrum',
            'tech_stack': 'Modern Web Stack',
            'architecture_pattern': 'MVC',
            'database_type': 'SQL Database',
            'cloud_platform': 'Cloud Platform',
            'team_size': '5-8 developers',
            'sprint_duration': '2 weeks',
            'platform': 'Web',
            'integrations': 'standard integrations',
            'test_environment': 'standard test environment',
            'quality_standards': 'industry standards',
            'security_requirements': 'standard security'
        }
        return fallbacks.get(variable, f'[MISSING: {variable}]')
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for template context."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def validate_template(self, agent_name: str) -> Dict[str, Any]:
        """
        Validate a template and return validation results.
        
        Args:
            agent_name: Name of the agent template to validate
            
        Returns:
            Dictionary with validation results
        """
        if agent_name not in self.templates:
            return {
                "valid": False,
                "error": f"Template not found: {agent_name}",
                "available_templates": list(self.templates.keys())
            }
        
        try:
            metadata = self.template_metadata[agent_name]
            template = self.templates[agent_name]
            
            # Test template with minimal context
            test_context = {
                'project_name': 'Test Project',
                'domain': 'test domain',
                'timestamp': self._get_timestamp()
            }
            
            # Add fallback values for all required variables
            for var in metadata.get('required_variables', []):
                if var not in test_context:
                    test_context[var] = self._get_fallback_value(var)
            
            # Test template substitution
            result = template.safe_substitute(**test_context)
            
            return {
                "valid": True,
                "required_variables": metadata.get('required_variables', []),
                "template_size": metadata.get('size', 0),
                "last_modified": metadata.get('last_modified'),
                "hash": metadata.get('hash'),
                "test_result_length": len(result)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "template_name": agent_name
            }
    
    def get_template_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template."""
        if agent_name not in self.templates:
            return None
        
        metadata = self.template_metadata.get(agent_name, {})
        versions = self.template_versions.get(agent_name, [])
        
        return {
            "name": agent_name,
            "filename": metadata.get('filename'),
            "path": metadata.get('path'),
            "hash": metadata.get('hash'),
            "last_modified": metadata.get('last_modified'),
            "size": metadata.get('size'),
            "required_variables": metadata.get('required_variables', []),
            "version_count": len(versions),
            "latest_version": versions[-1] if versions else None
        }
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with their metadata."""
        templates = []
        for agent_name in self.templates.keys():
            info = self.get_template_info(agent_name)
            if info:
                templates.append(info)
        return templates
    
    def reload_templates(self):
        """Reload all templates from disk."""
        logger.info("Reloading all templates...")
        self.templates.clear()
        self.template_metadata.clear()
        self._load_templates()
        logger.info(f"Reloaded {len(self.templates)} templates")
    
    def get_template_content(self, agent_name: str) -> Optional[str]:
        """Get the raw content of a template."""
        if agent_name not in self.templates:
            return None
        
        metadata = self.template_metadata.get(agent_name, {})
        template_path = metadata.get('path')
        
        if template_path and os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read template content for {agent_name}: {e}")
                return None
        
        return None

# Global instance
prompt_manager = PromptTemplateManager()
