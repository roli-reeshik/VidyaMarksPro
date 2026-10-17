"""
Unit & Integration Test Suite: Multi-Semester Ingestion, Openpyxl Patch,
Idempotent Upsert Logic, and Automated Re-appear Candidate Backlog Engine.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with INC Gazette & SGPGIMS Regulations.
"""

import io
import pytest
from decimal import Decimal
import openpyxl
from fastapi.testclient import TestClient

from backend.main import app
from backend.parsers.exam_cell_parser import (
    robust_load_workbook,
    clean_excel_filters_xml,
    patch_openpyxl_filters,
)
from backend.parsers.excel_parser import detect_semester_from_text
from backend.db.database import SyncSessionLocal
from backend.db.repository import ExaminationRepository
from backend.db.models import StudentBacklog, StudentSemesterRegistration
from backend.security import create_access_token


@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "Admin", "role": "Admin", "token_version": 1})
    return {"Authorization": f"Bearer {token}"}


def test_openpyxl_patch_and_cleaner():
    """Verify monkeypatch executes safely and clean_excel_filters_xml handles workbook bytes."""
    patch_openpyxl_filters()

    # Create a small in-memory workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TestSheet"
    ws.cell(row=1, column=1, value="Header 1")
    ws.cell(row=2, column=1, value="Data 1")
    buf = io.BytesIO()
    wb.save(buf)
    file_bytes = buf.getvalue()

    # Test cleaner
    cleaned = clean_excel_filters_xml(file_bytes)
    assert len(cleaned) > 0

    # Test robust_load_workbook
    loaded_wb = robust_load_workbook(file_bytes, data_only=True)
    assert "TestSheet" in loaded_wb.sheetnames
    assert loaded_wb["TestSheet"].cell(row=2, column=1).value == "Data 1"


def test_multi_semester_detection():
    """Test auto-detection across all 8 B.Sc. Nursing semesters."""
    # Semester 1
    assert detect_semester_from_text("B.Sc. Nursing First Semester Examination") == 1
    assert detect_semester_from_text("Applied Anatomy & Applied Physiology") == 1
    assert detect_semester_from_text("Communicative English") == 1

    # Semester 2
    assert detect_semester_from_text("Second Semester Tabulation Sheet") == 2
    assert detect_semester_from_text("Applied Biochemistry and Nutrition") == 2
    assert detect_semester_from_text("Nursing Foundation (I & II) N-NF") == 2

    # Semester 3
    assert detect_semester_from_text("Third Semester Master Data") == 3
    assert detect_semester_from_text("Applied Microbiology and Infection Control") == 3

    # Semester 4
    assert detect_semester_from_text("Fourth Semester Examination Data") == 4
    assert detect_semester_from_text("Pharmacology and Pathology") == 4

    # Semester 5
    assert detect_semester_from_text("Fifth Semester Tabulation") == 5
    assert detect_semester_from_text("Community Health Nursing I and Forensic Nursing") == 5

    # Semester 6
    assert detect_semester_from_text("Sixth Semester Examination") == 6
    assert detect_semester_from_text("Child Health Nursing and Mental Health Nursing") == 6

    # Semester 7
    assert detect_semester_from_text("Seventh Semester Final Examination") == 7
    assert detect_semester_from_text("Community Health Nursing II N-COMH (II) 401") == 7
    assert detect_semester_from_text("Nursing Research & Statistics NRST 405") == 7
    assert detect_semester_from_text("Midwifery / Obstetric and Gynaecological Nursing") == 7

    # Semester 8
    assert detect_semester_from_text("Eighth Semester Internship Assessment") == 8
    assert detect_semester_from_text("Intensive Clinical Practicum Competency Assessment INTE 415") == 8
    assert detect_semester_from_text("Elective-3 Scientific Writing Skills") == 8


def test_forthcoming_session_calculation():
    """Verify forthcoming session calculation for INC biannual cycle."""
    with SyncSessionLocal() as session:
        repo = ExaminationRepository(session)
        assert repo.get_next_examination_session("JANUARY - 2026") == "JULY - 2026"
        assert repo.get_next_examination_session("January 2026") == "JULY - 2026"
        assert repo.get_next_examination_session("JULY - 2026") == "JANUARY - 2027"
        assert repo.get_next_examination_session("August - 2025") == "JANUARY - 2026"
        assert repo.get_next_examination_session("December - 2025") == "JULY - 2025" or "JULY" in repo.get_next_examination_session("December - 2025")


