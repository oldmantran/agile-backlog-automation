#!/usr/bin/env python3
"""
Database setup and management for Agile Backlog Automation.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "backlog_jobs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create jobs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress INTEGER DEFAULT 0,
                        current_agent TEXT,
                        current_action TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user settings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        setting_type TEXT NOT NULL,
                        setting_key TEXT NOT NULL,
                        setting_value TEXT NOT NULL,
                        scope TEXT NOT NULL CHECK (scope IN ('session', 'user_default', 'global_default')),
                        is_user_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, setting_type, setting_key, scope)
                    )
                ''')
                
                # Create index for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_settings_lookup 
                    ON user_settings(user_id, setting_type, scope)
                ''')
                
                # Add is_user_default column if it doesn't exist (migration)
                try:
                    cursor.execute('ALTER TABLE user_settings ADD COLUMN is_user_default BOOLEAN DEFAULT FALSE')
                    logger.info("Added is_user_default column to user_settings table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_job(self, job_id: str, project_id: str, status: str = "queued", progress: int = 0):
        """Save or update a job."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO jobs 
                    (id, project_id, status, progress, start_time) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (job_id, project_id, status, progress, datetime.now()))
                conn.commit()
                logger.info(f"Job {job_id} saved to database")
        except Exception as e:
            logger.error(f"Failed to save job {job_id}: {e}")
            raise
    
    def update_job(self, job_id: str, **kwargs):
        """Update job fields."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                fields = []
                values = []
                for key, value in kwargs.items():
                    if key in ['status', 'progress', 'current_agent', 'current_action', 'error', 'end_time']:
                        fields.append(f"{key} = ?")
                        values.append(value)
                
                if fields:
                    values.append(job_id)
                    query = f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?"
                    cursor.execute(query, values)
                    conn.commit()
                    logger.info(f"Job {job_id} updated: {kwargs}")
                    
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all jobs: {e}")
            return []
    
    # User Settings Methods
    def save_user_setting(self, user_id: str, setting_type: str, setting_key: str, 
                         setting_value: str, scope: str = 'session', is_user_default: bool = False) -> bool:
        """Save or update a user setting."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_settings 
                    (user_id, setting_type, setting_key, setting_value, scope, is_user_default, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, setting_type, setting_key, setting_value, scope, is_user_default, datetime.now()))
                conn.commit()
                logger.info(f"Setting saved: {user_id}.{setting_type}.{setting_key} = {setting_value} ({scope}, user_default={is_user_default})")
                return True
        except Exception as e:
            logger.error(f"Failed to save user setting: {e}")
            return False
    
    def get_user_settings(self, user_id: str, setting_type: str, scope: str = None) -> Dict[str, str]:
        """Get user settings for a specific type and scope."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if scope:
                    cursor.execute('''
                        SELECT setting_key, setting_value 
                        FROM user_settings 
                        WHERE user_id = ? AND setting_type = ? AND scope = ?
                    ''', (user_id, setting_type, scope))
                else:
                    cursor.execute('''
                        SELECT setting_key, setting_value, scope
                        FROM user_settings 
                        WHERE user_id = ? AND setting_type = ?
                        ORDER BY 
                            CASE scope 
                                WHEN 'session' THEN 1 
                                WHEN 'user_default' THEN 2 
                                WHEN 'global_default' THEN 3 
                            END
                    ''', (user_id, setting_type))
                
                rows = cursor.fetchall()
                settings = {}
                
                for row in rows:
                    if len(row) == 2:  # scope specified
                        settings[row[0]] = row[1]
                    else:  # scope not specified, use highest priority
                        key, value, row_scope = row
                        if key not in settings:  # Only take first occurrence (highest priority)
                            settings[key] = value
                
                return settings
                
        except Exception as e:
            logger.error(f"Failed to get user settings: {e}")
            return {}
    
    def delete_user_settings(self, user_id: str, setting_type: str, scope: str = None) -> bool:
        """Delete user settings."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if scope:
                    cursor.execute('''
                        DELETE FROM user_settings 
                        WHERE user_id = ? AND setting_type = ? AND scope = ?
                    ''', (user_id, setting_type, scope))
                else:
                    cursor.execute('''
                        DELETE FROM user_settings 
                        WHERE user_id = ? AND setting_type = ?
                    ''', (user_id, setting_type))
                
                conn.commit()
                logger.info(f"Deleted settings for {user_id}.{setting_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete user settings: {e}")
            return False
    
    def get_setting_history(self, user_id: str, setting_type: str = None) -> List[Dict[str, Any]]:
        """Get setting change history for audit trail."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if setting_type:
                    cursor.execute('''
                        SELECT * FROM user_settings 
                        WHERE user_id = ? AND setting_type = ?
                        ORDER BY updated_at DESC
                    ''', (user_id, setting_type))
                else:
                    cursor.execute('''
                        SELECT * FROM user_settings 
                        WHERE user_id = ?
                        ORDER BY updated_at DESC
                    ''', (user_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get setting history: {e}")
            return []
    
    def has_custom_settings(self, user_id: str, setting_type: str, scope: str = 'user_default') -> bool:
        """Check if a user has custom settings (not defaults)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM user_settings 
                    WHERE user_id = ? AND setting_type = ? AND scope = ? AND is_user_default = TRUE
                ''', (user_id, setting_type, scope))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Failed to check custom settings: {e}")
            return False
    
    def get_settings_with_flags(self, user_id: str, setting_type: str, scope: str = None) -> Dict[str, Any]:
        """Get user settings with flags indicating if they are custom defaults."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if scope:
                    cursor.execute('''
                        SELECT setting_key, setting_value, is_user_default
                        FROM user_settings 
                        WHERE user_id = ? AND setting_type = ? AND scope = ?
                    ''', (user_id, setting_type, scope))
                else:
                    cursor.execute('''
                        SELECT setting_key, setting_value, scope, is_user_default
                        FROM user_settings 
                        WHERE user_id = ? AND setting_type = ?
                        ORDER BY 
                            CASE scope 
                                WHEN 'session' THEN 1 
                                WHEN 'user_default' THEN 2 
                                WHEN 'global_default' THEN 3 
                            END
                    ''', (user_id, setting_type))
                
                rows = cursor.fetchall()
                settings = {}
                
                for row in rows:
                    if len(row) == 3:  # scope specified
                        key, value, is_user_default = row
                        settings[key] = {
                            'value': value,
                            'is_user_default': bool(is_user_default)
                        }
                    else:  # scope not specified, use highest priority
                        key, value, row_scope, is_user_default = row
                        if key not in settings:  # Only take first occurrence (highest priority)
                            settings[key] = {
                                'value': value,
                                'scope': row_scope,
                                'is_user_default': bool(is_user_default)
                            }
                
                return settings
                
        except Exception as e:
            logger.error(f"Failed to get settings with flags: {e}")
            return {}

# Global database instance
db = Database()
