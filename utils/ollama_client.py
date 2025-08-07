#!/usr/bin/env python3
"""
Ollama Client for Local LLM Integration with Backlog Automation.

This module provides a local LLM client using Ollama, compatible with the existing
agent system. Supports GPU acceleration via CUDA and multiple model options.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama client for local LLM inference."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        # Don't set session timeout - we'll use per-request timeouts instead
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                logger.info(f"[OLLAMA] Connected to Ollama server at {self.base_url}")
                logger.info(f"[OLLAMA] Available models: {[m['name'] for m in response.json().get('models', [])]}")
            else:
                raise ConnectionError(f"Ollama server returned status {response.status_code}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Ollama server: {e}")
            raise ConnectionError(f"Cannot connect to Ollama server at {self.base_url}")
    
    def generate(self, 
                prompt: str, 
                system_prompt: str = None,
                temperature: float = 0.7,
                max_tokens: int = 8000,
                stream: bool = False) -> Dict[str, Any]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dictionary with 'content' and metadata
        """
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "seed": 42
                },
                "stream": stream
            }
            
            logger.info(f"[OLLAMA] Generating with Ollama model: {self.model}")
            logger.debug(f"[OLLAMA] Request payload: {json.dumps(payload, indent=2)}")
            
            # Make request
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=300  # 5 minute timeout for 70B models
            )
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            # Parse response
            data = response.json()
            content = data.get("message", {}).get("content", "")
            
            generation_time = time.time() - start_time
            tokens_used = data.get("eval_count", 0)
            
            logger.info(f"[OLLAMA] Generated {len(content)} characters in {generation_time:.2f}s")
            logger.info(f"[OLLAMA] Tokens used: {tokens_used}")
            
            return {
                "content": content,
                "model": self.model,
                "generation_time": generation_time,
                "tokens_used": tokens_used,
                "total_duration": data.get("total_duration", 0),
                "load_duration": data.get("load_duration", 0),
                "prompt_eval_duration": data.get("prompt_eval_duration", 0),
                "eval_duration": data.get("eval_duration", 0)
            }
            
        except Exception as e:
            logger.error(f"[ERROR] Ollama generation failed: {e}")
            raise Exception(f"Ollama generation error: {str(e)}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                raise Exception(f"Failed to list models: {response.status_code}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to list models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull/download a model."""
        try:
            logger.info(f"[OLLAMA] Pulling model: {model_name}")
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300  # Model pulling can take a while
            )
            
            if response.status_code == 200:
                logger.info(f"[OLLAMA] Successfully pulled model: {model_name}")
                return True
            else:
                logger.error(f"[ERROR] Failed to pull model: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Error pulling model {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """Get information about a model."""
        model = model_name or self.model
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": model},
                timeout=10  # Quick info request
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get model info: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Error getting model info: {e}"}
    
    def estimate_cost(self, tokens_used: int) -> Dict[str, float]:
        """
        Estimate cost for local inference (mostly electricity).
        
        Args:
            tokens_used: Number of tokens generated
            
        Returns:
            Dictionary with cost estimates
        """
        # Rough estimates for local inference costs
        # Based on electricity consumption and hardware depreciation
        
        # RTX 4090 power consumption: ~450W under load
        # Electricity cost: ~$0.12/kWh (US average)
        # Hardware depreciation: ~$0.50/hour (RTX 4090 lifespan)
        
        tokens_per_second = 50  # Conservative estimate for RTX 4090
        seconds_used = tokens_used / tokens_per_second
        
        # Power cost
        power_watts = 450  # RTX 4090 under load
        electricity_cost_per_kwh = 0.12
        power_cost = (power_watts * seconds_used / 3600) * electricity_cost_per_kwh
        
        # Hardware depreciation cost
        hardware_cost_per_hour = 0.50
        hardware_cost = (seconds_used / 3600) * hardware_cost_per_hour
        
        total_cost = power_cost + hardware_cost
        
        return {
            "power_cost": power_cost,
            "hardware_cost": hardware_cost,
            "total_cost": total_cost,
            "tokens_used": tokens_used,
            "time_seconds": seconds_used
        }


class OllamaProvider:
    """Ollama provider for the agent system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "llama3.1:8b")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.client = OllamaClient(base_url=self.base_url, model=self.model)
        
    def generate_response(self, 
                         system_prompt: str, 
                         user_input: str, 
                         temperature: float = 0.7,
                         max_tokens: int = 8000) -> str:
        """Generate response using Ollama."""
        try:
            result = self.client.generate(
                prompt=user_input,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Log cost estimate
            cost_estimate = self.client.estimate_cost(result["tokens_used"])
            logger.info(f"[COST] Local inference cost: ${cost_estimate['total_cost']:.4f}")
            
            return result["content"]
            
        except Exception as e:
            logger.error(f"[ERROR] Ollama provider error: {e}")
            raise Exception(f"Ollama generation failed: {str(e)}")


# Configuration presets for different use cases
OLLAMA_CONFIGS = {
    "fast": {
        "model": "llama3.1:8b",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "balanced": {
        "model": "codellama:34b", 
        "temperature": 0.6,
        "max_tokens": 3000
    },
    "high_quality": {
        "model": "llama3.1:70b",
        "temperature": 0.5,
        "max_tokens": 8000
    },
    "code_focused": {
        "model": "codellama:34b",
        "temperature": 0.3,
        "max_tokens": 2500
    }
}


def create_ollama_provider(preset: str = "balanced", custom_config: Dict[str, Any] = None) -> OllamaProvider:
    """
    Create an Ollama provider with preset configuration.
    
    Args:
        preset: Configuration preset ("fast", "balanced", "high_quality", "code_focused")
        custom_config: Custom configuration overrides
        
    Returns:
        Configured OllamaProvider instance
    """
    config = OLLAMA_CONFIGS.get(preset, OLLAMA_CONFIGS["balanced"]).copy()
    
    if custom_config:
        config.update(custom_config)
    
    return OllamaProvider(config) 