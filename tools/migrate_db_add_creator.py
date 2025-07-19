#!/usr/bin/env python3
"""
Database migration script to add the creator column to the backlog_jobs table.
"""

import sqlite3
import os

def migrate_database():
    """Add the creator column to the backlog_jobs table if it doesn't exist."""
    
    db_path = "backlog_jobs.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Creating new database...")
        # Import and run the database initialization
        from db import init_db
        init_db()
        print("✅ New database created with creator column.")
        return
    
    print(f"Migrating database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the creator column already exists
        cursor.execute("PRAGMA table_info(backlog_jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'creator' in columns:
            print("✅ Creator column already exists. No migration needed.")
            return
        
        print("🔧 Adding creator column to backlog_jobs table...")
        
        # Add the creator column with a default value
        cursor.execute("""
            ALTER TABLE backlog_jobs 
            ADD COLUMN creator TEXT DEFAULT 'user'
        """)
        
        # Update existing records to have 'user' as creator
        cursor.execute("""
            UPDATE backlog_jobs 
            SET creator = 'user' 
            WHERE creator IS NULL
        """)
        
        # Commit the changes
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("   - Added 'creator' column to backlog_jobs table")
        print("   - Set default value to 'user' for existing records")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(backlog_jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'creator' in columns:
            print("✅ Verification: creator column is now present in the table.")
        else:
            print("❌ Verification failed: creator column not found.")
            
    except sqlite3.Error as e:
        print(f"❌ Database migration failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database() 