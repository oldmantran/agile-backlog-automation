#!/usr/bin/env python3
"""
Check current Azure DevOps configuration
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config

def check_azure_config():
    """Check if Azure DevOps configuration is complete."""
    
    print("🔍 Checking Azure DevOps Configuration")
    print("=" * 50)
    
    # Check environment variables
    print("Environment Variables:")
    pat = os.getenv("AZURE_DEVOPS_PAT")
    org = os.getenv("AZURE_DEVOPS_ORG")
    project = os.getenv("AZURE_DEVOPS_PROJECT")
    
    print(f"  AZURE_DEVOPS_PAT: {'✅ Set' if pat else '❌ Not set'}")
    print(f"  AZURE_DEVOPS_ORG: {'✅ Set' if org else '❌ Not set'}")
    print(f"  AZURE_DEVOPS_PROJECT: {'✅ Set' if project else '❌ Not set'}")
    
    # Check config file
    print("\nConfiguration File:")
    try:
        config = Config()
        azure_config = config.get_setting('azure_devops', {})
        print(f"  Organization URL: {'✅ Set' if azure_config.get('organization_url') else '❌ Not set'}")
        print(f"  Project: {'✅ Set' if azure_config.get('project') else '❌ Not set'}")
        print(f"  Area Path: {'✅ Set' if azure_config.get('area_path') else '❌ Not set'}")
        print(f"  Iteration Path: {'✅ Set' if azure_config.get('iteration_path') else '❌ Not set'}")
    except Exception as e:
        print(f"  ❌ Error reading config: {e}")
    
    # Summary
    print("\nSummary:")
    has_env_pat = bool(pat)
    has_env_org = bool(org)
    has_env_project = bool(project)
    
    if has_env_pat and has_env_org and has_env_project:
        print("✅ Environment variables are configured")
        print("⚠️  You still need to provide area_path and iteration_path in the frontend")
    else:
        print("❌ Environment variables are missing")
        print("   Set AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG, and AZURE_DEVOPS_PROJECT")
    
    print("\nTo enable Azure DevOps integration, ensure:")
    print("1. Environment variables are set (or provide PAT in frontend)")
    print("2. Organization URL is provided in frontend")
    print("3. Project name is provided in frontend") 
    print("4. Area Path is provided in frontend (e.g., 'Real Estate')")
    print("5. Iteration Path is provided in frontend (e.g., 'Sprint 1')")

if __name__ == "__main__":
    check_azure_config() 