def test_automated_backlog_creation_and_clearing():
    """Verify that failing marks generate active backlogs and passing marks clear them."""
    with SyncSessionLocal() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2022-2026")

        # Create test student
        test_student = repo.upsert_student(
            batch_id=batch.id,
            roll_no="999901001",
            enrollment_no="EN_999901001",
            student_name="TEST BACKLOG CANDIDATE",
            father_name="TEST FATHER",
            modified_by="TEST_SUITE"
        )

        # Create registration for Semester 1
        test_reg = repo.upsert_registration(
            student_id=test_student.id,
            semester_number=1,
            exam_month_year="JANUARY - 2026",
            exam_type="MAIN",
            modified_by="TEST_SUITE"
        )

        course = repo.get_semester_courses(1)[0]  # First course in Sem 1

        # 1. Fail the student in this course
        mark_failed = repo.upsert_course_mark(
            registration_id=test_reg.id,
            course_id=course.id,
            internal_obtained=5.0,
            external_obtained=20.0,
            total_obtained=25.0,
            percentage=25.0,
            letter_grade="F",
            grade_point=0,
            course_result="FAIL",
            student_roll_no="999901001",
            modified_by="TEST_SUITE"
        )

        # Check that active backlog was automatically queued
        backlog = (
            session.query(StudentBacklog)
            .filter_by(student_id=test_student.id, course_id=course.id, backlog_status="ACTIVE")
            .first()
        )
        assert backlog is not None
        assert backlog.backlog_status == "ACTIVE"
        assert backlog.attempt_count == 1
        assert backlog.forthcoming_exam_month_year == "JULY - 2026"
        assert float(backlog.deficit_marks) > 0

        # 2. Re-appear and pass the student in a subsequent sitting
        reappear_reg = repo.upsert_registration(
            student_id=test_student.id,
            semester_number=1,
            exam_month_year="JULY - 2026",
            exam_type="REAPPEAR - I",
            attempt_number=1,
            attempt_label="REAPPEAR - I",
            modified_by="TEST_SUITE"
        )

        mark_passed = repo.upsert_course_mark(
            registration_id=reappear_reg.id,
            course_id=course.id,
            internal_obtained=18.0,
            external_obtained=42.0,
            total_obtained=60.0,
            percentage=60.0,
            letter_grade="B",
            grade_point=6,
            course_result="PASS",
            student_roll_no="999901001",
            modified_by="TEST_SUITE"
        )

        # Verify active backlog is now transitioned to CLEARED
        session.refresh(backlog)
        assert backlog.backlog_status == "CLEARED"
        assert backlog.cleared_in_registration_id == reappear_reg.id
        assert backlog.cleared_at is not None

        # Clean up test records
        session.delete(backlog)
        session.delete(mark_passed)
        session.delete(mark_failed)
        session.delete(reappear_reg)
        session.delete(test_reg)
        session.delete(test_student)
        session.commit()


