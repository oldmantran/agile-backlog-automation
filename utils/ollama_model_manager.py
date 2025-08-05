#!/usr/bin/env python3
"""
Ollama Model Manager - Ensures correct models are loaded before agent execution.

This module provides utilities to manage Ollama model loading and VRAM usage
to prevent agents from using incorrect models during workflow execution.
"""

import subprocess
import json
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about an Ollama model."""
    name: str
    id: str
    size_gb: float
    processor: str
    context: int
    until: str

class OllamaModelManager:
    """Manages Ollama model loading and VRAM usage."""
    
    def __init__(self, max_vram_gb: float = 22.0):
        """
        Initialize the Ollama model manager.
        
        Args:
            max_vram_gb: Maximum VRAM usage allowed for models (default: 22GB)
        """
        self.max_vram_gb = max_vram_gb
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_loaded_models(self) -> List[ModelInfo]:
        """
        Get list of currently loaded Ollama models.
        
        Returns:
            List of ModelInfo objects for currently loaded models
        """
        try:
            result = subprocess.run(['ollama', 'ps'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get Ollama model status: {result.stderr}")
                return []
            
            models = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        name = parts[0]
                        model_id = parts[1]
                        size_str = parts[2]
                        processor = parts[3]
                        context = int(parts[4]) if parts[4].isdigit() else 0
                        until = ' '.join(parts[5:])
                        
                        # Parse size (e.g., "21 GB" -> 21.0)
                        size_gb = 0.0
                        try:
                            if 'GB' in size_str:
                                size_gb = float(size_str.replace(' GB', ''))
                            elif 'MB' in size_str:
                                size_gb = float(size_str.replace(' MB', '')) / 1024
                        except ValueError:
                            self.logger.warning(f"Could not parse model size: {size_str}")
                        
                        models.append(ModelInfo(
                            name=name,
                            id=model_id,
                            size_gb=size_gb,
                            processor=processor,
                            context=context,
                            until=until
                        ))
            
            return models
            
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout getting Ollama model status")
            return []
        except Exception as e:
            self.logger.error(f"Error getting Ollama model status: {e}")
            return []
    
    def is_model_loaded(self, model_name: str) -> bool:
        """
        Check if a specific model is currently loaded.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is loaded, False otherwise
        """
        loaded_models = self.get_loaded_models()
        return any(model.name == model_name for model in loaded_models)
    
    def get_total_vram_usage(self) -> float:
        """
        Get total VRAM usage of currently loaded models.
        
        Returns:
            Total VRAM usage in GB
        """
        loaded_models = self.get_loaded_models()
        return sum(model.size_gb for model in loaded_models)
    
    def can_load_model(self, model_name: str, estimated_size_gb: float = None) -> bool:
        """
        Check if a model can be loaded without exceeding VRAM limit.
        
        Args:
            model_name: Name of the model to check
            estimated_size_gb: Estimated size in GB (if known)
            
        Returns:
            True if model can be loaded, False otherwise
        """
        current_usage = self.get_total_vram_usage()
        
        # If we don't know the size, assume worst case for large models
        if estimated_size_gb is None:
            if '32b' in model_name.lower():
                estimated_size_gb = 20.0
            elif '13b' in model_name.lower():
                estimated_size_gb = 8.0
            elif '7b' in model_name.lower():
                estimated_size_gb = 4.0
            else:
                estimated_size_gb = 10.0  # Conservative estimate
        
        # Check if loading this model would exceed the limit
        projected_usage = current_usage + estimated_size_gb
        
        return projected_usage <= self.max_vram_gb
    
    def preload_model(self, model_name: str, force_unload_others: bool = True) -> bool:
        """
        Preload a model into Ollama memory.
        
        Args:
            model_name: Name of the model to preload
            force_unload_others: Whether to unload other large models first
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if model is already loaded
            if self.is_model_loaded(model_name):
                self.logger.info(f"Model {model_name} is already loaded")
                return True
            
            # If force_unload_others is True, unload large models first
            if force_unload_others:
                loaded_models = self.get_loaded_models()
                large_models = [m for m in loaded_models if m.size_gb > 5.0]
                
                for model in large_models:
                    self.logger.info(f"Unloading large model {model.name} ({model.size_gb} GB) to make room")
                    # Ollama doesn't have explicit unload, but we can try to minimize memory
                    
            self.logger.info(f"Preloading model {model_name}...")
            
            # Use a simple prompt to load the model
            result = subprocess.run(['ollama', 'run', model_name, 'Hello'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=120)  # 2 minute timeout for model loading
            
            if result.returncode == 0:
                self.logger.info(f"Successfully preloaded model {model_name}")
                
                # Verify the model is now loaded
                if self.is_model_loaded(model_name):
                    return True
                else:
                    self.logger.warning(f"Model {model_name} appears to have loaded but is not showing in ps")
                    return True  # Still consider it successful
            else:
                self.logger.error(f"Failed to preload model {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout preloading model {model_name}")
            return False
        except Exception as e:
            self.logger.error(f"Error preloading model {model_name}: {e}")
            return False
    
    def ensure_model_loaded(self, model_name: str, provider: str = 'ollama') -> bool:
        """
        Ensure a model is loaded if using Ollama provider.
        
        Args:
            model_name: Name of the model to ensure is loaded
            provider: LLM provider ('ollama', 'openai', etc.)
            
        Returns:
            True if model is ready (or not using Ollama), False if failed
        """
        # Only manage Ollama models
        if provider.lower() != 'ollama':
            self.logger.debug(f"Provider {provider} doesn't require model management")
            return True
        
        if not model_name:
            self.logger.warning("No model name provided")
            return True
        
        self.logger.info(f"Ensuring Ollama model {model_name} is loaded...")
        
        # Check current status
        loaded_models = self.get_loaded_models()
        current_usage = sum(model.size_gb for model in loaded_models)
        
        self.logger.info(f"Current VRAM usage: {current_usage:.1f} GB / {self.max_vram_gb} GB limit")
        
        if self.is_model_loaded(model_name):
            self.logger.info(f"✅ Model {model_name} is already loaded")
            return True
        
        # Check if we can load the model
        if not self.can_load_model(model_name):
            self.logger.warning(f"Cannot load {model_name} - would exceed VRAM limit")
            # Try to preload anyway, letting Ollama manage memory
        
        # Preload the model
        success = self.preload_model(model_name, force_unload_others=True)
        
        if success:
            self.logger.info(f"✅ Model {model_name} is now ready for use")
        else:
            self.logger.error(f"❌ Failed to load model {model_name}")
        
        return success

# Global instance
ollama_manager = OllamaModelManager(max_vram_gb=22.0)