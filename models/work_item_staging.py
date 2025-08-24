"""
Work Item Staging Model for Outbox Pattern Implementation

This module handles the local persistence of generated work items before
Azure DevOps upload, enabling resumable operations and zero data loss.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class WorkItemStatus(Enum):
    """Status enumeration for work item staging."""
    PENDING = "pending"
    UPLOADING = "uploading"  
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"  # For items skipped due to parent failures


class WorkItemType(Enum):
    """Work item type enumeration."""
    EPIC = "Epic"
    FEATURE = "Feature" 
    USER_STORY = "User Story"
    TASK = "Task"
    TEST_PLAN = "Test Plan"
    TEST_SUITE = "Test Suite"
    TEST_CASE = "Test Case"


class WorkItemStaging:
    """
    Manages local staging of work items before Azure DevOps upload.
    Implements the outbox pattern for reliable data persistence.
    """
    
    def __init__(self, db_path: str = "agile_backlog.db"):
        """Initialize work item staging with database connection."""
        self.db_path = db_path
        self.logger = logging.getLogger("work_item_staging")
        self._init_database()
    
    def _init_database(self):
        """Initialize the work item staging table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS work_item_staging (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    work_item_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    local_parent_id INTEGER,  -- Reference to parent in staging table
                    ado_parent_id INTEGER,    -- ADO work item ID of parent (after upload)
                    ado_id INTEGER,           -- ADO work item ID (after successful upload)
                    status TEXT NOT NULL DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    generated_data TEXT NOT NULL,  -- JSON serialized work item data
                    hierarchy_level INTEGER NOT NULL,  -- 0=Epic, 1=Feature, 2=UserStory, 3=Task/TestCase
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_at TIMESTAMP,
                    last_retry_at TIMESTAMP
                )
            """)
            
            # Create indexes for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_status 
                ON work_item_staging(job_id, status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hierarchy_type 
                ON work_item_staging(job_id, hierarchy_level, work_item_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_parent_id 
                ON work_item_staging(local_parent_id)
            """)
            
            conn.commit()
            self.logger.info("Work item staging database initialized")
    
    def stage_backlog(self, job_id: str, backlog_data: Dict[str, Any]) -> int:
        """
        Stage all work items from backlog data into local database.
        
        Args:
            job_id: Unique identifier for this backlog generation job
            backlog_data: Complete backlog data structure
            
        Returns:
            Number of work items staged
        """
        self.logger.info(f"Staging backlog data for job {job_id}")
        staged_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            # Clear any existing staging data for this job
            conn.execute("DELETE FROM work_item_staging WHERE job_id = ?", (job_id,))
            
            # Stage epics first (hierarchy level 0)
            for epic_data in backlog_data.get('epics', []):
                epic_id = self._stage_work_item(
                    conn, job_id, WorkItemType.EPIC, epic_data, 
                    hierarchy_level=0
                )
                staged_count += 1
                
                # Stage features (hierarchy level 1)  
                for feature_data in epic_data.get('features', []):
                    feature_id = self._stage_work_item(
                        conn, job_id, WorkItemType.FEATURE, feature_data,
                        parent_id=epic_id, hierarchy_level=1
                    )
                    staged_count += 1
                    
                    # Stage test plan if needed
                    has_test_cases = (feature_data.get('test_cases') or 
                                    any(story.get('test_cases') for story in feature_data.get('user_stories', [])))
                    
                    test_plan_id = None
                    if has_test_cases:
                        test_plan_data = {
                            'title': f"Test Plan: {feature_data.get('title', 'Feature')}",
                            'feature_data': feature_data
                        }
                        test_plan_id = self._stage_work_item(
                            conn, job_id, WorkItemType.TEST_PLAN, test_plan_data,
                            parent_id=feature_id, hierarchy_level=1
                        )
                        staged_count += 1
                    
                    # Stage user stories (hierarchy level 2)
                    for user_story_data in feature_data.get('user_stories', []):
                        user_story_id = self._stage_work_item(
                            conn, job_id, WorkItemType.USER_STORY, user_story_data,
                            parent_id=feature_id, hierarchy_level=2
                        )
                        staged_count += 1
                        
                        # Stage tasks (hierarchy level 3)
                        for task_data in user_story_data.get('tasks', []):
                            self._stage_work_item(
                                conn, job_id, WorkItemType.TASK, task_data,
                                parent_id=user_story_id, hierarchy_level=3
                            )
                            staged_count += 1
                        
                        # Stage test suite and test cases (hierarchy level 3)
                        if user_story_data.get('test_cases') and test_plan_id:
                            test_suite_data = {
                                'title': f"Test Suite: {user_story_data.get('title', 'User Story')}",
                                'user_story_data': user_story_data,
                                'test_plan_id': test_plan_id
                            }
                            test_suite_id = self._stage_work_item(
                                conn, job_id, WorkItemType.TEST_SUITE, test_suite_data,
                                parent_id=test_plan_id, hierarchy_level=3
                            )
                            staged_count += 1
                            
                            for test_case_data in user_story_data.get('test_cases', []):
                                self._stage_work_item(
                                    conn, job_id, WorkItemType.TEST_CASE, test_case_data,
                                    parent_id=test_suite_id, hierarchy_level=3
                                )
                                staged_count += 1
                    
                    # Stage feature-level test cases
                    if feature_data.get('test_cases') and test_plan_id:
                        default_suite_data = {
                            'title': f"Default Test Suite: {feature_data.get('title', 'Feature')}",
                            'feature_data': feature_data,
                            'test_plan_id': test_plan_id
                        }
                        default_suite_id = self._stage_work_item(
                            conn, job_id, WorkItemType.TEST_SUITE, default_suite_data,
                            parent_id=test_plan_id, hierarchy_level=3
                        )
                        staged_count += 1
                        
                        for test_case_data in feature_data.get('test_cases', []):
                            self._stage_work_item(
                                conn, job_id, WorkItemType.TEST_CASE, test_case_data,
                                parent_id=default_suite_id, hierarchy_level=3
                            )
                            staged_count += 1
            
            conn.commit()
        
        self.logger.info(f"Successfully staged {staged_count} work items for job {job_id}")
        return staged_count
    
    def _stage_work_item(self, conn: sqlite3.Connection, job_id: str, 
                        work_item_type: WorkItemType, work_item_data: Dict[str, Any],
                        parent_id: Optional[int] = None, hierarchy_level: int = 0) -> int:
        """Stage a single work item and return its local ID."""
        
        cursor = conn.execute("""
            INSERT INTO work_item_staging 
            (job_id, work_item_type, title, local_parent_id, generated_data, hierarchy_level)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            work_item_type.value,
            work_item_data.get('title', 'Untitled'),
            parent_id,
            json.dumps(work_item_data),
            hierarchy_level
        ))
        
        return cursor.lastrowid
    
    def stage_work_item(self, job_id: str, work_item_type: str, title: str, 
                       description: str, work_item_data: Dict[str, Any]) -> int:
        """Public method to stage a single work item (for testing and direct use)."""
        with sqlite3.connect(self.db_path) as conn:
            item_data = work_item_data.copy()
            item_data['title'] = title
            item_data['description'] = description
            
            # Determine hierarchy level based on type
            hierarchy_map = {
                'Epic': 0,
                'Feature': 1,
                'User Story': 2,
                'Task': 3,
                'Test Case': 3
            }
            hierarchy_level = hierarchy_map.get(work_item_type, 0)
            
            staging_id = self._stage_work_item(
                conn, job_id, WorkItemType(work_item_type), 
                item_data, hierarchy_level=hierarchy_level
            )
            conn.commit()
            return staging_id
    
    def get_staging_summary(self, job_id: str) -> Dict[str, Any]:
        """Get summary statistics for staged work items."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get counts by type and status  
            cursor = conn.execute("""
                SELECT work_item_type, status, COUNT(*) as count
                FROM work_item_staging 
                WHERE job_id = ?
                GROUP BY work_item_type, status
                ORDER BY work_item_type, status
            """, (job_id,))
            
            results = cursor.fetchall()
            
            summary = {
                'job_id': job_id,
                'total_items': 0,
                'by_type': {},
                'by_status': {'pending': 0, 'uploading': 0, 'success': 0, 'failed': 0, 'skipped': 0}
            }
            
            for row in results:
                work_type = row['work_item_type']
                status = row['status']
                count = row['count']
                
                if work_type not in summary['by_type']:
                    summary['by_type'][work_type] = {}
                
                summary['by_type'][work_type][status] = count
                summary['by_status'][status] += count
                summary['total_items'] += count
            
            return summary
    
    def get_upload_queue(self, job_id: str, status: WorkItemStatus = WorkItemStatus.PENDING, 
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get work items ready for upload, ordered by hierarchy level."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT * FROM work_item_staging 
                WHERE job_id = ? AND status = ?
                ORDER BY hierarchy_level ASC, id ASC
            """
            params = [job_id, status.value]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            items = []
            for row in rows:
                item = dict(row)
                item['generated_data'] = json.loads(item['generated_data'])
                items.append(item)
            
            return items
    
    def update_upload_status(self, staging_id: int, status: WorkItemStatus,
                           ado_id: Optional[int] = None, error_message: Optional[str] = None):
        """Update the upload status of a staged work item."""
        with sqlite3.connect(self.db_path) as conn:
            if status == WorkItemStatus.SUCCESS:
                conn.execute("""
                    UPDATE work_item_staging 
                    SET status = ?, ado_id = ?, uploaded_at = CURRENT_TIMESTAMP, error_message = NULL
                    WHERE id = ?
                """, (status.value, ado_id, staging_id))
            elif status == WorkItemStatus.FAILED:
                conn.execute("""
                    UPDATE work_item_staging 
                    SET status = ?, retry_count = retry_count + 1, 
                        error_message = ?, last_retry_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status.value, error_message, staging_id))
            else:
                conn.execute("""
                    UPDATE work_item_staging 
                    SET status = ?
                    WHERE id = ?
                """, (status.value, staging_id))
            
            conn.commit()
    
    def get_parent_ado_id(self, local_parent_id: int) -> Optional[int]:
        """Get the ADO ID of a parent work item by its local staging ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT ado_id FROM work_item_staging 
                WHERE id = ? AND status = 'success'
            """, (local_parent_id,))
            
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_pending_items(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all pending items for a job."""
        return self.get_upload_queue(job_id, WorkItemStatus.PENDING)
    
    def get_failed_items(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all failed items for a job."""
        return self.get_upload_queue(job_id, WorkItemStatus.FAILED)
    
    def get_job_summary(self, job_id: str) -> Dict[str, Any]:
        """Alias for get_staging_summary for backward compatibility."""
        return self.get_staging_summary(job_id)
    
    def mark_item_status(self, staging_id: int, status: str, error_message: Optional[str] = None):
        """Mark an item's status (simplified interface)."""
        status_enum = WorkItemStatus(status)
        self.update_upload_status(staging_id, status_enum, error_message=error_message)
    
    def cleanup_successful_items(self, job_id: str):
        """Clean up only successful items."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM work_item_staging 
                WHERE job_id = ? AND status = 'success'
            """, (job_id,))
            conn.commit()
    
    def cleanup_successful_job(self, job_id: str, keep_failed: bool = True):
        """Clean up staging data after successful upload."""
        with sqlite3.connect(self.db_path) as conn:
            if keep_failed:
                # Keep failed items for retry
                conn.execute("""
                    DELETE FROM work_item_staging 
                    WHERE job_id = ? AND status = 'success'
                """, (job_id,))
                self.logger.info(f"Cleaned up successful work items for job {job_id}")
            else:
                # Remove all items for this job
                conn.execute("""
                    DELETE FROM work_item_staging 
                    WHERE job_id = ?
                """, (job_id,))
                self.logger.info(f"Cleaned up all work items for job {job_id}")
            
            conn.commit()