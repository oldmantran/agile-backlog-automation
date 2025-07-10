# Enhanced Backlog Sweeper: Targeted + Scheduled Sweeps

## 🎯 Current State Analysis

### ✅ **Already Working:**
1. **Targeted Sweeps**: Supervisor can call specific validations
   - `sweeper.validate_epics(epics)` 
   - `sweeper.validate_epic_feature_relationships(epics)`
   - `sweeper.validate_feature_user_story_relationships(epics)`
   - `sweeper.validate_user_story_tasks(epics)`
   - `sweeper.validate_test_artifacts(epics)`

2. **Scheduled Sweeps**: Basic scheduling exists
   - Uses APScheduler for recurring sweeps
   - Configurable via cron expression in settings.yaml
   - Calls `run_sweep()` for comprehensive validation

### 🔧 **Enhancements Needed:**

1. **Enhanced Targeted Sweeps**:
   - Supervisor calls after each agent stage
   - Immediate remediation of found issues
   - Stage-specific validation with immediate feedback

2. **Improved Scheduling**:
   - Better separation between targeted and scheduled sweeps
   - Different reporting behavior for each type
   - Configuration for different sweep frequencies

## 🚀 **Enhanced Implementation Plan:**

### 1. **Supervisor Integration** (Targeted Sweeps)
```python
# After each agent stage:
def _execute_stage_with_validation(self, stage, data):
    # Execute agent stage
    result = self._execute_stage(stage, data)
    
    # Run targeted validation
    discrepancies = self._run_targeted_sweep(stage)
    
    # Immediately remediate if issues found
    if discrepancies:
        self._immediate_remediation(discrepancies)
    
    return result

def _run_targeted_sweep(self, stage):
    sweeper = self._get_sweeper_agent()
    return sweeper.run_targeted_sweep(stage, self.workflow_data)
```

### 2. **Enhanced Sweeper Methods**
```python
def run_targeted_sweep(self, stage, workflow_data, immediate_callback=True):
    # Run stage-specific validation
    # Report immediately to supervisor for remediation
    
def run_scheduled_sweep(self):
    # Run comprehensive validation
    # Report findings but don't expect immediate action
```

### 3. **Enhanced Configuration**
```yaml
agents:
  backlog_sweeper_agent:
    enabled: true
    
    # Targeted sweeps (supervisor-initiated)
    targeted_sweeps:
      enabled: true
      immediate_remediation: true
      stages:
        - epic_strategist
        - feature_decomposer_agent
        - user_story_decomposer_agent
        - developer_agent
        - qa_tester_agent
    
    # Scheduled sweeps (autonomous)
    scheduled_sweeps:
      enabled: true
      schedule: "0 12 * * *"  # Daily at 12:00 UTC
      comprehensive: true
      report_only: false  # Set to true to only report, not remediate
```

This design allows both use cases while maintaining clean separation!
