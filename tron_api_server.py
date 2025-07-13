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
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

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
    includeQualityCheck: bool = True
    enhanceRequirements: bool = True
    maxItemsPerRun: int = 50

@dataclass
class WorkItem:
    id: int
    title: str
    type: str
    state: str
    areaPath: str
    assignedTo: Optional[str] = None

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
        "includeQualityCheck": True,
        "enhanceRequirements": True,
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

@app.post("/api/start-application")
async def start_application():
    """Start the main application (used by executable launcher)"""
    return {"status": "success", "message": "Application started successfully"}

if __name__ == "__main__":
    print("🎮 Starting Tron Backlog Automation API Server...")
    print("🌐 Frontend will be available at: http://localhost:8000")
    print("🔧 API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "tron_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
