# 🧠 Agile Backlog Automation

## 🚨 Recent Updates (2025-07)

- **New Mobile-First Frontend:**
  - Added React-based frontend with Chakra UI for a modern, responsive user interface
  - Implemented project creation wizard for intuitive backlog setup
  - Created dashboard for monitoring backlog generation progress

- **Test Case Hierarchy Analysis & Automation:**
  - Added scripts to analyze and reorganize test cases, ensuring they are parented by User Stories (not Features) for best practice in Azure DevOps.
  - Created a script to identify test cases directly under Features and (optionally) auto-create User Stories to parent them.
  - Enhanced logging and dry-run support for all reorganization scripts.
  
- **Environment Variable Handling:**
  - Standardized on `AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, and `AZURE_DEVOPS_PAT` for all scripts.
  - All scripts now robustly load the `.env` file from the project root, regardless of working directory.
  - Fixed Azure DevOps authentication to always use base64-encoded PATs.
- **QA Tester Agent & Test Plan Automation:**
  - Improved prompt and logic for the QA Tester Agent to support test case prioritization and grouping.
  - Prepared for automated creation of Test Plans and Suites based on a clean Feature → User Story → Test Case hierarchy.
- **Debugging & Validation:**
  - Added scripts and debug tools to verify work item relationships and Azure DevOps API responses.
  - Improved error handling and step-by-step logging for all automation scripts.

# 🧠 Agile Backlog Automatio## 🏗️ Architecture

### AI Agents
1. **Epic Strategist** - Transforms product vision into high-level epics
2. **Feature Decomposer** - Breaks epics into detailed features  
3. **Developer Agent** - Creates technical tasks with time estimates
4. **QA Tester Agent** - Generates test cases, edge cases, and validates acceptance criteria

### Workflow
```
Product Vision → Epics → Features → Developer Tasks → QA Test Cases & Validation
```

### Work Item Management Tools
- **Work Item Description Fixer** (`fix_work_item_descriptions.py`) - Fixes HTML formatting and section headers in work item descriptions
- **Test Case Mover** (`move_test_cases.py`) - Organizes test cases into proper area paths
- **Section Header Checker** (`check_section_headers.py`) - Validates and audits work item formatting
- **ADO Cleanup Tools** (`tools/cleanup_ado_workitems.py`) - Bulk cleanup and management utilities
- **Path Updater** (`tools/update_work_item_paths.py`) - Updates area and iteration paths for work items

## 🛠️ Utility Tools

The project includes several standalone utility tools for Azure DevOps work item management:

### Work Item Management
```bash
# Fix work item descriptions with proper HTML formatting
python fix_work_item_descriptions.py [--live] [--confirm]

# Move all test cases to a specific area path
python move_test_cases.py [--live] [--confirm]

# Check what section headers exist in work items
python check_section_headers.py

# Update area and iteration paths for work items
python tools/update_work_item_paths.py

# Clean up all work items in a project
python tools/cleanup_ado_workitems.py [--confirm]
```

### Testing and Validation
```bash
# Test individual components
python tools/test_config_loader.py
python tools/test_epic_strategist.py
python tools/test_feature_decomposer.py
python tools/test_developer_agent.py
python tools/test_qa_tester_agent.py

# Test complete chains
python tools/test_epic_to_feature_chain.py
python tools/test_epic_feature_task_chain.py
python tools/test_epic_feature_task_qa_chain.py

# Test Azure DevOps integration
python tools/test_azure_devops.py
python tools/test_notifications.py
```

### Development and Debugging
```bash
# Debug specific components
python tools/debug_agent_lockup.py
python tools/debug_epic_output.py
python tools/debug_feature_decomposer.py
python tools/debug_work_item_creation.py

