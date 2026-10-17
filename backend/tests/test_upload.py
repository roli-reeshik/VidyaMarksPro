"""
Integration Tests for Excel Parser & /api/upload
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.parsers.template_generator import generate_semester_template
from backend.parsers.excel_parser import ExcelSheetParser
from backend.security import create_access_token

client = TestClient(app)
admin_headers = {"Authorization": f"Bearer {create_access_token({'sub': 'Admin', 'role': 'Admin', 'token_version': 1})}"}


def test_metadata_endpoint():
    resp = client.get("/api/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert data["application_name"] == "VidyaMarksheet"
    assert "SGPGIMS" in data["institution_name"]
    assert data["branding"]["developed_by"] == "VidyaLabs"
    assert "Priyanka Kumari" in data["branding"]["contact_person"]
    assert data["branding"]["contact_mobile"] == "+91-9140189586"


def test_grading_scale_endpoint():
    resp = client.get("/api/grading-scale")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["scale"]) == 9
    assert data["scale"][0]["letter_grade"] == "O"
    assert data["scale"][0]["grade_point"] == 10


def test_semester_schemas_endpoint():
    resp = client.get("/api/schemas")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["semesters"]) == 8
    # Semester 1 checks
    sem1 = data["semesters"]["1"]
    assert sem1["semester_number"] == 1
    assert sem1["total_prescribed_credits"] == 14
    assert sem1["sgpa_eligible_credits"] == 12
    assert len(sem1["courses"]) == 3


def test_template_generation_and_parsing():
    # 1. Generate template for Semester 1
    excel_bytes = generate_semester_template(1)
    assert len(excel_bytes) > 0

    # 2. Parse generated template directly
    parser = ExcelSheetParser(file_content=excel_bytes, filename="sample_sem1.xlsx")
    result = parser.parse()

    assert result.success is True
    assert result.semester == 1
    assert result.total_students == 5

    # Check student 1 (ADNAN RAFIQ KUMAR)
    s1 = result.results[0]
    assert s1.student.name == "ADNAN RAFIQ KUMAR"
    assert s1.student.roll_no == "202501003"
    assert s1.student.enrollment_no == "2025631"
    assert s1.result_status == "PASS"
    assert len(s1.courses) == 3

    courses_by_code = {c.course_code: c for c in s1.courses}

    # Course (ANAT & PHYS): Total 73 -> B+ (7)
    anat = courses_by_code["ANAT 105 & PHYS 110"]
    assert anat.letter_grade == "B+"
    assert anat.grade_point == 7
    assert anat.is_pass is True

    # Course (SOCI & PSYC): Total 79 -> A (8)
    soci = courses_by_code["SOCI 115 & PSYC 120"]
    assert soci.letter_grade == "A"
    assert soci.grade_point == 8
    assert soci.is_pass is True

    # Course (ENGL 101): Total 44/50 (88%) -> O (10), not in SGPA
    engl = courses_by_code["ENGL 101"]
    assert engl.letter_grade == "O"
    assert engl.grade_point == 10
    assert engl.include_in_sgpa is False

    # SGPA = ((6*7) + (6*8)) / 12 = 90 / 12 = 7.5
    assert s1.sgpa == 7.5

    # Student 3 (AMAN CHAUDHARY with Grace marks)
    s3 = result.results[2]
    assert "GRACE" in s3.result_status

    # Student 5 (VANSH KUMAR - Failed student)
    s5 = result.results[4]
    assert s5.result_status == "FAIL"
    assert len(s5.failed_courses) > 0


def test_api_upload_endpoint():
    excel_bytes = generate_semester_template(1)
    file_payload = ("test_sem1.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(
        "/api/upload",
        files={"file": file_payload},
        data={"semester": "1"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["semester"] == 1
    assert data["total_students"] == 5
    assert data["passed_students"] == 4
    assert data["failed_students"] == 1