def test_backlog_roster_endpoint(auth_headers):
    """Verify GET /api/v1/analytics/backlog-roster API."""
    client = TestClient(app)
    res = client.get("/api/v1/analytics/backlog-roster", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "total_candidates" in data
    assert "roster" in data
    assert "branding" in data
    assert "VidyaLabs" in data["branding"]


def test_sem7_and_sem8_ingestion():
    """Verify explicit column ingestion for Semester 7 and Semester 8 against marked datasheets."""
    from backend.parsers.excel_parser import ExcelSheetParser
    from backend.parsers.exam_cell_parser import ExamCellParserAdapter

    # 1. SEMESTER 7 WORKBOOK (Matching Seventh Semester Highlighted Marks Fields.png)
    wb7 = openpyxl.Workbook()
    ws7 = wb7.active
    ws7.title = "7th Semester Data"

    # Header Row 1: Title
    ws7.cell(1, 1, "Sanjay Gandhi Postgraduate Institute of Medical Sciences, Lucknow Data sheet B.Sc. Nursing (Seventh semester)")
    # Header Row 2: Course titles
    ws7.cell(2, 6, "Community Health Nursing-II (Code No. N-COMH(II) 410) (Theory)")
    ws7.cell(2, 11, "Nursing Research & Statistics (Code No. NRST 405)")
    ws7.cell(2, 18, "Midwifery/Obstetrical and Gynecology (OBG) Nursing I & II (Theory) (Code No. N-MIDW(II)/OBGN410)")
    ws7.cell(2, 23, "Midwifery/Obstetrical and Gynecology (OBG) Nursing I & II (Practical) (Code No. N-MIDW(II)/OBGN410 (P))")
    ws7.cell(2, 28, "Community Health Nursing-II (Practical) (Code No. N-COMH(II) 410) (P)")
    ws7.cell(2, 33, "Grand Total= 500")
    ws7.cell(2, 34, "Result/ Remark")

    # Header Row 3: Subheaders
    headers_sem7 = [
        "S.No", "Name", "Father's Name", "Enroll No", "Roll NO.",
        "Int. 25", "COMH (I) (Ex. 75)", "Grand Total (100)", "Letter Grade", "Grade Point",
        "Int. (25)", "NUR (55)", "STAT (20)", "EX (75)", "Total (100)", "Letter Grade", "Grade Point",
        "Int. (25)", "MID Ex. (75)", "Total (100)", "Letter Grade", "Grade Point",
        "Int. (50)", "MID Ex. (50)", "Total (100)", "Letter Grade", "Grade Point",
        "Int. (50)", "EX (50)", "Total (100)", "Letter Grade", "Grade Point",
        "500", "Result"
    ]
    for c_idx, h_text in enumerate(headers_sem7, 1):
        ws7.cell(3, c_idx, h_text)

    # Row 4: Student Data
    row7 = [
        1, "ABHINANDAN KUMAR SHARMA", "KANHAIYA LAL SHARMA", "2022451", "202207001",
        20, 44, 64, "B", 6,
        14, 41, 17, 58, 72, "B+", 7,
        17, 44, 61, "B", 6,
        37, 41, 78, "A", 8,
        38, 43, 81, "A+", 9,
        356, "PASS"
    ]
    for c_idx, val in enumerate(row7, 1):
        ws7.cell(4, c_idx, val)

    buf7 = io.BytesIO()
    wb7.save(buf7)
    content7 = buf7.getvalue()

    # Ingest using ExcelSheetParser
    parser7 = ExcelSheetParser(content7, "7th_Sem_Tabulation.xlsx", explicit_semester=7)
    res7 = parser7.parse()
    assert len(res7.results) == 1
    stu7 = res7.results[0]
    assert stu7.student.roll_no == "202207001"
    assert stu7.student.name == "ABHINANDAN KUMAR SHARMA"
    assert len(stu7.courses) == 5
    assert stu7.grand_total_obtained == 356.0
    assert stu7.grand_total_max == 500.0
    assert stu7.result_status == "PASS"

    # Verify component marks
    comh_t = next(c for c in stu7.courses if "COMH" in c.course_code and c.component_name == "Theory")
    assert comh_t.internal_obtained == 20.0
    assert comh_t.external_obtained == 44.0
    assert comh_t.total_obtained == 64.0

    nrst = next(c for c in stu7.courses if "NRST" in c.course_code)
    assert nrst.internal_obtained == 14.0
    assert nrst.external_obtained == 58.0
    assert nrst.total_obtained == 72.0
    assert len(nrst.sub_components) == 2
    assert nrst.sub_components[0].obtained == 41.0
    assert nrst.sub_components[1].obtained == 17.0

    # Test ExamCellParserAdapter on Semester 7
    adapter7 = ExamCellParserAdapter(content7, semester=7)
    cell_recs7 = adapter7.parse()
    assert len(cell_recs7) == 1
    assert cell_recs7[0].roll_no == "202207001"
    assert "COMH_II_THEORY" in cell_recs7[0].courses
    assert cell_recs7[0].courses["COMH_II_THEORY"]["total"] in [64, "64"]

    # 2. SEMESTER 8 WORKBOOK (Matching Eighth Semester Highlighted Marks Fields.png)
    wb8 = openpyxl.Workbook()
    ws8 = wb8.active
    ws8.title = "8th Semester Data"

    # Header Row 1: Title
    ws8.cell(1, 1, "Sanjay Gandhi Postgraduate Institute of Medical Sciences, Lucknow Data sheet B.Sc. Nursing (Eighth semester)")
    # Header Row 2: Course titles
    ws8.cell(2, 6, "Competency Assessment (Code No. INTE - 415, 420, 425, 430 & 435)")
    ws8.cell(2, 11, "Grand Total= 200")
    ws8.cell(2, 12, "Result/ Remark")

    # Header Row 3: Subheaders
    headers_sem8 = [
        "S.No.", "Name", "Father's Name", "Enroll No.", "Roll No.",
        "Int. 100", "COMP ASS. (Ex. 100)", "Total (200)", "Letter Grade", "Grade Point",
        "200", "Result"
    ]
    for c_idx, h_text in enumerate(headers_sem8, 1):
        ws8.cell(3, c_idx, h_text)

    # Row 4: Student Data
    row8 = [
        1, "ABHINANDAN KUMAR SHARMA", "KANHAIYA LAL SHARMA", "2022451", "202208001",
        94, 95, 189, "O", 10,
        189, "PASS"
    ]
    for c_idx, val in enumerate(row8, 1):
        ws8.cell(4, c_idx, val)

    buf8 = io.BytesIO()
    wb8.save(buf8)
    content8 = buf8.getvalue()

    # Ingest using ExcelSheetParser
    parser8 = ExcelSheetParser(content8, "8th_Sem_Tabulation.xlsx", explicit_semester=8)
    res8 = parser8.parse()
    assert len(res8.results) == 1
    stu8 = res8.results[0]
    assert stu8.student.roll_no == "202208001"
    assert stu8.student.name == "ABHINANDAN KUMAR SHARMA"
    assert len(stu8.courses) == 1
    assert stu8.grand_total_obtained == 189.0
    assert stu8.grand_total_max == 200.0
    assert stu8.result_status == "PASS"

    comp_c1 = stu8.courses[0]
    assert comp_c1.internal_obtained == 94.0
    assert comp_c1.external_obtained == 95.0
    assert comp_c1.total_obtained == 189.0
    assert comp_c1.letter_grade == "O"
    assert comp_c1.grade_point == 10

    # Test ExamCellParserAdapter on Semester 8
    adapter8 = ExamCellParserAdapter(content8, semester=8)
    cell_recs8 = adapter8.parse()
    assert len(cell_recs8) == 1
    assert cell_recs8[0].roll_no == "202208001"
    assert "COMPETENCY" in cell_recs8[0].courses
    assert cell_recs8[0].courses["COMPETENCY"]["total"] in [189, "189"]

