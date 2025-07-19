# 🧠 Agile Backlog Automation

A sophisticated multi-agent AI system that transforms product visions into structured, actionable backlogs. Built with modern AI models, this system generates epics, features, user stories, developer tasks, and QA test cases with full Azure DevOps integration and advanced work item management capabilities.

## 🚨 Current Project Status (2025-07-19)

### **Critical Issues Identified**
- **Issue #49**: QA Agent Critical Failure - System crashes and loses progress during test generation
- **Issue #30**: Progress Bar Not Showing - Users can't monitor active jobs
- **Issue #43**: Missing API Authentication - Security vulnerability
- **Issue #50**: Parallel Processing Broken - Jobs taking 1.5+ hours instead of 30 minutes

### **Performance Issues**
- **API Rate Limiting**: Single LLM provider hitting 10 calls/second limit
- **Sequential Processing**: QA agent not using parallel processing despite configuration
- **Cost Impact**: Current jobs cost $50-100 each due to timeouts and failures
- **Target**: Reduce job time to <30 minutes and cost to $10-20 per job

### **Recent Improvements**
- **✅ Database-Based Settings Management**: Complete user settings system with session/user_default/global_default scopes
- **✅ User ID Resolution**: Email-based user identification using `.env` configuration
- **✅ Settings API**: Full REST API for managing work item limits and visual settings
- **✅ Frontend Integration**: Tron Settings screen with real-time preview and save options
- **SSE Implementation**: Server-Sent Events for real-time progress updates (needs testing)
- **Multi-Provider Support**: Framework for rotating LLM providers (not implemented)
- **Progress Persistence**: Framework for saving progress across failures (not implemented)
- **Comprehensive Logging**: Enhanced logging and monitoring capabilities

## 🏗️ Architecture Overview

### **Core Components**
```
Frontend (React) ←→ API Server (FastAPI) ←→ AI Agents ←→ Azure DevOps
     ↑                    ↑                    ↑              ↑
  Real-time UI      SSE Progress      Multi-Agent      Work Items
  Monitoring        Streaming         Pipeline         Creation
     ↑                    ↑                    ↑              ↑
  Settings UI       Settings API      Settings        Database
  Management        (Database)        Manager         Storage
```

### **AI Agent Pipeline**
1. **Epic Strategist** - Transforms product vision into high-level epics
2. **Feature Decomposer** - Breaks epics into features with business value focus
3. **User Story Decomposer** - Creates user stories with acceptance criteria
4. **Developer Agent** - Generates technical tasks with time estimates
5. **QA Lead Agent** - Orchestrates test generation with sub-agents:
   - **Test Plan Agent** - Creates test plans for features
   - **Test Suite Agent** - Creates test suites for user stories  
   - **Test Case Agent** - Creates individual test cases

### **Work Item Hierarchy (Azure DevOps)**
```
Epic
├── Feature (Business Value Focus)
│   ├── User Story (with Acceptance Criteria)
│   │   ├── Task (Development Work)
│   │   └── Test Case (QA Validation)
│   └── User Story (with Acceptance Criteria)
│       ├── Task (Development Work)
│       └── Test Case (QA Validation)
└── Feature (Business Value Focus)
    └── ...
```

### **Key Architecture Principles**
- **Features** focus on business value without acceptance criteria
- **User Stories** contain detailed acceptance criteria and are QA testing units
- **Test Cases** are always parented by User Stories for proper traceability
- **Tasks** represent technical implementation work for User Stories

## 📁 Project Structure

