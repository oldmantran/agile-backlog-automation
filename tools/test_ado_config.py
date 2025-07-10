#!/usr/bin/env python3
"""
Test Azure DevOps configuration and integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator

def test_ado_config():
    """Test if Azure DevOps is properly configured."""
    print("🔍 Testing Azure DevOps Configuration")
    print("=" * 50)
    
    try:
        # Check environment variables
        ado_org = os.getenv('AZURE_DEVOPS_ORG')
        ado_project = os.getenv('AZURE_DEVOPS_PROJECT') 
        ado_pat = os.getenv('AZURE_DEVOPS_PAT')
        
        print(f"🔗 AZURE_DEVOPS_ORG: {'✅ Set' if ado_org else '❌ Not set'}")
        print(f"📋 AZURE_DEVOPS_PROJECT: {'✅ Set' if ado_project else '❌ Not set'}")
        print(f"🔑 AZURE_DEVOPS_PAT: {'✅ Set' if ado_pat else '❌ Not set'}")
        
        if not all([ado_org, ado_project, ado_pat]):
            print("\n❌ Azure DevOps not fully configured")
            print("💡 Configure .env file with your Azure DevOps settings")
            return False
            
        # Test configuration loading
        config = Config()
        print("✅ Config loaded successfully")
        
        # Test ADO integrator initialization with existing area path
        # Using "Grit" area path since it has existing work items
        ado_integrator = AzureDevOpsIntegrator(
            organization_url=f"https://dev.azure.com/{ado_org}",
            project=ado_project,
            personal_access_token=ado_pat,
            area_path="Grit",  # Use existing area path with work items
            iteration_path=ado_project  # Use project root as iteration path
        )
        
        print(f"✅ ADO Integrator initialized")
        print(f"   Organization: {ado_org}")
        print(f"   Project: {ado_project}")
        print(f"   Enabled: {ado_integrator.enabled}")
        
        if ado_integrator.test_client:
            print("✅ Test Management client available")
            
            # Test API connectivity (simple call)
            try:
                # This is a simple API call to test connectivity
                existing_plans = ado_integrator.test_client._get_test_plans()
                print(f"✅ ADO API connectivity working - found {len(existing_plans.get('value', []))} existing test plans")
                return True
            except Exception as e:
                print(f"❌ ADO API connectivity failed: {e}")
                return False
        else:
            print("❌ Test Management client not available")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ado_config()
    if success:
        print("\n🎉 Azure DevOps integration is ready!")
        print("✅ End-to-end testing should create visible test artifacts in ADO")
    else:
        print("\n⚠️  Azure DevOps integration needs configuration")
        print("❌ End-to-end testing will use mock mode only")
    
    exit(0 if success else 1)
