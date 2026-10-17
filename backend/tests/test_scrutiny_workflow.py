"""
Test Suite: Scrutiny Verification Studio & Admin Remediation Workflow
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_sync_session
from backend.db.models import (
    AppUser,
    Student,
    StudentSemesterRegistration,
    StudentCourseMark,
    Course,
    ScrutinyVerification,
    MarksAuditLog,
)
from backend.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_scrutiny_test_env():
    """Configures users (Admin, Scrutiny, Viewer) and locates test registration data."""
    with get_sync_session() as session:
        # 1. Admin User
        admin = session.query(AppUser).filter_by(username="Admin").first()
        if not admin:
            admin = AppUser(
                username="Admin",
                full_name="System Administrator",
                role="Admin",
                hashed_password=hash_password("Admin"),
                is_active=True,
                must_change_password=False,
                token_version=1,
            )
            session.add(admin)
        else:
            admin.must_change_password = False
            admin.is_active = True

        # 2. Scrutiny Officer User
        scrutiny = session.query(AppUser).filter_by(username="TestScrutiny").first()
        if not scrutiny:
            scrutiny = AppUser(
                username="TestScrutiny",
                full_name="Scrutiny Officer Priya",
                role="Scrutiny",
                hashed_password=hash_password("Scrutiny@123"),
                is_active=True,
                must_change_password=False,
                token_version=1,
            )
            session.add(scrutiny)
        else:
            scrutiny.must_change_password = False
            scrutiny.is_active = True

        # 3. Viewer User (unauthorized for scrutiny)
        viewer = session.query(AppUser).filter_by(username="TestViewer").first()
        if not viewer:
            viewer = AppUser(
                username="TestViewer",
                full_name="Guest Viewer",
                role="Viewer",
                hashed_password=hash_password("Viewer@123"),
                is_active=True,
                must_change_password=False,
                token_version=1,
            )
            session.add(viewer)
        else:
            viewer.must_change_password = False
            viewer.is_active = True

        session.commit()

        # Find any existing registration to test against
        reg = session.query(StudentSemesterRegistration).first()
        assert reg is not None, "At least one registration must exist in DB."
        student_id = reg.student_id
        reg_id = reg.id
        semester = reg.semester_number
        session_str = reg.exam_month_year

    admin_token = create_access_token(data={"sub": "Admin", "role": "Admin", "token_version": 1})
    scrutiny_token = create_access_token(data={"sub": "TestScrutiny", "role": "Scrutiny", "token_version": 1})
    viewer_token = create_access_token(data={"sub": "TestViewer", "role": "Viewer", "token_version": 1})

    return {
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "scrutiny_headers": {"Authorization": f"Bearer {scrutiny_token}"},
        "viewer_headers": {"Authorization": f"Bearer {viewer_token}"},
        "registration_id": reg_id,
        "student_id": student_id,
        "semester": semester,
        "session": session_str,
    }


def test_session_context_endpoint(setup_scrutiny_test_env):
    """Verifies GET /api/v1/scrutiny/session-context returns rules, students, and datasheet."""
    headers = setup_scrutiny_test_env["scrutiny_headers"]
    semester = setup_scrutiny_test_env["semester"]

    response = client.get(
        f"/api/v1/scrutiny/session-context?semester={semester}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    assert "inc_rules" in data
    assert data["inc_rules"]["program_total_credits"] == 151.0
    assert "students" in data
    assert "datasheet_rows" in data
    assert len(data["students"]) > 0
    assert "branding" in data


def test_verify_student_workflow_and_iterations(setup_scrutiny_test_env):
    """
    Verifies submitting a verification record:
    1. First iteration: VERIFIED_CORRECT -> status becomes VERIFIED.
    2. Second iteration: NEEDS_CORRECTION -> status becomes FLAGGED, iteration increments.
    """
    headers = setup_scrutiny_test_env["scrutiny_headers"]
    reg_id = setup_scrutiny_test_env["registration_id"]
    stu_id = setup_scrutiny_test_env["student_id"]
    sem = setup_scrutiny_test_env["semester"]

    # Iteration 1: Mark as VERIFIED_CORRECT
    payload_1 = {
        "registration_id": reg_id,
        "student_id": stu_id,
        "semester_number": sem,
        "verification_status": "VERIFIED_CORRECT",
        "comments": "Checked all paper totals against physical register. All marks align.",
        "highlighted_fields": [],
        "suggested_changes": {},
    }
    resp1 = client.post("/api/v1/scrutiny/verify-student", json=payload_1, headers=headers)
    assert resp1.status_code == 200, resp1.text
    d1 = resp1.json()
    assert d1["scrutiny_status"] == "VERIFIED"
    iter_1 = d1["iteration_number"]

    # Iteration 2: Mark as NEEDS_CORRECTION with suggested changes
    payload_2 = {
        "registration_id": reg_id,
        "student_id": stu_id,
        "semester_number": sem,
        "verification_status": "NEEDS_CORRECTION",
        "comments": "Retotaling discrepancy detected in external component.",
        "highlighted_fields": ["ext_marks_row_1"],
        "suggested_changes": {
            "PHAR 205": {
                "field": "external_part_b",
                "current_val": 20,
                "suggested_val": 24,
                "reason": "Section B totaling was entered as 20 instead of 24 on physical answer book."
            }
        },
    }
    resp2 = client.post("/api/v1/scrutiny/verify-student", json=payload_2, headers=headers)
    assert resp2.status_code == 200, resp2.text
    d2 = resp2.json()
    assert d2["scrutiny_status"] == "FLAGGED"
    assert d2["iteration_number"] == iter_1 + 1
    verif_id = d2["verification_id"]
    assert verif_id is not None


def test_pending_remediations_and_admin_apply(setup_scrutiny_test_env):
    """
    Tests:
    1. Querying pending remediations as Admin.
    2. Role-check: Scrutiny user cannot apply remediation (403).
    3. Admin applying remediation -> recalculates totals, logs in audit trail.
    """
    admin_headers = setup_scrutiny_test_env["admin_headers"]
    scrutiny_headers = setup_scrutiny_test_env["scrutiny_headers"]
    reg_id = setup_scrutiny_test_env["registration_id"]
    stu_id = setup_scrutiny_test_env["student_id"]
    sem = setup_scrutiny_test_env["semester"]

    # First find a course code from the student's marks
    course_code = None
    with get_sync_session() as session:
        mark = (
            session.query(StudentCourseMark, Course)
            .join(Course, StudentCourseMark.course_id == Course.id)
            .filter(StudentCourseMark.registration_id == reg_id)
            .first()
        )
        if mark:
            course_code = mark[1].course_code

    if not course_code:
        course_code = "GENERIC"

    # Submit a needs_correction suggestion with the real course code
    payload = {
        "registration_id": reg_id,
        "student_id": stu_id,
        "semester_number": sem,
        "verification_status": "NEEDS_CORRECTION",
        "comments": "Retotaling mismatch in internal assessment.",
        "highlighted_fields": [f"course_{course_code}_internal"],
        "suggested_changes": {
            course_code: {
                "field": "internal",
                "current_val": 15,
                "suggested_val": 18,
                "reason": "Continuous assessment mark entry typo corrected."
            }
        },
    }
    sub_resp = client.post("/api/v1/scrutiny/verify-student", json=payload, headers=scrutiny_headers)
    assert sub_resp.status_code == 200
    v_id = sub_resp.json()["verification_id"]

    # 1. Check pending remediations
    pending_resp = client.get("/api/v1/scrutiny/pending-remediations", headers=admin_headers)
    assert pending_resp.status_code == 200
    remed_list = pending_resp.json()["remediations"]
    matching = [r for r in remed_list if r["verification_id"] == v_id]
    assert len(matching) > 0

    # 2. Scrutiny user cannot apply remediation
    unauth_resp = client.post(f"/api/v1/scrutiny/apply-remediation/{v_id}", headers=scrutiny_headers)
    assert unauth_resp.status_code == 403

    # 3. Admin applies remediation
    apply_resp = client.post(f"/api/v1/scrutiny/apply-remediation/{v_id}", headers=admin_headers)
    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()
    assert apply_data["status"] == "success"
    assert "updated_courses" in apply_data

    # 4. Verify DB updated
    with get_sync_session() as session:
        v_record = session.query(ScrutinyVerification).filter_by(id=v_id).first()
        assert v_record.is_actioned_by_admin is True
        assert v_record.actioned_by_admin_username == "Admin"

        # Check audit log
        audit = (
            session.query(MarksAuditLog)
            .filter_by(entity_type="scrutiny_remediation", entity_id=v_id)
            .order_by(MarksAuditLog.id.desc())
            .first()
        )
        assert audit is not None
        assert f"Scrutiny Suggestion #{v_id}" in audit.change_reason


def test_dismiss_remediation_workflow(setup_scrutiny_test_env):
    """Verifies Admin can dismiss a suggestion without modifying marks."""
    admin_headers = setup_scrutiny_test_env["admin_headers"]
    scrutiny_headers = setup_scrutiny_test_env["scrutiny_headers"]
    reg_id = setup_scrutiny_test_env["registration_id"]
    stu_id = setup_scrutiny_test_env["student_id"]
    sem = setup_scrutiny_test_env["semester"]

    payload = {
        "registration_id": reg_id,
        "student_id": stu_id,
        "semester_number": sem,
        "verification_status": "NEEDS_CORRECTION",
        "comments": "Suggested rechecking moderation mark.",
        "highlighted_fields": [],
        "suggested_changes": {},
    }
    sub_resp = client.post("/api/v1/scrutiny/verify-student", json=payload, headers=scrutiny_headers)
    assert sub_resp.status_code == 200
    v_id = sub_resp.json()["verification_id"]

    dismiss_resp = client.post(
        f"/api/v1/scrutiny/dismiss-remediation/{v_id}",
        json={"admin_notes": "Reviewed with Chief Examiner. Original score stands."},
        headers=admin_headers,
    )
    assert dismiss_resp.status_code == 200
    assert dismiss_resp.json()["status"] == "success"

    with get_sync_session() as session:
        v_record = session.query(ScrutinyVerification).filter_by(id=v_id).first()
        assert v_record.is_actioned_by_admin is True
        assert "Original score stands" in v_record.comments


def test_rbac_restrictions(setup_scrutiny_test_env):
    """Verifies that unauthorized Viewer cannot access scrutiny studio endpoints."""
    viewer_headers = setup_scrutiny_test_env["viewer_headers"]
    sem = setup_scrutiny_test_env["semester"]

    resp = client.get(f"/api/v1/scrutiny/session-context?semester={sem}", headers=viewer_headers)
    assert resp.status_code == 403
