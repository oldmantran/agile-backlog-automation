#!/usr/bin/env python3
"""
Script to integrate hardware auto-scaling into the supervisor workflow.
This script shows the exact changes needed in supervisor.py
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.hardware_optimizer import HardwareOptimizer
from utils.enhanced_parallel_processor import EnhancedParallelProcessor

def show_integration_example():
    """Show how to integrate hardware scaling into supervisor."""
    
    print("=== Hardware Auto-Scaling Integration Example ===\n")
    
    # 1. Initialize hardware optimizer
    optimizer = HardwareOptimizer()
    hw_info = optimizer.get_hardware_info()
    
    print(f"Detected Hardware:")
    print(f"  CPU Cores: {hw_info['cpu_cores']}")
    print(f"  CPU Threads: {hw_info['cpu_threads']}")
    print(f"  Memory: {hw_info['memory_gb']:.1f} GB")
    print(f"  Performance Tier: {hw_info['tier']}")
    print(f"  Optimal Workers: {hw_info['optimal_workers']}")
    print()
    
    # 2. Show stage-specific optimizations
    stages = ["epic_strategist", "feature_decomposer", "user_story_decomposer", "developer_agent", "qa_lead_agent"]
    
    print("Stage-Specific Optimizations:")
    for stage in stages:
        config = optimizer.get_stage_optimization(stage)
        print(f"\n  {stage}:")
        print(f"    Workers: {config['max_workers']}")
        print(f"    Rate Limit: {config['rate_limit']} req/sec")
        print(f"    Batch Size: {config['batch_size']}")
    
    print("\n=== Code Changes for supervisor.py ===\n")
    
    print("""
1. Add imports at the top:
```python
from utils.hardware_optimizer import HardwareOptimizer
from utils.enhanced_parallel_processor import EnhancedParallelProcessor
```

2. Initialize in __init__ method:
```python
def __init__(self, ...):
    # ... existing code ...
    
    # Initialize hardware optimizer
    self.hardware_optimizer = HardwareOptimizer()
    self.hardware_info = self.hardware_optimizer.get_hardware_info()
    
    # Log hardware detection
    logger.info(f"Hardware detected: {self.hardware_info['tier']} tier")
    logger.info(f"Optimal workers: {self.hardware_info['optimal_workers']}")
```

3. Replace ThreadPoolExecutor in each stage method:

OLD CODE:
```python
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    futures = []
    for item in work_items:
        future = executor.submit(self._process_item, item)
        futures.append(future)
    
    results = []
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
```

NEW CODE:
```python
# Get stage-specific optimization
stage_config = self.hardware_optimizer.get_stage_optimization("epic_strategist")

# Create processor for this stage
processor = EnhancedParallelProcessor(
    max_workers=stage_config['max_workers'],
    rate_limit=stage_config['rate_limit'],
    stage_name="epic_strategist"
)

# Process batch with automatic optimization
results = processor.process_batch(
    items=work_items,
    process_func=self._process_epic,
    batch_size=stage_config['batch_size']
)

# Log performance metrics
metrics = processor.get_metrics()
logger.info(f"Stage metrics: {metrics}")
```

4. Update job metadata with hardware info:
```python
self.update_job_metadata({
    "hardware_tier": self.hardware_info['tier'],
    "hardware_config": {
        "cpu_cores": self.hardware_info['cpu_cores'],
        "memory_gb": self.hardware_info['memory_gb'],
        "optimal_workers": self.hardware_info['optimal_workers']
    },
    "performance_expectations": self.hardware_optimizer.estimate_completion_time(
        work_item_count=total_items
    )
})
```
""")

def test_enhanced_processor():
    """Test the enhanced processor with a simple workload."""
    print("\n=== Testing Enhanced Processor ===\n")
    
    optimizer = HardwareOptimizer()
    config = optimizer.get_stage_optimization("epic_strategist")
    
    # Create processor
    processor = EnhancedParallelProcessor(
        max_workers=config['max_workers'],
        rate_limit=config['rate_limit'],
        stage_name="epic_strategist"
    )
    
    # Test items
    test_items = [f"Epic {i}" for i in range(1, 6)]
    
    def mock_process_epic(epic_name):
        """Mock epic processing function."""
        import time
        import random
        time.sleep(random.uniform(0.1, 0.3))  # Simulate processing
        return f"Processed: {epic_name}"
    
    print(f"Processing {len(test_items)} test items...")
    print(f"Using {config['max_workers']} workers, {config['rate_limit']} req/sec")
    
    # Process batch
    results = processor.process_batch(
        items=test_items,
        process_func=mock_process_epic
    )
    
    print("\nResults:")
    for result in results:
        print(f"  - {result}")
    
    # Show metrics
    metrics = processor.get_metrics()
    print(f"\nMetrics: {metrics}")

if __name__ == "__main__":
    show_integration_example()
    
    print("\n" + "="*50 + "\n")
    
    response = input("Run test of enhanced processor? (y/n): ")
    if response.lower() == 'y':
        test_enhanced_processor()
    
    print("\nIntegration guide complete. See supervisor.py for implementation.")