import sqlite3
import json

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Get job 24 data
cursor.execute("SELECT id, project_name, raw_summary FROM backlog_jobs WHERE id = 24")
result = cursor.fetchone()

if result:
    job_id, project_name, raw_summary = result
    print(f"Job ID: {job_id}")
    print(f"Project Name: {project_name}")
    
    if raw_summary:
        data = json.loads(raw_summary)
        print(f"test_artifacts_included: {data.get('test_artifacts_included')}")
        print(f"Domain from Azure config: {data.get('azure_config', {}).get('areaPath')}")
        print(f"Job ID from raw_summary: {data.get('job_id')}")
    else:
        print("No raw_summary data")
        
# Also check if there's a report for job 24
cursor.execute("SELECT id FROM backlog_reports WHERE backlog_job_id = 24")
report = cursor.fetchone()
print(f"Has persisted report: {report is not None}")

conn.close()