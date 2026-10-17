"""
Master Local PostgreSQL Database Initializer for VidyaMarksheet (Home PC Environment)
Developed at VidyaLabs | Priyanka Kumari (+91-9140189586)
Compliant with INC Gazette Regulations & SGPGIMS Lucknow Regulations.

Autonomous & Idempotent initialization pipeline:
Connection -> DB Verification -> Schema DDL -> Extended Migrations -> Data Seed -> Health Audit
"""

import os
import sys
from urllib.parse import quote_plus
from decimal import Decimal

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import text

# Load configuration strictly from backend/.env
ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(ENV_PATH, override=True)

DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "vidya_examination_db")
DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432"))


def step_print(stage: str, msg: str):
    print(f"[{stage}] {msg}")


def main():
    print("=" * 80)
    print(" VidyaMarksheet: PostgreSQL Database Initialization Pipeline (Home PC)")
    print(" Developed at VidyaLabs | Priyanka Kumari")
    print("=" * 80)
    print(f"Active Environment Config: {ENV_PATH}")
    print(f"Target DB: {DB_NAME} | Host: {DB_HOST}:{DB_PORT} | User: {DB_USER}")
    print("=" * 80)

    db_creation_status = "EXISTS"

    # -------------------------------------------------------------------------
    # STAGE 1: Dynamic Credential Handshake & Database Verification / Creation
    # -------------------------------------------------------------------------
    step_print("STAGE 1: HANDSHAKE", "Connecting to PostgreSQL maintenance database ('postgres')...")
    try:
        maintenance_conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=5,
        )
        maintenance_conn.autocommit = True
        step_print("STAGE 1: HANDSHAKE", "Maintenance handshake successful.")
    except Exception as e:
        print(f"\n[FATAL] Failed to connect to PostgreSQL maintenance database: {e}")
        sys.exit(1)

    with maintenance_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cur.fetchone()
        if not exists:
            step_print("STAGE 1: DB CREATION", f"Database '{DB_NAME}' not found. Executing CREATE DATABASE...")
            cur.execute(f'CREATE DATABASE "{DB_NAME}";')
            db_creation_status = "CREATED"
            step_print("STAGE 1: DB CREATION", f"Database '{DB_NAME}' created successfully.")
        else:
            db_creation_status = "EXISTS"
            step_print("STAGE 1: DB VERIFICATION", f"Database '{DB_NAME}' already exists.")

    maintenance_conn.close()

    # -------------------------------------------------------------------------
    # STAGE 2: Core Schema Construction (schema.sql & models.py)
    # -------------------------------------------------------------------------
    step_print("STAGE 2: SCHEMA DDL", f"Connecting to target database '{DB_NAME}' for schema application...")
    
    # Import SQLAlchemy engine and models
    from backend.db.database import sync_engine, Base
    from backend.db.models import (
        Batch,
        Student,
        Course,
        StudentSemesterRegistration,
        StudentCourseMark,
        CumulativeAcademicSummary,
        MarksAuditLog,
    )

    schema_sql_path = os.path.join(BASE_DIR, "backend", "db", "schema.sql")
    if os.path.exists(schema_sql_path):
        step_print("STAGE 2: SCHEMA DDL", f"Applying raw DDL from {schema_sql_path}...")
        with open(schema_sql_path, "r", encoding="utf-8") as f:
            ddl_content = f.read()

        # Connect directly via psycopg2 to execute schema.sql script
        conn_target = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        conn_target.autocommit = True
        with conn_target.cursor() as cur:
            cur.execute(ddl_content)
        conn_target.close()
        step_print("STAGE 2: SCHEMA DDL", "schema.sql DDL applied successfully.")

    step_print("STAGE 2: SCHEMA DDL", "Synchronizing SQLAlchemy declarative metadata via create_all()...")
    Base.metadata.create_all(bind=sync_engine)
    step_print("STAGE 2: SCHEMA DDL", "SQLAlchemy base models synchronized.")

    # -------------------------------------------------------------------------
    # STAGE 3: Execute Schema Migration Scripts
    # -------------------------------------------------------------------------
    step_print("STAGE 3: MIGRATIONS", "Running reappear schema migration (backend/scripts/migrate_reappear_schema.py)...")
    from backend.scripts.migrate_reappear_schema import run_migration as run_reappear_migration
    run_reappear_migration()
    step_print("STAGE 3: MIGRATIONS", "Reappear schema migration completed.")

    step_print("STAGE 3: MIGRATIONS", "Running workflow schema migration (backend/scripts/migrate_workflow_schema.py)...")
    from backend.scripts.migrate_workflow_schema import migrate_workflow_columns
    migrate_workflow_columns()
    step_print("STAGE 3: MIGRATIONS", "Workflow schema migration completed.")

    step_print("STAGE 3: MIGRATIONS", "Running Semester 4 external_part_c migration (backend/scripts/migrate_sem4_part_c.py)...")
    from backend.scripts.migrate_sem4_part_c import run_migration as run_sem4_migration
    run_sem4_migration()
    step_print("STAGE 3: MIGRATIONS", "Semester 4 external_part_c migration completed.")

    step_print("STAGE 3: MIGRATIONS", "Running longitudinal & audit schema migration (backend/scripts/migrate_longitudinal_and_audit_schema.py)...")
    from backend.scripts.migrate_longitudinal_and_audit_schema import run_migration as run_longitudinal_migration
    run_longitudinal_migration()
    step_print("STAGE 3: MIGRATIONS", "Longitudinal & audit schema migration completed.")

    step_print("STAGE 3: MIGRATIONS", "Running RBAC & auth schema migration (backend/scripts/migrate_auth_rbac.py)...")
    from backend.scripts.migrate_auth_rbac import run_migration as run_auth_migration
    run_auth_migration()
    step_print("STAGE 3: MIGRATIONS", "RBAC & auth schema migration completed.")

    # -------------------------------------------------------------------------
    # STAGE 4: Data Seed / Initial Migration
    # -------------------------------------------------------------------------
    step_print("STAGE 4: DATA SEED", "Seeding default B.Sc. Nursing curriculum course catalog...")
    from backend.db.init_db import seed_courses, seed_default_users
    seed_courses()
    step_print("STAGE 4: DATA SEED", "Course catalog seeded successfully.")

    step_print("STAGE 4: DATA SEED", "Seeding default institutional RBAC user accounts...")
    seed_default_users()
    step_print("STAGE 4: DATA SEED", "Institutional user accounts verified/seeded.")

    excel_file = os.path.join(BASE_DIR, "VidyaMarksheet_Master_DataSheet.xlsx")
    if os.path.exists(excel_file):
        step_print("STAGE 4: DATA SEED", f"Migrating historical student records from {excel_file}...")
        from backend.scripts.migrate_excel_to_pg import migrate_workbook
        migrate_workbook(file_path=excel_file, batch_name="Batch 2022-2026", start_year=2022, end_year=2026)
        step_print("STAGE 4: DATA SEED", "Workbook ingestion and longitudinal recalculation complete.")
    else:
        step_print("STAGE 4: DATA SEED", f"Notice: Excel master file '{excel_file}' not found. Skipping student ingestion.")

    # -------------------------------------------------------------------------
    # STAGE 5: Health Audit & CLI Diagnostic Summary
    # -------------------------------------------------------------------------
    step_print("STAGE 5: AUDIT", "Performing comprehensive database health audit...")
    with sync_engine.connect() as conn:
        # Count tables
        res_tables = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)).fetchall()
        verified_tables = [r[0] for r in res_tables]

        # Count courses
        course_count = conn.execute(text("SELECT COUNT(*) FROM courses;")).scalar() or 0

        # Count students
        student_count = conn.execute(text("SELECT COUNT(*) FROM students;")).scalar() or 0

        # Count registrations
        reg_count = conn.execute(text("SELECT COUNT(*) FROM student_semester_registrations;")).scalar() or 0

        # Count course marks
        marks_count = conn.execute(text("SELECT COUNT(*) FROM student_course_marks;")).scalar() or 0

        # Count cumulative summaries
        summary_count = conn.execute(text("SELECT COUNT(*) FROM cumulative_academic_summary;")).scalar() or 0

        # Count users
        user_count = conn.execute(text("SELECT COUNT(*) FROM app_users;")).scalar() or 0

    expected_tables = {
        "batches",
        "students",
        "courses",
        "student_semester_registrations",
        "student_course_marks",
        "cumulative_academic_summary",
        "marks_audit_log",
        "template_design_audit_log",
        "app_users",
        "auth_security_audit_log",
    }
    missing_tables = expected_tables - set(verified_tables)
    is_healthy = len(missing_tables) == 0 and course_count > 0

    health_status = "HEALTHY / READY" if is_healthy else f"INCOMPLETE (Missing: {missing_tables})"

    # Print Final CLI Summary Table
    print("\n" + "=" * 80)
    print("                    CLI DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f" {'Metric / Component':<36} | {'Status / Value':<38} ")
    print("-" * 80)
    print(f" {'Connected Environment Profile':<36} | {'Home PC (localhost:5432)':<38} ")
    print(f" {'Target PostgreSQL Database':<36} | {DB_NAME:<38} ")
    print(f" {'Database Creation State':<36} | {db_creation_status:<38} ")
    print(f" {'Total Public Tables Verified':<36} | {len(verified_tables):<38} ")
    for t in sorted(verified_tables):
        print(f"   • {t:<34} | {'[VERIFIED]':<38} ")
    print(f" {'Total Courses Seeded (Sem 1-8)':<36} | {course_count:<38} ")
    print(f" {'Institutional Users Seeded':<36} | {user_count:<38} ")
    print(f" {'Initial Students Ingested':<36} | {student_count:<38} ")
    print(f" {'Semester Registrations':<36} | {reg_count:<38} ")
    print(f" {'Course Marks Recorded':<36} | {marks_count:<38} ")
    print(f" {'Cumulative Summaries Calculated':<36} | {summary_count:<38} ")
    print(f" {'System Health Check':<36} | {health_status:<38} ")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