# Demo and testing
python tools/demo_prompt_system.py
python tools/test_grit_system.py
python tools/test_end_to_end.py
```sticated multi-agent AI system that transforms product visions into structured, actionable backlogs. Built with Grok from xAI, this system generates epics, features, developer tasks, and QA test cases with full Azure DevOps integration and advanced work item management capabilities.

## ✨ Features

### Core AI Automation
- **🤖 Multi-Agent Architecture**: Four specialized AI agents working in sequence
- **🔄 Modular Execution**: Run individual stages or the complete pipeline
- **📝 Flexible Input**: Support for interactive input or YAML configuration files
- **💾 Multiple Output Formats**: JSON and YAML with timestamped outputs
- **🎯 Human-in-the-Loop**: Review and approve at each stage
- **⚙️ Configurable Workflows**: Customizable agent prompts and settings

### Azure DevOps Integration
- **🔗 Work Item Creation**: Automatic creation of Epics, Features, User Stories, Tasks, and Test Cases
- **📋 Work Item Management**: Advanced tools for updating, moving, and organizing work items
- **🏗️ Area Path Management**: Automated organization of work items into proper area paths
- **🔧 Description Formatting**: Tools to fix and standardize work item descriptions with proper HTML
- **📊 Project Analytics**: Tools to analyze and validate work item structures

### Advanced Utilities
- **📧 Smart Notifications**: Teams and email alerts with summary reports
- **🧹 Cleanup Tools**: Bulk cleanup and management of Azure DevOps work items
- **🔍 Validation Tools**: Structure validation and quality assessment
- **📈 Estimation Tools**: Story point and time estimation capabilities
- **🧪 Testing Framework**: Comprehensive test suites for all components

## 🛠️ Architecture

### AI Agents
1. **Epic Strategist** - Transforms product vision into high-level epics
2. **Feature Decomposer** - Breaks epics into detailed features  
3. **Developer Agent** - Creates technical tasks with time estimates
4. **QA Tester Agent** - Generates test cases, edge cases, and validates acceptance criteria

### Workflow
```
Product Vision → Epics → Features → Developer Tasks → QA Test Cases & Validation
```

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/your-username/agile-backlog-automation.git
cd agile-backlog-automation

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux  
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
# Required - Grok API Configuration
GROK_API_KEY=your_grok_api_key_here
GROK_MODEL=grok-3-latest

# Optional - Azure DevOps Integration
AZURE_DEVOPS_PAT=your_personal_access_token
AZURE_DEVOPS_ORG=https://dev.azure.com/your-org
AZURE_DEVOPS_PROJECT=YourProjectName

# Optional - Notifications
TEAMS_WEBHOOK_URL=your_teams_webhook_url
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
EMAIL_USERNAME=your-email@domain.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@domain.com
EMAIL_TO=recipient@domain.com
```

### 3. Verify Configuration

```bash
python tools/test_config_loader.py
```

## 🧩 CLI Usage

### Main Pipeline
The main entry point is `tools/run_pipeline.py` with flexible execution options:

```bash
python tools/run_pipeline.py [--run STAGE] [--input PATH] [--project-type TYPE] [--project-name NAME]
```

#### Command Options

| Flag | Description | Default |
|------|-------------|---------|
| `--run` | Execution stage: `all`, `epic`, `feature`, `developer`, `qa` | `all` |
| `--input` | Path to YAML input file with product vision and/or existing data | Interactive prompt |
| `--project-type` | Project context: `fintech`, `healthcare`, `ecommerce`, `education`, `mobile`, `saas` | None |
| `--project-name` | Custom project name for context | None |

### Standalone Utilities

#### Work Item Management
```bash
# Fix formatting issues in work item descriptions
python fix_work_item_descriptions.py              # Dry run mode
python fix_work_item_descriptions.py --live       # Execute changes
python fix_work_item_descriptions.py --live --confirm  # Skip confirmation

# Move test cases to proper area path
python move_test_cases.py                         # Dry run mode
python move_test_cases.py --live --confirm        # Execute move

# Analyze section headers in work items
python check_section_headers.py

# Clean up project work items
python tools/cleanup_ado_workitems.py --confirm
```

