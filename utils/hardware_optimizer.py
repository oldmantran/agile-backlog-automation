#!/usr/bin/env python3
"""
Hardware-Aware Performance Optimizer

Automatically detects system capabilities and configures optimal parallel processing
settings for maximum performance with zero defects.
"""

import os
import psutil
import platform
from typing import Dict, Any
from dataclasses import dataclass
from utils.safe_logger import get_safe_logger


@dataclass
class HardwareProfile:
    """System hardware profile for optimization."""
    cpu_cores: int
    cpu_threads: int
    memory_gb: float
    platform: str
    cpu_freq_ghz: float
    
    # Calculated optimal settings
    optimal_workers: int
    optimal_rate_limit: float
    optimal_burst_capacity: int
    performance_tier: str  # 'high', 'medium', 'low'


class HardwareOptimizer:
    """Detects hardware capabilities and calculates optimal parallel processing settings."""
    
    def __init__(self):
        self.logger = get_safe_logger(__name__)
        self._profile = None
    
    def get_hardware_profile(self) -> HardwareProfile:
        """Get or calculate hardware profile with optimal settings."""
        if self._profile is None:
            self._profile = self._detect_hardware()
        return self._profile
    
    def _detect_hardware(self) -> HardwareProfile:
        """Detect system hardware and calculate optimal settings."""
        try:
            # CPU Detection
            cpu_cores = psutil.cpu_count(logical=False) or 4  # Physical cores
            cpu_threads = psutil.cpu_count(logical=True) or 8  # Logical threads
            
            # Memory Detection (in GB)
            memory_info = psutil.virtual_memory()
            memory_gb = memory_info.total / (1024**3)
            
            # CPU Frequency
            cpu_freq = psutil.cpu_freq()
            cpu_freq_ghz = (cpu_freq.max if cpu_freq and cpu_freq.max else 2400) / 1000.0
            
            # Platform Detection
            system_platform = f"{platform.system()} {platform.release()}"
            
            # Calculate optimal settings
            optimal_workers = self._calculate_optimal_workers(cpu_cores, cpu_threads, memory_gb)
            optimal_rate_limit = self._calculate_optimal_rate_limit(cpu_cores, cpu_freq_ghz)
            optimal_burst_capacity = optimal_workers * 3  # 3x burst capacity
            performance_tier = self._classify_performance_tier(cpu_cores, memory_gb, cpu_freq_ghz)
            
            profile = HardwareProfile(
                cpu_cores=cpu_cores,
                cpu_threads=cpu_threads,
                memory_gb=memory_gb,
                platform=system_platform,
                cpu_freq_ghz=cpu_freq_ghz,
                optimal_workers=optimal_workers,
                optimal_rate_limit=optimal_rate_limit,
                optimal_burst_capacity=optimal_burst_capacity,
                performance_tier=performance_tier
            )
            
            self.logger.info(f"Hardware Profile Detected:")
            self.logger.info(f"  CPU: {cpu_cores} cores, {cpu_threads} threads @ {cpu_freq_ghz:.1f}GHz")
            self.logger.info(f"  Memory: {memory_gb:.1f}GB")
            self.logger.info(f"  Platform: {system_platform}")
            self.logger.info(f"  Performance Tier: {performance_tier.upper()}")
            self.logger.info(f"  Optimal Workers: {optimal_workers}")
            self.logger.info(f"  Optimal Rate Limit: {optimal_rate_limit}/sec")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Hardware detection failed: {e}")
            # Return conservative fallback
            return HardwareProfile(
                cpu_cores=4,
                cpu_threads=8,
                memory_gb=8.0,
                platform="Unknown",
                cpu_freq_ghz=2.4,
                optimal_workers=4,
                optimal_rate_limit=10.0,
                optimal_burst_capacity=12,
                performance_tier='medium'
            )
    
    def _calculate_optimal_workers(self, cpu_cores: int, cpu_threads: int, memory_gb: float) -> int:
        """Calculate optimal worker count based on hardware."""
        # Base calculation: Use most of available threads, but not all
        # Leave some headroom for system processes and the main application
        base_workers = max(2, min(cpu_threads - 2, cpu_cores * 2))
        
        # Memory constraint: Each worker needs ~1GB for LLM processing
        memory_constraint = max(2, int(memory_gb * 0.6))  # Use 60% of available memory
        
        # Take the minimum to avoid oversubscription
        optimal = min(base_workers, memory_constraint)
        
        # Cap at reasonable maximum (even on high-end systems)
        optimal = min(optimal, 16)
        
        # Ensure minimum of 2 for parallel processing benefits
        optimal = max(2, optimal)
        
        self.logger.info(f"Worker calculation: {cpu_threads} threads -> {base_workers} base, {memory_gb:.1f}GB -> {memory_constraint} memory limit -> {optimal} optimal")
        
        return optimal
    
    def _calculate_optimal_rate_limit(self, cpu_cores: int, cpu_freq_ghz: float) -> float:
        """Calculate optimal rate limit based on CPU performance."""
        # Base rate scales with CPU cores and frequency
        base_rate = cpu_cores * cpu_freq_ghz * 2.0  # Aggressive scaling
        
        # Reasonable bounds
        optimal_rate = max(5.0, min(base_rate, 50.0))
        
        self.logger.info(f"Rate limit calculation: {cpu_cores} cores @ {cpu_freq_ghz:.1f}GHz -> {optimal_rate:.1f}/sec")
        
        return optimal_rate
    
    def _classify_performance_tier(self, cpu_cores: int, memory_gb: float, cpu_freq_ghz: float) -> str:
        """Classify system performance tier for logging/monitoring."""
        score = 0
        
        # CPU scoring
        if cpu_cores >= 16: score += 3
        elif cpu_cores >= 8: score += 2
        elif cpu_cores >= 4: score += 1
        
        # Memory scoring
        if memory_gb >= 32: score += 3
        elif memory_gb >= 16: score += 2
        elif memory_gb >= 8: score += 1
        
        # Frequency scoring
        if cpu_freq_ghz >= 3.5: score += 3
        elif cpu_freq_ghz >= 2.5: score += 2
        elif cpu_freq_ghz >= 2.0: score += 1
        
        if score >= 7: return 'high'
        elif score >= 4: return 'medium'
        else: return 'low'
    
    def get_stage_specific_config(self, stage_name: str) -> Dict[str, Any]:
        """Get optimized configuration for a specific processing stage."""
        profile = self.get_hardware_profile()
        
        # Stage-specific multipliers based on computational requirements
        stage_multipliers = {
            'epic_strategist': {
                'workers': 0.25,  # Single epic, high quality needed
                'rate': 0.5,      # Conservative rate for quality
                'min_workers': 1,
                'providers': ['openai', 'grok'],  # Premium providers for strategy
            },
            'feature_decomposer_agent': {
                'workers': 0.5,   # Medium parallelism
                'rate': 0.7,      # Moderate rate
                'min_workers': 1,
                'providers': ['openai', 'grok', 'ollama'],
            },
            'user_story_decomposer_agent': {
                'workers': 0.8,   # High parallelism for bulk processing
                'rate': 1.0,      # Full rate for volume
                'min_workers': 2,
                'providers': ['openai', 'ollama'],  # Cost-effective for volume
            },
            'developer_agent': {
                'workers': 1.0,   # Maximum parallelism (biggest bottleneck)
                'rate': 1.2,      # Aggressive rate for tasks
                'min_workers': 2,
                'providers': ['openai', 'ollama'],  # Task generation can use local
                'batch_size': 3,  # Enable batching for efficiency
            },
            'qa_lead_agent': {
                'workers': 0.4,   # Limited parallelism for test management
                'rate': 0.6,      # Conservative rate for QA
                'min_workers': 1,
                'providers': ['openai'],  # Premium provider for testing
            }
        }
        
        multipliers = stage_multipliers.get(stage_name, {
            'workers': 0.5, 'rate': 0.8, 'min_workers': 1, 'providers': ['openai']
        })
        
        return {
            'max_workers': max(multipliers['min_workers'], int(profile.optimal_workers * multipliers['workers'])),
            'min_workers': multipliers['min_workers'],
            'rate_limit_per_second': profile.optimal_rate_limit * multipliers['rate'],
            'burst_capacity': profile.optimal_burst_capacity,
            'providers': multipliers['providers'],
            'batch_size': multipliers.get('batch_size'),
            'timeout_seconds': 300,  # 5 minutes max per operation
            'circuit_breaker_threshold': 3 if profile.performance_tier == 'high' else 5
        }
    
    def get_current_load(self) -> Dict[str, float]:
        """Get current system load metrics for dynamic adjustment."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Simple load classification
            load_level = 'low'
            if cpu_percent > 80 or memory_percent > 85:
                load_level = 'high'
            elif cpu_percent > 60 or memory_percent > 70:
                load_level = 'medium'
                
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'load_level': load_level,
                'can_scale_up': cpu_percent < 70 and memory_percent < 60,
                'should_scale_down': cpu_percent > 85 or memory_percent > 90
            }
            
        except Exception as e:
            self.logger.warning(f"Could not get current load: {e}")
            return {
                'cpu_percent': 50.0,
                'memory_percent': 50.0, 
                'load_level': 'medium',
                'can_scale_up': True,
                'should_scale_down': False
            }


# Global instance for use across the application
hardware_optimizer = HardwareOptimizer()