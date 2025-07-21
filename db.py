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
                
                # Create LLM configuration table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS llm_configurations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        provider TEXT NOT NULL CHECK (provider IN ('openai', 'grok', 'ollama')),
                        model TEXT,
                        api_key TEXT,
                        base_url TEXT,
                        preset TEXT,
                        is_default BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, name)
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

    # LLM Configuration Methods
    def save_llm_configuration(self, user_id: str, name: str, provider: str, 
                              model: str = None, api_key: str = None, 
                              base_url: str = None, preset: str = None,
                              is_default: bool = False, is_active: bool = False) -> bool:
        """Save or update an LLM configuration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # If this is being set as default, unset other defaults for this user
                if is_default:
                    cursor.execute('''
                        UPDATE llm_configurations 
                        SET is_default = FALSE 
                        WHERE user_id = ?
                    ''', (user_id,))
                
                # If this is being set as active, unset other active configs for this user
                if is_active:
                    cursor.execute('''
                        UPDATE llm_configurations 
                        SET is_active = FALSE 
                        WHERE user_id = ?
                    ''', (user_id,))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO llm_configurations 
                    (user_id, name, provider, model, api_key, base_url, preset, is_default, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, name, provider, model, api_key, base_url, preset, is_default, is_active, datetime.now()))
                
                conn.commit()
                logger.info(f"LLM configuration '{name}' saved for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save LLM configuration: {e}")
            return False

    def get_llm_configurations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all LLM configurations for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM llm_configurations 
                    WHERE user_id = ?
                    ORDER BY is_default DESC, is_active DESC, name ASC
                ''', (user_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get LLM configurations: {e}")
            return []

    def get_active_llm_configuration(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the currently active LLM configuration for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM llm_configurations 
                    WHERE user_id = ? AND is_active = TRUE
                    LIMIT 1
                ''', (user_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get active LLM configuration: {e}")
            return None

    def get_default_llm_configuration(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the default LLM configuration for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM llm_configurations 
                    WHERE user_id = ? AND is_default = TRUE
                    LIMIT 1
                ''', (user_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get default LLM configuration: {e}")
            return None

    def delete_llm_configuration(self, user_id: str, name: str) -> bool:
        """Delete an LLM configuration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM llm_configurations 
                    WHERE user_id = ? AND name = ?
                ''', (user_id, name))
                
                conn.commit()
                logger.info(f"LLM configuration '{name}' deleted for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete LLM configuration: {e}")
            return False

    def set_active_llm_configuration(self, user_id: str, name: str) -> bool:
        """Set an LLM configuration as active."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, deactivate all other configurations for this user
                cursor.execute('''
                    UPDATE llm_configurations 
                    SET is_active = FALSE 
                    WHERE user_id = ?
                ''', (user_id,))
                
                # Then activate the specified configuration
                cursor.execute('''
                    UPDATE llm_configurations 
                    SET is_active = TRUE, updated_at = ?
                    WHERE user_id = ? AND name = ?
                ''', (datetime.now(), user_id, name))
                
                conn.commit()
                logger.info(f"LLM configuration '{name}' set as active for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set active LLM configuration: {e}")
            return False

    def create_default_llm_configurations(self, user_id: str) -> bool:
        """Create default LLM configurations for a new user."""
        try:
            # Create Ollama configuration
            self.save_llm_configuration(
                user_id=user_id,
                name="Ollama Local (8B)",
                provider="ollama",
                model="llama3.1:8b",
                base_url="http://localhost:11434",
                preset="fast",
                is_default=True,
                is_active=True
            )
            
            # Create OpenAI configuration
            self.save_llm_configuration(
                user_id=user_id,
                name="OpenAI GPT-4",
                provider="openai",
                model="gpt-4",
                api_key="",  # User will need to set this
                is_default=False,
                is_active=False
            )
            
            # Create Grok configuration
            self.save_llm_configuration(
                user_id=user_id,
                name="Grok (xAI)",
                provider="grok",
                model="grok-4-latest",
                api_key="",  # User will need to set this
                is_default=False,
                is_active=False
            )
            
            logger.info(f"Default LLM configurations created for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create default LLM configurations: {e}")
            return False

# Global database instance
db = Database()

def add_backlog_job(user_email: str, project_name: str, epics_generated: int = 0, 
                   features_generated: int = 0, user_stories_generated: int = 0,
                   tasks_generated: int = 0, test_cases_generated: int = 0,
                   execution_time_seconds: float = None, raw_summary: dict = None):
    """
    Add a backlog job to the database.
    
    Args:
        user_email: Email of the user who ran the job
        project_name: Name of the project
        epics_generated: Number of epics generated
        features_generated: Number of features generated
        user_stories_generated: Number of user stories generated
        tasks_generated: Number of tasks generated
        test_cases_generated: Number of test cases generated
        execution_time_seconds: Execution time in seconds
        raw_summary: Raw summary data as dictionary
    """
    try:
        # Create a unique job ID
        job_id = f"backlog_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_email.replace('@', '_').replace('.', '_')}"
        
        # Save the job using the existing save_job method
        db.save_job(
            job_id=job_id,
            project_id=project_name,
            status="completed",
            progress=100
        )
        
        # Update with additional details
        db.update_job(
            job_id=job_id,
            current_agent="completed",
            current_action="backlog_generation_complete",
            end_time=datetime.now(),
            error=None
        )
        
        logger.info(f"Backlog job logged successfully: {job_id}")
        return job_id
        
    except Exception as e:
        logger.error(f"Failed to add backlog job: {e}")
        raise
