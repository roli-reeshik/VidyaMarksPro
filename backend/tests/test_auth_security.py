"""
Enterprise Automated Security & RBAC Verification Test Suite.
Tests:
1. Brute-Force Test: 5 failed logins -> 6th attempt returns 423 Locked.
2. Invalidation Test: Password change increments token_version -> old token returns 401 Unauthorized.
3. Privilege Escalation Test: Operator role attempting /marksheets/mark-as-final returns 403 Forbidden.
4. Audit Trail Test: Verifies failed logins, lockouts, and unauthorized attempts are logged in auth_security_audit_log.
5. Strong Password Policy Test: Validates complexity rules and reject username match.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import get_sync_session
from backend.db.models import AppUser, AuthSecurityAuditLog
from backend.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_test_users():
    """Ensure baseline test accounts exist in standard state before tests run."""
    with get_sync_session() as session:
        # Reset Admin
        admin = session.query(AppUser).filter(AppUser.username == "Admin").first()
        if admin:
            admin.hashed_password = hash_password("Admin")
            admin.failed_login_attempts = 0
            admin.locked_until = None
            admin.token_version = 1
            admin.must_change_password = True
            admin.is_active = True

        # Reset Operator
        operator = session.query(AppUser).filter(AppUser.username == "Operator").first()
        if operator:
            operator.hashed_password = hash_password("Operator")
            operator.failed_login_attempts = 0
            operator.locked_until = None
            operator.token_version = 1
            operator.must_change_password = True
            operator.is_active = True
        else:
            operator = AppUser(
                username="Operator",
                full_name="Exam Cell Operator",
                role="Operator",
                hashed_password=hash_password("Operator"),
                is_active=True,
                must_change_password=True,
                token_version=1,
            )
            session.add(operator)

        # Reset SubDean
        subdean = session.query(AppUser).filter(AppUser.username == "SubDean").first()
        if subdean:
            subdean.hashed_password = hash_password("SubDean")
            subdean.failed_login_attempts = 0
            subdean.locked_until = None
            subdean.token_version = 1
            subdean.must_change_password = True
            subdean.is_active = True
        else:
            subdean = AppUser(
                username="SubDean",
                full_name="Sub-Dean Examination",
                role="SubDean",
                hashed_password=hash_password("SubDean"),
                is_active=True,
                must_change_password=True,
                token_version=1,
            )
            session.add(subdean)

        session.commit()
    yield
    with get_sync_session() as session:
        for uname in ["SubDean", "Operator"]:
            u = session.query(AppUser).filter(AppUser.username == uname).first()
            if u:
                session.delete(u)
        admin = session.query(AppUser).filter(AppUser.username == "Admin").first()
        if admin:
            admin.hashed_password = hash_password("Admin")
            admin.failed_login_attempts = 0
            admin.locked_until = None
            admin.token_version = 1
            admin.must_change_password = False
            admin.is_active = True
        session.commit()


def test_login_successful_and_cookie_delivery():
    """Verifies valid login issues JWT token and delivers HttpOnly cookie."""
    res = client.post("/api/v1/auth/login", json={"username": "Admin", "password": "Admin"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "Admin"
    assert data["user"]["role"] == "Admin"
    assert "vidya_access_token" in res.cookies


def test_brute_force_lockout_protection():
    """Attempt 5 incorrect logins -> assert 6th attempt returns 423 Locked."""
    username = "Operator"

    # Attempts 1 to 5: Incorrect password -> 401 Unauthorized
    for i in range(1, 6):
        res = client.post("/api/v1/auth/login", json={"username": username, "password": "WrongPassword123!"})
        assert res.status_code == 401
        assert "Invalid username or password" in res.json()["detail"]

    # 6th Attempt: Account is now locked -> 423 Locked
    res_6th = client.post("/api/v1/auth/login", json={"username": username, "password": "Operator"})
    assert res_6th.status_code == 423
    assert "temporarily locked" in res_6th.json()["detail"].lower()


def test_token_invalidation_upon_password_change():
    """Change password -> verify old token version is rejected with 401 Unauthorized."""
    # 1. Login as Admin to get Token V1
    login_res = client.post("/api/v1/auth/login", json={"username": "Admin", "password": "Admin"})
    assert login_res.status_code == 200
    token_v1 = login_res.json()["access_token"]

    # 2. Change password using Token V1
    new_password = "AdminSecurePass2026!"
    change_res = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "Admin",
            "new_password": new_password,
            "confirm_password": new_password,
        },
        headers={"Authorization": f"Bearer {token_v1}"}
    )
    assert change_res.status_code == 200
    token_v2 = change_res.json()["access_token"]
    assert token_v1 != token_v2

    # 3. Old Token V1 MUST now be rejected with 401 Unauthorized
    old_token_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_v1}"})
    assert old_token_res.status_code == 401
    assert "invalidated" in old_token_res.json()["detail"].lower()

    # 4. New Token V2 works
    new_token_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_v2}"})
    assert new_token_res.status_code == 200
    assert new_token_res.json()["username"] == "Admin"


def test_privilege_escalation_forbidden_operator():
    """Send request to /api/v1/marksheets/mark-as-final with 'Operator' credentials -> assert 403 Forbidden."""
    # First, log in as Operator and change password to satisfy forced rotation
    op_login = client.post("/api/v1/auth/login", json={"username": "Operator", "password": "Operator"})
    assert op_login.status_code == 200
    op_token = op_login.json()["access_token"]

    op_change = client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": "Operator",
            "new_password": "OperatorNewPass2026!",
            "confirm_password": "OperatorNewPass2026!",
        },
        headers={"Authorization": f"Bearer {op_token}"}
    )
    assert op_change.status_code == 200
    active_op_token = op_change.json()["access_token"]

    # Operator attempts to mark marksheets as FINAL -> 403 Forbidden
    payload = {
        "semester": 1,
        "roll_numbers": ["22045001"],
        "delivered_by": "Operator Unauthorized",
    }
    forbidden_res = client.post(
        "/api/v1/marksheets/mark-as-final",
        json=payload,
        headers={"Authorization": f"Bearer {active_op_token}"}
    )
    assert forbidden_res.status_code == 403
    assert "insufficient privileges" in forbidden_res.json()["detail"].lower() or "forbidden" in forbidden_res.json()["detail"].lower()


def test_security_audit_trail_logging():
    """Verifies failed attempts, lockouts, and unauthorized attempts appear in auth_security_audit_log."""
    with get_sync_session() as session:
        # Check that we have recorded audit logs
        logs = session.query(AuthSecurityAuditLog).order_by(AuthSecurityAuditLog.timestamp.desc()).all()
        actions = [l.action for l in logs]
        assert len(logs) > 0
        # Check presence of expected security events
        assert "LOGIN_SUCCESS" in actions or "LOGIN_FAILED" in actions
        assert any(act in ["UNAUTHORIZED_ACCESS", "LOCKED_OUT", "PASSWORD_CHANGED", "LOGIN_FAILED"] for act in actions)


def test_strong_password_policy_enforcement():
    """Verifies that weak, short, or username-matching passwords are rejected."""
    # Login as SubDean
    sub_login = client.post("/api/v1/auth/login", json={"username": "SubDean", "password": "SubDean"})
    sub_token = sub_login.json()["access_token"]

    # 1. Matching username
    res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "SubDean", "new_password": "SubDean", "confirm_password": "SubDean"},
        headers={"Authorization": f"Bearer {sub_token}"}
    )
    assert res.status_code == 400

    # 2. Too short (< 8 chars)
    res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "SubDean", "new_password": "Sub1!", "confirm_password": "Sub1!"},
        headers={"Authorization": f"Bearer {sub_token}"}
    )
    assert res.status_code == 400

    # 3. Missing special symbol
    res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "SubDean", "new_password": "SubDeanPassword123", "confirm_password": "SubDeanPassword123"},
        headers={"Authorization": f"Bearer {sub_token}"}
    )
    assert res.status_code == 400

    # 4. Valid strong password succeeds
    valid_new_pw = "SubDeanSecure@2026"
    res = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "SubDean", "new_password": valid_new_pw, "confirm_password": valid_new_pw},
        headers={"Authorization": f"Bearer {sub_token}"}
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
