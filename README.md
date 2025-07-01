# 🧠 Agile Backlog Automation

A sophisticated multi-agent AI system that transforms product visions into structured, actionable backlogs. Built with Grok from xAI, this system generates epics, features, developer tasks, and QA test cases with full Azure DevOps integration.

## ✨ Features

- **🤖 Multi-Agent Architecture**: Four specialized AI agents working in sequence
- **🔄 Modular Execution**: Run individual stages or the complete pipeline
- **📝 Flexible Input**: Support for interactive input or YAML configuration files
- **💾 Multiple Output Formats**: JSON and YAML with timestamped outputs
- **🔗 Azure DevOps Integration**: Direct work item creation and management
- **📧 Smart Notifications**: Teams and email alerts with summary reports
- **🎯 Human-in-the-Loop**: Review and approve at each stage
- **⚙️ Configurable Workflows**: Customizable agent prompts and settings

## �️ Architecture

### AI Agents
1. **Epic Strategist** - Transforms product vision into high-level epics
2. **Feature Decomposer** - Breaks epics into detailed features  
3. **Developer Agent** - Creates technical tasks with time estimates
4. **QA Tester Agent** - Generates test cases in Gherkin format

### Workflow
```
Product Vision → Epics → Features → Developer Tasks → QA Test Cases
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

The main entry point is `tools/run_pipeline.py` with flexible execution options:

```bash
python tools/run_pipeline.py [--run STAGE] [--input PATH]
```

### Command Options

| Flag | Description | Default |
|------|-------------|---------|
| `--run` | Execution stage: `all`, `epic`, `feature`, `developer` | `all` |
| `--input` | Path to YAML input file with product vision and/or existing data | Interactive prompt |

### Usage Examples

#### Interactive Mode
```bash
# Full pipeline with interactive input
python tools/run_pipeline.py

# Epic generation only with interactive input  
python tools/run_pipeline.py --run epic
```

#### File-Based Mode
```bash
# Complete pipeline from vision file
python tools/run_pipeline.py --run all --input samples/full_vision.yaml

# Generate epics only from vision
python tools/run_pipeline.py --run epic --input samples/vision_only.yaml

# Generate features from existing epics
python tools/run_pipeline.py --run feature --input samples/epics_with_vision.yaml

# Generate developer tasks from existing features
python tools/run_pipeline.py --run developer --input output/backlog_20250630_171414.yaml

# Resume from specific stage
python tools/run_pipeline.py --run feature --input output/epics_and_features_20250630_165816.yaml
```

## 📁 Input File Formats

### 1. Vision Only (`samples/vision_only.yaml`)
```yaml
product_vision: >
  Build a mobile-first budgeting app for college students
  that tracks spending, sets saving goals, and provides 
  financial insights to help them manage money effectively.
```

### 2. Vision with Epics (`samples/epics_with_vision.yaml`)
```yaml
product_vision: >
  Build a mobile-first budgeting app for college students
  that tracks spending, sets saving goals, and provides insights.

epics:
  - title: "Expense Tracking System"
    description: "Enable users to record, categorize, and monitor daily expenses"
    priority: "High"
    business_value: "Essential for core app functionality"
    
  - title: "Savings Goal Management"
    description: "Allow users to set, track, and achieve savings targets"
    priority: "Medium"
    business_value: "Drives user engagement and retention"
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
```

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

## 🧪 Testing & Validation

### Test Individual Components
```bash
# Test configuration loading
python tools/test_config_loader.py

# Test individual agents
python tools/test_epic_strategist.py
python tools/test_feature_decomposer.py  
python tools/test_developer_agent.py

# Test agent chains
python tools/test_epic_to_feature_chain.py
python tools/test_epic_feature_task_chain.py

# Test notifications
python tools/test_notifications.py
```

### Validation Tools
```bash
# Validate output structure
python tools/validation_tool.py --input output/backlog_20250630_171414.yaml

# Estimate complexity
python tools/estimation_tool.py --input output/backlog_20250630_171414.yaml
```

## 📊 Example Workflows

### Scenario 1: New Product Development
```bash
# Start with product vision
python tools/run_pipeline.py --run all --input samples/new_product_vision.yaml
```

### Scenario 2: Epic Refinement
```bash  
# Generate features for existing epics
python tools/run_pipeline.py --run feature --input samples/existing_epics.yaml
```

### Scenario 3: Sprint Planning
```bash
# Generate developer tasks for upcoming sprint
python tools/run_pipeline.py --run developer --input output/features_ready_for_dev.yaml
```

### Scenario 4: Iterative Development
```bash
# 1. Generate epics
python tools/run_pipeline.py --run epic --input samples/vision.yaml

# 2. Review and refine epics, then generate features  
python tools/run_pipeline.py --run feature --input output/epics_20250630_171414.yaml

# 3. Review features, then generate tasks
python tools/run_pipeline.py --run developer --input output/backlog_20250630_171414.yaml
```

## 🛠️ Development

### Project Structure
```
agile-backlog-automation/
├── agents/               # AI agent implementations
├── config/              # Configuration management
├── integrators/         # External service integrations  
├── output/              # Generated backlog outputs
├── prompts/             # Agent prompt templates
├── supervisor/          # Pipeline orchestration
├── tools/               # CLI tools and tests
├── utils/               # Shared utilities
├── requirements.txt     # Python dependencies
└── README.md           # This file
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

## � Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review test files in `/tools` for usage examples

---

**Built with ❤️ using Grok AI and Python**