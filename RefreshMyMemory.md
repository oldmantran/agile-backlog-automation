# Project Refresh Guide

## Project Overview
**Agile Backlog Automation** - A sophisticated multi-agent AI system that transforms product visions into structured, actionable backlogs. Built with modern AI models (including local LLM support via Ollama), this system generates epics, features, user stories, developer tasks, and QA test cases with full Azure DevOps integration and advanced work item management capabilities.

**Key Features:**
- **95-99% cost reduction** with local LLM (Ollama) support
- **Multi-agent AI pipeline** for comprehensive backlog generation
- **Real-time progress tracking** with SSE implementation
- **Azure DevOps integration** with full work item hierarchy
- **QA test case generation** with autonomous testing capabilities
- **Settings management** with database persistence

## Codebase Structure
- **`agents/`**: AI Agent implementations (epic_strategist, feature_decomposer, user_story_decomposer, developer_agent, qa_lead_agent)
- **`supervisor/`**: Workflow orchestration (supervisor.py, main.py)
- **`frontend/`**: React-based UI with TypeScript, Tailwind CSS, and Radix UI components
- **`unified_api_server.py`**: Main FastAPI server (consolidated API endpoints)
- **`db.py`**: Database operations for jobs and user settings
- **`config/`**: Configuration management (config_loader.py, settings.yaml)
- **`utils/`**: Utility functions (ollama_client.py, settings_manager.py, user_id_resolver.py)
- **`tools/`**: Development and debugging tools
- **`docs/`**: Comprehensive documentation and analysis files
- **`data/`**: Database files, logs, and generated outputs

## Documentation References
- **`docs/OLLAMA_LOCAL_LLM_IMPLEMENTATION_GUIDE.md`**: Local LLM setup and configuration
- **`docs/COMPREHENSIVE_APPLICATION_ANALYSIS.md`**: Detailed system architecture analysis
- **`docs/FRONTEND_BACKEND_INTEGRATION.md`**: Frontend-backend integration details
- **`docs/QA_TESTER_AGENT_QUALITY_REPORT.md`**: QA agent implementation and quality metrics
- **`docs/PROMPT_SYSTEM_GUIDE.md`**: AI prompt system and agent communication
- **`docs/SSE_TROUBLESHOOTING_GUIDE.md`**: Server-Sent Events troubleshooting
- **`docs/PARALLEL_PROCESSING_ANALYSIS.md`**: Parallel processing implementation details

## Frontend Design
- **Framework**: React 18 with TypeScript
- **UI Libraries**: Tailwind CSS, Radix UI components, Chakra UI icons
- **State Management**: Zustand for global state, React Query for server state
- **Form Handling**: React Hook Form with Yup validation
- **Styling**: Tailwind CSS with custom theme configuration
- **Key Components**: Settings management, real-time progress tracking, project creation wizard
- **Design Assets**: Stored in `frontend/public/icons/` and `frontend/src/components/ui/`

## Configurations
- **`config/settings.yaml`**: Agent configurations, workflow sequences, QA settings
- **`frontend/package.json`**: React dependencies, build scripts, proxy configuration
- **`requirements.txt`**: Python dependencies (FastAPI, SQLAlchemy, Pydantic, etc.)
- **`.env`**: Environment variables for LLM providers, Azure DevOps, API keys
- **`frontend/tailwind.config.ts`**: Tailwind CSS configuration
- **`frontend/tsconfig.json`**: TypeScript compiler options

## Dependencies and Tools
- **Backend**: Python 3.8+, FastAPI, SQLAlchemy, Pydantic, uvicorn
- **Frontend**: Node.js 16+, React 18, TypeScript, Tailwind CSS, Radix UI
- **AI/LLM**: Ollama (local), OpenAI, Grok (xAI) support
- **Database**: SQLite (backlog_jobs.db)
- **External APIs**: Azure DevOps REST API
- **Development**: Vite (via react-scripts), ESLint, PostCSS

## Development Workflow
- **Start Backend**: `python unified_api_server.py` (runs on port 8000)
- **Start Frontend**: `cd frontend && npm start` (runs on port 3000)
- **Quick Start**: `quick_start.bat` (Windows batch script)
- **Testing**: `python tools/test_ollama_integration.py` (Ollama tests)
- **Database**: SQLite database in `data/database/backlog_jobs.db`
- **Logs**: Application logs in `data/logs/` and `logs/`

## Recent Changes
- **Ollama Local LLM Integration**: Full support for local LLM inference with 95-99% cost reduction
- **Enhanced Settings Management**: Complete user settings system with database persistence
- **QA Agent Resilience**: Robust fallback mechanisms to prevent retry loops
- **Real-time Progress**: SSE implementation with live updates
- **System Defaults Toggle**: Users can choose between system defaults and custom settings
- **Cost Control**: User-specific work item limits with database persistence

## Additional Context
- **LLM Provider Support**: Ollama (local), OpenAI, Grok (xAI) with model switching
- **Work Item Hierarchy**: Epic → Feature → User Story → Task/Test Case
- **Azure DevOps Integration**: Full work item creation with proper parent-child relationships
- **QA Pipeline**: Test Plan → Test Suite → Test Case generation with autonomous testing metadata
- **Hardware Requirements**: 8GB RAM minimum, 16GB+ recommended, NVIDIA GPU for optimal performance
- **Cost Analysis**: Local LLM costs ~$0.02-0.05 per job vs $5-15 for cloud providers
- **Database Schema**: Jobs tracking, user settings, work item limits, session management
- **Error Handling**: Graceful degradation with comprehensive logging and fallback mechanisms 