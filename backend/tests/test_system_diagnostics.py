"""
Automated Verification Suite for System Diagnostics & Health Suite
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with INC Gazette Corrigendum & SGPGIMS Lucknow Regulations.

Tests:
1. Role Isolation (Operator & Faculty rejected with 403 Forbidden on diagnostic route).
2. Admin Execution (200 OK, all 7 subsystems evaluated non-destructively, live record count unaltered).
3. Fault Injection Simulation (Simulate single subsystem failure, verify overall report status is FAILED while other modules complete).
4. Streaming Diagnostic Event Endpoint (200 OK, text/event-stream content type, JSON event lines).
"""

import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.init_db import init_database, seed_courses
from backend.db.database import SyncSessionLocal
from backend.db.models import Student, StudentSemesterRegistration, StudentCourseMark, AppUser
from backend.security import create_access_token, hash_password
from backend.services.diagnostic_service import DiagnosticService

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_diagnostic_db():
    init_database()
    seed_courses()
    with SyncSessionLocal() as session:
        op = session.query(AppUser).filter_by(username="TestOperator").first()
        if not op:
            op = AppUser(
                username="TestOperator",
                full_name="Test Operator",
                hashed_password=hash_password("Operator@2026#Secure"),
                role="Operator",
                is_active=True,
                must_change_password=False,
                token_version=1,
            )
            session.add(op)
        else:
            op.must_change_password = False
            op.is_active = True

        fac = session.query(AppUser).filter_by(username="TestFaculty").first()
        if not fac:
            fac = AppUser(
                username="TestFaculty",
                full_name="Test Faculty",
                hashed_password=hash_password("Faculty@2026#Secure"),
                role="Faculty",
                is_active=True,
                must_change_password=False,
                token_version=1,
            )
            session.add(fac)
        else:
            fac.must_change_password = False
            fac.is_active = True

        session.commit()


@pytest.fixture
def admin_headers():
    token = create_access_token(data={"sub": "Admin", "role": "Admin", "token_version": 1})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def operator_headers():
    token = create_access_token(data={"sub": "TestOperator", "role": "Operator", "token_version": 1})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty_headers():
    token = create_access_token(data={"sub": "TestFaculty", "role": "Faculty", "token_version": 1})
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. Role-Based Access Control Isolation Test
# -----------------------------------------------------------------------------
def test_diagnostic_route_rbac_isolation(operator_headers, faculty_headers):
    """
    Verifies that only users with role 'Admin' can access the full-system diagnostic suite.
    Operator and Faculty roles must be rejected with 403 Forbidden.
    """
    # 1. Unauthenticated request -> 401
    res_unauth = client.post("/api/v1/admin/run-system-tests")
    assert res_unauth.status_code == 401

    # 2. Operator request -> 403
    res_op = client.post("/api/v1/admin/run-system-tests", headers=operator_headers)
    assert res_op.status_code == 403
    assert "Forbidden" in res_op.json()["detail"]

    # 3. Faculty request -> 403
    res_fac = client.post("/api/v1/admin/run-system-tests", headers=faculty_headers)
    assert res_fac.status_code == 403
    assert "Forbidden" in res_fac.json()["detail"]


# -----------------------------------------------------------------------------
# 2. Admin Diagnostic Execution & Non-Destructive Integrity Test
# -----------------------------------------------------------------------------
def test_admin_diagnostic_execution_and_integrity(admin_headers):
    """
    Verifies that Admin can execute full diagnostics.
    Asserts 200 OK, verified modules, duration metrics, and non-destructive execution
    (live database records count remains identical before and after).
    """
    with SyncSessionLocal() as session:
        initial_student_count = session.query(Student).count()
        initial_reg_count = session.query(StudentSemesterRegistration).count()
        initial_mark_count = session.query(StudentCourseMark).count()

    res = client.post("/api/v1/admin/run-system-tests", headers=admin_headers, json={"verbose": True})
    assert res.status_code == 200
    report = res.json()

    assert report["status"] in ["PASSED", "WARNING"]
    assert report["total_checks"] == 7
    assert report["passed_checks"] >= 6
    assert report["duration_ms"] > 0
    assert "VidyaLabs" in report["branding"]
    assert len(report["modules"]) == 7

    # Verify each subsystem key is present
    subsystem_keys = {m["subsystem_key"] for m in report["modules"]}
    expected_keys = {
        "database_integrity",
        "inc_rules_math",
        "auth_rbac",
        "excel_ingestion",
        "pdf_engine",
        "backlog_reappear",
        "filesystem_storage",
    }
    assert expected_keys.issubset(subsystem_keys)

    # Check log report format
    assert "[INFO]" in report["log_report"]
    assert "[SUCCESS]" in report["log_report"]

    # Verify non-destructive integrity: database counts must not have changed
    with SyncSessionLocal() as session:
        final_student_count = session.query(Student).count()
        final_reg_count = session.query(StudentSemesterRegistration).count()
        final_mark_count = session.query(StudentCourseMark).count()

    assert final_student_count == initial_student_count
    assert final_reg_count == initial_reg_count
    assert final_mark_count == initial_mark_count


# -----------------------------------------------------------------------------
# 3. Fault Injection Simulation Test
# -----------------------------------------------------------------------------
def test_diagnostic_fault_injection_resilience(admin_headers):
    """
    Simulates a failure in one subsystem (e.g. database table missing).
    Verifies that the targeted module reports FAIL with actionable suggested fix,
    the overall verdict is FAILED, and the remaining 6 subsystems continue to execute.
    """
    service = DiagnosticService()

    # Simulate database failure by mocking inspect to return an empty tables list
    with patch("backend.services.diagnostic_service.inspect") as mock_inspect:
        mock_inspector = mock_inspect.return_value
        mock_inspector.get_table_names.return_value = ["only_one_table"]

        report = service.run_all_diagnostics(verbose=True)

        assert report.status == "FAILED"
        assert report.failed_checks >= 1

        db_mod = next(m for m in report.modules if m.subsystem_key == "database_integrity")
        assert db_mod.status == "FAIL"
        assert "Missing core tables" in db_mod.details or "Missing" in str(db_mod.error)
        assert db_mod.suggested_fix is not None

        # Verify other modules still ran and completed
        math_mod = next(m for m in report.modules if m.subsystem_key == "inc_rules_math")
        assert math_mod.status == "PASS"


# -----------------------------------------------------------------------------
# 4. Server-Sent Events (SSE) Streaming Route Test
# -----------------------------------------------------------------------------
def test_diagnostic_sse_streaming_route():
    """
    Verifies GET /api/v1/admin/stream-system-tests returns text/event-stream
    and emits JSON formatted data lines with event types.
    """
    admin_token = create_access_token(data={"sub": "Admin", "role": "Admin", "token_version": 1})
    res = client.get(f"/api/v1/admin/stream-system-tests?token={admin_token}")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("Content-Type", "")

    # Inspect stream content
    lines = res.text.split("\n\n")
    data_lines = [line.replace("data: ", "").strip() for line in lines if line.startswith("data: ")]
    assert len(data_lines) >= 3  # at least start, logs, complete

    # Verify first event is start
    import json
    first_evt = json.loads(data_lines[0])
    assert first_evt.get("type") == "start"

    # Verify last event is complete
    last_evt = json.loads(data_lines[-1])
    assert last_evt.get("type") == "complete"
    assert "report" in last_evt
    assert last_evt["report"]["total_checks"] == 7
