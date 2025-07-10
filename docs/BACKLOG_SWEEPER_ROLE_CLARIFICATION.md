# Backlog Sweeper Agent Role and Flow

## 🎯 Backlog Sweeper Agent Role

The Backlog Sweeper Agent is a **monitoring and reporting agent** that:

1. **Scans the backlog** for quality issues, missing information, and violations
2. **Reports findings to the Supervisor** with specific agent assignment suggestions
3. **Does NOT modify work items directly** - only observes and reports
4. **Provides actionable recommendations** for the supervisor to route to appropriate agents

## 🔄 Proper Flow

### 1. Supervisor Initiates Sweep
```python
# Supervisor calls the sweeper
sweeper = self._get_sweeper_agent()
report = sweeper.run_sweep()  # Sweeper reports back to supervisor via callback
```

### 2. Sweeper Scans and Reports
```python
# In BacklogSweeperAgent.run_sweep()
discrepancies = []

# Scan for issues
discrepancies.extend(self.scrape_and_validate_work_items())
discrepancies.extend(self.validate_relationships())
discrepancies.extend(self.monitor_for_decomposition())

# Group by suggested agent
agent_assignments = {}
for discrepancy in discrepancies:
    agent = discrepancy.get('suggested_agent', 'supervisor')
    if agent not in agent_assignments:
        agent_assignments[agent] = []
    agent_assignments[agent].append(discrepancy)

# Create report
report = {
    'agent_assignments': agent_assignments,
    'discrepancies_by_priority': {...},
    'recommended_actions': [...]
}

# Report to supervisor (this triggers supervisor.receive_sweeper_report)
self.report_to_supervisor(report)
```

### 3. Supervisor Routes to Agents
```python
# In supervisor.receive_sweeper_report()
def receive_sweeper_report(self, report):
    agent_assignments = report.get('agent_assignments', {})
    
    for agent_name, discrepancies in agent_assignments.items():
        if discrepancies:
            self._route_discrepancies_to_agent(agent_name, discrepancies)

def _route_discrepancies_to_agent(self, agent_name, discrepancies):
    if agent_name == 'feature_decomposer_agent':
        self._handle_feature_decomposer_discrepancies(discrepancies)
    elif agent_name == 'user_story_decomposer_agent':
        self._handle_user_story_decomposer_discrepancies(discrepancies)
    # ... etc
```

### 4. Agents Remediate Issues
```python
# Each agent handles their assigned discrepancies
def _handle_feature_decomposer_discrepancies(self, work_item_groups):
    for wi_id, discrepancies in work_item_groups.items():
        # Agent performs remediation actions
        self.agents['feature_decomposer_agent'].remediate_discrepancy(discrepancies)
```

## 🔍 Example Discrepancy

When sweeper finds an issue:
```json
{
    "type": "missing_child_user_story",
    "work_item_id": 123,
    "work_item_type": "Feature", 
    "title": "User Authentication",
    "description": "Feature missing child User Story.",
    "severity": "high",
    "suggested_agent": "feature_decomposer_agent"  // Sweeper suggests who should fix it
}
```

The supervisor receives this and routes it to the `feature_decomposer_agent` for remediation.

## ✅ Key Principles

1. **Sweeper = Observer**: Never modifies work items, only reports issues
2. **Supervisor = Router**: Receives reports and routes to appropriate agents  
3. **Agents = Actors**: Actually fix the issues assigned to them
4. **Clear Separation**: Each component has a distinct, focused role

This ensures:
- Clean separation of concerns
- Traceable remediation workflow  
- Flexible routing logic
- Comprehensive monitoring without conflicts