#### Development and Testing
```bash
# Run comprehensive test suite
python tools/test_complete_chain.py

# Test specific components
python tools/test_[component_name].py

# Debug specific issues
python tools/debug_[component_name].py
```

### Usage Examples

#### AI Pipeline Examples
```bash
# Full pipeline with interactive input
python tools/run_pipeline.py

# Epic generation only with interactive input  
python tools/run_pipeline.py --run epic

# QA testing only with interactive input
python tools/run_pipeline.py --run qa

# Complete pipeline from vision file
python tools/run_pipeline.py --run all --input samples/grit_vision.yaml

# Generate epics only from vision
python tools/run_pipeline.py --run epic --input samples/taskmaster_vision.yaml

# Generate features from existing epics
python tools/run_pipeline.py --run feature --input output/epics_20250701_153000.yaml

# Generate developer tasks from existing features
python tools/run_pipeline.py --run developer --input output/backlog_20250701_153000.yaml

# Generate QA test cases from existing features
python tools/run_pipeline.py --run qa --input output/backlog_20250701_153000.yaml
```

#### Work Item Management Examples
```bash
# Fix all work item descriptions (preview changes)
python fix_work_item_descriptions.py

# Actually fix work item descriptions
python fix_work_item_descriptions.py --live --confirm

# Move all test cases to "Backlog Automation\Grit" area path
python move_test_cases.py --live --confirm

# Check what section headers exist in your work items
python check_section_headers.py

# Update area paths for all work items
python tools/update_work_item_paths.py

# Clean up all work items in the project
python tools/cleanup_ado_workitems.py --confirm
```

#### Project Context Examples
```bash
# Run with project type context
python tools/run_pipeline.py --project-type fintech --project-name "CryptoWallet Pro"

# Custom context variables  
python tools/run_pipeline.py \
  --project-name "MyApp" \
  --project-type ecommerce \
  --input samples/ecotracker_vision.yaml

# Healthcare project with compliance focus
python tools/run_pipeline.py --project-type healthcare --project-name "PatientPortal"
```

## 📁 Input File Formats

### Sample Vision Files
The project includes several sample vision files in the `samples/` directory:

- `grit_vision.yaml` - Logistics management system
- `taskmaster_vision.yaml` - Task management application
- `ecotracker_vision.yaml` - Environmental tracking app
- `oil_gas_visions.yaml` - Oil & gas industry applications
- `shipping_logistics_visions.yaml` - Shipping and logistics solutions
- `features_with_qa.yaml` - Feature examples with QA validation

### 1. Vision Only (`samples/taskmaster_vision.yaml`)
```yaml
product_vision: >
  Build a mobile-first task management app for remote teams
  that enables seamless collaboration, real-time updates, and
  productivity tracking across distributed workforces.
```

### 2. Complete Vision with Context (`samples/grit_vision.yaml`)
```yaml
product_vision: >
  Empower enterprise logistics managers to achieve operational excellence
  through intelligent shipment monitoring that reduces costs by 15-25%,
  prevents delays through predictive analytics, and provides actionable
  mid-tier intelligence.

project_context:
  industry: "logistics"
  target_users: ["Logistics Managers", "Supply Chain Directors"]
  tech_stack: "Python, React, Azure"
  compliance_requirements: ["SOC2", "ISO27001"]
```

### 3. Complete Backlog Structure
```yaml
product_vision: "Your product vision here"
epics:
  - title: "Epic Title"
    description: "Epic description"
    priority: "High"
    features:
      - title: "Feature Title"
        description: "Feature description"
        acceptance_criteria:
          - "Criterion 1"
          - "Criterion 2"
        tasks:
          - title: "Task Title"
            description: "Task description" 
            estimated_hours: 8
            type: "Development"
            priority: "High"
        test_cases:
          - title: "Test Case Title"
            type: "functional"
            priority: "High"
            gherkin:
              scenario: "Test scenario description"
              given: ["Precondition 1"]
              when: ["Action 1"]
              then: ["Expected result 1"]
        edge_cases:
          - title: "Edge Case Title"
            category: "boundary_condition"
            risk_level: "Medium"
        qa_validation:
          testability_score: 8
          recommendations: ["Recommendation 1"]
```

