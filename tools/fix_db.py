import sqlite3

# Connect to database
conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Check current columns
cursor.execute("PRAGMA table_info(backlog_jobs)")
columns = [col[1] for col in cursor.fetchall()]
print('Current columns:', columns)

# Add missing columns
try:
    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN status TEXT DEFAULT 'completed'")
    print('Added status column')
except:
    print('status column already exists')

try:
    cursor.execute("ALTER TABLE backlog_jobs ADD COLUMN is_deleted INTEGER DEFAULT 0")
    print('Added is_deleted column')
except:
    print('is_deleted column already exists')

# Commit changes
conn.commit()

# Verify
cursor.execute("PRAGMA table_info(backlog_jobs)")
updated_columns = [col[1] for col in cursor.fetchall()]
print('Updated columns:', updated_columns)

conn.close()
print('Database migration completed!') 