```
agile-backlog-automation/
├── agents/                    # AI Agent implementations
│   ├── base_agent.py         # Base agent class
│   ├── epic_strategist.py    # Epic generation agent
│   ├── feature_decomposer_agent.py
│   ├── user_story_decomposer_agent.py
│   ├── developer_agent.py    # Task generation agent
│   ├── qa_lead_agent.py      # QA orchestration agent (supervisor)
│   └── qa/                   # QA sub-agents
│       ├── test_plan_agent.py    # Test plan creation agent
│       ├── test_suite_agent.py   # Test suite creation agent
│       └── test_case_agent.py    # Test case creation agent
├── supervisor/               # Workflow orchestration
│   ├── supervisor.py        # Main workflow supervisor
│   └── main.py              # Supervisor entry point
├── frontend/                # React-based UI
│   ├── src/
│   │   ├── screens/         # Application screens
│   │   │   └── settings/    # Settings management screens
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API services
│   │   │   ├── api/         # API clients
│   │   │   │   ├── settingsApi.ts  # Settings API client
│   │   │   │   └── userApi.ts      # User API client
│   │   │   └── ... (other services)
│   │   └── hooks/           # Custom React hooks
│   └── package.json
├── docs/                    # Documentation and analysis files
│   ├── GITHUB_ISSUES_PRIORITIZATION_SUMMARY.md
│   ├── PARALLEL_PROCESSING_ANALYSIS.md
│   ├── SSE_TROUBLESHOOTING_GUIDE.md
│   ├── COMPREHENSIVE_APPLICATION_ANALYSIS.md
│   └── ... (other documentation)
├── unified_api_server.py    # Main FastAPI server (consolidated)
├── db.py                    # Database operations (jobs + user settings)
├── config/                  # Configuration management
│   ├── config_loader.py
│   └── settings.yaml
├── utils/                   # Utility functions
│   ├── settings_manager.py  # Database-based settings management
│   ├── user_id_resolver.py  # User identification from .env
│   └── ... (other utilities)
├── tools/                   # Development and debugging tools
│   ├── api_server.py             # Original API server (reference/backup)
│   ├── create_github_issues.py   # GitHub issue creation utility
│   ├── create_github_issues.bat  # GitHub issue creation batch file
│   ├── kill_dev_processes.bat    # Kill development processes (batch)
│   ├── kill_dev_processes.ps1    # Kill development processes (PowerShell)
│   ├── test_*.py                 # Test scripts
│   ├── check_*.py                # Validation scripts
│   └── debug_*.py                # Debugging utilities
├── integrators/             # External integrations
├── clients/                 # API clients
├── data/                    # All data files
│   ├── database/           # Database files
│   ├── logs/               # Application logs
│   └── output/             # Generated outputs
├── samples/                 # Sample configuration files
├── quick_start.bat          # Quick startup script
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- Node.js 16+ (for frontend)
- Azure DevOps account with PAT
- AI model API key (OpenAI, Anthropic, etc.)

### **1. Installation**

```bash
# Clone repository
git clone https://github.com/oldmantran/agile-backlog-automation.git
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

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### **2. Configuration**

Create a `.env` file in the project root:

```env
# Required - AI Model Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required - Azure DevOps Configuration
AZURE_DEVOPS_ORG=your_organization
AZURE_DEVOPS_PROJECT=your_project
AZURE_DEVOPS_PAT=your_personal_access_token

# Required - User Identification (for settings management)
EMAIL_TO=your_email@company.com
EMAIL_FROM=your_email@company.com

# Optional - Notification Configuration
TEAMS_WEBHOOK_URL=your_teams_webhook_url
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### **3. Start the Application**

```bash
# Start backend server
python unified_api_server.py

# In another terminal, start frontend
cd frontend
npm start

# Or use the quick start script
quick_start.bat
```

### **4. Create Your First Backlog**

1. Open the application in your browser
2. Navigate to "Create New Project"
3. Enter your product vision or use a sample configuration
4. Configure Azure DevOps settings
5. Start the backlog generation process
6. Monitor progress in real-time

## ⚙️ Configuration

### **Parallel Processing Settings**
```yaml
# config/settings.yaml
parallel_processing:
  enabled: true
  max_workers: 4
  rate_limit_per_second: 10
  feature_decomposition: true
  user_story_decomposition: true
  task_generation: true
  qa_generation: true
  qa_sub_agent_parallel: true
```

### **Agent Configuration**
```yaml
agents:
  epic_strategist:
    model: gpt-4
    temperature: 0.7
    max_tokens: 4000
  feature_decomposer:
    model: gpt-4
    temperature: 0.6
    max_tokens: 3000
  developer_agent:
    model: gpt-4
    temperature: 0.5
    max_tokens: 2000
  qa_lead_agent:
    model: gpt-4
    temperature: 0.6
    max_tokens: 3000
    sub_agents:
      test_plan_agent:
        model: gpt-4
        temperature: 0.5
        max_tokens: 2000
      test_suite_agent:
        model: gpt-4
        temperature: 0.5
        max_tokens: 2000
      test_case_agent:
        model: gpt-4
        temperature: 0.4
        max_tokens: 1500
