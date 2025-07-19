import sqlite3
import json

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()
cursor.execute('SELECT raw_summary FROM backlog_jobs WHERE id = 3')
result = cursor.fetchone()

if result and result[0]:
    summary = json.loads(result[0])
    print("Job 3 Details:")
    print(f"Project: {summary.get('project_name', 'Not found')}")
    print(f"Epics: {summary.get('epics_generated', 0)}")
    print(f"Features: {summary.get('features_generated', 0)}")
    print(f"User Stories: {summary.get('user_stories_generated', 0)}")
    print(f"Tasks: {summary.get('tasks_generated', 0)}")
    print(f"Test Cases: {summary.get('test_cases_generated', 0)}")
    
    # Check Azure integration
    ado_summary = summary.get('ado_summary', {})
    print(f"\nAzure DevOps Integration:")
    print(f"ADO Summary: {ado_summary}")
    
    # Check if there's any Azure config in the metadata
    if 'metadata' in summary:
        metadata = summary['metadata']
        print(f"\nMetadata:")
        print(f"Azure Config: {metadata.get('azure_config', 'Not found')}")
        
        # Check execution config
        exec_config = metadata.get('execution_config', {})
        print(f"Integrate Azure: {exec_config.get('integrate_azure', 'Not found')}")
    
    # Check if there's any Azure config in the workflow data
    if 'workflow_data' in summary:
        workflow_data = summary['workflow_data']
        if 'metadata' in workflow_data:
            azure_config = workflow_data['metadata'].get('azure_config', {})
            print(f"\nWorkflow Azure Config:")
            print(f"Organization URL: {azure_config.get('organization_url', 'Not set')}")
            print(f"Project: {azure_config.get('project', 'Not set')}")
            print(f"Area Path: {azure_config.get('area_path', 'Not set')}")
            print(f"Iteration Path: {azure_config.get('iteration_path', 'Not set')}")
    
else:
    print("No summary data found for job 3")

conn.close() 