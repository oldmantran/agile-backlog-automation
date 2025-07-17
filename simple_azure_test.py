#!/usr/bin/env python3
"""
Simple test script to verify Azure integration logic
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_azure_config_detection():
    """Test the Azure configuration detection logic."""
    
    print("🧪 Testing Azure Configuration Detection")
    print("=" * 50)
    
    # Test project data
    project_data = {
        "azureConfig": {
            "organizationUrl": "https://dev.azure.com/c4workx",
            "project": "Backlog Automation",
            "areaPath": "Real Estate",
            "iterationPath": "Sprint 2025-07",
            "personalAccessToken": "",  # Will be loaded from environment
            "enabled": False  # Test auto-enable logic
        }
    }
    
    # Extract Azure config
    azure_config = project_data.get("azureConfig", {})
    azure_integration_enabled = azure_config.get("enabled", False)
    
    # Azure DevOps parameters
    organization_url = azure_config.get("organizationUrl")
    project = azure_config.get("project")
    personal_access_token = azure_config.get("personalAccessToken") or os.getenv("AZURE_DEVOPS_PAT")
    area_path = azure_config.get("areaPath")
    iteration_path = azure_config.get("iterationPath")
    
    print(f"🔍 Azure DevOps Configuration Analysis:")
    print(f"   azure_integration_enabled (from config): {azure_integration_enabled}")
    print(f"   organization_url: {organization_url}")
    print(f"   project: {project}")
    print(f"   personal_access_token: {'Set' if personal_access_token else 'Not set'}")
    print(f"   area_path: {area_path}")
    print(f"   iteration_path: {iteration_path}")
    
    # Check if any Azure config is provided (alternative detection method)
    has_any_azure_config = any([
        organization_url,
        project,
        personal_access_token,
        area_path,
        iteration_path
    ])
    print(f"   has_any_azure_config: {has_any_azure_config}")
    
    # Validate Azure DevOps configuration
    if azure_integration_enabled:
        if not all([organization_url, project, personal_access_token]):
            print(f"❌ Azure integration enabled but missing required fields")
            azure_integration_enabled = False
    elif has_any_azure_config:
        print(f"⚠️ Azure config provided but integration not explicitly enabled")
        # Auto-enable if we have the required fields
        if all([organization_url, project, personal_access_token, area_path, iteration_path]):
            print(f"✅ Auto-enabling Azure integration (all required fields present)")
            azure_integration_enabled = True
        else:
            print(f"❌ Cannot auto-enable Azure integration (missing required fields)")
    
    print(f"   Final azure_integration_enabled: {azure_integration_enabled}")
    
    return azure_integration_enabled

def test_environment_variables():
    """Test environment variable configuration."""
    
    print("\n🔧 Testing Environment Variables")
    print("=" * 50)
    
    pat = os.getenv("AZURE_DEVOPS_PAT")
    org = os.getenv("AZURE_DEVOPS_ORG")
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    
    print(f"  AZURE_DEVOPS_PAT: {'✅ Set' if pat else '❌ Not set'}")
    print(f"  AZURE_DEVOPS_ORG: {'✅ Set' if org else '❌ Not set'}")
    print(f"  AZURE_DEVOPS_PROJECT: {'✅ Set' if project else '❌ Not set'}")
    
    return bool(pat and org and project)

def test_supervisor_initialization():
    """Test supervisor initialization with Azure config."""
    
    print("\n🔧 Testing Supervisor Initialization")
    print("=" * 50)
    
    try:
        from supervisor.supervisor import WorkflowSupervisor
        
        # Test supervisor initialization
        supervisor = WorkflowSupervisor(
            organization_url="https://dev.azure.com/c4workx",
            project="Backlog Automation",
            personal_access_token=os.getenv("AZURE_DEVOPS_PAT"),
            area_path="Real Estate",
            iteration_path="Sprint 2025-07",
            job_id="test_job_001"
        )
        
        print("✅ WorkflowSupervisor initialized successfully")
        print(f"   Azure integrator available: {supervisor.azure_integrator is not None}")
        
        if supervisor.azure_integrator:
            print("✅ Azure DevOps integration should work")
            return True
        else:
            print("❌ Azure DevOps integration not available")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize WorkflowSupervisor: {e}")
        return False

if __name__ == "__main__":
    print("Starting Azure integration logic test...")
    
    # Test 1: Configuration detection
    config_ok = test_azure_config_detection()
    
    # Test 2: Environment variables
    env_ok = test_environment_variables()
    
    # Test 3: Supervisor initialization
    supervisor_ok = test_supervisor_initialization()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Configuration Detection: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"   Supervisor Initialization: {'✅ PASS' if supervisor_ok else '❌ FAIL'}")
    
    if config_ok and env_ok and supervisor_ok:
        print("\n🎉 All tests passed! Azure integration should work.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
    
    print("\nTest completed.") 