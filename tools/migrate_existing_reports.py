#!/usr/bin/env python3
"""
Migration script to generate and persist summary reports for existing completed backlog jobs.

This script will:
1. Find all completed backlog jobs without reports
2. Generate reports for them using available data and logs
3. Store the reports in the database

Usage: python tools/migrate_existing_reports.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from utils.report_generator import BacklogSummaryReportGenerator
from db import db
from utils.safe_logger import get_safe_logger

logger = get_safe_logger(__name__)


def find_jobs_without_reports():
    """Find all completed backlog jobs that don't have reports."""
    conn = sqlite3.connect('backlog_jobs.db')
    cursor = conn.cursor()
    
    # Find completed jobs without reports
    query = """
        SELECT bj.id, bj.project_name, bj.created_at, bj.status,
               bj.epics_generated, bj.features_generated, bj.user_stories_generated,
               bj.tasks_generated, bj.test_cases_generated, bj.execution_time_seconds,
               bj.raw_summary
        FROM backlog_jobs bj
        LEFT JOIN backlog_reports br ON bj.id = br.backlog_job_id
        WHERE bj.status = 'completed' 
          AND bj.is_deleted = 0
          AND br.id IS NULL
        ORDER BY bj.created_at DESC
    """
    
    cursor.execute(query)
    jobs = cursor.fetchall()
    conn.close()
    
    return jobs


def find_log_file(job_id, created_at):
    """Try to find log file for a job."""
    # Try to extract job_id from raw_summary first
    log_patterns = []
    
    if job_id:
        log_patterns.extend([
            f"logs/backend_*job_{job_id}*.log",
            f"logs/supervisor_*job_{job_id}*.log"
        ])
    
    # Try date-based pattern
    if created_at:
        try:
            created_date = created_at.replace('-', '').replace(' ', '_').replace(':', '')[:15]
            log_patterns.extend([
                f"logs/backend_{created_date}*.log",
                f"logs/supervisor_{created_date}*.log"
            ])
        except:
            pass
    
    for pattern in log_patterns:
        log_files = list(Path('.').glob(pattern))
        if log_files:
            # Use the most recent file
            log_file = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
            return log_file
    
    return None


def migrate_job(job_data):
    """Migrate a single job by generating and saving its report."""
    job_id = job_data[0]
    project_name = job_data[1]
    
    print(f"\nProcessing job {job_id}: {project_name}")
    
    # Convert to dict format expected by report generator
    job_dict = {
        'id': job_data[0],
        'project_name': job_data[1],
        'created_at': str(job_data[2]),
        'status': job_data[3],
        'epics_generated': job_data[4],
        'features_generated': job_data[5],
        'user_stories_generated': job_data[6],
        'tasks_generated': job_data[7],
        'test_cases_generated': job_data[8],
        'execution_time_seconds': job_data[9],
        'raw_summary': job_data[10]
    }
    
    # Parse raw_summary
    raw_summary = {}
    if job_dict['raw_summary']:
        try:
            raw_summary = json.loads(job_dict['raw_summary']) if isinstance(job_dict['raw_summary'], str) else job_dict['raw_summary']
            job_dict['raw_summary'] = raw_summary
        except:
            pass
    
    # Try to find log file
    log_content = ""
    job_id_str = raw_summary.get('job_id', '')
    log_file = find_log_file(job_id_str, job_dict['created_at'])
    
    if log_file:
        print(f"  Found log file: {log_file}")
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
        except Exception as e:
            print(f"  Warning: Could not read log file: {e}")
    else:
        print(f"  No log file found")
    
    # Generate report
    try:
        generator = BacklogSummaryReportGenerator()
        report_data = generator.generate_report(job_dict, log_content)
        
        # Save to database
        if db.save_backlog_report(job_id, report_data):
            print(f"  ✅ Report generated and saved successfully")
            return True
        else:
            print(f"  ❌ Failed to save report to database")
            return False
            
    except Exception as e:
        print(f"  ❌ Error generating report: {e}")
        return False


def main():
    """Main migration function."""
    print("=== Backlog Report Migration Tool ===")
    print(f"Starting at: {datetime.now()}")
    print()
    
    # Find jobs without reports
    jobs = find_jobs_without_reports()
    print(f"Found {len(jobs)} completed jobs without reports")
    
    if not jobs:
        print("No jobs to migrate!")
        return
    
    # Confirm migration
    response = input(f"\nDo you want to generate reports for {len(jobs)} jobs? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        return
    
    # Process each job
    success_count = 0
    for job in jobs:
        if migrate_job(job):
            success_count += 1
    
    # Summary
    print("\n=== Migration Complete ===")
    print(f"Successfully migrated: {success_count}/{len(jobs)} jobs")
    print(f"Completed at: {datetime.now()}")


if __name__ == "__main__":
    main()