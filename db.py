from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import JSON as SQLAlchemyJSON
import datetime
import json

Base = declarative_base()

class BacklogJob(Base):
    __tablename__ = 'backlog_jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    epics_generated = Column(Integer, nullable=False)
    features_generated = Column(Integer, nullable=False)
    user_stories_generated = Column(Integer, nullable=False)
    tasks_generated = Column(Integer, nullable=False)
    test_cases_generated = Column(Integer, nullable=False)
    execution_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    raw_summary = Column(Text, nullable=True)  # Store JSON as text with UTF-8 encoding
    status = Column(String, default='completed')  # completed, failed, test_generated
    is_deleted = Column(Integer, default=0)  # 0 = active, 1 = soft deleted

# SQLite DB file
engine = create_engine('sqlite:///backlog_jobs.db', echo=False)
SessionLocal = sessionmaker(bind=engine)

# Create tables if not exist
def init_db():
    Base.metadata.create_all(engine)

# Helper to add a job
def add_backlog_job(
    user_email,
    project_name,
    epics_generated,
    features_generated,
    user_stories_generated,
    tasks_generated,
    test_cases_generated,
    execution_time_seconds,
    raw_summary,
    status='completed'
):
    session = SessionLocal()
    
    # Ensure proper UTF-8 encoding for JSON data
    if raw_summary:
        # Sanitize any Unicode characters in the summary
        sanitized_summary = _sanitize_json_for_storage(raw_summary)
        raw_summary_json = json.dumps(sanitized_summary, ensure_ascii=False)
    else:
        raw_summary_json = None
        
    job = BacklogJob(
        user_email=user_email,
        project_name=project_name,
        epics_generated=epics_generated,
        features_generated=features_generated,
        user_stories_generated=user_stories_generated,
        tasks_generated=tasks_generated,
        test_cases_generated=test_cases_generated,
        execution_time_seconds=execution_time_seconds,
        raw_summary=raw_summary_json,
        status=status
    )
    session.add(job)
    session.commit()
    session.close()

def _sanitize_json_for_storage(data):
    """Recursively sanitize JSON data for database storage."""
    # Handle circular references and complex objects
    if hasattr(data, '__dict__'):
        # Convert objects to dict, but be careful of circular refs
        try:
            data = data.__dict__
        except:
            return str(data)
    
    if isinstance(data, dict):
        sanitized_dict = {}
        for key, value in data.items():
            try:
                sanitized_dict[str(key)] = _sanitize_json_for_storage(value)
            except (RecursionError, TypeError):
                sanitized_dict[str(key)] = str(value)
        return sanitized_dict
    elif isinstance(data, list):
        sanitized_list = []
        for item in data:
            try:
                sanitized_list.append(_sanitize_json_for_storage(item))
            except (RecursionError, TypeError):
                sanitized_list.append(str(item))
        return sanitized_list
    elif isinstance(data, str):
        # Sanitize Unicode characters in strings
        import re
        # Replace common Unicode characters
        replacements = {
            '✅': '[SUCCESS]',
            '❌': '[FAILED]',
            '⚠️': '[WARNING]',
            '📊': '[STATS]',
            '🔍': '[SEARCH]',
            '📝': '[NOTE]',
            '🎯': '[TARGET]',
            '🚀': '[LAUNCH]',
            '💡': '[IDEA]',
            '🔧': '[TOOL]',
            '📋': '[CHECKLIST]',
            '🎨': '[DESIGN]',
            '🔒': '[SECURE]',
            '🌟': '[STAR]',
            '⭐': '[STAR]',
            '🎉': '[CELEBRATE]',
            '🔄': '[REFRESH]',
            '📈': '[TREND]',
            '💾': '[SAVE]',
            '🎪': '[EVENT]',
            '🚨': '[ALERT]',
            '📧': '[EMAIL]',
            '📤': '[SEND]',
            '📥': '[RECEIVE]'
        }
        
        for unicode_char, replacement in replacements.items():
            data = data.replace(unicode_char, replacement)
        
        # Remove any remaining problematic Unicode characters
        data = re.sub(r'[^\x00-\x7F]+', '?', data)
        return data
    else:
        return data

# Helper to get jobs by user (filtered)
def get_jobs_by_user(user_email, exclude_test_generated=True, exclude_failed=True, exclude_deleted=True):
    session = SessionLocal()
    query = session.query(BacklogJob).filter_by(user_email=user_email)
    
    if exclude_deleted:
        query = query.filter_by(is_deleted=0)
    
    if exclude_test_generated:
        # Exclude test-generated backlogs (identified by project name patterns)
        query = query.filter(
            ~BacklogJob.project_name.like('%Test%'),
            ~BacklogJob.project_name.like('%test%'),
            ~BacklogJob.project_name.like('%AI Generated Backlog%'),
            ~BacklogJob.status.like('%test_generated%')
        )
    
    if exclude_failed:
        # Exclude failed backlogs
        query = query.filter(
            ~BacklogJob.status.like('%failed%'),
            ~BacklogJob.status.like('%Failed%')
        )
    
    jobs = query.order_by(BacklogJob.created_at.desc()).all()
    session.close()
    return jobs

# Helper to get all jobs (filtered)
def get_all_jobs(exclude_test_generated=True, exclude_failed=True, exclude_deleted=True):
    session = SessionLocal()
    query = session.query(BacklogJob)
    
    if exclude_deleted:
        query = query.filter_by(is_deleted=0)
    
    if exclude_test_generated:
        # Exclude test-generated backlogs
        query = query.filter(
            ~BacklogJob.project_name.like('%Test%'),
            ~BacklogJob.project_name.like('%test%'),
            ~BacklogJob.project_name.like('%AI Generated Backlog%'),
            ~BacklogJob.status.like('%test_generated%')
        )
    
    if exclude_failed:
        # Exclude failed backlogs
        query = query.filter(
            ~BacklogJob.status.like('%failed%'),
            ~BacklogJob.status.like('%Failed%')
        )
    
    jobs = query.order_by(BacklogJob.created_at.desc()).all()
    session.close()
    return jobs

# Helper to soft delete a job
def soft_delete_job(job_id):
    session = SessionLocal()
    job = session.query(BacklogJob).filter_by(id=job_id).first()
    if job:
        job.is_deleted = 1
        session.commit()
        session.close()
        return True
    session.close()
    return False

# Helper to get job by ID
def get_job_by_id(job_id):
    session = SessionLocal()
    job = session.query(BacklogJob).filter_by(id=job_id).first()
    session.close()
    return job

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
