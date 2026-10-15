"""
Database package initialization for VidyaMarksheet.
VidyaLabs Copyright © 2026.
"""

from backend.db.database import (
    Base,
    async_engine,
    sync_engine,
    AsyncSessionLocal,
    SyncSessionLocal,
    get_async_session,
    get_sync_session,
    DATABASE_URL,
    SYNC_DATABASE_URL,
)
from backend.db.models import (
    Batch,
    Student,
    Course,
    StudentSemesterRegistration,
    StudentCourseMark,
    CumulativeAcademicSummary,
    MarksAuditLog,
)

__all__ = [
    "Base",
    "async_engine",
    "sync_engine",
    "AsyncSessionLocal",
    "SyncSessionLocal",
    "get_async_session",
    "get_sync_session",
    "DATABASE_URL",
    "SYNC_DATABASE_URL",
    "Batch",
    "Student",
    "Course",
    "StudentSemesterRegistration",
    "StudentCourseMark",
    "CumulativeAcademicSummary",
    "MarksAuditLog",
]
