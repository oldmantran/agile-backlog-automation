from fastapi import APIRouter, HTTPException, Query
from db import db
from typing import List

router = APIRouter()

@router.on_event("startup")
def startup_event():
    # Database is initialized automatically in the Database class
    pass

@router.get("/api/backlog/jobs", response_model=List[dict])
def get_jobs(
    user_email: str = Query(...),
    exclude_test_generated: bool = Query(True),
    exclude_failed: bool = Query(True),
    exclude_deleted: bool = Query(True)
):
    # For now, return empty list since we're using a different job structure
    # TODO: Implement job filtering based on user_email when needed
    return []

@router.delete("/api/backlog/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete a backlog job"""
    try:
        # Remove job from active jobs
        db.remove_job(job_id)
        return {"status": "success", "message": f"Job {job_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found: {str(e)}")

@router.get("/api/backlog/jobs/all", response_model=List[dict])
def get_all_jobs_api(
    exclude_test_generated: bool = Query(True),
    exclude_failed: bool = Query(True),
    exclude_deleted: bool = Query(True)
):
    jobs = db.get_all_jobs()
    return jobs
