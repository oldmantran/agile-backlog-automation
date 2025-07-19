#!/usr/bin/env python3
"""
REST API Server for Agile Backlog Automation Frontend Integration.

This FastAPI server provides endpoints for the React frontend to interact
with the backend agents and workflow supervisor.
"""

import os
import sys
import json
import asyncio
import logging
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks, status, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from utils.logger import setup_logger

# Initialize logging
logger = setup_logger(__name__)

# Global storage for active jobs (in production, use Redis or database)
active_jobs: Dict[str, Dict[str, Any]] = {}

# WebSocket connections for log streaming
log_connections: List[WebSocket] = []
log_queue = queue.Queue()

# Custom log handler for streaming logs to WebSocket clients
class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_message = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": self.format(record),
                "module": record.module if hasattr(record, 'module') else record.name
            }
            log_queue.put(log_message)
        except Exception:
            pass

# Set up WebSocket log handler
websocket_handler = WebSocketLogHandler()
websocket_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
websocket_handler.setFormatter(formatter)

# Add handler to root logger to capture all logs
root_logger = logging.getLogger()
root_logger.addHandler(websocket_handler)

# Also add to uvicorn logger
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.addHandler(websocket_handler)

# Log distribution task
async def distribute_logs():
    """Distribute log messages to all connected WebSocket clients"""
    while True:
        try:
            if not log_queue.empty():
                log_message = log_queue.get_nowait()
                disconnected_clients = []
                
                for websocket in log_connections:
                    try:
                        await websocket.send_json(log_message)
                    except Exception:
                        disconnected_clients.append(websocket)
                
                # Remove disconnected clients
                for client in disconnected_clients:
                    if client in log_connections:
                        log_connections.remove(client)
            
            await asyncio.sleep(0.1)  # Small delay to prevent excessive CPU usage
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("Starting Agile Backlog Automation API Server")
    
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)
    
    # Start log distribution task
    asyncio.create_task(distribute_logs())
    
    logger.info("API Server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Server")



# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Agile Backlog Automation API",
    description="REST API for managing agile backlog generation workflows",
    version="1.0.0",
    lifespan=lifespan
)

# Mount job log API router
from api_server_jobs import router as jobs_router
app.include_router(jobs_router)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for active jobs (in production, use Redis or database)
active_jobs: Dict[str, Dict[str, Any]] = {}

# Pydantic models for request/response
class ProjectBasics(BaseModel):
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    domain: str = Field(..., description="Business domain")

class ProductVision(BaseModel):
    visionStatement: str = Field(..., description="Product vision statement")
    businessObjectives: List[str] = Field(default=[], description="Business objectives (extracted from vision if empty)")
    successMetrics: List[str] = Field(default=[], description="Success metrics (extracted from vision if empty)")
    targetAudience: str = Field(default="end users", description="Target audience (extracted from vision if default)")

class AzureConfig(BaseModel):
    organizationUrl: str = Field(default="", description="Azure DevOps organization URL")
    personalAccessToken: str = Field(default="", description="Personal access token (loaded from .env if empty)")
    project: str = Field(default="", description="Azure DevOps project name")
    areaPath: str = Field(default="", description="Area path")
    iterationPath: str = Field(default="", description="Iteration path")

class CreateProjectRequest(BaseModel):
    basics: ProjectBasics
    vision: ProductVision
    azureConfig: AzureConfig = Field(default_factory=AzureConfig, description="Azure DevOps configuration (optional for content-only mode)")

class GenerationStatus(BaseModel):
    jobId: str
    projectId: str
    status: str = Field(..., description="queued|running|completed|failed")
    progress: int = Field(..., ge=0, le=100)
    currentAgent: str = ""
    currentAction: str = ""
    startTime: datetime
    endTime: Optional[datetime] = None
    error: Optional[str] = None

