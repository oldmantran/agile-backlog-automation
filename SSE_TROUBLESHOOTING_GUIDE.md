# 🔧 SSE Implementation Troubleshooting Guide

## 📋 Overview

This guide helps you troubleshoot the Server-Sent Events (SSE) implementation in your Agile Backlog Automation application. The SSE system provides real-time progress updates from the backend to the frontend during backlog generation.

## 🏗️ Architecture

```
Frontend (React) ←→ SSE Stream ←→ Backend (FastAPI)
     ↑                                    ↑
  EventSource                        Progress Callback
```

## 🚀 Quick Start Testing

### 1. Start the Backend Server
```bash
# Start the main API server
python api_server.py
```

### 2. Test SSE Implementation
```bash
# Run the automated test
python test_sse_implementation.py
```

### 3. Test Frontend SSE
```bash
# Open the HTML test page in your browser
# File: test_sse_frontend.html
```

## 🔍 Common Issues & Solutions

### Issue 1: SSE Connection Fails
**Symptoms:**
- Frontend shows "SSE connection failed"
- Browser console shows CORS errors
- Network tab shows failed requests

**Solutions:**
1. **Check CORS Configuration:**
   ```python
   # In api_server.py - ensure CORS is properly configured
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Verify Server is Running:**
   ```bash
   curl http://localhost:8000/api/health
   ```

3. **Check SSE Endpoint:**
   ```bash
   curl http://localhost:8000/api/progress/stream/test_job_123
   ```

### Issue 2: No Progress Updates
**Symptoms:**
- SSE connects but no progress updates received
- Progress bar stays at 0%
- No real-time updates during backlog generation

**Solutions:**
1. **Check Job Creation:**
   ```bash
   # Create a test job
   curl -X POST http://localhost:8000/api/test/create-job
   ```

2. **Verify Progress Callback:**
   ```python
   # In api_server.py - ensure progress callback is working
   def progress_callback(progress: int, action: str):
       if job_id in active_jobs:
           active_jobs[job_id]["progress"] = progress
           active_jobs[job_id]["currentAction"] = action
           logger.info(f"Job {job_id} progress: {progress}% - {action}")
   ```

3. **Check Active Jobs Storage:**
   ```python
   # Verify job is in active_jobs dictionary
   print(active_jobs.keys())
   ```

### Issue 3: Frontend SSE Hook Issues
**Symptoms:**
- `useSSEProgress` hook not connecting
- React component not receiving updates
- Console errors in browser

**Solutions:**
1. **Check SSE Hook Implementation:**
   ```typescript
   // In useSSEProgress.ts - verify EventSource creation
   const eventSource = new EventSource(`http://localhost:8000/api/progress/stream/${jobId}`, {
       withCredentials: false // Important for CORS
   });
   ```

2. **Verify Job ID:**
   ```typescript
   // Ensure jobId is valid before connecting
   if (!jobId) {
       console.error('No job ID provided');
       return;
   }
   ```

3. **Check Error Handling:**
   ```typescript
   eventSource.onerror = (event) => {
       console.error('SSE connection error:', event);
       setError('SSE connection error');
   };
   ```

### Issue 4: Backend Progress Callback Not Working
**Symptoms:**
- Backend logs show no progress updates
- Supervisor workflow runs but no SSE updates
- Job status not updating

**Solutions:**
1. **Check Supervisor Integration:**
   ```python
   # In api_server.py - ensure progress callback is passed correctly
   results = await asyncio.to_thread(
       supervisor.execute_workflow, 
       product_vision, 
       save_outputs=True, 
       integrate_azure=azure_integration_enabled,
       progress_callback=progress_callback  # Make sure this is passed
   )
   ```

2. **Verify Supervisor Progress Callback:**
   ```python
   # In supervisor/supervisor.py - check progress callback usage
   if progress_callback:
       progress_callback(int(final_progress), action)
   ```

3. **Check Thread Safety:**
   ```python
   # Ensure active_jobs updates are thread-safe
   import threading
   jobs_lock = threading.Lock()
   
   with jobs_lock:
       active_jobs[job_id]["progress"] = progress
   ```

## 🧪 Testing Procedures

### Automated Testing
```bash
# Run the comprehensive test suite
python test_sse_implementation.py
```

### Manual Testing
1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Create Test Job:**
   ```bash
   curl -X POST http://localhost:8000/api/test/create-job
   ```

3. **Test SSE Stream:**
   ```bash
   # Replace JOB_ID with actual job ID
   curl -N http://localhost:8000/api/progress/stream/JOB_ID
   ```

4. **Update Progress:**
   ```bash
   # Replace JOB_ID with actual job ID
   curl -X POST "http://localhost:8000/api/test/update-job/JOB_ID?progress=50"
   ```

### Frontend Testing
1. Open `test_sse_frontend.html` in browser
2. Click "Create Test Job"
3. Click "Connect SSE"
4. Click "Update Progress" to test real-time updates

## 🔧 Debugging Tools

### Backend Debugging
```python
# Add debug logging to api_server.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints to progress callback
def progress_callback(progress: int, action: str):
    logger.debug(f"Progress callback: {progress}% - {action}")
    # ... rest of implementation
