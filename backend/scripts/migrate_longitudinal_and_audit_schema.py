"""
Migration script: Longitudinal Sem 1-8 Auto-Insertion, Delivery Lifecycle & Template Design Audit Log
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import os
import sys
from sqlalchemy import text

# Ensure base dir in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db.database import get_sync_session, sync_engine, Base
from backend.db.models import (
    StudentSemesterRegistration,
    CumulativeAcademicSummary,
    MarksAuditLog,
    TemplateDesignAuditLog,
)


def run_migration():
    print("[MIGRATION] Running longitudinal, delivery status & audit schema migration...")
    try:
        with sync_engine.connect() as conn:
            # 1. Update student_semester_registrations
            conn.execute(text("""
                ALTER TABLE student_semester_registrations 
                ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(20) DEFAULT 'PROVISIONAL';
            """))
            conn.execute(text("""
                ALTER TABLE student_semester_registrations 
                ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITH TIME ZONE;
            """))
            conn.execute(text("""
                ALTER TABLE student_semester_registrations 
                ADD COLUMN IF NOT EXISTS delivered_by VARCHAR(100);
            """))

            # 2. Update cumulative_academic_summary
            for s in range(1, 9):
                conn.execute(text(f"""
                    ALTER TABLE cumulative_academic_summary 
                    ADD COLUMN IF NOT EXISTS sem{s}_pct NUMERIC(5, 2);
                """))
                conn.execute(text(f"""
                    ALTER TABLE cumulative_academic_summary 
                    ADD COLUMN IF NOT EXISTS sem{s}_credits NUMERIC(4, 1);
                """))
                conn.execute(text(f"""
                    ALTER TABLE cumulative_academic_summary 
                    ADD COLUMN IF NOT EXISTS sem{s}_sgpa NUMERIC(4, 2);
                """))

            conn.execute(text("""
                ALTER TABLE cumulative_academic_summary 
                ADD COLUMN IF NOT EXISTS total_credits NUMERIC(5, 1) DEFAULT 151.0;
            """))
            conn.execute(text("""
                ALTER TABLE cumulative_academic_summary 
                ADD COLUMN IF NOT EXISTS overall_percentage NUMERIC(5, 2);
            """))
            conn.execute(text("""
                ALTER TABLE cumulative_academic_summary 
                ADD COLUMN IF NOT EXISTS overall_grade VARCHAR(10);
            """))
            conn.execute(text("""
                ALTER TABLE cumulative_academic_summary 
                ADD COLUMN IF NOT EXISTS grading_performance VARCHAR(50);
            """))
            conn.execute(text("""
                ALTER TABLE cumulative_academic_summary 
                ADD COLUMN IF NOT EXISTS final_result VARCHAR(20);
            """))

            # 3. Update marks_audit_log
            conn.execute(text("""
                ALTER TABLE marks_audit_log 
                ADD COLUMN IF NOT EXISTS semester_number SMALLINT;
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_sem ON marks_audit_log(semester_number);
            """))

            # 4. Create template_design_audit_log
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS template_design_audit_log (
                    id SERIAL PRIMARY KEY,
                    semester_number SMALLINT NOT NULL,
                    changed_property VARCHAR(100) NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    modified_by VARCHAR(100) DEFAULT 'Marksheet Layout Studio',
                    modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    notes TEXT
                );
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_template_design_sem ON template_design_audit_log(semester_number);
            """))

            conn.commit()
            print("[MIGRATION] PostgreSQL schema altered successfully.")
    except Exception as e:
        print(f"[MIGRATION WARNING] Skipping direct PG migration (DB might be offline or using SQLite in tests): {e}")

    # Synchronize SQLAlchemy declarative metadata
    try:
        Base.metadata.create_all(bind=sync_engine)
        print("[MIGRATION] SQLAlchemy Base metadata synchronized.")
    except Exception as e:
        print(f"[MIGRATION WARNING] Base.metadata.create_all skipped: {e}")


if __name__ == "__main__":
    run_migration()
