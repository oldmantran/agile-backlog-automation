#!/usr/bin/env python3
"""Test the user ID flow from API to agents."""

import requests
import json

# Test 1: Check current user endpoint
print("1. Testing /api/user/current endpoint...")
try:
    response = requests.get("http://localhost:8000/api/user/current")
    if response.status_code == 200:
        data = response.json()
        print(f"   Success: {data}")
        user_id = data.get('data', {}).get('user_id')
        print(f"   User ID: {user_id}")
    else:
        print(f"   Failed: Status {response.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Check agent configuration loading
print("\n2. Testing agent configuration loading...")
from utils.unified_llm_config import get_agent_config

agents = ['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_lead_agent']

for agent_name in agents:
    config = get_agent_config(agent_name, "1")
    print(f"   {agent_name:30s}: {config.provider}:{config.model:15s} (source: {config.source})")

# Test 3: Check database configurations
print("\n3. Checking database configurations...")
import sqlite3
conn = sqlite3.connect('backlog_jobs.db')
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT user_id FROM llm_configurations WHERE is_active=1")
user_ids = cursor.fetchall()
print(f"   Active user IDs in llm_configurations: {[uid[0] for uid in user_ids]}")

cursor.execute("SELECT DISTINCT user_id FROM user_settings WHERE setting_type='llm_config'")
user_ids = cursor.fetchall()
print(f"   User IDs in user_settings: {[uid[0] for uid in user_ids]}")

conn.close()

print("\n✅ All user IDs should be '1' now")