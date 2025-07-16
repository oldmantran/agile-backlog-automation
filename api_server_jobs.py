from fastapi import APIRouter, HTTPException, Query
from db import get_jobs_by_user, get_all_jobs, init_db, soft_delete_job
from typing import List

router = APIRouter()

@router.on_event("startup")
def startup_event():
    init_db()

@router.get("/api/backlog/jobs", response_model=List[dict])
def get_jobs(
    user_email: str = Query(...),
    exclude_test_generated: bool = Query(True),
    exclude_failed: bool = Query(True),
    exclude_deleted: bool = Query(True)
):
    jobs = get_jobs_by_user(user_email, exclude_test_generated, exclude_failed, exclude_deleted)
    return [
        {
            "id": job.id,
            "user_email": job.user_email,
            "project_name": job.project_name,
            "epics_generated": job.epics_generated,
            "features_generated": job.features_generated,
            "user_stories_generated": job.user_stories_generated,
            "tasks_generated": job.tasks_generated,
            "test_cases_generated": job.test_cases_generated,
            "execution_time_seconds": job.execution_time_seconds,
            "created_at": job.created_at,
            "raw_summary": job.raw_summary,
            "status": job.status,
            "is_deleted": job.is_deleted,
        }
        for job in jobs
    ]

@router.delete("/api/backlog/jobs/{job_id}")
def delete_job(job_id: int):
    """Soft delete a backlog job (keeps it in DB for reference)"""
    success = soft_delete_job(job_id)
    if success:
        return {"status": "success", "message": f"Job {job_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@router.get("/api/backlog/jobs/all", response_model=List[dict])
def get_all_jobs_api(
    exclude_test_generated: bool = Query(True),
    exclude_failed: bool = Query(True),
    exclude_deleted: bool = Query(True)
):
    jobs = get_all_jobs(exclude_test_generated, exclude_failed, exclude_deleted)
    return [
        {
            "id": job.id,
            "user_email": job.user_email,
            "project_name": job.project_name,
            "epics_generated": job.epics_generated,
            "features_generated": job.features_generated,
            "user_stories_generated": job.user_stories_generated,
            "tasks_generated": job.tasks_generated,
            "test_cases_generated": job.test_cases_generated,
            "execution_time_seconds": job.execution_time_seconds,
            "created_at": job.created_at,
            "raw_summary": job.raw_summary,
            "status": job.status,
            "is_deleted": job.is_deleted,
        }
        for job in jobs
    ]