```

### **Spending Limits & Cost Control**
```yaml
spending_limits:
  enabled: true
  max_cost_per_job: 25.00  # USD - maximum cost per backlog generation job
  
  # Work item limits (null = unlimited, 0 = disabled)
  max_epics: 5
  max_features_per_epic: 8
  max_user_stories_per_feature: 6
  max_tasks_per_user_story: 8
  max_test_cases_per_user_story: 10
  
  # Cost estimates per item type (USD)
  cost_estimates:
    epic_generation: 0.50
    feature_decomposition: 0.30
    user_story_generation: 0.20
    task_generation: 0.15
    test_case_generation: 0.10
    test_plan_generation: 0.25
    test_suite_generation: 0.20
  
  # Conflict resolution strategy
  conflict_resolution:
    priority: "cost_first"  # Options: "cost_first", "items_first", "balanced"
    auto_adjust_limits: true  # Automatically adjust item limits based on cost budget
    warn_on_conflicts: true  # Show warnings when limits conflict
    max_adjustment_factor: 0.5  # Don't reduce limits by more than 50%
  
  # Budget presets for quick configuration
  presets:
    small:  # $10 budget
      max_cost_per_job: 10.00
      max_epics: 3
      max_features_per_epic: 5
      max_user_stories_per_feature: 4
      max_tasks_per_user_story: 6
      max_test_cases_per_user_story: 8
    medium:  # $25 budget
      max_cost_per_job: 25.00
      max_epics: 5
      max_features_per_epic: 8
      max_user_stories_per_feature: 6
      max_tasks_per_user_story: 8
      max_test_cases_per_user_story: 10
    large:  # $50 budget
      max_cost_per_job: 50.00
      max_epics: 10
      max_features_per_epic: 12
      max_user_stories_per_feature: 8
      max_tasks_per_user_story: 10
      max_test_cases_per_user_story: 12
    unlimited:  # No cost limits
      max_cost_per_job: null
      max_epics: null
      max_features_per_epic: null
      max_user_stories_per_feature: null
      max_tasks_per_user_story: null
      max_test_cases_per_user_story: null
