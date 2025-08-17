#!/usr/bin/env python3
"""
Fix job 24 data issues:
1. Update test_artifacts_included to False
2. Regenerate the report with correct data
"""

import sqlite3
import json
from utils.report_generator import BacklogSummaryReportGenerator
from db import db

# First, update the raw_summary to fix test_artifacts_included
conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Get current raw_summary
cursor.execute("SELECT raw_summary FROM backlog_jobs WHERE id = 24")
result = cursor.fetchone()

if result:
    raw_summary = json.loads(result[0])
    
    # Fix test_artifacts_included
    raw_summary['test_artifacts_included'] = False
    
    # Update in database
    cursor.execute("UPDATE backlog_jobs SET raw_summary = ? WHERE id = 24", 
                   (json.dumps(raw_summary),))
    conn.commit()
    print("[SUCCESS] Fixed test_artifacts_included to False")
    
    # Now regenerate the report with the correct log file
    # Get the TutorBot log file
    log_file = "logs/backend_20250817_144129_job_20250817_144129_proj_20250817_144129.log"
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        # Get job data
        cursor.execute("""
            SELECT id, project_name, created_at, status,
                   epics_generated, features_generated, user_stories_generated,
                   tasks_generated, test_cases_generated, execution_time_seconds,
                   raw_summary
            FROM backlog_jobs
            WHERE id = 24
        """)
        
        result = cursor.fetchone()
        job_data = {
            'id': result[0],
            'project_name': result[1],
            'created_at': str(result[2]),
            'status': result[3],
            'epics_generated': result[4],
            'features_generated': result[5],
            'user_stories_generated': result[6],
            'tasks_generated': result[7],
            'test_cases_generated': result[8],
            'execution_time_seconds': result[9],
            'raw_summary': json.loads(result[10])
        }
        
        # Generate correct report
        generator = BacklogSummaryReportGenerator()
        report_data = generator.generate_report(job_data, log_content)
        
        # Fix metadata
        report_data['metadata']['domain'] = 'education'
        
        # Fix upload count - you confirmed 263 were uploaded
        report_data['work_item_statistics']['azure_devops_upload']['total_uploaded'] = 263
        report_data['work_item_statistics']['azure_devops_upload']['upload_success_rate'] = 100.0
        
        # Save the corrected report
        if db.save_backlog_report(24, report_data):
            print("[SUCCESS] Report regenerated and saved with correct data")
        else:
            print("[ERROR] Failed to save regenerated report")
            
    except Exception as e:
        print(f"[ERROR] Error regenerating report: {e}")

conn.close()

print("\nTo verify the fix:")
print("1. Refresh My Projects page - TutorBot should now show 'Add Testing' button")
print("2. Download the summary report - it should show correct vision and stats")