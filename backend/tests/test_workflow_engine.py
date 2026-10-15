"""
Test suite for Role-Based Workflow Approval State Machine & Audit History.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_sync_session
from backend.db.repository import ExaminationRepository
from backend.db.models import Student, StudentSemesterRegistration, MarksAuditLog

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_student():
    """Seeds a test student and registration for workflow testing."""
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Workflow Test Batch 2026")
        student = repo.upsert_student(
            batch_id=batch.id,
            roll_no="TEST_WF_01",
            enrollment_no="ENROLL_WF_01",
            student_name="PRIYA SHARMA",
            father_name="RAJESH SHARMA",
            modified_by="TEST_SETUP"
        )
        reg = repo.upsert_registration(
            student_id=student.id,
            semester_number=1,
            exam_month_year="JANUARY - 2026",
            exam_type="MAIN",
            attempt_number=0,
            attempt_label="MAIN",
            total_credits=20.0,
            sgpa_credits=20.0,
            grand_total_obtained=380.0,
            grand_total_max=500.0,
            percentage=76.0,
            credit_score=160.0,
            sgpa=8.0,
            result_status="PASS",
            result_remarks="Grading Performance - PASS",
            modified_by="TEST_SETUP"
        )
        # Ensure it starts in DRAFT
        reg.workflow_status = "DRAFT"
        session.commit()

    yield

    # Teardown test data
    with get_sync_session() as session:
        s = session.query(Student).filter_by(roll_no="TEST_WF_01").first()
        if s:
            session.delete(s)
            session.commit()


def test_initial_draft_status():
    """Verify that student registrations start in DRAFT status."""
    res = client.get("/api/v1/workflow/status/1")
    assert res.status_code == 200
    data = res.json()
    assert "counts" in data
    assert "DRAFT" in data["counts"]
    # Check student is present
    students = data.get("students", [])
    matching = [s for s in students if s["roll_no"] == "TEST_WF_01"]
    assert len(matching) == 1
    assert matching[0]["workflow_status"] == "DRAFT"


def test_scrutiny_committee_transition_to_scrutinized():
    """Scrutiny Committee can transition marks from DRAFT to SCRUTINIZED."""
    payload = {
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "SCRUTINIZED",
        "user_role": "Scrutiny Committee",
        "operator_name": "Dr. Verma",
        "remarks": "Verified IA & EA components"
    }
    res = client.post("/api/v1/workflow/transition", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["target_status"] == "SCRUTINIZED"

    # Verify status changed in DB
    status_res = client.get("/api/v1/workflow/status/1")
    students = status_res.json()["students"]
    matching = [s for s in students if s["roll_no"] == "TEST_WF_01"][0]
    assert matching["workflow_status"] == "SCRUTINIZED"


def test_scrutiny_committee_forbidden_from_approving():
    """Only Admin / Sub-Dean role can transition marks to APPROVED. Scrutiny Committee must be rejected with 403."""
    # First move to SCRUTINIZED
    client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "SCRUTINIZED",
        "user_role": "Scrutiny Committee",
        "operator_name": "Dr. Verma"
    })

    # Attempt to approve with Scrutiny Committee role
    forbidden_payload = {
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "APPROVED",
        "user_role": "Scrutiny Committee",
        "operator_name": "Dr. Verma",
        "remarks": "Attempting approval without Sub-Dean credentials"
    }
    res = client.post("/api/v1/workflow/transition", json=forbidden_payload)
    assert res.status_code == 403
    assert "Admin / Sub-Dean" in res.json()["detail"]


def test_admin_subdean_approval_and_lock():
    """Admin / Sub-Dean can transition to APPROVED and then LOCKED."""
    # 1. Scrutinize
    client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "SCRUTINIZED",
        "user_role": "Scrutiny Committee",
        "operator_name": "Dr. Verma"
    })

    # 2. Approve by Sub-Dean
    approve_res = client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "APPROVED",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations",
        "remarks": "Approved by Examination Board"
    })
    assert approve_res.status_code == 200
    assert approve_res.json()["target_status"] == "APPROVED"

    # 3. Lock by Sub-Dean
    lock_res = client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "LOCKED",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations",
        "remarks": "Published & locked"
    })
    assert lock_res.status_code == 200
    assert lock_res.json()["target_status"] == "LOCKED"

    # Check status
    status_res = client.get("/api/v1/workflow/status/1")
    matching = [s for s in status_res.json()["students"] if s["roll_no"] == "TEST_WF_01"][0]
    assert matching["workflow_status"] == "LOCKED"
    assert matching["is_locked"] is True


def test_locked_record_prevents_transitions_without_unlock():
    """When a record is LOCKED, regular transition attempts are rejected."""
    # Lock the student
    client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "LOCKED",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations"
    })

    # Try moving back to DRAFT without unlock
    res = client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "DRAFT",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations"
    })
    assert res.status_code == 403
    assert "LOCKED" in res.json()["detail"]


def test_unlock_for_reevaluation_requires_justification_and_admin_role():
    """Unlocking for re-evaluation requires Admin role and mandatory justification."""
    # Lock the student
    client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "LOCKED",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations"
    })

    # Non-admin attempt -> 403
    fail_role_res = client.post("/api/v1/workflow/unlock", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "user_role": "Scrutiny Committee",
        "operator_name": "Dr. Verma",
        "justification": "Re-evaluation request"
    })
    assert fail_role_res.status_code == 403

    # Admin attempt with empty justification -> 422 Unprocessable Entity
    empty_just_res = client.post("/api/v1/workflow/unlock", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations",
        "justification": ""
    })
    assert empty_just_res.status_code == 422

    # Proper Admin unlock with justification -> 200
    success_unlock = client.post("/api/v1/workflow/unlock", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations",
        "justification": "Grievance petition #204 re-checking approved by Sub-Dean committee",
        "target_status": "DRAFT"
    })
    assert success_unlock.status_code == 200
    assert success_unlock.json()["new_status"] == "DRAFT"

    # Status in DB should be DRAFT now
    status_res = client.get("/api/v1/workflow/status/1")
    matching = [s for s in status_res.json()["students"] if s["roll_no"] == "TEST_WF_01"][0]
    assert matching["workflow_status"] == "DRAFT"
    assert matching["is_locked"] is False


def test_audit_history_retrieval():
    """Audit history returns chronological list of changes with all required fields."""
    # Execute a workflow transition and unlock to generate audit logs
    client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "SCRUTINIZED",
        "user_role": "Scrutiny Committee",
        "operator_name": "Dr. Rao",
        "remarks": "Committee scrutiny completed"
    })
    client.post("/api/v1/workflow/transition", json={
        "semester_number": 1,
        "roll_no": "TEST_WF_01",
        "target_status": "APPROVED",
        "user_role": "Admin / Sub-Dean",
        "operator_name": "Dean Examinations",
        "remarks": "Sub-Dean Approval"
    })

    res = client.get("/api/v1/workflow/audit-history/TEST_WF_01")
    assert res.status_code == 200
    data = res.json()
    assert data["roll_no"] == "TEST_WF_01"
    assert data["total_records"] >= 2

    # Verify history items contain: Timestamp | User / Operator | Subject / Field | Old Value | New Value | Reason / Justification
    first_entry = data["history"][0]
    assert "timestamp" in first_entry
    assert "modified_by" in first_entry
    assert "field_name" in first_entry
    assert "old_value" in first_entry
    assert "new_value" in first_entry
    assert "change_reason" in first_entry
