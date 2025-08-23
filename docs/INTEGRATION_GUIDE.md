# Integration Guide for Complete Features

## 1. Hardware Auto-Scaling Integration

### Current State
- ✅ `utils/hardware_optimizer.py` - Complete hardware detection and optimization
- ✅ `utils/enhanced_parallel_processor.py` - Enterprise parallel processing with backpressure
- ✅ `config/settings.yaml` - Configuration ready with auto-scaling enabled
- ❌ `supervisor/supervisor.py` - Still using basic ThreadPoolExecutor

### Integration Steps

1. **Import the enhanced processor in supervisor.py**:
```python
from utils.enhanced_parallel_processor import EnhancedParallelProcessor
from utils.hardware_optimizer import HardwareOptimizer
```

2. **Replace ThreadPoolExecutor initialization**:
```python
# OLD CODE (around line 200-210)
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

# NEW CODE
hardware_optimizer = HardwareOptimizer()
stage_config = hardware_optimizer.get_stage_optimization("epic_strategist")  # Per stage
processor = EnhancedParallelProcessor(
    max_workers=stage_config["max_workers"],
    rate_limit=stage_config["rate_limit"],
    stage_name="epic_strategist"
)
results = processor.process_batch(work_items, self._process_epic)
```

3. **Update each stage execution method**:
- `_execute_epic_generation`
- `_execute_feature_decomposition`  
- `_execute_user_story_decomposition`
- `_execute_task_generation`
- `_execute_qa_workflow`

4. **Add hardware info to job metadata**:
```python
hardware_info = hardware_optimizer.get_hardware_info()
self.update_job_metadata({
    "hardware_tier": hardware_info["tier"],
    "optimal_workers": hardware_info["optimal_workers"],
    "system_info": hardware_info
})
```

## 2. Outbox Pattern Integration

### Current State
- ✅ `models/work_item_staging.py` - Complete staging model
- ✅ `integrators/outbox_uploader.py` - Reliable upload with retry
- ✅ `integrators/azure_devops_api.py` - Full ADO integration
- ✅ `tools/retry_failed_uploads.py` - Recovery utilities
- ❌ Direct upload still used in supervisor

### Integration Steps

1. **Import staging components in supervisor.py**:
```python
from models.work_item_staging import WorkItemStaging
from integrators.outbox_uploader import OutboxUploader
```

2. **Replace direct Azure DevOps upload**:
```python
# OLD CODE (in _upload_to_azure_devops method)
ado_api = AzureDevOpsAPI(...)
for work_item in work_items:
    ado_api.create_work_item(...)

# NEW CODE
# Stage all work items first
staging = WorkItemStaging(self.db_path)
staging_ids = []
for work_item in work_items:
    staging_id = staging.add_work_item(
        job_id=self.job_id,
        work_item_type=work_item["type"],
        title=work_item["title"],
        parent_id=work_item.get("parent_staging_id"),
        generated_data=work_item,
        hierarchy_level=work_item["level"]
    )
    staging_ids.append(staging_id)

# Upload using outbox pattern
uploader = OutboxUploader(staging, ado_api)
upload_results = uploader.upload_all(self.job_id)

# Update job with staging summary
self.update_job_metadata({
    "staging_summary": staging.get_job_summary(self.job_id),
    "upload_results": upload_results
})
```

3. **Add recovery endpoint to API**:
```python
@app.post("/api/jobs/{job_id}/retry-uploads")
async def retry_failed_uploads(job_id: str):
    """Retry failed Azure DevOps uploads for a job."""
    staging = WorkItemStaging()
    job_data = db.get_job(job_id)
    
    # Reconstruct Azure DevOps config
    ado_config = job_data["azure_config"]
    ado_api = AzureDevOpsAPI(**ado_config)
    
    # Retry uploads
    uploader = OutboxUploader(staging, ado_api)
    results = uploader.retry_failed(job_id)
    
    return {"status": "success", "results": results}
```

## 3. SSE Backend Implementation

### Current State
- ✅ Frontend `useHybridProgress` hook complete
- ✅ Polling fallback implemented
- ❌ SSE endpoints missing in backend

### Integration Steps

