# Active Prompt Files

This document clarifies which prompt files are actually used during workflow execution.

## Currently Active Prompts (Used in Production)

Based on `config/settings.yaml`, these are the prompt files actually used:

| Agent | Active Prompt File | Status |
|-------|-------------------|---------|
| **Epic Strategist** | `prompts/epic_strategist.txt` | ✅ Streamlined (42 lines) |
| **Feature Decomposer** | `prompts/feature_decomposer_agent.txt` | ✅ Streamlined (56 lines) |
| **User Story Decomposer** | `prompts/user_story_decomposer.txt` | ✅ Streamlined (~60 lines) |
| **Developer Agent** | `prompts/developer_agent.txt` | ✅ Streamlined (46 lines) |
| **QA Lead Agent** | `prompts/qa_lead_agent.txt` | Original |
| **Test Plan Agent** | `prompts/test_plan_agent.txt` | Original |
| **Test Suite Agent** | `prompts/test_suite_agent.txt` | Original |
| **Test Case Agent** | `prompts/test_case_agent.txt` | Original |
| **Backlog Sweeper** | `prompts/backlog_sweeper_agent.txt` | Original |

## Backup/Alternative Versions (NOT Used)

These files exist but are NOT actively used:

| File | Purpose |
|------|---------|
| `epic_strategist_original.txt` | Backup of original verbose prompt (111 lines) |
| `epic_strategist_v2.txt` | Intermediate version during development |
| `feature_decomposer_agent_original.txt` | Backup of original prompt (76 lines) |
| `user_story_decomposer_original.txt` | Backup of original prompt (78 lines) |
| `developer_agent_original.txt` | Backup of original prompt (93 lines) |
| `developer_agent_enhanced.txt` | Enhanced version with additional fields (not implemented) |

## How Prompts Are Loaded

1. **Configuration**: `config/settings.yaml` specifies the prompt file for each agent
2. **Prompt Manager**: `utils/prompt_manager.py` loads all `.txt` files from the `prompts/` directory
3. **Agent Usage**: Each agent requests its template by name (e.g., "epic_strategist")
4. **Template Resolution**: The prompt manager strips `.txt` and uses the filename as the template name

## Important Notes

- The streamlined versions are the active ones (no suffix)
- Original versions are kept for reference only
- The prompt manager loads ALL `.txt` files but only uses what agents request
- Agent names in code must match the prompt filenames (minus `.txt`)

## Verifying Active Prompts

To verify which prompt an agent is using:

1. Check `config/settings.yaml` for the `prompt_file` setting
2. Or run: `grep -n "prompt_file" config/settings.yaml`
3. The actual prompt content is in the file specified

## Future Cleanup

Consider removing the backup files after confirming the streamlined versions are stable:
- `*_original.txt` files
- `*_v2.txt` files
- `developer_agent_enhanced.txt` (unless planning to implement)

This would reduce confusion and make it clear which prompts are active.