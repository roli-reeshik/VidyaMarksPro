"""
Tests for Formal Gazette Tabulation Register (TR) Export Engine (A3/Legal Landscape).
Tests HTML generation, Playwright PDF export, openpyxl Excel export, and API endpoints.
VidyaMarksheet Copyright © VidyaLabs.
"""

import io
import pytest
import openpyxl
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_sync_session
from backend.db.init_db import init_database, seed_courses
from backend.db.models import Batch, Student, StudentSemesterRegistration
from backend.db.repository import ExaminationRepository
from backend.tr_generator import (
    build_tr_data_from_db,
    build_tr_data_from_evaluated_students,
    TabulationRegisterPdfGenerator,
    TabulationRegisterExcelGenerator,
    TabulationRegisterData,
)

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_database()
    seed_courses()


def test_build_tr_data_from_db():
    """Verifies building TabulationRegisterData from PostgreSQL."""
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2022-2026")

        # Ensure at least 2 students exist
        s1 = repo.upsert_student(
            batch_id=batch.id,
            roll_no="TR_TEST_101",
            enrollment_no="EN_TR_101",
            student_name="Ananya Verma",
            father_name="Sanjay Verma",
        )
        s2 = repo.upsert_student(
            batch_id=batch.id,
            roll_no="TR_TEST_102",
            enrollment_no="EN_TR_102",
            student_name="Rahul Singh",
            father_name="Mahesh Singh",
        )
        session.commit()

        courses = repo.get_semester_courses(1)
        for stu in [s1, s2]:
            reg = repo.upsert_registration(
                student_id=stu.id,
                semester_number=1,
                exam_month_year="JANUARY - 2026",
                grand_total_obtained=175.0,
                grand_total_max=250.0,
                percentage=70.0,
                sgpa=7.2,
                result_status="PASS",
            )
            for c in courses:
                repo.upsert_course_mark(
                    registration_id=reg.id,
                    course_id=c.id,
                    internal_obtained=18.0,
                    external_obtained=52.0,
                    total_obtained=70.0,
                    percentage=70.0,
                    letter_grade="B+",
                    grade_point=7,
                    course_result="PASS",
                )
        session.commit()

        tr_data = build_tr_data_from_db(session, semester_number=1, batch_id=batch.id, page_size=10)
        assert tr_data.semester_number == 1
        assert len(tr_data.courses) >= 3
        assert tr_data.total_appeared >= 2
        assert tr_data.total_passed >= 2
        assert tr_data.pass_percentage > 0.0
        assert len(tr_data.pages) >= 1
        assert len(tr_data.pages[0].students) >= 2


def test_render_tr_html():
    """Verifies Jinja2 HTML rendering of A3 landscape Tabulation Register."""
    with get_sync_session() as session:
        tr_data = build_tr_data_from_db(session, semester_number=1, page_size=10)
        pdf_gen = TabulationRegisterPdfGenerator()
        html = pdf_gen.render_html(tr_data)

        # Check required institutional branding and statutory components
        assert "SANJAY GANDHI POSTGRADUATE INSTITUTE OF MEDICAL SCIENCES, LUCKNOW" in html
        assert "COLLEGE OF NURSING" in html
        assert "TABULATION REGISTER FOR B.Sc. NURSING" in html
        assert "Tabulated By" in html
        assert "Verified By" in html
        assert "Assistant Registrar" in html
        assert "Controller of Examinations / Sub-Dean" in html
        assert "size: A3 landscape" in html
        assert "VidyaMarksheet" in html


def test_generate_tr_excel():
    """Verifies openpyxl Excel (.xlsx) export formatting and structure."""
    with get_sync_session() as session:
        tr_data = build_tr_data_from_db(session, semester_number=1, page_size=15)
        excel_gen = TabulationRegisterExcelGenerator()
        excel_bytes = excel_gen.generate_excel(tr_data)

        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 2000

        # Load generated workbook with openpyxl and verify cells
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
        assert "TR_Sem_1" in wb.sheetnames
        ws = wb["TR_Sem_1"]

        # Check headers
        assert ws["A1"].value == "SANJAY GANDHI POSTGRADUATE INSTITUTE OF MEDICAL SCIENCES, LUCKNOW"
        assert ws["A2"].value == "COLLEGE OF NURSING"
        assert "TABULATION REGISTER" in str(ws["A3"].value)
        assert ws["B6"].value == "Roll No"
        assert ws["D6"].value == "Candidate Name"


