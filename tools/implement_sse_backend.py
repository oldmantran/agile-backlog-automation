#!/usr/bin/env python3
"""
Script to show SSE (Server-Sent Events) backend implementation.
This enables real-time progress tracking in the frontend.
"""

print("=== SSE Backend Implementation Guide ===\n")

print("The frontend useHybridProgress hook is ready and waiting for these endpoints.\n")

print("=== Add to unified_api_server.py ===\n")

print("""
1. Add imports at the top:
```python
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import AsyncGenerator
```

2. Add SSE streaming endpoint:
```python
@app.get("/api/progress/stream/{job_id}")
async def stream_progress(job_id: str) -> StreamingResponse:
    \"\"\"
    Stream job progress updates via Server-Sent Events.
    Frontend will connect to this endpoint for real-time updates.
    \"\"\"
    
    async def generate_events() -> AsyncGenerator[str, None]:
        last_progress = -1
        last_status = None
        retry_count = 0
        max_retries = 300  # 5 minutes max
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'jobId': job_id})}\\n\\n"
        
        while retry_count < max_retries:
            try:
                # Get current job state from database
                job = db.get_job(job_id)
                
                if not job:
                    # Job not found - send error and close
                    yield f"data: {json.dumps({
                        'type': 'error',
                        'jobId': job_id,
                        'message': 'Job not found'
                    })}\\n\\n"
                    break
                
                # Check if progress changed
                current_progress = job.get('progress', 0)
                current_status = job.get('status', 'unknown')
                
                if current_progress != last_progress or current_status != last_status:
                    # Send progress update
                    event_data = {
                        'type': 'progress',
                        'jobId': job_id,
                        'progress': current_progress,
                        'status': current_status,
                        'currentAction': job.get('current_action', ''),
                        'currentAgent': job.get('current_agent', ''),
                        'timestamp': job.get('updated_at', ''),
                        'source': 'database'
                    }
                    
                    yield f"data: {json.dumps(event_data)}\\n\\n"
                    
                    last_progress = current_progress
                    last_status = current_status
                
                # Check if job completed
                if current_status in ['completed', 'failed', 'cancelled']:
                    # Send final event
                    yield f"data: {json.dumps({
                        'type': 'final',
                        'jobId': job_id,
                        'status': current_status,
                        'progress': current_progress
                    })}\\n\\n"
                    break
                
                # Wait before next check
                # More frequent updates when actively running
                if current_status == 'running' and current_progress < 95:
                    await asyncio.sleep(1)  # 1 second for active jobs
                else:
                    await asyncio.sleep(2)  # 2 seconds otherwise
                
                retry_count += 1
                
            except Exception as e:
                logger.error(f"SSE error for job {job_id}: {e}")
                yield f"data: {json.dumps({
                    'type': 'error',
                    'jobId': job_id,
                    'message': str(e)
                })}\\n\\n"
                break
        
        # Timeout after max retries
        if retry_count >= max_retries:
            yield f"data: {json.dumps({
                'type': 'error',
                'jobId': job_id,
                'message': 'Stream timeout - job taking too long'
            })}\\n\\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Access-Control-Allow-Origin": "*"  # Adjust for production
        }
    )
```

3. Add polling endpoint with ETag support:
```python
from fastapi import Request, Response

@app.get("/api/jobs/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    \"\"\"
    Get job progress with ETag support for efficient polling fallback.
    Returns 304 Not Modified if data hasn't changed.
    \"\"\"
    
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check ownership
    if job.get('user_id') != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate ETag from progress and timestamp
    etag = f'W/"{job["progress"]}-{job.get("updated_at", "")}"'
    
    # Check If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        # Data hasn't changed - return 304
        response.status_code = 304
        return None
    
    # Set response headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=0"
    
    # Return progress data
    return {
        "jobId": job_id,
        "progress": job.get("progress", 0),
        "status": job.get("status", "unknown"),
        "currentAction": job.get("current_action", ""),
        "currentAgent": job.get("current_agent", ""),
        "lastUpdated": job.get("updated_at", ""),
        "etag": etag,
        "source": "database"
    }
```

4. Update supervisor to emit more granular progress:
```python
# In supervisor.py, update progress more frequently:

def update_progress(self, progress: int, action: str, agent: str = None):
    \"\"\"Update progress and trigger SSE events.\"\"\"
    
    # Update in database immediately
    self.db.update_job(
        job_id=self.job_id,
        progress=progress,
        current_action=action,
        current_agent=agent,
        updated_at=datetime.utcnow().isoformat()
    )
    
    # Log for debugging
    logger.info(f"[{self.job_id}] {progress}% - {action}")

# Use throughout the workflow:
self.update_progress(5, "Initializing workflow", "supervisor")
self.update_progress(10, "Generating epics", "epic_strategist")
self.update_progress(15, f"Generated {len(epics)} epics", "epic_strategist")
# ... etc
```

5. Test the SSE endpoint:
```bash
# Test with curl
curl -N -H "Accept: text/event-stream" \\
  http://localhost:8000/api/progress/stream/YOUR_JOB_ID

# You should see:
# data: {"type": "connected", "jobId": "YOUR_JOB_ID"}
# data: {"type": "progress", "jobId": "YOUR_JOB_ID", "progress": 10, ...}
# data: {"type": "progress", "jobId": "YOUR_JOB_ID", "progress": 25, ...}
# data: {"type": "final", "jobId": "YOUR_JOB_ID", "status": "completed"}
```

6. Frontend will automatically use SSE when available:
The useHybridProgress hook will:
- Try SSE connection first
- Fall back to polling if SSE fails
- Show connection type in UI
- Handle reconnection automatically

No frontend changes needed - it's already waiting for these endpoints!
""")

print("\n=== Benefits ===")
print("✓ Real-time updates without polling overhead")
print("✓ Lower server load (no constant polling)")
print("✓ Better user experience (instant feedback)")
print("✓ Automatic fallback to polling if SSE fails")
print("✓ Works through proxies and firewalls")
print("\nThe frontend is ready - just add these endpoints!")