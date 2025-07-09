# Comprehensive Agent Functions Summary

## 📁 base_agent.py - Base Agent Class
All other agents inherit from this foundation class:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize agent | name: str, config: Config | Agent instance | Sets up basic agent properties, API keys, and validates prompt template |
| `get_prompt` | Generate dynamic prompt | context: dict (optional) | str | Retrieves and processes prompt template with context variables |
| `run` | Execute agent | user_input: str, context: dict (optional) | str | Sends request to Grok API and returns assistant response |

## 📁 epic_strategist.py - Epic Strategy Agent
Strategic planning and epic-level work item management:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize epic strategist | config: Config | EpicStrategist instance | Inherits from base agent with "epic_strategist" name |
| `generate_epics` | Create strategic epics | product_vision: str, context: dict (optional) | list[dict] | Transforms product vision into structured epics with business value, priority, and timeline |

## 📁 decomposition_agent.py - Work Item Decomposition Agent
Hierarchical breakdown and structural organization:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize decomposer | config: Config | DecompositionAgent instance | Sets up agent with quality validator for work item enhancement |
| `decompose_epic` | Break epic into features | epic: dict, context: dict (optional) | list[dict] | Converts epics into **Features with business value ONLY** (no acceptance criteria) |
| `decompose_feature_to_user_stories` | Break feature into stories | feature: dict, context: dict (optional) | list[dict] | Creates **User Stories with acceptance criteria** from feature specifications |
| `run_with_template` | Execute with custom template | user_input: str, context: dict, template_name: str | str | Allows custom prompt template execution for specialized decomposition |
| `_create_fallback_user_stories` | Generate fallback stories | feature: dict | list[dict] | Creates basic user stories when AI processing fails |
| `_validate_and_enhance_user_stories` | Enhance story quality | user_stories: list | list[dict] | Validates and improves user story quality standards |
| `_enhance_single_user_story` | Enhance individual story | story: dict | dict | Adds metadata, validation, and quality improvements to single story |

## 📁 developer_agent.py - Development Task Agent
Technical implementation planning and task creation:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize developer agent | config: Config | DeveloperAgent instance | Sets up agent with quality validator for task management |
| `generate_tasks` | Create development tasks | feature: dict, context: dict (optional) | list[dict] | Generates technical tasks from feature specifications with tech stack context |
| `estimate_story_points` | Calculate story points | user_story: dict, context: dict (optional) | int | Estimates complexity using Fibonacci scale (1-13) based on story content |
| `_extract_json_from_response` | Parse JSON responses | response: str | str | Extracts JSON from various response formats (code blocks, plain text) |
| `_validate_and_enhance_tasks` | Enhance task quality | tasks: list | list[dict] | Validates and improves task quality standards |
| `_enhance_single_task` | Enhance individual task | task: dict | dict | Adds metadata, estimation, and quality improvements to single task |

