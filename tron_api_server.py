#!/usr/bin/env python3
"""
Tron-themed Backlog Automation API Server
Handles frontend requests and executes Python scripts
"""

import os
import sys
import json
import subprocess
import threading
import time
import asyncio
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn
import logging
import queue

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import supervisor and config
from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from utils.logger import setup_logger

# Initialize logging
logger = setup_logger(__name__)

app = FastAPI(title="Backlog Automation API", version="2.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend build
if (project_root / "frontend" / "build").exists():
    app.mount("/static", StaticFiles(directory=project_root / "frontend" / "build" / "static"), name="static")

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

# Start log distribution task on server startup
async def startup_event():
    """Start background tasks on server startup"""
    asyncio.create_task(distribute_logs())

# Add startup event to app
app.add_event_handler("startup", startup_event)

# Models
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

# Project and backlog generation models
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

# Global storage for active jobs
active_jobs: Dict[str, Dict[str, Any]] = {}

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

# API Routes

@app.get("/")
async def serve_frontend():
    """Serve the frontend application"""
    frontend_build = project_root / "frontend" / "build" / "index.html"
    if frontend_build.exists():
        with open(frontend_build, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return {"message": "Tron Backlog Automation API v2.0", "status": "Backend running, frontend not built"}

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

# Project and Backlog Generation Endpoints

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
                "startTime": job_data["startTime"].isoformat() if isinstance(job_data["startTime"], datetime) else job_data["startTime"],
                "endTime": job_data["endTime"].isoformat() if job_data["endTime"] and isinstance(job_data["endTime"], datetime) else job_data["endTime"]
            }
            for job_data in active_jobs.values()
        ]
    }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details by ID."""
    project_file = Path("output") / f"project_{project_id}.json"
    if not project_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    with open(project_file, 'r') as f:
        project_info = json.load(f)
    
    return {"success": True, "data": project_info}

@app.get("/api/projects/{project_id}/backlog")
async def get_project_backlog(project_id: str):
    """Get generated backlog for a project."""
    backlog_file = Path("output") / f"backlog_{project_id}.json"
    if not backlog_file.exists():
        raise HTTPException(status_code=404, detail="Backlog not found")
    
    with open(backlog_file, 'r') as f:
        backlog_data = json.load(f)
    
    return {"success": True, "data": backlog_data}

@app.post("/api/validate-azure")
async def validate_azure_connection(data: dict):
    """Validate Azure DevOps connection"""
    # This would implement actual Azure DevOps validation
    # For now, return success if all required fields are present
    required_fields = ["pat", "org", "project"]
    
    if all(data.get(field) for field in required_fields):
        return {"status": "success", "message": "Azure DevOps connection validated"}
    else:
        raise HTTPException(status_code=400, detail="Missing required Azure DevOps configuration")

@app.post("/api/validate-ai")
async def validate_ai_connection(data: dict):
    """Validate AI provider connection"""
    provider = data.get("provider")
    api_key = data.get("apiKey")
    
    if provider and api_key:
        return {"status": "success", "message": f"{provider.upper()} connection validated"}
    else:
        raise HTTPException(status_code=400, detail="Missing AI provider configuration")

@app.get("/api/workitems")
async def get_work_items():
    """Get work items from Azure DevOps"""
    # Mock data for demonstration
    # In a real implementation, this would call Azure DevOps API
    mock_items = [
        WorkItem(1, "User login functionality", "User Story", "Active", "MyProject\\Web", "john.doe@company.com"),
        WorkItem(2, "Database connection setup", "Task", "New", "MyProject\\Backend", None),
        WorkItem(3, "API endpoint for user management", "Feature", "In Progress", "MyProject\\API", "jane.smith@company.com"),
        WorkItem(4, "Unit tests for authentication", "Test Case", "New", "MyProject\\Testing", None),
        WorkItem(5, "Deploy to staging environment", "Bug", "Resolved", "MyProject\\DevOps", "deploy.bot@company.com")
    ]
    
    return [asdict(item) for item in mock_items]

@app.post("/api/workitems/delete")
async def delete_work_items(data: dict):
    """Delete selected work items"""
    item_ids = data.get("itemIds", [])
    
    # In a real implementation, this would delete items via Azure DevOps API
    # For now, simulate the process
    
    if not item_ids:
        raise HTTPException(status_code=400, detail="No items selected for deletion")
    
    # Simulate processing time
    time.sleep(2)
    
    return {"status": "success", "message": f"Deleted {len(item_ids)} work items", "deletedIds": item_ids}

@app.get("/api/testcases")
async def get_test_cases():
    """Get test cases from Azure DevOps"""
    # Mock data
    mock_cases = [
        {"id": 101, "title": "Login with valid credentials", "state": "Active", "areaPath": "MyProject\\Testing", "testSuite": "Authentication Tests"},
        {"id": 102, "title": "Login with invalid password", "state": "Active", "areaPath": "MyProject\\Testing", "testSuite": "Authentication Tests"},
        {"id": 103, "title": "Password reset functionality", "state": "New", "areaPath": "MyProject\\Testing", "testSuite": "User Management"}
    ]
    return mock_cases

@app.get("/api/testsuites")
async def get_test_suites():
    """Get test suites from Azure DevOps"""
    mock_suites = [
        {"id": 201, "name": "Authentication Tests", "testCaseCount": 15},
        {"id": 202, "name": "User Management", "testCaseCount": 8},
        {"id": 203, "name": "API Integration", "testCaseCount": 12}
    ]
    return mock_suites

@app.get("/api/testplans")
async def get_test_plans():
    """Get test plans from Azure DevOps"""
    mock_plans = [
        {"id": 301, "name": "Sprint 1 Testing", "state": "Active", "testSuiteCount": 3},
        {"id": 302, "name": "Release Validation", "state": "Completed", "testSuiteCount": 5},
        {"id": 303, "name": "Performance Testing", "state": "In Progress", "testSuiteCount": 2}
    ]
    return mock_plans

@app.post("/api/test/delete")
async def delete_test_items(data: dict):
    """Delete selected test cases, suites, and plans"""
    test_cases = data.get("testCases", [])
    test_suites = data.get("testSuites", [])
    test_plans = data.get("testPlans", [])
    
    total_items = len(test_cases) + len(test_suites) + len(test_plans)
    
    if total_items == 0:
        raise HTTPException(status_code=400, detail="No items selected for deletion")
    
    # Simulate processing time
    time.sleep(3)
    
    return {"status": "success", "message": f"Deleted {total_items} test items"}

@app.get("/api/sweeper/config")
async def get_sweeper_config():
    """Get backlog sweeper configuration"""
    return {
        "targetArea": "MyProject",
        "iterationPath": "",
        "includeAcceptanceCriteria": True,
        "includeTaskDecomposition": True,
        "maxItemsPerRun": 50
    }

@app.post("/api/sweeper/config")
async def save_sweeper_config(config: SweeperConfig):
    """Save backlog sweeper configuration"""
    # In a real implementation, this would save to a config file
    return {"status": "success", "message": "Sweeper configuration saved"}

@app.post("/api/sweeper/start")
async def start_sweeper(config: SweeperConfig, background_tasks: BackgroundTasks):
    """Start the backlog sweeper process"""
    global sweeper_status
    
    if sweeper_status["isRunning"]:
        raise HTTPException(status_code=400, detail="Sweeper is already running")
    
    # Reset status
    sweeper_status.update({
        "isRunning": True,
        "progress": 0,
        "currentItem": "",
        "processedItems": 0,
        "totalItems": 20,  # Mock total
        "errors": [],
        "completedActions": [],
        "logs": []
    })
    
    # Start background task
    background_tasks.add_task(run_sweeper_background, config)
    
    return {"status": "success", "message": "Backlog sweeper started"}

@app.post("/api/sweeper/stop")
async def stop_sweeper():
    """Stop the backlog sweeper process"""
    global sweeper_status
    sweeper_status["isRunning"] = False
    return {"status": "success", "message": "Backlog sweeper stopped"}

@app.get("/api/sweeper/status")
async def get_sweeper_status():
    """Get current sweeper status"""
    return sweeper_status

async def run_sweeper_background(config: SweeperConfig):
    """Background task to simulate sweeper execution"""
    global sweeper_status
    
    try:
        # Simulate sweeper process
        items = [f"Work Item {i+1}" for i in range(sweeper_status["totalItems"])]
        
        for i, item in enumerate(items):
            if not sweeper_status["isRunning"]:
                break
                
            sweeper_status["currentItem"] = item
            sweeper_status["processedItems"] = i + 1
            sweeper_status["progress"] = ((i + 1) / len(items)) * 100
            
            # Simulate processing time
            time.sleep(2)
            
            # Add to completed actions
            action = f"Enhanced {item} with acceptance criteria"
            sweeper_status["completedActions"].append(action)
            sweeper_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] {action}")
            
            # Simulate occasional error
            if i % 10 == 9:  # Every 10th item
                error = f"Warning: {item} missing description"
                sweeper_status["errors"].append(error)
                sweeper_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] ERROR: {error}")
        
        sweeper_status["isRunning"] = False
        sweeper_status["currentItem"] = "Completed"
        
    except Exception as e:
        sweeper_status["isRunning"] = False
        sweeper_status["errors"].append(f"Sweeper failed: {str(e)}")

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

@app.post("/api/start-application")
async def start_application():
    """Start the main application (used by executable launcher)"""
    return {"status": "success", "message": "Application started successfully"}

def open_browser():
    """Open the browser after a short delay to ensure server is ready"""
    time.sleep(2)  # Wait 2 seconds for server to start
    url = "http://localhost:8000"
    try:
        webbrowser.open(url)
        print(f"🌐 Opened browser to: {url}")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"🌐 Please manually open: {url}")

if __name__ == "__main__":
    print("🎮 Starting Tron Backlog Automation API Server...")
    print("🌐 Frontend will be available at: http://localhost:8000")
    print("🔧 API documentation at: http://localhost:8000/docs")
    
    # Start browser opening in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    uvicorn.run(
        "tron_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
