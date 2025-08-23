# CLAUDE.md Discrepancy Summary

## Executive Summary

The CLAUDE.md file contains numerous incorrect claims and future-dated features that don't exist in the codebase. This summary provides a quick overview of the major discrepancies found.

## Critical Discrepancies

### 1. Quality Threshold (HIGH PRIORITY)
- **Claims**: 80+ EXCELLENT rating required
- **Reality**: 75+ minimum score (includes GOOD ratings)
- **Impact**: User expectations mismatch

### 2. Future Dating
- **Claims**: Multiple "August 2025" updates
- **Reality**: Current date is January 2025
- **Impact**: Confusing timeline, suggests features not yet built

### 3. Missing Major Features
- Hardware auto-scaling system
- GPT-5 support
- Two-phase workflow with test toggle
- SSE progress tracking
- Async vision optimization
- Outbox pattern for reliability
- TodoWrite/Task tools

### 4. Incorrect Technical Details
- Prompt lines: Claims 42, actual 120
- Template format: Claims dots/underscores, actual `${variable}`
- JWT: Basic implementation, not enterprise system described

## Recommended Actions

1. **Immediate**: Update quality threshold documentation to 75+
2. **High Priority**: Remove or mark unimplemented features as "Planned"
3. **Medium Priority**: Fix all future dates to actual dates
4. **Low Priority**: Clean up formatting and organization

## Files for Reference

- `CLAUDE_CORRECTED.md` - Accurate version based on actual codebase
- `CLAUDE_MD_DISCREPANCIES.md` - Detailed discrepancy report
- `CLAUDE_MD_VERIFICATION_CHECKLIST.md` - Checklist for future verification

## Key Takeaway

The system works well but the documentation significantly overstates its capabilities. The corrected version provides accurate guidance for development work.