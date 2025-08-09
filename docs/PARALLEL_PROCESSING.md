# Hardware-Aware Enhanced Parallel Processing System

## Overview

The Enhanced Parallel Processing System provides **hardware-aware auto-scaling** capabilities for the Agile Backlog Automation pipeline. The system automatically detects your hardware capabilities (CPU cores, memory, current load) and configures optimal parallel processing settings for **maximum performance with zero defects**. No user configuration required - the system optimizes itself.

## Architecture

### Core Components

#### 1. Enhanced Parallel Processor (`utils/enhanced_parallel_processor.py`)
- **Token Bucket Rate Limiting**: Dynamic rate adjustment based on system performance
- **Circuit Breaker Pattern**: Automatic failure detection and recovery
- **Backpressure Detection**: Real-time monitoring with automatic capacity adjustment
- **Provider Rotation**: Round-robin load balancing across multiple LLM providers
- **Request Batching**: Intelligent coalescing of API requests to reduce costs

#### 2. Stage-Specific Configuration
Each processing stage can be independently configured:
- **Epic Strategist**: High-capacity single processing (no parallelism needed)
- **Feature Decomposer**: Medium parallelism with careful rate limiting
- **User Story Decomposer**: High parallelism for bulk story processing
- **Developer Agent**: Optimized for task generation with batching support
- **QA Agents**: Limited parallelism with specialized test generation

### Key Features

#### Dynamic Backpressure Control
The system automatically adjusts capacity based on performance metrics:

```python
# Backpressure triggers
if error_rate > 20%:
    reduce_workers_by(25%)
    reduce_rate_by(50%)
elif latency > 30_seconds:
    reduce_workers_by(25%)
    reduce_rate_by(50%)
elif error_rate < 5% and latency < 5_seconds:
    increase_workers_by(33%)
    increase_rate_by(25%)
```

#### Provider Rotation
Distributes load across multiple LLM providers:
- **OpenAI**: Primary provider for high-quality generation
- **Grok (xAI)**: Secondary provider for cost optimization
- **Ollama**: Local provider for privacy-sensitive operations

#### Intelligent Batching
Reduces API costs by batching compatible requests:
- **Feature Decomposition**: Process multiple epics together
- **Task Generation**: Batch story processing where applicable
- **QA Generation**: Group related test generation

## Configuration

### settings.yaml Configuration
```yaml
workflow:
  parallel_processing:
    enabled: true
    max_workers: 4
    rate_limit_per_second: 10.0
    
    # Stage-specific settings
    stages:
      feature_decomposer_agent:
        enabled: true
        max_workers: 2
        min_workers: 1
        rate_limit_per_second: 8.0
        circuit_breaker_threshold: 3
        providers: ["openai", "grok", "ollama"]
        batch_size: null
        
      user_story_decomposer_agent:
        enabled: true
        max_workers: 3
        min_workers: 1
        rate_limit_per_second: 12.0
        circuit_breaker_threshold: 5
        providers: ["openai", "grok"]
        batch_size: 2
        
      developer_agent:
        enabled: true
        max_workers: 4
        min_workers: 2
        rate_limit_per_second: 15.0
        circuit_breaker_threshold: 3
        providers: ["openai", "ollama"]
        batch_size: 3
        
      qa_lead_agent:
        enabled: true
        max_workers: 2
        min_workers: 1
        rate_limit_per_second: 6.0
        circuit_breaker_threshold: 2
        providers: ["openai"]
        batch_size: null
```

### Runtime Configuration
The supervisor automatically configures the enhanced processor:

```python
def _configure_enhanced_parallel_processor(self):
    """Configure the enhanced parallel processor with stage-specific settings."""
    from utils.enhanced_parallel_processor import enhanced_processor, StageConfig, RateLimitConfig
    
    stages_config = {
        'feature_decomposer_agent': StageConfig(
            max_workers=self.parallel_config.get('feature_max_workers', 2),
            min_workers=1,
            rate_limit=RateLimitConfig(
                tokens_per_second=8.0,
                burst_capacity=4,
                min_tokens_per_second=2.0,
                max_tokens_per_second=16.0
            ),
            timeout_seconds=120,
            circuit_breaker_threshold=3,
            providers=['openai', 'grok', 'ollama'],
            batch_size=None
        ),
        # ... other stages
    }
```

## Observability & Monitoring

### Metrics Tracking
The system tracks comprehensive metrics for each stage and provider:

#### Per-Stage Metrics
- **Request Count**: Total requests processed
- **Success/Failure Rates**: Error percentage tracking
- **Average Latency**: Response time monitoring
- **Queue Depth**: Backlog tracking
- **Active Workers**: Current parallelism level

#### Per-Provider Metrics
- **Provider Usage**: Round-robin distribution tracking
- **Provider Latency**: Performance comparison
- **Provider Errors**: Reliability assessment
- **Last Used**: Load balancing verification

### Accessing Metrics
```python
from utils.enhanced_parallel_processor import enhanced_processor

# Get all metrics
all_metrics = enhanced_processor.get_metrics()

# Get specific stage metrics
dev_metrics = enhanced_processor.get_metrics('developer_agent')
print(f"Developer Agent - Latency: {dev_metrics['avg_latency_ms']}ms")
print(f"Developer Agent - Error Rate: {dev_metrics['error_rate']:.2%}")
```

