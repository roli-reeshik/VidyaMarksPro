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
        """))
        conn.commit()
    print("Database tables initialized successfully.")


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