## 🎯 Modular Prompt System

The system features a powerful **modular, template-based prompt system** with dynamic context injection for role-specific, domain-aware outputs.

### Context-Aware Generation
```bash
# Run with project type context
python tools/run_pipeline.py --project-type fintech --project-name "CryptoWallet Pro"

# Custom context variables  
python tools/run_pipeline.py \
  --project-name "MyApp" \
  --domain "e-commerce" \
  --tech-stack "React, Node.js, PostgreSQL" \
  --timeline "6 months"

# Healthcare project with compliance focus
python tools/run_pipeline.py --project-type healthcare --project-name "PatientPortal"
```

### Supported Project Types
- **Fintech**: Banking, payments, cryptocurrency (PCI DSS, SOX compliance)
- **Healthcare**: Medical apps, patient management (HIPAA, FDA compliance)  
- **E-commerce**: Online retail, marketplaces (PCI DSS, GDPR compliance)
- **Education**: Learning platforms, student management (FERPA, COPPA compliance)
- **Mobile App**: iOS/Android applications, cross-platform development
- **SaaS**: Software as a Service, multi-tenant applications

### Key Benefits
- **Domain-Specific**: Agents understand industry terminology and requirements
- **Compliance-Aware**: Automatically includes relevant regulatory considerations
- **Technology-Focused**: Tailors recommendations to your tech stack
- **User-Centric**: Adapts to your target user personas

### Example Context Impact
**Generic Output**: "Create user authentication system"
**Fintech Context**: "Implement multi-factor authentication with PCI DSS compliance, fraud detection, and regulatory audit trails for financial transactions"

📖 **[Complete Prompt System Guide](docs/PROMPT_SYSTEM_GUIDE.md)**

## 📤 Output Structure

The system generates timestamped outputs in both JSON and YAML formats:

```
output/
├── backlog_20250630_171414.json    # Complete structured backlog
├── backlog_20250630_171414.yaml    # Human-readable format
├── epics_and_features_20250630_165816.json  # Intermediate outputs
└── epics_and_features_20250630_165816.yaml
```

### Output Schema
```yaml
product_vision: "Your product vision"
epics:
  - title: "Epic Name"
    description: "Epic description"
    priority: "High|Medium|Low"
    business_value: "Value statement"
    features:
      - title: "Feature Name"
        description: "Feature description"
        acceptance_criteria:
          - "User can perform action X"
          - "System validates input Y"
        priority: "High|Medium|Low"
        estimated_story_points: 8
        tasks:
          - title: "Task Name"
            description: "Technical implementation details"
            type: "Development|Testing|Design|Documentation"
            estimated_hours: 4
            priority: "High|Medium|Low"
            dependencies: []
        test_cases:
          - title: "Test scenario name"
            type: "functional|security|performance|boundary"
            priority: "High|Medium|Low"
            gherkin:
              feature: "Feature name"
              scenario: "Specific test scenario"
              given: ["Precondition 1", "Precondition 2"]
              when: ["User action 1", "System action 2"]
              then: ["Expected outcome 1", "Validation 2"]
            estimated_time_minutes: 10
        edge_cases:
          - title: "Edge case name"
            category: "boundary_condition|security|performance|integration"
            description: "Detailed edge case description"
            risk_level: "High|Medium|Low|Critical"
            test_scenario: "How to reproduce the edge case"
            expected_behavior: "What should happen"
        qa_validation:
          testability_score: 8
          enhanced_criteria: ["Enhanced criterion 1"]
          recommendations: ["Improvement recommendation 1"]
          missing_scenarios: ["Missing test scenario 1"]
```

## ⚙️ Configuration

