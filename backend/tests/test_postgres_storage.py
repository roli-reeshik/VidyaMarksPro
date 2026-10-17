"""
Integration Tests for PostgreSQL Examination Persistence Engine (vidya_examination_db).
Tests ACID upserts, audit logging, longitudinal CGPA evaluation, and FastAPI endpoints.
VidyaLabs Copyright © 2026.
"""

import io
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_sync_session
from backend.db.init_db import init_database, seed_courses
from backend.db.models import Batch, Student, StudentSemesterRegistration, Course, MarksAuditLog, StudentCourseMark
from backend.db.repository import ExaminationRepository
from backend.parsers.template_generator import generate_semester_template
from backend.security import create_access_token

client = TestClient(app)
admin_headers = {"Authorization": f"Bearer {create_access_token({'sub': 'Admin', 'role': 'Admin', 'token_version': 1})}"}


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure schema and courses are initialized before tests."""
    init_database()
    seed_courses()


def test_postgres_tables_and_catalog():
    """Verifies that courses catalog across all 8 semesters is loaded in PostgreSQL."""
    with get_sync_session() as session:
        courses = session.query(Course).all()
        assert len(courses) >= 32, "Expected at least 32 prescribed courses across Semesters 1-8"

        # Verify Sem 1 ENGL 101 exclusion and passing percentage
        engl = session.query(Course).filter_by(semester_number=1, course_code="ENGL 101").first()
        assert engl is not None
        assert engl.include_in_sgpa is False
        assert float(engl.min_pass_pct) == 40.0
        assert float(engl.credits) == 2.0


def test_repository_student_upsert_and_audit():
    """Tests student creation, update, and automated audit logging."""
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2025-2029", start_year=2025, end_year=2029)

        # Initial student creation
        student = repo.upsert_student(
            batch_id=batch.id,
            roll_no="TEST_ROLL_999",
            enrollment_no="TEST_ENROLL_999",
            student_name="Original Name",
            father_name="Father Name",
            modified_by="TEST_SUITE",
        )
        session.commit()

        # Update demographic name
        student_updated = repo.upsert_student(
            batch_id=batch.id,
            roll_no="TEST_ROLL_999",
            enrollment_no="TEST_ENROLL_999",
            student_name="Corrected Full Name",
            father_name="Father Name",
            modified_by="ADMIN_CORRECTION",
        )
        session.commit()

        assert student_updated.student_name == "Corrected Full Name"

        # Verify audit trail record exists
        audits = (
            session.query(MarksAuditLog)
            .filter_by(student_roll_no="TEST_ROLL_999", field_name="student_name")
            .all()
        )
        assert len(audits) >= 1
        assert audits[-1].old_value == "Original Name"
        assert audits[-1].new_value == "Corrected Full Name"
        assert audits[-1].modified_by == "ADMIN_CORRECTION"


def test_upload_examination_datasheet_api():
    """Tests POST /api/v1/examination/upload-datasheet with generated Excel template."""
    excel_bytes = generate_semester_template(1)
    file_payload = ("test_sem1.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(
        "/api/v1/examination/upload-datasheet",
        files={"file": file_payload},
        data={
            "semester_number": 1,
            "batch_name": "Batch 2022-2026",
            "exam_month_year": "JANUARY - 2026",
            "exam_type": "MAIN",
        },
        headers=admin_headers,
    )

    assert response.status_code == 200, f"Upload failed: {response.text}"
    data = response.json()
    assert data["success"] is True
    assert data["semester_number"] == 1
    assert data["total_students"] >= 1
    assert data["database"] == "vidya_examination_db"


def test_get_marksheet_endpoint():
    """Tests GET /api/v1/marksheets/{semester}/{roll_no}."""
    # First get a student from DB
    with get_sync_session() as session:
        from sqlalchemy import func
        reg = (
            session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .join(StudentCourseMark, StudentCourseMark.registration_id == StudentSemesterRegistration.id)
            .filter(StudentSemesterRegistration.semester_number == 1)
            .group_by(StudentSemesterRegistration.id, Student.id)
            .having(func.count(StudentCourseMark.id) >= 3)
            .first()
        )
        assert reg is not None, "Expected at least one Sem 1 student with full courses in DB"
        roll_no = reg[1].roll_no

    response = client.get(f"/api/v1/marksheets/1/{roll_no}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["student"]["roll_no"] == roll_no
    assert data["semester_number"] == 1
    assert "courses" in data
    assert len(data["courses"]) >= 3
    assert "sgpa" in data
    assert "result_status" in data


def test_get_batch_marksheets_endpoint():
    """Tests GET /api/v1/marksheets/{semester}/batch/{batch_id}."""
    with get_sync_session() as session:
        batch = session.query(Batch).first()
        assert batch is not None
        batch_id = batch.id

    response = client.get(f"/api/v1/marksheets/1/batch/{batch_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["batch_id"] == batch_id
    assert "marksheets" in data
    assert len(data["marksheets"]) >= 1


def test_get_analytics_endpoint():
    """Tests GET /api/v1/analytics/{semester}/{batch_id}."""
    with get_sync_session() as session:
        batch = session.query(Batch).first()
        batch_id = batch.id

    response = client.get(f"/api/v1/analytics/1/{batch_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["semester_number"] == 1
    assert data["total_students"] >= 1
    assert "pass_percentage" in data
    assert "average_sgpa" in data
    assert "grade_distribution" in data
    assert "subject_performance" in data


def test_batches_and_students_routes():
    """Tests GET /api/v1/batches and GET /api/v1/students."""
    resp_b = client.get("/api/v1/batches", headers=admin_headers)
    assert resp_b.status_code == 200
    assert len(resp_b.json()) >= 1

    resp_s = client.get("/api/v1/students", headers=admin_headers)
    assert resp_s.status_code == 200
    assert len(resp_s.json()) >= 1


def test_audit_trail_endpoint():
    """Tests GET /api/v1/audit-trail/{roll_no}."""
    response = client.get("/api/v1/audit-trail/TEST_ROLL_999")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    assert logs[0]["student_roll_no"] == "TEST_ROLL_999"


def test_reappear_cycle_and_exemption_engine():
    """
    Tests institutional Reappear Examination cycle:
    1. Main attempt: Student fails 1 subject and passes the rest.
    2. Reappear-I attempt: Retakes failed subject and passes.
    3. Exemption engine carries forward passed subjects with is_exempted=True and 'Ex.' marks.
    4. Evaluates result: 'PASS (CLEARED IN REAPPEAR - I)' and updates SGPA/CGPA.
    """
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2022-2026")

        # 1. Register student for Main Attempt (Attempt 0)
        roll = "REAPPEAR_TEST_001"
        student = repo.upsert_student(
            batch_id=batch.id,
            roll_no=roll,
            enrollment_no="ENROLL_REAPPEAR_001",
            student_name="Pooja Sharma",
            father_name="Ram Sharma",
            modified_by="TEST_REAPPEAR"
        )
        session.commit()

        # Main Attempt Registration
        main_reg = repo.upsert_registration(
            student_id=student.id,
            semester_number=1,
            exam_month_year="JANUARY - 2026",
            exam_type="MAIN",
            attempt_number=0,
            attempt_label="MAIN",
            result_status="FAIL in Applied Anatomy & Applied Physiology",
            modified_by="TEST_REAPPEAR"
        )

        courses = repo.get_semester_courses(1)
        anat = next(c for c in courses if "ANAT" in c.course_code)
        engl = next(c for c in courses if "ENGL" in c.course_code)
        soci = next(c for c in courses if "SOCI" in c.course_code)

        # Main Attempt marks: Fail ANAT, pass ENGL and SOCI
        repo.upsert_course_mark(
            registration_id=main_reg.id,
            course_id=anat.id,
            internal_obtained=10.0,
            external_obtained=25.0,
            total_obtained=35.0,
            percentage=35.0,
            letter_grade="F",
            grade_point=0,
            course_result="FAIL",
            is_exempted=False,
            student_roll_no=roll,
            modified_by="TEST_REAPPEAR"
        )
        repo.upsert_course_mark(
            registration_id=main_reg.id,
            course_id=engl.id,
            internal_obtained=18.0,
            external_obtained=18.0,
            total_obtained=36.0,
            percentage=72.0,
            letter_grade="B+",
            grade_point=7,
            course_result="PASS",
            is_exempted=False,
            student_roll_no=roll,
            modified_by="TEST_REAPPEAR"
        )
        repo.upsert_course_mark(
            registration_id=main_reg.id,
            course_id=soci.id,
            internal_obtained=19.0,
            external_obtained=51.0,
            total_obtained=70.0,
            percentage=70.0,
            letter_grade="B+",
            grade_point=7,
            course_result="PASS",
            is_exempted=False,
            student_roll_no=roll,
            modified_by="TEST_REAPPEAR"
        )
        session.commit()

        # 2. Reappear-I Attempt (Attempt 1): Student retakes only ANAT
        reappear_reg = repo.upsert_registration(
            student_id=student.id,
            semester_number=1,
            exam_month_year="JULY - 2026",
            exam_type="REAPPEAR - I",
            attempt_number=1,
            attempt_label="REAPPEAR - I",
            result_status="IN EVALUATION",
            modified_by="TEST_REAPPEAR"
        )

        # In Reappear sheet, only ANAT has newly obtained marks
        repo.upsert_course_mark(
            registration_id=reappear_reg.id,
            course_id=anat.id,
            internal_obtained=16.0,
            external_obtained=42.0,
            total_obtained=58.0,
            percentage=58.0,
            letter_grade="C",
            grade_point=5,
            course_result="PASS",
            is_exempted=False,
            student_roll_no=roll,
            modified_by="TEST_REAPPEAR"
        )
        session.commit()

        # 3. Resolve exemptions for Reappear-I
        resolved = repo.resolve_reappear_exemptions(
            student_id=student.id,
            semester_number=1,
            current_registration_id=reappear_reg.id,
            attempt_label="REAPPEAR - I",
            modified_by="TEST_REAPPEAR"
        )
        session.commit()

        assert resolved is not None
        assert resolved.attempt_label == "REAPPEAR - I"
        assert resolved.attempt_number == 1
        assert "PASS (CLEARED IN REAPPEAR - I)" in resolved.result_status
        assert float(resolved.sgpa) > 0.0

        # 4. Verify marksheet delivery API output
        marksheet = repo.get_student_marksheet_data(1, roll)
        assert marksheet is not None
        assert marksheet["attempt_number"] == 1
        assert marksheet["attempt_label"] == "REAPPEAR - I"
        assert marksheet["attempt_indicator"] == "(REAPPEAR - I)"
        assert marksheet["result_status"] == "PASS (CLEARED IN REAPPEAR - I)"

        course_map = {c["course_code"]: c for c in marksheet["courses"]}
        anat_out = course_map[anat.course_code]
        engl_out = course_map[engl.course_code]
        soci_out = course_map[soci.course_code]

        # Retaken course has actual marks
        assert anat_out["is_exempted"] is False
        assert anat_out["internal_obtained"] == 16.0
        assert anat_out["external_obtained"] == 42.0
        assert anat_out["total_obtained"] == 58.0
        assert anat_out["is_pass"] is True

        # Previously cleared courses render "Ex."
        assert engl_out["is_exempted"] is True
        assert engl_out["internal_obtained"] == "Ex."
        assert engl_out["external_obtained"] == "Ex."
        assert engl_out["total_obtained"] == 36.0
        assert engl_out["letter_grade"] == "B+"
        assert engl_out["grade_point"] == 7
        assert engl_out["is_pass"] is True

        assert soci_out["is_exempted"] is True
        assert soci_out["internal_obtained"] == "Ex."
        assert soci_out["external_obtained"] == "Ex."
        assert soci_out["total_obtained"] == 70.0
        assert soci_out["letter_grade"] == "B+"
        assert soci_out["grade_point"] == 7
        assert soci_out["is_pass"] is True
