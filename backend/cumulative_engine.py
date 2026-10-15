"""
Longitudinal Cumulative Academic Summary Engine for B.Sc. Nursing (Semesters 1 through 8).
Compliant with Indian Nursing Council (INC) Gazette Regulations & SGPGIMS Lucknow Regulations.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

# Prescribed SGPA credits per semester under INC Gazette Regulations (Total = 151.0)
PRESCRIBED_SEMESTER_CREDITS: Dict[int, float] = {
    1: 12.0,  # 14 total - 2 (ENGL 101 College Exam) = 12.0 SGPA credits
    2: 31.0,
    3: 17.0,
    4: 21.0,
    5: 11.0,
    6: 21.0,
    7: 26.0,
    8: 12.0,
}

TOTAL_PROGRAM_CREDITS: float = 151.0


class SemesterAcademicRecord(BaseModel):
    semester_number: int = Field(..., ge=1, le=8)
    credits: float
    sgpa: float
    percentage: float
    result_status: str = "PASS"  # 'PASS', 'PASS WITH GRACE', 'FAIL'


class FinalAcademicEvaluationStatement(BaseModel):
    semesters: List[SemesterAcademicRecord] = []
    total_credits: float = TOTAL_PROGRAM_CREDITS
    cgpa: float
    overall_percentage: float
    overall_grade: str
    grading_performance: str
    final_result: str  # 'PASS' or 'FAIL'
    is_complete: bool = False


def determine_inc_overall_grade(overall_percentage: float) -> Tuple[str, str]:
    """
    Determines Letter Grade and Qualitative Grading Performance according to the INC 10-Point Scale:
    - >= 85.00%: O (Outstanding)
    - 80.00% - 84.99%: A+ (Excellent)
    - 75.00% - 79.99%: A (Very Good)
    - 65.00% - 74.99%: B+ (Good)
    - 60.00% - 64.99%: B (Above Average)
    - 50.00% - 59.99%: C (Average)
    - < 50.00%: F (Fail)
    """
    pct = round(overall_percentage, 2)
    if pct >= 85.00:
        return "O", "Outstanding"
    elif pct >= 80.00:
        return "A+", "Excellent"
    elif pct >= 75.00:
        return "A", "Very Good"
    elif pct >= 65.00:
        return "B+", "Good"
    elif pct >= 60.00:
        return "B", "Above Average"
    elif pct >= 50.00:
        return "C", "Average"
    else:
        return "F", "Fail"


def compute_final_academic_evaluation(
    records: List[SemesterAcademicRecord]
) -> FinalAcademicEvaluationStatement:
    """
    Computes the Longitudinal Final Academic Evaluation Statement across Semesters 1 to 8:
    - CGPA = Sum(Credits_i * SGPA_i) / 151.0 (rounded to 2 decimal places)
    - Overall Percentage = Sum(Percentages_i) / 8.0 (rounded to 2 decimal places)
    - Overall Letter Grade & Grading Performance per INC scale
    - Final Result = 'PASS' if all 8 semesters passed, 'FAIL' if any pending backlogs
    """
    # Sort by semester number 1 through 8
    sorted_records = sorted(records, key=lambda r: r.semester_number)
    
    # Check for backlogs
    has_backlog = any("FAIL" in r.result_status.upper() for r in sorted_records)
    is_complete = len(sorted_records) == 8

    # Sum of Credits * SGPA
    total_credit_points = sum(r.credits * r.sgpa for r in sorted_records)
    divisor_credits = TOTAL_PROGRAM_CREDITS if is_complete else max(1.0, sum(r.credits for r in sorted_records))
    cgpa = round(total_credit_points / divisor_credits, 2)

    # Average of semester percentages
    divisor_count = 8.0 if is_complete else max(1.0, float(len(sorted_records)))
    overall_percentage = round(sum(r.percentage for r in sorted_records) / divisor_count, 2)

    letter_grade, performance = determine_inc_overall_grade(overall_percentage)
    
    if is_complete and not has_backlog:
        final_result = "PASS"
    else:
        final_result = "FAIL" if has_backlog else "IN PROGRESS"

    return FinalAcademicEvaluationStatement(
        semesters=sorted_records,
        total_credits=TOTAL_PROGRAM_CREDITS,
        cgpa=cgpa,
        overall_percentage=overall_percentage,
        overall_grade=letter_grade,
        grading_performance=performance,
        final_result=final_result,
        is_complete=is_complete,
    )