### Agent Configuration (`config/settings.yaml`)
```yaml
project:
  name: "Your Project Name"
  default_area_path: "Project\\Area"
  default_iteration_path: "Project\\Sprint 2025-07"

agents:
  epic_strategist:
    prompt_file: "prompts/epic_strategist.txt"
  feature_decomposer:
    prompt_file: "prompts/feature_decomposer.txt"
  developer_agent:
    prompt_file: "prompts/developer_agent.txt"
    estimation_unit: "hours"
  qa_tester_agent:
    prompt_file: "prompts/qa_tester_agent.txt"
    test_case_format: "gherkin"

workflow:
  sequence:
    - epic_strategist
    - feature_decomposer  
    - developer_agent
    - qa_tester_agent
  output_format: "azure_devops"

notifications:
  enabled: true
  channels: [teams, email]
  summary_report:
    format: markdown
    send_to:
      - "project-manager@company.com"
      - "tech-lead@company.com"
```

### Custom Agent Prompts
Customize agent behavior by editing prompt files in the `prompts/` directory:

- `epic_strategist.txt` - Controls epic generation strategy
- `feature_decomposer.txt` - Defines feature breakdown approach  
- `developer_agent.txt` - Shapes technical task creation
- `qa_tester_agent.txt` - Guides test case generation

## 🔗 Integrations

### Azure DevOps
Automatically creates work items in Azure DevOps:
- **Epics** → Azure DevOps Epics
- **Features** → Azure DevOps Features  
- **Tasks** → Azure DevOps User Stories/Tasks
- **Test Cases** → Azure DevOps Test Cases

### Notifications
- **Microsoft Teams** - Real-time pipeline status updates
- **Email** - Detailed summary reports with markdown formatting

## 🔧 Work Item Management Features

The system includes powerful utilities for managing Azure DevOps work items:

### Description Formatting (`fix_work_item_descriptions.py`)
- **HTML Formatting**: Converts plain text descriptions to proper HTML
- **Section Header Formatting**: Ensures consistent formatting of section headers like **Acceptance Criteria:**, **Business Value:**, etc.
- **Bullet Point Organization**: Properly formats bullet lists with appropriate line breaks
- **Bulk Processing**: Can process hundreds of work items in a single operation
- **Safe Operations**: Dry-run mode to preview changes before applying

### Test Case Organization (`move_test_cases.py`)
- **Area Path Management**: Moves test cases to proper organizational structure
- **Bulk Operations**: Handles large numbers of test cases efficiently
- **Safety Features**: Confirmation prompts and dry-run capabilities
- **Progress Tracking**: Real-time progress updates during operations

### Work Item Analysis (`check_section_headers.py`)
- **Section Header Discovery**: Identifies all section headers used in work items
- **Formatting Audit**: Analyzes formatting consistency across work items
- **Quality Assessment**: Provides insights into work item structure quality

### Project Maintenance Tools
- **Path Updates** (`tools/update_work_item_paths.py`): Update area and iteration paths
- **Bulk Cleanup** (`tools/cleanup_ado_workitems.py`): Remove all work items from a project
- **Debug Tools**: Various debugging utilities for troubleshooting

### Key Benefits
- **Consistency**: Ensures all work items follow the same formatting standards
- **Efficiency**: Bulk operations save hours of manual work
- **Quality**: Improves readability and professionalism of work items
- **Maintenance**: Simplifies ongoing project maintenance tasks

## 🔬 QA Testing Capabilities

The QA Tester Agent provides comprehensive testing analysis for each feature:

### Test Case Generation
- **Functional Testing** - Happy path and alternative flow scenarios in Gherkin format
- **Security Testing** - SQL injection, XSS, and authentication bypass scenarios
- **Performance Testing** - Load testing and response time validation scenarios
- **Boundary Testing** - Edge cases with minimum/maximum values and input validation
- **Integration Testing** - API endpoint and service connectivity testing
- **Usability Testing** - Accessibility and user experience validation

### Edge Case Identification
- **Boundary Conditions** - Maximum/minimum limits and invalid inputs
- **Error Handling** - System failure scenarios and recovery testing
- **Security Vulnerabilities** - Malicious input and unauthorized access attempts
- **Performance Edge Cases** - High load and resource constraint scenarios
- **Integration Failures** - Service outages and connectivity issues