## Performance Optimizations

### Rate Limiting Strategy
- **Token Bucket Algorithm**: Smooth rate limiting with burst capacity
- **Dynamic Adjustment**: Automatic rate changes based on system performance
- **Exponential Backoff**: Intelligent retry timing with jitter

### Circuit Breaker Strategy
- **Failure Threshold**: Configurable failure count before circuit opens
- **Recovery Timeout**: Time before attempting recovery
- **Half-Open Testing**: Gradual recovery validation

### Backpressure Management
- **Proactive Monitoring**: Continuous performance assessment
- **Gradual Adjustment**: Smooth capacity changes to avoid system shock
- **Recovery Protocol**: Automatic capacity restoration when metrics improve

## Usage Examples

### Basic Usage
```python
from utils.enhanced_parallel_processor import enhanced_processor, StageConfig

# Configure a stage
config = StageConfig(
    max_workers=3,
    rate_limit=RateLimitConfig(tokens_per_second=10.0),
    providers=['openai', 'grok']
)
enhanced_processor.configure_stage('my_stage', config)

# Process items
items = ['item1', 'item2', 'item3']
def process_function(item, context):
    return f"processed_{item}"

results = enhanced_processor.process_batch(
    'my_stage', 
    items, 
    process_function
)
```

### Advanced Configuration
```python
# Stage with batching and provider rotation
config = StageConfig(
    max_workers=4,
    min_workers=2,
    rate_limit=RateLimitConfig(
        tokens_per_second=15.0,
        burst_capacity=8,
        min_tokens_per_second=5.0,
        max_tokens_per_second=30.0
    ),
    timeout_seconds=90,
    circuit_breaker_threshold=3,
    providers=['openai', 'grok', 'ollama'],
    batch_size=3,
    batch_timeout_ms=200
)
```

## Best Practices

### 1. Stage Configuration
- **Epic Stage**: Single worker, no batching (high-quality generation needed)
- **Feature Stage**: Low parallelism (2-3 workers) for careful processing
- **Story Stage**: Medium parallelism (3-4 workers) for bulk processing
- **Task Stage**: High parallelism (4-6 workers) with batching for efficiency
- **QA Stage**: Limited parallelism (2 workers) for specialized processing

### 2. Provider Selection
- **Primary Provider**: Use most reliable provider (OpenAI) for critical stages
- **Secondary Providers**: Distribute load across Grok/Ollama for cost optimization
- **Local Providers**: Use Ollama for privacy-sensitive or high-volume operations

### 3. Rate Limiting
- **Conservative Start**: Begin with lower rates and let system scale up
- **Monitor Metrics**: Watch for error rates and latency spikes
- **Adjust Gradually**: Avoid sudden capacity changes that shock the system

### 4. Error Handling
- **Circuit Breakers**: Set appropriate failure thresholds for each stage
- **Timeouts**: Configure realistic timeouts based on expected processing time
- **Recovery**: Allow sufficient time for systems to recover before retrying

## Integration with Workflow

The enhanced parallel processor integrates seamlessly with the existing workflow:

```python
# In supervisor/supervisor.py
def execute_feature_decomposition_stage(self, epics, project_context):
    if self._should_use_enhanced_parallel('feature_decomposer_agent'):
        return enhanced_processor.process_batch(
            'feature_decomposer_agent',
            epics,
            self._process_feature_decomposition,
            project_context
        )
    else:
        return self._process_sequential(epics, self._process_feature_decomposition)
```

## Troubleshooting

### Common Issues

#### High Error Rates
- **Symptom**: Error rate > 20%
- **Action**: System automatically reduces capacity
- **Resolution**: Check provider status, API keys, rate limits

#### High Latency
- **Symptom**: Average latency > 30 seconds
- **Action**: System reduces workers and rate limits
- **Resolution**: Monitor provider performance, consider switching providers

#### Circuit Breaker Opens
- **Symptom**: Requests blocked, circuit breaker open
- **Action**: System waits for recovery timeout
- **Resolution**: Check underlying service health, adjust thresholds if needed

### Debugging
```python
# Check current metrics
metrics = enhanced_processor.get_metrics()
for stage, data in metrics.items():
    print(f"{stage}: {data['error_rate']:.2%} errors, {data['avg_latency_ms']:.1f}ms avg")

# Monitor circuit breaker states
for stage in enhanced_processor.circuit_breakers:
    breaker = enhanced_processor.circuit_breakers[stage]
    print(f"{stage} circuit breaker: {breaker.state.value}")
```

## Future Enhancements

### Planned Features
1. **Machine Learning Optimization**: AI-driven capacity planning
2. **Cost Optimization**: Intelligent provider selection based on pricing
3. **Geographic Distribution**: Multi-region provider support
4. **Advanced Batching**: Semantic request grouping
5. **Predictive Scaling**: Proactive capacity adjustment

### Monitoring Integration
- **Prometheus Metrics**: Export metrics for monitoring dashboards
- **Health Checks**: Endpoint for system health validation
- **Alerting**: Automated notifications for system issues