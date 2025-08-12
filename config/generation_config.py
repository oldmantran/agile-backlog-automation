"""
Proactive generation configuration for all agents.

This module defines generation multipliers to improve work item quality
by generating more items upfront and selecting the best ones.
"""

# Generation multipliers for each agent type
# These values determine how many extra items to generate to account for quality filtering
GENERATION_MULTIPLIERS = {
    "epic_strategist": 2.0,        # Generate 2x epics (was 1.5x)
    "feature_decomposer": 2.0,     # Generate 2x features
    "user_story_decomposer": 2.0,  # Generate 2x user stories
    "developer_agent": 2.5         # Generate 2.5x tasks (highest rejection rate)
}

# Explanation of multipliers:
# - Epic Strategist: ~30% rejection rate, so 2x provides good buffer
# - Feature Decomposer: ~25% rejection rate, so 2x is sufficient
# - User Story Decomposer: ~15% rejection rate (best performer), but 2x ensures quality
# - Developer Agent: ~58% rejection rate (worst performer), needs 2.5x

def get_generation_multiplier(agent_name: str) -> float:
    """
    Get the generation multiplier for a specific agent.
    
    Args:
        agent_name: The name of the agent
        
    Returns:
        The generation multiplier (default 2.0 if not configured)
    """
    return GENERATION_MULTIPLIERS.get(agent_name, 2.0)

def get_generation_count(agent_name: str, target_count: int) -> int:
    """
    Calculate how many items to generate based on target count and multiplier.
    
    Args:
        agent_name: The name of the agent
        target_count: The desired number of quality items
        
    Returns:
        The number of items to generate upfront
    """
    multiplier = get_generation_multiplier(agent_name)
    return max(target_count, int(target_count * multiplier))