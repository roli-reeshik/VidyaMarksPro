"""
INC 10-Point Grading Scale Engine
Compliant with Indian Nursing Council (INC) Gazette and SGPGIMS Lucknow Regulations.
"""

from typing import Optional, Tuple
from pydantic import BaseModel, Field


class GradeResult(BaseModel):
    letter_grade: str = Field(..., description="Letter Grade (O, A+, A, B+, B, C, P, F, Ab)")
    grade_point: int = Field(..., description="Grade Point (0-10)")
    is_pass: bool = Field(..., description="Whether candidate met the passing threshold")
    performance_description: str = Field(..., description="INC qualitative performance descriptor")
    percentage: float = Field(..., description="Calculated percentage rounded to 2 decimal places")


def calculate_inc_grade(
    obtained_marks: Optional[float],
    max_marks: float,
    is_english_or_elective: bool = False,
    is_absent: bool = False,
    has_failed_threshold: bool = False
) -> GradeResult:
    """
    Computes INC 10-Point Grade based on:
      85.00% & Above             -> O   (10) - Outstanding
      80.00% to 84.99%           -> A+  (9)  - Excellent
      75.00% to 79.99%           -> A   (8)  - Very Good
      65.00% to 74.99%           -> B+  (7)  - Good
      60.00% to 64.99%           -> B   (6)  - Above Average
      50.00% to 59.99%           -> C   (5)  - Pass / Average
      40.00% to 49.99%           -> P   (4)  - Pass (Restricted STRICTLY to Communicative English and Electives)
      < 50.00% (<40% for Eng/El) -> F   (0)  - Fail
      Absent                     -> Ab  (0)  - Absent
    """
    if is_absent or obtained_marks is None:
        return GradeResult(
            letter_grade="Ab",
            grade_point=0,
            is_pass=False,
            performance_description="Absent",
            percentage=0.0
        )

    if max_marks <= 0:
        return GradeResult(
            letter_grade="F",
            grade_point=0,
            is_pass=False,
            performance_description="Invalid Max Marks",
            percentage=0.0
        )

    # Use standard 2-decimal rounded percentage
    percentage = round((obtained_marks / max_marks) * 100.0, 2)

    if has_failed_threshold:
        return GradeResult(
            letter_grade="F",
            grade_point=0,
            is_pass=False,
            performance_description="Fail (Threshold not met)",
            percentage=percentage
        )

    if percentage >= 85.00:
        return GradeResult(
            letter_grade="O",
            grade_point=10,
            is_pass=True,
            performance_description="Outstanding",
            percentage=percentage
        )
    elif percentage >= 80.00:
        return GradeResult(
            letter_grade="A+",
            grade_point=9,
            is_pass=True,
            performance_description="Excellent",
            percentage=percentage
        )
    elif percentage >= 75.00:
        return GradeResult(
            letter_grade="A",
            grade_point=8,
            is_pass=True,
            performance_description="Very Good",
            percentage=percentage
        )
    elif percentage >= 65.00:
        return GradeResult(
            letter_grade="B+",
            grade_point=7,
            is_pass=True,
            performance_description="Good",
            percentage=percentage
        )
    elif percentage >= 60.00:
        return GradeResult(
            letter_grade="B",
            grade_point=6,
            is_pass=True,
            performance_description="Above Average",
            percentage=percentage
        )
    elif percentage >= 50.00:
        return GradeResult(
            letter_grade="C",
            grade_point=5,
            is_pass=True,
            performance_description="Average",
            percentage=percentage
        )
    elif 40.00 <= percentage < 50.00:
        if is_english_or_elective:
            return GradeResult(
                letter_grade="P",
                grade_point=4,
                is_pass=True,
                performance_description="Pass",
                percentage=percentage
            )
        else:
            # Standard courses fail below 50% - strictly no 'P' grade allowed
            return GradeResult(
                letter_grade="F",
                grade_point=0,
                is_pass=False,
                performance_description="Fail",
                percentage=percentage
            )
    else:  # percentage < 40.00
        return GradeResult(
            letter_grade="F",
            grade_point=0,
            is_pass=False,
            performance_description="Fail",
            percentage=percentage
        )


def compute_sgpa(course_evaluations: list[dict]) -> Tuple[float, float, int]:
    """
    Computes SGPA and total credit score.
    Returns: (sgpa, total_credit_score, total_eval_credits)
    Courses where `include_in_sgpa` is False are omitted from SGPA computation.
    """
    total_credit_points = 0.0
    total_credits = 0

    for item in course_evaluations:
        credits = item.get("credits", 0)
        grade_point = item.get("grade_point", 0)
        include_in_sgpa = item.get("include_in_sgpa", True)

        if include_in_sgpa and credits > 0:
            total_credits += credits
            total_credit_points += credits * grade_point

    if total_credits == 0:
        return 0.0, 0.0, 0

    sgpa = round(total_credit_points / total_credits, 2)
    return sgpa, round(total_credit_points, 2), total_credits


STATUTORY_SGPA_CREDITS = {
    1: 12,
    2: 31,
    3: 17,
    4: 21,
    5: 11,
    6: 21,
    7: 26,
    8: 12,
}


def evaluate_student_semester(*args, **kwargs):
    """
    Standardized In-App Re-Calculation Pipeline for B.Sc. Nursing Semesters 1 to 8.
    Delegates to backend.evaluation_engine.evaluate_student_semester.
    """
    from backend.evaluation_engine import evaluate_student_semester as _eval
    return _eval(*args, **kwargs)