1. **Add SSE endpoint to unified_api_server.py**:
```python
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.get("/api/progress/stream/{job_id}")
async def stream_progress(job_id: str):
    """Stream job progress via Server-Sent Events."""
    
    async def event_generator():
        last_etag = None
        
        while True:
            try:
                # Get current job progress
                job = db.get_job(job_id)
                if not job:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                    break
                
                # Generate ETag from progress data
                etag = f"{job['progress']}-{job['updated_at']}"
                
                # Only send if data changed
                if etag != last_etag:
                    progress_data = {
                        'type': 'progress',
                        'jobId': job_id,
                        'progress': job['progress'],
                        'status': job['status'],
                        'currentAction': job.get('current_action'),
                        'currentAgent': job.get('current_agent'),
                        'timestamp': job.get('updated_at'),
                        'etag': etag,
                        'source': 'database'
                    }
                    
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    last_etag = etag
                
                # Send final message and close on completion
                if job['status'] in ['completed', 'failed']:
                    final_data = {
                        'type': 'final',
                        'jobId': job_id,
                        'status': job['status'],
                        'progress': job['progress']
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                    break
                
                # Wait before next check (adaptive based on progress rate)
                await asyncio.sleep(1 if job['progress'] < 90 else 0.5)
                
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'message': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

2. **Add progress polling endpoint with ETag support**:
```python
@app.get("/api/jobs/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    request: Request,
    response: Response
):
    """Get job progress with ETag support for efficient polling."""
    
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate ETag
    etag = f'"{job["progress"]}-{job["updated_at"]}"'
    
    # Check If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        response.status_code = 304  # Not Modified
        return None
    
    # Set ETag header
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"
    
    return {
        "jobId": job_id,
        "progress": job["progress"],
        "status": job["status"],
        "currentAction": job.get("current_action"),
        "currentAgent": job.get("current_agent"),
        "lastUpdated": job.get("updated_at"),
        "etag": etag,
        "source": "database"
    }
```

3. **Update supervisor to emit progress more frequently**:
```python
def update_progress(self, progress: int, action: str, agent: str = None):
    """Update job progress in database."""
    self.current_progress = progress
    self.current_action = action
    self.current_agent = agent
    
    # Update database immediately for SSE
    self.db.update_job(
        self.job_id,
        progress=progress,
        current_action=action,
        current_agent=agent,
        updated_at=datetime.utcnow().isoformat()
    )
    
    # Log for debugging
    logger.info(f"Progress: {progress}% - {action}")
```

## 4. Testing the Integration

### Test Hardware Auto-Scaling
```python
# Create test script: tools/test_hardware_integration.py
from utils.hardware_optimizer import HardwareOptimizer
from utils.enhanced_parallel_processor import EnhancedParallelProcessor

optimizer = HardwareOptimizer()
print("Hardware Info:", optimizer.get_hardware_info())
print("Epic Stage Config:", optimizer.get_stage_optimization("epic_strategist"))

# Test with small workload
processor = EnhancedParallelProcessor(max_workers=4, rate_limit=10)
results = processor.process_batch(
    items=["test1", "test2", "test3"],
    process_func=lambda x: f"processed_{x}"
)
print("Results:", results)
```

### Test Outbox Pattern
```python
# Create test script: tools/test_outbox_integration.py
from models.work_item_staging import WorkItemStaging

staging = WorkItemStaging()
staging_id = staging.add_work_item(
    job_id="test-job-123",
    work_item_type="Epic",
    title="Test Epic",
    generated_data={"description": "Test"},
    hierarchy_level=0
)
print("Staged work item:", staging_id)
print("Job summary:", staging.get_job_summary("test-job-123"))
```

### Test SSE Progress
```bash
# Test SSE endpoint with curl
curl -N -H "Accept: text/event-stream" \
  http://localhost:8000/api/progress/stream/YOUR_JOB_ID

# Test polling with ETag
curl -i -H "If-None-Match: \"75-2024-01-15T10:30:00\"" \
  http://localhost:8000/api/jobs/YOUR_JOB_ID/progress
```

## Implementation Order

1. **Phase 1**: Outbox Pattern (Highest Value - Prevents Data Loss)
   - Protects 2+ hour generation investment
   - Enables retry without regeneration
   - Minimal code changes required

2. **Phase 2**: SSE Progress Tracking (Best User Experience)
   - Real-time progress updates
   - Reduces server load vs constant polling
   - Frontend already ready

3. **Phase 3**: Hardware Auto-Scaling (Performance Boost)
   - Automatic performance optimization
   - Requires more testing across hardware
   - Biggest performance impact

## Configuration Changes

### Enable Outbox Pattern
```yaml
# config/settings.yaml
azure_devops:
  use_outbox_pattern: true
  staging_batch_size: 50
  upload_retry_attempts: 3
  upload_timeout_seconds: 30
```

### Enable Hardware Optimization
```yaml
# config/settings.yaml
workflow:
  parallel_processing:
    enabled: true
    use_hardware_optimization: true
    # Remove hardcoded values - let hardware optimizer decide
    # max_workers: null
    # rate_limit_per_second: null
```

## Monitoring

Add logging to track the integration:

```python
# In supervisor.py
logger.info(f"Using hardware optimization: {hardware_info}")
logger.info(f"Staging {len(work_items)} items before upload")
logger.info(f"SSE connection established for job {job_id}")
```

## Rollback Plan

Each feature can be toggled via configuration:

```python
# In supervisor.py
if self.config.get("use_hardware_optimization", False):
    # Use enhanced processor
else:
    # Use legacy ThreadPoolExecutor

if self.config.get("use_outbox_pattern", False):
    # Use staging
else:
    # Use direct upload

if self.config.get("enable_sse", False):
    # SSE endpoints active
else:
    # Polling only
```