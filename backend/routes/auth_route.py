"""
FastAPI Authentication & User Management Router.
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Endpoints:
- POST /api/v1/auth/login (HttpOnly Cookie + Bearer Token)
- POST /api/v1/auth/change-password (Self-Service Password Rotation)
- POST /api/v1/auth/admin/reset-password (Admin Password Reset)
- POST /api/v1/auth/logout (Cookie Revocation)
- GET  /api/v1/auth/me (Current Session Profile)
- GET  /api/v1/auth/users (Roster - Admin Only)
- GET  /api/v1/auth/audit-logs (Security Audit Trail)
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.db.database import get_sync_session
from backend.db.models import AppUser, AuthSecurityAuditLog
from backend.security import (
    verify_password,
    hash_password,
    validate_password_strength,
    create_access_token,
    get_client_ip,
    get_user_agent,
    log_security_event,
    get_current_user_from_token,
    require_admin,
    require_subdean,
    require_authenticated,
    AuthenticatedUser,
    MAX_FAILED_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Enterprise Authentication & RBAC Engine"])


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class LoginJsonRequest(BaseModel):
    username: str = Field(..., description="Institutional Username")
    password: str = Field(..., description="Password")


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Current institutional password")
    new_password: str = Field(..., description="New strong password")
    confirm_password: Optional[str] = Field(None, description="Confirmation of new password")


class AdminResetPasswordRequest(BaseModel):
    target_username: str = Field(..., description="Target username to reset")
    new_password: str = Field(..., description="New password for target user")


class CreateUserRequest(BaseModel):
    username: str = Field(..., description="Institutional Username / User ID")
    full_name: str = Field(..., description="Full Name of User")
    role: str = Field(..., description="Assigned Institutional Role (Admin, SubDean, Scrutiny, Operator, Faculty, Viewer)")
    password: str = Field(..., description="Initial Password")


class UpdateUserRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    full_name: Optional[str] = Field(None, description="Full Name of User")
    role: Optional[str] = Field(None, description="Assigned Role")
    is_active: Optional[bool] = Field(None, description="Account active status")



class UserProfileResponse(BaseModel):
    username: str
    role: str
    full_name: str
    must_change_password: bool
    is_active: bool
    last_login_at: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


# -----------------------------------------------------------------------------
# 1. Login Endpoint (HttpOnly Cookie & Bearer Token)
# -----------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
):
    """
    Authenticates user, protects against brute-force attacks (5 failed attempts -> 15 min lockout),
    issues JWT with 8-hour expiration, and delivers token via HttpOnly Cookie (XSS mitigation).
    Accepts JSON body or Form Data.
    """
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Parse JSON or Form payload
    username = None
    password = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            pass
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing username or password."
        )

    clean_username = username.strip()

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.username == clean_username).first()

        now_utc = datetime.now(timezone.utc)

        # Check existing lockout state
        if user and user.locked_until:
            if user.locked_until > now_utc:
                log_security_event(
                    session=session,
                    username=clean_username,
                    action="LOCKED_OUT",
                    ip_address=client_ip,
                    user_agent=user_agent,
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account temporarily locked due to multiple failed login attempts. Try again in 15 minutes."
                )
            else:
                # Lockout expired, reset counters
                user.locked_until = None
                user.failed_login_attempts = 0
                session.commit()

        # Check if user account is blocked
        if user and not user.is_active:
            log_security_event(
                session=session,
                username=clean_username,
                action="LOGIN_BLOCKED",
                ip_address=client_ip,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is blocked. Contact System Administrator."
            )

        # Validate credentials
        valid = False
        if user and user.is_active:
            valid = verify_password(password, user.hashed_password)

        if not valid:
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = now_utc + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    session.commit()
                    log_security_event(
                        session=session,
                        username=clean_username,
                        action="LOCKED_OUT",
                        ip_address=client_ip,
                        user_agent=user_agent,
                    )
                    # 5th attempt locks the account; 6th will be rejected by top check with 423
                else:
                    session.commit()
                    log_security_event(
                        session=session,
                        username=clean_username,
                        action="LOGIN_FAILED",
                        ip_address=client_ip,
                        user_agent=user_agent,
                    )
            else:
                log_security_event(
                    session=session,
                    username=clean_username,
                    action="LOGIN_FAILED",
                    ip_address=client_ip,
                    user_agent=user_agent,
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password."
            )

        # Successful Login: Reset lockout and update timestamps
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now_utc
        session.commit()

        log_security_event(
            session=session,
            username=user.username,
            action="LOGIN_SUCCESS",
            ip_address=client_ip,
            user_agent=user_agent,
        )

        token_data = {
            "sub": user.username,
            "role": user.role,
            "must_change_password": user.must_change_password,
            "token_version": user.token_version,
        }
        token = create_access_token(data=token_data)

        # Set HttpOnly Cookie (XSS Mitigation)
        response.set_cookie(
            key="vidya_access_token",
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,  # Set True under production HTTPS
            max_age=8 * 3600,
            path="/"
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "role": user.role,
                "full_name": user.full_name,
                "must_change_password": user.must_change_password,
            }
        }


# -----------------------------------------------------------------------------
# 2. Self-Service Password Change (Increments token_version for instant revocation)
# -----------------------------------------------------------------------------
@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current_user: AuthenticatedUser = Depends(require_authenticated),
):
    """
    Self-service password rotation. Enforces complexity rules, updates hash,
    sets must_change_password=False, and increments token_version to invalidate old tokens.
    """
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Verify old password
        if not verify_password(payload.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect."
            )

        if payload.confirm_password is not None and payload.new_password != payload.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password and confirmation do not match."
            )

        # Strong Password Policy Validation
        is_strong, error_msg = validate_password_strength(payload.new_password, user.username)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Rotate password & increment token version (Session Revocation)
        user.hashed_password = hash_password(payload.new_password)
        user.must_change_password = False
        user.token_version += 1
        session.commit()

        log_security_event(
            session=session,
            username=user.username,
            action="PASSWORD_CHANGED",
            ip_address=client_ip,
            user_agent=user_agent,
        )

        # Issue newly versioned token
        new_token = create_access_token(data={
            "sub": user.username,
            "role": user.role,
            "must_change_password": False,
            "token_version": user.token_version,
        })

        response.set_cookie(
            key="vidya_access_token",
            value=new_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=8 * 3600,
            path="/"
        )

        return {
            "success": True,
            "message": "Password changed successfully. Active sessions revoked.",
            "access_token": new_token,
            "user": {
                "username": user.username,
                "role": user.role,
                "full_name": user.full_name,
                "must_change_password": False,
            }
        }


# -----------------------------------------------------------------------------
# 3. Administrator Password Reset
# -----------------------------------------------------------------------------
@router.post("/admin/reset-password")
def admin_reset_password(
    payload: AdminResetPasswordRequest,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Administrative reset: Sets target user's password, forces rotation on next login,
    and increments token_version to invalidate their active sessions.
    """
    client_ip = get_client_ip(request)

    with get_sync_session() as session:
        target = session.query(AppUser).filter(AppUser.username == payload.target_username.strip()).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{payload.target_username}' not found."
            )

        is_strong, error_msg = validate_password_strength(payload.new_password, target.username)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        target.hashed_password = hash_password(payload.new_password)
        target.must_change_password = True
        target.token_version += 1
        target.failed_login_attempts = 0
        target.locked_until = None
        session.commit()

        log_security_event(
            session=session,
            username=target.username,
            action="PASSWORD_CHANGED",
            ip_address=client_ip,
            user_agent=f"Reset by Admin '{admin_user.username}'",
        )

        return {
            "success": True,
            "message": f"Password for user '{target.username}' reset successfully. User must change password on next login."
        }


