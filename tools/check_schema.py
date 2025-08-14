#!/usr/bin/env python3
"""Check database schema"""

import sqlite3

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(llm_configurations)")
columns = cursor.fetchall()

print("LLM Configurations table schema:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

conn.close()