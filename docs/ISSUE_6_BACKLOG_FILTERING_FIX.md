# Issue #6 Backlog Filtering and Deletion Fix

## Problem Description

**Issue**: On the My Projects screen, there are tiles with information about previous backlogs created. Many of them are generated and saved in the DB because of system testing and are tagged as "AI Generated Backlog". These test-generated backlogs and failed backlogs should be excluded from the display, and users should have the ability to delete backlog tiles that are not relevant.

**Requirements**:
1. **Exclude test-generated backlogs** (tagged as "AI Generated Backlog")
2. **Exclude failed backlogs**
3. **Add delete functionality** for backlog tiles (soft delete - keep in DB for reference)

## Root Cause Analysis

The issue was that the current system:
1. **No filtering mechanism** - All backlog jobs were displayed regardless of type or status
2. **No status tracking** - Database didn't track job status or test-generated flags
3. **No deletion capability** - Users couldn't remove irrelevant backlog tiles
4. **No soft delete** - No way to hide items while keeping them in DB for reference

## Solution Implemented

### 1. Database Schema Enhancement

**File**: `db.py`

**Changes**:
- Added `status` field to track job status (completed, failed, test_generated)
- Added `is_deleted` field for soft delete functionality (0 = active, 1 = deleted)
- Updated `add_backlog_job()` function to accept status parameter
- Enhanced filtering functions with configurable options

**New Fields**:
```python
status = Column(String, default='completed')  # completed, failed, test_generated
is_deleted = Column(Integer, default=0)  # 0 = active, 1 = soft deleted
```

### 2. Enhanced Database Functions

**New Functions**:
- `get_jobs_by_user()` - Now supports filtering parameters
- `get_all_jobs()` - Now supports filtering parameters
- `soft_delete_job()` - Soft delete functionality
- `get_job_by_id()` - Get individual job by ID

**Filtering Logic**:
```python
# Exclude test-generated backlogs
query = query.filter(
    ~BacklogJob.project_name.like('%Test%'),
    ~BacklogJob.project_name.like('%test%'),
    ~BacklogJob.project_name.like('%AI Generated Backlog%'),
    ~BacklogJob.status.like('%test_generated%')
)

# Exclude failed backlogs
query = query.filter(
    ~BacklogJob.status.like('%failed%'),
    ~BacklogJob.status.like('%Failed%')
)

# Exclude deleted backlogs
query = query.filter_by(is_deleted=0)
```

### 3. API Endpoint Enhancements

**File**: `api_server_jobs.py`

**Changes**:
- Updated `/api/backlog/jobs` endpoint with filtering parameters
- Updated `/api/backlog/jobs/all` endpoint with filtering parameters
- Added `/api/backlog/jobs/{job_id}` DELETE endpoint for soft delete
- Enhanced response schema to include new fields

**New Parameters**:
- `exclude_test_generated` (default: true)
- `exclude_failed` (default: true)
- `exclude_deleted` (default: true)

**New Endpoint**:
```python
@router.delete("/api/backlog/jobs/{job_id}")
def delete_job(job_id: int):
    """Soft delete a backlog job (keeps it in DB for reference)"""
    success = soft_delete_job(job_id)
    if success:
        return {"status": "success", "message": f"Job {job_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
```

### 4. Frontend Type Updates

**File**: `frontend/src/types/backlogJob.ts`

**Changes**:
- Added `status?: string` field
- Added `is_deleted?: number` field

### 5. API Service Updates

**File**: `frontend/src/services/api/backlogApi.ts`

**Changes**:
- Enhanced `getBacklogJobs()` with filtering parameters
- Added `deleteBacklogJob()` function for soft delete

**New Function**:
```typescript
deleteBacklogJob: async (jobId: number): Promise<{ status: string; message: string }> => {
  const response = await api.delete(`/backlog/jobs/${jobId}`);
  return response.data;
}
```

### 6. Frontend UI Enhancements

**File**: `frontend/src/screens/project/MyProjectsScreen.tsx`

**Changes**:
- Added delete functionality with `handleDeleteBacklogJob()`
- Enhanced backlog jobs display with delete buttons
- Added status badges for better visibility
- Added informational text about automatic filtering
- Improved layout with delete buttons in each job tile

