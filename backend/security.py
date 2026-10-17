"""
Enterprise Security Engine for VidyaMarksheet Examination System.
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.
Provides:
- Strict Cryptographic Configuration (JWT HS256, 8-hour TTL, 32+ char Secret Key Enforcement)
- Password Hashing (Bcrypt via CryptContext with Python 3.14 safety)
- Strong Password Complexity Policy
- Brute-Force Rate Limiting (5 failed attempts -> 15 min 423 Locked)
- Role-Based Access Control (RBAC) Dependency Injection
- Security Audit Logging (LOGIN_SUCCESS, LOGIN_FAILED, LOCKED_OUT, PASSWORD_CHANGED, UNAUTHORIZED_ACCESS)
- Token Version Invalidation (Session revocation upon password rotation)
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import os
import re
import types
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

import bcrypt

# Ensure passlib compatibility with modern bcrypt (>=4.0/5.0) under Python 3.14
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = types.SimpleNamespace(__version__=getattr(bcrypt, "__version__", "5.0.0"))

_orig_hashpw = bcrypt.hashpw
def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
    if len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)
bcrypt.hashpw = _safe_hashpw

from passlib.context import CryptContext
import jwt
from dotenv import load_dotenv
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Load environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

# -----------------------------------------------------------------------------
# 1. Cryptographic Configuration & Abort Checks
# -----------------------------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
WEAK_SECRETS = {"secret", "changeme", "default", "123456", "admin", "jwt_secret", ""}

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32 or JWT_SECRET_KEY.lower() in WEAK_SECRETS:
    raise RuntimeError(
        "FATAL: JWT_SECRET_KEY is missing, too short (<32 chars), or set to a weak default in backend/.env. "
        "Enterprise RBAC security requires a strong 32+ character cryptographic secret key. Startup aborted."
    )

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------------------------------------------------------
# 2. Password Hashing & Strength Policy
# -----------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """Hashes password using bcrypt with 72-byte safe handling."""
    safe_pwd = plain_password[:72]
    return pwd_context.hash(safe_pwd)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored bcrypt hash."""
    try:
        safe_pwd = plain_password[:72]
        return pwd_context.verify(safe_pwd, hashed_password)
    except Exception:
        return False


def validate_password_strength(password: str, username: str) -> Tuple[bool, Optional[str]]:
    """
    Enforces strong institutional password policy:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special symbol (!@#$%^&*)
    - Does not match username
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if password.lower() == username.lower():
        return False, "Password cannot match the username."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special symbol (!@#$%^&*)."
    return True, None


# -----------------------------------------------------------------------------
# 3. JWT Token Generation & Verification
# -----------------------------------------------------------------------------
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )


# -----------------------------------------------------------------------------
# 4. Request Metadata & Security Audit Logging
# -----------------------------------------------------------------------------
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "Unknown")


def log_security_event(
    session: Session,
    username: Optional[str],
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Persists security audit event into auth_security_audit_log."""
    try:
        from backend.db.models import AuthSecurityAuditLog
        audit_entry = AuthSecurityAuditLog(
            username=username,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(audit_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[SECURITY AUDIT ERROR] Failed to log security event: {e}")


# -----------------------------------------------------------------------------
# 5. Dependency Providers & Strict RBAC Enforcement
# -----------------------------------------------------------------------------
from backend.db.database import get_sync_session
from pydantic import BaseModel

class AuthenticatedUser(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    must_change_password: bool
    token_version: int
    is_active: bool


def get_current_user_from_token(
    request: Request,
    session: Session
) -> AuthenticatedUser:
    """
    Extracts JWT from Authorization header (explicit) or HttpOnly cookie 'vidya_access_token' (ambient).
    Validates token version against database user to support instant revocation.
    """
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    if not token:
        token = request.cookies.get("vidya_access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing access token."
        )

    payload = decode_access_token(token)
    username = payload.get("sub")
    token_version = payload.get("token_version", 1)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject username."
        )

    from backend.db.models import AppUser
    user = session.query(AppUser).filter(AppUser.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked. Contact System Administrator."
        )

    # Invalidation Check: Verify token version matches active database version
    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated due to password rotation or status change. Please log in again."
        )

    return AuthenticatedUser(
        id=user.id,
        username=user.username,
        role=user.role,
        full_name=user.full_name,
        must_change_password=user.must_change_password,
        token_version=user.token_version,
        is_active=user.is_active,
    )


def require_authenticated(request: Request):
    """Ensures caller has a valid, active authenticated session."""
    with get_sync_session() as session:
        return get_current_user_from_token(request, session)


def enforce_password_change_gate(request: Request) -> AuthenticatedUser:
    """
    Interceptor Dependency:
    If a user makes a request with a valid token where must_change_password == TRUE,
    allow access ONLY to /api/v1/auth/change-password and /api/v1/auth/logout.
    For all other operational routes, return 428 Precondition Required.
    """
    with get_sync_session() as session:
        user = get_current_user_from_token(request, session)
        path = request.url.path
        allowed_paths = ("/api/v1/auth/change-password", "/api/v1/auth/logout", "/api/v1/auth/me")
        if user.must_change_password and not any(path.startswith(p) for p in allowed_paths):
            client_ip = get_client_ip(request)
            log_security_event(
                session=session,
                username=user.username,
                action="UNAUTHORIZED_ACCESS",
                ip_address=client_ip,
                user_agent=f"{request.method} {path} [Blocked: 428 Must Change Password]",
            )
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="Password change required before accessing the application."
            )
        return user


def require_role(allowed_roles: list, enforce_password_rotation: bool = True):
    """
    Factory dependency checking role authorization and forced password rotation.
    Logs unauthorized 403 access attempts to auth_security_audit_log.
    """
    def dependency(request: Request) -> AuthenticatedUser:
        with get_sync_session() as session:
            user = get_current_user_from_token(request, session)
            client_ip = get_client_ip(request)
            route_desc = f"{request.method} {request.url.path}"

            # Check forced password rotation for operational routes (428 Precondition Required)
            if enforce_password_rotation and user.must_change_password:
                log_security_event(
                    session=session,
                    username=user.username,
                    action="UNAUTHORIZED_ACCESS",
                    ip_address=client_ip,
                    user_agent=f"{route_desc} [Blocked: 428 Must Change Password]",
                )
                raise HTTPException(
                    status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                    detail="Password change required before accessing the application."
                )

            # Role Authorization Check (with hyphen normalization for Sub-Dean / SubDean)
            norm_user_role = user.role.replace("-", "").strip().lower()
            norm_allowed = [r.replace("-", "").strip().lower() for r in allowed_roles]
            if norm_user_role not in norm_allowed:
                log_security_event(
                    session=session,
                    username=user.username,
                    action="UNAUTHORIZED_ACCESS",
                    ip_address=client_ip,
                    user_agent=f"{route_desc} [Role '{user.role}' not in {allowed_roles}]",
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: Role '{user.role}' has insufficient privileges for this operation."
                )

            return user

    return dependency


# Role-specific dependencies
require_admin = require_role(["Admin"])
require_subdean = require_role(["Admin", "Sub-Dean", "SubDean"])
require_scrutiny = require_role(["Admin", "Sub-Dean", "SubDean", "Scrutiny"])
require_operator = require_role(["Admin", "Sub-Dean", "SubDean", "Scrutiny", "Operator"])
require_viewer = require_role(["Admin", "Sub-Dean", "SubDean", "Scrutiny", "Operator", "Faculty", "Viewer"])

