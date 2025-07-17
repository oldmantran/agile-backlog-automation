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
import queue
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
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
    from db import add_backlog_job
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

# Global storage for active jobs (in production, use Redis or database)
active_jobs: Dict[str, Dict[str, Any]] = {}

# WebSocket connections for log streaming
log_connections: List[WebSocket] = []
log_queue = queue.Queue()

# Global state for background processes
background_processes: Dict[str, subprocess.Popen] = {}
sweeper_status = {"isRunning": False, "progress": 0, "currentItem": "", "processedItems": 0, "totalItems": 0, "errors": [], "completedActions": [], "logs": []}

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

# Test WebSocket logging
logger.info("🔧 WebSocket log handler initialized and attached to loggers")

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
    logger.info("Starting Unified Agile Backlog Automation API Server")
    
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)
    
    # Start log distribution task
    asyncio.create_task(distribute_logs())
    
    logger.info("Unified API Server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Unified API Server")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Unified Agile Backlog Automation API",
    description="REST API for managing agile backlog generation workflows and management tools",
    version="2.0.0",
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

# Serve static files from frontend build
project_root = Path(__file__).parent
if (project_root / "frontend" / "build").exists():
    app.mount("/static", StaticFiles(directory=project_root / "frontend" / "build" / "static"), name="static")

# Pydantic models for request/response
class ConfigData(BaseModel):
    azureDevOpsPat: str = ""
    azureDevOpsOrg: str = ""
    azureDevOpsProject: str = ""
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
        "grokApiKey": env_config.get("GROK_API_KEY", "")
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
        "GROK_API_KEY": config.grokApiKey
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
        
        # Add to background tasks
        background_tasks.add_task(run_backlog_generation, job_id, project_info)
        logger.info(f"✅ Background task added for job: {job_id}")
        
        response_data = {"jobId": job_id}
        logger.info(f"📤 Returning response: {response_data}")
        
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
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = active_jobs[job_id]
    
    # Convert job_status to match GenerationStatus model
    generation_status = {
        "jobId": job_status.get("jobId", job_id),
        "projectId": job_status.get("projectId", "unknown"),
        "status": job_status.get("status", "unknown"),
        "progress": job_status.get("progress", 0),
        "currentAgent": job_status.get("currentAgent", ""),
        "currentAction": job_status.get("currentAction", ""),
        "startTime": job_status.get("startTime"),
        "endTime": job_status.get("endTime"),
        "error": job_status.get("error")
    }
    
    logger.info(f"📊 Returning status for job {job_id}: {generation_status}")
    
    return {
        "success": True,
        "data": generation_status
    }

@app.get("/api/jobs")
async def get_all_jobs():
    """Get all active and recent jobs."""
    return {
        "success": True,
        "data": [
            {
                **job_data,
                "startTime": job_data["startTime"].isoformat() if isinstance(job_data["startTime"], datetime) else job_data["startTime"],
                "endTime": job_data["endTime"].isoformat() if job_data["endTime"] and isinstance(job_data["endTime"], datetime) else job_data["endTime"]
            }
            for job_data in active_jobs.values()
        ]
    }

@app.post("/api/jobs/add")
async def add_job(job_data: dict):
    """Add a job to the active jobs tracking."""
    try:
        job_id = job_data.get("jobId")
        if not job_id:
            raise HTTPException(status_code=400, detail="jobId is required")
        
        active_jobs[job_id] = job_data
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

async def run_backlog_generation(job_id: str, project_info: Dict[str, Any]):
    """Background task to run the actual backlog generation."""
    logger.info(f"Starting backlog generation for job {job_id}")
    
    try:
        # Initialize job status
        active_jobs[job_id] = {
            "jobId": job_id,
            "projectId": project_info.get("id", "unknown"),
            "status": "running",
            "progress": 0,
            "currentAgent": "Supervisor",
            "currentAction": "Initializing workflow...",
            "startTime": datetime.now(),
            "error": None,
            "endTime": None
        }
        logger.info(f"🚀 Job {job_id} initialized and ready for execution")
        
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
        
        # Initialize supervisor
        try:
            logger.info(f"🔧 Initializing WorkflowSupervisor for job {job_id} with Azure config:")
            logger.info(f"   organization_url: {organization_url}")
            logger.info(f"   project: {project_name}")
            logger.info(f"   area_path: {area_path}")
            logger.info(f"   iteration_path: {iteration_path}")
            
            supervisor = WorkflowSupervisor(
                organization_url=organization_url,
                project=project_name,
                personal_access_token=personal_access_token,
                area_path=area_path,
                iteration_path=iteration_path,
                job_id=job_id
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
            
        except Exception as e:
            error_msg = f"Failed to initialize WorkflowSupervisor: {str(e)}"
            logger.error(f"❌ {error_msg}")
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = error_msg
            active_jobs[job_id]["endTime"] = datetime.now()
            return {"error": error_msg}
        
        # Progress callback
        def progress_callback(progress: int, action: str):
            if job_id in active_jobs:
                active_jobs[job_id]["progress"] = progress
                active_jobs[job_id]["currentAction"] = action
                active_jobs[job_id]["currentAgent"] = action.split()[0] if action else "Supervisor"  # Extract agent name from action
                active_jobs[job_id]["status"] = "running"  # Ensure status is running during execution
                logger.info(f"📊 Progress update for job {job_id}: {progress}% - {action}")

        # Prepare context
        context = {
            "project_name": project_name,
            "project_domain": project_domain,
            "azure_integration_enabled": azure_integration_enabled,
            "azure_config": azure_config
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
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = error_msg
            active_jobs[job_id]["endTime"] = datetime.now()
            return {"error": error_msg}

        # Create product vision
        vision_data = project_data.get("vision", {})
        product_vision = f"""
Project: {project_name}
Domain: {project_domain}

Vision Statement:
{vision_data.get('visionStatement', 'No vision statement provided')}

Key Features:
{vision_data.get('keyFeatures', 'No key features specified')}

Target Users:
{vision_data.get('targetUsers', 'No target users specified')}

Success Criteria:
{vision_data.get('successCriteria', 'No success criteria specified')}
""".strip()

        # Execute workflow
        try:
            logger.info(f"🚀 Starting workflow execution for job {job_id}")
            logger.info(f"   integrate_azure: {azure_integration_enabled}")
            logger.info(f"   product_vision length: {len(product_vision)} characters")
            logger.info(f"   save_outputs: True")
            
            results = supervisor.execute_workflow(
                product_vision,
                save_outputs=True,
                integrate_azure=azure_integration_enabled,
                progress_callback=progress_callback
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
            active_jobs[job_id]["status"] = "completed"
            active_jobs[job_id]["progress"] = 100
            active_jobs[job_id]["currentAction"] = "Completed"
            active_jobs[job_id]["endTime"] = datetime.now()

            return {"job_id": job_id, "status": "completed", "results": results}

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = error_msg
            active_jobs[job_id]["endTime"] = datetime.now()
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error in run_backlog_generation: {str(e)}"
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = error_msg
            active_jobs[job_id]["endTime"] = datetime.now()
        logger.error(error_msg)
        return {"error": error_msg}

# WebSocket and Application Management Endpoints
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for streaming server logs to the frontend"""
    await websocket.accept()
    log_connections.append(websocket)
    
    try:
        await websocket.send_json({
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "🌐 Connected to unified server log stream",
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
        "message": "📡 Direct queue test message from unified server",
        "module": "test_api"
    }
    log_queue.put(test_message)
    
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

if __name__ == "__main__":
    uvicorn.run(
        "unified_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to prevent multiprocessing issues
        log_level="info"
    ) 