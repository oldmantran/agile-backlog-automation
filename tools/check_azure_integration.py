#!/usr/bin/env python3
"""
Check Azure DevOps integration status for the latest job
"""

import sqlite3
import json

def check_azure_integration():
    """Check if Azure DevOps integration worked for the latest job."""
    
    print("🔍 Checking Azure DevOps Integration Status")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        # Get the latest job
        cursor.execute('SELECT id, project_name, raw_summary, created_at FROM backlog_jobs ORDER BY created_at DESC LIMIT 1')
        result = cursor.fetchone()
        
        if not result:
            print("❌ No jobs found in database")
            return
        
        job_id, project_name, raw_summary, created_at = result
        print(f"📋 Latest Job: {job_id}")
        print(f"📁 Project: {project_name}")
        print(f"⏰ Created: {created_at}")
        
        if raw_summary:
            try:
                summary = json.loads(raw_summary)
                print(f"\n📊 Job Summary:")
                print(f"   Epics: {summary.get('epics_generated', 0)}")
                print(f"   Features: {summary.get('features_generated', 0)}")
                print(f"   User Stories: {summary.get('user_stories_generated', 0)}")
                print(f"   Tasks: {summary.get('tasks_generated', 0)}")
                print(f"   Test Cases: {summary.get('test_cases_generated', 0)}")
                
                # Check Azure integration
                ado_summary = summary.get('ado_summary', {})
                if ado_summary:
                    print(f"\n🔗 Azure DevOps Integration:")
                    print(f"   Status: {ado_summary.get('status', 'Unknown')}")
                    if ado_summary.get('work_items_created'):
                        print(f"   Work Items Created: {len(ado_summary['work_items_created'])}")
                    if ado_summary.get('error'):
                        print(f"   Error: {ado_summary['error']}")
                    if ado_summary.get('missing_artifacts'):
                        print(f"   Missing Artifacts: {ado_summary['missing_artifacts']}")
                else:
                    print(f"\n❌ No Azure DevOps integration data found")
                    
            except json.JSONDecodeError:
                print(f"❌ Could not parse job summary JSON")
        else:
            print(f"❌ No raw summary data found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_azure_integration() 