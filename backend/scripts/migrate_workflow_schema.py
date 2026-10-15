"""
Database migration script to add workflow state machine columns to student_semester_registrations in PostgreSQL.
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

from sqlalchemy import text
from backend.db.database import sync_engine

def migrate_workflow_columns():
    with sync_engine.connect() as conn:
        print("Checking and applying workflow schema columns...")
        conn.execute(text("""
            ALTER TABLE student_semester_registrations 
            ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(30) DEFAULT 'DRAFT',
            ADD COLUMN IF NOT EXISTS workflow_updated_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS workflow_updated_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS workflow_remarks TEXT;
        """))
        conn.commit()
        print("Workflow columns verified / added successfully in PostgreSQL.")

if __name__ == "__main__":
    migrate_workflow_columns()
