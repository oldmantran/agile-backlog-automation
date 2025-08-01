# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend
- Start the main API server: `python unified_api_server.py`
- Run a single test: `python -m pytest <test_file.py>::<test_function>`
- Install dependencies: `pip install -r requirements.txt`

### Frontend 
- Start development server: `cd frontend && npm start`
- Build for production: `cd frontend && npm run build`
- Run tests: `cd frontend && npm test`
- Install dependencies: `cd frontend && npm install`

### Testing
- Test Ollama integration: `python tools/test_ollama_integration.py`
- Test Azure DevOps connection: `python tools/test_ado_connection.py`
- Test complete workflow: `python tools/test_complete_workflow.py`

### Development Scripts
- Start application: `tools/start_application.bat` (Windows) or `tools/quick_start.bat`
- Kill development processes: `tools/kill_dev_processes.bat` (Windows)
- Debug QA agents: `python tools/debug_qa_lead_agent.py`
- Scan test artifacts: `python tools/scan_remaining_test_artifacts.py`

## Architecture Overview

This is a multi-agent AI system that transforms product visions into structured Azure DevOps backlogs.

### Core Components

**Frontend**: React TypeScript application with Tailwind CSS and shadcn/ui components. Uses React Query for API state management and provides real-time progress updates via Server-Sent Events.

**Backend**: FastAPI server (`unified_api_server.py`) that orchestrates the AI agent pipeline and provides REST endpoints for the frontend.

**AI Agent Pipeline**: Multi-stage workflow managed by `supervisor/supervisor.py`:
1. `epic_strategist.py` - Creates high-level epics from product vision
2. `feature_decomposer_agent.py` - Breaks epics into features
3. `user_story_decomposer_agent.py` - Creates user stories with acceptance criteria
4. `developer_agent.py` - Generates technical tasks with time estimates
5. `qa_lead_agent.py` - Orchestrates QA sub-agents for test generation

**LLM Provider Support**: 
- Local LLM via Ollama (recommended for cost savings)
- Cloud providers: OpenAI, Grok (xAI)
- Configuration managed through `utils/settings_manager.py`

### Key Directories

- `agents/` - AI agent implementations with base agent class
- `agents/qa/` - QA-specific sub-agents for test management
- `supervisor/` - Workflow orchestration and stage management
- `frontend/src/` - React application with screens, components, and services
- `utils/` - Shared utilities including LLM client management
- `config/` - Configuration files and settings management
- `tools/` - Development and debugging scripts
- `prompts/` - Agent prompt templates

### Database & Configuration

**Database**: SQLite database (`db.py`) for job tracking and user settings persistence.

**Configuration**: YAML-based configuration (`config/settings.yaml`) with support for:
- Agent settings and timeouts
- Work item limits and presets (small/medium/large/unlimited)
- Parallel processing configuration
- QA test organization requirements

**Settings Management**: User-specific settings stored in database with fallback to system defaults, managed through the frontend Settings page.

### Azure DevOps Integration

Full integration with Azure DevOps Test Management API:
- Creates proper work item hierarchy (Epic → Feature → User Story → Task/Test Case)
- Automatic parent-child linking and area path management
- Test plan, test suite, and test case creation with requirement-based organization
- Bulk operations and cleanup utilities in `tools/` directory

### Development Patterns

**Error Handling**: Comprehensive error handling with fallback mechanisms, especially in QA agents to prevent retry loops.

**Parallel Processing**: Configurable parallel execution for agent stages with rate limiting and worker pool management.

**Real-time Updates**: Server-Sent Events (SSE) for live progress updates during backlog generation.

**Testing**: Extensive test suite in `tools/` directory for individual components, integration testing, and Azure DevOps connectivity validation.