# API Endpoints

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/projects")
async def create_project(project_data: CreateProjectRequest, background_tasks: BackgroundTasks):
    """Create a new project and return project ID."""
    try:
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store project data
        project_info = {
            "id": project_id,
            "data": project_data.dict(),
            "status": "created",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        # Save project to file for persistence
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        project_file = output_dir / f"project_{project_id}.json"
        with open(project_file, 'w') as f:
            json.dump(project_info, f, indent=2)
        
        logger.info(f"Created project {project_id}")
        
        return {
            "success": True,
            "data": {
                "projectId": project_id,
                "status": "created"
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.post("/api/backlog/generate/{project_id}")
async def generate_backlog(project_id: str, background_tasks: BackgroundTasks):
    """Start backlog generation for a project."""
    try:
        # Check if project exists
        project_file = Path("output") / f"project_{project_id}.json"
        if not project_file.exists():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Load project data
        with open(project_file, 'r') as f:
            project_info = json.load(f)
        
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize job status
        job_status = {
            "jobId": job_id,
            "projectId": project_id,
            "status": "queued",
            "progress": 0,
            "currentAgent": "",
            "currentAction": "Initializing workflow",
            "startTime": datetime.now(),
            "endTime": None,
            "error": None
        }
        
        active_jobs[job_id] = job_status
        
        # Start background task for backlog generation
        background_tasks.add_task(run_backlog_generation, job_id, project_info)
        
        logger.info(f"Started backlog generation job {job_id} for project {project_id}")
        
        return {
            "success": True,
            "data": {"jobId": job_id}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting backlog generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

@app.get("/api/backlog/status/{job_id}")
async def get_generation_status(job_id: str):
    """Get the status of a backlog generation job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = active_jobs[job_id]
    
    return {
        "success": True,
        "data": GenerationStatus(**job_status).dict()
    }

@app.get("/api/jobs")
async def get_all_jobs():
    """Get all active and recent jobs."""
    return {
        "success": True,
        "data": [
            {
                **job_data,
                "jobId": job_id
            }
            for job_id, job_data in active_jobs.items()
        ]
    }

@app.get("/api/backlog/templates")
async def get_templates(domain: Optional[str] = None):
    """Get available backlog templates."""
    # Mock templates for now - in production, load from templates directory
    templates = [
        {
            "id": "fintech_basic",
            "name": "FinTech Basic",
            "domain": "fintech",
            "description": "Basic template for financial technology projects",
            "features": ["Payment Processing", "User Management", "Security", "Compliance"]
        },
        {
            "id": "ecommerce_standard",
            "name": "E-commerce Standard",
            "domain": "ecommerce",
            "description": "Standard template for e-commerce platforms",
            "features": ["Product Catalog", "Shopping Cart", "Order Management", "Payment Gateway"]
        },
        {
            "id": "healthcare_hipaa",
            "name": "Healthcare HIPAA",
            "domain": "healthcare",
            "description": "HIPAA-compliant healthcare application template",
            "features": ["Patient Management", "EMR Integration", "Privacy Controls", "Audit Logging"]
        }
    ]
    
    if domain:
        templates = [t for t in templates if t["domain"] == domain]
    
    return {
        "success": True,
        "data": templates
    }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details."""
    project_file = Path("output") / f"project_{project_id}.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    with open(project_file, 'r') as f:
        project_info = json.load(f)
    
    return {
        "success": True,
        "data": project_info
    }

@app.get("/api/projects/{project_id}/backlog")
async def get_project_backlog(project_id: str):
    """Get generated backlog for a project."""
    # Look for the most recent backlog file for this project
    output_dir = Path("output")
    backlog_files = list(output_dir.glob(f"backlog_*_{project_id}.json"))
    
    if not backlog_files:
        # Look for any recent backlog file as fallback
        backlog_files = list(output_dir.glob("backlog_*.json"))
        if not backlog_files:
            raise HTTPException(status_code=404, detail="No backlog found for project")
    
    # Get the most recent file
    latest_backlog = max(backlog_files, key=lambda x: x.stat().st_mtime)
    
    with open(latest_backlog, 'r') as f:
        backlog_data = json.load(f)
    
    return {
        "success": True,
        "data": backlog_data
    }

# Background task functions

async def run_backlog_generation(job_id: str, project_info: Dict[str, Any]):
    """Background task to run the actual backlog generation."""
    try:
        logger.info(f"Starting backlog generation for job {job_id}")
        
        # Update job status
        active_jobs[job_id]["status"] = "running"
        active_jobs[job_id]["currentAction"] = "Initializing workflow"
        active_jobs[job_id]["progress"] = 10
        
        # Extract project data
        project_data = project_info["data"]
        project_name = project_data["basics"]["name"]
        project_domain = project_data["basics"]["domain"]
        
        # Extract area/iteration path and Azure DevOps credentials from Azure config
        azure_config = project_data.get("azureConfig", {})
        organization_url = azure_config.get("organizationUrl")
        project_name_ado = azure_config.get("project")
        area_path = azure_config.get("areaPath")
        iteration_path = azure_config.get("iterationPath")
        
        # Only get PAT from environment if explicitly provided in config
        personal_access_token = azure_config.get("personalAccessToken")
        if not personal_access_token:
            # Only use environment PAT if other config is provided
            if organization_url or project_name_ado or area_path or iteration_path:
                personal_access_token = os.getenv("AZURE_DEVOPS_PAT")
        
        # Check if Azure integration is enabled (if any meaningful Azure config is provided)
        azure_integration_enabled = bool(
            (organization_url and organization_url.strip()) or
            (personal_access_token and personal_access_token.strip()) or
            (project_name_ado and project_name_ado.strip()) or
            (area_path and area_path.strip()) or
            (iteration_path and iteration_path.strip())
        )
        
        if azure_integration_enabled and not all([organization_url, personal_access_token, project_name_ado, area_path, iteration_path]):
            error_msg = "organizationUrl, personalAccessToken (or AZURE_DEVOPS_PAT in .env), project, areaPath, and iterationPath must all be provided in the Azure DevOps configuration."
            logger.error(error_msg)
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = error_msg
            active_jobs[job_id]["endTime"] = datetime.now()
            return

        # Initialize the workflow supervisor with Azure DevOps config (if enabled) and job_id
        if azure_integration_enabled:
            supervisor = WorkflowSupervisor(
                organization_url=organization_url,
                project=project_name_ado,
                personal_access_token=personal_access_token,
                area_path=area_path,
                iteration_path=iteration_path,
                job_id=job_id
            )
        else:
            # Content-only mode (no Azure integration)
            supervisor = WorkflowSupervisor(job_id=job_id)
        
        # Define progress callback function
        def progress_callback(progress: int, action: str):
            """Update job progress in real-time."""
            if job_id in active_jobs:
                active_jobs[job_id]["progress"] = progress
                active_jobs[job_id]["currentAction"] = action
                logger.info(f"Job {job_id} progress: {progress}% - {action}")
        
        # Run the workflow with project context
        context = {
            "project_type": project_domain,
            "project_name": project_name,
            "project_description": project_data["basics"]["description"],
            "vision_statement": project_data["vision"]["visionStatement"],
            "business_objectives": project_data["vision"]["businessObjectives"],
            "target_audience": project_data["vision"]["targetAudience"],
            "azure_config": project_data["azureConfig"]
        }
        
        # Set up the project context for the supervisor
        supervisor.configure_project_context(project_domain, context)
        
        # Create the product vision string
        product_vision = f"""
        Project: {project_name}
        Domain: {project_domain}
        Description: {project_data["basics"]["description"]}
        Vision Statement: {project_data["vision"]["visionStatement"]}
        Business Objectives: {', '.join(project_data["vision"]["businessObjectives"])}
        Target Audience: {project_data["vision"]["targetAudience"]}
        Success Metrics: {', '.join(project_data["vision"]["successMetrics"])}
        """
        
        # Run the supervisor workflow with progress callback
        results = await asyncio.to_thread(
            supervisor.execute_workflow, 
            product_vision, 
            save_outputs=True, 
            integrate_azure=azure_integration_enabled,
            progress_callback=progress_callback
        )
        
        # Update final progress
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["endTime"] = datetime.now()
        
        logger.info(f"Completed backlog generation for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in backlog generation job {job_id}: {str(e)}")
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["endTime"] = datetime.now()

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for streaming server logs to the frontend"""
    await websocket.accept()
    log_connections.append(websocket)
    
    try:
        await websocket.send_json({
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "🌐 Connected to server log stream",
            "module": "websocket"
        })
        
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in log_connections:
            log_connections.remove(websocket)

@app.post("/api/test/logs")
async def test_log_generation():
    """Test endpoint to generate log messages for WebSocket streaming verification"""
    logger.info("🧪 Test log message - INFO level")
    logger.warning("⚠️ Test log message - WARNING level")
    logger.error("❌ Test log message - ERROR level")
    
    # Also test direct queue insertion
    test_message = {
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "message": "📡 Direct queue test message",
        "module": "test_api"
    }
    log_queue.put(test_message)
    
    return {"status": "success", "message": "Test log messages generated"}

# SSE Progress Streaming Endpoints

@app.post("/api/test/create-job")
async def create_test_job():
    """Create a test job for SSE testing."""
    try:
        job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        active_jobs[job_id] = {
            "jobId": job_id,
            "projectId": "test_project",
            "status": "running",
            "progress": 0,
            "currentAction": "Test job created",
            "startTime": datetime.now(),
            "endTime": None,
            "error": None
        }
        
        logger.info(f"Created test job: {job_id}")
        return {"jobId": job_id, "message": "Test job created successfully"}
    except Exception as e:
        logger.error(f"Failed to create test job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test/update-job/{job_id}")
async def update_test_job(job_id: str, progress: int = 50):
    """Update a test job progress for SSE testing."""
    try:
        if job_id in active_jobs:
            active_jobs[job_id]["progress"] = progress
            active_jobs[job_id]["currentAction"] = f"Test progress update: {progress}%"
            logger.info(f"Updated test job {job_id} progress to {progress}%")
            return {"message": f"Job {job_id} updated to {progress}%"}
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    except Exception as e:
        logger.error(f"Failed to update test job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/stream/{job_id}")
async def stream_progress(job_id: str, request: Request):
    """Stream progress updates for a specific job using Server-Sent Events."""
    
    async def event_generator():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'jobId': job_id, 'message': 'SSE connection established'})}\n\n"
            
            last_progress = -1
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected for job {job_id}")
                    break
                
                # Get current job status
                if job_id not in active_jobs:
                    yield f"data: {json.dumps({'type': 'error', 'jobId': job_id, 'message': 'Job not found or not active'})}\n\n"
                    break
                
                job_data = active_jobs[job_id]
                current_progress = job_data.get('progress', 0)
                current_status = job_data.get('status', 'unknown')
                current_action = job_data.get('currentAction', '')
                
                # Only send update if progress changed
                if current_progress != last_progress:
                    progress_data = {
                        'type': 'progress',
                        'jobId': job_id,
                        'progress': current_progress,
                        'status': current_status,
                        'currentAction': current_action,
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    last_progress = current_progress
                    
                    # If job is completed or failed, send final message and close
                    if current_status in ['completed', 'failed']:
                        final_data = {
                            'type': 'final',
                            'jobId': job_id,
                            'status': current_status,
                            'progress': current_progress,
                            'message': f'Job {current_status}',
                            'timestamp': datetime.now().isoformat()
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                
                # Wait before next check
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"SSE error for job {job_id}: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'jobId': job_id, 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Credentials": "true",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to prevent multiprocessing issues
        log_level="info"
    )
