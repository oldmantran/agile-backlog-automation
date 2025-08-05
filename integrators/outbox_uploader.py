"""
Outbox Pattern Uploader for Azure DevOps Integration

Handles reliable upload of staged work items with retry logic,
parent-child dependency resolution, and comprehensive error handling.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models.work_item_staging import WorkItemStaging, WorkItemStatus, WorkItemType
from integrators.azure_devops_api import AzureDevOpsIntegrator


class OutboxUploader:
    """
    Manages the upload of staged work items to Azure DevOps using the outbox pattern.
    Provides reliable, resumable uploads with comprehensive error handling.
    """
    
    def __init__(self, ado_integrator: AzureDevOpsIntegrator, db_path: str = "agile_backlog.db"):
        """Initialize the outbox uploader."""
        self.ado_integrator = ado_integrator
        self.staging = WorkItemStaging(db_path)
        self.logger = logging.getLogger("outbox_uploader")
        
        # Upload configuration
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds
        self.rate_limit_delay = 0.1  # 100ms between uploads
        self.batch_size = 50  # Process in batches for large volumes
    
    def upload_job(self, job_id: str, resume: bool = True) -> Dict[str, Any]:
        """
        Upload all work items for a job with comprehensive error handling.
        
        Args:
            job_id: Job identifier to upload
            resume: Whether to resume from previous failures
            
        Returns:
            Upload summary with success/failure counts
        """
        self.logger.info(f"Starting outbox upload for job {job_id} (resume={resume})")
        
        # Get initial summary
        initial_summary = self.staging.get_staging_summary(job_id)
        self.logger.info(f"Initial staging summary: {initial_summary['total_items']} total items")
        
        results = {
            'job_id': job_id,
            'started_at': datetime.now().isoformat(),
            'total_items': initial_summary['total_items'],
            'uploaded': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            # Upload in dependency order to maintain parent-child relationships
            # Special handling for test artifacts which have cross-level dependencies
            upload_phases = [
                {'level': 0, 'description': 'Epics'},
                {'level': 1, 'types': ['Feature'], 'description': 'Features'}, 
                {'level': 1, 'types': ['Test Plan'], 'description': 'Test Plans'},
                {'level': 2, 'description': 'User Stories'},
                {'level': 3, 'types': ['Task'], 'description': 'Tasks'},
                {'level': 3, 'types': ['Test Suite'], 'description': 'Test Suites'}, 
                {'level': 3, 'types': ['Test Case'], 'description': 'Test Cases'}
            ]
            
            for phase in upload_phases:
                level = phase['level']
                types_filter = phase.get('types')
                description = phase['description']
                
                self.logger.info(f"Processing {description} (level {level})")
                level_results = self._upload_hierarchy_level(job_id, level, resume, types_filter)
                
                results['uploaded'] += level_results['uploaded']
                results['failed'] += level_results['failed']
                results['skipped'] += level_results['skipped']
                results['errors'].extend(level_results['errors'])
                
                # Log progress
                total_processed = results['uploaded'] + results['failed'] + results['skipped']
                progress = (total_processed / results['total_items']) * 100 if results['total_items'] > 0 else 0
                self.logger.info(f"Progress: {total_processed}/{results['total_items']} ({progress:.1f}%)")
        
        except Exception as e:
            self.logger.error(f"Upload job failed with exception: {e}")
            results['errors'].append(f"Upload job exception: {str(e)}")
        
        finally:
            results['completed_at'] = datetime.now().isoformat()
            
            # Final summary
            final_summary = self.staging.get_staging_summary(job_id)
            results['final_summary'] = final_summary
            
            success_rate = (results['uploaded'] / results['total_items']) * 100 if results['total_items'] > 0 else 0
            
            self.logger.info(f"Upload job completed:")
            self.logger.info(f"  ✅ Uploaded: {results['uploaded']}")
            self.logger.info(f"  ❌ Failed: {results['failed']}")
            self.logger.info(f"  ⏭️ Skipped: {results['skipped']}")
            self.logger.info(f"  📈 Success Rate: {success_rate:.1f}%")
            
            if results['errors']:
                self.logger.warning(f"  ⚠️ Errors encountered: {len(results['errors'])}")
        
        return results
    
    def _upload_hierarchy_level(self, job_id: str, hierarchy_level: int, resume: bool, 
                               types_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Upload all work items at a specific hierarchy level, optionally filtered by type."""
        results = {'uploaded': 0, 'failed': 0, 'skipped': 0, 'errors': []}
        
        # Get items at this hierarchy level that need uploading
        status_filter = WorkItemStatus.PENDING
        if resume:
            # Also retry failed items
            pending_items = self.staging.get_upload_queue(job_id, WorkItemStatus.PENDING)
            failed_items = self.staging.get_upload_queue(job_id, WorkItemStatus.FAILED)
            items = pending_items + failed_items
        else:
            items = self.staging.get_upload_queue(job_id, status_filter)
        
        # Filter by hierarchy level
        level_items = [item for item in items if item['hierarchy_level'] == hierarchy_level]
        
        # Further filter by work item types if specified
        if types_filter:
            level_items = [item for item in level_items if item['work_item_type'] in types_filter]
        
        if not level_items:
            self.logger.debug(f"No items to upload at hierarchy level {hierarchy_level}")
            return results
        
        self.logger.info(f"Uploading {len(level_items)} items at hierarchy level {hierarchy_level}")
        
        # Process items in batches
        for i in range(0, len(level_items), self.batch_size):
            batch = level_items[i:i + self.batch_size]
            batch_results = self._upload_batch(batch)
            
            results['uploaded'] += batch_results['uploaded']
            results['failed'] += batch_results['failed']
            results['skipped'] += batch_results['skipped']
            results['errors'].extend(batch_results['errors'])
            
            # Rate limiting between batches
            if i + self.batch_size < len(level_items):
                time.sleep(self.rate_limit_delay * 10)  # Longer delay between batches
        
        return results
    
    def _upload_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload a batch of work items."""
        results = {'uploaded': 0, 'failed': 0, 'skipped': 0, 'errors': []}
        
        for item in items:
            item_result = self._upload_single_item(item)
            
            if item_result['status'] == 'success':
                results['uploaded'] += 1
            elif item_result['status'] == 'failed':
                results['failed'] += 1
            elif item_result['status'] == 'skipped':
                results['skipped'] += 1
            
            if item_result.get('error'):
                results['errors'].append(item_result['error'])
            
            # Rate limiting between individual items
            time.sleep(self.rate_limit_delay)
        
        return results
    
    def _upload_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a single work item with retry logic."""
        staging_id = item['id']
        work_item_type = item['work_item_type']
        title = item['title']
        generated_data = item['generated_data']
        
        self.logger.debug(f"Uploading {work_item_type}: {title}")
        
        # Check if parent exists (for non-top-level items)
        parent_ado_id = None
        if item['local_parent_id']:
            parent_ado_id = self.staging.get_parent_ado_id(item['local_parent_id'])
            if not parent_ado_id:
                # Parent hasn't been uploaded successfully yet, skip this item
                self.staging.update_upload_status(staging_id, WorkItemStatus.SKIPPED, 
                                                error_message="Parent not uploaded yet")
                return {
                    'status': 'skipped', 
                    'error': f"Skipped {work_item_type} '{title}' - parent not uploaded"
                }
        
        # Mark as uploading
        self.staging.update_upload_status(staging_id, WorkItemStatus.UPLOADING)
        
        # Attempt upload with retries
        for attempt in range(self.max_retries + 1):
            try:
                ado_id = self._create_ado_work_item(work_item_type, generated_data, parent_ado_id)
                
                # Success!
                self.staging.update_upload_status(staging_id, WorkItemStatus.SUCCESS, ado_id=ado_id)
                self.logger.debug(f"Successfully uploaded {work_item_type}: {title} (ADO ID: {ado_id})")
                return {'status': 'success', 'ado_id': ado_id}
                
            except Exception as e:
                error_msg = f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {str(e)}"
                self.logger.warning(f"Upload failed for {work_item_type} '{title}': {error_msg}")
                
                if attempt < self.max_retries:
                    # Wait before retry with exponential backoff
                    retry_delay = self.retry_delay * (2 ** attempt)
                    time.sleep(retry_delay)
                else:
                    # Final failure
                    full_error = f"Failed to upload {work_item_type} '{title}' after {self.max_retries + 1} attempts: {str(e)}"
                    self.staging.update_upload_status(staging_id, WorkItemStatus.FAILED, 
                                                    error_message=full_error)
                    return {'status': 'failed', 'error': full_error}
        
        return {'status': 'failed', 'error': 'Unexpected failure path'}
    
    def _create_ado_work_item(self, work_item_type: str, generated_data: Dict[str, Any], 
                             parent_ado_id: Optional[int] = None) -> int:
        """Create a work item in Azure DevOps using the appropriate method."""
        
        if work_item_type == WorkItemType.EPIC.value:
            result = self.ado_integrator._create_epic(generated_data)
            
        elif work_item_type == WorkItemType.FEATURE.value:
            if not parent_ado_id:
                raise ValueError("Feature requires parent epic ID")
            result = self.ado_integrator._create_feature(generated_data, parent_ado_id)
            
        elif work_item_type == WorkItemType.USER_STORY.value:
            if not parent_ado_id:
                raise ValueError("User story requires parent feature ID")
            result = self.ado_integrator._create_user_story(generated_data, parent_ado_id)
            
        elif work_item_type == WorkItemType.TASK.value:
            if not parent_ado_id:
                raise ValueError("Task requires parent user story ID")
            result = self.ado_integrator._create_task(generated_data, parent_ado_id)
            
        elif work_item_type == WorkItemType.TEST_PLAN.value:
            if not parent_ado_id:
                raise ValueError("Test plan requires parent feature ID")
            result = self.ado_integrator._create_test_plan(generated_data['feature_data'], parent_ado_id)
            
        elif work_item_type == WorkItemType.TEST_SUITE.value:
            # Test suite requires parent test plan ID (Azure DevOps ID, not local staging ID)
            if not parent_ado_id:
                raise ValueError("Test suite requires parent test plan Azure DevOps ID")
            
            if 'user_story_data' in generated_data:
                result = self.ado_integrator._create_test_suite(
                    generated_data['user_story_data'], 
                    parent_ado_id,  # Use Azure DevOps test plan ID
                    None  # Test suite doesn't need a separate parent
                )
            else:
                result = self.ado_integrator._create_default_test_suite(
                    generated_data['feature_data'],
                    parent_ado_id,  # Use Azure DevOps test plan ID
                    None  # Test suite doesn't need a separate parent
                )
            
        elif work_item_type == WorkItemType.TEST_CASE.value:
            if not parent_ado_id:
                raise ValueError("Test case requires parent test suite ID")
            result = self.ado_integrator._create_test_case(generated_data, None, parent_ado_id)
            
        else:
            raise ValueError(f"Unknown work item type: {work_item_type}")
        
        if not result or 'id' not in result:
            raise ValueError(f"Failed to create {work_item_type} - no ID returned")
        
        return result['id']
    
    def retry_failed_items(self, job_id: str, work_item_type: Optional[str] = None) -> Dict[str, Any]:
        """Retry upload of failed items for a specific job."""
        self.logger.info(f"Retrying failed items for job {job_id}")
        
        # Get failed items
        failed_items = self.staging.get_upload_queue(job_id, WorkItemStatus.FAILED)
        
        if work_item_type:
            failed_items = [item for item in failed_items if item['work_item_type'] == work_item_type]
        
        if not failed_items:
            self.logger.info("No failed items to retry")
            return {'retried': 0, 'success': 0, 'still_failed': 0}
        
        self.logger.info(f"Retrying {len(failed_items)} failed items")
        
        results = {'retried': len(failed_items), 'success': 0, 'still_failed': 0}
        
        for item in failed_items:
            # Reset status to pending for retry
            self.staging.update_upload_status(item['id'], WorkItemStatus.PENDING)
            
            # Attempt upload
            item_result = self._upload_single_item(item)
            
            if item_result['status'] == 'success':
                results['success'] += 1
            else:
                results['still_failed'] += 1
        
        self.logger.info(f"Retry results: {results['success']} succeeded, {results['still_failed']} still failed")
        return results