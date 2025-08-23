#!/usr/bin/env python3
"""
Script to integrate the outbox pattern for Azure DevOps uploads.
This prevents data loss by staging all work items before upload.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.work_item_staging import WorkItemStaging
from integrators.outbox_uploader import OutboxUploader
from integrators.azure_devops_api import AzureDevOpsAPI

def show_integration_example():
    """Show how to integrate outbox pattern into supervisor."""
    
    print("=== Outbox Pattern Integration Example ===\n")
    
    print("Benefits:")
    print("  ✓ Zero data loss - all work items persisted before upload")
    print("  ✓ Resumable uploads - retry failures without regenerating")
    print("  ✓ Better error handling - individual failures don't affect others")
    print("  ✓ Upload progress tracking - see exactly what succeeded/failed")
    print()
    
    print("=== Code Changes for supervisor.py ===\n")
    
    print("""
1. Add imports at the top:
```python
from models.work_item_staging import WorkItemStaging
from integrators.outbox_uploader import OutboxUploader
```

2. Replace the _upload_to_azure_devops method:

OLD CODE:
```python
def _upload_to_azure_devops(self, work_items):
    ado_api = AzureDevOpsAPI(
        organization_url=self.azure_config['organization_url'],
        project=self.azure_config['project'],
        pat=self.azure_config['pat']
    )
    
    created_items = []
    for item in work_items:
        try:
            result = ado_api.create_work_item(...)
            created_items.append(result)
        except Exception as e:
            logger.error(f"Failed to create {item['type']}: {e}")
    
    return created_items
```

NEW CODE:
```python
def _upload_to_azure_devops(self, work_items):
    # Stage all work items first
    staging = WorkItemStaging(self.db_path)
    
    logger.info(f"Staging {len(work_items)} work items before upload...")
    staging_map = {}  # Map old IDs to staging IDs
    
    for item in work_items:
        # Determine hierarchy level
        hierarchy_level = {
            'Epic': 0,
            'Feature': 1,
            'User Story': 2,
            'Task': 3,
            'Test Case': 3,
            'Test Plan': 1,
            'Test Suite': 3
        }.get(item['work_item_type'], 3)
        
        # Get parent staging ID if exists
        parent_staging_id = None
        if item.get('parent_id'):
            parent_staging_id = staging_map.get(item['parent_id'])
        
        # Stage the work item
        staging_id = staging.add_work_item(
            job_id=self.job_id,
            work_item_type=item['work_item_type'],
            title=item['title'],
            local_parent_id=parent_staging_id,
            generated_data=item,
            hierarchy_level=hierarchy_level
        )
        
        # Map for parent references
        staging_map[item.get('id', item['title'])] = staging_id
    
    # Get staging summary
    staging_summary = staging.get_job_summary(self.job_id)
    logger.info(f"Staged {staging_summary['total']} items successfully")
    
    # Update job with staging info
    self.update_job_metadata({
        'staging_summary': staging_summary,
        'staging_complete': True
    })
    
    # Initialize Azure DevOps API
    ado_api = AzureDevOpsAPI(
        organization_url=self.azure_config['organization_url'],
        project=self.azure_config['project'],
        pat=self.azure_config['pat']
    )
    
    # Upload using outbox pattern
    logger.info("Starting Azure DevOps upload with outbox pattern...")
    uploader = OutboxUploader(staging, ado_api)
    
    # Upload with progress tracking
    upload_summary = uploader.upload_all(
        job_id=self.job_id,
        progress_callback=lambda curr, total: self.update_progress(
            80 + int(20 * curr / total),  # 80-100% for upload phase
            f"Uploading to Azure DevOps ({curr}/{total})"
        )
    )
    
    # Log results
    logger.info(f"Upload complete: {upload_summary}")
    
    # Update job with final results
    self.update_job_metadata({
        'upload_summary': upload_summary,
        'azure_integration': {
            'total_staged': staging_summary['total'],
            'total_uploaded': upload_summary['by_status'].get('success', 0),
            'failed_uploads': upload_summary['by_status'].get('failed', 0),
            'skipped_uploads': upload_summary['by_status'].get('skipped', 0)
        }
    })
    
    # Return created work items for compatibility
    created_items = staging.get_uploaded_work_items(self.job_id)
    return created_items
```

