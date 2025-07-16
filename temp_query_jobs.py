import json

# Check the most recent backlog file
with open('output/backlog_20250716_143742.json', 'r') as f:
    data = json.load(f)

print(f'Epics: {len(data.get("epics", []))}')
print(f'Features: {len(data.get("features", []))}')
print(f'User Stories: {len(data.get("user_stories", []))}')
print(f'Tasks: {len(data.get("tasks", []))}')
print(f'Test Cases: {len(data.get("test_cases", []))}')