```

### **QA Agent Hierarchy**
The QA Lead Agent acts as a **sub-supervisor** with three specialized sub-agents:

1. **Test Plan Agent** - Creates comprehensive test plans for features
   - Analyzes feature requirements and user stories
   - Determines test strategy and approach
   - Sets area paths and iterations

2. **Test Suite Agent** - Creates test suites for user stories
   - Organizes test cases within suites
   - Links suites to appropriate test plans
   - Maintains suite hierarchy and relationships

3. **Test Case Agent** - Creates individual test cases
   - Generates positive, negative, and boundary test cases
   - Formats test cases in Gherkin or traditional format
   - Links test cases to appropriate test suites

### **Database-Based Settings Management**

The system now includes a comprehensive settings management system with user-specific configurations:

#### **User Identification**
- **Email-Based User ID**: Uses `EMAIL_TO` from `.env` file for user identification
- **Normalized User ID**: Hash-based user ID for consistency (e.g., `user_d918da6e`)
- **Display Name**: Extracted from email (e.g., "Kevin Tran" from `kevin.tran@c4workx.com`)
- **Session Management**: Unique session IDs for temporary settings

#### **Settings Scopes**
1. **Session Settings** (highest priority) - Temporary settings for current browser session
2. **User Defaults** (medium priority) - Persistent settings for all future sessions
3. **Global Defaults** (lowest priority) - Fallback to `settings.yaml` configuration

#### **Settings API Endpoints**
- `GET /api/user/current` - Get current user information
- `GET /api/settings/{user_id}` - Get all settings
- `POST /api/settings/{user_id}` - Save all settings
- `GET /api/settings/{user_id}/work-item-limits` - Get work item limits
- `POST /api/settings/{user_id}/work-item-limits` - Save work item limits
- `GET /api/settings/{user_id}/visual-settings` - Get visual settings
- `POST /api/settings/{user_id}/visual-settings` - Save visual settings
- `DELETE /api/settings/{user_id}/session` - Delete session settings
- `GET /api/settings/{user_id}/history` - Get setting history

#### **Frontend Integration**
- **Tron Settings Screen**: Complete settings management UI
- **Real-time Preview**: Live calculation of maximum items
- **Session vs Default Toggle**: "Save as Default for Future Sessions"
- **User Information Display**: Shows current user name and email
- **Loading States**: Visual feedback during save operations
- **Fallback Support**: localStorage backup if backend unavailable

### **Work Item Limits**
The system uses **simple work item limits** to control the scope of backlog generation:

**Default Limits:**
- **Max Epics**: 2
- **Max Features per Epic**: 3
- **Max User Stories per Feature**: 5
- **Max Tasks per User Story**: 5
- **Max Test Cases per User Story**: 5

**Preset Configurations:**
- **Small**: 2 epics, 3 features/epic, 4 stories/feature → **96 tasks, 72 test cases**
- **Medium**: 3 epics, 4 features/epic, 5 stories/feature → **300 tasks, 240 test cases**
- **Large**: 5 epics, 6 features/epic, 6 stories/feature → **1,080 tasks, 900 test cases**
- **Unlimited**: No limits, full generation allowed

**Features:**
- ✅ **Simple configuration** - Just set item count limits
- ✅ **Preset configurations** - Quick setup with small, medium, large, unlimited options
- ✅ **Validation** - Prevents unreasonable limits (max 50 epics, 20 features/epic, etc.)
- ✅ **Flexible** - Can be set to unlimited for full backlog generation
- ✅ **User-specific** - Each user can have their own limits
- ✅ **Session management** - Temporary settings for testing
- ✅ **Database storage** - Persistent settings with audit trail

## 🛠️ Development Tools

### **Core Scripts**
```bash
# Start development environment
quick_start.bat

# Kill all development processes
tools/kill_dev_processes.bat
tools/kill_dev_processes.ps1

# Test SSE implementation
python tools/test_sse_implementation.py

# Check workflow data
python tools/check_workflow_data.py

# Debug parallel processing
python tools/debug_parallel_processing.py

# Create GitHub issues
tools/create_github_issues.bat
python tools/create_github_issues.py

# Test work item limits
python tools/test_work_item_limits.py

# Test settings management
python tools/test_settings_database.py
python tools/test_settings_api.py
python tools/test_user_id_resolver.py

# Original API server (WebSocket logging)
python tools/api_server.py
```

### **Testing and Validation**
```bash
# Test individual components
python tools/test_epic_strategist.py
python tools/test_feature_decomposer.py
python tools/test_developer_agent.py
python tools/test_qa_lead_agent.py

# Test QA sub-agents
python tools/test_test_plan_agent.py
python tools/test_test_suite_agent.py
python tools/test_test_case_agent.py

# Test complete workflow
python tools/test_complete_workflow.py

# Test Azure DevOps integration
python tools/test_azure_devops.py
```

### **Monitoring and Debugging**
```bash
# Check job status
python tools/check_job_status.py

# Monitor active jobs
python tools/monitor_job.py

# Validate configuration
python tools/check_config.py