## 📁 qa_tester_agent.py - Quality Assurance Agent
**USER STORY-FOCUSED** test planning, validation, and Azure DevOps test management:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize QA agent | config: Config | QATesterAgent instance | Sets up agent with quality validator and Azure DevOps test client |
| `generate_user_story_test_cases` | Create comprehensive test cases | user_story: dict, context: dict (optional) | list[dict] | **PRIMARY METHOD**: Generates test cases with boundary/failure scenarios for user stories |
| `validate_user_story_testability` | Analyze story testability | user_story: dict, context: dict (optional) | dict | Comprehensive testability analysis with acceptance criteria enhancement |
| `create_test_plan_structure` | Design test organization | feature: dict, context: dict (optional) | dict | Creates user story-focused test plan structure with recommendations |
| `enhance_acceptance_criteria` | Improve acceptance criteria | user_story: dict, context: dict (optional) | list | Enhances acceptance criteria to meet quality standards |
| `validate_acceptance_criteria_quality` | Validate AC standards | acceptance_criteria: list, story_context: dict (optional) | dict | Validates criteria against INVEST/BDD principles with QA recommendations |
| `ensure_test_organization` | Create ADO test structure | user_story: dict, required: bool | dict | Ensures test plans and suites exist in Azure DevOps for proper organization |
| `create_test_cases` | Create ADO test cases | user_story: dict, test_cases: list, require_organization: bool | list | Creates test cases in Azure DevOps with proper test suite organization |
| `create_test_cases_with_fallback` | Create tests with fallback | user_story: dict, test_cases: list | dict | Creates test cases with graceful error handling and detailed result reporting |
| `_format_test_steps` | Format test steps for ADO | test_case: dict | list | Converts test case data into Azure DevOps test step format |
| `_validate_and_enhance_test_cases` | Enhance test quality | test_cases: list | list[dict] | Validates and improves test case quality with boundary/failure focus |
| `_enhance_single_test_case` | Enhance individual test | test_case: dict | dict | Adds automation scoring, risk assessment, and execution complexity |
| `_classify_test_type` | Classify test types | test_case: dict | str | Categorizes tests (functional, boundary, security, performance, etc.) |
| `_calculate_automation_score` | Score automation potential | test_case: dict | int | Calculates automation suitability score (1-10) with reasoning |
| `_assess_test_risk` | Assess test risk level | test_case: dict | str | Determines risk level (high/medium/low) based on test characteristics |
| `_analyze_test_scenario` | Analyze scenario complexity | test_case: dict | dict | Identifies boundary conditions and failure scenarios in test cases |
| `_estimate_execution_complexity` | Estimate test complexity | test_case: dict | str | Estimates execution complexity (high/medium/low) based on test type and steps |
| `_estimate_execution_time` | Estimate execution time | complexity: str, test_type: str | int | Estimates test execution time in minutes based on complexity and type |
| `_analyze_acceptance_criteria` | Analyze AC completeness | user_story: dict | dict | Analyzes acceptance criteria for testability and enhancement needs |
| `_determine_coverage_type` | Determine coverage type | test_case: dict, user_story: dict | str | Identifies the type of test coverage provided (boundary, negative, etc.) |
| `_validate_test_coverage` | Validate coverage completeness | test_cases: list, user_story: dict, acceptance_criteria: list | dict | Validates comprehensive test coverage against story complexity |
| `_generate_fallback_analysis` | Generate fallback analysis | user_story: dict, criteria_analysis: dict | dict | Creates fallback testability analysis when AI processing fails |
| `_enhance_testability_analysis` | Enhance analysis quality | analysis: dict, user_story: dict | dict | Validates and enhances testability analysis with quality checks |

## 📁 backlog_sweeper_agent.py - Monitoring & Compliance Agent
Backlog monitoring, quality assurance, and discrepancy reporting (read-only):

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize sweeper | ado_client, supervisor_callback (optional), config (optional) | BacklogSweeperAgent instance | Sets up monitoring agent with validation rules and supervisor integration |
| `run_sweep` | Execute comprehensive sweep | None | dict | Performs full backlog analysis and generates structured findings report |
| `scrape_and_validate_work_items` | Validate all work items | None | list[dict] | Monitors all ADO work items for quality compliance and standards |
| `validate_relationships` | Check item hierarchies | None | list[dict] | Validates parent-child relationships and structural integrity |
| `monitor_for_decomposition` | Monitor decomposition needs | None | list[dict] | Identifies work items requiring decomposition or restructuring |
| `validate_dashboard_requirements` | Check reporting requirements | None | list[dict] | Validates dashboard and reporting configuration requirements |
| `report_to_supervisor` | Send findings to supervisor | report: dict | None | Reports structured findings to supervisor for intelligent agent routing |
| `_validate_acceptance_criteria` | Validate AC compliance | criteria_text: str, wi_id: int, title: str | list[dict] | Validates acceptance criteria against INVEST/SMART/BDD principles |
| `_generate_action_recommendations` | Generate remediation plan | discrepancies: list, dashboard_requirements: list | list[str] | Creates specific action recommendations with agent assignments |
| `get_logger` / `logger` | Access logging system | None | Logger | Provides logging functionality for monitoring activities |
| `scheduled_sweep` | Execute scheduled monitoring | None | None | Static method for automated scheduled sweep execution |

