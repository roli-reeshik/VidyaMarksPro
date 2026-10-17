"""
Administrative User Management Portal Route (/api/v1/users).
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Provides:
- GET /api/v1/users (List all registered accounts)
- POST /api/v1/users (Create new account with temporary password & must_change_password=True)
- PATCH /api/v1/users/{user_id}/status (Toggle Active/Blocked state; instantly revokes sessions on block)
- PATCH /api/v1/users/{user_id}/role (Role assignment with security audit logging)
- POST /api/v1/users/{user_id}/reset-password (Admin password reset to temporary password)
- DELETE /api/v1/users/{user_id} (Delete institutional user)
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.db.database import get_sync_session
from backend.db.models import AppUser, AuthSecurityAuditLog
from backend.security import (
    hash_password,
    get_client_ip,
    get_user_agent,
    log_security_event,
    require_admin,
    AuthenticatedUser,
)

router = APIRouter(prefix="/api/v1/users", tags=["Administrative User Management Portal"])

VALID_ROLES = {"Admin", "Sub-Dean", "SubDean", "Scrutiny", "Operator", "Faculty", "Viewer"}
CANONICAL_ROLES = {"Admin", "Sub-Dean", "Scrutiny", "Operator", "Faculty", "Viewer"}


def normalize_role_name(role: str) -> str:
    r = role.strip()
    if r.lower() == "subdean":
        return "Sub-Dean"
    for cr in CANONICAL_ROLES:
        if cr.lower() == r.lower():
            return cr
    return r


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------
class UserCreateRequest(BaseModel):
    username: str = Field(..., description="User ID / Login ID")
    full_name: str = Field(..., description="Full Name of User")
    role: str = Field(..., description="Assigned Institutional Role")
    temporary_password: Optional[str] = Field(None, description="Temporary Initial Password")
    email: Optional[str] = Field(None, description="Email address (optional)")


class UserStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Active status (False = Blocked)")


class UserRoleUpdateRequest(BaseModel):
    role: str = Field(..., description="New institutional role")


class AdminResetPasswordRequest(BaseModel):
    temporary_password: Optional[str] = Field(None, description="New temporary password")


class UserResponseItem(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str]
    role: str
    is_active: bool
    must_change_password: bool
    created_at: Optional[str]
    last_login_at: Optional[str]


# -----------------------------------------------------------------------------
# 1. GET /api/v1/users - List Registered Users
# -----------------------------------------------------------------------------
@router.get("", response_model=List[UserResponseItem])
def list_users(admin_user: AuthenticatedUser = Depends(require_admin)):
    """
    Returns a list of all registered institutional users.
    Omits hashed_password for security.
    Protected by require_admin.
    """
    with get_sync_session() as session:
        users = session.query(AppUser).order_by(AppUser.id.asc()).all()
        return [
            UserResponseItem(
                id=u.id,
                username=u.username,
                full_name=u.full_name,
                email=u.email,
                role=u.role,
                is_active=u.is_active,
                must_change_password=u.must_change_password,
                created_at=u.created_at.isoformat() if u.created_at else None,
                last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
            )
            for u in users
        ]


# -----------------------------------------------------------------------------
# 2. POST /api/v1/users - Create New Institutional User
# -----------------------------------------------------------------------------
@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Creates a new institutional user with assigned role.
    Hashes password using bcrypt. Sets must_change_password=True and is_active=True.
    Returns 201 Created with the user record.
    """
    clean_username = payload.username.strip()
    clean_full_name = payload.full_name.strip()
    norm_role = normalize_role_name(payload.role)

    if not clean_username or not clean_full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and Full Name are mandatory."
        )

    if norm_role not in CANONICAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Allowed roles: {sorted(list(CANONICAL_ROLES))}"
        )

    temp_password = (payload.temporary_password or "").strip()
    if not temp_password:
        temp_password = clean_username

    client_ip = get_client_ip(request)

    with get_sync_session() as session:
        existing = session.query(AppUser).filter(AppUser.username == clean_username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{clean_username}' already exists in institutional records."
            )

        new_user = AppUser(
            username=clean_username,
            full_name=clean_full_name,
            email=payload.email.strip() if payload.email else None,
            role=norm_role,
            hashed_password=hash_password(temp_password),
            is_active=True,
            must_change_password=True,
            token_version=1,
            created_by=admin_user.username,
            created_at=datetime.now(timezone.utc),
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        log_security_event(
            session=session,
            username=clean_username,
            action="USER_CREATED",
            ip_address=client_ip,
            user_agent=f"Created by Admin '{admin_user.username}' [Role: {norm_role}]",
        )

        return {
            "success": True,
            "message": f"User '{clean_username}' created successfully.",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "email": new_user.email,
                "role": new_user.role,
                "is_active": new_user.is_active,
                "must_change_password": new_user.must_change_password,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
            }
        }


