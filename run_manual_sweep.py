#!/usr/bin/env python3
"""
Manual Backlog Sweeper Full Assessment Runner

This script runs a comprehensive backlog sweep and demonstrates the coordination
between the Backlog Sweeper Agent and the Supervisor for real-time issue detection
and agent routing.

Usage:
    python run_manual_sweep.py

Features:
- Connects to your actual Azure DevOps project
- Runs full backlog assessment with all validation rules
- Shows real-time supervisor coordination and agent routing
- Provides detailed reporting with actionable recommendations
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.backlog_sweeper_agent import BacklogSweeperAgent
from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from integrators.azure_devops_api import AzureDevOpsIntegrator
from utils.logger import setup_logger


class SupervisorReportHandler:
    """Handles supervisor reports for demonstration purposes."""
    
    def __init__(self):
        self.reports_received = []
        self.agent_actions = []
        
    def handle_sweeper_report(self, report):
        """Mock supervisor report handler to show coordination."""
        print(f"\n🎯 SUPERVISOR: Received sweeper report at {datetime.now().strftime('%H:%M:%S')}")
        print(f"   📊 Summary: {report['summary']['total_discrepancies']} total discrepancies")
        print(f"   🔥 High Priority: {report['summary']['high_priority_count']}")
        print(f"   ⚡ Medium Priority: {report['summary']['medium_priority_count']}")
        print(f"   📝 Low Priority: {report['summary']['low_priority_count']}")
        
        # Show agent assignments
        agent_assignments = report.get('agent_assignments', {})
        if agent_assignments:
            print(f"\n🤖 SUPERVISOR: Routing discrepancies to agents:")
            for agent_name, discrepancies in agent_assignments.items():
                if discrepancies:
                    print(f"   → {agent_name}: {len(discrepancies)} tasks")
                    # Show first few discrepancies as examples
                    for i, disc in enumerate(discrepancies[:2]):
                        wi_id = disc.get('work_item_id', 'N/A')
                        desc = disc.get('description', 'No description')[:60] + "..."
                        print(f"     • Work Item {wi_id}: {desc}")
                    if len(discrepancies) > 2:
                        print(f"     • ... and {len(discrepancies) - 2} more")
        
        # Show dashboard requirements
        dashboard_reqs = report.get('dashboard_requirements', [])
        if dashboard_reqs:
            print(f"\n📊 SUPERVISOR: Dashboard requirements identified:")
            for req in dashboard_reqs[:3]:
                print(f"   • {req.get('description', 'No description')[:60]}...")
        
        # Show recommendations
        recommendations = report.get('recommended_actions', [])
        if recommendations:
            print(f"\n💡 SUPERVISOR: Action recommendations:")
            for rec in recommendations[:3]:
                print(f"   • {rec[:60]}...")
        
        self.reports_received.append(report)
        return report


def run_manual_backlog_sweep():
    """Run a comprehensive manual backlog sweep with supervisor coordination."""
    
    print("🚀 Agile Backlog Automation - Manual Sweep")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Load configuration
        print("📋 Step 1: Loading configuration...")
        config = Config()
        config_data = config.get_config()
        print(f"   ✅ Configuration loaded")
        print(f"   📁 Project: {config_data.get('azure_devops', {}).get('project', 'Not configured')}")
        print(f"   🏢 Organization: {config_data.get('azure_devops', {}).get('organization_url', 'Not configured')}")
        
        # 2. Initialize Azure DevOps connection
        print("\n🔗 Step 2: Connecting to Azure DevOps...")
        try:
            ado_client = AzureDevOpsIntegrator(
                organization_url=config_data.get('azure_devops', {}).get('organization_url'),
                personal_access_token=config_data.get('azure_devops', {}).get('personal_access_token'),
                project_name=config_data.get('azure_devops', {}).get('project')
            )
            
            # Test connection
            test_query = "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project"
            test_results = ado_client.query_work_items(test_query, max_results=1)
            
            print(f"   ✅ Connected to Azure DevOps successfully")
            print(f"   📊 Project has work items (test query returned {len(test_results)} items)")
            
        except Exception as e:
            print(f"   ❌ Failed to connect to Azure DevOps: {e}")
            print("   💡 Make sure your .env file has correct AZURE_DEVOPS_* settings")
            return
        
        # 3. Initialize supervisor report handler
        print("\n🎯 Step 3: Setting up supervisor coordination...")
        report_handler = SupervisorReportHandler()
        print("   ✅ Supervisor report handler ready")
        
        # 4. Initialize Backlog Sweeper Agent
        print("\n🤖 Step 4: Initializing Backlog Sweeper Agent...")
        sweeper = BacklogSweeperAgent(
            ado_client=ado_client,
            supervisor_callback=report_handler.handle_sweeper_report,
            config=config_data
        )
        print("   ✅ Backlog Sweeper Agent initialized")
        
        # Show current configuration
        print(f"   ⚙️  Min Acceptance Criteria: {sweeper.min_criteria_count}")
        print(f"   ⚙️  Max Acceptance Criteria: {sweeper.max_criteria_count}")
        print(f"   ⚙️  Require BDD Format: {sweeper.require_bdd_format}")
        print(f"   ⚙️  Max Discrepancies per Run: {sweeper.max_discrepancies_per_run}")
        
        # 5. Run the comprehensive sweep
        print("\n🔍 Step 5: Running comprehensive backlog sweep...")
        print("   This will analyze all work items for:")
        print("   • Acceptance criteria quality and compliance")
        print("   • Work item relationships and hierarchy")
        print("   • Decomposition requirements")
        print("   • Area path consistency")
        print("   • Dashboard and reporting needs")
        print()
        
        # Run the sweep with timing
        start_time = time.time()
        
        print("🔄 SWEEP STARTING...")
        print("-" * 40)
        
        report = sweeper.run_sweep()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("-" * 40)
        print(f"✅ SWEEP COMPLETED in {duration:.2f} seconds")
        
        # 6. Display detailed results
        print(f"\n📈 Step 6: Detailed Results Analysis")
        print("=" * 40)
        
        if report:
            summary = report.get('summary', {})
            print(f"📊 SWEEP SUMMARY:")
            print(f"   Total Discrepancies Found: {summary.get('total_discrepancies', 0)}")
            print(f"   High Priority Issues: {summary.get('high_priority_count', 0)}")
            print(f"   Medium Priority Issues: {summary.get('medium_priority_count', 0)}")
            print(f"   Low Priority Issues: {summary.get('low_priority_count', 0)}")
            print(f"   Agents with Assignments: {summary.get('agents_with_assignments', 0)}")
            print(f"   Dashboard Requirements: {summary.get('dashboard_requirements', 0)}")
            
            # Show breakdown by agent
            agent_assignments = report.get('agent_assignments', {})
            if agent_assignments:
                print(f"\n🤖 AGENT ASSIGNMENT BREAKDOWN:")
                for agent_name, discrepancies in agent_assignments.items():
                    if discrepancies:
                        print(f"   {agent_name}: {len(discrepancies)} tasks")
            
            # Show high priority issues in detail
            high_priority = report.get('discrepancies_by_priority', {}).get('high', [])
            if high_priority:
                print(f"\n🔥 HIGH PRIORITY ISSUES (Top 5):")
                for i, issue in enumerate(high_priority[:5]):
                    wi_id = issue.get('work_item_id', 'N/A')
                    issue_type = issue.get('type', 'unknown')
                    title = issue.get('title', 'No title')
                    desc = issue.get('description', 'No description')[:80] + "..."
                    print(f"   {i+1}. [{issue_type}] Work Item {wi_id}: {title}")
                    print(f"      {desc}")
                if len(high_priority) > 5:
                    print(f"   ... and {len(high_priority) - 5} more high priority issues")
            
            # Show recommendations
            recommendations = report.get('recommended_actions', [])
            if recommendations:
                print(f"\n💡 TOP RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations[:5]):
                    print(f"   {i+1}. {rec}")
                if len(recommendations) > 5:
                    print(f"   ... and {len(recommendations) - 5} more recommendations")
        
        # 7. Save results
        print(f"\n💾 Step 7: Saving results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Save comprehensive report
        output_file = f"output/manual_sweep_report_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"   📄 Full report saved: {output_file}")
        
        # Save summary for quick review
        summary_file = f"output/manual_sweep_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Backlog Sweep Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total Discrepancies: {summary.get('total_discrepancies', 0)}\n")
            f.write(f"High Priority: {summary.get('high_priority_count', 0)}\n")
            f.write(f"Medium Priority: {summary.get('medium_priority_count', 0)}\n")
            f.write(f"Low Priority: {summary.get('low_priority_count', 0)}\n")
            f.write(f"Duration: {duration:.2f} seconds\n\n")
            
            if recommendations:
                f.write("Top Recommendations:\n")
                for i, rec in enumerate(recommendations[:10]):
                    f.write(f"{i+1}. {rec}\n")
        
        print(f"   📝 Summary saved: {summary_file}")
        
        print(f"\n🎉 Manual sweep completed successfully!")
        print(f"   Check the output files for detailed analysis and next steps.")
        
    except Exception as e:
        print(f"\n❌ Error during manual sweep: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_manual_backlog_sweep()
