"""
Test for Longitudinal Sem 1-8 Final Academic Evaluation Statement calculation.
Compliant with Indian Nursing Council (INC) Gazette Regulations.
Developed at VidyaLabs | Priyanka Kumari.
"""

import pytest
from backend.cumulative_engine import (
    SemesterAcademicRecord,
    compute_final_academic_evaluation,
    determine_inc_overall_grade,
)


def test_cumulative_sem8_longitudinal_evaluation():
    credits_list = [12, 31, 17, 21, 11, 21, 26, 12]
    sgpas = [7.00, 7.45, 7.00, 6.33, 7.18, 6.19, 7.08, 10.00]
    percentages = [68.40, 75.43, 68.67, 66.29, 69.14, 63.80, 71.20, 94.50]

    records = [
        SemesterAcademicRecord(
            semester_number=i + 1,
            credits=credits_list[i],
            sgpa=sgpas[i],
            percentage=percentages[i],
            result_status="PASS",
        )
        for i in range(8)
    ]

    eval_result = compute_final_academic_evaluation(records)

    assert eval_result.is_complete is True
    assert eval_result.cgpa == 7.15
    assert eval_result.overall_percentage == 72.18
    assert eval_result.overall_grade == "B+"
    assert eval_result.grading_performance == "Good"
    assert eval_result.final_result == "PASS"


def test_grade_scale_boundaries():
    assert determine_inc_overall_grade(85.00) == ("O", "Outstanding")
    assert determine_inc_overall_grade(84.99) == ("A+", "Excellent")
    assert determine_inc_overall_grade(79.99) == ("A", "Very Good")
    assert determine_inc_overall_grade(74.99) == ("B+", "Good")
    assert determine_inc_overall_grade(64.99) == ("B", "Above Average")
    assert determine_inc_overall_grade(59.99) == ("C", "Average")
    assert determine_inc_overall_grade(49.99) == ("F", "Fail")
