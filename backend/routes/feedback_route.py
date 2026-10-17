"""
Universal User Feedback Database Persistence & Admin Review Route
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.

Endpoints:
- POST  /api/v1/feedback/submit:
    Accessible by ANY authenticated user. Submits feedback record to PostgreSQL app_feedback.
- GET   /api/v1/feedback/all:
    Protected (Admin and Sub-Dean). Lists feedback registry with query filters.
- GET   /api/v1/feedback/summary:
    Protected (Admin only). Aggregated feedback KPIs.
- PATCH /api/v1/feedback/{feedback_id}/status:
    Protected (Admin only). Updates feedback status and administrative internal notes.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, constr
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.db.database import get_sync_session
from backend.db.models import AppFeedback
from backend.security import require_authenticated, require_subdean, require_admin

router = APIRouter(prefix="/api/v1/feedback", tags=["Universal User Feedback Engine"])

VALID_CATEGORIES = {
    "UI/UX Improvement",
    "Calculation/Grading Discrepancy",
    "Feature Request",
    "Bug/Defect",
    "General Feedback",
}

VALID_STATUSES = {"NEW", "UNDER_REVIEW", "RESOLVED", "ARCHIVED"}


class FeedbackSubmissionPayload(BaseModel):
    category: str = Field(..., description="Feedback category")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject summary (min 5 chars)")
    feedback_text: str = Field(..., min_length=10, description="Detailed feedback body (min 10 chars)")
    rating: int = Field(..., ge=1, le=5, description="Institutional user rating (1-5 stars)")


class FeedbackStatusUpdatePayload(BaseModel):
    status: str = Field(..., description="Target status: 'NEW', 'UNDER_REVIEW', 'RESOLVED', 'ARCHIVED'")
    admin_notes: Optional[str] = Field(None, description="Administrative internal notes or actions taken")


@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackSubmissionPayload,
    current_user: Any = Depends(require_authenticated),
):
    """
    Submits user feedback and persists it directly into PostgreSQL `app_feedback` table.
    Automatically captures username and user_role from the verified JWT session.
    """
    # Validate category
    cat = payload.category.strip()
    if cat not in VALID_CATEGORIES:
        # Fall back to General Feedback if non-standard or preserve
        if not cat:
            cat = "General Feedback"

    with get_sync_session() as session:
        feedback_entry = AppFeedback(
            user_id=getattr(current_user, "id", None),
            username=current_user.username,
            user_role=current_user.role,
            category=cat,
            subject=payload.subject.strip(),
            feedback_text=payload.feedback_text.strip(),
            rating=payload.rating,
            status="NEW",
            admin_notes=None,
            submitted_at=datetime.now(timezone.utc),
            resolved_at=None,
        )
        session.add(feedback_entry)
        session.commit()
        session.refresh(feedback_entry)

        return {
            "status": "success",
            "message": "Thank you! Your feedback has been stored and routed to the System Administrator.",
            "feedback_id": feedback_entry.id,
            "submitted_at": feedback_entry.submitted_at.isoformat() if feedback_entry.submitted_at else None,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.get("/all")
def get_all_feedback(
    category: Optional[str] = Query(None, description="Filter by feedback category"),
    status: Optional[str] = Query(None, description="Filter by status ('NEW', 'UNDER_REVIEW', 'RESOLVED', 'ARCHIVED')"),
    role: Optional[str] = Query(None, description="Filter by submitter role"),
    current_user: Any = Depends(require_subdean),
):
    """
    Retrieves full feedback registry with submitter username, role, timestamp, text, rating, and status.
    Protected: Accessible ONLY by Admin and Sub-Dean roles.
    """
    with get_sync_session() as session:
        query = session.query(AppFeedback)

        if category and category.strip() and category.strip().lower() != "all":
            query = query.filter(AppFeedback.category.ilike(f"%{category.strip()}%"))

        if status and status.strip() and status.strip().lower() != "all":
            query = query.filter(AppFeedback.status == status.strip().upper())

        if role and role.strip() and role.strip().lower() != "all":
            query = query.filter(AppFeedback.user_role.ilike(f"%{role.strip()}%"))

        records = query.order_by(desc(AppFeedback.submitted_at)).all()

        results = []
        for r in records:
            results.append({
                "id": r.id,
                "user_id": r.user_id,
                "username": r.username,
                "user_role": r.user_role,
                "category": r.category,
                "subject": r.subject,
                "feedback_text": r.feedback_text,
                "rating": r.rating,
                "status": r.status,
                "admin_notes": r.admin_notes,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            })

        return {
            "status": "success",
            "count": len(results),
            "feedbacks": results,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.get("/summary")
def get_feedback_summary(
    current_user: Any = Depends(require_admin),
):
    """
    Returns aggregated feedback KPIs: Total Submitted, Pending Review, Resolved Count,
    and Average System Rating.
    Protected: Accessible ONLY by role 'Admin'.
    """
    with get_sync_session() as session:
        total_submitted = session.query(func.count(AppFeedback.id)).scalar() or 0
        pending_review = (
            session.query(func.count(AppFeedback.id))
            .filter(AppFeedback.status.in_(["NEW", "UNDER_REVIEW"]))
            .scalar()
            or 0
        )
        resolved_count = (
            session.query(func.count(AppFeedback.id))
            .filter(AppFeedback.status == "RESOLVED")
            .scalar()
            or 0
        )
        archived_count = (
            session.query(func.count(AppFeedback.id))
            .filter(AppFeedback.status == "ARCHIVED")
            .scalar()
            or 0
        )
        avg_rating = session.query(func.avg(AppFeedback.rating)).scalar()
        average_rating = round(float(avg_rating), 2) if avg_rating is not None else 5.0

        # Category Breakdown
        cat_counts = (
            session.query(AppFeedback.category, func.count(AppFeedback.id))
            .group_by(AppFeedback.category)
            .all()
        )
        categories_breakdown = {c: count for c, count in cat_counts}

        return {
            "status": "success",
            "kpis": {
                "total_submitted": total_submitted,
                "pending_review": pending_review,
                "resolved_count": resolved_count,
                "archived_count": archived_count,
                "average_rating": average_rating,
            },
            "category_breakdown": categories_breakdown,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.patch("/{feedback_id}/status")
def update_feedback_status(
    feedback_id: int,
    payload: FeedbackStatusUpdatePayload,
    current_user: Any = Depends(require_admin),
):
    """
    Updates feedback status ('UNDER_REVIEW', 'RESOLVED', 'ARCHIVED') and optional internal admin notes.
    Automatically sets `resolved_at = NOW()` when marked as 'RESOLVED'.
    Protected: Accessible ONLY by role 'Admin'.
    """
    new_status = payload.status.strip().upper()
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of: {sorted(list(VALID_STATUSES))}.",
        )

    with get_sync_session() as session:
        feedback = session.query(AppFeedback).filter_by(id=feedback_id).first()
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback record with ID {feedback_id} not found.",
            )

        feedback.status = new_status
        if payload.admin_notes is not None:
            feedback.admin_notes = payload.admin_notes.strip()

        if new_status == "RESOLVED":
            feedback.resolved_at = datetime.now(timezone.utc)
        elif new_status != "RESOLVED":
            feedback.resolved_at = None

        session.commit()
        session.refresh(feedback)

        return {
            "status": "success",
            "message": f"Feedback #{feedback_id} status updated to {new_status}.",
            "feedback": {
                "id": feedback.id,
                "status": feedback.status,
                "admin_notes": feedback.admin_notes,
                "resolved_at": feedback.resolved_at.isoformat() if feedback.resolved_at else None,
            },
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }
