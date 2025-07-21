#!/usr/bin/env python3
"""
LLM Configuration Manager for Backlog Automation.

This module manages LLM configurations from the database and provides
a unified interface for agents to get their LLM settings.
"""

import os
import logging
from typing import Dict, Any, Optional
from db import db
from utils.user_id_resolver import user_id_resolver

logger = logging.getLogger(__name__)

class LLMConfigManager:
    """Manages LLM configurations from database with environment fallback."""
    
    def __init__(self):
        self._cached_config = None
        self._cache_timestamp = None
        self._cache_duration = 5  # Cache for 5 seconds (much shorter for responsiveness)
    
    def get_active_configuration(self, user_id: str = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get the active LLM configuration for a user.
        
        Args:
            user_id: User ID (if None, uses current user)
            force_refresh: If True, bypass cache and reload from database
            
        Returns:
            Dictionary with LLM configuration
        """
        if not user_id:
            user_id = user_id_resolver.get_default_user_id()
        
        # Check cache first (unless force_refresh is True)
        if not force_refresh and self._is_cache_valid():
            return self._cached_config
        
        # Try to get from database
        config = db.get_active_llm_configuration(user_id)
        
        if config:
            # Convert database config to standard format
            standard_config = self._convert_db_config_to_standard(config)
            self._cache_config(standard_config)
            logger.info(f"📋 Loaded active LLM config from database: {config['name']} ({config['provider']})")
            return standard_config
        
        # Fallback to environment variables
        env_config = self._load_from_environment()
        self._cache_config(env_config)
        logger.info(f"📋 Loaded LLM config from environment: {env_config['provider']}")
        return env_config
    
    def _convert_db_config_to_standard(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database configuration to standard format."""
        return {
            'provider': db_config['provider'],
            'model': db_config['model'],
            'api_key': db_config.get('api_key', ''),
            'base_url': db_config.get('base_url', ''),
            'preset': db_config.get('preset', ''),
            'name': db_config.get('name', ''),
            'is_active': bool(db_config.get('is_active', False)),
            'is_default': bool(db_config.get('is_default', False))
        }
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load LLM configuration from environment variables."""
        return {
            'provider': os.getenv('LLM_PROVIDER', 'openai'),
            'model': os.getenv('OLLAMA_MODEL', 'llama3.1:8b'),
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            'preset': os.getenv('OLLAMA_PRESET', 'fast'),
            'name': 'Environment Default',
            'is_active': True,
            'is_default': True
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid."""
        if not self._cached_config or not self._cache_timestamp:
            return False
        
        import time
        return (time.time() - self._cache_timestamp) < self._cache_duration
    
    def _cache_config(self, config: Dict[str, Any]):
        """Cache the configuration."""
        self._cached_config = config
        import time
        self._cache_timestamp = time.time()
    
    def clear_cache(self):
        """Clear the configuration cache."""
        self._cached_config = None
        self._cache_timestamp = None
        logger.info("🧹 Cleared LLM configuration cache")
    
    def force_refresh_configuration(self, user_id: str = None) -> Dict[str, Any]:
        """
        Force refresh the configuration from database, bypassing cache.
        
        Args:
            user_id: User ID (if None, uses current user)
            
        Returns:
            Fresh configuration from database
        """
        logger.info("Forcing configuration refresh from database")
        return self.get_active_configuration(user_id, force_refresh=True)
    
    def get_provider_config(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get provider-specific configuration for agents.
        
        Args:
            user_id: User ID (if None, uses current user)
            
        Returns:
            Dictionary with provider-specific settings
        """
        config = self.get_active_configuration(user_id)
        provider = config['provider']
        
        if provider == 'ollama':
            return {
                'provider': 'ollama',
                'model': config['model'],
                'base_url': config['base_url'],
                'preset': config['preset']
            }
        elif provider == 'openai':
            return {
                'provider': 'openai',
                'model': config['model'],
                'api_key': config['api_key']
            }
        elif provider == 'grok':
            return {
                'provider': 'grok',
                'model': config['model'],
                'api_key': config['api_key']
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def get_environment_variables(self, user_id: str = None) -> Dict[str, str]:
        """
        Get environment variables that would be set for this configuration.
        
        Args:
            user_id: User ID (if None, uses current user)
            
        Returns:
            Dictionary of environment variable names and values
        """
        config = self.get_active_configuration(user_id)
        provider = config['provider']
        
        env_vars = {
            'LLM_PROVIDER': provider
        }
        
        if provider == 'ollama':
            env_vars.update({
                'OLLAMA_MODEL': config['model'],
                'OLLAMA_BASE_URL': config['base_url'],
                'OLLAMA_PRESET': config['preset']
            })
        elif provider == 'openai':
            env_vars.update({
                'OPENAI_API_KEY': config['api_key']
            })
        elif provider == 'grok':
            env_vars.update({
                'GROK_API_KEY': config['api_key']
            })
        
        return env_vars

# Global instance
llm_config_manager = LLMConfigManager()

def get_llm_config(user_id: str = None) -> Dict[str, Any]:
    """Convenience function to get LLM configuration."""
    return llm_config_manager.get_active_configuration(user_id)

def get_llm_provider_config(user_id: str = None) -> Dict[str, Any]:
    """Convenience function to get provider-specific configuration."""
    return llm_config_manager.get_provider_config(user_id)

def get_llm_env_vars(user_id: str = None) -> Dict[str, str]:
    """Convenience function to get environment variables for current config."""
    return llm_config_manager.get_environment_variables(user_id) 