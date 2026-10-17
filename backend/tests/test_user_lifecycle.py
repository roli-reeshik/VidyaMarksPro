"""
Automated Verification Suite: User Lifecycle Management, Role-Based Access Control,
Mandatory First-Login Password Change Gate (HTTP 428), and Instant Account Revocation (HTTP 403).
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_sync_session
from backend.db.models import AppUser
from backend.security import hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_user():
    """Ensure faculty_rajesh is cleaned up before and after test execution."""
    with get_sync_session() as session:
        # Reset Admin account state
        admin = session.query(AppUser).filter(AppUser.username == "Admin").first()
        if admin:
            admin.hashed_password = hash_password("Admin")
            admin.is_active = True
            admin.must_change_password = False
            admin.token_version = 1
            admin.failed_login_attempts = 0
            admin.locked_until = None

        existing = session.query(AppUser).filter(AppUser.username == "faculty_rajesh").first()
        if existing:
            session.delete(existing)
        session.commit()

    yield

    with get_sync_session() as session:
        existing = session.query(AppUser).filter(AppUser.username == "faculty_rajesh").first()
        if existing:
            session.delete(existing)
        admin = session.query(AppUser).filter(AppUser.username == "Admin").first()
        if admin:
            admin.hashed_password = hash_password("Admin")
            admin.is_active = True
            admin.must_change_password = False
            admin.token_version = 1
        session.commit()


def test_user_management_complete_lifecycle():
    # =========================================================================
    # Step 1: Root Admin Login & Account Creation
    # =========================================================================
    login_resp = client.post("/api/v1/auth/login", json={"username": "Admin", "password": "Admin"})
    assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
    admin_token = login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Verify listing users
    list_resp = client.get("/api/v1/users", headers=admin_headers)
    assert list_resp.status_code == 200

    # Create new user 'faculty_rajesh' with role 'Faculty' and temporary password
    temp_password = "TempPassword123!"
    create_payload = {
        "username": "faculty_rajesh",
        "full_name": "Dr. Rajesh Kumar",
        "email": "rajesh@vidyamarksheet.edu",
        "role": "Faculty",
        "temporary_password": temp_password,
    }
    create_resp = client.post("/api/v1/users", json=create_payload, headers=admin_headers)
    assert create_resp.status_code == 201, f"Create user failed: {create_resp.text}"
    created_user_data = create_resp.json()["user"]
    user_id = created_user_data["id"]
    assert created_user_data["username"] == "faculty_rajesh"
    assert created_user_data["role"] == "Faculty"
    assert created_user_data["is_active"] is True
    assert created_user_data["must_change_password"] is True

    # =========================================================================
    # Step 2: First Login & Mandatory Password Change Gate (HTTP 428)
    # =========================================================================
    # faculty_rajesh logs in with temporary password
    user_login_resp = client.post("/api/v1/auth/login", json={"username": "faculty_rajesh", "password": temp_password})
    assert user_login_resp.status_code == 200, f"faculty_rajesh login failed: {user_login_resp.text}"
    user_token = user_login_resp.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    assert user_login_resp.json()["user"]["must_change_password"] is True

    # Attempt to access an operational endpoint (GET /api/v1/batches) before changing password
    gate_resp = client.get("/api/v1/batches", headers=user_headers)
    assert gate_resp.status_code == 428, f"Expected 428 Precondition Required, got {gate_resp.status_code}: {gate_resp.text}"
    assert "Password change required" in gate_resp.json()["detail"]

    # =========================================================================
    # Step 3: Self-Service Password Change & Operational Access Granted
    # =========================================================================
    strong_new_password = "SecurePassword2026!"
    change_resp = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": temp_password,
            "new_password": strong_new_password,
            "confirm_password": strong_new_password,
        },
        headers=user_headers,
    )
    assert change_resp.status_code == 200, f"Password change failed: {change_resp.text}"
    assert change_resp.json()["user"]["must_change_password"] is False
    updated_user_token = change_resp.json()["access_token"]
    updated_headers = {"Authorization": f"Bearer {updated_user_token}"}

    # Now faculty_rajesh accesses the operational endpoint (/api/v1/batches) -> Must succeed with 200 OK
    batches_resp = client.get("/api/v1/batches", headers=updated_headers)
    assert batches_resp.status_code == 200, f"Operational access failed after password change: {batches_resp.text}"

    # =========================================================================
    # Step 4: Role-Based Access Control (RBAC) Gate - Unauthorized Action (HTTP 403)
    # =========================================================================
    # faculty_rajesh (role 'Faculty') attempts to upload datasheet to /api/upload -> Must be 403 Forbidden
    dummy_file = io.BytesIO(b"dummy excel content")
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("test.xlsx", dummy_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=updated_headers,
    )
    assert upload_resp.status_code == 403, f"Expected 403 Forbidden on upload for Faculty role, got {upload_resp.status_code}: {upload_resp.text}"
    assert "Forbidden" in upload_resp.json()["detail"]

    # =========================================================================
    # Step 5: Admin Instant Account Deactivation/Block & Immediate Token Revocation
    # =========================================================================
    # Root Admin blocks faculty_rajesh
    block_resp = client.patch(f"/api/v1/users/{user_id}/status", json={"is_active": False}, headers=admin_headers)
    assert block_resp.status_code == 200, f"Block account failed: {block_resp.text}"
    assert block_resp.json()["user"]["is_active"] is False

    # Previous session token must be immediately revoked (either 401 or 403)
    post_block_access = client.get("/api/v1/batches", headers=updated_headers)
    assert post_block_access.status_code in (401, 403), f"Revocation failed: {post_block_access.text}"

    # faculty_rajesh attempts to login again while blocked -> Must return 403 Forbidden
    blocked_login_resp = client.post("/api/v1/auth/login", json={"username": "faculty_rajesh", "password": strong_new_password})
    assert blocked_login_resp.status_code == 403, f"Expected 403 Forbidden on blocked login, got {blocked_login_resp.status_code}: {blocked_login_resp.text}"
    assert "Account is blocked" in blocked_login_resp.json()["detail"]
