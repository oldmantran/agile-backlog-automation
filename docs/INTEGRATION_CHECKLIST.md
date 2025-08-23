# Integration Checklist

## Quick Summary

All three features are **fully implemented** but need to be connected:

1. **Hardware Auto-Scaling**: Replace ThreadPoolExecutor with EnhancedParallelProcessor
2. **Outbox Pattern**: Replace direct upload with staging + OutboxUploader  
3. **SSE Progress**: Add streaming endpoints to unified_api_server.py

## Priority Order (Recommended)

### 1. Outbox Pattern (HIGHEST VALUE - Do First)
**Why**: Prevents data loss from your 2+ hour generation work

- [ ] Import WorkItemStaging and OutboxUploader in supervisor.py
- [ ] Replace _upload_to_azure_devops method with staging version
- [ ] Add /api/jobs/{job_id}/retry-uploads endpoint
- [ ] Test with: `python tools/integrate_outbox_pattern.py`
- [ ] Add retry button to UI (optional)

**Time**: ~1-2 hours

### 2. SSE Progress Tracking (BEST UX - Do Second)  
**Why**: Real-time updates, less server load

- [ ] Add streaming imports to unified_api_server.py
- [ ] Add /api/progress/stream/{job_id} endpoint
- [ ] Add /api/jobs/{job_id}/progress with ETag support
- [ ] Update supervisor to emit more progress events
- [ ] Test with curl: `curl -N http://localhost:8000/api/progress/stream/JOB_ID`

**Time**: ~1 hour

### 3. Hardware Auto-Scaling (PERFORMANCE - Do Third)
**Why**: 2-3x faster processing on good hardware

- [ ] Import HardwareOptimizer and EnhancedParallelProcessor in supervisor.py
- [ ] Initialize hardware optimizer in __init__
- [ ] Replace ThreadPoolExecutor in all 5 stage methods
- [ ] Add hardware info to job metadata
- [ ] Test with: `python tools/integrate_hardware_scaling.py`

**Time**: ~2-3 hours (needs testing across stages)

## Testing Order

1. **Unit Tests** (run these first):
   ```bash
   python tools/test_outbox_integration.py
   python tools/test_hardware_integration.py
   ```

2. **Integration Test**:
   ```bash
   # Start server with one feature at a time
   python unified_api_server.py
   
   # Create a small test project
   # Check logs for staging/hardware/SSE messages
   ```

3. **End-to-End Test**:
   - Create project with 3 epics
   - Watch for SSE updates
   - Check staging in database
   - Simulate upload failure and retry

## Configuration Flags

Add to `config/settings.yaml`:

```yaml
features:
  use_outbox_pattern: true      # Enable staging before upload
  use_hardware_scaling: true    # Enable auto-optimization
  enable_sse_progress: true     # Enable real-time updates
  
# Feature-specific settings
outbox:
  batch_size: 50
  retry_attempts: 3
  timeout_seconds: 30

hardware_scaling:
  min_workers: 2
  max_workers: null  # Auto-detect
  
sse:
  update_interval_ms: 1000
  timeout_minutes: 10
```

## Rollback Plan

Each feature can be disabled independently:

```python
# In supervisor.py
if self.config.get('features', {}).get('use_outbox_pattern', False):
    # Use staging
else:
    # Use direct upload

if self.config.get('features', {}).get('use_hardware_scaling', False):
    # Use EnhancedParallelProcessor
else:
    # Use ThreadPoolExecutor
```

## Success Metrics

### Outbox Pattern Success:
- Zero data loss during upload failures
- Ability to retry failed uploads
- Upload progress visible in logs

### SSE Success:
- Real-time progress bar updates
- "sse" shown as connectionType in UI
- Automatic fallback to polling on error

### Hardware Scaling Success:
- Faster completion times
- Hardware info in job metadata
- Stage-specific worker counts in logs

## Common Issues

1. **SSE not working**: Check if nginx/proxy is buffering responses
2. **Hardware detection fails**: Falls back to conservative defaults
3. **Staging performance**: Use batch inserts for large jobs

## Support Scripts

- `tools/integrate_hardware_scaling.py` - Shows exact code changes
- `tools/integrate_outbox_pattern.py` - Tests staging functionality
- `tools/implement_sse_backend.py` - Complete SSE implementation
- `tools/retry_failed_uploads.py` - Already exists for recovery

## Questions?

The implementations are production-ready. The integration is mostly copy-paste with minor adjustments for your workflow.