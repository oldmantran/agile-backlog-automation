#!/usr/bin/env python3
"""
Simple Azure DevOps integration test.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator

def main():
    print("🔍 Testing Azure DevOps Integration...")
    
    # Load config
    config = Config()
    integrator = AzureDevOpsIntegrator(config)
    
    print(f"Organization: {integrator.organization}")
    print(f"Project: {integrator.project}")
    print(f"Enabled: {integrator.enabled}")
    print(f"Org Base URL: {integrator.org_base_url}")
    print(f"Project Base URL: {integrator.project_base_url}")
    
    if integrator.enabled:
        print("\n🌐 Testing connection...")
        try:
            success = integrator.test_connection()
            if success:
                print("✅ Azure DevOps connection successful!")
            else:
                print("❌ Connection failed")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    else:
        print("❌ Integration not enabled")

if __name__ == "__main__":
    main()
