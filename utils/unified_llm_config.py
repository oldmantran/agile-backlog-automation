"""
Unified LLM Configuration Manager
Consolidates all LLM configuration into a single, hierarchical system.

Configuration Priority (highest to lowest):
1. Runtime overrides (temporary per-request)
2. Database user settings (persistent preferences) 
3. Settings.yaml agent-specific config (project defaults)
4. Environment variables (deployment defaults)
5. Hard-coded fallbacks (system defaults)
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from utils.safe_logger import get_safe_logger

logger = get_safe_logger(__name__)

@dataclass
class LLMConfig:
    """Complete LLM configuration for an agent."""
    provider: str = "openai"
    model: str = "gpt-5-mini"  # Updated default to match current OpenAI model
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 120
    temperature: float = 0.7
    max_tokens: int = 4000
    preset: str = "balanced"
    
    # Configuration source tracking
    source: str = "fallback"
    overrides: Dict[str, str] = field(default_factory=dict)

class UnifiedLLMConfigManager:
    """Manages all LLM configuration from multiple sources."""
    
    def __init__(self, settings_file: str = "config/settings.yaml"):
        self.settings_file = settings_file
        self._agent_configs = {}
        self._global_config = None
        self._load_settings()
    
    def _load_settings(self):
        """Load configuration from settings.yaml."""
        try:
            with open(self.settings_file, 'r') as f:
                settings = yaml.safe_load(f)
                
            # Extract agent configurations
            agents = settings.get('agents', {})
            for agent_name, agent_config in agents.items():
                if isinstance(agent_config, dict):
                    self._agent_configs[agent_name] = agent_config
            
            logger.info(f"Loaded agent configurations: {list(self._agent_configs.keys())}")
            
        except Exception as e:
            logger.warning(f"Could not load settings file {self.settings_file}: {e}")
    
    def get_config(self, agent_name: str, user_id: Optional[str] = None, 
                   runtime_overrides: Optional[Dict[str, Any]] = None) -> LLMConfig:
        """
        Get unified LLM configuration for an agent.
        FRONTEND IS THE SINGLE SOURCE OF TRUTH - Database configurations take precedence.
        
        Args:
            agent_name: Name of the agent
            user_id: User ID for database preferences
            runtime_overrides: Temporary per-request overrides
        
        Returns:
            Complete LLM configuration with source tracking
        """
        config = LLMConfig()
        sources = []
        
        # 1. Hard-coded fallbacks (lowest priority)
        sources.append("fallback")
        
        # 2. Database user settings (HIGHEST PRIORITY - Frontend is the source of truth)
        if user_id:
            try:
                from utils.llm_config_manager import LLMConfigManager
                db_config_manager = LLMConfigManager()
                
                # Try to get agent-specific configuration first
                agent_config = self._get_agent_specific_config(user_id, agent_name)
                if agent_config:
                    config.provider = agent_config['provider']
                    config.model = agent_config['model']
                    if 'preset' in agent_config:
                        config.preset = agent_config['preset']
                    sources.append(f"database[{agent_name}]")
                else:
                    # Fall back to global user configuration
                    db_config = db_config_manager.get_active_configuration(user_id)
                    if db_config and db_config.get('provider'):
                        config.provider = db_config['provider']
                        if 'model' in db_config and db_config['model']:
                            config.model = db_config['model']
                        if 'preset' in db_config:
                            config.preset = db_config['preset']
                        sources.append("database[global]")
                    
            except Exception as e:
                logger.warning(f"Could not load database config for user {user_id}: {e}")
        
        # 3. Runtime overrides (highest priority for temporary changes)
        if runtime_overrides:
            for key, value in runtime_overrides.items():
                if hasattr(config, key) and value is not None:
                    setattr(config, key, value)
                    config.overrides[key] = str(value)
            if runtime_overrides:
                sources.append("runtime")
        
        # Load provider-specific configuration (API keys, URLs) from environment ONLY
        if config.provider == "openai":
            config.api_key = os.getenv("OPENAI_API_KEY")
            config.api_url = "https://api.openai.com/v1/chat/completions"
        elif config.provider == "grok":
            config.api_key = os.getenv("GROK_API_KEY") 
            config.api_url = "https://api.x.ai/v1/chat/completions"
        elif config.provider == "ollama":
            config.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Set source tracking (using safe characters for Windows)
        config.source = " -> ".join(sources)
        
        # Validate final configuration
        self._validate_config(config, agent_name)
        
        logger.info(f"Agent {agent_name} config: {config.provider}:{config.model} (sources: {config.source})")
        return config
    
    def _get_agent_specific_config(self, user_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent-specific configuration from database."""
        try:
            import sqlite3
            conn = sqlite3.connect('backlog_jobs.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT provider, model, preset
                FROM llm_configurations 
                WHERE user_id = ? AND agent_name = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
            ''', (user_id, agent_name))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'provider': row[0],
                    'model': row[1],
                    'preset': row[2]
                }
            return None
            
        except Exception as e:
            logger.warning(f"Could not load agent-specific config for {agent_name}: {e}")
            return None
    
    def _validate_config(self, config: LLMConfig, agent_name: str):
        """Validate the final configuration."""
        if config.provider not in ["openai", "grok", "ollama"]:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
        
        if config.provider != "ollama" and not config.api_key:
            raise ValueError(f"API key required for provider: {config.provider}")
        
        if not config.model:
            raise ValueError(f"Model not specified for agent: {agent_name}")
    
    def get_all_agent_configs(self, user_id: Optional[str] = None) -> Dict[str, LLMConfig]:
        """Get configuration for all agents."""
        configs = {}
        
        # Get configurations for all agents in settings.yaml
        for agent_name in self._agent_configs.keys():
            configs[agent_name] = self.get_config(agent_name, user_id)
        
        # Also include common agents that might not be in settings
        common_agents = [
            "epic_strategist", "feature_decomposer_agent", 
            "user_story_decomposer_agent", "developer_agent", "qa_lead_agent"
        ]
        
        for agent_name in common_agents:
            if agent_name not in configs:
                configs[agent_name] = self.get_config(agent_name, user_id)
        
        return configs
    
    def update_agent_config(self, agent_name: str, updates: Dict[str, Any]):
        """Update agent configuration in settings.yaml."""
        try:
            with open(self.settings_file, 'r') as f:
                settings = yaml.safe_load(f)
            
            if 'agents' not in settings:
                settings['agents'] = {}
            
            if agent_name not in settings['agents']:
                settings['agents'][agent_name] = {}
            
            # Update configuration
            settings['agents'][agent_name].update(updates)
            
            # Write back to file
            with open(self.settings_file, 'w') as f:
                yaml.dump(settings, f, default_flow_style=False, indent=2)
            
            # Reload configuration
            self._load_settings()
            
            logger.info(f"Updated configuration for agent {agent_name}: {updates}")
            
        except Exception as e:
            logger.error(f"Failed to update agent config: {e}")
            raise

# Global instance
unified_config = UnifiedLLMConfigManager()

def get_agent_config(agent_name: str, user_id: Optional[str] = None, 
                    **runtime_overrides) -> LLMConfig:
    """Convenience function to get agent configuration."""
    return unified_config.get_config(agent_name, user_id, runtime_overrides)