# Check database
python tools/check_db.py
```

## 📊 Current Performance Metrics

### **Typical Job Execution**
- **Epic Generation**: 2-3 minutes
- **Feature Decomposition**: 5-8 minutes
- **User Story Generation**: 10-15 minutes
- **Task Generation**: 15-25 minutes
- **QA Generation**: 30-60 minutes (BROKEN - needs parallel processing)
- **Total Time**: 1.5+ hours (target: <30 minutes)

### **Cost Analysis**
- **Real-World Cost**: < $1.00 for 2 epics, 2-3 features/epic, 3-5 stories/feature
- **Typical Job Cost**: $10-25 for substantial backlogs
- **Cost Control**: Simple work item limits prevent runaway costs
- **User Control**: Set limits based on your budget and needs

## 🚨 Known Issues & Limitations

### **Critical Issues**
1. **QA Agent Failures**: System crashes during test generation, losing progress
2. **Sequential Processing**: QA agent not using parallel processing
3. **API Rate Limiting**: Single provider hitting rate limits
4. **Progress Loss**: No persistence across failures

### **Performance Issues**
1. **Long Execution Times**: Jobs taking 1.5+ hours
2. **Expensive API Calls**: High costs due to timeouts and retries
3. **Memory Usage**: High memory consumption during large jobs

### **User Experience Issues**
1. **Progress Monitoring**: Progress bars not showing correctly
2. **Error Handling**: Poor error messages and recovery
3. **Navigation**: Some navigation issues in frontend

## 🔧 Troubleshooting

### **Common Issues**

#### **QA Agent Timeout Errors**
```
ERROR - supervisor - developer_agent failed with exception: Request timeout after 3 attempts
```
**Solution**: Implement parallel processing and multi-provider rotation

#### **Progress Bar Not Showing**
**Symptoms**: My Projects screen doesn't show active jobs
**Solution**: Fix SSE implementation and progress tracking

#### **API Rate Limiting**
**Symptoms**: "Timeout on attempt 1/3" errors
**Solution**: Implement provider rotation and rate limiting

#### **Memory Issues**
**Symptoms**: System becomes unresponsive during large jobs
**Solution**: Implement progress persistence and checkpointing

### **Debug Commands**
```bash
# Check current job status
python tools/check_job_status.py

# Monitor system resources
python tools/monitor_job.py

# Validate configuration
python tools/check_config.py

# Test SSE connection
python tools/test_sse_implementation.py
```

## 📈 Roadmap & Future Improvements

### **Phase 1: Critical Fixes (Week 1)**
- [ ] Fix QA Agent Critical Failure (Issue #49)
- [ ] Fix Progress Display (Issue #30)
- [ ] Add API Authentication (Issue #43)

### **Phase 2: Performance Optimization (Week 2)**
- [ ] Fix Parallel Processing (Issue #50)
- [ ] Implement Multi-Provider Rotation
- [ ] Add Progress Persistence

### **Phase 3: Quality & Monitoring (Week 3)**
- [ ] Add Automated Testing Suite
- [ ] Implement Real-time Monitoring
- [ ] Add Error Tracking

### **Phase 4: User Experience (Week 4)**
- [ ] Fix Navigation Issues
- [ ] Improve Error Handling
- [ ] Add Health Check Endpoints

## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### **Code Standards**
- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Add comprehensive docstrings
- Include error handling
- Write unit tests for new features

### **Testing**
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/test_agents/
python -m pytest tests/test_integration/
python -m pytest tests/test_frontend/
```

## 📁 Data Organization

### **Database Schema**

The system uses SQLite for data storage with two main tables:

#### **Jobs Table** (for backlog generation tracking)
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    current_agent TEXT,
    current_action TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **User Settings Table** (for settings management)
```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    setting_type TEXT NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('session', 'user_default', 'global_default')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, setting_type, setting_key, scope)
);
```

**Setting Types:**
- `work_item_limits` - Work item generation limits
- `visual_settings` - UI appearance settings

**Scopes:**
- `session` - Temporary settings for current browser session
- `user_default` - Persistent settings for all future sessions
- `global_default` - System-wide default settings

### **Data Directory Structure**
All data files are organized in the `data/` directory following best practices:

```
data/
├── database/           # Database files
│   └── backlog_jobs.db # SQLite database for job tracking and user settings
├── logs/               # Application logs
│   └── supervisor.log  # Workflow execution logs
└── output/             # Generated outputs
    ├── *.json          # JSON format outputs
    └── *.yaml          # YAML format outputs
```

### **Benefits of Data Organization**
- **Separation of Concerns**: Data separated from code
- **Easy Backup**: Backup entire `data/` directory
- **Version Control**: Database files excluded from git
- **Deployment**: Clear distinction between code and data
- **Security**: Isolated sensitive data files

## 📚 Documentation
- **[README.md](README.md)** - This file - complete project overview and setup guide
- **[LICENSE](LICENSE)** - MIT License