# -----------------------------------------------------------------------------
# 3b. Admin User Management (Create, Update, Delete)
# -----------------------------------------------------------------------------
VALID_ROLES = {"Admin", "SubDean", "Scrutiny", "Operator", "Faculty", "Viewer"}


@router.post("/admin/create-user")
def admin_create_user(
    payload: CreateUserRequest,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Creates a new institutional user with an assigned RBAC role.
    Admin grants access as per the role (Faculty, Operator, SubDean, Viewer, Scrutiny, Admin).
    """
    clean_username = payload.username.strip()
    clean_name = payload.full_name.strip()
    role = payload.role.strip()

    if not clean_username or not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and Full Name are required."
        )

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{role}'. Allowed roles: {', '.join(sorted(VALID_ROLES))}"
        )

    if not payload.password or len(payload.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters long."
        )

    client_ip = get_client_ip(request)

    with get_sync_session() as session:
        existing = session.query(AppUser).filter(AppUser.username == clean_username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with username '{clean_username}' already exists."
            )

        new_user = AppUser(
            username=clean_username,
            full_name=clean_name,
            role=role,
            hashed_password=hash_password(payload.password),
            is_active=True,
            must_change_password=False,
            failed_login_attempts=0,
            locked_until=None,
            token_version=1,
        )
        session.add(new_user)
        session.commit()

        log_security_event(
            session=session,
            username=clean_username,
            action="USER_CREATED",
            ip_address=client_ip,
            user_agent=f"Created by Admin '{admin_user.username}' with role '{role}'",
        )

        return {
            "success": True,
            "message": f"User '{clean_username}' successfully created with role '{role}'.",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "is_active": new_user.is_active,
            }
        }


@router.put("/admin/users/{user_id}")
def admin_update_user(
    user_id: int,
    payload: UpdateUserRequest,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Updates user details or grants/changes role.
    """
    client_ip = get_client_ip(request)

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        if payload.role is not None:
            clean_role = payload.role.strip()
            if clean_role not in VALID_ROLES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role '{clean_role}'. Allowed roles: {', '.join(sorted(VALID_ROLES))}"
                )
            user.role = clean_role
            user.token_version += 1  # Invalidate previous token so new role takes effect

        if payload.full_name is not None and payload.full_name.strip():
            user.full_name = payload.full_name.strip()

        if payload.is_active is not None:
            user.is_active = payload.is_active
            if not payload.is_active:
                user.token_version += 1  # Revoke session immediately

        session.commit()

        log_security_event(
            session=session,
            username=user.username,
            action="USER_UPDATED",
            ip_address=client_ip,
            user_agent=f"Updated by Admin '{admin_user.username}'",
        )

        return {
            "success": True,
            "message": f"User '{user.username}' updated successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
            }
        }


