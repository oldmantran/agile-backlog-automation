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
    raw_summary = Column(Text, nullable=True)  # Store JSON as text

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
    job = BacklogJob(
        user_email=user_email,
        project_name=project_name,
        epics_generated=epics_generated,
        features_generated=features_generated,
        user_stories_generated=user_stories_generated,
        tasks_generated=tasks_generated,
        test_cases_generated=test_cases_generated,
        execution_time_seconds=execution_time_seconds,
        raw_summary=json.dumps(raw_summary)
    )
    session.add(job)
    session.commit()
    session.close()

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
