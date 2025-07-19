import sqlite3

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Check table structure
cursor.execute('PRAGMA table_info(backlog_jobs)')
columns = cursor.fetchall()
print('Database columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

print('\nLatest job:')
cursor.execute('SELECT * FROM backlog_jobs ORDER BY id DESC LIMIT 1')
result = cursor.fetchone()
if result:
    print(f'ID: {result[0]}')
    print(f'Project Name: {result[2]}')
    print(f'Status: {result[12]}')
    print(f'Creator: {result[13]}')
else:
    print('No jobs found')

conn.close() 