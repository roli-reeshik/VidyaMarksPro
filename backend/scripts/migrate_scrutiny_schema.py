"""
Database Migration Script for Scrutiny Verification Studio & App Feedback
Creates tables:
- scrutiny_verifications
- app_feedback
Adds columns to student_semester_registrations:
- scrutiny_status VARCHAR(30) DEFAULT 'PENDING'
- last_scrutinized_at TIMESTAMP WITH TIME ZONE
VidyaLabs Copyright © 2026.
"""

from sqlalchemy import text
from backend.db.database import sync_engine, Base, get_sync_session
from backend.db.models import ScrutinyVerification, AppFeedback

def run_migration():
    print("Starting Scrutiny & Feedback Schema Migration...")
    
    # 1. Add columns to student_semester_registrations
    with get_sync_session() as session:
        session.execute(text("""
            ALTER TABLE student_semester_registrations 
            ADD COLUMN IF NOT EXISTS scrutiny_status VARCHAR(30) DEFAULT 'PENDING';
        """))
        session.execute(text("""
            ALTER TABLE student_semester_registrations 
            ADD COLUMN IF NOT EXISTS last_scrutinized_at TIMESTAMP WITH TIME ZONE;
        """))
        session.commit()
        print("  - Added scrutiny_status and last_scrutinized_at to student_semester_registrations.")

    # 2. Create tables using SQLAlchemy metadata
    Base.metadata.create_all(bind=sync_engine, tables=[
        AppFeedback.__table__,
        ScrutinyVerification.__table__
    ])
    print("  - Ensured app_feedback and scrutiny_verifications tables exist.")
    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
