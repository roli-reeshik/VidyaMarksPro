"""
Tests for Examination Cell Ingestion Route (/api/exam-cell/ingest and /api/exam-cell/batch)
Branding: VidyaMarksheet by VidyaLabs
"""

import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

DATA_SHEET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "VidyaMarksheet_Master_DataSheet.xlsx")


def test_exam_cell_ingest_route():
    assert os.path.exists(DATA_SHEET_PATH), f"File {DATA_SHEET_PATH} does not exist"

    with open(DATA_SHEET_PATH, "rb") as f:
        file_bytes = f.read()

    file_payload = ("VidyaMarksheet_Master_DataSheet.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(
        "/api/exam-cell/ingest",
        files={"file": file_payload}
    )

    assert response.status_code == 200
    records = response.json()
    assert isinstance(records, list)
    assert len(records) > 0

    # Find candidate (ADITYA KUMAR KATHERIYA) with grace formula
    s1 = next(r for r in records if r["roll_no"] == "202501002")
    assert s1["roll_no"] == "202501002"
    assert s1["enroll_no"] == "2025630"
    assert s1["student_name"] == "ADITYA KUMAR KATHERIYA"
    assert s1["father_name"] == "VIJAY KUMAR"

    # Courses structure
    courses = s1["courses"]
    assert "ANAT_PHYS" in courses
    assert "SOCI_PSYC" in courses
    assert "ENGL" in courses

    # ANAT_PHYS
    anat = courses["ANAT_PHYS"]
    assert anat["int_marks"] == 20
    assert anat["ex_part_a"] == 19
    assert anat["ex_part_b"] == 20
    assert anat["ex_total"] == 39
    assert anat["grace"] == 0
    assert anat["total"] == 59

    # SOCI_PSYC (with 2.5 grace marks)
    soci = courses["SOCI_PSYC"]
    assert soci["int_marks"] == 20
    assert soci["ex_part_a"] == 20
    assert soci["ex_part_b"] == 15
    assert soci["ex_total"] == 35
    assert soci["grace"] == 2.5
    assert soci["total"] == 57.5

    # ENGL
    engl = courses["ENGL"]
    assert engl["int_marks"] == 21
    assert engl["ex_marks"] == 23
    assert engl["total"] == 44

    # Remarks
    assert "PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY" in s1["raw_remarks"]


def test_exam_cell_batch_route():
    with open(DATA_SHEET_PATH, "rb") as f:
        file_bytes = f.read()

    file_payload = ("VidyaMarksheet_Master_DataSheet.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(
        "/api/exam-cell/batch",
        files={"file": file_payload}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["branding"] == "VidyaMarksheet by VidyaLabs"
    assert data["total_records"] == 3
    assert len(data["records"]) == 3
