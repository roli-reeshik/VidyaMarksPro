"""
Unit Tests for INC 10-Point Grading Scale Engine
"""

import pytest
from backend.grading import calculate_inc_grade, compute_sgpa


def test_outstanding_grade():
    res = calculate_inc_grade(85.0, 100.0)
    assert res.letter_grade == "O"
    assert res.grade_point == 10
    assert res.is_pass is True

    res2 = calculate_inc_grade(95.0, 100.0)
    assert res2.letter_grade == "O"
    assert res2.grade_point == 10


def test_excellent_grade():
    res = calculate_inc_grade(84.99, 100.0)
    assert res.letter_grade == "A+"
    assert res.grade_point == 9
    assert res.is_pass is True

    res2 = calculate_inc_grade(80.0, 100.0)
    assert res2.letter_grade == "A+"
    assert res2.grade_point == 9


def test_very_good_grade():
    res = calculate_inc_grade(79.9, 100.0)
    assert res.letter_grade == "A"
    assert res.grade_point == 8
    assert res.is_pass is True

    res2 = calculate_inc_grade(75.0, 100.0)
    assert res2.letter_grade == "A"
    assert res2.grade_point == 8


def test_good_grade():
    res = calculate_inc_grade(74.9, 100.0)
    assert res.letter_grade == "B+"
    assert res.grade_point == 7
    assert res.is_pass is True

    res2 = calculate_inc_grade(65.0, 100.0)
    assert res2.letter_grade == "B+"
    assert res2.grade_point == 7


def test_above_average_grade():
    res = calculate_inc_grade(64.5, 100.0)
    assert res.letter_grade == "B"
    assert res.grade_point == 6
    assert res.is_pass is True

    res2 = calculate_inc_grade(60.0, 100.0)
    assert res2.letter_grade == "B"
    assert res2.grade_point == 6


def test_average_pass_grade():
    res = calculate_inc_grade(59.9, 100.0)
    assert res.letter_grade == "C"
    assert res.grade_point == 5
    assert res.is_pass is True

    res2 = calculate_inc_grade(50.0, 100.0)
    assert res2.letter_grade == "C"
    assert res2.grade_point == 5


def test_pass_grade_strictly_restricted():
    # In standard courses, 40-49.99% MUST BE F (Fail)!
    res_standard = calculate_inc_grade(45.0, 100.0, is_english_or_elective=False)
    assert res_standard.letter_grade == "F"
    assert res_standard.grade_point == 0
    assert res_standard.is_pass is False

    # In Communicative English or Electives, 40-49.99% IS P (Pass with 4 grade points)!
    res_english = calculate_inc_grade(22.0, 50.0, is_english_or_elective=True)  # 44%
    assert res_english.letter_grade == "P"
    assert res_english.grade_point == 4
    assert res_english.is_pass is True


def test_fail_grades():
    # Standard course below 50%
    res = calculate_inc_grade(49.9, 100.0, is_english_or_elective=False)
    assert res.letter_grade == "F"
    assert res.grade_point == 0
    assert res.is_pass is False

    # English below 40%
    res2 = calculate_inc_grade(19.0, 50.0, is_english_or_elective=True)  # 38%
    assert res2.letter_grade == "F"
    assert res2.grade_point == 0
    assert res2.is_pass is False


def test_absent():
    res = calculate_inc_grade(None, 100.0, is_absent=True)
    assert res.letter_grade == "Ab"
    assert res.grade_point == 0
    assert res.is_pass is False


def test_sgpa_computation():
    # Sample semester 1 courses:
    # 1. Communicative English: 2 credits, Grade B (6), include_in_sgpa=False
    # 2. Applied Anatomy & Phys: 6 credits, Grade B+ (7), include_in_sgpa=True
    # 3. Applied Sociology & Psyc: 6 credits, Grade A (8), include_in_sgpa=True
    evals = [
        {"credits": 2, "grade_point": 6, "include_in_sgpa": False},
        {"credits": 6, "grade_point": 7, "include_in_sgpa": True},
        {"credits": 6, "grade_point": 8, "include_in_sgpa": True},
    ]
    sgpa, score, total_credits = compute_sgpa(evals)
    # Total points = (6*7) + (6*8) = 42 + 48 = 90
    # Eligible credits = 12
    # SGPA = 90 / 12 = 7.5
    assert total_credits == 12
    assert score == 90.0
    assert sgpa == 7.5