**New Features**:
- **Delete Buttons**: Each backlog tile has a trash icon for deletion
- **Status Badges**: Shows job status (completed, failed, etc.)
- **Filtering Info**: Text explaining that test/failed backlogs are automatically filtered
- **Soft Delete**: Items are hidden but remain in database for reference

## How It Works Now

### 1. **Automatic Filtering**
- Test-generated backlogs are identified by project name patterns:
  - Contains "Test" or "test"
  - Contains "AI Generated Backlog"
  - Status contains "test_generated"
- Failed backlogs are identified by status containing "failed" or "Failed"
- Deleted backlogs are filtered by `is_deleted = 1`

### 2. **User-Controlled Deletion**
- Users can click the trash icon on any backlog tile
- Items are soft-deleted (marked as `is_deleted = 1`)
- Items remain in database for reference but are hidden from display
- No data is permanently lost

### 3. **API Flexibility**
- All filtering is configurable via API parameters
- Default behavior excludes test/failed/deleted items
- Can be overridden to show all items if needed

## Benefits of the Fix

### 1. **Cleaner User Interface**
- ✅ No more test-generated backlogs cluttering the display
- ✅ No more failed backlogs showing up
- ✅ Users can remove irrelevant items

### 2. **Better Data Management**
- ✅ Soft delete preserves data for reference
- ✅ Configurable filtering options
- ✅ Status tracking for better organization

### 3. **Improved User Experience**
- ✅ Clear visual indicators for job status
- ✅ Easy deletion of unwanted items
- ✅ Informative messaging about filtering

### 4. **Data Integrity**
- ✅ No permanent data loss
- ✅ Audit trail maintained
- ✅ Flexible filtering options

## Testing

### Test Script Created
**File**: `tools/test_issue_6_backlog_filtering.py`

**Tests**:
- ✅ Database schema validation
- ✅ Backlog filtering functionality
- ✅ Deletion functionality
- ✅ API endpoint verification

### Manual Testing Steps
1. Start the unified API server: `python unified_api_server.py`
2. Navigate to My Projects screen
3. Verify test-generated and failed backlogs are filtered out
4. Test deletion functionality by clicking trash icons
5. Verify deleted items are hidden but not permanently removed

## Files Modified

1. **`db.py`** - Database schema and functions
2. **`api_server_jobs.py`** - API endpoints
3. **`frontend/src/types/backlogJob.ts`** - Type definitions
4. **`frontend/src/services/api/backlogApi.ts`** - API service
5. **`frontend/src/screens/project/MyProjectsScreen.tsx`** - UI enhancements
6. **`tools/test_issue_6_backlog_filtering.py`** - Test script (new)
7. **`ISSUE_6_BACKLOG_FILTERING_FIX.md`** - Documentation (new)

## Migration Notes

### Database Migration
The database schema has been updated with new fields. Existing databases will need to be migrated:

```sql
-- Add new columns to existing database
ALTER TABLE backlog_jobs ADD COLUMN status TEXT DEFAULT 'completed';
ALTER TABLE backlog_jobs ADD COLUMN is_deleted INTEGER DEFAULT 0;
```

### Backward Compatibility
- Existing API calls will continue to work
- Default filtering behavior maintains current functionality
- New parameters are optional with sensible defaults

## Verification

The fix ensures that:

✅ **Test-generated backlogs are filtered out** - No more clutter from system testing  
✅ **Failed backlogs are filtered out** - Only successful backlogs shown  
✅ **Users can delete irrelevant items** - Soft delete functionality implemented  
✅ **Data is preserved** - Items remain in database for reference  
✅ **API is flexible** - Configurable filtering options available  
✅ **UI is improved** - Better visual indicators and user controls  

## Impact

This fix significantly improves the user experience on the My Projects screen by:
- Removing clutter from test-generated backlogs
- Hiding failed backlogs that aren't useful
- Providing user control over what's displayed
- Maintaining data integrity through soft deletes

The changes are **low risk** because:
- No existing data is lost
- API changes are backward compatible
- Soft delete preserves all information
- Filtering is configurable and can be disabled if needed 