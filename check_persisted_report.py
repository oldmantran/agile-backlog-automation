import sqlite3
import json

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

# Get the persisted report for job 24
cursor.execute("SELECT report_data FROM backlog_reports WHERE backlog_job_id = 24")
result = cursor.fetchone()

if result:
    report_data = json.loads(result[0])
    
    # Check vision statement
    vision = report_data.get('vision_statement', {})
    vision_text = vision.get('statement', '')
    
    print("Vision statement preview:")
    print(vision_text[:200] + "..." if len(vision_text) > 200 else vision_text)
    
    print("\nMetadata:")
    print(f"Project name: {report_data.get('metadata', {}).get('project_name')}")
    print(f"Domain: {report_data.get('metadata', {}).get('domain')}")
    
    print("\nWork items:")
    stats = report_data.get('work_item_statistics', {})
    print(f"Total generated: {stats.get('total_generated')}")
    print(f"Total uploaded: {stats.get('azure_devops_upload', {}).get('total_uploaded')}")
    
else:
    print("No persisted report found for job 24")

conn.close()