### Acceptance Criteria Validation
- **Testability Scoring** - 1-10 scale assessment of how testable criteria are
- **Enhancement Recommendations** - Specific suggestions for improving testability
- **Missing Scenarios** - Identification of untested edge cases and workflows
- **Risk Assessment** - Critical, High, Medium, Low risk categorization

### Example QA Output
```yaml
features:
  - title: "User Authentication"
    test_cases:
      - title: "Successful login with valid credentials"
        type: "functional"
        priority: "High"
        gherkin:
          scenario: "User logs in successfully"
          given: ["User has valid account", "User is on login page"]
          when: ["User enters correct email and password", "User clicks login"]
          then: ["User is redirected to dashboard", "Welcome message appears"]
    edge_cases:
      - title: "SQL injection attempt in login field"
        category: "security"
        risk_level: "Critical"
        description: "Test for SQL injection vulnerability in email field"
    qa_validation:
      testability_score: 9
      recommendations: ["Add specific error message validation"]
```

## 🧪 Testing & Validation

### Test Individual Components
```bash
# Test configuration loading
python tools/test_config_loader.py

# Test individual agents
python tools/test_epic_strategist.py
python tools/test_feature_decomposer.py  
python tools/test_developer_agent.py
python tools/test_qa_tester_agent.py

# Test specialized capabilities
python tools/test_qa_individual_capabilities.py
python tools/test_qa_quality_assessment.py
python tools/test_user_story_decomposition.py
```

### Test Agent Chains
```bash
# Test agent chains
python tools/test_epic_to_feature_chain.py
python tools/test_epic_feature_task_chain.py
python tools/test_epic_feature_task_qa_chain.py
python tools/test_complete_chain.py

# Test end-to-end workflows
python tools/test_end_to_end.py
python tools/test_grit_system.py
```

### Test Integrations
```bash
# Test Azure DevOps integration
python tools/test_azure_devops.py

# Test notifications
python tools/test_notifications.py

# Test prompt system
python tools/test_prompt_system.py
python tools/demo_prompt_system.py
```

### Validation and Debugging Tools
```bash
# Validate output structure
python tools/validation_tool.py --input output/backlog_20250701_153000.yaml

# Debug specific issues
python tools/debug_agent_lockup.py
python tools/debug_epic_output.py
python tools/debug_feature_decomposer.py
python tools/debug_work_item_creation.py

# Test business value formats
python tools/test_business_value_formats.py

# Test structure validation
python tools/test_structure_validation.py
```

## 📊 Example Workflows

### Scenario 1: New Product Development (Complete Pipeline)
```bash
# Start with product vision - complete AI-driven backlog generation
python tools/run_pipeline.py --run all --input samples/grit_vision.yaml --project-type saas

# Output: Complete backlog with epics, features, tasks, and test cases
```

### Scenario 2: Work Item Management & Organization
```bash
# Fix formatting issues in existing work items
python fix_work_item_descriptions.py --live --confirm

# Organize test cases into proper area paths
python move_test_cases.py --live --confirm

# Update area and iteration paths for all work items
python tools/update_work_item_paths.py

# Audit and validate work item structure
python check_section_headers.py
```

### Scenario 3: Epic Refinement & Feature Planning
```bash  
# Generate features for existing epics
python tools/run_pipeline.py --run feature --input output/epics_20250701_153000.yaml

# Generate comprehensive test cases for features
python tools/run_pipeline.py --run qa --input output/backlog_20250701_153000.yaml
```

### Scenario 4: Sprint Planning & Task Generation
```bash
# Generate developer tasks for upcoming sprint
python tools/run_pipeline.py --run developer --input output/features_ready_for_dev.yaml

# Validate and estimate task complexity
python tools/validation_tool.py --input output/backlog_with_tasks.yaml
```

