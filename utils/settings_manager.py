#!/usr/bin/env python3
"""
Settings Manager - Handles user settings with database storage and config fallback.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from db import db

logger = logging.getLogger(__name__)

@dataclass
class WorkItemLimits:
    """Work item limits configuration."""
    max_epics: Optional[int] = 2
    max_features_per_epic: Optional[int] = 3
    max_user_stories_per_feature: Optional[int] = 5
    max_tasks_per_user_story: Optional[int] = 5
    max_test_cases_per_user_story: Optional[int] = 5

@dataclass
class VisualSettings:
    """Visual settings configuration."""
    glow_intensity: int = 70

class SettingsManager:
    """Manages user settings with database storage and config fallback."""
    
    def __init__(self, config_settings: Dict[str, Any]):
        self.config_settings = config_settings
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validate config_settings structure
        if not isinstance(config_settings, dict):
            raise ValueError("config_settings must be a dictionary")
        
        # Log configuration precedence rules
        self.logger.info("Settings precedence: session > user_default > global_default > config_fallback")
        
        # Validate critical configuration exists
        self._validate_config_completeness()
    
    def get_work_item_limits(self, user_id: str, session_id: str = None) -> WorkItemLimits:
        """
        Get work item limits with priority: session > user_default > global_default.
        
        Args:
            user_id: User identifier
            session_id: Session identifier (optional)
            
        Returns:
            WorkItemLimits with resolved values
        """
        # Get global defaults from config
        global_limits = self.config_settings.get('work_item_limits', {})
        default_limits = WorkItemLimits(
            max_epics=global_limits.get('max_epics', 2),
            max_features_per_epic=global_limits.get('max_features_per_epic', 3),
            max_user_stories_per_feature=global_limits.get('max_user_stories_per_feature', 5),
            max_tasks_per_user_story=global_limits.get('max_tasks_per_user_story', 5),
            max_test_cases_per_user_story=global_limits.get('max_test_cases_per_user_story', 5)
        )
        
        # Get user defaults from database
        user_defaults = db.get_user_settings(user_id, 'work_item_limits', 'user_default')
        
        # Get session settings from database (if session_id provided)
        session_settings = {}
        if session_id:
            session_settings = db.get_user_settings(session_id, 'work_item_limits', 'session')
        
        # Resolve settings with priority
        resolved_limits = WorkItemLimits()
        
        # Helper function to get value with priority
        def get_resolved_value(key: str, config_key: str) -> Optional[int]:
            # Priority: session > user_default > global_default
            if session_settings.get(key):
                return int(session_settings[key])
            elif user_defaults.get(key):
                return int(user_defaults[key])
            else:
                return getattr(default_limits, config_key)
        
        resolved_limits.max_epics = get_resolved_value('max_epics', 'max_epics')
        resolved_limits.max_features_per_epic = get_resolved_value('max_features_per_epic', 'max_features_per_epic')
        resolved_limits.max_user_stories_per_feature = get_resolved_value('max_user_stories_per_feature', 'max_user_stories_per_feature')
        resolved_limits.max_tasks_per_user_story = get_resolved_value('max_tasks_per_user_story', 'max_tasks_per_user_story')
        resolved_limits.max_test_cases_per_user_story = get_resolved_value('max_test_cases_per_user_story', 'max_test_cases_per_user_story')
        
        self.logger.info(f"Resolved work item limits for {user_id}: {resolved_limits}")
        return resolved_limits
    
    def has_custom_work_item_limits(self, user_id: str) -> bool:
        """
        Check if a user has custom work item limits (not system defaults).
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has custom settings, False if using system defaults
        """
        return db.has_custom_settings(user_id, 'work_item_limits', 'user_default')
    
    def get_work_item_limits_with_flags(self, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """
        Get work item limits with flags indicating if they are custom defaults.
        
        Args:
            user_id: User identifier
            session_id: Session identifier (optional)
            
        Returns:
            Dictionary with limits and flags
        """
        # Get settings with flags
        settings_with_flags = db.get_settings_with_flags(user_id, 'work_item_limits', 'user_default')
        
        # Get resolved limits
        resolved_limits = self.get_work_item_limits(user_id, session_id)
        
        # Combine into result
        result = {
            'limits': {
                'max_epics': resolved_limits.max_epics,
                'max_features_per_epic': resolved_limits.max_features_per_epic,
                'max_user_stories_per_feature': resolved_limits.max_user_stories_per_feature,
                'max_tasks_per_user_story': resolved_limits.max_tasks_per_user_story,
                'max_test_cases_per_user_story': resolved_limits.max_test_cases_per_user_story
            },
            'has_custom_settings': self.has_custom_work_item_limits(user_id),
            'settings_detail': settings_with_flags
        }
        
        return result
    
    def save_work_item_limits(self, user_id: str, limits: Dict[str, Any], 
                             scope: str = 'session', session_id: str = None, is_user_default: bool = False) -> bool:
        """
        Save work item limits to database.
        
        Args:
            user_id: User identifier
            limits: Dictionary of limits to save
            scope: 'session' or 'user_default'
            session_id: Session identifier (for session scope)
            is_user_default: Whether these are custom user defaults (vs system defaults)
            
        Returns:
            True if saved successfully
        """
        target_id = session_id if scope == 'session' else user_id
        
        try:
            for key, value in limits.items():
                if key in ['max_epics', 'max_features_per_epic', 'max_user_stories_per_feature', 
                          'max_tasks_per_user_story', 'max_test_cases_per_user_story']:
                    success = db.save_user_setting(
                        target_id, 'work_item_limits', key, str(value), scope, is_user_default
                    )
                    if not success:
                        self.logger.error(f"Failed to save {key} = {value}")
                        return False
            
            self.logger.info(f"Saved work item limits for {target_id} ({scope}, user_default={is_user_default}): {limits}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save work item limits: {e}")
            return False
    
    def get_visual_settings(self, user_id: str, session_id: str = None) -> VisualSettings:
        """
        Get visual settings with priority: session > user_default > global_default.
        
        Args:
            user_id: User identifier
            session_id: Session identifier (optional)
            
        Returns:
            VisualSettings with resolved values
        """
        # Get user defaults from database
        user_defaults = db.get_user_settings(user_id, 'visual_settings', 'user_default')
        
        # Get session settings from database (if session_id provided)
        session_settings = {}
        if session_id:
            session_settings = db.get_user_settings(session_id, 'visual_settings', 'session')
        
        # Resolve settings with priority
        glow_intensity = 70  # Default
        
        if session_settings.get('glow_intensity'):
            glow_intensity = int(session_settings['glow_intensity'])
        elif user_defaults.get('glow_intensity'):
            glow_intensity = int(user_defaults['glow_intensity'])
        
        resolved_settings = VisualSettings(glow_intensity=glow_intensity)
        
        self.logger.info(f"Resolved visual settings for {user_id}: {resolved_settings}")
        return resolved_settings
    
    def save_visual_settings(self, user_id: str, settings: Dict[str, Any], 
                           scope: str = 'session', session_id: str = None) -> bool:
        """
        Save visual settings to database.
        
        Args:
            user_id: User identifier
            settings: Dictionary of settings to save
            scope: 'session' or 'user_default'
            session_id: Session identifier (for session scope)
            
        Returns:
            True if saved successfully
        """
        target_id = session_id if scope == 'session' else user_id
        
        try:
            for key, value in settings.items():
                if key in ['glow_intensity']:
                    success = db.save_user_setting(
                        target_id, 'visual_settings', key, str(value), scope
                    )
                    if not success:
                        self.logger.error(f"Failed to save {key} = {value}")
                        return False
            
            self.logger.info(f"Saved visual settings for {target_id} ({scope}): {settings}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save visual settings: {e}")
            return False
    
    def get_all_settings(self, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """
        Get all settings for a user/session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier (optional)
            
        Returns:
            Dictionary with all settings
        """
        work_item_limits = self.get_work_item_limits(user_id, session_id)
        visual_settings = self.get_visual_settings(user_id, session_id)
        
        return {
            'work_item_limits': {
                'max_epics': work_item_limits.max_epics,
                'max_features_per_epic': work_item_limits.max_features_per_epic,
                'max_user_stories_per_feature': work_item_limits.max_user_stories_per_feature,
                'max_tasks_per_user_story': work_item_limits.max_tasks_per_user_story,
                'max_test_cases_per_user_story': work_item_limits.max_test_cases_per_user_story
            },
            'visual_settings': {
                'glow_intensity': visual_settings.glow_intensity
            }
        }
    
    def save_all_settings(self, user_id: str, settings: Dict[str, Any], 
                         scope: str = 'session', session_id: str = None) -> bool:
        """
        Save all settings to database.
        
        Args:
            user_id: User identifier
            settings: Dictionary with all settings
            scope: 'session' or 'user_default'
            session_id: Session identifier (for session scope)
            
        Returns:
            True if saved successfully
        """
        success = True
        
        if 'work_item_limits' in settings:
            success &= self.save_work_item_limits(
                user_id, settings['work_item_limits'], scope, session_id
            )
        
        if 'visual_settings' in settings:
            success &= self.save_visual_settings(
                user_id, settings['visual_settings'], scope, session_id
            )
        
        return success
    
    def delete_session_settings(self, session_id: str) -> bool:
        """
        Delete all session-specific settings.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            # Delete work item limits
            db.delete_user_settings(session_id, 'work_item_limits', 'session')
            
            # Delete visual settings
            db.delete_user_settings(session_id, 'visual_settings', 'session')
            
            self.logger.info(f"Deleted session settings for {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session settings: {e}")
            return False
    
    def get_setting_history(self, user_id: str, setting_type: str = None) -> List[Dict[str, Any]]:
        """
        Get setting change history for audit trail.
        
        Args:
            user_id: User identifier
            setting_type: Type of settings to get history for (optional)
            
        Returns:
            List of setting changes
        """
        return db.get_setting_history(user_id, setting_type)
    
    def _validate_config_completeness(self) -> None:
        """Validate that critical configuration sections exist."""
        required_sections = ['work_item_limits', 'agents', 'workflow']
        missing_sections = []
        
        for section in required_sections:
            if section not in self.config_settings:
                missing_sections.append(section)
        
        if missing_sections:
            error_msg = f"Missing critical configuration sections: {missing_sections}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate work_item_limits structure
        wil_config = self.config_settings.get('work_item_limits', {})
        if not isinstance(wil_config, dict):
            raise ValueError("work_item_limits must be a dictionary")
        
        # Validate agents configuration
        agents_config = self.config_settings.get('agents', {})
        if not isinstance(agents_config, dict):
            raise ValueError("agents configuration must be a dictionary")
        
        # Validate workflow configuration
        workflow_config = self.config_settings.get('workflow', {})
        if not isinstance(workflow_config, dict):
            raise ValueError("workflow configuration must be a dictionary")
        
        sequence = workflow_config.get('sequence', [])
        if not isinstance(sequence, list) or len(sequence) == 0:
            raise ValueError("workflow.sequence must be a non-empty list")
        
        self.logger.info("Configuration validation passed")
    
    def validate_environment_variables(self) -> Dict[str, Any]:
        """Validate required environment variables are present."""
        import os
        
        validation_report = {
            "status": "healthy",
            "missing_vars": [],
            "warnings": []
        }
        
        # Critical environment variables
        critical_vars = [
            "AZURE_DEVOPS_PAT",
            "AZURE_DEVOPS_ORG", 
            "AZURE_DEVOPS_PROJECT"
        ]
        
        # Optional but recommended
        recommended_vars = [
            "LLM_PROVIDER",
            "OLLAMA_MODEL",
            "OPENAI_API_KEY",
            "USER_ID"
        ]
        
        for var in critical_vars:
            if not os.getenv(var):
                validation_report["missing_vars"].append(var)
                validation_report["status"] = "unhealthy"
        
        for var in recommended_vars:
            if not os.getenv(var):
                validation_report["warnings"].append(f"Recommended variable {var} not set")
        
        return validation_report 