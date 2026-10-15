"""
FastAPI Route for Core Evaluation Engine (/api/evaluation)
Phase 2: Evaluates normalized StudentRecord data into 10-Point Grades, Grace Marks, and SGPA.
Branding: VidyaMarksheet by VidyaLabs
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from backend.schemas.canonical_models import StudentRecord
from backend.evaluation_engine import (
    EvaluationEngine,
    EvaluatedStudentRecord,
    EvaluationBatchResult
)

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation Engine"])


@router.post("/batch", response_model=EvaluationBatchResult)
def evaluate_student_batch(
    records: List[StudentRecord],
    semester: int = Query(default=1, ge=1, le=8, description="Target Semester number"),
    auto_grace: bool = Query(default=False, description="Enable auto-grace calculation mode")
):
    """
    Evaluates an array of normalized StudentRecord objects:
    - Verifies INC passing thresholds (IA >= 50%, EA >= 50%, Total >= 50%, English >= 40%)
    - Verifies pre-specified grace marks or calculates auto-grace (deficit <= 5.0)
    - Computes 10-point letter grades, grade points, and semester credit scores
    - Computes statutory SGPA rounded to 2 decimal places.
    """
    try:
        engine = EvaluationEngine(semester_number=semester, auto_grace=auto_grace)
        result = engine.evaluate_batch(records)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error evaluating student batch: {str(e)}"
        )


@router.post("/student", response_model=EvaluatedStudentRecord)
def evaluate_single_student(
    student: StudentRecord,
    semester: int = Query(default=1, ge=1, le=8),
    auto_grace: bool = Query(default=False)
):
    """Evaluates a single candidate StudentRecord."""
    try:
        engine = EvaluationEngine(semester_number=semester, auto_grace=auto_grace)
        return engine.evaluate_student(student)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error evaluating student: {str(e)}"
        )