3. Add retry endpoint to unified_api_server.py:
```python
@app.post("/api/jobs/{job_id}/retry-uploads")
async def retry_failed_uploads(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    \"\"\"Retry failed Azure DevOps uploads for a job.\"\"\"
    try:
        # Get job data
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        
        # Check ownership
        if job.get('user_id') != current_user['id']:
            raise HTTPException(403, "Not authorized")
        
        # Get Azure config from job
        raw_summary = json.loads(job.get('result_data', '{}'))
        azure_config = raw_summary.get('azure_config')
        if not azure_config:
            raise HTTPException(400, "No Azure DevOps configuration found")
        
        # Initialize components
        staging = WorkItemStaging()
        ado_api = AzureDevOpsAPI(
            organization_url=azure_config['organization_url'],
            project=azure_config['project'],
            pat=azure_config['pat']
        )
        uploader = OutboxUploader(staging, ado_api)
        
        # Retry failed uploads
        logger.info(f"Retrying failed uploads for job {job_id}")
        retry_summary = uploader.retry_failed(job_id)
        
        # Update job metadata
        db.update_job_metadata(job_id, {
            'retry_attempts': job.get('retry_attempts', 0) + 1,
            'last_retry': datetime.utcnow().isoformat(),
            'retry_summary': retry_summary
        })
        
        return {
            "status": "success",
            "summary": retry_summary,
            "message": f"Retried {retry_summary['retried']} failed uploads"
        }
        
    except Exception as e:
        logger.error(f"Retry uploads error: {e}")
        raise HTTPException(500, str(e))
```

4. Add UI button in ProjectHistoryCard (MyProjectsScreen.tsx):
```typescript
{job.metadata?.staging_summary?.by_status?.failed > 0 && (
  <Button
    onClick={() => retryFailedUploads(job.id)}
    disabled={isRetrying}
    variant="outline"
    size="sm"
    className="text-orange-600"
  >
    <FiRotateCcw className="mr-2" />
    Retry {job.metadata.staging_summary.by_status.failed} Failed Uploads
  </Button>
)}
```
""")

def test_staging():
    """Test the staging functionality."""
    print("\n=== Testing Work Item Staging ===\n")
    
    # Create test staging
    staging = WorkItemStaging(":memory:")  # In-memory for testing
    
    # Add test work items
    test_items = [
        {
            "job_id": "test-job-001",
            "type": "Epic",
            "title": "Test Epic 1",
            "level": 0,
            "data": {"description": "Test epic description"}
        },
        {
            "job_id": "test-job-001", 
            "type": "Feature",
            "title": "Test Feature 1",
            "level": 1,
            "parent_id": 1,  # Will reference Epic
            "data": {"description": "Test feature description"}
        },
        {
            "job_id": "test-job-001",
            "type": "User Story", 
            "title": "Test Story 1",
            "level": 2,
            "parent_id": 2,  # Will reference Feature
            "data": {"description": "Test story description"}
        }
    ]
    
    print("Staging test work items...")
    staging_ids = []
    
    for item in test_items:
        parent_id = None
        if "parent_id" in item:
            parent_id = staging_ids[item["parent_id"] - 1]
        
        staging_id = staging.add_work_item(
            job_id=item["job_id"],
            work_item_type=item["type"],
            title=item["title"],
            local_parent_id=parent_id,
            generated_data=item["data"],
            hierarchy_level=item["level"]
        )
        staging_ids.append(staging_id)
        print(f"  Staged: {item['type']} - {item['title']} (ID: {staging_id})")
    
    # Get summary
    summary = staging.get_job_summary("test-job-001")
    print(f"\nStaging Summary: {summary}")
    
    # Show hierarchy
    print("\nWork Item Hierarchy:")
    items = staging.get_pending_items("test-job-001")
    for item in items:
        indent = "  " * item[8]  # hierarchy_level
        print(f"{indent}└─ {item[2]}: {item[3]}")

if __name__ == "__main__":
    show_integration_example()
    
    print("\n" + "="*50 + "\n")
    
    response = input("Run staging test? (y/n): ")
    if response.lower() == 'y':
        test_staging()
    
    print("\nSee INTEGRATION_GUIDE.md for complete implementation details.")