#!/usr/bin/env python3
"""
Enhanced Parallel Processing Module

Implements enterprise-grade parallel processing with:
- Rate limiting with token buckets and exponential backoff
- Per-stage concurrency caps
- Backpressure and adaptivity
- Circuit breakers and graceful error handling
- Provider rotation and load balancing
- Comprehensive observability
"""

import asyncio
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union
from collections import deque, defaultdict
import queue
import random
from contextlib import contextmanager
import functools

from utils.safe_logger import get_safe_logger


class CircuitBreakerState(Enum):
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RateLimitConfig:
    """Rate limiting configuration using token bucket algorithm."""
    tokens_per_second: float = 10.0
    burst_capacity: int = 20
    provider: Optional[str] = None
    min_tokens_per_second: float = 1.0  # Minimum rate for backpressure
    max_tokens_per_second: float = 20.0  # Maximum rate for recovery


@dataclass
class BackpressureMetrics:
    """Metrics for backpressure detection."""
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    queue_depth: int = 0
    active_requests: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StageConfig:
    """Configuration for a specific processing stage."""
    max_workers: int = 2
    min_workers: int = 1  # Minimum workers during backpressure
    timeout_seconds: int = 60
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    enabled: bool = True
    circuit_breaker_threshold: int = 5  # Failures before opening circuit
    circuit_breaker_timeout: int = 30   # Seconds before trying half-open
    providers: List[str] = field(default_factory=lambda: ['default'])  # Provider rotation list
    batch_size: Optional[int] = None  # Optional batching for requests
    batch_timeout_ms: int = 100  # Wait time to collect batch


