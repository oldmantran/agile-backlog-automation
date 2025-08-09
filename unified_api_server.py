#!/usr/bin/env python3
"""
Unified REST API Server for Agile Backlog Automation Frontend Integration.

This FastAPI server provides endpoints for the React frontend to interact
with the backend agents, workflow supervisor, and management tools.
Combines the best features from api_server.py and tron_api_server.py.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
from dataclasses import dataclass

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from supervisor.supervisor import WorkflowSupervisor
    from config.config_loader import Config
    from utils.logger import setup_logger
    from utils.project_context import ProjectContext
    from utils.notifier import Notifier
    from db import db
    from utils.settings_manager import SettingsManager
    from utils.user_id_resolver import user_id_resolver
    from auth.auth_routes import router as auth_router
    from auth.user_auth import auth_manager
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

# Global flag for shutdown
shutdown_event = threading.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
    shutdown_event.set()
    # Force exit after a short delay if needed
    threading.Timer(5.0, lambda: os._exit(0)).start()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Initialize logging
logger = setup_logger(__name__)

# Global storage for active jobs (simplified - only one job at a time)
active_jobs: Dict[str, Dict[str, Any]] = {}
active_jobs_lock = threading.Lock()  # Thread-safe lock for active_jobs access

# Remove job persistence - we don't need it for simple use case
# JOBS_FILE = Path("output") / "active_jobs.json"

def clear_all_jobs():
    """Clear all active jobs - simple reset."""
    with active_jobs_lock:
        active_jobs.clear()
        logger.info("🧹 Cleared all active jobs")

def get_active_job():
    """Get the single active job if any."""
    with active_jobs_lock:
        if active_jobs:
            job_id = list(active_jobs.keys())[0]
            return job_id, active_jobs[job_id]
        return None, None

def set_active_job(job_id: str, job_data: Dict[str, Any]):
    """Set a single active job, clearing any existing ones."""
    with active_jobs_lock:
        # Clear any existing jobs
        active_jobs.clear()
        # Set the new job
        active_jobs[job_id] = job_data
        logger.info(f"📋 Set active job: {job_id}")

def remove_job(job_id: str):
    """Remove a specific job."""
    with active_jobs_lock:
        if job_id in active_jobs:
            del active_jobs[job_id]
            logger.info(f"🗑️ Removed job: {job_id}")

# SSE connections for progress streaming
sse_connections: Dict[str, List[asyncio.Queue]] = {}

# Global state for background processes
background_processes: Dict[str, subprocess.Popen] = {}
sweeper_status = {"isRunning": False, "progress": 0, "currentItem": "", "processedItems": 0, "totalItems": 0, "errors": [], "completedActions": [], "logs": []}

# Initialize settings manager
config = Config()
settings_manager = SettingsManager(config.settings)

# Thread pool for CPU-intensive AI tasks
ai_thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="AI_Worker")

# Disable FastAPI access logs completely
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.setLevel(logging.ERROR)

logger.info("🔧 SSE progress streaming ready")

# SSE progress distribution task
async def distribute_sse_progress():
    """Distribute progress updates to all connected SSE clients"""
    while True:
        try:
            await asyncio.sleep(0.1)  # Small delay to prevent excessive CPU usage
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("Starting Unified Agile Backlog Automation API Server")
    
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)
    
    # Load active jobs from disk on startup
    # load_active_jobs() # Removed as per edit
    
    # Clean up old jobs on startup
    # cleanup_old_jobs() # Removed as per edit

    # Start SSE progress distribution task
    asyncio.create_task(distribute_sse_progress())

    logger.info("Unified API Server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Unified API Server")
    
    # Save active jobs to disk on shutdown
    # save_active_jobs() # Removed as per edit

    # Shutdown thread pool
    logger.info("Shutting down AI thread pool...")
    ai_thread_pool.shutdown(wait=True)
    logger.info("AI thread pool shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Unified Agile Backlog Automation API",
    description="REST API for managing agile backlog generation workflows and management tools",
    version="2.0.0",
    lifespan=lifespan
)

# Job management is now handled directly in this unified server
# (api_server_jobs.py functionality was consolidated here)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Serve static files from frontend build (only if build directory exists)
project_root = Path(__file__).parent
static_dir = project_root / "frontend" / "build" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Pydantic models for request/response
class ConfigData(BaseModel):
    azureDevOpsPat: str = ""
    azureDevOpsOrg: str = ""
    azureDevOpsProject: str = ""
    llmProvider: str = "openai"
    areaPath: str = ""
    openaiApiKey: str = ""
    grokApiKey: str = ""
    ollamaModel: str = "llama3.1:8b"
    ollamaUrl: str = "http://localhost:11434"
    ollamaPreset: str = "fast"

# Settings Request/Response Models
class SettingsRequest(BaseModel):
    settings: Dict[str, Any]
    scope: str = "session"
    session_id: Optional[str] = None

class WorkItemLimitsRequest(BaseModel):
    max_epics: Optional[int] = 2
    max_features_per_epic: Optional[int] = 3
    max_user_stories_per_feature: Optional[int] = 5
    max_tasks_per_user_story: Optional[int] = 5
    max_test_cases_per_user_story: Optional[int] = 5
    scope: str = "session"
    session_id: Optional[str] = None

class VisualSettingsRequest(BaseModel):
    glow_intensity: int = 70
    scope: str = "session"
    session_id: Optional[str] = None

class SessionDeleteRequest(BaseModel):
    session_id: str
    llmProvider: str = "openai"
    areaPath: str = ""
    openaiApiKey: str = ""
    grokApiKey: str = ""

class SweeperConfig(BaseModel):
    targetArea: str
    iterationPath: str = ""
    includeAcceptanceCriteria: bool = True
    includeTaskDecomposition: bool = True

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
    domainStrategy: Optional[Dict[str, Any]] = Field(None, description="Domain selection strategy for enhanced context")
    includeTestArtifacts: bool = Field(True, description="Whether to generate test plans, test suites, and test cases")

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

# WorkItem model for mock data
@dataclass
class WorkItem:
    id: int
    title: str
    work_item_type: str
    state: str
    area_path: str
    assigned_to: Optional[str] = None

# Utility functions
def load_env_config() -> Dict[str, str]:
    """Load configuration from .env file"""
    env_file = project_root / ".env"
    config = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def save_env_config(config: Dict[str, str]) -> bool:
    """Save configuration to .env file"""
    try:
        env_file = project_root / ".env"
        lines = []
        
        # Read existing file and preserve non-config lines
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith('#'):
                        lines.append(line)
                    elif '=' in line_stripped:
                        key = line_stripped.split('=', 1)[0].strip()
                        if key in config:
                            lines.append(f"{key}={config[key]}\n")
                            del config[key]  # Remove from dict so we don't add it again
                        else:
                            lines.append(line)
                    else:
                        lines.append(line)
        
        # Add any new config items
        for key, value in config.items():
            lines.append(f"{key}={value}\n")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def run_python_script(script_name: str, args: List[str] = None) -> subprocess.Popen:
    """Run a Python script in the background"""
    if args is None:
        args = []
    
    script_path = project_root / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_name}")
    
    cmd = [sys.executable, str(script_path)] + args
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=project_root
    )

# API Endpoints

@app.get("/")
async def serve_frontend():
    """Serve the frontend application"""
    frontend_build = project_root / "frontend" / "build" / "index.html"
    if frontend_build.exists():
        with open(frontend_build, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return {"message": "Unified Agile Backlog Automation API v2.0", "status": "Backend running, frontend not built"}

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify API connectivity."""
    logger.info("🧪 Test endpoint called")
    return {
        "success": True,
        "data": {
            "message": "API is working",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    build_version = db.get_build_version()
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.1.0", "build": build_version}

@app.get("/api/build-version")
async def get_build_version():
    """Get current build version from database."""
    try:
        build_version = db.get_build_version()
        return {"build_version": build_version, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Failed to get build version: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve build version")

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    env_config = load_env_config()
    
    return {
        "azureDevOpsPat": env_config.get("AZURE_DEVOPS_PAT", ""),
        "azureDevOpsOrg": env_config.get("AZURE_DEVOPS_ORG", ""),
        "azureDevOpsProject": env_config.get("AZURE_DEVOPS_PROJECT", ""),
        "llmProvider": env_config.get("LLM_PROVIDER", "openai"),
        "areaPath": env_config.get("AREA_PATH", ""),
        "openaiApiKey": env_config.get("OPENAI_API_KEY", ""),
        "grokApiKey": env_config.get("GROK_API_KEY", ""),
        "ollamaModel": env_config.get("OLLAMA_MODEL", "llama3.1:8b"),
        "ollamaUrl": env_config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollamaPreset": env_config.get("OLLAMA_PRESET", "fast")
    }

@app.post("/api/config")
async def save_config(config: ConfigData):
    """Save configuration to .env file"""
    env_config = {
        "AZURE_DEVOPS_PAT": config.azureDevOpsPat,
        "AZURE_DEVOPS_ORG": config.azureDevOpsOrg,
        "AZURE_DEVOPS_PROJECT": config.azureDevOpsProject,
        "LLM_PROVIDER": config.llmProvider,
        "AREA_PATH": config.areaPath,
        "OPENAI_API_KEY": config.openaiApiKey,
        "GROK_API_KEY": config.grokApiKey,
        "OLLAMA_MODEL": config.ollamaModel,
        "OLLAMA_BASE_URL": config.ollamaUrl,
        "OLLAMA_PRESET": config.ollamaPreset
    }
    
    # Remove empty values
    env_config = {k: v for k, v in env_config.items() if v}
    
    if save_env_config(env_config):
        return {"status": "success", "message": "Configuration saved successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save configuration")

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
            },
            "projectId": project_id  # Also include at root level for compatibility
        }
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.post("/api/generate-backlog")
async def generate_backlog_direct(project_data: CreateProjectRequest, background_tasks: BackgroundTasks):
    """Generate a backlog directly from project data (single-step API)."""
    logger.info("🚀 Direct backlog generation requested")
    logger.info(f"🔍 Request received at: {datetime.now().isoformat()}")
    logger.info(f"🔍 Include test artifacts: {project_data.includeTestArtifacts}")
    
    try:
        # Generate unique IDs
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_id}"
        logger.info(f"🆔 Generated project ID: {project_id}, job ID: {job_id}")
        
        # Store project info
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
        
        # Initialize job status immediately
        set_active_job(job_id, {
            "jobId": job_id,
            "projectId": project_id,
            "status": "queued",
            "progress": 0,
            "currentAgent": "Supervisor",
            "currentAction": "Initializing...",
            "startTime": datetime.now(),
            "error": None,
            "endTime": None,
            "includeTestArtifacts": project_data.includeTestArtifacts
        })
        logger.info(f"🚀 Job {job_id} initialized and queued")
        
        # Add to background tasks using thread pool (non-blocking)
        background_tasks.add_task(run_backlog_generation_threaded, job_id, project_info)
        logger.info(f"✅ Background task added for job: {job_id}")
        
        # Return response immediately with both job_id and project_id for compatibility
        response_data = {
            "project_id": project_id,
            "job_id": job_id,
            "jobId": job_id,  # For backward compatibility
            "projectId": project_id,  # For backward compatibility
            "status": "queued",
            "includeTestArtifacts": project_data.includeTestArtifacts
        }
        logger.info(f"📤 Returning response: {response_data}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"Error starting backlog generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start backlog generation: {str(e)}")

@app.get("/api/projects")
async def list_projects(page: int = 1, limit: int = 10):
    """List all projects with pagination and basic info."""
    try:
        output_dir = Path("output")
        all_projects = []
        
        if output_dir.exists():
            # Find all project files
            for project_file in output_dir.glob("project_*.json"):
                try:
                    with open(project_file, 'r') as f:
                        project_info = json.load(f)
                    
                    # Extract basic project info
                    project_data = project_info.get("data", {})
                    basics = project_data.get("basics", {})
                    
                    project_summary = {
                        "id": project_info.get("id"),
                        "name": basics.get("name", "Unknown"),
                        "description": basics.get("description", ""),
                        "domain": basics.get("domain", ""),
                        "status": project_info.get("status", "unknown"),
                        "createdAt": project_info.get("createdAt"),
                        "updatedAt": project_info.get("updatedAt")
                    }
                    all_projects.append(project_summary)
                except Exception as e:
                    logger.warning(f"Error reading project file {project_file}: {e}")
                    continue
        
        # Sort by creation date (newest first)
        all_projects.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_projects = all_projects[start_idx:end_idx]
        
        return {
            "success": True,
            "data": {
                "projects": paginated_projects,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": len(all_projects),
                    "pages": (len(all_projects) + limit - 1) // limit
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

@app.post("/api/backlog/generate/{project_id}")
async def generate_backlog(project_id: str, background_tasks: BackgroundTasks):
    """Generate a backlog for a project."""
    logger.info(f"🚀 Backlog generation requested for project: {project_id}")
    logger.info(f"🔍 Request received at: {datetime.now().isoformat()}")
    logger.info(f"🔍 Background tasks object: {background_tasks}")
    
    try:
        # Get project info
        project_file = Path("output") / f"project_{project_id}.json"
        if not project_file.exists():
            logger.error(f"❌ Project file not found: {project_file}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        with open(project_file, 'r') as f:
            project_info = json.load(f)
        
        logger.info(f"📋 Project info loaded: {project_info.get('id', 'unknown')}")
        
        # Generate unique job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_id}"
        logger.info(f"🆔 Generated job ID: {job_id}")
        
        # Initialize job status immediately
        set_active_job(job_id, {
            "jobId": job_id,
            "projectId": project_id,
            "status": "queued",
            "progress": 0,
            "currentAgent": "Supervisor",
            "currentAction": "Initializing...",
            "startTime": datetime.now(),
            "error": None,
            "endTime": None
        })
        logger.info(f"🚀 Job {job_id} initialized and queued")
        
        # Add to background tasks using thread pool (non-blocking)
        background_tasks.add_task(run_backlog_generation_threaded, job_id, project_info)
        logger.info(f"✅ Background task added for job: {job_id}")
        
        # Return response immediately
        response_data = {"jobId": job_id}
        logger.info(f"📤 Returning response: {response_data}")
        logger.info(f"📤 Response timestamp: {datetime.now().isoformat()}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        error_msg = f"Failed to start backlog generation: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/backlog/status/{job_id}")
async def get_generation_status(job_id: str):
    """Get the status of a backlog generation job."""
    job_id, job_data = get_active_job()
    if not job_id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert job_status to match GenerationStatus model
    generation_status = {
        "jobId": job_data.get("jobId", job_id),
        "projectId": job_data.get("projectId", "unknown"),
        "status": job_data.get("status", "unknown"),
        "progress": job_data.get("progress", 0),
        "currentAgent": job_data.get("currentAgent", ""),
        "currentAction": job_data.get("currentAction", ""),
        "startTime": job_data.get("startTime"),
        "endTime": job_data.get("endTime"),
        "error": job_data.get("error")
    }
    
    # Only log progress changes, not every status request
    current_progress = generation_status.get('progress', 0)
    if job_id in active_jobs and active_jobs[job_id].get('progress') != current_progress:
        logger.info(f"📊 Progress update for job {job_id}: {active_jobs[job_id].get('progress', 0)}% → {current_progress}%")
    elif job_id not in active_jobs:
        logger.info(f"📊 Initial status for job {job_id}: {current_progress}%")
    
    return {
        "success": True,
        "data": generation_status
    }

@app.post("/api/test/cleanup-jobs")
async def cleanup_jobs_endpoint():
    """Manually trigger job cleanup for testing."""
    try:
        clear_all_jobs()
        return {"message": "All jobs cleared", "current_jobs": list(active_jobs.keys())}
    except Exception as e:
        logger.error(f"Failed to cleanup jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def get_all_jobs():
    """Get all active and recent jobs."""
    job_id, job_data = get_active_job()
    if not job_id:
        return {"success": True, "data": []}
    
    return {
        "success": True,
        "data": [
            {
                **job_data,
                "startTime": job_data["startTime"].isoformat() if isinstance(job_data["startTime"], datetime) else job_data["startTime"],
                "endTime": job_data["endTime"].isoformat() if job_data["endTime"] and isinstance(job_data["endTime"], datetime) else job_data["endTime"]
            }
        ]
    }

@app.post("/api/jobs/add")
async def add_job(job_data: dict):
    """Add a job to the active jobs tracking."""
    try:
        job_id = job_data.get("jobId")
        if not job_id:
            raise HTTPException(status_code=400, detail="jobId is required")
        
        set_active_job(job_id, job_data)
        logger.info(f"Added job {job_id} to active jobs tracking")
        
        return {
            "success": True,
            "data": {"jobId": job_id, "message": "Job added to tracking"}
        }
    except Exception as e:
        logger.error(f"Error adding job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add job: {str(e)}")

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

@app.post("/api/projects/{project_id}/generate-test-artifacts")
async def generate_test_artifacts(project_id: str, background_tasks: BackgroundTasks):
    """Generate test artifacts for an existing project that was created without them."""
    logger.info(f"🧪 Test artifact generation requested for project: {project_id}")
    
    try:
        # Get project info
        project_file = Path("output") / f"project_{project_id}.json"
        if not project_file.exists():
            logger.error(f"❌ Project file not found: {project_file}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        with open(project_file, 'r') as f:
            project_info = json.load(f)
        
        # Look for the most recent backlog file for this project
        output_dir = Path("output")
        backlog_files = list(output_dir.glob(f"backlog_*_{project_id}.json"))
        
        if not backlog_files:
            logger.error(f"❌ No backlog found for project: {project_id}")
            raise HTTPException(status_code=404, detail="No backlog found for this project")
        
        # Get the most recent backlog
        latest_backlog = max(backlog_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_backlog, 'r') as f:
            backlog_data = json.load(f)
        
        # Check if test artifacts already exist
        if any(epic.get('test_plan') or any(f.get('test_cases') for f in epic.get('features', [])) 
               for epic in backlog_data.get('epics', [])):
            logger.warning(f"⚠️ Test artifacts already exist for project: {project_id}")
            raise HTTPException(status_code=400, detail="Test artifacts already exist for this project")
        
        # Generate job ID for test artifact generation
        job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_id}"
        logger.info(f"🆔 Generated test job ID: {job_id}")
        
        # Initialize job status
        set_active_job(job_id, {
            "jobId": job_id,
            "projectId": project_id,
            "status": "queued",
            "progress": 0,
            "currentAgent": "QA Lead Agent",
            "currentAction": "Initializing test artifact generation...",
            "startTime": datetime.now(),
            "error": None,
            "endTime": None,
            "isTestArtifactOnly": True
        })
        
        # Add to background tasks
        background_tasks.add_task(run_test_artifact_generation, job_id, project_info, backlog_data)
        logger.info(f"✅ Background task added for test generation job: {job_id}")
        
        return {
            "success": True,
            "data": {
                "jobId": job_id,
                "message": "Test artifact generation started"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to start test artifact generation: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

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

# Azure DevOps and AI Validation Endpoints
@app.post("/api/validate-azure")
async def validate_azure_connection(data: dict):
    """Validate Azure DevOps connection"""
    try:
        # Mock validation - in production, test actual connection
        return {"status": "success", "message": "Azure DevOps connection validated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/validate-ai")
async def validate_ai_connection(data: dict):
    """Validate AI provider connection"""
    try:
        # Mock validation - in production, test actual connection
        return {"status": "success", "message": "AI provider connection validated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

# Work Item Management Endpoints
@app.get("/api/workitems")
async def get_work_items():
    """Get work items from Azure DevOps"""
    # Mock data for now
    work_items = [
        WorkItem(1, "Implement user authentication", "User Story", "Active", "Project\\Features"),
        WorkItem(2, "Design database schema", "Task", "Completed", "Project\\Backend"),
        WorkItem(3, "Create API endpoints", "User Story", "Active", "Project\\API")
    ]
    
    return {
        "success": True,
        "data": [asdict(item) for item in work_items]
    }

@app.post("/api/workitems/delete")
async def delete_work_items(data: dict):
    """Delete work items from Azure DevOps"""
    try:
        # Mock deletion - in production, call Azure DevOps API
        item_ids = data.get("itemIds", [])
        return {
            "status": "success",
            "message": f"Deleted {len(item_ids)} work items",
            "deletedIds": item_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# Test Management Endpoints
@app.get("/api/testcases")
async def get_test_cases():
    """Get test cases from Azure DevOps"""
    # Mock data
    return {
        "success": True,
        "data": [
            {"id": 1, "title": "Login functionality test", "state": "Active"},
            {"id": 2, "title": "User registration test", "state": "Active"}
        ]
    }

@app.get("/api/testsuites")
async def get_test_suites():
    """Get test suites from Azure DevOps"""
    # Mock data
    return {
        "success": True,
        "data": [
            {"id": 1, "name": "Authentication Suite", "testCaseCount": 5},
            {"id": 2, "name": "User Management Suite", "testCaseCount": 3}
        ]
    }

@app.get("/api/testplans")
async def get_test_plans():
    """Get test plans from Azure DevOps"""
    # Mock data
    return {
        "success": True,
        "data": [
            {"id": 1, "name": "Sprint 1 Test Plan", "testSuiteCount": 2},
            {"id": 2, "name": "Regression Test Plan", "testSuiteCount": 1}
        ]
    }

@app.post("/api/test/delete")
async def delete_test_items(data: dict):
    """Delete test items from Azure DevOps"""
    try:
        # Mock deletion
        item_ids = data.get("itemIds", [])
        item_type = data.get("itemType", "testcase")
        return {
            "status": "success",
            "message": f"Deleted {len(item_ids)} {item_type}s",
            "deletedIds": item_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# Backlog Sweeper Endpoints
@app.get("/api/sweeper/config")
async def get_sweeper_config():
    """Get current sweeper configuration"""
    return {
        "success": True,
        "data": {
            "targetArea": "",
            "iterationPath": "",
            "includeAcceptanceCriteria": True,
            "includeTaskDecomposition": True
        }
    }

@app.post("/api/sweeper/config")
async def save_sweeper_config(config: SweeperConfig):
    """Save sweeper configuration"""
    # In production, save to config file
    return {"status": "success", "message": "Sweeper configuration saved"}

@app.post("/api/sweeper/start")
async def start_sweeper(config: SweeperConfig, background_tasks: BackgroundTasks):
    """Start the backlog sweeper"""
    try:
        if sweeper_status["isRunning"]:
            raise HTTPException(status_code=400, detail="Sweeper is already running")
        
        # Reset status
        sweeper_status.update({
            "isRunning": True,
            "progress": 0,
            "currentItem": "",
            "processedItems": 0,
            "totalItems": 0,
            "errors": [],
            "completedActions": [],
            "logs": []
        })
        
        # Start background task
        background_tasks.add_task(run_sweeper_background, config)
        
        return {"status": "success", "message": "Sweeper started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sweeper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start sweeper: {str(e)}")

@app.post("/api/sweeper/stop")
async def stop_sweeper():
    """Stop the backlog sweeper"""
    sweeper_status["isRunning"] = False
    return {"status": "success", "message": "Sweeper stopped"}

@app.get("/api/sweeper/status")
async def get_sweeper_status():
    """Get sweeper status"""
    return {"success": True, "data": sweeper_status}

# Background task functions
async def run_sweeper_background(config: SweeperConfig):
    """Background task to run the backlog sweeper"""
    try:
        logger.info("Starting backlog sweeper")
        
        # Mock sweeper process
        total_items = 10
        sweeper_status["totalItems"] = total_items
        
        for i in range(total_items):
            if not sweeper_status["isRunning"]:
                break
                
            sweeper_status["currentItem"] = f"Item {i+1}"
            sweeper_status["progress"] = int((i + 1) / total_items * 100)
            sweeper_status["processedItems"] = i + 1
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            # Add some logs
            log_entry = f"Processed {sweeper_status['currentItem']}"
            sweeper_status["logs"].append(log_entry)
            logger.info(log_entry)
        
        sweeper_status["isRunning"] = False
        sweeper_status["progress"] = 100
        sweeper_status["completedActions"].append("Sweep completed")
        
        logger.info("Backlog sweeper completed")
        
    except Exception as e:
        logger.error(f"Error in sweeper: {str(e)}")
        sweeper_status["isRunning"] = False
        sweeper_status["errors"].append(str(e))

async def run_backlog_generation_threaded(job_id: str, project_info: Dict[str, Any]):
    """Async wrapper that runs the AI processing in a separate thread to prevent blocking."""
    logger.info(f"🔄 Starting threaded backlog generation for job {job_id}")
    
    try:
        # Run the actual AI processing in a thread pool to prevent blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(ai_thread_pool, run_backlog_generation_sync, job_id, project_info)
        logger.info(f"✅ Threaded backlog generation completed for job {job_id}")
        return result
    except Exception as e:
        error_msg = f"Threaded backlog generation failed for job {job_id}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
        return {"error": error_msg}

def run_backlog_generation_sync(job_id: str, project_info: Dict[str, Any]):
    """Synchronous version of backlog generation that runs in a separate thread."""
    
    # Start auto-logging to capture all output for this job
    from utils.auto_log_dumper import start_auto_logging, stop_auto_logging
    log_dumper = start_auto_logging(job_id=job_id)
    
    try:
        logger.info(f"Starting backlog generation for job {job_id}")
        
        # Update job status to running (job is already initialized)
        set_active_job(job_id, {"status": "running", "currentAction": "Starting workflow execution..."})
        
        # Extract project data
        project_data = project_info.get("data", {})
        
        # Check Azure DevOps integration
        azure_config = project_data.get("azureConfig", {})
        azure_integration_enabled = azure_config.get("enabled", False)
        
        # Azure DevOps parameters
        organization_url = azure_config.get("organizationUrl")
        azure_project = azure_config.get("project")
        personal_access_token = azure_config.get("personalAccessToken")
        area_path = azure_config.get("areaPath")
        iteration_path = azure_config.get("iterationPath")
        
        # Use Azure DevOps project name as the project name, fallback to basics.name if not available
        project_name = azure_project or project_data.get("basics", {}).get("name", "Unknown Project")
        
        # Extract test artifacts configuration
        include_test_artifacts = project_data.get("includeTestArtifacts", True)
        logger.info(f"🧪 Include test artifacts: {include_test_artifacts}")
        
        # Extract domain from vision statement using VisionContextExtractor
        from utils.vision_context_extractor import VisionContextExtractor
        vision_extractor = VisionContextExtractor()
        
        # Extract enhanced context from vision
        vision_data = project_data.get("vision", {})
        vision_statement = vision_data.get('visionStatement', '')
        
        enhanced_context = vision_extractor.extract_context(
            project_data=project_data,
            business_objectives=vision_data.get('businessObjectives', []),
            target_audience=vision_data.get('targetAudience'),
            domain=project_data.get("basics", {}).get("domain")
        )
        
        # Use extracted domain or fallback to dynamic
        project_domain = enhanced_context.get('domain', 'dynamic')
        
        # Load PAT from .env if not provided in request
        if not personal_access_token:
            env_config = load_env_config()
            personal_access_token = env_config.get("AZURE_DEVOPS_PAT", "")
            if personal_access_token:
                logger.info(f"🔑 Loaded Azure DevOps PAT from .env file")
            else:
                logger.warning(f"⚠️ Azure DevOps PAT not found in request or .env file")
        
        # Enhanced logging for Azure DevOps configuration
        logger.info(f"🔍 Azure DevOps Configuration Analysis for job {job_id}:")
        logger.info(f"   azure_integration_enabled (from config): {azure_integration_enabled}")
        logger.info(f"   organization_url: {organization_url}")
        logger.info(f"   project: {project_name}")
        logger.info(f"   personal_access_token: {'Set' if personal_access_token else 'Not set'}")
        logger.info(f"   area_path: {area_path}")
        logger.info(f"   iteration_path: {iteration_path}")
        
        # Check if any Azure config is provided (alternative detection method)
        has_any_azure_config = any([
            organization_url,
            project_name,
            personal_access_token,
            area_path,
            iteration_path
        ])
        logger.info(f"   has_any_azure_config: {has_any_azure_config}")
        
        # Validate Azure DevOps configuration
        if azure_integration_enabled:
            if not all([organization_url, project_name, personal_access_token]):
                logger.warning(f"❌ Azure integration enabled but missing required fields for job {job_id}")
                azure_integration_enabled = False
        elif has_any_azure_config:
            logger.info(f"⚠️ Azure config provided but integration not explicitly enabled for job {job_id}")
            # Auto-enable if we have the required fields
            if all([organization_url, project_name, personal_access_token, area_path, iteration_path]):
                logger.info(f"✅ Auto-enabling Azure integration for job {job_id} (all required fields present)")
                azure_integration_enabled = True
            else:
                logger.warning(f"❌ Cannot auto-enable Azure integration for job {job_id} (missing required fields)")
        
        logger.info(f"   Final azure_integration_enabled: {azure_integration_enabled}")
        
        # Get current user ID for settings management
        current_user_id = user_id_resolver.get_default_user_id()
        logger.info(f"🔧 Using user ID for settings: {current_user_id}")
        
        # Initialize supervisor with error handling for Azure DevOps
        try:
            logger.info(f"🔧 Initializing WorkflowSupervisor for job {job_id} with Azure config:")
            logger.info(f"   organization_url: {organization_url}")
            logger.info(f"   project: {project_name}")
            logger.info(f"   area_path: {area_path}")
            logger.info(f"   iteration_path: {iteration_path}")
            
            # If Azure integration is enabled but credentials are invalid, disable it
            if azure_integration_enabled and (not personal_access_token or not organization_url or not project_name):
                logger.warning(f"⚠️ Azure integration enabled but credentials incomplete, disabling for job {job_id}")
                azure_integration_enabled = False
            
            # Initialize supervisor with safe defaults if Azure integration is disabled
            if azure_integration_enabled:
                supervisor = WorkflowSupervisor(
                    organization_url=organization_url,
                    project=project_name,
                    personal_access_token=personal_access_token,
                    area_path=area_path,
                    iteration_path=iteration_path,
                    job_id=job_id,
                    settings_manager=settings_manager,
                    user_id=current_user_id,
                    include_test_artifacts=include_test_artifacts
                )
            else:
                # Initialize without Azure DevOps integration
                logger.info(f"🔧 Initializing WorkflowSupervisor without Azure DevOps integration for job {job_id}")
                supervisor = WorkflowSupervisor(
                    organization_url="",  # Empty to disable Azure integration
                    project=project_name,
                    personal_access_token="",  # Empty to disable Azure integration
                    area_path="",
                    iteration_path="",
                    job_id=job_id,
                    settings_manager=settings_manager,
                    user_id=current_user_id,
                    include_test_artifacts=include_test_artifacts
                )
            
            # IMPORTANT: Set the project name in the supervisor's project context
            supervisor.project = project_name
            supervisor.project_context.update_context({
                'project_name': project_name,
                'domain': project_domain
            })
            
            logger.info(f"✅ WorkflowSupervisor initialized successfully for job {job_id}")
            logger.info(f"   Project name set to: {project_name}")
            logger.info(f"   Domain set to: {project_domain}")
            logger.info(f"   Azure integration: {'enabled' if azure_integration_enabled else 'disabled'}")
            
        except Exception as e:
            error_msg = f"Failed to initialize WorkflowSupervisor: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # If Azure DevOps validation failed, try without Azure integration
            if "401" in str(e) or "Unauthorized" in str(e) or "Azure" in str(e):
                logger.info(f"🔄 Azure DevOps validation failed, retrying without Azure integration for job {job_id}")
                try:
                    azure_integration_enabled = False
                    supervisor = WorkflowSupervisor(
                        organization_url="",
                        project=project_name,
                        personal_access_token="",
                        area_path="",
                        iteration_path="",
                        job_id=job_id,
                        settings_manager=settings_manager,
                        user_id=current_user_id,
                        include_test_artifacts=include_test_artifacts
                    )
                    supervisor.project = project_name
                    supervisor.project_context.update_context({
                        'project_name': project_name,
                        'domain': project_domain
                    })
                    logger.info(f"✅ WorkflowSupervisor initialized successfully without Azure DevOps for job {job_id}")
                except Exception as retry_error:
                    error_msg = f"Failed to initialize WorkflowSupervisor (retry without Azure): {str(retry_error)}"
                    logger.error(f"❌ {error_msg}")
                    set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
                    return {"error": error_msg}
            else:
                set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
                return {"error": error_msg}
        
        # Progress callback with thread-safe updates
        def progress_callback(progress: int, action: str):
            try:
                set_active_job(job_id, {
                    **get_active_job()[1], # Get current job data
                    "progress": progress,
                    "currentAction": action,
                    "currentAgent": action.split()[0] if action else "Supervisor",
                    "status": "running"
                })
                logger.info(f"📊 Progress update for job {job_id}: {progress}% - {action}")
                
            except Exception as e:
                logger.error(f"Error in progress callback for job {job_id}: {str(e)}")

        # Prepare context
        context = {
            "project_name": project_name,
            "project_domain": project_domain,
            "azure_integration_enabled": azure_integration_enabled,
            "azure_config": azure_config if azure_integration_enabled else {}
        }

        # Configure project context
        try:
            config = Config()
            project_context = ProjectContext(config)
            
            # Update context with project data
            project_updates = {
                "project_name": project_name,
                "domain": project_domain,
                "platform": "Web Application",  # Default platform
                "target_users": project_data.get("vision", {}).get("targetUsers", "End users"),
                "timeline": "6-12 months"  # Default timeline
            }
            project_context.update_context(project_updates)
            
        except Exception as e:
            error_msg = f"Failed to configure project context: {str(e)}"
            set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
            return {"error": error_msg}

        # Create product vision - use the full comprehensive vision statement
        vision_data = project_data.get("vision", {})
        full_vision = vision_data.get('visionStatement', 'No vision statement provided')
        
        product_vision = f"""
Project: {project_name}
Domain: {project_domain}

{full_vision}
""".strip()

        # Get includeTestArtifacts flag - defaults to True for backward compatibility
        include_test_artifacts = project_data.get('includeTestArtifacts', True)
        logger.info(f"🔧 includeTestArtifacts flag: {include_test_artifacts}")

        # Execute workflow
        try:
            logger.info(f"🚀 Starting workflow execution for job {job_id}")
            logger.info(f"   integrate_azure: {azure_integration_enabled}")
            logger.info(f"   product_vision length: {len(product_vision)} characters")
            logger.info(f"   save_outputs: True")
            logger.info(f"   include_test_artifacts: {include_test_artifacts}")
            
            results = supervisor.execute_workflow(
                product_vision,
                save_outputs=True,
                integrate_azure=azure_integration_enabled,
                progress_callback=progress_callback,
                include_test_artifacts=include_test_artifacts
            )
            
            logger.info(f"✅ Workflow execution completed for job {job_id}")
            logger.info(f"   Results type: {type(results)}")
            if isinstance(results, dict):
                logger.info(f"   Results keys: {list(results.keys())}")
                if 'azure_integration' in results:
                    azure_result = results['azure_integration']
                    logger.info(f"   Azure integration status: {azure_result.get('status', 'Unknown')}")
                    if azure_result.get('work_items_created'):
                        logger.info(f"   Work items created: {len(azure_result['work_items_created'])}")
                    if azure_result.get('error'):
                        logger.error(f"   Azure integration error: {azure_result['error']}")

            # Update job status
            set_active_job(job_id, {"status": "completed", "progress": 100, "currentAction": "Completed", "endTime": datetime.now()})

            return {"job_id": job_id, "status": "completed", "results": results}

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error in run_backlog_generation: {str(e)}"
        set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
        logger.error(error_msg)
        return {"error": error_msg}
    finally:
        # Always save the log file regardless of success or failure
        try:
            log_file = stop_auto_logging()
            if log_file:
                logger.info(f"📋 Backend log automatically saved to: {log_file}")
        except Exception as log_error:
            logger.warning(f"⚠️ Failed to save auto log: {log_error}")


def run_test_artifact_generation(job_id: str, project_info: Dict[str, Any], backlog_data: Dict[str, Any]):
    """Generate test artifacts for an existing backlog."""
    logger.info(f"🧪 Starting test artifact generation for job {job_id}")
    
    try:
        # Update job status
        set_active_job(job_id, {"status": "running", "progress": 10, "currentAction": "Loading project configuration"})
        
        # Extract project configuration
        project_data = project_info.get('data', {})
        azure_config = project_data.get('azureConfig', {})
        
        # Initialize configuration
        config = Config()
        
        # Initialize supervisor for test-only workflow
        azure_integration_enabled = bool(
            azure_config.get('organizationUrl') and 
            azure_config.get('project') and 
            azure_config.get('areaPath')
        )
        
        # Progress callback
        def progress_callback(progress: int, action: str):
            try:
                set_active_job(job_id, {
                    **get_active_job()[1],  # Get current job data
                    "progress": progress,
                    "currentAction": action,
                    "currentAgent": "QA Lead Agent",
                    "status": "running"
                })
                logger.info(f"📊 Test generation progress for job {job_id}: {progress}% - {action}")
            except Exception as e:
                logger.error(f"Error in progress callback for test job {job_id}: {str(e)}")
        
        # Update progress
        progress_callback(20, "Initializing QA Lead Agent")
        
        # Initialize QA Lead Agent directly
        from agents.qa.qa_lead_agent import QALeadAgent
        qa_agent = QALeadAgent(config)
        
        # Process each epic and its features to generate test artifacts
        epics_with_tests = []
        total_epics = len(backlog_data.get('epics', []))
        
        for epic_idx, epic in enumerate(backlog_data.get('epics', [])):
            epic_progress = 20 + (epic_idx / total_epics) * 70
            progress_callback(int(epic_progress), f"Processing epic {epic_idx + 1}/{total_epics}: {epic.get('title', '')[:50]}...")
            
            # Generate test plan for epic
            test_plan = qa_agent.generate_test_plan(epic)
            if test_plan:
                epic['test_plan'] = test_plan
            
            # Process features
            for feature_idx, feature in enumerate(epic.get('features', [])):
                feature_progress = epic_progress + ((feature_idx + 1) / len(epic.get('features', []))) * (70 / total_epics)
                progress_callback(int(feature_progress), f"Generating test cases for feature: {feature.get('title', '')[:50]}...")
                
                # Generate test cases for each user story
                for story in feature.get('user_stories', []):
                    test_cases = qa_agent.generate_test_cases(story, feature, epic)
                    if test_cases:
                        story['test_cases'] = test_cases
            
            epics_with_tests.append(epic)
        
        # Update backlog data with test artifacts
        backlog_data['epics'] = epics_with_tests
        
        # Save updated backlog
        progress_callback(90, "Saving test artifacts")
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save with test suffix
        test_backlog_file = output_dir / f"backlog_with_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_info['id']}.json"
        with open(test_backlog_file, 'w') as f:
            json.dump(backlog_data, f, indent=2)
        
        logger.info(f"✅ Saved test-enhanced backlog to {test_backlog_file}")
        
        # If Azure integration is enabled, upload test artifacts
        if azure_integration_enabled:
            progress_callback(95, "Uploading test artifacts to Azure DevOps")
            # TODO: Implement test artifact upload to Azure DevOps
            logger.info("🔄 Test artifact upload to Azure DevOps not yet implemented")
        
        # Update job status to completed
        set_active_job(job_id, {
            "status": "completed", 
            "progress": 100, 
            "currentAction": "Test artifact generation completed",
            "endTime": datetime.now()
        })
        
        logger.info(f"✅ Test artifact generation completed for job {job_id}")
        return {"job_id": job_id, "status": "completed", "test_backlog_file": str(test_backlog_file)}
        
    except Exception as e:
        error_msg = f"Test artifact generation failed: {str(e)}"
        set_active_job(job_id, {"status": "failed", "error": error_msg, "endTime": datetime.now()})
        logger.error(error_msg)
        return {"error": error_msg}


# SSE Progress Streaming Endpoints

@app.post("/api/test/create-job")
async def create_test_job():
    """Create a test job for SSE testing."""
    try:
        job_id = f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        set_active_job(job_id, {
            "jobId": job_id,
            "projectId": "test_project",
            "status": "running",
            "progress": 0,
            "currentAction": "Test job created",
            "startTime": datetime.now(),
            "endTime": None,
            "error": None
        })
        
        logger.info(f"Created test job: {job_id}")
        return {"jobId": job_id, "message": "Test job created successfully"}
    except Exception as e:
        logger.error(f"Failed to create test job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test/update-job/{job_id}")
async def update_test_job(job_id: str, progress: int = 50):
    """Update a test job progress for SSE testing."""
    try:
        set_active_job(job_id, {"progress": progress, "currentAction": f"Test progress update: {progress}%"})
        logger.info(f"Updated test job {job_id} progress to {progress}%")
        return {"message": f"Job {job_id} updated to {progress}%"}
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
                current_job_id, job_data = get_active_job()
                
                if not current_job_id or current_job_id != job_id:
                    yield f"data: {json.dumps({'type': 'error', 'jobId': job_id, 'message': 'Job not found or not active'})}\n\n"
                    break
                
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



@app.post("/api/test/logs")
async def test_log_generation():
    """Test endpoint to generate log messages for WebSocket streaming verification"""
    logger.info("🧪 Test log message - INFO level")
    logger.warning("⚠️ Test log message - WARNING level")
    logger.error("❌ Test log message - ERROR level")
    
    # Also test direct queue insertion
    # test_message = { # This line was removed as per the edit hint
    #     "timestamp": datetime.now().isoformat(),
    #     "level": "INFO",
    #     "message": "📡 Direct queue test message from unified server",
    #     "module": "test_api"
    # }
    # log_queue.put(test_message) # This line was removed as per the edit hint
    
    return {"status": "success", "message": "Test log messages generated"}

@app.post("/api/start-application")
async def start_application():
    """Start the full application (backend + frontend)"""
    try:
        # Start frontend in background
        threading.Timer(2.0, open_browser).start()
        return {"status": "success", "message": "Application starting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start application: {str(e)}")

def open_browser():
    """Open browser to the application"""
    try:
        webbrowser.open("http://localhost:3000")
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")

# User Settings Endpoints
@app.get("/api/settings/{user_id}")
async def get_user_settings(user_id: str, session_id: str = None):
    """Get all settings for a user/session."""
    try:
        settings = settings_manager.get_all_settings(user_id, session_id)
        return {
            "success": True,
            "data": settings
        }
    except Exception as e:
        logger.error(f"Failed to get settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/{user_id}")
async def save_user_settings(user_id: str, request: SettingsRequest):
    """Save user settings."""
    try:
        success = settings_manager.save_all_settings(
            user_id, request.settings, request.scope, request.session_id
        )
        
        if success:
            return {
                "success": True,
                "message": f"Settings saved successfully ({request.scope})"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
            
    except Exception as e:
        logger.error(f"Failed to save settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings/{user_id}/work-item-limits")
async def get_work_item_limits(user_id: str, session_id: str = None):
    """Get work item limits for a user/session."""
    try:
        limits_with_flags = settings_manager.get_work_item_limits_with_flags(user_id, session_id)
        return {
            "success": True,
            "data": limits_with_flags
        }
    except Exception as e:
        logger.error(f"Failed to get work item limits for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/{user_id}/work-item-limits")
async def save_work_item_limits(user_id: str, request: WorkItemLimitsRequest):
    """Save work item limits."""
    try:
        limits = {
            'max_epics': request.max_epics,
            'max_features_per_epic': request.max_features_per_epic,
            'max_user_stories_per_feature': request.max_user_stories_per_feature,
            'max_tasks_per_user_story': request.max_tasks_per_user_story,
            'max_test_cases_per_user_story': request.max_test_cases_per_user_story
        }
        
        # Determine if this is a custom user default
        is_user_default = getattr(request, 'is_user_default', request.scope == 'user_default')
        
        success = settings_manager.save_work_item_limits(
            user_id, limits, request.scope, request.session_id, is_user_default
        )
        
        if success:
            return {
                "success": True,
                "message": f"Work item limits saved successfully ({request.scope})",
                "is_user_default": is_user_default
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save work item limits")
            
    except Exception as e:
        logger.error(f"Failed to save work item limits for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/settings/{user_id}/work-item-limits")
async def delete_work_item_limits(user_id: str, scope: str = Query('user_default')):
    """Delete work item limits."""
    try:
        success = db.delete_user_settings(user_id, 'work_item_limits', scope)
        
        if success:
            return {
                "success": True,
                "message": f"Work item limits deleted successfully ({scope})"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete work item limits")
            
    except Exception as e:
        logger.error(f"Failed to delete work item limits for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings/{user_id}/visual-settings")
async def get_visual_settings(user_id: str, session_id: str = None):
    """Get visual settings for a user/session."""
    try:
        settings = settings_manager.get_visual_settings(user_id, session_id)
        return {
            "success": True,
            "data": {
                "glow_intensity": settings.glow_intensity
            }
        }
    except Exception as e:
        logger.error(f"Failed to get visual settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/{user_id}/visual-settings")
async def save_visual_settings(user_id: str, request: VisualSettingsRequest):
    """Save visual settings."""
    try:
        settings = {
            'glow_intensity': request.glow_intensity
        }
        
        success = settings_manager.save_visual_settings(
            user_id, settings, request.scope, request.session_id
        )
        
        if success:
            return {
                "success": True,
                "message": f"Visual settings saved successfully ({request.scope})"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save visual settings")
            
    except Exception as e:
        logger.error(f"Failed to save visual settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/settings/{user_id}/session")
async def delete_session_settings(user_id: str, request: SessionDeleteRequest):
    """Delete session-specific settings."""
    try:
        success = settings_manager.delete_session_settings(request.session_id)
        
        if success:
            return {
                "success": True,
                "message": "Session settings deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete session settings")
            
    except Exception as e:
        logger.error(f"Failed to delete session settings for {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings/{user_id}/history")
async def get_setting_history(user_id: str, setting_type: str = None):
    """Get setting change history for audit trail."""
    try:
        history = settings_manager.get_setting_history(user_id, setting_type)
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        logger.error(f"Failed to get setting history for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get available Ollama models"""
    try:
        import subprocess
        import json
        
        # Use the full path to ollama
        import os
        username = os.getenv('USERNAME', '')
        ollama_path = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Ollama\\ollama.exe"
        
        # Check if the path exists
        if not os.path.exists(ollama_path):
            return {"models": [], "error": f"Ollama not found at {ollama_path}"}
        
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Parse the text output
            lines = result.stdout.strip().split('\n')
            models = []
            
            # Skip header line and parse model names
            for line in lines[1:]:  # Skip "NAME ID SIZE MODIFIED" header
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])  # First column is the model name
            
            return {"models": models}
        else:
            return {"models": [], "error": f"Failed to get models: {result.stderr}"}
            
    except Exception as e:
        return {"models": [], "error": str(e)}

@app.get("/api/user/current")
async def get_current_user():
    """Get current user information."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        user_email = user_id_resolver.get_user_email()
        display_name = user_id_resolver.get_user_display_name()
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "email": user_email,
                "display_name": display_name
            }
        }
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LLM Configuration API Endpoints
class LLMConfigurationRequest(BaseModel):
    name: str
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    preset: Optional[str] = None
    is_default: bool = False
    is_active: bool = False

@app.get("/api/llm/configurations")
async def get_llm_configurations():
    """Get all LLM configurations for the current user."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        configurations = db.get_llm_configurations(user_id)
        return {"configurations": configurations}
    except Exception as e:
        logger.error(f"Failed to get LLM configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LLM configurations")

@app.get("/api/llm/configurations/active")
async def get_active_llm_configuration():
    """Get the currently active LLM configuration for the current user."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        configuration = db.get_active_llm_configuration(user_id)
        if not configuration:
            # Return default configuration from environment
            env_config = load_env_config()
            return {
                "name": "Environment Default",
                "provider": env_config.get("LLM_PROVIDER", "openai"),
                "model": env_config.get("OLLAMA_MODEL", "llama3.1:8b"),
                "base_url": env_config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                "preset": env_config.get("OLLAMA_PRESET", "fast"),
                "is_default": True,
                "is_active": True
            }
        
        return configuration
    except Exception as e:
        logger.error(f"Failed to get active LLM configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active LLM configuration")

@app.post("/api/llm/configurations")
async def save_llm_configuration(config: LLMConfigurationRequest):
    """Save or update an LLM configuration."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = db.save_llm_configuration(
            user_id=user_id,
            name=config.name,
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            preset=config.preset,
            is_default=config.is_default,
            is_active=config.is_active
        )
        
        if success:
            return {"message": "LLM configuration saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save LLM configuration")
    except Exception as e:
        logger.error(f"Failed to save LLM configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to save LLM configuration")

@app.post("/api/llm/configurations/{name}/activate")
async def activate_llm_configuration(name: str):
    """Set an LLM configuration as active."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = db.set_active_llm_configuration(user_id, name)
        if success:
            return {"message": f"LLM configuration '{name}' activated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to activate LLM configuration")
    except Exception as e:
        logger.error(f"Failed to activate LLM configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate LLM configuration")

@app.delete("/api/llm/configurations/{name}")
async def delete_llm_configuration(name: str):
    """Delete an LLM configuration."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = db.delete_llm_configuration(user_id, name)
        if success:
            return {"message": f"LLM configuration '{name}' deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete LLM configuration")
    except Exception as e:
        logger.error(f"Failed to delete LLM configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete LLM configuration")

@app.post("/api/llm/configurations/initialize")
async def initialize_default_llm_configurations():
    """Initialize default LLM configurations for the current user."""
    try:
        user_id = user_id_resolver.get_default_user_id()
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = db.create_default_llm_configurations(user_id)
        if success:
            return {"message": "Default LLM configurations created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create default LLM configurations")
    except Exception as e:
        logger.error(f"Failed to initialize LLM configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize LLM configurations")

# Backlog Jobs Management Endpoints
@app.get("/api/backlog/jobs")
async def get_backlog_jobs(
    user_email: str,
    exclude_test_generated: bool = True,
    exclude_failed: bool = True,
    exclude_deleted: bool = True
):
    """Get backlog jobs for a user."""
    try:
        # Call the database method with limit of 6 for recent projects
        jobs = db.get_backlog_jobs(
            user_email=user_email, 
            exclude_test_generated=exclude_test_generated, 
            exclude_failed=exclude_failed, 
            exclude_deleted=exclude_deleted,
            limit=6
        )
        return jobs
    except Exception as e:
        logger.error(f"Failed to get backlog jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backlog jobs: {str(e)}")

@app.delete("/api/backlog/jobs/{job_id}")
async def delete_backlog_job(job_id: int):
    """Delete a backlog job."""
    try:
        success = db.delete_backlog_job(job_id)
        if success:
            return {"status": "success", "message": f"Job {job_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        logger.error(f"Failed to delete backlog job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

# Domain Management Endpoints
@app.get("/api/domains")
async def get_domains():
    """Get all available domains."""
    logger.info("Domains API endpoint called")
    try:
        # Direct database query
        import sqlite3
        db_path = "backlog_jobs.db"
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, domain_key, display_name, description, is_active
                FROM domains 
                WHERE is_active = 1 
                ORDER BY display_name
            ''')
            domains = [dict(row) for row in cursor.fetchall()]
            
        logger.info(f"Successfully retrieved {len(domains)} domains from database")
        return domains
    except Exception as e:
        logger.error(f"Failed to get domains: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Always return some domains to prevent empty dropdown
        fallback_domains = [
            {"id": 1, "domain_key": "technology", "display_name": "Technology", "description": "Software development and technology projects", "is_active": 1},
            {"id": 2, "domain_key": "healthcare", "display_name": "Healthcare", "description": "Healthcare and medical technology", "is_active": 1},
            {"id": 3, "domain_key": "finance", "display_name": "Finance", "description": "Financial services and fintech", "is_active": 1},
            {"id": 4, "domain_key": "retail", "display_name": "Retail", "description": "E-commerce and retail solutions", "is_active": 1},
            {"id": 5, "domain_key": "education", "display_name": "Education", "description": "Educational technology and learning platforms", "is_active": 1},
            {"id": 6, "domain_key": "manufacturing", "display_name": "Manufacturing", "description": "Manufacturing and industrial automation", "is_active": 1},
            {"id": 7, "domain_key": "government", "display_name": "Government", "description": "Government and public sector solutions", "is_active": 1}
        ]
        logger.info(f"Returning {len(fallback_domains)} fallback domains")
        return fallback_domains

@app.post("/api/domains/detect")
async def detect_domain(request: dict):
    """Detect domain from text using AI."""
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Import domain detection utility
        try:
            from utils.domain_detector import DomainDetector
            detector = DomainDetector()
            detected_domain = detector.detect_domain(text)
        except ImportError:
            # Fallback if domain_detector doesn't exist
            logger.warning("DomainDetector not available, using fallback")
            # Simple keyword-based detection
            text_lower = text.lower()
            if any(word in text_lower for word in ['technology', 'software', 'app', 'platform', 'system']):
                detected_domain = "technology"
            elif any(word in text_lower for word in ['finance', 'banking', 'payment', 'money']):
                detected_domain = "fintech"
            elif any(word in text_lower for word in ['health', 'medical', 'patient', 'doctor']):
                detected_domain = "healthcare"
            elif any(word in text_lower for word in ['retail', 'shopping', 'ecommerce', 'store']):
                detected_domain = "retail"
            else:
                detected_domain = "technology"  # Default
        
        return {"domain": detected_domain}
    except Exception as e:
        logger.error(f"Failed to detect domain: {e}")
        # Return a fallback domain instead of failing
        return {"domain": "technology"}

# Agent-Specific LLM Configuration Endpoints

class AgentLLMConfigRequest(BaseModel):
    agent_name: str
    provider: str
    model: str
    custom_model: Optional[str] = None
    preset: str = "balanced"

class AgentLLMConfigResponse(BaseModel):
    agent_name: str
    provider: str
    model: str
    preset: str
    is_active: bool

@app.get("/api/llm-configurations/{user_id}")
async def get_agent_llm_configurations(user_id: str):
    """Get all agent-specific LLM configurations for a user."""
    try:
        import sqlite3
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        # Get all active configurations for this user
        cursor.execute('''
            SELECT agent_name, provider, model, preset, is_active
            FROM llm_configurations 
            WHERE user_id = ? AND is_active = 1
            ORDER BY agent_name, updated_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        configurations = []
        for row in results:
            configurations.append({
                "agent_name": row[0] or "global",
                "provider": row[1],
                "model": row[2],
                "preset": row[3] or "balanced",
                "is_active": bool(row[4])
            })
        
        logger.info(f"Returning {len(configurations)} LLM configurations for user {user_id}: {configurations}")
        return {
            "success": True,
            "data": configurations  # Keep consistent with actual response format
        }
        
    except Exception as e:
        logger.error(f"Failed to get LLM configurations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm-configurations/{user_id}")
async def save_agent_llm_configurations(user_id: str, configurations: List[AgentLLMConfigRequest]):
    """Save agent-specific LLM configurations for a user."""
    try:
        import sqlite3
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        # Deactivate all existing configurations for this user
        cursor.execute('''
            UPDATE llm_configurations 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        
        # Insert or update new configurations
        for config in configurations:
            # Use custom_model if provided, otherwise use model
            final_model = config.custom_model if config.custom_model else config.model
            
            # Check if configuration exists
            cursor.execute('''
                SELECT id FROM llm_configurations 
                WHERE user_id = ? AND agent_name = ? AND provider = ?
            ''', (user_id, config.agent_name, config.provider))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute('''
                    UPDATE llm_configurations 
                    SET model = ?, preset = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (final_model, config.preset, existing[0]))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO llm_configurations 
                    (user_id, name, provider, model, agent_name, preset, is_active, is_default) 
                    VALUES (?, ?, ?, ?, ?, ?, 1, 0)
                ''', (
                    user_id,
                    f"{config.provider.title()} {final_model} ({config.agent_name})",
                    config.provider,
                    final_model,
                    config.agent_name,
                    config.preset
                ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved {len(configurations)} LLM configurations for user {user_id}")
        
        return {
            "success": True,
            "message": f"Saved {len(configurations)} LLM configurations",
            "data": {"user_id": user_id, "configurations_count": len(configurations)}
        }
        
    except Exception as e:
        logger.error(f"Failed to save LLM configurations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/llm-configurations/{user_id}")
async def reset_agent_llm_configurations(user_id: str):
    """Reset all LLM configurations for a user to defaults."""
    try:
        import sqlite3
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        # Deactivate all configurations for this user
        cursor.execute('''
            UPDATE llm_configurations 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Reset LLM configurations for user {user_id}")
        
        return {
            "success": True,
            "message": "LLM configurations reset to defaults",
            "data": {"user_id": user_id}
        }
        
    except Exception as e:
        logger.error(f"Failed to reset LLM configurations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Build Version Endpoint
@app.get("/api/build-version")
async def get_build_version():
    """Get current build version."""
    try:
        build_version = db.get_build_version()
        return {
            "build_version": build_version,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get build version: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get build version: {str(e)}")

# Retry Failed Uploads Endpoint
class RetryFailedUploadsRequest(BaseModel):
    job_id: str
    action: str = "retry"  # retry, summary, details, cleanup

@app.post("/api/retry-failed-uploads")
async def retry_failed_uploads(request: RetryFailedUploadsRequest):
    """Retry failed uploads for a staging job."""
    try:
        job_id = request.job_id
        action = request.action
        
        logger.info(f"Retry failed uploads requested for job {job_id}, action: {action}")
        
        # Import the retry tool module
        import subprocess
        import tempfile
        import os
        
        # Execute the retry tool
        retry_script = "tools/retry_failed_uploads.py"
        if not os.path.exists(retry_script):
            raise HTTPException(status_code=404, detail="Retry tool not found")
        
        # Execute the command
        cmd = [sys.executable, retry_script, job_id, action]
        logger.info(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Retry operation completed successfully",
                "output": result.stdout,
                "job_id": job_id,
                "action": action
            }
        else:
            logger.error(f"Retry failed with return code {result.returncode}: {result.stderr}")
            return {
                "success": False,
                "message": f"Retry operation failed",
                "error": result.stderr,
                "job_id": job_id,
                "action": action
            }
            
    except subprocess.TimeoutExpired:
        logger.error(f"Retry operation timed out for job {job_id}")
        raise HTTPException(status_code=408, detail="Retry operation timed out")
    except Exception as e:
        logger.error(f"Failed to retry uploads for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry uploads: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "unified_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to prevent multiprocessing issues
        log_level="info"
    ) 