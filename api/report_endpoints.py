"""
API endpoints for backlog generation summary reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
import json
from pathlib import Path
import sqlite3

from auth.auth_routes import get_current_user
from auth.user_auth import User
from utils.report_generator import BacklogSummaryReportGenerator
from utils.safe_logger import get_safe_logger

logger = get_safe_logger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/backlog/{job_id}/summary")
async def get_backlog_summary_report(
    job_id: int,
    format: Optional[str] = "json",
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive summary report for a backlog generation job.
    
    Args:
        job_id: The backlog job ID
        format: Output format - 'json' or 'markdown' (default: json)
        
    Returns:
        Summary report in requested format
    """
    try:
        # Get job data from database using direct SQLite connection
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        query = """
            SELECT id, project_name, created_at, status,
                   epics_generated, features_generated, user_stories_generated,
                   tasks_generated, test_cases_generated, execution_time_seconds,
                   raw_summary
            FROM backlog_jobs
            WHERE id = ? AND user_id = ? AND is_deleted = 0
        """
        
        cursor.execute(query, (job_id, current_user.id))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Backlog job not found")
        
        # Convert to dict
        job_data = {
            'id': result[0],
            'project_name': result[1],
            'created_at': str(result[2]),
            'status': result[3],
            'epics_generated': result[4],
            'features_generated': result[5],
            'user_stories_generated': result[6],
            'tasks_generated': result[7],
            'test_cases_generated': result[8],
            'execution_time_seconds': result[9],
            'raw_summary': result[10]
        }
        
        # Get log file path from raw_summary
        raw_summary = {}
        if job_data['raw_summary']:
            try:
                raw_summary = json.loads(job_data['raw_summary']) if isinstance(job_data['raw_summary'], str) else job_data['raw_summary']
            except:
                pass
        
        # Try to find the log file
        job_id_str = raw_summary.get('job_id', '')
        if not job_id_str:
            # Try to construct from created_at
            created_date = job_data['created_at'].replace('-', '').replace(' ', '_').replace(':', '')[:15]
            job_id_str = f"job_{created_date}_proj_{created_date}"
        
        log_patterns = [
            f"logs/backend_*{job_id_str}*.log",
            f"logs/backend_{created_date}*.log",
            f"logs/supervisor_{created_date}*.log"
        ]
        
        log_content = ""
        log_file_found = False
        
        for pattern in log_patterns:
            log_files = list(Path('.').glob(pattern))
            if log_files:
                # Use the most recent file
                log_file = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    log_file_found = True
                    logger.info(f"Found log file: {log_file}")
                    break
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
        
        if not log_file_found:
            logger.warning(f"No log file found for job {job_id}")
        
        # Generate report
        generator = BacklogSummaryReportGenerator()
        report_data = generator.generate_report(job_data, log_content)
        
        # Return in requested format
        if format.lower() == 'markdown':
            markdown_content = generator.format_markdown_report(report_data)
            return Response(
                content=markdown_content,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"inline; filename=backlog_summary_{job_id}.md"
                }
            )
        else:
            return report_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating backlog summary report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backlog/{job_id}/summary/download")
async def download_backlog_summary_report(
    job_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Download the backlog summary report as a markdown file.
    
    Args:
        job_id: The backlog job ID
        
    Returns:
        Markdown file download
    """
    try:
        # Use the existing endpoint to generate the report
        markdown_content = await get_backlog_summary_report(
            job_id=job_id,
            format="markdown",
            current_user=current_user
        )
        
        return Response(
            content=markdown_content.body,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=backlog_summary_{job_id}.md"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backlog summary report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Temporary test endpoint without auth
@router.get("/test/backlog/{job_id}/summary/download")
async def test_download_backlog_summary_report(
    job_id: int
):
    """
    Test endpoint - Download the backlog summary report without authentication.
    
    Args:
        job_id: The backlog job ID
        
    Returns:
        Markdown file download
    """
    try:
        # Get job data from database - simplified without user check
        conn = sqlite3.connect('backlog_jobs.db')
        cursor = conn.cursor()
        
        query = """
            SELECT id, project_name, created_at, status,
                   epics_generated, features_generated, user_stories_generated,
                   tasks_generated, test_cases_generated, execution_time_seconds,
                   raw_summary
            FROM backlog_jobs
            WHERE id = ? AND is_deleted = 0
        """
        
        cursor.execute(query, (job_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Backlog job not found")
        
        # Convert to dict (same as main endpoint)
        job_data = {
            'id': result[0],
            'project_name': result[1],
            'created_at': str(result[2]),
            'status': result[3],
            'epics_generated': result[4],
            'features_generated': result[5],
            'user_stories_generated': result[6],
            'tasks_generated': result[7],
            'test_cases_generated': result[8],
            'execution_time_seconds': result[9],
            'raw_summary': result[10]
        }
        
        # Generate report (rest is same as authenticated endpoint)
        raw_summary = {}
        if job_data['raw_summary']:
            try:
                raw_summary = json.loads(job_data['raw_summary']) if isinstance(job_data['raw_summary'], str) else job_data['raw_summary']
            except:
                pass
        
        # Try to find the log file
        job_id_str = raw_summary.get('job_id', '')
        if not job_id_str:
            created_date = job_data['created_at'].replace('-', '').replace(' ', '_').replace(':', '')[:15]
            job_id_str = f"job_{created_date}_proj_{created_date}"
        
        log_patterns = [
            f"logs/backend_*{job_id_str}*.log",
            f"logs/backend_{created_date}*.log",
            f"logs/supervisor_{created_date}*.log"
        ]
        
        log_content = ""
        log_file_found = False
        
        for pattern in log_patterns:
            log_files = list(Path('.').glob(pattern))
            if log_files:
                log_file = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    log_file_found = True
                    logger.info(f"Found log file: {log_file}")
                    break
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
        
        if not log_file_found:
            logger.warning(f"No log file found for job {job_id}")
        
        # Generate report
        generator = BacklogSummaryReportGenerator()
        report_data = generator.generate_report(job_data, log_content)
        markdown_content = generator.format_markdown_report(report_data)
        
        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=backlog_summary_{job_id}.md"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test download endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))