def test_api_endpoints_tabulation_register():
    """Tests FastAPI Tabulation Register endpoints."""
    # 1. GET /data
    resp_data = client.get("/api/v1/tabulation-register/data?semester=1")
    assert resp_data.status_code == 200
    json_data = resp_data.json()
    assert json_data["semester_number"] == 1
    assert "courses" in json_data
    assert "pages" in json_data

    # 2. GET /preview-html
    resp_html = client.get("/api/v1/tabulation-register/preview-html?semester=1")
    assert resp_html.status_code == 200
    assert "text/html" in resp_html.headers["content-type"]
    assert "TABULATION REGISTER" in resp_html.text

    # 3. GET /excel
    resp_excel = client.get("/api/v1/tabulation-register/excel?semester=1")
    assert resp_excel.status_code == 200
    assert "openxmlformats" in resp_excel.headers["content-type"]
    assert len(resp_excel.content) > 1000

    # 4. POST /export-excel from payload
    sample_students = [
        {
            "roll_no": "PAYLOAD_001",
            "enroll_no": "EN_PAYLOAD_001",
            "student_name": "Test Student A",
            "father_name": "Test Father A",
            "result_status": "PASS",
            "total_marks_obtained": 180.0,
            "total_marks_max": 250.0,
            "overall_percentage": 72.0,
            "sgpa": 7.4,
            "courses": {
                "ENGL 101": {
                    "course_code": "ENGL 101",
                    "internal_marks": 20,
                    "effective_external": 20,
                    "total_marks": 40,
                    "letter_grade": "A",
                    "grade_point": 8,
                    "is_pass": True,
                }
            }
        }
    ]
    resp_post_excel = client.post(
        "/api/v1/tabulation-register/export-excel",
        json={
            "students": sample_students,
            "semester_number": 1,
            "batch_name": "Batch 2025-2029",
            "session_month_year": "JANUARY - 2026",
            "page_size": 15
        }
    )
    assert resp_post_excel.status_code == 200
    assert len(resp_post_excel.content) > 1000

    # 5. GET /pdf
    resp_pdf = client.get("/api/v1/tabulation-register/pdf?semester=1")
    assert resp_pdf.status_code == 200
    assert "application/pdf" in resp_pdf.headers["content-type"]
    assert len(resp_pdf.content) > 5000

    # 6. POST /data-from-payload with multiple candidates verifying pagination
    multi_students = [
        {
            "roll_no": f"PAYLOAD_PAGINATE_{i:03d}",
            "enroll_no": f"EN_PAGINATE_{i:03d}",
            "student_name": f"Student {i}",
            "father_name": f"Father {i}",
            "result_status": "PASS",
            "total_marks_obtained": 180.0,
            "total_marks_max": 250.0,
            "overall_percentage": 72.0,
            "sgpa": 7.4,
            "courses": {
                "ENGL 101": {
                    "course_code": "ENGL 101",
                    "internal_marks": 20,
                    "effective_external": 20,
                    "total_marks": 40,
                    "letter_grade": "A",
                    "grade_point": 8,
                    "is_pass": True,
                }
            }
        }
        for i in range(1, 26)  # 25 students
    ]
    resp_dfp = client.post(
        "/api/v1/tabulation-register/data-from-payload",
        json={
            "students": multi_students,
            "semester_number": 1,
            "batch_name": "Batch 2025-2029",
            "session_month_year": "JANUARY - 2026",
            "page_size": 10,
        }
    )
    assert resp_dfp.status_code == 200
    dfp_json = resp_dfp.json()
    assert dfp_json["total_appeared"] == 25
    assert len(dfp_json["pages"]) == 3  # 10 + 10 + 5
    assert len(dfp_json["pages"][0]["students"]) == 10
    assert len(dfp_json["pages"][1]["students"]) == 10
    assert len(dfp_json["pages"][2]["students"]) == 5

    # 7. POST /sync-to-db to persist students to PostgreSQL
    resp_sync = client.post(
        "/api/v1/tabulation-register/sync-to-db",
        json={
            "students": multi_students,
            "semester_number": 1,
            "batch_name": "Batch 2025-2029",
            "session_month_year": "JANUARY - 2026",
            "page_size": 10,
        }
    )
    assert resp_sync.status_code == 200
    sync_json = resp_sync.json()
    assert sync_json["status"] == "success"
    assert sync_json["synced_count"] == 25

