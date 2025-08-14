#!/usr/bin/env python3
"""
Database setup and management for Agile Backlog Automation.
"""

import sqlite3
import os
import json
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
                
                # Create jobs table with proper constraints
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
                        progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
                        current_agent TEXT,
                        current_action TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        error TEXT,
                        result_data TEXT,  -- JSON storage for job results
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create system info table for build version tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        info_key TEXT NOT NULL UNIQUE,
                        info_value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create backlog jobs table for job completion statistics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS backlog_jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        project_name TEXT NOT NULL,
                        epics_generated INTEGER DEFAULT 0,
                        features_generated INTEGER DEFAULT 0,
                        user_stories_generated INTEGER DEFAULT 0,
                        tasks_generated INTEGER DEFAULT 0,
                        test_cases_generated INTEGER DEFAULT 0,
                        execution_time_seconds REAL,
                        status TEXT DEFAULT 'completed',
                        raw_summary TEXT,
                        is_deleted INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        -- Progress tracking columns for hybrid SSE + DB polling
                        progress INTEGER DEFAULT 0,
                        current_action TEXT,
                        current_agent TEXT,
                        last_progress_update TIMESTAMP,
                        progress_etag TEXT
                    )
                ''')
                
                # Add progress columns to existing backlog_jobs if they don't exist
                try:
                    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN progress INTEGER DEFAULT 0")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                try:
                    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN current_action TEXT")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                    
                try:
                    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN current_agent TEXT")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                    
                try:
                    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN last_progress_update TIMESTAMP")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                    
                try:
                    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN progress_etag TEXT")
                except sqlite3.OperationalError:
                    pass  # Column already exists
                
                # Create user settings table with proper constraints
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        setting_type TEXT NOT NULL CHECK (setting_type IN ('work_item_limits', 'visual_settings', 'llm_config', 'preferences')),
                        setting_key TEXT NOT NULL,
                        setting_value TEXT NOT NULL,
                        scope TEXT NOT NULL CHECK (scope IN ('session', 'user_default', 'global_default')),
                        is_user_default BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, setting_type, setting_key, scope)
                    )
                ''')
                
                # Create LLM configuration table with proper constraints
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS llm_configurations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        provider TEXT NOT NULL CHECK (provider IN ('openai', 'grok', 'ollama')),
                        model TEXT,
                        api_key TEXT,  -- TODO: Encrypt in production
                        base_url TEXT,
                        preset TEXT CHECK (preset IN ('fast', 'balanced', 'high_quality', 'code_focused') OR preset IS NULL),
                        is_default BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, name)
                    )
                ''')
                
                # Create indexes for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_settings_lookup 
                    ON user_settings(user_id, setting_type, scope)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_jobs_status 
                    ON jobs(status, created_at)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_jobs_project 
                    ON jobs(project_id, created_at)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_llm_configs_user 
                    ON llm_configurations(user_id, is_active)
                ''')
                
                # Add missing columns if they don't exist (migrations)
                try:
                    cursor.execute('ALTER TABLE user_settings ADD COLUMN is_user_default BOOLEAN DEFAULT FALSE')
                    logger.info("Added is_user_default column to user_settings table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                try:
                    cursor.execute('ALTER TABLE jobs ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                    logger.info("Added updated_at column to jobs table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                try:
                    cursor.execute('ALTER TABLE jobs ADD COLUMN result_data TEXT')
                    logger.info("Added result_data column to jobs table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass

                # Add agent_name column to llm_configurations for per-agent model support
                try:
                    cursor.execute('ALTER TABLE llm_configurations ADD COLUMN agent_name TEXT')
                    logger.info("Added agent_name column to llm_configurations table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                # Add configuration_mode column to llm_configurations for mode persistence
                try:
                    cursor.execute('ALTER TABLE llm_configurations ADD COLUMN configuration_mode TEXT CHECK (configuration_mode IN ("global", "agent-specific") OR configuration_mode IS NULL)')
                    logger.info("Added configuration_mode column to llm_configurations table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                # Add agent_name column to llm_configurations for agent-specific configs
                try:
                    cursor.execute('ALTER TABLE llm_configurations ADD COLUMN agent_name TEXT')
                    logger.info("Added agent_name column to llm_configurations table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                # Create optimized visions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS optimized_visions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        original_vision TEXT NOT NULL,
                        optimized_vision TEXT NOT NULL,
                        domains TEXT NOT NULL,  -- JSON array of domains with weights
                        quality_score INTEGER NOT NULL,
                        quality_rating TEXT NOT NULL,
                        optimization_feedback TEXT,  -- JSON object with improvement details
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create table to track which backlogs came from optimized visions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS backlog_vision_mapping (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backlog_job_id INTEGER NOT NULL,
                        optimized_vision_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (backlog_job_id) REFERENCES backlog_jobs(id),
                        FOREIGN KEY (optimized_vision_id) REFERENCES optimized_visions(id)
                    )
                ''')
                
                # Create indexes for optimized visions
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_optimized_visions_user 
                    ON optimized_visions(user_id, created_at DESC)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_backlog_vision_mapping 
                    ON backlog_vision_mapping(backlog_job_id, optimized_vision_id)
                ''')
                
                # Create vision optimization jobs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vision_optimization_jobs (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
                        original_vision TEXT NOT NULL,
                        domains TEXT NOT NULL,  -- JSON array
                        optimized_vision_id INTEGER,  -- FK to optimized_visions when complete
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        FOREIGN KEY (optimized_vision_id) REFERENCES optimized_visions(id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_vision_jobs_user_status 
                    ON vision_optimization_jobs(user_id, status, created_at DESC)
                ''')
                
                # Add original_assessment column if it doesn't exist
                cursor.execute('''
                    PRAGMA table_info(vision_optimization_jobs)
                ''')
                columns = [col[1] for col in cursor.fetchall()]
                if 'original_assessment' not in columns:
                    cursor.execute('''
                        ALTER TABLE vision_optimization_jobs 
                        ADD COLUMN original_assessment TEXT
                    ''')
                if 'optimization_feedback' not in columns:
                    cursor.execute('''
                        ALTER TABLE vision_optimization_jobs 
                        ADD COLUMN optimization_feedback TEXT
                    ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """Validate database integrity and return health report."""
        report = {
            "status": "healthy",
            "issues": [],
            "tables": {},
            "indexes": {},
            "constraints": {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                expected_tables = ['jobs', 'user_settings', 'llm_configurations', 'system_info', 'backlog_jobs']
                
                for table in expected_tables:
                    if table in tables:
                        report["tables"][table] = "exists"
                        
                        # Check table structure
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()
                        report["tables"][f"{table}_columns"] = len(columns)
                    else:
                        report["tables"][table] = "missing"
                        report["issues"].append(f"Missing table: {table}")
                        report["status"] = "unhealthy"
                
                # Check indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                expected_indexes = [
                    'idx_user_settings_lookup', 
                    'idx_jobs_status', 
                    'idx_jobs_project', 
                    'idx_llm_configs_user'
                ]
                
                for index in expected_indexes:
                    if index in indexes:
                        report["indexes"][index] = "exists"
                    else:
                        report["indexes"][index] = "missing"
                        report["issues"].append(f"Missing index: {index}")
                
                # Check for orphaned records (example - would need foreign keys)
                cursor.execute("SELECT COUNT(*) FROM jobs WHERE status NOT IN ('queued', 'running', 'completed', 'failed', 'cancelled')")
                invalid_status_count = cursor.fetchone()[0]
                if invalid_status_count > 0:
                    report["issues"].append(f"Found {invalid_status_count} jobs with invalid status")
                    report["status"] = "unhealthy"
                
        except Exception as e:
            report["status"] = "error"
            report["issues"].append(f"Database validation failed: {str(e)}")
        
        return report
    
    def repair_database(self) -> bool:
        """Attempt to repair common database issues."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fix invalid job statuses
                cursor.execute("""
                    UPDATE jobs 
                    SET status = 'failed' 
                    WHERE status NOT IN ('queued', 'running', 'completed', 'failed', 'cancelled')
                """)
                
                # Fix invalid progress values
                cursor.execute("""
                    UPDATE jobs 
                    SET progress = CASE 
                        WHEN progress < 0 THEN 0
                        WHEN progress > 100 THEN 100
                        ELSE progress
                    END 
                    WHERE progress < 0 OR progress > 100
                """)
                
                # Add missing updated_at timestamps
                cursor.execute("""
                    UPDATE jobs 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE updated_at IS NULL
                """)
                
                conn.commit()
                logger.info("Database repair completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False
    
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
            # Create OpenAI configuration (now default)
            self.save_llm_configuration(
                user_id=user_id,
                name="OpenAI GPT-5-mini",
                provider="openai",
                model="gpt-5-mini",
                api_key="",  # User will need to set this
                is_default=True,
                is_active=True
            )
            
            # Create Ollama configuration
            self.save_llm_configuration(
                user_id=user_id,
                name="Ollama Local (14B)",
                provider="ollama",
                model="qwen2.5:14b-instruct-q4_K_M",
                base_url="http://localhost:11434",
                preset="balanced",
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
    
    def get_system_info(self, info_key: str) -> Optional[str]:
        """Get system information value by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT info_value FROM system_info WHERE info_key = ?', (info_key,))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get system info {info_key}: {e}")
            return None
    
    def set_system_info(self, info_key: str, info_value: str) -> bool:
        """Set system information value, updating timestamp."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO system_info (info_key, info_value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (info_key, info_value))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to set system info {info_key}: {e}")
            return False
    
    def get_build_version(self) -> str:
        """Get current build version from database."""
        version = self.get_system_info('build_version')
        return version if version else "2025.08.04.001"  # Default fallback
    
    def increment_build_version(self) -> str:
        """Increment build version for current date."""
        from datetime import datetime
        
        current_date = datetime.now().strftime("%Y.%m.%d")
        current_version = self.get_build_version()
        
        try:
            # Parse current version
            if current_version.startswith(current_date):
                # Same day, increment build number
                parts = current_version.split('.')
                if len(parts) == 4:
                    build_num = int(parts[3]) + 1
                else:
                    build_num = 1
            else:
                # New day, reset to 001
                build_num = 1
            
            new_version = f"{current_date}.{build_num:03d}"
            self.set_system_info('build_version', new_version)
            logger.info(f"Build version updated to: {new_version}")
            return new_version
            
        except Exception as e:
            logger.error(f"Failed to increment build version: {e}")
            # Return default version for current date
            fallback_version = f"{current_date}.001"
            self.set_system_info('build_version', fallback_version)
            return fallback_version
    
    def add_backlog_job(self, user_email: str, project_name: str, epics_generated: int = 0,
                       features_generated: int = 0, user_stories_generated: int = 0,
                       tasks_generated: int = 0, test_cases_generated: int = 0,
                       execution_time_seconds: float = None, raw_summary: dict = None) -> int:
        """Add a backlog job to the database and return the job ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO backlog_jobs (
                        user_email, project_name, epics_generated, features_generated,
                        user_stories_generated, tasks_generated, test_cases_generated,
                        execution_time_seconds, raw_summary
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_email, project_name, epics_generated, features_generated,
                    user_stories_generated, tasks_generated, test_cases_generated,
                    execution_time_seconds, json.dumps(raw_summary) if raw_summary else None
                ))
                job_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Backlog job added successfully with ID: {job_id}")
                return job_id
        except Exception as e:
            logger.error(f"Failed to add backlog job: {e}")
            raise
    
    def get_backlog_jobs(self, user_email: str = None, exclude_test_generated: bool = False,
                        exclude_failed: bool = False, exclude_deleted: bool = True,
                        limit: int = None) -> List[Dict[str, Any]]:
        """Get backlog jobs with optional filtering."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                where_conditions = []
                params = []
                
                if user_email:
                    where_conditions.append("user_email = ?")
                    params.append(user_email)
                
                if exclude_deleted:
                    where_conditions.append("is_deleted = 0")
                
                if exclude_failed:
                    where_conditions.append("status != 'failed'")
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                limit_clause = f"LIMIT {limit}" if limit else ""
                
                query = f'''
                    SELECT * FROM backlog_jobs 
                    {where_clause}
                    ORDER BY created_at DESC
                    {limit_clause}
                '''
                
                cursor.execute(query, params)
                jobs = []
                for row in cursor.fetchall():
                    job = dict(row) 
                    # Parse raw_summary JSON if it exists
                    if job['raw_summary']:
                        try:
                            job['raw_summary'] = json.loads(job['raw_summary'])
                        except json.JSONDecodeError:
                            job['raw_summary'] = None
                    jobs.append(job)
                
                return jobs
        except Exception as e:
            logger.error(f"Failed to get backlog jobs: {e}")
            return []
    
    def delete_backlog_job(self, job_id: int) -> bool:
        """Soft delete a backlog job."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE backlog_jobs SET is_deleted = 1 WHERE id = ?',
                    (job_id,)
                )
                success = cursor.rowcount > 0
                conn.commit()
                if success:
                    logger.info(f"Backlog job {job_id} marked as deleted")
                return success
        except Exception as e:
            logger.error(f"Failed to delete backlog job {job_id}: {e}")
            return False
    
    def update_job_progress(self, job_id: str, progress: int, current_action: str = None, 
                           current_agent: str = None, force_write: bool = False) -> bool:
        """
        Update job progress with throttled database writes.
        
        Args:
            job_id: Job ID (matches raw_summary.job_id)
            progress: Progress percentage (0-100)
            current_action: Current action description
            current_agent: Current agent name
            force_write: Force write even if recently updated
            
        Returns:
            bool: True if update was written to DB, False if throttled
        """
        import hashlib
        import time
        
        try:
            # Generate etag from progress data for conditional updates
            etag_data = f"{progress}:{current_action}:{current_agent}"
            new_etag = hashlib.md5(etag_data.encode()).hexdigest()[:8]
            
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                
                # Find job by job_id in raw_summary
                cursor.execute("""
                    SELECT id, progress, last_progress_update, progress_etag
                    FROM backlog_jobs 
                    WHERE raw_summary LIKE ? AND is_deleted = 0
                    ORDER BY created_at DESC LIMIT 1
                """, (f'%"job_id":"{job_id}"%',))
                
                result = cursor.fetchone()
                if not result:
                    logger.debug(f"No backlog job found with job_id: {job_id}")
                    return False
                
                db_id, old_progress, last_update, old_etag = result
                
                # Throttle writes: only update if progress changed significantly or forced
                current_time = time.time()
                last_update_time = 0
                if last_update:
                    try:
                        last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                        last_update_time = last_update_dt.timestamp()
                    except:
                        pass
                
                # Skip if recently updated and no significant change
                if not force_write and (current_time - last_update_time) < 2.0:
                    if old_etag == new_etag or abs((old_progress or 0) - progress) < 5:
                        return False  # Throttled
                
                # Update progress
                cursor.execute("""
                    UPDATE backlog_jobs 
                    SET progress = ?, current_action = ?, current_agent = ?,
                        last_progress_update = CURRENT_TIMESTAMP, progress_etag = ?
                    WHERE id = ?
                """, (progress, current_action, current_agent, new_etag, db_id))
                
                conn.commit()
                logger.debug(f"Progress updated for job {job_id}: {progress}% - {current_action}")
                return True
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning(f"Database locked during progress update for job {job_id}, skipping")
                return False
            logger.error(f"Failed to update job progress for {job_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")
            return False
    
    def get_job_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job progress from database by job_id.
        
        Args:
            job_id: Job ID (matches raw_summary.job_id)
            
        Returns:
            Dict with progress data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT progress, current_action, current_agent, 
                           last_progress_update, progress_etag, status
                    FROM backlog_jobs 
                    WHERE raw_summary LIKE ? AND is_deleted = 0
                    ORDER BY created_at DESC LIMIT 1
                """, (f'%"job_id":"{job_id}"%',))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return {
                    "progress": result["progress"] or 0,
                    "currentAction": result["current_action"],
                    "currentAgent": result["current_agent"],
                    "status": result["status"],
                    "lastUpdated": result["last_progress_update"],
                    "etag": result["progress_etag"],
                    "jobId": job_id
                }
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning(f"Database locked during progress read for job {job_id}")
                return None
            logger.error(f"Failed to get job progress for {job_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get job progress for {job_id}: {e}")
            return None
    
    def save_optimized_vision(self, user_id: str, original_vision: str, optimized_vision: str,
                            domains: list, quality_score: int, quality_rating: str,
                            optimization_feedback: dict = None, original_assessment: dict = None) -> int:
        """
        Save an optimized vision to the database.
        
        Args:
            user_id: User ID
            original_vision: Original vision statement
            optimized_vision: Optimized vision statement
            domains: List of domains with priorities
            quality_score: Quality score (0-100)
            quality_rating: Quality rating (e.g., EXCELLENT, GOOD)
            optimization_feedback: Optional feedback dictionary
            
        Returns:
            ID of the saved vision
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO optimized_visions 
                    (user_id, original_vision, optimized_vision, domains, 
                     quality_score, quality_rating, optimization_feedback)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    original_vision,
                    optimized_vision,
                    json.dumps(domains),
                    quality_score,
                    quality_rating,
                    json.dumps(optimization_feedback) if optimization_feedback else None
                ))
                
                vision_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Saved optimized vision {vision_id} for user {user_id}")
                return vision_id
                
        except Exception as e:
            logger.error(f"Failed to save optimized vision: {e}")
            raise
    
    def get_optimized_visions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get optimized visions for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of visions to return
            
        Returns:
            List of vision dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM optimized_visions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                visions = []
                for row in cursor.fetchall():
                    vision = dict(row)
                    # Parse JSON fields
                    if vision.get('domains'):
                        vision['domains'] = json.loads(vision['domains'])
                    if vision.get('optimization_feedback'):
                        vision['optimization_feedback'] = json.loads(vision['optimization_feedback'])
                    visions.append(vision)
                
                return visions
                
        except Exception as e:
            logger.error(f"Failed to get optimized visions: {e}")
            return []
    
    def create_vision_optimization_job(self, user_id: str, original_vision: str, domains: list) -> str:
        """
        Create a new vision optimization job.
        
        Args:
            user_id: User ID
            original_vision: Original vision text
            domains: List of domains
            
        Returns:
            Job ID
        """
        try:
            job_id = f"vision_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO vision_optimization_jobs 
                    (id, user_id, status, original_vision, domains)
                    VALUES (?, ?, 'pending', ?, ?)
                """, (job_id, user_id, original_vision, json.dumps(domains)))
                
                conn.commit()
                logger.info(f"Created vision optimization job {job_id}")
                return job_id
                
        except Exception as e:
            logger.error(f"Failed to create vision optimization job: {e}")
            raise
    
    def update_vision_job_status(self, job_id: str, status: str, optimized_vision_id: int = None, 
                                error_message: str = None, original_assessment: dict = None) -> bool:
        """
        Update vision optimization job status.
        
        Args:
            job_id: Job ID
            status: New status (processing, completed, failed)
            optimized_vision_id: ID of saved optimized vision (for completed jobs)
            error_message: Error message (for failed jobs)
            
        Returns:
            Success boolean
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status == 'processing':
                    cursor.execute("""
                        UPDATE vision_optimization_jobs 
                        SET status = ?, started_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (status, job_id))
                elif status == 'completed':
                    # Store original assessment as JSON
                    original_assessment_json = json.dumps(original_assessment) if original_assessment else None
                    cursor.execute("""
                        UPDATE vision_optimization_jobs 
                        SET status = ?, completed_at = CURRENT_TIMESTAMP, 
                            optimized_vision_id = ?, original_assessment = ?
                        WHERE id = ?
                    """, (status, optimized_vision_id, original_assessment_json, job_id))
                elif status == 'failed':
                    cursor.execute("""
                        UPDATE vision_optimization_jobs 
                        SET status = ?, completed_at = CURRENT_TIMESTAMP, 
                            error_message = ?
                        WHERE id = ?
                    """, (status, error_message, job_id))
                else:
                    cursor.execute("""
                        UPDATE vision_optimization_jobs 
                        SET status = ?
                        WHERE id = ?
                    """, (status, job_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to update vision job {job_id}: {e}")
            return False
    
    def get_vision_job_status(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get vision optimization job status.
        
        Args:
            job_id: Job ID
            user_id: User ID (for verification)
            
        Returns:
            Job status dictionary or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT j.*, v.optimized_vision, v.quality_score, v.quality_rating,
                           v.optimization_feedback as vision_optimization_feedback
                    FROM vision_optimization_jobs j
                    LEFT JOIN optimized_visions v ON j.optimized_vision_id = v.id
                    WHERE j.id = ? AND j.user_id = ?
                """, (job_id, user_id))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                job = dict(row)
                # Parse JSON fields
                if job.get('domains'):
                    job['domains'] = json.loads(job['domains'])
                if job.get('original_assessment'):
                    job['original_assessment'] = json.loads(job['original_assessment'])
                if job.get('optimization_feedback'):
                    job['optimization_feedback'] = json.loads(job['optimization_feedback'])
                if job.get('vision_optimization_feedback'):
                    job['optimization_feedback'] = json.loads(job['vision_optimization_feedback'])
                    
                return job
                
        except Exception as e:
            logger.error(f"Failed to get vision job {job_id}: {e}")
            return None
    
    def get_optimized_vision_by_id(self, vision_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific optimized vision by ID.
        
        Args:
            vision_id: Vision ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Vision dictionary or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM optimized_visions 
                    WHERE id = ? AND user_id = ?
                """, (vision_id, user_id))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                vision = dict(row)
                # Parse JSON fields
                if vision.get('domains'):
                    vision['domains'] = json.loads(vision['domains'])
                if vision.get('optimization_feedback'):
                    vision['optimization_feedback'] = json.loads(vision['optimization_feedback'])
                
                return vision
                
        except Exception as e:
            logger.error(f"Failed to get optimized vision {vision_id}: {e}")
            return None

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
        # Use the Database class method
        job_id = db.add_backlog_job(
            user_email=user_email,
            project_name=project_name,
            epics_generated=epics_generated,
            features_generated=features_generated,
            user_stories_generated=user_stories_generated,
            tasks_generated=tasks_generated,
            test_cases_generated=test_cases_generated,
            execution_time_seconds=execution_time_seconds,
            raw_summary=raw_summary
        )
        
        logger.info(f"Backlog job logged successfully with ID: {job_id}")
        return job_id
        
    except Exception as e:
        logger.error(f"Failed to add backlog job: {e}")
        raise


# =====================================================
# DOMAIN MANAGEMENT FUNCTIONS
# =====================================================

def get_all_domains(include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Get all available domains with their subdomains."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            where_clause = "" if include_inactive else "WHERE d.is_active = TRUE"
            
            cursor.execute(f'''
                SELECT 
                    d.id, d.domain_key, d.display_name, d.description, 
                    d.icon_name, d.color_code, d.is_active, d.sort_order
                FROM domains d
                {where_clause}
                ORDER BY d.sort_order, d.display_name
            ''')
            
            domains = []
            for row in cursor.fetchall():
                domain = dict(row)
                
                # Get subdomains for this domain
                cursor.execute('''
                    SELECT id, subdomain_key, display_name, description, is_active, sort_order
                    FROM subdomains 
                    WHERE domain_id = ? AND is_active = TRUE
                    ORDER BY sort_order, display_name
                ''', (domain['id'],))
                
                domain['subdomains'] = [dict(sub_row) for sub_row in cursor.fetchall()]
                domains.append(domain)
            
            return domains
            
    except Exception as e:
        logger.error(f"Failed to get domains: {e}")
        return []

def get_domain_patterns(domain_id: int, subdomain_id: int = None) -> List[str]:
    """Get patterns for domain detection."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            if subdomain_id:
                cursor.execute('''
                    SELECT pattern_value FROM domain_patterns 
                    WHERE domain_id = ? AND (subdomain_id = ? OR subdomain_id IS NULL) 
                    AND is_active = TRUE
                    ORDER BY weight DESC
                ''', (domain_id, subdomain_id))
            else:
                cursor.execute('''
                    SELECT pattern_value FROM domain_patterns 
                    WHERE domain_id = ? AND subdomain_id IS NULL 
                    AND is_active = TRUE
                    ORDER BY weight DESC
                ''', (domain_id,))
            
            return [row[0] for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Failed to get domain patterns: {e}")
        return []

def get_domain_user_types(domain_id: int, subdomain_id: int = None) -> Dict[str, Dict[str, Any]]:
    """Get user types for a domain."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if subdomain_id:
                cursor.execute('''
                    SELECT user_type_key, display_name, description, user_patterns
                    FROM domain_user_types 
                    WHERE domain_id = ? AND (subdomain_id = ? OR subdomain_id IS NULL)
                    AND is_active = TRUE
                    ORDER BY sort_order, display_name
                ''', (domain_id, subdomain_id))
            else:
                cursor.execute('''
                    SELECT user_type_key, display_name, description, user_patterns
                    FROM domain_user_types 
                    WHERE domain_id = ? AND subdomain_id IS NULL
                    AND is_active = TRUE
                    ORDER BY sort_order, display_name
                ''', (domain_id,))
            
            user_types = {}
            for row in cursor.fetchall():
                row_dict = dict(row)
                patterns = json.loads(row_dict['user_patterns']) if row_dict['user_patterns'] else []
                user_types[row_dict['user_type_key']] = {
                    'display_name': row_dict['display_name'],
                    'description': row_dict['description'],
                    'patterns': patterns
                }
            
            return user_types
            
    except Exception as e:
        logger.error(f"Failed to get domain user types: {e}")
        return {}

def get_domain_vocabulary(domain_id: int, subdomain_id: int = None, category: str = None) -> List[str]:
    """Get vocabulary terms for a domain."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            where_conditions = ["domain_id = ?", "is_active = TRUE"]
            params = [domain_id]
            
            if subdomain_id:
                where_conditions.append("(subdomain_id = ? OR subdomain_id IS NULL)")
                params.append(subdomain_id)
            else:
                where_conditions.append("subdomain_id IS NULL")
            
            if category:
                where_conditions.append("category = ?")
                params.append(category)
            
            query = f'''
                SELECT term FROM domain_vocabulary 
                WHERE {" AND ".join(where_conditions)}
                ORDER BY term
            '''
            
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Failed to get domain vocabulary: {e}")
        return []

def save_project_domains(project_id: str, domain_selections: List[Dict[str, Any]], selected_by: str):
    """Save domain selections for a project."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing selections for this project
            cursor.execute('DELETE FROM project_domains WHERE project_id = ?', (project_id,))
            
            # Insert new selections
            for selection in domain_selections:
                cursor.execute('''
                    INSERT INTO project_domains 
                    (project_id, domain_id, subdomain_id, is_primary, weight, selected_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    selection['domain_id'],
                    selection.get('subdomain_id'),
                    selection.get('is_primary', False),
                    selection.get('weight', 1.0),
                    selected_by
                ))
            
            conn.commit()
            logger.info(f"Saved {len(domain_selections)} domain selections for project {project_id}")
            
    except Exception as e:
        logger.error(f"Failed to save project domains: {e}")
        raise

def get_project_domains(project_id: str) -> List[Dict[str, Any]]:
    """Get domain selections for a project."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    pd.domain_id, pd.subdomain_id, pd.is_primary, pd.weight,
                    d.domain_key, d.display_name as domain_name,
                    s.subdomain_key, s.display_name as subdomain_name
                FROM project_domains pd
                JOIN domains d ON pd.domain_id = d.id
                LEFT JOIN subdomains s ON pd.subdomain_id = s.id
                WHERE pd.project_id = ?
                ORDER BY pd.is_primary DESC, pd.weight DESC, d.display_name
            ''', (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        logger.error(f"Failed to get project domains: {e}")
        return []

def submit_domain_request(request_data: Dict[str, Any]) -> str:
    """Submit a new domain request."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO domain_requests 
                (requested_by, request_type, parent_domain_id, requested_domain_key, 
                 requested_display_name, justification, proposed_patterns, 
                 proposed_user_types, proposed_vocabulary, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_data['requested_by'],
                request_data['request_type'],
                request_data.get('parent_domain_id'),
                request_data.get('requested_domain_key'),
                request_data.get('requested_display_name'),
                request_data['justification'],
                json.dumps(request_data.get('proposed_patterns', [])),
                json.dumps(request_data.get('proposed_user_types', [])),
                json.dumps(request_data.get('proposed_vocabulary', [])),
                request_data.get('priority', 'medium')
            ))
            
            request_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Domain request submitted: {request_id}")
            return str(request_id)
            
    except Exception as e:
        logger.error(f"Failed to submit domain request: {e}")
        raise

def get_domain_requests(status: str = None, user_id: str = None) -> List[Dict[str, Any]]:
    """Get domain requests with optional filtering."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            where_conditions = []
            params = []
            
            if status:
                where_conditions.append("status = ?")
                params.append(status)
            
            if user_id:
                where_conditions.append("requested_by = ?")
                params.append(user_id)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            cursor.execute(f'''
                SELECT 
                    dr.*, 
                    d.display_name as parent_domain_name
                FROM domain_requests dr
                LEFT JOIN domains d ON dr.parent_domain_id = d.id
                {where_clause}
                ORDER BY dr.created_at DESC
            ''', params)
            
            requests = []
            for row in cursor.fetchall():
                request_dict = dict(row)
                
                # Parse JSON fields
                for json_field in ['proposed_patterns', 'proposed_user_types', 'proposed_vocabulary']:
                    if request_dict[json_field]:
                        request_dict[json_field] = json.loads(request_dict[json_field])
                
                requests.append(request_dict)
            
            return requests
            
    except Exception as e:
        logger.error(f"Failed to get domain requests: {e}")
        return []

def get_all_domains() -> List[Dict[str, Any]]:
    """Get all domains from the database."""
    try:
        db = Database()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id,
                    domain_key,
                    display_name,
                    description,
                    is_active
                FROM domains
                WHERE is_active = 1
                ORDER BY display_name
            ''')
            
            domains = []
            for row in cursor.fetchall():
                domains.append(dict(row))
            
            return domains
            
    except Exception as e:
        logger.error(f"Failed to get all domains: {e}")
        return []

# Database instance for module-level functions
_db_instance = None

def _get_db_instance():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

# Optimized Visions Methods
def save_optimized_vision(user_id: str, original_vision: str, optimized_vision: str,
                          domains: List[Dict[str, Any]], quality_score: int, quality_rating: str,
                          optimization_feedback: Dict[str, Any] = None) -> int:
    """Save an optimized vision and return its ID."""
    try:
        db = _get_db_instance()
        with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO optimized_visions (
                        user_id, original_vision, optimized_vision, domains,
                        quality_score, quality_rating, optimization_feedback
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, original_vision, optimized_vision, json.dumps(domains),
                    quality_score, quality_rating, 
                    json.dumps(optimization_feedback) if optimization_feedback else None
                ))
                vision_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Optimized vision saved with ID: {vision_id}")
                return vision_id
    except Exception as e:
        logger.error(f"Failed to save optimized vision: {e}")
        raise
    
def get_optimized_visions(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get optimized visions for a user."""
    try:
        db = _get_db_instance()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                    SELECT * FROM optimized_visions
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
            ''', (user_id, limit))
            
            visions = []
            for row in cursor.fetchall():
                vision = dict(row)
                # Parse JSON fields
                vision['domains'] = json.loads(vision['domains']) if vision['domains'] else []
                vision['optimization_feedback'] = json.loads(vision['optimization_feedback']) if vision['optimization_feedback'] else {}
                visions.append(vision)
            
            return visions
    except Exception as e:
        logger.error(f"Failed to get optimized visions: {e}")
        return []
    
def get_optimized_vision_by_id(vision_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific optimized vision by ID."""
    try:
        db = _get_db_instance()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM optimized_visions WHERE id = ?', (vision_id,))
            row = cursor.fetchone()
            
            if row:
                vision = dict(row)
                vision['domains'] = json.loads(vision['domains']) if vision['domains'] else []
                vision['optimization_feedback'] = json.loads(vision['optimization_feedback']) if vision['optimization_feedback'] else {}
                return vision
            return None
    except Exception as e:
        logger.error(f"Failed to get optimized vision {vision_id}: {e}")
        return None
    
def link_backlog_to_optimized_vision(backlog_job_id: int, optimized_vision_id: int) -> bool:
    """Link a backlog job to the optimized vision it was created from."""
    try:
        db = _get_db_instance()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO backlog_vision_mapping (backlog_job_id, optimized_vision_id)
                VALUES (?, ?)
            ''', (backlog_job_id, optimized_vision_id))
            conn.commit()
            logger.info(f"Linked backlog job {backlog_job_id} to optimized vision {optimized_vision_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to link backlog to optimized vision: {e}")
        return False
    
def get_backlogs_from_optimized_vision(optimized_vision_id: int) -> List[Dict[str, Any]]:
    """Get all backlog jobs created from a specific optimized vision."""
    try:
        db = _get_db_instance()
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT bj.* FROM backlog_jobs bj
                JOIN backlog_vision_mapping bvm ON bj.id = bvm.backlog_job_id
                WHERE bvm.optimized_vision_id = ?
                ORDER BY bj.created_at DESC
            ''', (optimized_vision_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to get backlogs from optimized vision: {e}")
        return []
