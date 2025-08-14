#!/usr/bin/env python3
"""Test agent-specific configuration loading."""

from utils.unified_llm_config import get_agent_config

agents = ['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_lead_agent']

print("Testing agent-specific configurations for user 'default_user':")
print("-" * 70)

for agent_name in agents:
    config = get_agent_config(agent_name, 'default_user')
    print(f"{agent_name:30s}: {config.provider}:{config.model:15s} (source: {config.source})")