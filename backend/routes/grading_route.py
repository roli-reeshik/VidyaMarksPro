"""
FastAPI Route for Live INC Grade Calculation Engine
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.grading import calculate_inc_grade, GradeResult

router = APIRouter(prefix="/api/grade", tags=["Grading Engine"])


@router.get("/calculate", response_model=GradeResult)
def calculate_grade_endpoint(
    obtained: Optional[float] = Query(None, description="Marks obtained"),
    max_marks: float = Query(100.0, gt=0, description="Maximum marks for the component"),
    is_english_or_elective: bool = Query(False, description="Whether this is Communicative English or an Elective module"),
    is_absent: bool = Query(False, description="Whether student was absent")
):
    """
    Computes INC 10-Point Grade, Grade Point, Pass/Fail status,
    and performance description for any given score.
    """
    return calculate_inc_grade(
        obtained_marks=obtained,
        max_marks=max_marks,
        is_english_or_elective=is_english_or_elective,
        is_absent=is_absent
    )