### Scenario 5: Quality Assurance Focus
```bash
# Generate comprehensive test cases for existing features
python tools/run_pipeline.py --run qa --input output/features_ready_for_testing.yaml

# Test QA capabilities individually
python tools/test_qa_individual_capabilities.py
python tools/test_qa_quality_assessment.py
```

### Scenario 6: Project Cleanup & Maintenance
```bash
# Clean up test environment
python tools/cleanup_ado_workitems.py --confirm

# Debug issues with work item creation
python tools/debug_work_item_creation.py

# Validate project structure
python tools/test_structure_validation.py
```

### Scenario 7: Iterative Development Process
```bash
# 1. Generate epics from vision
python tools/run_pipeline.py --run epic --input samples/taskmaster_vision.yaml

# 2. Review and refine epics, then generate features  
python tools/run_pipeline.py --run feature --input output/epics_20250701_153000.yaml

# 3. Generate tasks and organize work items
python tools/run_pipeline.py --run developer --input output/backlog_20250701_153000.yaml
python tools/update_work_item_paths.py

# 4. Generate test cases and validate
python tools/run_pipeline.py --run qa --input output/backlog_20250701_153000.yaml
python tools/validation_tool.py --input output/final_backlog.yaml
```

## 🛠️ Development

### Project Structure
```
agile-backlog-automation/
├── agents/                    # AI agent implementations
│   ├── base_agent.py         # Base class for all agents
│   ├── epic_strategist.py    # Epic generation agent
│   ├── feature_decomposer.py # Feature breakdown agent
│   ├── developer_agent.py    # Task creation agent
│   └── qa_tester_agent.py    # Test case generation agent
├── config/                   # Configuration management
│   ├── config_loader.py      # Configuration loading utilities
│   └── settings.yaml         # Agent and workflow settings
├── docs/                     # Documentation
│   ├── PROMPT_SYSTEM_GUIDE.md
│   ├── QA_TESTER_AGENT_QUALITY_REPORT.md
│   └── SUPERVISOR_IMPLEMENTATION.md
├── integrators/              # External service integrations
│   └── azure_devops_api.py   # Azure DevOps API integration
├── logs/                     # Application logs
├── output/                   # Generated backlog outputs
├── prompts/                  # Agent prompt templates
├── samples/                  # Sample input files
│   ├── grit_vision.yaml
│   ├── taskmaster_vision.yaml
│   └── ecotracker_vision.yaml
├── supervisor/               # Pipeline orchestration
├── tools/                    # CLI tools and utilities
│   ├── run_pipeline.py       # Main pipeline runner
│   ├── cleanup_ado_workitems.py # ADO cleanup utility
│   ├── update_work_item_paths.py # Path management
│   └── test_*.py             # Test suites
├── utils/                    # Shared utilities
│   ├── prompt_manager.py     # Prompt template management
│   ├── project_context.py    # Project context handling
│   ├── notifier.py           # Notification system
│   └── logger.py             # Logging utilities
├── fix_work_item_descriptions.py # Work item formatter
├── move_test_cases.py        # Test case organizer
├── check_section_headers.py  # Work item auditor
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Adding Custom Agents
1. Create agent class in `agents/` inheriting from `BaseAgent`
2. Add prompt file in `prompts/`
3. Update `config/settings.yaml` workflow sequence
4. Register agent in pipeline supervisor

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `GROK_API_KEY` | Yes | xAI Grok API authentication |
| `GROK_MODEL` | No | Model version (default: grok-3-latest) |
| `AZURE_DEVOPS_PAT` | No | Azure DevOps Personal Access Token |
| `AZURE_DEVOPS_ORG` | No | Azure DevOps Organization URL |
| `AZURE_DEVOPS_PROJECT` | No | Azure DevOps Project Name |
| `TEAMS_WEBHOOK_URL` | No | Microsoft Teams webhook for notifications |
| `EMAIL_*` | No | SMTP configuration for email notifications |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🤝 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review test files in `/tools` for usage examples

---

**Built with ❤️ using Grok AI and Python**