#!/usr/bin/env python3
"""
Run Backlog Sweeper against Backlog Automation project for area path RE-34B
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
from agents.backlog_sweeper_agent import BacklogSweeperAgent

def run_backlog_sweeper():
    """Run backlog sweeper against Backlog Automation project for area path RE-34B"""
    
    print("🔍 Starting Backlog Sweeper for Backlog Automation Project")
    print("=" * 60)
    
    try:
        # Load configuration
        config = Config()
        
        # Azure DevOps configuration for Backlog Automation project
        organization_url = "https://dev.azure.com/c4workx"
        project = "Backlog Automation"
        area_path = "RE-34B"  # Target area path
        iteration_path = "Sprint 2025-07"  # Default iteration
        
        # Get PAT from environment
        personal_access_token = os.getenv("AZURE_DEVOPS_PAT")
        if not personal_access_token:
            print("❌ Error: AZURE_DEVOPS_PAT environment variable not set")
            return False
        
        print(f"📋 Configuration:")
        print(f"   Organization: {organization_url}")
        print(f"   Project: {project}")
        print(f"   Area Path: {area_path}")
        print(f"   Iteration Path: {iteration_path}")
        print()
        
        # Initialize Azure DevOps integrator
        print("🔧 Initializing Azure DevOps integrator...")
        ado_client = AzureDevOpsIntegrator(
            organization_url=organization_url,
            project=project,
            personal_access_token=personal_access_token,
            area_path=area_path,
            iteration_path=iteration_path
        )
        
        if not ado_client.enabled:
            print("❌ Error: Azure DevOps integrator not enabled")
            return False
        
        print("✅ Azure DevOps integrator initialized successfully")
        print()
        
        # Initialize backlog sweeper agent
        print("🔧 Initializing Backlog Sweeper Agent...")
        sweeper = BacklogSweeperAgent(ado_client, config=config.settings)
        print("✅ Backlog Sweeper Agent initialized successfully")
        print()
        
        # Run the sweep
        print("🚀 Starting backlog sweep...")
        start_time = datetime.now()
        
        # Run comprehensive sweep
        report = sweeper.run_sweep()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Backlog sweep completed in {duration:.2f} seconds")
        print()
        
        # Process and display results
        print("📊 Sweep Results:")
        print("=" * 40)
        
        # Extract summary from report
        summary = report.get('summary', {})
        total_discrepancies = summary.get('total_discrepancies', 0)
        high_priority_count = summary.get('high_priority_count', 0)
        medium_priority_count = summary.get('medium_priority_count', 0)
        low_priority_count = summary.get('low_priority_count', 0)
        
        print(f"📈 Total Discrepancies Found: {total_discrepancies}")
        print(f"🚨 High Priority Issues: {high_priority_count}")
        print(f"⚠️  Medium Priority Issues: {medium_priority_count}")
        print(f"ℹ️  Low Priority Issues: {low_priority_count}")
        print()
        
        # Display agent assignments
        agent_assignments = report.get('agent_assignments', {})
        if agent_assignments:
            print("🤖 Issues by Suggested Agent:")
            for agent_name, discrepancies in agent_assignments.items():
                if discrepancies:
                    print(f"   {agent_name}: {len(discrepancies)} issues")
        print()
        
        # Display recommended actions
        recommended_actions = report.get('recommended_actions', [])
        if recommended_actions:
            print("💡 Recommended Actions:")
            for i, action in enumerate(recommended_actions[:10], 1):  # Show first 10
                print(f"   {i}. {action}")
            if len(recommended_actions) > 10:
                print(f"   ... and {len(recommended_actions) - 10} more actions")
        print()
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"sweep_report_RE34B_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Detailed report saved to: {report_filename}")
        
        # Display critical issues if any
        if high_priority_count > 0:
            print()
            print("🚨 CRITICAL ISSUES DETECTED:")
            print("=" * 30)
            
            # Find high priority discrepancies
            discrepancies = report.get('discrepancies', [])
            high_priority_issues = [d for d in discrepancies if d.get('priority') == 'high']
            
            for i, issue in enumerate(high_priority_issues[:5], 1):  # Show first 5
                work_item_id = issue.get('work_item_id', 'N/A')
                work_item_type = issue.get('work_item_type', 'Unknown')
                description = issue.get('description', 'No description')
                
                print(f"{i}. [{work_item_type} {work_item_id}] {description}")
            
            if len(high_priority_issues) > 5:
                print(f"   ... and {len(high_priority_issues) - 5} more critical issues")
        
        print()
        print("🎯 Sweep Summary:")
        if total_discrepancies == 0:
            print("✅ No issues found - backlog is in good health!")
        elif high_priority_count == 0:
            print("⚠️  Minor issues found - consider addressing medium/low priority items")
        else:
            print("🚨 Critical issues found - immediate attention required!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running backlog sweeper: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = run_backlog_sweeper()
    sys.exit(0 if success else 1) 