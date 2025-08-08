"""
Model Fallback Manager - Handles intelligent model switching for quality optimization
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from utils.safe_logger import get_safe_logger

@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    display_name: str
    timeout_seconds: int
    max_attempts: int
    strengths: List[str]  # What this model is good at
    
@dataclass 
class ModelAttempt:
    """Record of a model attempt."""
    model_name: str
    attempt_number: int
    success: bool
    quality_score: int
    error_message: Optional[str]
    duration_seconds: float

class ModelFallbackManager:
    """Manages intelligent model fallback for quality optimization."""
    
    def __init__(self):
        self.logger = get_safe_logger(__name__)
        self.attempt_history: List[ModelAttempt] = []
        
        # Define model hierarchy for epic generation
        # Order: qwen2.5:14b first (better quality), then llama3.1:8b (faster fallback)
        self.epic_models = [
            ModelConfig(
                name="qwen2.5:14b-instruct-q4_K_M", 
                display_name="Qwen 2.5 14B Instruct",
                timeout_seconds=300,  # Increased from 240 for better success rate
                max_attempts=3,
                strengths=["domain_knowledge", "detailed_output", "quality"]
            ),
            ModelConfig(
                name="llama3.1:8b-instruct-q4_K_M",
                display_name="Llama 3.1 8B Instruct",
                timeout_seconds=240,  # Increased from 180 for better success rate
                max_attempts=3,
                strengths=["instruction_following", "structured_output", "speed"]
            )
        ]
        
    def get_next_model_for_epics(self) -> Tuple[ModelConfig, int]:
        """
        Get the next model to try for epic generation.
        
        Returns:
            Tuple of (ModelConfig, attempt_number_for_this_model)
        """
        # Check if we should try the first model
        primary_attempts = self._count_model_attempts(self.epic_models[0].name)
        if primary_attempts < self.epic_models[0].max_attempts:
            return self.epic_models[0], primary_attempts + 1
            
        # Check if we should try the second model
        secondary_attempts = self._count_model_attempts(self.epic_models[1].name)
        if secondary_attempts < self.epic_models[1].max_attempts:
            return self.epic_models[1], secondary_attempts + 1
            
        # All models exhausted, return the best fallback
        self.logger.warning("All epic generation models exhausted, using final fallback")
        return self.epic_models[1], secondary_attempts + 1
    
    def record_attempt(self, model_name: str, attempt_number: int, success: bool, 
                      quality_score: int, error_message: Optional[str] = None,
                      duration_seconds: float = 0.0):
        """Record the result of a model attempt."""
        attempt = ModelAttempt(
            model_name=model_name,
            attempt_number=attempt_number,
            success=success,
            quality_score=quality_score,
            error_message=error_message,
            duration_seconds=duration_seconds
        )
        
        self.attempt_history.append(attempt)
        
        # Log the attempt
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"[MODEL ATTEMPT] {model_name} attempt {attempt_number}: {status} "
                        f"(score: {quality_score}/100, time: {duration_seconds:.1f}s)")
        
        if error_message:
            self.logger.info(f"[MODEL ERROR] {error_message}")
    
    def should_switch_models(self) -> bool:
        """Determine if we should switch to the next model."""
        if not self.attempt_history:
            return False
            
        current_model = self.attempt_history[-1].model_name
        model_attempts = self._count_model_attempts(current_model)
        
        # Find the current model config
        current_config = None
        for config in self.epic_models:
            if config.name == current_model:
                current_config = config
                break
                
        if not current_config:
            return True  # Unknown model, switch
            
        # Switch if we've exceeded max attempts for current model
        return model_attempts >= current_config.max_attempts
    
    def get_attempt_summary(self) -> Dict[str, Any]:
        """Get a summary of all attempts."""
        if not self.attempt_history:
            return {"total_attempts": 0, "models_tried": []}
            
        summary = {
            "total_attempts": len(self.attempt_history),
            "models_tried": [],
            "best_score": max(attempt.quality_score for attempt in self.attempt_history),
            "total_duration": sum(attempt.duration_seconds for attempt in self.attempt_history)
        }
        
        # Group by model
        model_stats = {}
        for attempt in self.attempt_history:
            if attempt.model_name not in model_stats:
                model_stats[attempt.model_name] = {
                    "attempts": 0,
                    "successes": 0,
                    "best_score": 0,
                    "avg_duration": 0,
                    "total_duration": 0
                }
            
            stats = model_stats[attempt.model_name]
            stats["attempts"] += 1
            if attempt.success:
                stats["successes"] += 1
            stats["best_score"] = max(stats["best_score"], attempt.quality_score)
            stats["total_duration"] += attempt.duration_seconds
            
        # Calculate averages and add to summary
        for model_name, stats in model_stats.items():
            stats["avg_duration"] = stats["total_duration"] / stats["attempts"]
            stats["success_rate"] = stats["successes"] / stats["attempts"]
            summary["models_tried"].append({
                "model": model_name,
                **stats
            })
        
        return summary
    
    def reset_attempts(self):
        """Reset attempt history for a new generation cycle."""
        self.attempt_history.clear()
        self.logger.info("[MODEL FALLBACK] Reset attempt history for new generation cycle")
    
    def _count_model_attempts(self, model_name: str) -> int:
        """Count attempts for a specific model."""
        return sum(1 for attempt in self.attempt_history if attempt.model_name == model_name)
    
    def preload_models(self):
        """Preload both models to keep them in memory."""
        self.logger.info("[MODEL PRELOAD] Ensuring both epic generation models are loaded")
        
        import requests
        import json
        
        for model_config in self.epic_models:
            try:
                # Make a small test request to load the model
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model_config.name,
                        "prompt": "Hello",
                        "stream": False,
                        "options": {"num_predict": 1}
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.logger.info(f"[MODEL PRELOAD] {model_config.display_name} loaded successfully")
                else:
                    self.logger.warning(f"[MODEL PRELOAD] Failed to preload {model_config.display_name}: {response.status_code}")
                    
            except Exception as e:
                self.logger.warning(f"[MODEL PRELOAD] Error preloading {model_config.display_name}: {str(e)}")