import sqlite3
import json

conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()
cursor.execute('SELECT id, project_data FROM backlog_jobs ORDER BY id DESC LIMIT 1')
result = cursor.fetchone()

if result and result[1]:
    job_id, project_data_json = result
    data = json.loads(project_data_json)
    print(f"Project Data for Job {job_id}:")
    
    # Check the structure
    if 'data' in data:
        project_data = data['data']
        print(f"Project Name: {project_data.get('basics', {}).get('name', 'Not found')}")
        
        # Check Azure configuration
        azure_config = project_data.get('azureConfig', {})
        print(f"\nAzure DevOps Configuration:")
        print(f"Organization URL: {azure_config.get('organizationUrl', 'Not set')}")
        print(f"Project: {azure_config.get('project', 'Not set')}")
        print(f"Area Path: {azure_config.get('areaPath', 'Not set')}")
        print(f"Iteration Path: {azure_config.get('iterationPath', 'Not set')}")
        print(f"Personal Access Token: {'Set' if azure_config.get('personalAccessToken') else 'Not set'}")
        
        # Check if any Azure config is provided
        has_any_config = any([
            azure_config.get('organizationUrl'),
            azure_config.get('project'),
            azure_config.get('areaPath'),
            azure_config.get('iterationPath'),
            azure_config.get('personalAccessToken')
        ])
        
        print(f"\nHas any Azure config: {has_any_config}")
        
        # Check if all required config is provided
        has_all_config = all([
            azure_config.get('organizationUrl'),
            azure_config.get('project'),
            azure_config.get('areaPath'),
            azure_config.get('iterationPath'),
            azure_config.get('personalAccessToken')
        ])
        
        print(f"Has all required Azure config: {has_all_config}")
        
    else:
        print("No 'data' field found in project data")
else:
    print("No project data found")

conn.close() 