## 📁 supervisor/supervisor.py - Workflow Orchestration
Coordinates multi-agent workflows and manages the complete pipeline:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `__init__` | Initialize supervisor | config_path: str (optional) | WorkflowSupervisor instance | Sets up supervisor with configuration, agents, and logging |
| `_initialize_agents` | Create agent instances | None | dict | Initializes all agent instances with proper configuration |
| `configure_project_context` | Set project context | project_type: str, custom_context: dict | None | Configures project-specific context and prompt customization |
| `execute_workflow` | Run complete workflow | product_vision: str, stages: list, human_review: bool, azure_integration: bool, context: dict | dict | Orchestrates complete multi-agent pipeline from vision to ADO work items |
| `_execute_epic_generation` | Execute epic stage | None | None | Coordinates epic generation using Epic Strategist agent |
| `_execute_feature_decomposition` | Execute feature stage | None | None | Coordinates feature decomposition using Decomposition Agent |
| `_execute_user_story_decomposition` | Execute story stage | None | None | Coordinates user story creation using Decomposition Agent |
| `_execute_task_generation` | Execute task stage | None | None | Coordinates task generation using Developer Agent |
| `_execute_qa_generation` | Execute QA stage | None | None | **UPDATED**: Coordinates test case generation at USER STORY level using QA Tester Agent |
| `_human_review_checkpoint` | Provide human review | stage: str | None | Enables human-in-the-loop review and approval at workflow stages |
| `_show_detailed_view` | Display stage details | stage: str | None | Shows detailed view of stage results for review |
| `_integrate_with_azure_devops` | ADO integration | None | None | Integrates workflow results with Azure DevOps work items |
| `_send_completion_notifications` | Send completion alerts | None | None | Sends workflow completion notifications via configured channels |
| `_send_error_notifications` | Send error alerts | error: Exception | None | Sends error notifications when workflow encounters failures |
| `_calculate_workflow_stats` | Calculate execution stats | None | dict | Calculates comprehensive workflow execution statistics |
| `_finalize_workflow_data` | Finalize workflow data | None | None | Finalizes and structures complete workflow data for output |
| `_save_intermediate_output` | Save stage outputs | stage: str | None | Saves intermediate stage outputs for resume capability |
| `_save_final_output` | Save final results | None | None | Saves complete workflow results in JSON and YAML formats |
| `_save_output` | Save data to files | data: dict, filename: str | None | Utility method to save data in multiple formats |
| `_get_default_stages` | Get default workflow stages | None | list[str] | Returns default workflow execution stages |
| `get_execution_status` | Get current status | None | dict | Returns current workflow execution status and progress |

## 📁 supervisor/main.py - Command Line Interface
Provides command-line interface and execution modes:

| Function | Purpose | Inputs | Outputs | Description |
|----------|---------|--------|---------|-------------|
| `main` | Main entry point | None | None | Parses command-line arguments and routes to appropriate execution mode |
| `build_custom_context` | Build project context | args | dict | Constructs custom project context from command-line arguments |
| `execute_interactive_mode` | Run interactive mode | supervisor: WorkflowSupervisor, args, logger | None | Executes workflow in interactive mode with user prompts |
| `execute_file_mode` | Run file-based mode | supervisor: WorkflowSupervisor, args, logger | None | Executes workflow using product vision from file input |
| `execute_resume_mode` | Resume workflow | supervisor: WorkflowSupervisor, args, logger | None | Resumes interrupted workflow from saved state |
| `execute_workflow` | Execute workflow | supervisor: WorkflowSupervisor, vision: str, args, logger | dict | Central workflow execution with error handling and logging |
| `print_execution_summary` | Print results summary | result: dict | None | Displays comprehensive workflow execution summary |

