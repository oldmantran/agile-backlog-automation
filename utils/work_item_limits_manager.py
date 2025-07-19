#!/usr/bin/env python3
"""
Work Item Limits Manager - Simplified version without cost calculations
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class WorkItemLimits:
    """Configuration for work item limits."""
    enabled: bool = True
    max_epics: Optional[int] = 2
    max_features_per_epic: Optional[int] = 3
    max_user_stories_per_feature: Optional[int] = 5
    max_tasks_per_user_story: Optional[int] = 5
    max_test_cases_per_user_story: Optional[int] = 5


@dataclass
class LimitValidation:
    """Result of limit validation."""
    valid: bool
    warnings: List[str]
    max_possible_items: Dict[str, int]


class WorkItemLimitsManager:
    """Manages work item limits for backlog generation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = self._load_config(config)
    
    def _load_config(self, config: Dict[str, Any]) -> WorkItemLimits:
        """Load work item limits configuration from config dict."""
        limits_config = config.get('work_item_limits', {})
        
        return WorkItemLimits(
            enabled=limits_config.get('enabled', True),
            max_epics=limits_config.get('max_epics', 2),
            max_features_per_epic=limits_config.get('max_features_per_epic', 3),
            max_user_stories_per_feature=limits_config.get('max_user_stories_per_feature', 5),
            max_tasks_per_user_story=limits_config.get('max_tasks_per_user_story', 5),
            max_test_cases_per_user_story=limits_config.get('max_test_cases_per_user_story', 5)
        )
    
    def validate_limits(self, user_limits: Optional[Dict[str, Any]] = None) -> LimitValidation:
        """
        Validate work item limits.
        
        Args:
            user_limits: User-provided limits (can override config)
            
        Returns:
            LimitValidation with validation results
        """
        if not self.config.enabled:
            return LimitValidation(
                valid=True,
                warnings=[],
                max_possible_items={}
            )
        
        # Merge user limits with config defaults
        limits = {
            'max_epics': user_limits.get('max_epics', self.config.max_epics) if user_limits else self.config.max_epics,
            'max_features_per_epic': user_limits.get('max_features_per_epic', self.config.max_features_per_epic) if user_limits else self.config.max_features_per_epic,
            'max_user_stories_per_feature': user_limits.get('max_user_stories_per_feature', self.config.max_user_stories_per_feature) if user_limits else self.config.max_user_stories_per_feature,
            'max_tasks_per_user_story': user_limits.get('max_tasks_per_user_story', self.config.max_tasks_per_user_story) if user_limits else self.config.max_tasks_per_user_story,
            'max_test_cases_per_user_story': user_limits.get('max_test_cases_per_user_story', self.config.max_test_cases_per_user_story) if user_limits else self.config.max_test_cases_per_user_story
        }
        
        warnings = []
        
        # Check for negative values
        for key, value in limits.items():
            if value is not None and value < 0:
                warnings.append(f"{key} cannot be negative: {value}")
        
        # Check for unreasonably high values
        if limits.get('max_epics') is not None and limits.get('max_epics', 0) > 50:
            warnings.append("max_epics cannot exceed 50")
        
        if limits.get('max_features_per_epic') is not None and limits.get('max_features_per_epic', 0) > 20:
            warnings.append("max_features_per_epic cannot exceed 20")
        
        if limits.get('max_user_stories_per_feature') is not None and limits.get('max_user_stories_per_feature', 0) > 15:
            warnings.append("max_user_stories_per_feature cannot exceed 15")
        
        if limits.get('max_tasks_per_user_story') is not None and limits.get('max_tasks_per_user_story', 0) > 20:
            warnings.append("max_tasks_per_user_story cannot exceed 20")
        
        if limits.get('max_test_cases_per_user_story') is not None and limits.get('max_test_cases_per_user_story', 0) > 25:
            warnings.append("max_test_cases_per_user_story cannot exceed 25")
        
        # Calculate max possible items
        max_possible_items = self._calculate_max_possible_items(limits)
        
        return LimitValidation(
            valid=len(warnings) == 0,
            warnings=warnings,
            max_possible_items=max_possible_items
        )
    
    def _calculate_max_possible_items(self, limits: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate maximum possible items that can be generated with current limits.
        
        Args:
            limits: Current limits
            
        Returns:
            Dictionary with max possible counts for each item type
        """
        max_items = {}
        
        if limits['max_epics']:
            max_items['epics'] = limits['max_epics']
            
            if limits['max_features_per_epic']:
                max_items['features'] = limits['max_epics'] * limits['max_features_per_epic']
                
                if limits['max_user_stories_per_feature']:
                    max_items['user_stories'] = (limits['max_epics'] * 
                                               limits['max_features_per_epic'] * 
                                               limits['max_user_stories_per_feature'])
                    
                    if limits['max_tasks_per_user_story']:
                        max_items['tasks'] = (limits['max_epics'] * 
                                            limits['max_features_per_epic'] * 
                                            limits['max_user_stories_per_feature'] * 
                                            limits['max_tasks_per_user_story'])
                    
                    if limits['max_test_cases_per_user_story']:
                        max_items['test_cases'] = (limits['max_epics'] * 
                                                 limits['max_features_per_epic'] * 
                                                 limits['max_user_stories_per_feature'] * 
                                                 limits['max_test_cases_per_user_story'])
        
        return max_items
    
    def get_preset_config(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a named preset.
        
        Args:
            preset_name: Name of preset (small, medium, large, unlimited)
            
        Returns:
            Preset configuration or None if not found
        """
        presets = {
            'small': {
                'max_epics': 2,
                'max_features_per_epic': 3,
                'max_user_stories_per_feature': 4,
                'max_tasks_per_user_story': 4,
                'max_test_cases_per_user_story': 3
            },
            'medium': {
                'max_epics': 3,
                'max_features_per_epic': 4,
                'max_user_stories_per_feature': 5,
                'max_tasks_per_user_story': 5,
                'max_test_cases_per_user_story': 4
            },
            'large': {
                'max_epics': 5,
                'max_features_per_epic': 6,
                'max_user_stories_per_feature': 6,
                'max_tasks_per_user_story': 6,
                'max_test_cases_per_user_story': 5
            },
            'unlimited': {
                'max_epics': None,
                'max_features_per_epic': None,
                'max_user_stories_per_feature': None,
                'max_tasks_per_user_story': None,
                'max_test_cases_per_user_story': None
            }
        }
        
        return presets.get(preset_name)
    
    def get_current_limits(self) -> Dict[str, Any]:
        """
        Get current work item limits.
        
        Returns:
            Dictionary with current limits
        """
        return {
            'max_epics': self.config.max_epics,
            'max_features_per_epic': self.config.max_features_per_epic,
            'max_user_stories_per_feature': self.config.max_user_stories_per_feature,
            'max_tasks_per_user_story': self.config.max_tasks_per_user_story,
            'max_test_cases_per_user_story': self.config.max_test_cases_per_user_story
        } 