"""
Unit & Regulatory Tests for Evaluation Engine (Phase 2)
Compliant with INC Gazette & SGPGIMS Lucknow Regulations
Branding: VidyaMarksheet by VidyaLabs
"""

import os
import pytest
from backend.schemas.canonical_models import StudentRecord
from backend.evaluation_engine import EvaluationEngine
from backend.parsers.exam_cell_parser import ExamCellParserAdapter

DATA_SHEET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "VidyaMarksheet_Master_DataSheet.xlsx")


def test_standard_passing_thresholds():
    engine = EvaluationEngine(semester_number=1)

    # Student meeting exact 50% cutoffs:
    # IA: 12.5 / 25 (50%), EA: 37.5 / 75 (50%), Total: 50.0 / 100 (50%)
    bare_pass_student = StudentRecord(
        roll_no="202501099",
        enroll_no="2025700",
        student_name="BARE PASS CANDIDATE",
        father_name="FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 12.5,
                "ex_part_a": 18.5,
                "ex_part_b": 19.0,
                "ex_total": 37.5,
                "grace": 0,
                "total": 50.0
            },
            "SOCI_PSYC": {
                "int_marks": 15, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 55
            },
            "ENGL": {
                "int_marks": 10, "ex_marks": 10, "total": 20
            }
        },
        raw_remarks="PASS"
    )

    evaluated = engine.evaluate_student(bare_pass_student)
    anat = evaluated.courses["ANAT_PHYS"]
    assert anat.internal_pass is True
    assert anat.external_pass is True
    assert anat.aggregate_pass is True
    assert anat.is_pass is True
    assert anat.letter_grade == "C"
    assert anat.grade_point == 5
    assert evaluated.result_status == "PASS"


def test_english_pass_threshold_and_p_grade_restriction():
    engine = EvaluationEngine(semester_number=1)

    # English scored 42% (21/50) -> Must receive 'P' (Grade Point: 4)
    # Standard course scored 45% (45/100) -> Must receive 'F' (Grade Point: 0), NEVER 'P'!
    candidate = StudentRecord(
        roll_no="202501098",
        enroll_no="2025701",
        student_name="GRADE P TEST",
        father_name="FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 15,
                "ex_part_a": 15,
                "ex_part_b": 15,
                "ex_total": 30,  # Below 37.5 -> Fail
                "grace": 0,
                "total": 45  # 45% in standard course -> F (0)
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 60
            },
            "ENGL": {
                "int_marks": 10,
                "ex_marks": 11,
                "total": 21  # 42% in English -> P (4)
            }
        },
        raw_remarks="FAIL"
    )

    evaluated = engine.evaluate_student(candidate)
    engl = evaluated.courses["ENGL"]
    assert engl.letter_grade == "P"
    assert engl.grade_point == 4
    assert engl.is_pass is True
    assert engl.include_in_sgpa is False

    anat = evaluated.courses["ANAT_PHYS"]
    assert anat.letter_grade == "F"
    assert anat.grade_point == 0
    assert anat.is_pass is False


def test_prespecified_grace_verification():
    engine = EvaluationEngine(semester_number=1)
    # Aditya with 35 + 2.5 = 37.5
    aditya = StudentRecord(
        roll_no="202501002",
        enroll_no="2025630",
        student_name="ADITYA KUMAR KATHERIYA",
        father_name="VIJAY KUMAR",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20, "ex_part_a": 19, "ex_part_b": 20, "ex_total": 39, "grace": 0, "total": 59
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 15, "ex_total": 35, "grace": 2.5, "total": 57.5
            },
            "ENGL": {
                "int_marks": 21, "ex_marks": 23, "total": 44
            }
        },
        raw_remarks="PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY"
    )

    evaluated = engine.evaluate_student(aditya)
    soci = evaluated.courses["SOCI_PSYC"]
    assert soci.is_pass is True
    assert soci.grace_awarded == 2.5
    assert soci.effective_external == 37.5
    assert soci.total_marks == 57.5
    assert soci.letter_grade == "C"
    assert soci.grade_point == 5
    assert evaluated.sgpa == 5.0
    assert evaluated.result_status == "PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY"


def test_auto_grace_calculation_mode():
    # Enable auto_grace mode: candidate has raw 35 (deficit 2.5 <= 5.0) and grace=0 in sheet
    engine = EvaluationEngine(semester_number=1, auto_grace=True)
    candidate = StudentRecord(
        roll_no="202501088",
        enroll_no="2025720",
        student_name="AUTO GRACE CANDIDATE",
        father_name="FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 60
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 15, "ex_total": 35, "grace": 0, "total": 55
            },
            "ENGL": {
                "int_marks": 20, "ex_marks": 20, "total": 40
            }
        },
        raw_remarks="NEEDS EVALUATION"
    )

    evaluated = engine.evaluate_student(candidate)
    soci = evaluated.courses["SOCI_PSYC"]
    assert soci.is_pass is True
    assert soci.grace_awarded == 2.5
    assert soci.effective_external == 37.5
    assert soci.total_marks == 57.5
    assert evaluated.result_status == "PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY"
    assert evaluated.sgpa == 5.5  # (6*6 + 6*5) / 12 = 66 / 12 = 5.5


def test_auto_grace_rejected_if_multiple_subjects_fail():
    # Candidate fails both ANAT and SOCI -> Ineligible for auto grace!
    engine = EvaluationEngine(semester_number=1, auto_grace=True)
    candidate = StudentRecord(
        roll_no="202501087",
        enroll_no="2025721",
        student_name="MULTIPLE FAIL CANDIDATE",
        father_name="FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20, "ex_part_a": 15, "ex_part_b": 15, "ex_total": 30, "grace": 0, "total": 50
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 15, "ex_total": 35, "grace": 0, "total": 55
            },
            "ENGL": {
                "int_marks": 20, "ex_marks": 20, "total": 40
            }
        },
        raw_remarks="FAIL"
    )

    evaluated = engine.evaluate_student(candidate)
    assert evaluated.result_status == "FAIL"
    assert len(evaluated.failed_courses) == 2


def test_master_datasheet_batch_evaluation():
    with open(DATA_SHEET_PATH, "rb") as f:
        adapter = ExamCellParserAdapter(f.read())
        students = adapter.parse()

    engine = EvaluationEngine(semester_number=1)
    batch_res = engine.evaluate_batch(students)

    assert batch_res.total_candidates == 3
    assert batch_res.passed_count == 2
    assert batch_res.failed_count == 1
    assert batch_res.grace_awarded_count == 1

    # Student 1: Aditi Sharma -> 7.0 SGPA
    aditi = next(r for r in batch_res.results if r.roll_no == "202501001")
    assert aditi.sgpa == 7.0
    assert aditi.result_status == "PASS"

    # Student 2: Aditya -> 5.0 SGPA with 2.5 grace
    aditya = next(r for r in batch_res.results if r.roll_no == "202501002")
    assert aditya.sgpa == 5.0
    assert "2.5 GRACE" in aditya.result_status

    # Student 3: Vansh -> Fail
    vansh = next(r for r in batch_res.results if r.roll_no == "202501064")
    assert vansh.result_status == "FAIL"
    assert vansh.sgpa == 0.0
