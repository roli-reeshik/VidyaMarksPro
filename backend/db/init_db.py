"""
Database initialization and course catalog seeder for vidya_examination_db.
Executes pure SQL DDL or SQLAlchemy metadata.create_all, and seeds all 8 semesters of courses.
VidyaLabs Copyright © 2026.
"""

from decimal import Decimal
from sqlalchemy import text
from backend.db.database import sync_engine, get_sync_session, Base
from backend.db.models import Course, Batch


SEEDED_COURSES = [
    # Semester 1
    {
        "semester_number": 1,
        "course_code": "ENGL 101",
        "course_title": "Communicative English",
        "credits": Decimal("2.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": False,  # Excluded from SGPA per INC
        "min_pass_pct": Decimal("40.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
    {
        "semester_number": 1,
        "course_code": "ANAT 105 & PHYS 110",
        "course_title": "Applied Anatomy & Applied Physiology",
        "credits": Decimal("6.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 1,
        "course_code": "SOCI 115 & PSYC 120",
        "course_title": "Applied Sociology & Applied Psychology",
        "credits": Decimal("6.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    # Semester 2
    {
        "semester_number": 2,
        "course_code": "BIOC 135 & NUTR 140",
        "course_title": "Applied Biochemistry & Applied Nutrition & Dietetics",
        "credits": Decimal("5.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 2,
        "course_code": "N-NF (I & II) 125 (T)",
        "course_title": "Nursing Foundation I & II (Theory)",
        "credits": Decimal("12.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 2,
        "course_code": "N-NF (I & II) 125 (P)",
        "course_title": "Nursing Foundation I & II (Practical)",
        "credits": Decimal("11.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 2,
        "course_code": "HNIT 145",
        "course_title": "Health/Nursing Informatics & Technology",
        "credits": Decimal("3.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
    # Semester 3
    {
        "semester_number": 3,
        "course_code": "MICR 201",
        "course_title": "Applied Microbiology and Infection Control including Safety",
        "credits": Decimal("3.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 3,
        "course_code": "N-AHN (I) 215 (T)",
        "course_title": "Adult Health Nursing I with Integrated Pathophysiology (Theory)",
        "credits": Decimal("7.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 3,
        "course_code": "N-AHN (I) 215 (P)",
        "course_title": "Adult Health Nursing I (Practical)",
        "credits": Decimal("7.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    # Semester 4
    {
        "semester_number": 4,
        "course_code": "PHAR (I & II)-205 & PATH (I & II)-210",
        "course_title": "Pharmacology (I & II) & Pathology (I & II) (including Genetics)",
        "credits": Decimal("6.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 4,
        "course_code": "N-AHN (II) 225 (T)",
        "course_title": "Adult Health Nursing II with Integrated Pathophysiology (Theory)",
        "credits": Decimal("7.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 4,
        "course_code": "N-AHN (II) 225 (P)",
        "course_title": "Adult Health Nursing II (Practical)",
        "credits": Decimal("7.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 4,
        "course_code": "PROF 230",
        "course_title": "Professionalism, Professional Values & Ethics including Bioethics",
        "credits": Decimal("1.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
    {
        "semester_number": 4,
        "course_code": "Elective-1",
        "course_title": "Elective Module (Soft Skills)",
        "credits": Decimal("1.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": False,  # Excluded from SGPA
        "min_pass_pct": Decimal("40.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
    # Semester 5
    {
        "semester_number": 5,
        "course_code": "N-COMH (I) 310 (T)",
        "course_title": "Community Health Nursing I (Theory)",
        "credits": Decimal("5.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 5,
        "course_code": "N-COMH (I) 310 (P)",
        "course_title": "Community Health Nursing I (Practical)",
        "credits": Decimal("2.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 5,
        "course_code": "EDUC 315",
        "course_title": "Educational Technology / Nursing Education",
        "credits": Decimal("3.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 5,
        "course_code": "N-FORN 320",
        "course_title": "Introduction to Forensic Nursing",
        "credits": Decimal("1.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
    # Semester 6
    {
        "semester_number": 6,
        "course_code": "N-CHN (I & II) 301 (T)",
        "course_title": "Child Health Nursing (I & II) (Theory)",
        "credits": Decimal("5.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 6,
        "course_code": "N-CHN (I & II) 301 (P)",
        "course_title": "Child Health Nursing (I & II) (Practical)",
        "credits": Decimal("4.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 6,
        "course_code": "N-MHN (I & II) 305 (T)",
        "course_title": "Mental Health Nursing (I & II) (Theory)",
        "credits": Decimal("5.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 6,
        "course_code": "N-MHN (I & II) 305 (P)",
        "course_title": "Mental Health Nursing (I & II) (Practical)",
        "credits": Decimal("3.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 6,
        "course_code": "NMLE 330",
        "course_title": "Nursing Management & Leadership",
        "credits": Decimal("4.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 6,
        "course_code": "Elective-2",
        "course_title": "Accreditation and Practice Standards (Elective)",
        "credits": Decimal("1.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": False,  # Excluded from SGPA
        "min_pass_pct": Decimal("40.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
    # Semester 7
    {
        "semester_number": 7,
        "course_code": "N-COMH (II) 401 (T)",
        "course_title": "Community Health Nursing II (Theory)",
        "credits": Decimal("5.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 7,
        "course_code": "N-COMH (II) 401 (P)",
        "course_title": "Community Health Nursing II (Practical)",
        "credits": Decimal("2.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 7,
        "course_code": "NRST 405",
        "course_title": "Nursing Research & Statistics",
        "credits": Decimal("4.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 7,
        "course_code": "N-MIDW/OBGN (I & II) 335 & 410 (T)",
        "course_title": "Midwifery/Obstetrics and Gynaecology (OBG) Nursing I & II (Theory)",
        "credits": Decimal("8.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("75.00"),
        "max_total": Decimal("100.00"),
    },
    {
        "semester_number": 7,
        "course_code": "N-MIDW/OBGN (I & II) 335 & 410 (P)",
        "course_title": "Midwifery/Obstetrics and Gynaecology (OBG) Nursing I & II (Practical)",
        "credits": Decimal("7.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("50.00"),
        "max_external": Decimal("50.00"),
        "max_total": Decimal("100.00"),
    },
    # Semester 8
    {
        "semester_number": 8,
        "course_code": "INTE 415, 420, 425, 430 & 435",
        "course_title": "Competency Assessment (Internship / Intensive Clinical Practicum)",
        "credits": Decimal("12.0"),
        "is_theory": False,
        "is_practical": True,
        "is_college_exam": False,
        "include_in_sgpa": True,
        "min_pass_pct": Decimal("50.00"),
        "max_internal": Decimal("100.00"),
        "max_external": Decimal("100.00"),
        "max_total": Decimal("200.00"),
    },
    {
        "semester_number": 8,
        "course_code": "Elective-3",
        "course_title": "Scientific Writing Skills (Elective)",
        "credits": Decimal("1.0"),
        "is_theory": True,
        "is_practical": False,
        "is_college_exam": True,
        "include_in_sgpa": False,  # Excluded from SGPA
        "min_pass_pct": Decimal("40.00"),
        "max_internal": Decimal("25.00"),
        "max_external": Decimal("25.00"),
        "max_total": Decimal("50.00"),
    },
]


def init_database():
    """Initializes schema and tables in PostgreSQL database."""
    print("Initializing PostgreSQL tables using SQLAlchemy metadata...")
    Base.metadata.create_all(bind=sync_engine)
    with sync_engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE student_semester_registrations 
            ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(30) DEFAULT 'DRAFT',
            ADD COLUMN IF NOT EXISTS workflow_updated_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS workflow_updated_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS workflow_remarks TEXT,
            ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(20) DEFAULT 'PROVISIONAL',
            ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS delivered_by VARCHAR(100);

            ALTER TABLE student_course_marks
            ADD COLUMN IF NOT EXISTS external_part_c NUMERIC(5, 2);

            ALTER TABLE cumulative_academic_summary
            ADD COLUMN IF NOT EXISTS sem1_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem1_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem1_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem2_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem2_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem2_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem3_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem3_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem3_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem4_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem4_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem4_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem5_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem5_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem5_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem6_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem6_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem6_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem7_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem7_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem7_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS sem8_credits NUMERIC(4, 1),
            ADD COLUMN IF NOT EXISTS sem8_sgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS sem8_pct NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS cumulative_earned_credits NUMERIC(5, 1) DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS total_credits NUMERIC(5, 1) DEFAULT 151.0,
            ADD COLUMN IF NOT EXISTS total_prescribed_credits NUMERIC(5, 1) DEFAULT 151.0,
            ADD COLUMN IF NOT EXISTS cgpa NUMERIC(4, 2),
            ADD COLUMN IF NOT EXISTS overall_percentage NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS final_percentage NUMERIC(5, 2),
            ADD COLUMN IF NOT EXISTS overall_grade VARCHAR(10),
            ADD COLUMN IF NOT EXISTS final_letter_grade VARCHAR(10),
            ADD COLUMN IF NOT EXISTS grading_performance VARCHAR(50),
            ADD COLUMN IF NOT EXISTS division_classification VARCHAR(50),
            ADD COLUMN IF NOT EXISTS final_result VARCHAR(20),
            ADD COLUMN IF NOT EXISTS overall_result VARCHAR(30);

            CREATE TABLE IF NOT EXISTS app_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(150) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(30) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                must_change_password BOOLEAN DEFAULT TRUE,
                failed_login_attempts INT DEFAULT 0,
                locked_until TIMESTAMP WITH TIME ZONE,
                token_version INT DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login_at TIMESTAMP WITH TIME ZONE
            );

            CREATE TABLE IF NOT EXISTS auth_security_audit_log (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                action VARCHAR(50) NOT NULL,
                ip_address VARCHAR(50),
                user_agent TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS app_feedback (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES app_users(id) ON DELETE SET NULL,
                username VARCHAR(50) NOT NULL,
                user_role VARCHAR(30) NOT NULL,
                category VARCHAR(50) NOT NULL,
                subject VARCHAR(200) NOT NULL,
                feedback_text TEXT NOT NULL,
                rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
                status VARCHAR(20) DEFAULT 'NEW',
                admin_notes TEXT,
                submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                resolved_at TIMESTAMP WITH TIME ZONE
            );

            CREATE TABLE IF NOT EXISTS scrutiny_verifications (
                id SERIAL PRIMARY KEY,
                registration_id INT REFERENCES student_semester_registrations(id) ON DELETE CASCADE,
                student_id INT REFERENCES students(id) ON DELETE CASCADE,
                semester_number INT NOT NULL,
                scrutiny_user_id INT REFERENCES app_users(id) ON DELETE SET NULL,
                scrutiny_username VARCHAR(50) NOT NULL,
                verification_status VARCHAR(30) NOT NULL,
                comments TEXT,
                highlighted_fields JSONB DEFAULT '[]'::jsonb,
                suggested_changes JSONB DEFAULT '{}'::jsonb,
                iteration_number INT DEFAULT 1,
                verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_actioned_by_admin BOOLEAN DEFAULT FALSE,
                actioned_by_admin_username VARCHAR(50),
                actioned_at TIMESTAMP WITH TIME ZONE
            );

            ALTER TABLE student_semester_registrations ADD COLUMN IF NOT EXISTS scrutiny_status VARCHAR(30) DEFAULT 'PENDING';
            ALTER TABLE student_semester_registrations ADD COLUMN IF NOT EXISTS last_scrutinized_at TIMESTAMP WITH TIME ZONE;
            ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email VARCHAR(100);
            ALTER TABLE app_users ADD COLUMN IF NOT EXISTS created_by VARCHAR(50) DEFAULT 'Admin';

            CREATE INDEX IF NOT EXISTS idx_users_username ON app_users(username);
            CREATE INDEX IF NOT EXISTS idx_auth_audit_user ON auth_security_audit_log(username);
            CREATE INDEX IF NOT EXISTS idx_auth_audit_time ON auth_security_audit_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_feedback_status_cat ON app_feedback(status, category);
            CREATE INDEX IF NOT EXISTS idx_feedback_user ON app_feedback(username);
            CREATE INDEX IF NOT EXISTS idx_scrutiny_reg_iter ON scrutiny_verifications(registration_id, iteration_number);
            CREATE INDEX IF NOT EXISTS idx_scrutiny_actioned ON scrutiny_verifications(is_actioned_by_admin);
        """))
        conn.commit()
    print("Database tables initialized successfully.")
    seed_default_users()


DEFAULT_USERS = [
    {"username": "Admin", "password": "Admin", "role": "Admin", "full_name": "System Administrator"},
]


def seed_default_users():
    """Seeds default institutional RBAC accounts if app_users is empty."""
    from backend.db.models import AppUser
    from backend.security import hash_password
    with get_sync_session() as session:
        user_count = session.query(AppUser).count()
        if user_count == 0:
            print("Seeding default institutional RBAC user accounts...")
            for u in DEFAULT_USERS:
                new_user = AppUser(
                    username=u["username"],
                    full_name=u["full_name"],
                    role=u["role"],
                    hashed_password=hash_password(u["password"]),
                    is_active=True,
                    must_change_password=False,
                    failed_login_attempts=0,
                    locked_until=None,
                    token_version=1,
                )
                session.add(new_user)
            session.commit()
            print(f"Successfully seeded {len(DEFAULT_USERS)} default institutional accounts.")
        else:
            print(f"app_users already populated ({user_count} accounts found). Skipping user seeding.")


def seed_courses():
    """Seeds or updates courses across Semesters 1 through 8 in PostgreSQL."""
    with get_sync_session() as session:
        # Default batch
        default_batch = session.query(Batch).filter_by(batch_name="Batch 2022-2026").first()
        if not default_batch:
            default_batch = Batch(
                batch_name="Batch 2022-2026",
                start_year=2022,
                end_year=2026,
                total_prescribed_credits=151,
            )
            session.add(default_batch)
            print("Created default batch: Batch 2022-2026")

        print("Seeding course master catalog across Semesters 1-8...")
        count_added = 0
        count_updated = 0
        for cdata in SEEDED_COURSES:
            existing = (
                session.query(Course)
                .filter_by(
                    semester_number=cdata["semester_number"],
                    course_code=cdata["course_code"],
                )
                .first()
            )
            if existing:
                for k, v in cdata.items():
                    setattr(existing, k, v)
                count_updated += 1
            else:
                new_course = Course(**cdata)
                session.add(new_course)
                count_added += 1

        session.commit()
        print(f"Courses seeded successfully: {count_added} added, {count_updated} updated.")


if __name__ == "__main__":
    init_database()
    seed_courses()