@router.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Deletes an institutional user account.
    Admin cannot delete their own active account.
    """
    client_ip = get_client_ip(request)

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        if user.username.lower() == admin_user.username.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own active administrator account."
            )

        deleted_username = user.username
        session.delete(user)
        session.commit()

        log_security_event(
            session=session,
            username=deleted_username,
            action="USER_DELETED",
            ip_address=client_ip,
            user_agent=f"Deleted by Admin '{admin_user.username}'",
        )

        return {
            "success": True,
            "message": f"User '{deleted_username}' deleted successfully."
        }



# -----------------------------------------------------------------------------
# 4. Logout Endpoint (Cookie Clearing)
# -----------------------------------------------------------------------------
@router.post("/logout")
def logout(response: Response):
    """Clears HttpOnly access cookie."""
    response.delete_cookie(key="vidya_access_token", path="/")
    return {"success": True, "message": "Logged out successfully."}


# -----------------------------------------------------------------------------
# 5. Current User Profile
# -----------------------------------------------------------------------------
@router.get("/me")
def get_me(current_user: AuthenticatedUser = Depends(require_authenticated)):
    """Returns profile of currently authenticated user."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "must_change_password": current_user.must_change_password,
        "last_login_at": None,
    }


# -----------------------------------------------------------------------------
# 6. Roster Listing (Admin Only)
# -----------------------------------------------------------------------------
@router.get("/users")
def list_users(admin_user: AuthenticatedUser = Depends(require_admin)):
    """Lists institutional accounts (Admin only)."""
    with get_sync_session() as session:
        users = session.query(AppUser).order_by(AppUser.id).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "must_change_password": u.must_change_password,
                "failed_login_attempts": u.failed_login_attempts,
                "is_locked": bool(u.locked_until and u.locked_until > datetime.now(timezone.utc)),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            }
            for u in users
        ]


# -----------------------------------------------------------------------------
# 7. Security Audit Trail (Admin & SubDean)
# -----------------------------------------------------------------------------
@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    authority: AuthenticatedUser = Depends(require_subdean)
):
    """Retrieves chronological security audit logs."""
    with get_sync_session() as session:
        logs = (
            session.query(AuthSecurityAuditLog)
            .order_by(AuthSecurityAuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": l.id,
                "username": l.username,
                "action": l.action,
                "ip_address": l.ip_address,
                "user_agent": l.user_agent,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ]
