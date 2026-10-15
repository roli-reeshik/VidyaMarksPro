"""
Unit & Invariance Tests for Quality Audit Gate Engine (Phase 3)
Branding: VidyaMarksheet by VidyaLabs
"""

import os
import pytest
from backend.schemas.canonical_models import StudentRecord
from backend.audit_engine import QualityAuditGate, QualityAuditReport
from backend.parsers.exam_cell_parser import ExamCellParserAdapter

DATA_SHEET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "VidyaMarksheet_Master_DataSheet.xlsx")


def test_clean_student_passes_audit():
    gate = QualityAuditGate(semester_number=1)
    clean_student = StudentRecord(
        roll_no="202501001",
        enroll_no="2025629",
        student_name="ADITI SHARMA",
        father_name="SATISH KUMAR SHARMA",
        courses={
            "ANAT_PHYS": {
                "int_marks": 19,
                "ex_part_a": 24,
                "ex_part_b": 27,
                "ex_total": 51,
                "grace": 0,
                "total": 70
            },
            "SOCI_PSYC": {
                "int_marks": 19,
                "ex_part_a": 31,
                "ex_part_b": 17,
                "ex_total": 48,
                "grace": 0,
                "total": 67
            },
            "ENGL": {
                "int_marks": 21,
                "ex_marks": 24,
                "total": 45
            }
        },
        raw_remarks="PASS"
    )

    report = gate.audit_batch([clean_student])
    assert report.is_valid is True
    assert report.can_export_pdf is True
    assert report.critical_errors_count == 0
    assert report.clean_candidates == 1
    assert len(report.anomalies) == 0


def test_arithmetic_invariance_subcomponent_mismatch():
    gate = QualityAuditGate(semester_number=1)
    # Part A (24) + Part B (27) == 51, but ex_total is set to 55 (faulty entry)
    buggy_student = StudentRecord(
        roll_no="202501002",
        enroll_no="2025630",
        student_name="TEST STUDENT",
        father_name="TEST FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20,
                "ex_part_a": 24,
                "ex_part_b": 27,
                "ex_total": 55,  # Mismatch! 24 + 27 != 55
                "grace": 0,
                "total": 75
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 60
            },
            "ENGL": {
                "int_marks": 20, "ex_marks": 20, "total": 40
            }
        },
        raw_remarks="PASS"
    )

    report = gate.audit_batch([buggy_student])
    assert report.is_valid is False
    assert report.can_export_pdf is False
    assert any("Subcomponent Parity" in a.field for a in report.anomalies)


def test_arithmetic_invariance_course_total_sum_mismatch():
    gate = QualityAuditGate(semester_number=1)
    # IA (20) + EA (50) == 70, but total is given as 75
    buggy_student = StudentRecord(
        roll_no="202501003",
        enroll_no="2025631",
        student_name="TEST STUDENT 2",
        father_name="TEST FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20,
                "ex_part_a": 25,
                "ex_part_b": 25,
                "ex_total": 50,
                "grace": 0,
                "total": 75  # Mismatch! 20 + 50 = 70 != 75
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 60
            },
            "ENGL": {
                "int_marks": 20, "ex_marks": 20, "total": 40
            }
        },
        raw_remarks="PASS"
    )

    report = gate.audit_batch([buggy_student])
    assert report.is_valid is False
    assert any("Total Sum Parity" in a.field for a in report.anomalies)


def test_grace_policy_audit_exceeding_5_marks_cap():
    gate = QualityAuditGate(semester_number=1)
    # Student awarded 6.0 grace marks (exceeds INC statutory 5.0 marks cap)
    greedy_grace_student = StudentRecord(
        roll_no="202501004",
        enroll_no="2025632",
        student_name="EXCESS GRACE CANDIDATE",
        father_name="TEST FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 60
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 15, "ex_part_b": 16, "ex_total": 31.5, "grace": 6.0, "total": 57.5
            },
            "ENGL": {
                "int_marks": 20, "ex_marks": 20, "total": 40
            }
        },
        raw_remarks="PASS WITH 6.0 GRACE MARKS"
    )

    report = gate.audit_batch([greedy_grace_student])
    assert report.is_valid is False
    assert any("Statutory Grace Cap" in a.field for a in report.anomalies)


def test_grace_policy_audit_grade_inflation():
    gate = QualityAuditGate(semester_number=1)
    # Raw EA is 45 (already passing >= 37.5), but grace of 2.0 is awarded
    inflated_student = StudentRecord(
        roll_no="202501005",
        enroll_no="2025633",
        student_name="INFLATED STUDENT",
        father_name="TEST FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 20, "ex_part_a": 25, "ex_part_b": 20, "ex_total": 45, "grace": 2.0, "total": 67
            },
            "SOCI_PSYC": {
                "int_marks": 20, "ex_part_a": 20, "ex_part_b": 20, "ex_total": 40, "grace": 0, "total": 60
            },
            "ENGL": {
                "int_marks": 20, "ex_marks": 20, "total": 40
            }
        },
        raw_remarks="PASS"
    )

    report = gate.audit_batch([inflated_student])
    assert report.is_valid is False
    assert any("Grace Inflation" in a.field for a in report.anomalies)


def test_demographics_missing_father_and_duplicate_roll():
    gate = QualityAuditGate(semester_number=1)
    student1 = StudentRecord(
        roll_no="202501010",
        enroll_no="2025640",
        student_name="NAME ONE",
        father_name="",  # Missing father name!
        courses={"ANAT_PHYS": {"int_marks": 20, "ex_total": 40, "grace": 0, "total": 60}},
        raw_remarks="PASS"
    )
    student2 = StudentRecord(
        roll_no="202501010",  # Duplicate roll no!
        enroll_no="2025641",
        student_name="NAME TWO",
        father_name="VALID FATHER",
        courses={"ANAT_PHYS": {"int_marks": 20, "ex_total": 40, "grace": 0, "total": 60}},
        raw_remarks="PASS"
    )

    report = gate.audit_batch([student1, student2])
    assert report.is_valid is False
    assert any("Father's Name" in a.field for a in report.anomalies)
    assert any("Duplicate" in a.field for a in report.anomalies)


def test_boundary_outlier_marks_exceeded():
    gate = QualityAuditGate(semester_number=1)
    # IA marks given as 30 / 25
    outlier_student = StudentRecord(
        roll_no="202501015",
        enroll_no="2025650",
        student_name="OUTLIER CANDIDATE",
        father_name="VALID FATHER",
        courses={
            "ANAT_PHYS": {
                "int_marks": 30,  # Max is 25!
                "ex_total": 40,
                "grace": 0,
                "total": 70
            }
        },
        raw_remarks="PASS"
    )

    report = gate.audit_batch([outlier_student])
    assert report.is_valid is False
    assert any("Internal Marks" in a.field for a in report.anomalies)


def test_actual_master_datasheet_passes_quality_audit():
    assert os.path.exists(DATA_SHEET_PATH)
    with open(DATA_SHEET_PATH, "rb") as f:
        file_bytes = f.read()

    adapter = ExamCellParserAdapter(file_bytes)
    students = adapter.parse()

    gate = QualityAuditGate(semester_number=1)
    report = gate.audit_batch(students)

    assert report.is_valid is True
    assert report.can_export_pdf is True
    assert report.critical_errors_count == 0
    assert report.total_candidates == 3