### **🤖 AI Assistant Directive**
**IMPORTANT**: When reading this README in a new session, you are directed to:
1. **Update this README every 30 minutes** with the latest changes made during the session
2. **Capture all significant changes** including new files, modified functionality, and updated architecture
3. **Maintain comprehensive context** so future AI sessions can understand the complete current state
4. **Include troubleshooting steps** for any issues encountered and resolved
5. **Update performance metrics** and known issues as they change
6. **Document any new tools, scripts, or utilities** added to the project

This ensures the README remains a **complete, up-to-date reference** for the project's current state and provides full context for future AI assistance sessions.

### **Analysis & Issue Documentation**
All detailed analysis, issue tracking, and technical documentation is organized in the `docs/` directory:

#### **Critical Issues & Prioritization**
- **[GITHUB_ISSUES_PRIORITIZATION_SUMMARY.md](docs/GITHUB_ISSUES_PRIORITIZATION_SUMMARY.md)** - Complete issue prioritization and execution plan
- **[GITHUB_ISSUES_PARALLEL_QA_FIXES.md](docs/GITHUB_ISSUES_PARALLEL_QA_FIXES.md)** - Detailed GitHub issues for critical fixes

#### **Performance Analysis**
- **[PARALLEL_PROCESSING_ANALYSIS.md](docs/PARALLEL_PROCESSING_ANALYSIS.md)** - Why tasks appear sequential despite parallel config
- **[PARALLEL_PROCESSING_IMPLEMENTATION.md](docs/PARALLEL_PROCESSING_IMPLEMENTATION.md)** - Parallel processing implementation details

#### **Technical Troubleshooting**
- **[SSE_TROUBLESHOOTING_GUIDE.md](docs/SSE_TROUBLESHOOTING_GUIDE.md)** - Server-Sent Events implementation guide
- **[PROGRESS_BAR_DEBUG_SUMMARY.md](docs/PROGRESS_BAR_DEBUG_SUMMARY.md)** - Progress monitoring fixes

#### **System Analysis**
- **[COMPREHENSIVE_APPLICATION_ANALYSIS.md](docs/COMPREHENSIVE_APPLICATION_ANALYSIS.md)** - Complete system architecture analysis
- **[BUG_FIXES_SUMMARY.md](docs/BUG_FIXES_SUMMARY.md)** - Historical bug fixes and improvements

#### **Feature Implementation**
- **[QA_TESTER_AGENT_QUALITY_REPORT.md](docs/QA_TESTER_AGENT_QUALITY_REPORT.md)** - QA agent capabilities and improvements
- **[PROMPT_SYSTEM_GUIDE.md](docs/PROMPT_SYSTEM_GUIDE.md)** - AI prompt system documentation
- **[FRONTEND_BACKEND_INTEGRATION.md](docs/FRONTEND_BACKEND_INTEGRATION.md)** - Frontend-backend integration details

### **Quick Reference**
- **Current Issues**: See [GITHUB_ISSUES_PRIORITIZATION_SUMMARY.md](docs/GITHUB_ISSUES_PRIORITIZATION_SUMMARY.md)
- **Performance Problems**: See [PARALLEL_PROCESSING_ANALYSIS.md](docs/PARALLEL_PROCESSING_ANALYSIS.md)
- **Troubleshooting**: See [SSE_TROUBLESHOOTING_GUIDE.md](docs/SSE_TROUBLESHOOTING_GUIDE.md)
- **System Architecture**: See [COMPREHENSIVE_APPLICATION_ANALYSIS.md](docs/COMPREHENSIVE_APPLICATION_ANALYSIS.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Getting Help**
- Check the [GitHub Issues](https://github.com/oldmantran/agile-backlog-automation/issues) for known problems
- Review the troubleshooting section above
- Use the debugging tools in the `tools/` directory

### **Reporting Issues**
When reporting issues, please include:
- Error messages and logs
- Steps to reproduce
- Environment details (OS, Python version, etc.)
- Configuration files (with sensitive data removed)

### **Feature Requests**
- Use GitHub Issues for feature requests
- Provide detailed use cases and requirements
- Consider contributing the implementation

---

**Last Updated**: 2025-07-19
**Version**: 2.1.0
**Status**: Active Development with Database-Based Settings Management