class TokenBucket:
    """Thread-safe token bucket for rate limiting with dynamic rate adjustment."""
    
    def __init__(self, rate: float, capacity: int, min_rate: float = 1.0, max_rate: float = 20.0):
        self.rate = rate
        self.base_rate = rate  # Original rate for reference
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()
        
    def adjust_rate(self, factor: float):
        """Adjust token generation rate by factor (0.5 = half speed, 2.0 = double speed)."""
        with self._lock:
            new_rate = self.base_rate * factor
            self.rate = max(self.min_rate, min(self.max_rate, new_rate))
            return self.rate
        
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens. Returns True if successful."""
        with self._lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_tokens(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """Wait for tokens to become available."""
        start_time = time.time()
        backoff = 0.1
        
        while time.time() - start_time < timeout:
            if self.consume(tokens):
                return True
            
            time.sleep(backoff)
            backoff = min(2.0, backoff * 1.5)  # Exponential backoff with jitter
            backoff += random.uniform(0, 0.1)  # Add jitter
            
        return False


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()
        self.logger = get_safe_logger(__name__)
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if (time.time() - self.last_failure_time) > self.timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise Exception("Circuit breaker is OPEN - request blocked")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit breaker if it was half-open
            with self._lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.logger.info("Circuit breaker reset to CLOSED")
            
            return result
            
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    self.logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
                
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self.state = CircuitBreakerState.OPEN
                    self.logger.warning("Circuit breaker returned to OPEN from HALF_OPEN")
            
            raise e


class EnhancedParallelProcessor:
    """Enhanced parallel processor with enterprise-grade features."""
    
    def __init__(self):
        self.logger = get_safe_logger(__name__)
        self.stage_configs: Dict[str, StageConfig] = {}
        self.rate_limiters: Dict[str, TokenBucket] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.metrics: Dict[str, BackpressureMetrics] = {}
        self.executors: Dict[str, ThreadPoolExecutor] = {}
        self._shutdown_event = threading.Event()
        
        # Observability metrics
        self.request_counts = defaultdict(int)
        self.latency_history = defaultdict(lambda: deque(maxlen=100))
        self.error_counts = defaultdict(int)
        
        # Provider rotation
        self.provider_queues: Dict[str, queue.Queue] = {}
        self.provider_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'avg_latency_ms': 0.0,
            'last_used': None
        })
        
        # Batch processing
        self.batch_queues: Dict[str, queue.Queue] = {}
        self.batch_threads: Dict[str, threading.Thread] = {}
        
        # Dynamic backpressure
        self.backpressure_controllers: Dict[str, Dict[str, Any]] = {}
        self._start_backpressure_monitor()
        
    def configure_stage(self, stage_name: str, config: StageConfig):
        """Configure a processing stage."""
        self.stage_configs[stage_name] = config
        
        # Initialize rate limiter with dynamic adjustment
        rate_config = config.rate_limit
        self.rate_limiters[stage_name] = TokenBucket(
            rate=rate_config.tokens_per_second,
            capacity=rate_config.burst_capacity,
            min_rate=rate_config.min_tokens_per_second,
            max_rate=rate_config.max_tokens_per_second
        )
        
        # Initialize circuit breaker
        self.circuit_breakers[stage_name] = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout
        )
        
        # Initialize executor
        self.executors[stage_name] = ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix=f"enhanced-{stage_name}"
        )
        
        # Initialize metrics
        self.metrics[stage_name] = BackpressureMetrics()
        
        # Initialize provider rotation
        if config.providers:
            self.provider_queues[stage_name] = queue.Queue()
            for provider in config.providers:
                self.provider_queues[stage_name].put(provider)
        
        # Initialize batch processing if enabled
        if config.batch_size and config.batch_size > 1:
            self._initialize_batch_processor(stage_name, config)
        
        # Initialize backpressure controller
        self.backpressure_controllers[stage_name] = {
            'current_workers': config.max_workers,
            'adjusting': False,
            'last_adjustment': time.time()
        }
        
        self.logger.info(f"Configured stage '{stage_name}' with {config.max_workers} workers")
    
    def process_batch(self, 
                     stage_name: str,
                     items: List[Any],
                     process_func: Callable,
                     context: Optional[Dict] = None,
                     **kwargs) -> List[Any]:
        """Process a batch of items with enhanced parallel processing."""
        
        if stage_name not in self.stage_configs:
            raise ValueError(f"Stage '{stage_name}' not configured")
        
        config = self.stage_configs[stage_name]
        
        if not config.enabled or len(items) <= 1:
            self.logger.info(f"Processing {len(items)} items sequentially for stage '{stage_name}'")
            return self._process_sequential(items, process_func, context, **kwargs)
        
        # Check if batch processing is enabled and beneficial
        if config.batch_size and config.batch_size > 1 and len(items) >= config.batch_size:
            return self._process_batch_optimized(stage_name, items, process_func, context, **kwargs)
        
        return self._process_parallel(stage_name, items, process_func, context, **kwargs)
    
    def _process_sequential(self, items: List[Any], process_func: Callable, context: Optional[Dict], **kwargs) -> List[Any]:
        """Process items sequentially."""
        results = []
        for item in items:
            try:
                result = process_func(item, context, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Sequential processing failed: {e}")
                results.append(None)
        return results
    
    def _process_batch_optimized(self, stage_name: str, items: List[Any], process_func: Callable, 
                                context: Optional[Dict], **kwargs) -> List[Any]:
        """Process items in optimized batches to reduce API calls."""
        config = self.stage_configs[stage_name]
        batch_size = config.batch_size
        
        self.logger.info(f"Processing {len(items)} items in batches of {batch_size} for stage '{stage_name}'")
        
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch as a single unit if the process function supports it
            try:
                # Check if process_func supports batch processing
                if hasattr(process_func, 'supports_batch') and process_func.supports_batch:
                    batch_result = process_func(batch, context, is_batch=True, **kwargs)
                    results.extend(batch_result)
                else:
                    # Fall back to parallel processing for this batch
                    batch_results = self._process_parallel(stage_name, batch, process_func, context, **kwargs)
                    results.extend(batch_results)
            except Exception as e:
                self.logger.error(f"Batch processing failed for items {i}-{i+len(batch)}: {e}")
                results.extend([None] * len(batch))
        
        return results
    
    def _process_parallel(self, 
                         stage_name: str, 
                         items: List[Any], 
                         process_func: Callable, 
                         context: Optional[Dict], 
                         **kwargs) -> List[Any]:
        """Process items in parallel with enhanced features."""
        
        config = self.stage_configs[stage_name]
        executor = self.executors[stage_name]
        rate_limiter = self.rate_limiters[stage_name]
        circuit_breaker = self.circuit_breakers[stage_name]
        
        self.logger.info(f"Processing {len(items)} items in parallel for stage '{stage_name}' with {config.max_workers} workers")
        
        # Track batch metrics
        start_time = time.time()
        successful_items = 0
        failed_items = 0
        
        # Submit tasks with rate limiting
        future_to_item = {}
        results = [None] * len(items)
        
        for i, item in enumerate(items):
            # Wait for rate limit token
            if not rate_limiter.wait_for_tokens(1, timeout=config.timeout_seconds):
                self.logger.warning(f"Rate limit timeout for item {i} in stage '{stage_name}'")
                failed_items += 1
                continue
            
            # Submit task with circuit breaker and provider rotation
            try:
                # Use dynamic worker count from backpressure controller
                current_workers = self.backpressure_controllers[stage_name]['current_workers']
                if len(future_to_item) >= current_workers:
                    # Wait for some tasks to complete before submitting more
                    time.sleep(0.1)
                
                def protected_process():
                    # Use enhanced processing with provider rotation
                    return circuit_breaker.call(
                        self._enhanced_process_with_provider,
                        stage_name, process_func, item, context, **kwargs
                    )
                
                future = executor.submit(protected_process)
                future_to_item[future] = i
                
            except Exception as e:
                self.logger.error(f"Failed to submit task for item {i}: {e}")
                failed_items += 1
        
        # Collect results with timeout handling
        for future in as_completed(future_to_item, timeout=config.timeout_seconds):
            item_index = future_to_item[future]
            
            try:
                result = future.result(timeout=config.timeout_seconds)
                results[item_index] = result
                successful_items += 1
                
                # Record success metrics
                self._record_success_metric(stage_name, start_time)
                
            except Exception as e:
                self.logger.error(f"Task failed for item {item_index} in stage '{stage_name}': {e}")
                failed_items += 1
                
                # Record failure metrics
                self._record_failure_metric(stage_name)
        
        # Update metrics and check for backpressure
        self._update_metrics(stage_name, successful_items, failed_items, time.time() - start_time)
        self._check_backpressure(stage_name)
        
        self.logger.info(f"Stage '{stage_name}' completed: {successful_items} successful, {failed_items} failed")
        
        return results
    
    def _record_success_metric(self, stage_name: str, start_time: float):
        """Record successful operation metrics."""
        latency_ms = (time.time() - start_time) * 1000
        self.latency_history[stage_name].append(latency_ms)
        self.request_counts[stage_name] += 1
    
    def _record_failure_metric(self, stage_name: str):
        """Record failed operation metrics."""
        self.error_counts[stage_name] += 1
        self.request_counts[stage_name] += 1
    
    def _update_metrics(self, stage_name: str, successful: int, failed: int, duration: float):
        """Update backpressure metrics for a stage."""
        metrics = self.metrics[stage_name]
        
        # Calculate average latency
        if self.latency_history[stage_name]:
            metrics.avg_latency_ms = sum(self.latency_history[stage_name]) / len(self.latency_history[stage_name])
        
        # Calculate error rate
        total_requests = self.request_counts[stage_name]
        if total_requests > 0:
            metrics.error_rate = self.error_counts[stage_name] / total_requests
        
        # Update other metrics
        metrics.timestamp = datetime.now()
        
        self.logger.info(f"Stage '{stage_name}' metrics - Latency: {metrics.avg_latency_ms:.1f}ms, Error rate: {metrics.error_rate:.2%}")
    
    def _check_backpressure(self, stage_name: str):
        """Check for backpressure conditions and dynamically adapt."""
        metrics = self.metrics[stage_name]
        config = self.stage_configs[stage_name]
        controller = self.backpressure_controllers[stage_name]
        
        # Skip if recently adjusted
        if time.time() - controller['last_adjustment'] < 10:  # 10 second cooldown
            return
        
        # Dynamic adjustment based on metrics
        should_reduce = False
        should_increase = False
        
        # Check for high error rate
        if metrics.error_rate > 0.2:  # 20% error rate
            should_reduce = True
            self.logger.warning(f"High error rate ({metrics.error_rate:.2%}) detected for stage '{stage_name}'")
        
        # Check for high latency
        elif metrics.avg_latency_ms > 30000:  # 30 seconds
            should_reduce = True
            self.logger.warning(f"High latency ({metrics.avg_latency_ms:.1f}ms) detected for stage '{stage_name}'")
        
        # Check if we can increase capacity (low error rate and reasonable latency)
        elif metrics.error_rate < 0.05 and metrics.avg_latency_ms < 5000:
            should_increase = True
        
        # Apply dynamic adjustments
        if should_reduce and controller['current_workers'] > config.min_workers:
            self._reduce_capacity(stage_name)
        elif should_increase and controller['current_workers'] < config.max_workers:
            self._increase_capacity(stage_name)
    
    def get_metrics(self, stage_name: Optional[str] = None) -> Dict[str, Any]:
        """Get observability metrics for a stage or all stages."""
        if stage_name:
            if stage_name not in self.metrics:
                return {}
            
            metrics = self.metrics[stage_name]
            return {
                'avg_latency_ms': metrics.avg_latency_ms,
                'error_rate': metrics.error_rate,
                'total_requests': self.request_counts[stage_name],
                'total_errors': self.error_counts[stage_name],
                'circuit_breaker_state': self.circuit_breakers[stage_name].state.value,
                'active_workers': self.stage_configs[stage_name].max_workers,
                'last_updated': metrics.timestamp.isoformat()
            }
        else:
            return {stage: self.get_metrics(stage) for stage in self.stage_configs.keys()}
    
    def _start_backpressure_monitor(self):
        """Start background thread for monitoring backpressure."""
        def monitor():
            while not self._shutdown_event.is_set():
                for stage_name in self.stage_configs.keys():
                    if self.metrics.get(stage_name):
                        self._check_backpressure(stage_name)
                time.sleep(5)  # Check every 5 seconds
        
        monitor_thread = threading.Thread(target=monitor, name="backpressure-monitor", daemon=True)
        monitor_thread.start()
    
    def _reduce_capacity(self, stage_name: str):
        """Reduce capacity for a stage due to backpressure."""
        controller = self.backpressure_controllers[stage_name]
        rate_limiter = self.rate_limiters[stage_name]
        
        # Reduce workers by 25%
        new_workers = max(1, int(controller['current_workers'] * 0.75))
        controller['current_workers'] = new_workers
        controller['last_adjustment'] = time.time()
        
        # Reduce rate limit by 50%
        new_rate = rate_limiter.adjust_rate(0.5)
        
        self.logger.info(f"Reduced capacity for stage '{stage_name}': workers={new_workers}, rate={new_rate:.1f}/s")
    
    def _increase_capacity(self, stage_name: str):
        """Increase capacity for a stage when metrics improve."""
        controller = self.backpressure_controllers[stage_name]
        rate_limiter = self.rate_limiters[stage_name]
        config = self.stage_configs[stage_name]
        
        # Increase workers by 33%
        new_workers = min(config.max_workers, int(controller['current_workers'] * 1.33))
        controller['current_workers'] = new_workers
        controller['last_adjustment'] = time.time()
        
        # Increase rate limit by 25%
        new_rate = rate_limiter.adjust_rate(1.25)
        
        self.logger.info(f"Increased capacity for stage '{stage_name}': workers={new_workers}, rate={new_rate:.1f}/s")
    
    def _get_next_provider(self, stage_name: str) -> str:
        """Get next provider in rotation for load balancing."""
        if stage_name not in self.provider_queues:
            return 'default'
        
        try:
            # Get provider from queue
            provider = self.provider_queues[stage_name].get_nowait()
            # Put it back at the end for rotation
            self.provider_queues[stage_name].put(provider)
            return provider
        except queue.Empty:
            return 'default'
    
    def _initialize_batch_processor(self, stage_name: str, config: StageConfig):
        """Initialize batch processing for a stage."""
        self.batch_queues[stage_name] = queue.Queue()
        
        def batch_processor():
            batch = []
            last_process = time.time()
            
            while not self._shutdown_event.is_set():
                try:
                    # Wait for items with timeout
                    timeout = config.batch_timeout_ms / 1000.0
                    item = self.batch_queues[stage_name].get(timeout=timeout)
                    batch.append(item)
                    
                    # Process batch if full or timeout reached
                    if len(batch) >= config.batch_size or (time.time() - last_process) > timeout:
                        if batch:
                            self._process_batch_items(stage_name, batch)
                            batch = []
                            last_process = time.time()
                            
                except queue.Empty:
                    # Process any remaining items
                    if batch:
                        self._process_batch_items(stage_name, batch)
                        batch = []
                        last_process = time.time()
        
        thread = threading.Thread(target=batch_processor, name=f"batch-{stage_name}", daemon=True)
        thread.start()
        self.batch_threads[stage_name] = thread
    
    def _process_batch_items(self, stage_name: str, batch: List[Any]):
        """Process a batch of items together."""
        self.logger.info(f"Processing batch of {len(batch)} items for stage '{stage_name}'")
        # This would be implemented by the specific agent to handle batched requests
        # For now, we'll process them individually
        for item in batch:
            # Process each item (this would be optimized in real implementation)
            pass
    
    def _enhanced_process_with_provider(self, stage_name: str, process_func: Callable, 
                                       item: Any, context: Optional[Dict], **kwargs):
        """Process item with provider rotation and enhanced error handling."""
        provider = self._get_next_provider(stage_name)
        
        # Add provider to context
        if context is None:
            context = {}
        enhanced_context = {**context, 'provider': provider}
        
        start_time = time.time()
        try:
            result = process_func(item, enhanced_context, **kwargs)
            
            # Update provider metrics
            provider_key = f"{stage_name}:{provider}"
            self.provider_metrics[provider_key]['requests'] += 1
            latency = (time.time() - start_time) * 1000
            
            # Update rolling average latency
            prev_avg = self.provider_metrics[provider_key]['avg_latency_ms']
            count = self.provider_metrics[provider_key]['requests']
            self.provider_metrics[provider_key]['avg_latency_ms'] = (
                (prev_avg * (count - 1) + latency) / count
            )
            self.provider_metrics[provider_key]['last_used'] = time.time()
            
            return result
            
        except Exception as e:
            # Update provider error metrics
            provider_key = f"{stage_name}:{provider}"
            self.provider_metrics[provider_key]['errors'] += 1
            raise e
    
    def shutdown(self):
        """Gracefully shutdown all executors."""
        self.logger.info("Shutting down enhanced parallel processor...")
        self._shutdown_event.set()
        
        for stage_name, executor in self.executors.items():
            self.logger.info(f"Shutting down executor for stage '{stage_name}'")
            executor.shutdown(wait=True)
        
        self.logger.info("Enhanced parallel processor shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global instance for use across the application
enhanced_processor = EnhancedParallelProcessor()