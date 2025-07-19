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
```

### **AI Agent Pipeline**
1. **Epic Strategist** - Transforms product vision into high-level epics
2. **Feature Decomposer** - Breaks epics into features with business value focus
3. **User Story Decomposer** - Creates user stories with acceptance criteria
4. **Developer Agent** - Generates technical tasks with time estimates
5. **QA Lead Agent** - Orchestrates test generation
6. **QA Tester Agent** - Creates test cases and validates acceptance criteria

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
│   ├── qa_lead_agent.py      # QA orchestration agent
│   └── qa/                   # QA sub-agents
├── supervisor/               # Workflow orchestration
│   ├── supervisor.py        # Main workflow supervisor
│   └── main.py              # Supervisor entry point
├── frontend/                # React-based UI
│   ├── src/
│   │   ├── screens/         # Application screens
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API services
│   │   └── hooks/           # Custom React hooks
│   └── package.json
├── docs/                    # Documentation and analysis files
│   ├── GITHUB_ISSUES_PRIORITIZATION_SUMMARY.md
│   ├── PARALLEL_PROCESSING_ANALYSIS.md
│   ├── SSE_TROUBLESHOOTING_GUIDE.md
│   ├── COMPREHENSIVE_APPLICATION_ANALYSIS.md
│   └── ... (other documentation)
├── api_server.py            # Main FastAPI server
├── unified_api_server.py    # Consolidated API server
├── db.py                    # Database operations
├── config/                  # Configuration management
│   ├── config_loader.py
│   └── settings.yaml
├── utils/                   # Utility functions
├── tools/                   # Development and debugging tools
├── integrators/             # External integrations
├── clients/                 # API clients
├── logs/                    # Application logs
├── output/                  # Generated outputs
├── samples/                 # Sample configuration files
├── kill_dev_processes.bat   # Process cleanup (Windows)
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
python api_server.py

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
```

## 🛠️ Development Tools

### **Core Scripts**
```bash
# Start development environment
quick_start.bat

# Kill all development processes
kill_dev_processes.bat

# Test SSE implementation
python tools/test_sse_implementation.py

# Check workflow data
python tools/check_workflow_data.py

# Debug parallel processing
python tools/debug_parallel_processing.py
```

### **Testing and Validation**
```bash
# Test individual components
python tools/test_epic_strategist.py
python tools/test_feature_decomposer.py
python tools/test_developer_agent.py
python tools/test_qa_lead_agent.py

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
- **Current Cost**: $50-100 per job
- **Target Cost**: $10-20 per job
- **Potential Savings**: 70-80% reduction

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

## 📚 Documentation

### **Core Documentation**
- **[README.md](README.md)** - This file - complete project overview and setup guide
- **[LICENSE](LICENSE)** - MIT License

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
**Version**: 2.0.0
**Status**: Active Development with Critical Issues