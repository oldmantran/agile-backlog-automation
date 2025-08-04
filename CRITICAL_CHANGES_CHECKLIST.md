# 🚨 CRITICAL CHANGES CHECKLIST

**Use this checklist EVERY TIME you modify core system components.**

## Pre-Change Checklist ✅

### 1. Impact Assessment
- [ ] What system components will this change affect?
- [ ] Could this break vision statement processing?
- [ ] Could this break template variable resolution?
- [ ] Could this break agent-supervisor communication?
- [ ] Could this break project context flow?

### 2. Backup Current State
- [ ] Run regression tests to ensure current state is working: `tools/run_regression_tests.bat`
- [ ] Document current behavior that should be preserved
- [ ] Note any existing test failures (if any)

### 3. Change Planning
- [ ] Document exactly what you're changing and why
- [ ] Identify the minimal change needed
- [ ] Plan how to test the change

## During Change ⚠️

### 4. Make Minimal Changes
- [ ] Change only what's necessary
- [ ] Avoid "while I'm here" improvements that aren't essential
- [ ] Keep related changes together in single commits

### 5. Test Incrementally  
- [ ] Test each logical change step
- [ ] Don't make multiple unrelated changes at once
- [ ] Verify imports still work after each change

## Post-Change Checklist ✅

### 6. MANDATORY Testing (Must ALL Pass)
- [ ] `python tools/pre_commit_check.py` - **MUST PASS 100%**
- [ ] `python tests/test_core_smoke.py` - **MUST PASS 100%**  
- [ ] `python tests/test_vision_integration.py` - **MUST PASS 100%**
- [ ] All critical imports work: `python -c "from unified_api_server import app; from supervisor.supervisor import WorkflowSupervisor"`

### 7. Functional Verification
- [ ] Start the application: `python unified_api_server.py`
- [ ] Access frontend at http://localhost:8000
- [ ] Try creating a new project with a vision statement
- [ ] Verify the project creation form works
- [ ] Check that domain selection works
- [ ] Verify settings page loads and saves

### 8. Integration Testing
- [ ] Run a complete mini-workflow test with include_test_artifacts=False
- [ ] Check that vision statement appears in generated work items
- [ ] Verify no template variable errors in logs
- [ ] Confirm agents can generate prompts without errors

## 🚨 FAILURE PROTOCOL

### If ANY Test Fails:
1. **STOP IMMEDIATELY** - do not continue
2. **Revert your changes** if possible
3. **Analyze the failure** - understand root cause
4. **Fix the issue** before proceeding
5. **Re-run ALL tests** before continuing

### Common Failure Patterns:
- **Template validation errors** → Check prompt_manager.py changes
- **Missing context variables** → Check project_context.py and supervisor.py
- **Agent initialization failures** → Check base_agent.py modifications
- **Import errors** → Check for circular imports or missing files

## 🎯 SPECIFIC COMPONENT GUIDELINES

### When Changing Template System (`utils/prompt_manager.py`):
- [ ] Test with empty context (agent initialization scenario)
- [ ] Test with full context (runtime scenario)  
- [ ] Verify all template variables resolve correctly
- [ ] Check both sync and async agent execution paths

### When Changing Agent System (`agents/base_agent.py`):
- [ ] Test agent initialization without context
- [ ] Test prompt generation with context
- [ ] Verify LLM provider switching still works
- [ ] Check that circuit breaker logic still functions

### When Changing Supervisor (`supervisor/supervisor.py`):
- [ ] Test context updates flow correctly to agents
- [ ] Verify workflow_data structure maintains integrity
- [ ] Check that progress callbacks still work
- [ ] Test both with and without Azure DevOps integration

### When Changing API Server (`unified_api_server.py`):
- [ ] Verify all endpoints still respond
- [ ] Test project creation end-to-end
- [ ] Check SSE progress streaming works
- [ ] Verify settings persistence works

## ⚡ QUICK VERIFICATION COMMANDS

```bash
# Quick smoke test (30 seconds)
python tools/pre_commit_check.py

# Full regression test (2-3 minutes)
tools/run_regression_tests.bat

# Manual verification (1 minute)
python unified_api_server.py
# Then visit http://localhost:8000 and try creating a project
```

## 📋 CHANGE LOG TEMPLATE

When you make changes, document them:

```
## Change: [Brief Description]
**Date**: [Date]
**Components Modified**: [List files changed]
**Reason**: [Why was this change needed]
**Risk Assessment**: [Low/Medium/High - likelihood of breaking core functionality]
**Testing Performed**: [What tests were run]
**Verification**: [How was the change verified to work]
```

---

**Remember: It's better to spend 5 minutes on testing than 2 hours debugging a regression.**