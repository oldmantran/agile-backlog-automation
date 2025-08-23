# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Last Verified**: January 2025

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

### Testing (Verified Working)
- Test Ollama integration: `python tools/test_ollama_integration.py`
- Test Azure DevOps connection: `python tools/test_ado_connection.py`
- Test complete workflow: `python tools/test_complete_workflow.py`
- Run full regression test suite: `tools/run_regression_tests.bat` (Windows)
- Run pre-commit checks: `python tools/pre_commit_check.py`
- Validate core functionality: `python tests/test_core_smoke.py`
- Test vision processing pipeline: `python tests/test_vision_integration.py`

### Development Scripts
- Start application: `tools/quick_start.bat` (Windows)
- Kill development processes: `tools/kill_dev_processes.bat` (Windows)
- Debug QA agents: `python tools/debug_qa_lead_agent.py`
- Scan test artifacts: `python tools/scan_remaining_test_artifacts.py`
- Debug parallel processing: `python tools/debug_parallel_processing.py`
- Retry failed uploads: `python tools/retry_failed_uploads.py <job_id> [retry|summary|details|cleanup]`

## Quality & Robustness Protocol

**CRITICAL**: Zero tolerance for generic/fallback work items and false success notifications.

### Quality Standards
1. **Minimum Quality Score**: All work items must achieve a quality score of 75 or higher
   - EXCELLENT: 80-100 points (preferred)
   - GOOD: 70-79 points (acceptable if >= 75)
   - FAIR/POOR: Below 70 (rejected)
2. **No Generic Content**: System fails cleanly rather than create placeholder items
3. **Fail-Fast Principle**: Stop immediately when quality standards cannot be met
4. **Accurate Notifications**: Error emails for failures, celebration emails only for true success

### Regression Prevention Protocol

#### Before Making Any Changes:
1. Run regression tests: `tools/run_regression_tests.bat`
2. Document what you're changing and why
3. Identify potential impact areas (vision processing, template system, context flow)

#### After Making Changes:
1. **MANDATORY**: Run `python tools/pre_commit_check.py` - must pass 100%
2. Test specific functionality you modified with targeted tests
3. Run full regression suite before considering changes complete
4. Verify in browser that basic project creation still works

### Core Functions That Must NEVER Break:
- Vision statement processing from API → Supervisor → Agents
- Template variable resolution (uses `${variable}` format)
- Agent prompt generation and LLM communication  
- Project context flow through all stages
- Domain selection and basic project creation
- Settings persistence and retrieval

### Regression Test Files:
- `tests/test_core_smoke.py` - Critical path validation
- `tests/test_vision_integration.py` - End-to-end vision processing
- `tools/pre_commit_check.py` - Pre-commit safety checks
- `tools/run_regression_tests.bat` - Complete test suite

## Architecture Overview

This is a multi-agent AI system that transforms product visions into structured Azure DevOps backlogs.

### Core Components

**Frontend**: React TypeScript application with Tailwind CSS and shadcn/ui components. Uses React Query for API state management.

**Backend**: FastAPI server (`unified_api_server.py`) that orchestrates the AI agent pipeline and provides REST endpoints for the frontend.

**Authentication System**: Basic JWT authentication with bcrypt password hashing. Located in `auth/` directory.

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
- Template System: Comprehensive prompt template system using `${variable}` syntax

### Key Directories (All Verified)
- `agents/` - AI agent implementations with base agent class
- `agents/qa/` - QA-specific sub-agents for test management
- `supervisor/` - Workflow orchestration and stage management
- `frontend/src/` - React application with screens, components, and services
- `auth/` - Basic JWT authentication system
- `utils/` - Shared utilities including LLM client management
- `config/` - Configuration files and settings management
- `tools/` - Development and debugging scripts
- `prompts/` - Agent prompt templates
- `docs/` - Documentation

### Database & Configuration

**Database**: SQLite database (`db.py`) for job tracking and user settings persistence.

**Configuration**: YAML-based configuration (`config/settings.yaml`) with support for:
- Agent settings and timeouts
- Work item limits and presets (small/medium/large/unlimited)
- Parallel processing configuration
- QA test organization requirements

**Quality Configuration**: Managed through `config/quality_config.py`:
- Minimum quality score: 75
- Quality ratings: EXCELLENT (80-100), GOOD (70-79), FAIR (50-69), POOR (0-49)

### Azure DevOps Integration

Full integration with Azure DevOps Test Management API:
- Creates proper work item hierarchy (Epic → Feature → User Story → Task/Test Case)
- Automatic parent-child linking and area path management
- Test plan, test suite, and test case creation with requirement-based organization
- Bulk operations and cleanup utilities in `tools/` directory

### Development Patterns

**Error Handling**: Robust error handling with fail-fast approach. Fallback mechanisms removed in favor of proper error reporting to prevent creation of generic work items.

**Parallel Processing**: Configurable parallel execution for agent stages with rate limiting and worker pool management.

**Testing**: Extensive test suite in `tools/` directory for individual components, integration testing, and Azure DevOps connectivity validation.

## Critical Development Guidelines

### Unicode Encoding Prevention (MANDATORY)
**NEVER use emojis in code** - Windows cp1252 encoding causes UnicodeEncodeError crashes.

```python
# FORBIDDEN - Will crash on Windows
print("✅ Success")
logger.info("❌ Failed")

# REQUIRED - Always use safe logging
from utils.safe_logger import get_safe_logger, safe_print
logger = get_safe_logger(__name__)
logger.info("Success")  # Auto-converts to [SUCCESS]
safe_print("Failed")    # Auto-converts to [ERROR]
```

### LLM Configuration
Use `utils.unified_llm_config.get_agent_config()` for LLM configuration.

Configuration priority (highest to lowest):
1. Runtime overrides (temporary)
2. Database user settings (persistent)  
3. Settings.yaml agent config (project defaults)
4. Environment variables (deployment)
5. Hard-coded fallbacks

## Recent Updates

### Quality Threshold System
- Minimum quality score of 75 required for all work items
- Automatic retry logic when items fail quality checks
- Centralized configuration in `config/quality_config.py`

### Authentication System
- Basic JWT authentication with local user management
- Located in `auth/` directory
- Uses bcrypt for password hashing

### Agent Configuration
- All agents accept user ID for loading user-specific LLM configurations
- Frontend-driven configuration management
- Database persistence for user settings

### Summary Report Generator
- Generate comprehensive backlog summaries from completed jobs
- Includes metrics, quality analysis, and domain alignment
- Access via `/api/reports/summary/{job_id}` endpoint

### Domain Scoring Enhancements
- Enhanced Energy domain knowledge with 40+ terms and 8+ personas
- Flexible domain scoring with 50% weight for better accuracy
- Improved infrastructure and NFR detection

## Current Capabilities
- Multi-agent workflow for backlog generation
- Quality gates with 75+ score requirement
- Real-time progress tracking
- Domain-specific generation for 31+ industries
- Flexible testing generation
- Azure DevOps integration
- Summary report generation with comprehensive metrics

## Important Notes

1. This documentation reflects the actual state of the codebase as of January 2025
2. Some features mentioned in the original CLAUDE.md are not yet implemented
3. Quality threshold is 75+, not 80+ as originally stated
4. No hardware auto-scaling or performance tier detection currently exists
5. No two-phase workflow or test artifact toggle currently implemented
6. No SSE (Server-Sent Events) implementation found
7. No outbox pattern or TodoWrite tool implementation found