# -----------------------------------------------------------------------------
# 3. PATCH /api/v1/users/{user_id}/status - Toggle Account Active/Blocked
# -----------------------------------------------------------------------------
@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Toggles account active state (Active <-> Blocked).
    When is_active is set to FALSE (BLOCKED): increments token_version to immediately
    revoke all existing JWT tokens, forcing immediate logout.
    """
    client_ip = get_client_ip(request)

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found."
            )

        if user.username.lower() == admin_user.username.lower() and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot block their own active account."
            )

        user.is_active = payload.is_active
        if not payload.is_active:
            # Increment token_version to immediately revoke all active JWT sessions
            user.token_version += 1

        session.commit()

        action = "ACCOUNT_ACTIVATED" if payload.is_active else "ACCOUNT_BLOCKED"
        log_security_event(
            session=session,
            username=user.username,
            action=action,
            ip_address=client_ip,
            user_agent=f"Status set to {payload.is_active} by Admin '{admin_user.username}'",
        )

        return {
            "success": True,
            "message": f"Account for '{user.username}' {'activated' if payload.is_active else 'blocked'} successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "token_version": user.token_version,
            }
        }


# -----------------------------------------------------------------------------
# 4. PATCH /api/v1/users/{user_id}/role - Update Institutional Role
# -----------------------------------------------------------------------------
@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Updates the user's role and logs the modification in auth_security_audit_log.
    Increments token_version to update permissions immediately.
    """
    client_ip = get_client_ip(request)
    norm_role = normalize_role_name(payload.role)

    if norm_role not in CANONICAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Allowed roles: {sorted(list(CANONICAL_ROLES))}"
        )

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found."
            )

        old_role = user.role
        user.role = norm_role
        user.token_version += 1  # Require re-issue so new role claims apply
        session.commit()

        log_security_event(
            session=session,
            username=user.username,
            action="ROLE_CHANGED",
            ip_address=client_ip,
            user_agent=f"Role changed from '{old_role}' to '{norm_role}' by Admin '{admin_user.username}'",
        )

        return {
            "success": True,
            "message": f"Role for user '{user.username}' updated to '{norm_role}'.",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
        }


# -----------------------------------------------------------------------------
# 5. POST /api/v1/users/{user_id}/reset-password - Admin Password Reset
# -----------------------------------------------------------------------------
@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: Optional[AdminResetPasswordRequest] = None,
    request: Request = None,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Resets target user's password to a temporary password,
    forces must_change_password=True, and increments token_version to revoke active sessions.
    """
    client_ip = get_client_ip(request) if request else None

    with get_sync_session() as session:
        user = session.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found."
            )

        temp_pwd = payload.temporary_password.strip() if (payload and payload.temporary_password) else f"{user.username}#2026"
        user.hashed_password = hash_password(temp_pwd)
        user.must_change_password = True
        user.token_version += 1
        user.failed_login_attempts = 0
        user.locked_until = None
        session.commit()

        log_security_event(
            session=session,
            username=user.username,
            action="PASSWORD_RESET_BY_ADMIN",
            ip_address=client_ip,
            user_agent=f"Password reset to temporary by Admin '{admin_user.username}'",
        )

        return {
            "success": True,
            "message": f"Password for user '{user.username}' reset successfully. User must change password upon next login.",
            "temporary_password": temp_pwd,
        }


# -----------------------------------------------------------------------------
# 6. DELETE /api/v1/users/{user_id} - Delete Institutional Account
# -----------------------------------------------------------------------------
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    admin_user: AuthenticatedUser = Depends(require_admin),
):
    """
    Deletes an institutional user account. Root admin cannot be deleted.
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