## 🔄 Key Integration Points

### Agent Responsibilities Matrix:
- **Epic Strategist**: Strategic planning, epic creation from product vision, business value analysis
- **Decomposition Agent**: Hierarchical breakdown, epic→feature→user story decomposition, **Features have NO acceptance criteria**
- **Developer Agent**: Technical implementation planning, task generation, story point estimation
- **QA Tester Agent**: **USER STORY-LEVEL** test case generation, acceptance criteria validation, Azure DevOps test management, boundary/failure testing
- **Backlog Sweeper**: Quality monitoring, compliance checking, discrepancy reporting (read-only), supervisor integration
- **Workflow Supervisor**: Pipeline orchestration, agent coordination, human-in-the-loop, Azure DevOps integration

### 🚨 **CRITICAL RECENT CHANGES - Acceptance Criteria Refactoring**

#### **What Changed:**
1. **Features NO LONGER have acceptance criteria** - Features focus on business value only
2. **User Stories have ALL acceptance criteria** - Mapped to dedicated ADO field
3. **QA generation works at User Story level** - Not feature level
4. **Azure DevOps integration updated** - Proper field mapping for acceptance criteria

#### **Why This Matters:**
- **Compliance**: Follows Azure DevOps best practices and hierarchy standards
- **Clarity**: Features focus on business value, User Stories focus on detailed requirements
- **Testability**: Acceptance criteria are properly linked to testable User Stories
- **Organization**: Test plans organize by Feature, test suites organize by User Story
- **Searchability**: Acceptance criteria are in dedicated ADO fields

### Enhanced QA Agent Features:
- **User Story Focus**: Exclusively generates test cases at user story level (feature-level methods **REMOVED**)
- **Boundary/Failure Testing**: Comprehensive edge case and error scenario generation
- **Azure DevOps Integration**: Full test plan/suite/case management with proper organization
- **Testability Analysis**: Advanced acceptance criteria enhancement and testability scoring
- **Automation Assessment**: Test automation scoring and recommendations
- **Risk Assessment**: Test risk analysis and execution complexity estimation

### Shared Dependencies:
- All agents inherit from `base_agent.py` for consistent Grok API interaction
- Most agents use `WorkItemQualityValidator` for standardized quality checks
- QA Tester Agent integrates with Azure DevOps Test Management API and Test Client
- Backlog Sweeper Agent coordinates with supervisor for intelligent agent routing
- Supervisor orchestrates complete pipeline with human review capabilities

### Quality Standards:
- **INVEST Principles**: User stories follow Independent, Negotiable, Valuable, Estimable, Small, Testable
- **SMART Criteria**: Acceptance criteria are Specific, Measurable, Achievable, Relevant, Time-bound
- **BDD Format Support**: Given/When/Then test case structuring
- **Fibonacci Estimation**: Automated story point estimation (1-13 scale)
- **Comprehensive Test Coverage**: Functional, boundary, negative, security, performance, and integration testing
- **Azure DevOps Compliance**: Full integration with ADO work items, test plans, and test management

### 🏗️ **Proper ADO Hierarchy:**

```
Epic (Business Strategy)
├── Feature (Business Value + UI/UX + Technical Considerations)
│   ├── User Story (Acceptance Criteria + Detailed Requirements)
│   │   ├── Task (Technical Implementation)
│   │   └── Test Cases (Validation)
│   └── User Story (Acceptance Criteria + Detailed Requirements)
│       ├── Task (Technical Implementation)
│       └── Test Cases (Validation)
└── Feature (Business Value + UI/UX + Technical Considerations)
    └── User Story (Acceptance Criteria + Detailed Requirements)
        ├── Task (Technical Implementation)
        └── Test Cases (Validation)
```

This unified structure ensures each agent has clear responsibilities while maintaining consistent quality standards and seamless integration patterns across the entire agile backlog automation system, with **proper acceptance criteria placement at the User Story level only**.
