"""
Integration Tests for Quality Audit API Routes (/api/audit/verify and /api/audit/upload-and-audit)
Branding: VidyaMarksheet by VidyaLabs
"""

import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

DATA_SHEET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "VidyaMarksheet_Master_DataSheet.xlsx")


def test_audit_upload_and_audit_route():
    assert os.path.exists(DATA_SHEET_PATH)
    with open(DATA_SHEET_PATH, "rb") as f:
        file_bytes = f.read()

    file_payload = ("VidyaMarksheet_Master_DataSheet.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(
        "/api/audit/upload-and-audit",
        files={"file": file_payload},
        data={"semester": "1"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    audit_report = data["audit_report"]
    assert audit_report["is_valid"] is True
    assert audit_report["can_export_pdf"] is True
    assert audit_report["critical_errors_count"] == 0
    assert audit_report["total_candidates"] == 3

    evaluation = data["evaluation"]
    assert evaluation["total_candidates"] == 3
    assert evaluation["passed_count"] == 2
    assert evaluation["failed_count"] == 1
    assert evaluation["grace_awarded_count"] == 1


def test_audit_verify_route_with_arithmetic_flaw():
    # Submit a payload with broken Part A + Part B != External
    payload = [
        {
            "roll_no": "202501099",
            "enroll_no": "2025700",
            "student_name": "FLAWED CANDIDATE",
            "father_name": "FATHER",
            "courses": {
                "ANAT_PHYS": {
                    "int_marks": 20,
                    "ex_part_a": 20,
                    "ex_part_b": 20,
                    "ex_total": 50,  # 20 + 20 != 50!
                    "grace": 0,
                    "total": 70
                }
            },
            "raw_remarks": "PASS"
        }
    ]

    response = client.post(
        "/api/audit/verify",
        json=payload
    )

    assert response.status_code == 200
    report = response.json()
    assert report["is_valid"] is False
    assert report["can_export_pdf"] is False
    assert report["critical_errors_count"] >= 1
    assert any("Subcomponent Parity" in a["field"] for a in report["anomalies"])
