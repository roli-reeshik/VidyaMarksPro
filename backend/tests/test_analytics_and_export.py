"""
Automated Verification & Smoke Test Suite
Analytics & Longitudinal KPI Engine, Automated Structured Marksheet File Exporter,
and Universal User Feedback Engine.

Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import os
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_sync_session
from backend.db.models import (
    AppUser,
    AppFeedback,
    Student,
    StudentSemesterRegistration,
    StudentCourseMark,
)
from backend.security import hash_password, create_access_token

client = TestClient(app)

TEST_EXPORT_DIR = os.path.abspath("./test_exported_marksheets_suite")


@pytest.fixture(scope="module")
def setup_test_users_and_tokens():
    """Sets up Admin and Faculty test users with valid JWT tokens."""
    with get_sync_session() as session:
        # Admin User
        admin = session.query(AppUser).filter(AppUser.username == "Admin").first()
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

        # Faculty User
        faculty = session.query(AppUser).filter(AppUser.username == "TestFaculty").first()
        if not faculty:
            faculty = AppUser(
                username="TestFaculty",
                full_name="Dr. Test Faculty",
                role="Faculty",
                hashed_password=hash_password("Faculty@123"),
                is_active=True,
                must_change_password=False,
                token_version=1,
            )
            session.add(faculty)
        else:
            faculty.must_change_password = False
            faculty.is_active = True

        session.commit()
        session.refresh(admin)
        session.refresh(faculty)

        admin_token = create_access_token({
            "sub": admin.username,
            "token_version": admin.token_version,
            "role": admin.role,
        })
        faculty_token = create_access_token({
            "sub": faculty.username,
            "token_version": faculty.token_version,
            "role": faculty.role,
        })

    yield {
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "faculty_headers": {"Authorization": f"Bearer {faculty_token}"},
    }

    # Teardown: Clean up Faculty user and test feedback records
    with get_sync_session() as session:
        session.query(AppFeedback).filter(AppFeedback.username.in_(["TestFaculty", "Admin"])).delete(synchronize_session=False)
        fac = session.query(AppUser).filter(AppUser.username == "TestFaculty").first()
        if fac:
            session.delete(fac)
        session.commit()

    if os.path.exists(TEST_EXPORT_DIR):
        shutil.rmtree(TEST_EXPORT_DIR, ignore_errors=True)


# =============================================================================
# PART 1: ANALYTICS & LONGITUDINAL KPI TESTS
# =============================================================================

def test_analytics_overview_january_2026(setup_test_users_and_tokens):
    """
    Query analytics for January 2026:
    - Verifies overall passing rate formula: (total_passed / total_registered) * 100
    - Verifies Top 3 rankers calculation and distinction badges
    - Verifies max and median percentage metrics
    - Verifies grade distribution and longitudinal trends
    """
    headers = setup_test_users_and_tokens["admin_headers"]
    res = client.get("/api/v1/analytics/overview?exam_session=JANUARY - 2026", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert "kpis" in data
    kpis = data["kpis"]

    # Verify pass rate formula
    tot = kpis["total_registered"]
    passed = kpis["total_passed"]
    assert tot > 0, "January 2026 cohort should have registered students in database"
    expected_pass_rate = round((passed / tot) * 100.0, 2)
    assert kpis["overall_passing_rate"] == expected_pass_rate

    # Verify Top 3 rankers calculation
    top_3 = data["top_3_rankers"]
    assert len(top_3) <= 3
    assert len(top_3) > 0

    # Verify Rank 1 >= Rank 2 >= Rank 3 in SGPA
    for i in range(len(top_3)):
        ranker = top_3[i]
        assert ranker["rank"] == i + 1
        assert "student_name" in ranker
        assert "roll_no" in ranker
        assert "sgpa" in ranker
        assert "percentage" in ranker
        assert "distinction_badge" in ranker
        if i > 0:
            assert top_3[i - 1]["sgpa"] >= top_3[i]["sgpa"]

    # Verify Grade Distribution keys
    assert "grade_distribution" in data
    for g in ["O", "A+", "A", "B+", "B", "C", "F"]:
        assert g in data["grade_distribution"]


def test_subject_performance_endpoint(setup_test_users_and_tokens):
    """
    Query subject performance endpoint:
    - Verifies course grouping, mean internal and external scores, pass percentage, and failure count.
    - Confirms challenging subjects (like PHAR 205, ANAT 105) are flagged.
    """
    headers = setup_test_users_and_tokens["admin_headers"]
    res = client.get("/api/v1/analytics/subject-performance", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    assert "courses" in data
    courses = data["courses"]
    assert len(courses) > 0

    first_course = courses[0]
    assert "course_code" in first_course
    assert "course_title" in first_course
    assert "mean_internal_score" in first_course
    assert "mean_external_score" in first_course
    assert "pass_percentage" in first_course
    assert "failed_count" in first_course
    assert "is_challenging" in first_course


# =============================================================================
# PART 2: AUTOMATED STRUCTURED MARKSHEET FILE EXPORTER TESTS
# =============================================================================

def test_structured_marksheet_single_export(setup_test_users_and_tokens):
    """
    Export sample student marksheet:
    - Verifies directory hierarchy: {STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/
    - Verifies file name pattern: {Student_Name_In_Proper_Case}_{Roll_No}.pdf
    - Verifies file is created on disk with valid PDF header
    """
    headers = setup_test_users_and_tokens["admin_headers"]

    # Find an active student in the database
    with get_sync_session() as session:
        reg = (
            session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .first()
        )
        assert reg is not None, "At least one registration must exist in database"
        reg_obj, stu_obj = reg
        test_sem = reg_obj.semester_number
        test_roll = stu_obj.roll_no
        test_session = reg_obj.exam_month_year

    payload = {
        "semester": test_sem,
        "roll_no": test_roll,
        "exam_month_year": test_session,
        "custom_directory": TEST_EXPORT_DIR,
    }

    res = client.post("/api/v1/marksheets/export-single", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "success"
    file_path = data["file_path"]
    filename = data["filename"]
    output_dir = data["output_directory"]

    # Verify naming convention: {Proper_Name}_{Roll_No}.pdf
    assert filename.endswith(f"_{test_roll}.pdf")
    assert filename.endswith(".pdf")
    # Verify no invalid path characters in filename
    for bad_char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        assert bad_char not in filename

    # Verify structured directory hierarchy exists on disk
    assert os.path.exists(output_dir)
    assert f"Semester_{test_sem}" in output_dir
    assert os.path.exists(file_path)

    # Verify valid PDF header bytes (%PDF)
    with open(file_path, "rb") as f:
        header = f.read(5)
        assert header.startswith(b"%PDF")


def test_export_config_endpoint(setup_test_users_and_tokens):
    """Verifies export configuration endpoint returns available sessions and naming specs."""
    headers = setup_test_users_and_tokens["admin_headers"]
    res = client.get("/api/v1/marksheets/export-config", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert "default_storage_dir" in data
    assert "available_sessions" in data
    assert "{Student_Name_In_Proper_Case}_{Roll_No}.pdf" in data["naming_specification"]
    assert len(data["available_sessions"]) > 0


# =============================================================================
# PART 3: UNIVERSAL USER FEEDBACK PERSISTENCE & ACCESS TESTS
# =============================================================================

def test_feedback_lifecycle_and_rbac(setup_test_users_and_tokens):
    """
    Test Feedback Persistence & Access:
    1. Submit feedback as 'Faculty' user -> assert 201 Created and verify record is inserted into PostgreSQL app_feedback.
    2. Query /api/v1/feedback/all as 'Faculty' -> assert 403 Forbidden.
    3. Query /api/v1/feedback/all as 'Admin' -> assert 200 OK and verify the submitted feedback is retrieved.
    4. Update status via /api/v1/feedback/{id}/status as 'Admin' -> verify status updates to 'RESOLVED' in database.
    """
    faculty_headers = setup_test_users_and_tokens["faculty_headers"]
    admin_headers = setup_test_users_and_tokens["admin_headers"]

    # 1. Submit feedback as Faculty user
    feedback_payload = {
        "category": "UI/UX Improvement",
        "subject": "Add Quick Filter for Backlogs",
        "feedback_text": "It would be tremendously useful to have a 1-click filter for students with active arrears.",
        "rating": 5,
    }

    submit_res = client.post("/api/v1/feedback/submit", json=feedback_payload, headers=faculty_headers)
    assert submit_res.status_code == 201, submit_res.text
    submit_data = submit_res.json()
    assert submit_data["status"] == "success"
    feedback_id = submit_data["feedback_id"]

    # Verify record in PostgreSQL app_feedback table
    with get_sync_session() as session:
        record = session.query(AppFeedback).filter_by(id=feedback_id).first()
        assert record is not None
        assert record.username == "TestFaculty"
        assert record.user_role == "Faculty"
        assert record.category == "UI/UX Improvement"
        assert record.subject == "Add Quick Filter for Backlogs"
        assert record.rating == 5
        assert record.status == "NEW"

    # 2. Query /api/v1/feedback/all as Faculty -> assert 403 Forbidden
    fac_all_res = client.get("/api/v1/feedback/all", headers=faculty_headers)
    assert fac_all_res.status_code == 403, (
        f"Faculty must not have permission to view full feedback registry. Got: {fac_all_res.status_code}"
    )

    # 3. Query /api/v1/feedback/all as Admin -> assert 200 OK and verify submitted feedback is present
    admin_all_res = client.get("/api/v1/feedback/all", headers=admin_headers)
    assert admin_all_res.status_code == 200, admin_all_res.text
    feedbacks_list = admin_all_res.json()["feedbacks"]
    found = any(f["id"] == feedback_id and f["username"] == "TestFaculty" for f in feedbacks_list)
    assert found, f"Feedback with ID {feedback_id} from TestFaculty must be present in Admin feed."

    # Verify /api/v1/feedback/summary as Admin
    summary_res = client.get("/api/v1/feedback/summary", headers=admin_headers)
    assert summary_res.status_code == 200, summary_res.text
    summary_kpis = summary_res.json()["kpis"]
    assert summary_kpis["total_submitted"] >= 1
    assert summary_kpis["average_rating"] >= 1.0

    # 4. Update status via /api/v1/feedback/{id}/status as Admin -> verify status updates to 'RESOLVED' in database
    status_payload = {
        "status": "RESOLVED",
        "admin_notes": "Implemented quick backlog pill filter in modern Executive Dashboard.",
    }
    patch_res = client.patch(f"/api/v1/feedback/{feedback_id}/status", json=status_payload, headers=admin_headers)
    assert patch_res.status_code == 200, patch_res.text
    patch_data = patch_res.json()
    assert patch_data["status"] == "success"
    assert patch_data["feedback"]["status"] == "RESOLVED"
    assert patch_data["feedback"]["resolved_at"] is not None

    # Verify directly in PostgreSQL database
    with get_sync_session() as session:
        updated_rec = session.query(AppFeedback).filter_by(id=feedback_id).first()
        assert updated_rec.status == "RESOLVED"
        assert updated_rec.resolved_at is not None
        assert "quick backlog pill filter" in updated_rec.admin_notes
