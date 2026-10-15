"""
FastAPI Router for Role-Based Workflow Approval & Field-Level Audit Trail.
Lifecycle: DRAFT -> SCRUTINIZED -> APPROVED -> LOCKED
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, Query, Depends

from backend.db.database import get_sync_session
from backend.db.repository import ExaminationRepository

router = APIRouter(prefix="/api/v1/workflow", tags=["Role-Based Workflow Approval Engine"])


class WorkflowTransitionRequest(BaseModel):
    semester_number: int = Field(..., ge=1, le=8, description="Target Semester Number (1 to 8)")
    target_status: str = Field(..., description="Target status ('SCRUTINIZED', 'APPROVED', 'LOCKED')")
    user_role: str = Field("Scrutiny Committee", description="Role of the current user ('Scrutiny Committee', 'Admin / Sub-Dean')")
    operator_name: str = Field("System Operator", description="Name or identifier of the operator")
    roll_no: Optional[str] = Field(None, description="Optional student roll number; if omitted, transitions all students in the semester")
    remarks: Optional[str] = Field(None, description="Optional transition remarks or verification notes")


class WorkflowUnlockRequest(BaseModel):
    semester_number: int = Field(..., ge=1, le=8, description="Target Semester Number (1 to 8)")
    user_role: str = Field("Admin / Sub-Dean", description="Role of administrator issuing the override")
    operator_name: str = Field("Sub-Dean Examinations", description="Name of the administrator")
    justification: str = Field(..., min_length=5, description="Mandatory justification / reason for unlocking")
    roll_no: Optional[str] = Field(None, description="Optional student roll number; if omitted, unlocks all students in the semester")
    target_status: str = Field("DRAFT", description="Status to revert to (default 'DRAFT')")


@router.get("/status/{semester}")
def get_semester_workflow_status(
    semester: int,
    batch_id: Optional[int] = Query(None, description="Optional cohort batch filter")
):
    """
    Returns workflow status summary for a semester:
    - Counts of DRAFT, SCRUTINIZED, APPROVED, LOCKED
    - Overall cohort status
    - Student-level status items
    """
    if not (1 <= semester <= 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester must be an integer between 1 and 8."
        )

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        summary = repo.get_semester_workflow_summary(semester_number=semester, batch_id=batch_id)
        return summary


@router.post("/transition")
def transition_workflow(payload: WorkflowTransitionRequest):
    """
    Transitions marksheet workflow state:
    DRAFT -> SCRUTINIZED -> APPROVED -> LOCKED

    Rules:
    - Only 'Admin / Sub-Dean' role can transition to 'APPROVED' or 'LOCKED'.
    - Scrutiny Committee can transition DRAFT -> SCRUTINIZED.
    - If marksheet is 'LOCKED', transitions are blocked (Unlock override required).
    """
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        try:
            result = repo.transition_workflow_status(
                semester_number=payload.semester_number,
                target_status=payload.target_status,
                user_role=payload.user_role,
                operator_name=payload.operator_name,
                roll_no=payload.roll_no,
                remarks=payload.remarks,
            )
            return result
        except PermissionError as pe:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(pe)
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow transition error: {str(e)}"
            )


@router.post("/unlock")
def unlock_for_reevaluation(payload: WorkflowUnlockRequest):
    """
    Administrator Override: Unlocks LOCKED marksheets for re-evaluation.
    Requires 'Admin / Sub-Dean' role and a mandatory substantive justification comment.
    Reverts status to DRAFT and logs an administrative audit entry.
    """
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        try:
            result = repo.unlock_for_reevaluation(
                semester_number=payload.semester_number,
                user_role=payload.user_role,
                operator_name=payload.operator_name,
                justification=payload.justification,
                roll_no=payload.roll_no,
                target_status=payload.target_status,
            )
            return result
        except PermissionError as pe:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(pe)
            )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unlock override error: {str(e)}"
            )


@router.get("/audit-history/{roll_no}")
def get_audit_history(roll_no: str):
    """
    Queries marks_audit_log and returns chronological history:
    [Timestamp | User / Operator | Subject / Field | Old Value | New Value | Reason / Justification]
    """
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        trail = repo.get_audit_trail_for_student(roll_no)
        return {
            "roll_no": roll_no.strip(),
            "total_records": len(trail),
            "history": trail
        }
