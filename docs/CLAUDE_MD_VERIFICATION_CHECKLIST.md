# CLAUDE.md Verification Checklist

## How to Use This Checklist
1. Go through each section
2. Mark items as [✓] Verified, [✗] Incorrect, or [?] Unclear
3. Add notes about what needs to be updated
4. Update CLAUDE.md based on findings

## 1. Development Commands

### Backend Commands
- [ ] `python unified_api_server.py` - Start API server
- [ ] `python -m pytest <test_file.py>::<test_function>` - Run single test
- [ ] `pip install -r requirements.txt` - Install dependencies

### Frontend Commands
- [ ] `cd frontend && npm start` - Start dev server
- [ ] `cd frontend && npm run build` - Build production
- [ ] `cd frontend && npm test` - Run tests

### Testing Scripts (Verify these exist)
- [ ] `python tools/test_ollama_integration.py`
- [ ] `python tools/test_ado_connection.py`
- [ ] `python tools/test_complete_workflow.py`
- [ ] `tools/run_regression_tests.bat`
- [ ] `python tools/pre_commit_check.py`
- [ ] `python tests/test_core_smoke.py`
- [ ] `python tests/test_vision_integration.py`

## 2. Quality Standards

### Current Claims
- [ ] "All work items must achieve EXCELLENT rating (80+ score)"
  - **Check**: Look in `config/quality_config.py` for actual threshold
  - **Check**: Search for "minimum_quality_score" in agents
  
- [ ] "System fails cleanly rather than create placeholder items"
  - **Check**: Look for fallback generation in agents
  - **Check**: Search for "generic" or "placeholder" in agent code

## 3. Architecture Claims

### Agent Pipeline
- [ ] Epic Strategist exists at `agents/epic_strategist.py`
- [ ] Feature Decomposer exists at `agents/feature_decomposer_agent.py`
- [ ] User Story Decomposer exists at `agents/user_story_decomposer_agent.py`
- [ ] Developer Agent exists at `agents/developer_agent.py`
- [ ] QA Lead Agent exists at `agents/qa_lead_agent.py`

### Authentication
- [ ] "Complete JWT authentication system"
  - **Check**: Look in `auth/` directory for JWT implementation
  - **Check**: Search for "jwt" in authentication files

## 4. Recent Updates (August 2025)

### Verify These Features Exist
- [ ] Streamlined Agent Prompts (check prompt files)
- [ ] Domain-Specific Task Generation (check developer agent)
- [ ] Two-Phase Workflow (check for "Add Testing" button)
- [ ] Hybrid Progress Tracking (check for SSE + polling)

## 5. Performance Claims

### Hardware Tiers
- [ ] "10-15 minutes" for High tier (16+ cores)
- [ ] "15-25 minutes" for Medium tier (8+ cores)
- [ ] "25-35 minutes" for Low tier (4+ cores)
  - **Check**: Look for performance tier logic in code
  - **Check**: Search for actual timing data in logs

## 6. Critical Guidelines

### Unicode Prevention
- [ ] "Never use emojis - causes Windows crashes"
  - **Check**: Search for emoji usage in recent code
  - **Check**: Verify safe_logger is being used

### LLM Configuration
- [ ] "Single source of truth via get_agent_config()"
  - **Check**: Verify this function exists and is used
  - **Check**: Look for other LLM config methods

## 7. File/Directory Structure

### Verify These Directories Exist
- [ ] `agents/` - AI agent implementations
- [ ] `agents/qa/` - QA sub-agents
- [ ] `supervisor/` - Workflow orchestration
- [ ] `frontend/src/` - React application
- [ ] `auth/` - Authentication system
- [ ] `utils/` - Utilities
- [ ] `config/` - Configuration
- [ ] `tools/` - Development scripts
- [ ] `prompts/` - Agent prompts
- [ ] `docs/` - Documentation

## Common Discrepancy Patterns

1. **Version Drift**: Features described but later modified/removed
2. **Naming Changes**: Files/functions renamed but docs not updated
3. **Threshold Changes**: Quality scores, timeouts changed
4. **Feature Flags**: Some features may be disabled/optional
5. **Platform Differences**: Windows vs Linux paths/commands

## Update Process

1. **Date Stamp**: Add "Last Verified: [DATE]" to each section
2. **Version Tags**: Tag claims with version when added
3. **Deprecation**: Mark outdated info as "DEPRECATED as of [DATE]"
4. **Conditionals**: Add "If X enabled" for optional features
