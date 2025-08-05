#!/usr/bin/env python3
"""
Retry Failed Uploads Utility

This script helps manage and retry failed work item uploads from the outbox pattern.
Useful for recovering from partial upload failures.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
os.chdir(project_root)

from models.work_item_staging import WorkItemStaging, WorkItemStatus
from integrators.outbox_uploader import OutboxUploader
from integrators.azure_devops_api import AzureDevOpsIntegrator


def show_failed_summary(job_id: str = None):
    """Show summary of failed uploads."""
    print("=" * 60)
    print("FAILED UPLOADS SUMMARY")
    print("=" * 60)
    
    staging = WorkItemStaging()
    
    if job_id:
        print(f"Job ID: {job_id}")
        summary = staging.get_staging_summary(job_id)
        print(f"Total items: {summary['total_items']}")
        print(f"Failed items: {summary['by_status'].get('failed', 0)}")
        print(f"Skipped items: {summary['by_status'].get('skipped', 0)}")
        
        print("\nBreakdown by type:")
        for work_type, counts in summary['by_type'].items():
            failed = counts.get('failed', 0)
            skipped = counts.get('skipped', 0)
            if failed > 0 or skipped > 0:
                print(f"  {work_type}: {failed} failed, {skipped} skipped")
    else:
        # Show all jobs with failures
        print("No specific job ID provided. This would show all jobs with failures.")
        print("Usage: python tools/retry_failed_uploads.py <job_id>")


def retry_failed_uploads(job_id: str, work_item_type: str = None):
    """Retry failed uploads for a specific job."""
    print("=" * 60)
    print("RETRYING FAILED UPLOADS")
    print("=" * 60)
    
    # Initialize components
    try:
        # Get Azure DevOps configuration from the original job's raw_summary
        azure_config = None
        try:
            from db import db
            
            # Extract the base job ID from the staging job ID
            # job_20250804_162036_proj_20250804_162036 -> look for a backlog job from around that time
            import re
            match = re.search(r'(\d{8}_\d{6})', job_id)
            if match:
                timestamp_part = match.group(1)
                # Look for backlog jobs from that timeframe
                all_jobs = db.get_backlog_jobs(limit=50)  # Get more jobs to search
                for job in all_jobs:
                    if job.get('raw_summary') and isinstance(job['raw_summary'], dict):
                        stored_job_id = job['raw_summary'].get('job_id', '')
                        if timestamp_part in stored_job_id:
                            azure_config = job['raw_summary'].get('azure_config', {})
                            print(f"Found Azure config from backlog job {job['id']}")
                            break
        except Exception as e:
            print(f"Warning: Could not retrieve Azure config from database: {e}")
        
        # No fallback - require stored configuration
        if not azure_config:
            print("ERROR: No stored Azure DevOps configuration found for this job")
            print("Cannot proceed with retry - the original job configuration is required")
            print("This usually means the job was created before configuration persistence was implemented")
            return False
        
        # Extract required configuration values
        organization_url = azure_config.get('organizationUrl')
        project = azure_config.get('project')
        pat = azure_config.get('personalAccessToken')
        area_path = azure_config.get('areaPath')
        iteration_path = azure_config.get('iterationPath')
        
        # Validate all required configuration is present
        missing_config = []
        if not organization_url:
            missing_config.append('organizationUrl')
        if not project:
            missing_config.append('project')
        if not pat:
            missing_config.append('personalAccessToken')
        if not area_path:
            missing_config.append('areaPath')
        if not iteration_path:
            missing_config.append('iterationPath')
        
        if missing_config:
            print(f"ERROR: Missing required Azure DevOps configuration: {', '.join(missing_config)}")
            print("Cannot proceed with retry - incomplete stored configuration")
            return False
        
        print(f"Azure DevOps Configuration:")
        print(f"  Organization: {organization_url}")
        print(f"  Project: {project}")
        print(f"  Area Path: {area_path}")
        print(f"  Iteration Path: {iteration_path}")
        print(f"  Config source: Stored job data")
        
        # Initialize Azure DevOps integrator
        ado_integrator = AzureDevOpsIntegrator(
            organization_url=organization_url,
            project=project,
            personal_access_token=pat,
            area_path=area_path,
            iteration_path=iteration_path
        )
        
        # Initialize outbox uploader
        uploader = OutboxUploader(ado_integrator)
        
        print(f"Job ID: {job_id}")
        if work_item_type:
            print(f"Work Item Type Filter: {work_item_type}")
        
        # Retry failed items
        print("\nStarting retry process...")
        results = uploader.retry_failed_items(job_id, work_item_type)
        
        print(f"\nRetry Results:")
        print(f"  Items retried: {results['retried']}")
        print(f"  Successful on retry: {results['success']}")
        print(f"  Still failed: {results['still_failed']}")
        
        if results['success'] > 0:
            print(f"\n✅ Successfully recovered {results['success']} items!")
        
        if results['still_failed'] > 0:
            print(f"\n❌ {results['still_failed']} items still failed after retry")
            print("Check logs for detailed error messages.")
        
        return results['success'] > 0
        
    except Exception as e:
        print(f"ERROR: Retry failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_staging_details(job_id: str):
    """Show detailed staging information for a job."""
    print("=" * 60)
    print("STAGING DETAILS")
    print("=" * 60)
    
    staging = WorkItemStaging()
    
    # Get failed items
    failed_items = staging.get_upload_queue(job_id, WorkItemStatus.FAILED)
    skipped_items = staging.get_upload_queue(job_id, WorkItemStatus.SKIPPED)
    
    if failed_items:
        print(f"\nFailed Items ({len(failed_items)}):")
        for item in failed_items[:10]:  # Show first 10
            print(f"  - {item['work_item_type']}: {item['title']}")
            if item['error_message']:
                print(f"    Error: {item['error_message'][:100]}...")
            print(f"    Retries: {item['retry_count']}")
        
        if len(failed_items) > 10:
            print(f"  ... and {len(failed_items) - 10} more failed items")
    
    if skipped_items:
        print(f"\nSkipped Items ({len(skipped_items)}):")
        for item in skipped_items[:10]:  # Show first 10
            print(f"  - {item['work_item_type']}: {item['title']}")
            if item['error_message']:
                print(f"    Reason: {item['error_message'][:100]}...")
        
        if len(skipped_items) > 10:
            print(f"  ... and {len(skipped_items) - 10} more skipped items")


def cleanup_successful_staging(job_id: str):
    """Clean up successfully uploaded items from staging."""
    print("=" * 60)
    print("CLEANUP SUCCESSFUL STAGING")
    print("=" * 60)
    
    staging = WorkItemStaging()
    
    summary = staging.get_staging_summary(job_id)
    successful_count = summary['by_status'].get('success', 0)
    
    if successful_count == 0:
        print("No successful items to clean up.")
        return
    
    print(f"Found {successful_count} successful items to clean up.")
    
    confirm = input("Are you sure you want to clean up successful items? (y/N): ")
    if confirm.lower() == 'y':
        staging.cleanup_successful_job(job_id, keep_failed=True)
        print(f"✅ Cleaned up {successful_count} successful items.")
    else:
        print("Cleanup cancelled.")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Retry Failed Uploads Utility")
        print("=" * 40)
        print("Usage:")
        print("  python tools/retry_failed_uploads.py <job_id> [command] [options]")
        print()
        print("Commands:")
        print("  summary    - Show summary of failed uploads (default)")
        print("  retry      - Retry failed uploads")  
        print("  details    - Show detailed staging information")
        print("  cleanup    - Clean up successful staging records")
        print()
        print("Options for retry:")
        print("  --type <work_item_type>  - Only retry specific type")
        print()
        print("Examples:")
        print("  python tools/retry_failed_uploads.py job_20250803_185337 summary")
        print("  python tools/retry_failed_uploads.py job_20250803_185337 retry")
        print("  python tools/retry_failed_uploads.py job_20250803_185337 retry --type Epic")
        return
    
    job_id = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "summary"
    
    print(f"Retry Failed Uploads Utility - {datetime.now().isoformat()}")
    
    if command == "summary":
        show_failed_summary(job_id)
    
    elif command == "retry":
        work_item_type = None
        if len(sys.argv) > 3 and sys.argv[3] == "--type" and len(sys.argv) > 4:
            work_item_type = sys.argv[4]
        
        success = retry_failed_uploads(job_id, work_item_type)
        sys.exit(0 if success else 1)
    
    elif command == "details":
        show_staging_details(job_id)
    
    elif command == "cleanup":
        cleanup_successful_staging(job_id)
    
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: summary, retry, details, cleanup")
        sys.exit(1)


if __name__ == "__main__":
    main()