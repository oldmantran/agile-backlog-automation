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
    raw_summary
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
        raw_summary=raw_summary_json
    )
    session.add(job)
    session.commit()
    session.close()

def _sanitize_json_for_storage(data):
    """Recursively sanitize JSON data for database storage."""
    if isinstance(data, dict):
        return {key: _sanitize_json_for_storage(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_sanitize_json_for_storage(item) for item in data]
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

# Helper to get jobs by user

def get_jobs_by_user(user_email):
    session = SessionLocal()
    jobs = session.query(BacklogJob).filter_by(user_email=user_email).order_by(BacklogJob.created_at.desc()).all()
    session.close()
    return jobs

# Helper to get all jobs
def get_all_jobs():
    session = SessionLocal()
    jobs = session.query(BacklogJob).order_by(BacklogJob.created_at.desc()).all()
    session.close()
    return jobs

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
