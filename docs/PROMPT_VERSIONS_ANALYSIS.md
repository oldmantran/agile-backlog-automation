# Prompt Template Versions Analysis

## How Prompts Are Loaded

The `PromptTemplateManager` in `utils/prompt_manager.py` loads prompts based on the agent name:
- When an agent requests its prompt, it uses `prompt_manager.get_prompt(self.name, context)`
- The manager looks for `{agent_name}.txt` in the prompts folder
- Version suffixes like `_v2`, `_original`, `_enhanced` are NOT automatically loaded

## Which Prompts Are Actually Used

Based on the loading mechanism, here are the ACTIVE prompts:
- ✅ `epic_strategist.txt` - ACTIVE (not `epic_strategist_v2.txt` or `epic_strategist_original.txt`)
- ✅ `developer_agent.txt` - ACTIVE (not the enhanced or domain_enhanced versions)
- ✅ `feature_decomposer_agent.txt` - ACTIVE
- ✅ `user_story_decomposer.txt` - ACTIVE
- ✅ `backlog_sweeper_agent.txt` - ACTIVE
- ✅ `vision_optimizer_agent.txt` - ACTIVE (not `vision_optimizer.txt` without "_agent")
- ✅ `qa_lead_agent.txt` - ACTIVE
- ✅ `test_plan_agent.txt` - ACTIVE
- ✅ `test_suite_agent.txt` - ACTIVE
- ✅ `test_case_agent.txt` - ACTIVE

## Summary of Duplicate Prompt Files

### Epic Strategist (3 versions!)
1. `epic_strategist.txt` - Current version I just edited
2. `epic_strategist_v2.txt` - V2 version
3. `epic_strategist_original.txt` - Original backup

### Developer Agent (4 versions!!!)
1. `developer_agent.txt` - Base version
2. `developer_agent_original.txt` - Original backup
3. `developer_agent_enhanced.txt` - Enhanced version
4. `developer_agent_domain_enhanced.txt` - Domain-specific enhanced version

### Feature Decomposer Agent (2 versions)
1. `feature_decomposer_agent.txt` - Current version
2. `feature_decomposer_agent_original.txt` - Original backup

### User Story Decomposer (2 versions)
1. `user_story_decomposer.txt` - Current version (no "_agent" suffix)
2. `user_story_decomposer_original.txt` - Original backup

### Backlog Sweeper Agent (2 versions)
1. `backlog_sweeper_agent.txt` - Current version
2. `backlog_sweeper_agent_original.txt` - Original backup

### Vision Optimizer (2 versions with different names!)
1. `vision_optimizer.txt` - One version
2. `vision_optimizer_agent.txt` - Another version (with "_agent" suffix)

### Single Version Prompts (No duplicates)
- `qa_lead_agent.txt`
- `test_plan_agent.txt`
- `test_suite_agent.txt`
- `test_case_agent.txt`

## UNUSED/DUPLICATE Prompt Files (These should be deleted!)

### Inactive Versions:
- ❌ `epic_strategist_v2.txt` - NOT USED
- ❌ `epic_strategist_original.txt` - NOT USED  
- ❌ `developer_agent_original.txt` - NOT USED
- ❌ `developer_agent_enhanced.txt` - NOT USED
- ❌ `developer_agent_domain_enhanced.txt` - NOT USED (this might be the version with domain examples you wanted!)
- ❌ `feature_decomposer_agent_original.txt` - NOT USED
- ❌ `user_story_decomposer_original.txt` - NOT USED
- ❌ `backlog_sweeper_agent_original.txt` - NOT USED
- ❌ `vision_optimizer.txt` - NOT USED (missing "_agent" suffix)

## Critical Issues

1. **Wasted Enhancement Work**: The `developer_agent_domain_enhanced.txt` file likely contains the domain-specific enhancements but it's NOT being used!
2. **Confusing File Names**: Some agents require "_agent" suffix (vision_optimizer_agent) while others don't (user_story_decomposer)
3. **No Version Control Strategy**: Using file suffixes instead of git branches/tags
4. **Maintenance Nightmare**: 9 duplicate/unused prompt files cluttering the directory

## The Real Problem

When you asked me to "enhance developer agent prompt with domain-specific examples", I might have:
1. Created or edited `developer_agent_domain_enhanced.txt` - which is NOT being used
2. OR edited `developer_agent.txt` - which IS being used

Without checking git history, we can't know which enhancements are actually active!