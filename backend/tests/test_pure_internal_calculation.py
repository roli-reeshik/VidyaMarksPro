"""
Comprehensive Regulatory & Ingestion Isolation Unit Tests
Testing Pure In-App Calculation of Totals, Percentages, Grade Points, Letter Grades, and SGPA
Compliant with INC Gazette Corrigendum (April 19, 2022 / No. 205) and SGPGIMS Regulations.

Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import pytest
from backend.evaluation_engine import evaluate_student_semester, STATUTORY_SGPA_CREDITS
from backend.grading import (
    calculate_inc_grade,
    compute_sgpa,
    evaluate_student_semester as grading_evaluate_student_semester,
    STATUTORY_SGPA_CREDITS as GRADING_STATUTORY_CREDITS
)
from backend.schemas.canonical_models import StudentRecord


def test_statutory_credits_all_semesters_compliance():
    """
    Verifies statutory SGPA credits for Semesters 1 through 8
    as mandated by the INC Gazette Corrigendum (April 19, 2022 / No. 205).
    """
    expected_credits = {
        1: 12,
        2: 31,
        3: 17,
        4: 21,
        5: 11,
        6: 21,
        7: 26,
        8: 12,
    }
    assert STATUTORY_SGPA_CREDITS == expected_credits
    assert GRADING_STATUTORY_CREDITS == expected_credits


def test_ingestion_isolation_corrupted_sheet_total_ignored():
    """
    Test Case: Corrupted Sheet Total (e.g. IA = 17, EA = 49, Sheet Total = 49).
    The Ingestion Isolation Rule dictates that the system must strictly compute:
      Total = IA (17) + EA (49) = 66.0
      Percentage = (66.0 / 100.0) * 100 = 66.0%
      Grade = B+ (Grade Point: 7)
    Pre-calculated sheet total 49.0 MUST BE IGNORED.
    """
    student_payload = {
        "roll_no": "202501001",
        "enroll_no": "2025001",
        "student_name": "CORRUPTED TOTAL TEST CANDIDATE",
        "father_name": "MR. FATHER",
        "semester_number": 3,
        "courses": {
            "AHN_I_THEORY": {
                "course_code": "N-AHN (I) 215",
                "course_title": "Adult Health Nursing I (Theory)",
                "int_marks": 17.0,
                "ex_marks": 49.0,
                "total": 49.0,  # Corrupted sheet total matching Column 13 (Ex. 75)!
                "grace": 0.0,
                "credits": 7,
                "include_in_sgpa": True,
            },
            "AHN_I_PRACT": {
                "course_code": "N-AHN (I) 215",
                "course_title": "Adult Health Nursing I (Practical)",
                "int_marks": 35.0,
                "ex_marks": 35.0,
                "total": 999.0,  # Fictitious absurd sheet total
                "grace": 0.0,
                "credits": 7,
                "include_in_sgpa": True,
            },
            "MICR": {
                "course_code": "MICR 201",
                "course_title": "Applied Microbiology and Infection Control",
                "int_marks": 18.0,
                "ex_marks": 52.0,
                "total": 0.0,  # Zero sheet total
                "grace": 0.0,
                "credits": 3,
                "include_in_sgpa": True,
            }
        }
    }

    result = evaluate_student_semester(student_payload, semester_number=3)

    # 1. AHN_I_THEORY isolation
    ahn_th = result.courses["AHN_I_THEORY"]
    assert ahn_th["total_obtained"] == 66.0, f"Expected 66.0, got {ahn_th['total_obtained']}"
    assert ahn_th["percentage"] == 66.0
    assert ahn_th["letter_grade"] == "B+"
    assert ahn_th["grade_point"] == 7
    assert ahn_th["credit_points"] == 49.0  # 7 credits * 7 GP

    # 2. AHN_I_PRACT isolation
    ahn_pr = result.courses["AHN_I_PRACT"]
    assert ahn_pr["total_obtained"] == 70.0  # 35 + 35
    assert ahn_pr["percentage"] == 70.0
    assert ahn_pr["letter_grade"] == "B+"
    assert ahn_pr["grade_point"] == 7
    assert ahn_pr["credit_points"] == 49.0  # 7 credits * 7 GP

    # 3. MICR isolation
    micr = result.courses["MICR"]
    assert micr["total_obtained"] == 70.0  # 18 + 52
    assert micr["percentage"] == 70.0
    assert micr["letter_grade"] == "B+"
    assert micr["grade_point"] == 7
    assert micr["credit_points"] == 21.0  # 3 credits * 7 GP

    # 4. Semester Summary & SGPA (Sem 3 = 17 statutory credits)
    assert result.total_sgpa_credits == 17
    assert result.total_credit_score == (49.0 + 49.0 + 21.0)  # 119.0
    assert result.sgpa == round(119.0 / 17, 2)  # 7.0
    assert result.grand_total_obtained == (66.0 + 70.0 + 70.0)  # 206.0
    assert result.result_status == "PASS"
    assert len(result.backlog_queue) == 0


def test_missing_sheet_total_pure_in_app_calculation():
    """
    Test Case: Sheet Total completely omitted or None.
    In-app calculation derives exact pure component totals and grades.
    """
    raw_data = {
        "roll_no": "202501002",
        "student_name": "OMITTED TOTAL CANDIDATE",
        "semester": 1,
        "courses": {
            "ANAT_PHYS": {"int_marks": 20.0, "ex_part_a": 30.0, "ex_part_b": 30.0, "ex_total": 60.0},
            "SOCI_PSYC": {"int_marks": 19.0, "ex_total": 56.0},
            "ENGL": {"int_marks": 15.0, "ex_marks": 15.0}
        }
    }

    result = grading_evaluate_student_semester(raw_data)

    assert result.courses["ANAT_PHYS"]["total_obtained"] == 80.0
    assert result.courses["ANAT_PHYS"]["letter_grade"] == "A+"
    assert result.courses["ANAT_PHYS"]["grade_point"] == 9

    assert result.courses["SOCI_PSYC"]["total_obtained"] == 75.0
    assert result.courses["SOCI_PSYC"]["letter_grade"] == "A"
    assert result.courses["SOCI_PSYC"]["grade_point"] == 8

    assert result.courses["ENGL"]["total_obtained"] == 30.0
    assert result.courses["ENGL"]["letter_grade"] == "B"
    assert result.courses["ENGL"]["grade_point"] == 6

    # Sem 1 = 12 statutory credits (English excluded from SGPA)
    # Credit score = (6 * 9) + (6 * 8) = 54 + 48 = 102
    assert result.total_sgpa_credits == 12
    assert result.total_credit_score == 102.0
    assert result.sgpa == 8.5  # 102 / 12
    assert result.result_status == "PASS"


def test_english_and_elective_pass_threshold_and_p_grade_law():
    """
    Tests INC Gazette Law:
    1. Communicative English (ENGL 101) & Electives pass at 40% (Grade P, GP 4)
       and are EXCLUDED from SGPA calculation.
    2. Core courses fail below 50% and CAN NEVER receive Grade 'P'.
    """
    student_data = {
        "roll_no": "202501003",
        "student_name": "GRADE P VERIFICATION",
        "semester_number": 1,
        "courses": {
            "ANAT_PHYS": {
                "int_marks": 12.5,
                "ex_total": 35.0,  # Below 37.5 EA pass threshold -> Fail!
                "credits": 6,
            },
            "SOCI_PSYC": {
                "int_marks": 15.0,
                "ex_total": 45.0,  # Total = 60.0 -> Grade B (GP 6)
                "credits": 6,
            },
            "ENGL": {
                "int_marks": 10.0,
                "ex_marks": 11.0,  # Total = 21/50 (42%) -> Passes at 40% -> Grade P (GP 4)
                "credits": 2,
            }
        }
    }

    result = evaluate_student_semester(student_data)

    # English: 42% -> Grade P, GP 4, is_pass=True, include_in_sgpa=False
    engl = result.courses["ENGL"]
    assert engl["percentage"] == 42.0
    assert engl["letter_grade"] == "P"
    assert engl["grade_point"] == 4
    assert engl["is_pass"] is True
    assert engl["include_in_sgpa"] is False

    # ANAT_PHYS: failed threshold -> Grade F, GP 0, is_pass=False, NEVER 'P'
    anat = result.courses["ANAT_PHYS"]
    assert anat["letter_grade"] == "F"
    assert anat["grade_point"] == 0
    assert anat["is_pass"] is False

    # Overall result status
    assert result.result_status == "FAIL"
    assert len(result.backlog_queue) == 1
    assert result.backlog_queue[0]["course_code"] == "ANAT 105 & PHYS 110"
    assert result.backlog_queue[0]["backlog_status"] == "ACTIVE"


def test_sem4_three_part_subcomponent_pure_derivation():
    """
    Tests Semester 4 Archetype C (3-Part Subcomponent Split):
    Pharmacology (Ex. 38) + Pathology (Ex. 25) + Genetics (Ex. 12) = 75 EA.
    Derives total purely from subcomponents + IA.
    """
    sem4_data = {
        "roll_no": "202504001",
        "student_name": "SEM 4 CANDIDATE",
        "semester_number": 4,
        "courses": {
            "PHAR_PATH": {
                "int_marks": 20.0,
                "ex_part_a": 28.0,  # Pharmacology
                "ex_part_b": 18.0,  # Pathology
                "ex_part_c": 9.0,   # Genetics
                # Note: ex_total omitted!
                "credits": 6
            },
            "AHN_II_THEORY": {
                "int_marks": 20.0,
                "ex_total": 55.0,
                "credits": 7
            },
            "AHN_II_PRACT": {
                "int_marks": 40.0,
                "ex_total": 42.0,
                "credits": 7
            },
            "PROF": {
                "int_marks": 20.0,
                "ex_marks": 20.0,
                "credits": 1
            }
        }
    }

    result = evaluate_student_semester(sem4_data)

    phar = result.courses["PHAR_PATH"]
    # EA = 28 + 18 + 9 = 55.0
    # Total = 20.0 + 55.0 = 75.0
    assert phar["external_obtained"] == 55.0
    assert phar["total_obtained"] == 75.0
    assert phar["percentage"] == 75.0
    assert phar["letter_grade"] == "A"
    assert phar["grade_point"] == 8

    # Sem 4 statutory SGPA credits = 21
    assert result.total_sgpa_credits == 21
    assert result.result_status == "PASS"
    assert len(result.backlog_queue) == 0


def test_automated_backlog_queuing_on_failing_grade():
    """
    Verifies that any student receiving Grade 'F' or failing any course
    is automatically queued into the backlog queue with appropriate deficit metadata.
    """
    failing_candidate = {
        "roll_no": "202502042",
        "student_name": "BACKLOG TEST CANDIDATE",
        "semester": 2,
        "courses": {
            "BIOC_NUTR": {"int_marks": 18.0, "ex_marks": 45.0, "credits": 5},
            "NNF_THEORY": {"int_marks": 11.0, "ex_marks": 32.0, "credits": 12},  # Both IA (11 < 12.5) & EA (32 < 37.5) failed!
            "NNF_PRACT": {"int_marks": 40.0, "ex_marks": 40.0, "credits": 11},
            "HNIT": {"int_marks": 20.0, "ex_marks": 20.0, "credits": 3}
        }
    }

    result = evaluate_student_semester(failing_candidate)

    assert result.result_status == "FAIL"
    assert len(result.failed_courses) == 1
    assert len(result.backlog_queue) == 1

    bl = result.backlog_queue[0]
    assert bl["course_code"] == "N-NF (I & II) 125"
    assert bl["backlog_status"] == "ACTIVE"
    assert bl["semester_number"] == 2
    assert bl["failed_component"] == "Both IA and EA"
    assert bl["deficit_marks"] > 0.0
