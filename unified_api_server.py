#!/usr/bin/env python3
"""
Unified REST API Server for Agile Backlog Automation Frontend Integration.

This FastAPI server provides endpoints for the React frontend to interact
with the backend agents, workflow supervisor, and management tools.
Combines the best features from api_server.py and tron_api_server.py.
"""

import os
import sys
import json
import asyncio
import logging
import queue
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
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

# Global state for background processes
background_processes: Dict[str, subprocess.Popen] = {}
sweeper_status = {
    "isRunning": False,
    "progress": 0,
    "currentItem": "",
    "processedItems": 0,
    "totalItems": 0,
    "errors": [],
    "completedActions": [],
    "logs": []
}

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
            }
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
                "startTime": job_data["startTime"].isoformat() if isinstance(job_data["startTime"], datetime) else job_data["startTime"],
                "endTime": job_data["endTime"].isoformat() if job_data["endTime"] and isinstance(job_data["endTime"], datetime) else job_data["endTime"]
            }
            for job_data in active_jobs.values()
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
    print(f"[DEBUG] Starting backlog generation for job {job_id}")
    
    try:
        # Initialize job status
        active_jobs[job_id] = {
            "jobId": job_id,
            "projectId": project_info.get("id", "unknown"),
            "status": "running",
            "progress": 0,
            "currentAgent": "",
            "currentAction": "",
            "startTime": datetime.now(),
            "error": None,
            "endTime": None
        }
        
        print(f"[DEBUG] Job {job_id} initialized with status: {active_jobs[job_id]}")
        
        # Extract project data
        project_data = project_info.get("data", {})
        print(f"[DEBUG] Project data extracted: {list(project_data.keys()) if project_data else 'None'}")
        
        # Determine project domain
        project_domain = project_data.get("basics", {}).get("domain", "software development")
        project_name = project_data.get("basics", {}).get("name", "Unknown Project")
        print(f"[DEBUG] Project domain: {project_domain}, name: {project_name}")
        
        # Check Azure DevOps integration
        azure_config = project_data.get("azureConfig", {})
        azure_integration_enabled = azure_config.get("enabled", False)
        print(f"[DEBUG] Azure integration enabled: {azure_integration_enabled}")
        
        if azure_integration_enabled:
            print(f"[DEBUG] Azure config: {azure_config}")
            organization_url = azure_config.get("organizationUrl")
            project = azure_config.get("project")
            personal_access_token = azure_config.get("personalAccessToken")
            area_path = azure_config.get("areaPath")
            iteration_path = azure_config.get("iterationPath")
            
            print(f"[DEBUG] Azure params - org:{organization_url}, project:{project}, area:{area_path}, iteration:{iteration_path}")
            
            if not all([organization_url, project, personal_access_token]):
                logger.warning("Azure DevOps integration disabled: missing required configuration")
                print(f"[DEBUG] Azure DevOps integration disabled: missing required configuration")
                azure_integration_enabled = False
        else:
            organization_url = None
            project = None
            personal_access_token = None
            area_path = None
            iteration_path = None
            print(f"[DEBUG] Azure integration disabled: 'project'")
        
        # Initialize supervisor
        print(f"[DEBUG] About to initialize WorkflowSupervisor...")
        print(f"[DEBUG] WorkflowSupervisor parameters:")
        print(f"[DEBUG]   - organization_url: {organization_url} (type: {type(organization_url)})")
        print(f"[DEBUG]   - project: {project} (type: {type(project)})")
        print(f"[DEBUG]   - personal_access_token: {'***' if personal_access_token else None} (type: {type(personal_access_token)})")
        print(f"[DEBUG]   - area_path: {area_path} (type: {type(area_path)})")
        print(f"[DEBUG]   - iteration_path: {iteration_path} (type: {type(iteration_path)})")
        print(f"[DEBUG]   - job_id: {job_id} (type: {type(job_id)})")
        print(f"[DEBUG]   - config_path: None (not provided)")
        
        try:
            supervisor = WorkflowSupervisor(
                organization_url=organization_url,
                project=project,
                personal_access_token=personal_access_token,
                area_path=area_path,
                iteration_path=iteration_path,
                job_id=job_id
            )
            print(f"[DEBUG] WorkflowSupervisor initialized successfully")
        except Exception as e:
            print(f"[DEBUG] Exception during WorkflowSupervisor initialization: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
        # Progress callback function
        def progress_callback(progress: int, action: str):
            print(f"[DEBUG] Progress callback: {progress}% - {action}")
            active_jobs[job_id]["progress"] = progress
            active_jobs[job_id]["currentAction"] = action
        
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
        print(f"[DEBUG] Context prepared: {list(context.keys())}")
        
        # Set up the project context for the supervisor
        print(f"[DEBUG] About to configure project context...")
        try:
            supervisor.configure_project_context(project_domain, context)
            print(f"[DEBUG] Project context configured successfully")
        except Exception as e:
            print(f"[DEBUG] Exception during project context configuration: {e}")
            import traceback
            print(traceback.format_exc())
            raise
        
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
        print(f"[DEBUG] Product vision created (length: {len(product_vision)})")
        
        # Run the supervisor workflow with progress callback
        print(f"[DEBUG] About to execute workflow...")
        try:
            results = supervisor.execute_workflow(
                product_vision, 
                save_outputs=True, 
                integrate_azure=azure_integration_enabled,
                progress_callback=progress_callback
            )
            print(f"[DEBUG] Workflow executed successfully")
        except Exception as e:
            import traceback
            logger.error(f"Workflow execution failed: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"[DEBUG] Workflow execution failed: {str(e)}")
            print(traceback.format_exc())
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = str(e)
            active_jobs[job_id]["endTime"] = datetime.now()
            return
        
        # Update final progress
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["endTime"] = datetime.now()
        active_jobs[job_id]["results"] = results
        
        logger.info(f"Backlog generation completed for job {job_id}")
        print(f"[DEBUG] Backlog generation completed for job {job_id}")
        
    except Exception as e:
        import traceback
        logger.error(f"Error in backlog generation job {job_id}: {e}")
        logger.error(traceback.format_exc())
        print(f"[DEBUG] Error in backlog generation job {job_id}: {e}")
        print(traceback.format_exc())
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["endTime"] = datetime.now()

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