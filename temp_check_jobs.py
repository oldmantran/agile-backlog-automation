import sqlite3

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:')
for row in cursor.fetchall():
    print(row)
conn.close()
