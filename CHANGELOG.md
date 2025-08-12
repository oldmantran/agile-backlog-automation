# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - August 12, 2025

#### Vision Optimization Feature
- **New Vision Optimizer Agent**: AI-powered vision statement enhancement for generating EXCELLENT quality work items
- **Domain Weighting System**: Support for up to 3 domains with automatic weight distribution:
  - 1 domain: 100%
  - 2 domains: Primary 80%, Secondary 20%
  - 3 domains: Primary 70%, Secondary 20%, Tertiary 10%
- **Database Schema**: New tables for storing optimized visions and tracking associated backlogs
- **Optimize Vision Screen**: New UI for vision optimization with domain selection grid
- **Seamless Integration**: Direct flow from optimization to project creation with pre-populated data
- **API Endpoints**:
  - POST `/api/vision/optimize` - Optimize a vision statement with domain weighting
  - GET `/api/vision/optimized` - Retrieve user's optimized visions
  - GET `/api/vision/optimized/{id}` - Get specific optimized vision
- **Deployment Documentation**: Comprehensive guides for deploying to various platforms

### Changed
- **Removed Auto-Domain Detection**: Manual domain selection is now required in project creation
- **Welcome Screen**: Added "Optimize New Vision" button with purple theme and Sparkles icon

### Fixed
- Module import errors in OptimizeVisionScreen component
- TypeScript type safety for optimizedVisionId in project submission

## [2025.08.11] - August 11, 2025

### Fixed
- **Email Notifications**: Azure DevOps work item URLs now included in completion emails
- **Epic Strategist**: Fixed quality retry mechanism that was producing worse results
- **QA Configuration**: QA sub-agents now properly inherit LLM settings from QA Lead Agent
- **Template Variables**: Resolved naming issues causing workflow failures
- **LLM Configuration**: Fixed save errors and improved error handling

### Changed
- **Epic Generation**: Reduced quality retries from 3 to 1 for better performance
- **Quality Improvement**: Enhanced prompts focus on improving existing epics rather than creating new ones

## [2025.08.10] - August 10, 2025

### Added
- **Configuration Mode Persistence**: Agent-specific mode now properly persists between sessions
- **User Settings Storage**: Configuration mode stored in user_settings table as primary source
- **Streamlined Agent Prompts**: All agents optimized for better quality and maintainability

### Fixed
- **Mode Toggle**: Configuration mode no longer reverts after saving
- **Database Queries**: Fixed ordering issues in configuration lookups
- **UI Synchronization**: Frontend properly refreshes after mode changes

### Changed
- **Prompt Optimization**: 
  - Epic Strategist: 62% reduction in prompt size, quality improved to 86/100
  - All agents: Response format instructions moved to top
  - Added concrete examples showing exact JSON structure
- **Quality Threshold**: Universal 75+ score requirement for all work items

## [Previous Versions]

See git history for changes prior to August 2025.