from fastapi import APIRouter, HTTPException, Query
from db import get_jobs_by_user, get_all_jobs, init_db
from typing import List

router = APIRouter()

@router.on_event("startup")
def startup_event():
    init_db()

@router.get("/api/backlog/jobs", response_model=List[dict])
def get_jobs(user_email: str = Query(...)):
    jobs = get_jobs_by_user(user_email)
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
        }
        for job in jobs
    ]

@router.get("/api/backlog/jobs/all", response_model=List[dict])
def get_all_jobs_api():
    jobs = get_all_jobs()
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
        }
        for job in jobs
    ]
