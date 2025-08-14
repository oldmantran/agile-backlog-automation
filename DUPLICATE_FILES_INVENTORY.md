# Duplicate/Versioned Files Inventory Report

## Executive Summary
This repository contains multiple versions of files that are causing confusion and potential bugs. The most critical issue is with quality assessor files where v2 versions exist alongside original versions, but only some agents use the v2 versions.

## Critical Issues Found

### 1. Quality Assessor Version Confusion

#### Files with Both Original and V2 Versions:
- `utils/epic_quality_assessor.py` vs `utils/epic_quality_assessor_v2.py`
- `utils/feature_quality_assessor.py` vs `utils/feature_quality_assessor_v2.py`
- `utils/user_story_quality_assessor.py` vs `utils/user_story_quality_assessor_v2.py`

#### Current Usage:
- **Epic Strategist**: Uses `epic_quality_assessor_v2.py` ✅
- **Feature Decomposer**: Uses `feature_quality_assessor_v2.py` ✅
- **User Story Decomposer**: Uses `user_story_quality_assessor_v2.py` ✅
- **Developer Agent**: Uses `task_quality_assessor.py` (no v2 exists)
- **Vision Optimizer**: Uses `vision_quality_assessor.py` (no v2 exists)

**PROBLEM**: When fixing bugs (like the agriculture domain issue), developers may fix the wrong version of the file.

### 2. Frontend Component Duplicates

#### Duplicate Screen Components:
- `BacklogSweeperScreen.tsx` vs `BacklogSweeperScreen_new.tsx`
- `WorkItemsCleanupScreen.tsx` vs `WorkItemsCleanupScreen_NEW.tsx`
- `TestCasesCleanupScreen.tsx` vs `TestCasesCleanupScreen_NEW.tsx`
- Original `MainDashboard.tsx` appears to be missing (only `MainDashboard_NEW.tsx` exists)

#### Current Usage in App.tsx:
- Both versions of BacklogSweeperScreen are imported and used on different routes
- Both versions of cleanup screens are imported but routes are incomplete
- Routes use `/backlog-sweeper` (old) and `/backlog-sweeper-new` (new)

### 3. Other Duplicates

#### Agent Files:
- `agents/developer_agent.py` (active) vs `agents/developer_agent_old.py` (backup?)

#### Tool Scripts:
- `tools/optimize_ollama_gpu.py` (assumed) vs `tools/optimize_ollama_gpu_v2.py`

#### Prompt Templates:
- `prompts/epic_strategist.txt` vs `prompts/epic_strategist_v2.txt`
- **NOTE**: Need to verify which prompt file is actually being used by the epic strategist

## Recommendations

### Immediate Actions Required:

1. **Consolidate Quality Assessors**:
   - Merge improvements from v1 into v2 versions
   - Delete v1 versions
   - Update all imports to use consistent versions
   - Rename v2 files to remove "_v2" suffix

2. **Clean Up Frontend Components**:
   - Determine which version of each screen is production-ready
   - Delete unused versions
   - Update App.tsx to use only one version of each component
   - Remove duplicate routes

3. **Remove Old/Backup Files**:
   - Delete `developer_agent_old.py` if it's just a backup
   - Evaluate if v2 tool scripts should replace originals

4. **Standardize Naming Convention**:
   - Never use "_v2", "_new", "_old", "_NEW" suffixes
   - Use git for version control, not file naming
   - If multiple implementations are needed, use descriptive names (e.g., `BacklogSweeperGridView.tsx` vs `BacklogSweeperListView.tsx`)

### Long-term Best Practices:

1. **Use Git Branches**: For experimental versions, use feature branches instead of creating duplicate files
2. **Delete Before Committing**: Never commit backup/old versions to the repository
3. **Single Source of Truth**: Each component/module should have exactly one implementation file
4. **Clear Migration Path**: When replacing components, do it atomically - update all references in one commit

## Impact Analysis

The current state is causing:
1. **Bug Fix Confusion**: Developers may fix bugs in the wrong version of files (as happened with the agriculture domain issue)
2. **Maintenance Overhead**: Changes must be duplicated across multiple versions
3. **Testing Complexity**: Unclear which versions are being tested
4. **Onboarding Difficulty**: New developers don't know which files to modify
5. **Potential Runtime Errors**: Different parts of the system using different versions of the same logic

## Prompt Files Analysis

### The Prompt Loading System
- Prompts are loaded by `PromptTemplateManager` based on exact agent name
- Only files matching `{agent_name}.txt` are loaded
- Version suffixes (`_v2`, `_enhanced`, etc.) are IGNORED

### Active vs Inactive Prompts
**ACTIVE (10 files)**:
- ✅ `epic_strategist.txt`
- ✅ `developer_agent.txt` (missing domain examples!)
- ✅ `feature_decomposer_agent.txt`
- ✅ `user_story_decomposer.txt`
- ✅ `backlog_sweeper_agent.txt`
- ✅ `vision_optimizer_agent.txt`
- ✅ `qa_lead_agent.txt`
- ✅ `test_plan_agent.txt`
- ✅ `test_suite_agent.txt`
- ✅ `test_case_agent.txt`

**INACTIVE (9 files - should be deleted!)**:
- ❌ `epic_strategist_v2.txt`
- ❌ `epic_strategist_original.txt`
- ❌ `developer_agent_original.txt`
- ❌ `developer_agent_enhanced.txt`
- ❌ `developer_agent_domain_enhanced.txt` (HAS THE DOMAIN EXAMPLES!)
- ❌ `feature_decomposer_agent_original.txt`
- ❌ `user_story_decomposer_original.txt`
- ❌ `backlog_sweeper_agent_original.txt`
- ❌ `vision_optimizer.txt`

### Critical Finding
The `developer_agent_domain_enhanced.txt` contains all 31 domain-specific technical examples but is NOT being used! The active `developer_agent.txt` lacks these enhancements.

## Complete Duplicate Files Summary

### Python Files:
- **Quality Assessors**: 3 files have both original and v2 versions (6 files total, 3 duplicates)
- **Agent Files**: 1 old backup file (`developer_agent_old.py`)

### Frontend Components:
- **Screens**: 4 components have duplicate versions (8 files total, 4 duplicates)

### Prompt Templates:
- **Prompts**: 19 total files, 9 are unused duplicates

### Total Waste:
- **17 duplicate/unused files** across the repository
- Confusion about which versions are active
- Lost work (domain enhancements not being used)

## Action Items

1. [ ] Merge `developer_agent_domain_enhanced.txt` content into `developer_agent.txt`
2. [ ] Delete all 9 inactive prompt files
3. [ ] Consolidate v2 quality assessors (remove v2 suffix after merging)
4. [ ] Clean up frontend duplicate components
5. [ ] Delete `developer_agent_old.py`
6. [ ] Add .gitignore rules to prevent committing files with version suffixes
7. [ ] Create a naming convention guide
8. [ ] Document all consolidations in CHANGELOG.md