```

### Frontend Debugging
```typescript
// Add debug logging to useSSEProgress.ts
console.log(`🔗 Connecting to SSE stream for job: ${jobId}`);
console.log(`📡 Raw SSE message: ${event.data}`);
```

### Network Debugging
1. Open browser DevTools
2. Go to Network tab
3. Filter by "EventStream"
4. Monitor SSE connection and messages

## 📊 Monitoring & Logs

### Backend Logs
```bash
# Check supervisor logs
tail -f logs/supervisor.log

# Check API server logs
# (logs are printed to console when running api_server.py)
```

### Frontend Logs
```javascript
// Check browser console for SSE events
// Look for:
// - Connection establishment
// - Progress updates
// - Error messages
```

## 🚨 Emergency Fixes

### If SSE Completely Broken
1. **Fallback to Polling:**
   ```typescript
   // Temporarily disable SSE and use polling
   const usePollingProgress = (jobId: string) => {
       const [progress, setProgress] = useState(0);
       
       useEffect(() => {
           const interval = setInterval(async () => {
               const response = await fetch(`/api/backlog/status/${jobId}`);
               const data = await response.json();
               setProgress(data.progress);
           }, 2000);
           
           return () => clearInterval(interval);
       }, [jobId]);
       
       return progress;
   };
   ```

2. **Restart Services:**
   ```bash
   # Kill existing processes
   pkill -f "python.*api_server"
   
   # Restart server
   python api_server.py
   ```

3. **Clear Browser Cache:**
   - Hard refresh (Ctrl+F5)
   - Clear browser cache
   - Disable browser extensions temporarily

## 📈 Performance Optimization

### Backend Optimizations
```python
# Reduce SSE polling frequency
await asyncio.sleep(0.5)  # Instead of 1 second

# Batch progress updates
if current_progress != last_progress and (current_progress - last_progress) >= 5:
    # Only send updates for 5%+ changes
```

### Frontend Optimizations
```typescript
// Debounce progress updates
const debouncedSetProgress = useCallback(
    debounce((progress: number) => setProgress(progress), 100),
    []
);
```

## 🔗 Related Files

- `api_server.py` - Main API server with SSE endpoints
- `frontend/src/hooks/useSSEProgress.ts` - Frontend SSE hook
- `test_sse_implementation.py` - Automated SSE tests
- `test_sse_frontend.html` - Manual SSE testing page
- `supervisor/supervisor.py` - Workflow supervisor with progress callbacks

## 📞 Support

If you're still experiencing issues after following this guide:

1. Check the logs for specific error messages
2. Run the automated tests to isolate the problem
3. Verify all dependencies are installed correctly
4. Ensure the backend server is running on the correct port
5. Check for any firewall or network issues blocking SSE connections 