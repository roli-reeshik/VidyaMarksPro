"""
Schema Migration Script for Semester 4 Three-Section Split (PHAR + PATH + GEN).
Adds external_part_c NUMERIC(5, 2) to student_course_marks.
"""

from backend.db.database import get_sync_session
from sqlalchemy import text


def run_migration():
    with get_sync_session() as session:
        print("Running Semester 4 external_part_c DDL migration on vidya_examination_db...")
        session.execute(text("""
            ALTER TABLE student_course_marks
            ADD COLUMN IF NOT EXISTS external_part_c NUMERIC(5, 2);
        """))
        session.commit()
        print("DDL Migration completed successfully.")

        # Verify column
        res = session.execute(text("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'student_course_marks' 
              AND column_name IN ('external_part_a', 'external_part_b', 'external_part_c')
            ORDER BY column_name;
        """)).fetchall()
        for r in res:
            print(f"  Column confirmed: {r[0]}.{r[1]} ({r[2]})")


if __name__ == "__main__":
    run_migration()
