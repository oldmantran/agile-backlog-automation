import sqlite3
import sys

job_id = "job_20250716_125104"

try:
    conn = sqlite3.connect('backlog_jobs.db')
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Available tables: {tables}")
    
    # Try to find the job in any table that might exist
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT * FROM {table_name} WHERE job_id = ?", (job_id,))
            result = cursor.fetchone()
            if result:
                print(f"Job found in table {table_name}: {result}")
                break
        except Exception as e:
            print(f"Error querying table {table_name}: {e}")
    else:
        print(f"Job {job_id} not found in any table")
    
    conn.close()
except Exception as e:
    print(f"Error accessing database: {e}")
