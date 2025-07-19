#!/usr/bin/env python3
"""
Database Migration Script
Adds missing columns to existing backlog_jobs table


import sqlite3
import os

def migrate_database():
    db_path = 'backlog_jobs.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Creating new database...")
        return
    
    print(f"Migrating database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if status column exists
        cursor.execute("PRAGMA table_info(backlog_jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Existing columns: {columns}")
        
        # Add status column if it doesn't exist
        if 'status' not in columns:
            print("Adding 'status' column...")
            cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN status TEXT DEFAULT 'completed'")
            print("✓ Added status column")
        else:
            print("✓ 'status' column already exists")
        
        # Add is_deleted column if it doesn't exist
        if 'is_deleted' not in columns:
            print("Adding 'is_deleted' column...")
            cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN is_deleted INTEGER DEFAULT 0")
            print("✓ Added 'is_deleted column")
        else:
            print("✓ 'is_deleted' column already exists")
        
        # Commit the changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(backlog_jobs)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
        print("✓ Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database migration failed: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\nMigration completed. You can now restart the server.")
    else:
        print("\nMigration failed. Please check the error messages above.") 