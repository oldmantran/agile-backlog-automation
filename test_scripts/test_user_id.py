#!/usr/bin/env python3
"""Test user ID resolution."""

from utils.user_id_resolver import user_id_resolver
from utils.unified_llm_config import get_agent_config

# Test user ID resolution
user_id = user_id_resolver.get_default_user_id()
print(f"Default user ID: {user_id}")

# Test agent config retrieval
agents = ['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_lead_agent']

for agent_name in agents:
    config = get_agent_config(agent_name, user_id)
    print(f"\n{agent_name}:")
    print(f"  Provider: {config.provider}")
    print(f"  Model: {config.model}")
    print(f"  Preset: {config.preset}")
    print(f"  Source: {config.source}")