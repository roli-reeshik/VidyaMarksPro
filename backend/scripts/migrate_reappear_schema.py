"""
Schema Migration Script for Reappear Auditing and Subject Exemptions.
Adds attempt_number, attempt_label to student_semester_registrations
and is_exempted, original_exam_month_year to student_course_marks.
"""

from backend.db.database import get_sync_session
from sqlalchemy import text


def run_migration():
    with get_sync_session() as session:
        print("Running Reappear DDL migration on vidya_examination_db...")
        session.execute(text("""
            ALTER TABLE student_semester_registrations 
            ADD COLUMN IF NOT EXISTS attempt_number SMALLINT DEFAULT 0,
            ADD COLUMN IF NOT EXISTS attempt_label VARCHAR(30) DEFAULT 'MAIN';

            ALTER TABLE student_course_marks
            ADD COLUMN IF NOT EXISTS is_exempted BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS original_exam_month_year VARCHAR(50);
        """))
        session.commit()
        print("DDL Migration completed successfully.")

        # Verify columns
        res = session.execute(text("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE column_name IN ('attempt_number', 'attempt_label', 'is_exempted', 'original_exam_month_year')
            ORDER BY table_name, column_name;
        """)).fetchall()
        for r in res:
            print(f"  Column confirmed: {r[0]}.{r[1]} ({r[2]})")


if __name__ == "__main__":
    run_migration()
