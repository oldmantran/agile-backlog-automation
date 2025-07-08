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
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from contextlib import asynccontextmanager

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from utils.logger import setup_logger

# Initialize logging
logger = setup_logger(__name__)

# Global storage for active jobs (in production, use Redis or database)
active_jobs: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("Starting Agile Backlog Automation API Server")
    
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)
    
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
    teamSize: int = Field(..., ge=1, le=50, description="Team size")
    timeline: str = Field(..., description="Project timeline")

class ProductVision(BaseModel):
    visionStatement: str = Field(..., description="Product vision statement")
    businessObjectives: List[str] = Field(..., description="Business objectives")
    successMetrics: List[str] = Field(..., description="Success metrics")
    targetAudience: str = Field(..., description="Target audience")

class AzureConfig(BaseModel):
    organizationUrl: str = Field(..., description="Azure DevOps organization URL")
    personalAccessToken: str = Field(..., description="Personal access token")
    project: str = Field(..., description="Azure DevOps project name")
    areaPath: str = Field(..., description="Area path")
    iterationPath: str = Field(..., description="Iteration path")

class CreateProjectRequest(BaseModel):
    basics: ProjectBasics
    vision: ProductVision
    azureConfig: AzureConfig

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
        active_jobs[job_id]["currentAction"] = "Initializing supervisor"
        active_jobs[job_id]["progress"] = 10
        
        # Initialize the workflow supervisor
        config = Config()
        supervisor = WorkflowSupervisor(config)
        
        # Extract project data
        project_data = project_info["data"]
        project_name = project_data["basics"]["name"]
        project_domain = project_data["basics"]["domain"]
        
        # Update progress
        active_jobs[job_id]["currentAgent"] = "supervisor"
        active_jobs[job_id]["currentAction"] = "Running epic strategist"
        active_jobs[job_id]["progress"] = 30
        
        # Run the workflow with project context
        context = {
            "project_type": project_domain,
            "project_name": project_name,
            "project_description": project_data["basics"]["description"],
            "team_size": project_data["basics"]["teamSize"],
            "timeline": project_data["basics"]["timeline"],
            "vision_statement": project_data["vision"]["visionStatement"],
            "business_objectives": project_data["vision"]["businessObjectives"],
            "target_audience": project_data["vision"]["targetAudience"],
            "azure_config": project_data["azureConfig"]
        }
        
        # Update progress
        active_jobs[job_id]["currentAction"] = "Generating backlog items"
        active_jobs[job_id]["progress"] = 60
        
        # Run the supervisor workflow
        results = await asyncio.to_thread(supervisor.run_workflow, context)
        
        # Update final progress
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["currentAction"] = "Backlog generation completed"
        active_jobs[job_id]["progress"] = 100
        active_jobs[job_id]["endTime"] = datetime.now()
        
        logger.info(f"Completed backlog generation for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in backlog generation job {job_id}: {str(e)}")
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["endTime"] = datetime.now()

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to prevent multiprocessing issues
        log_level="info"
    )
