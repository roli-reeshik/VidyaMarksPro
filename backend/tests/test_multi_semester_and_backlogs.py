"""
Automated Verification & Smoke Test Suite:
1. Openpyxl Filter Bug Patch Verification
2. Semester 4 Three-Part Subcomponent Split (Phar 38 / Path 25 / Gen 12)
3. Semester 8 Competency Assessment (Int 100 + Ext 100 = 200 Max Marks)
4. Idempotent Re-upload and Audit Trail Logic (Zero Duplication)
5. Automated Failure Capture & Active Backlog Enrollment
6. Re-appear Roster API & Administrative Openpyxl Excel Export

Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with INC Gazette Corrigendum & SGPGIMS Lucknow Regulations.
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
    ExamCellParserAdapter,
)
from backend.parsers.excel_parser import ExcelSheetParser
from backend.db.database import get_sync_session, SyncSessionLocal
from backend.db.init_db import init_database, seed_courses
from backend.db.models import (
    Batch,
    Student,
    StudentSemesterRegistration,
    StudentCourseMark,
    Course,
    MarksAuditLog,
    StudentBacklog,
)
from backend.db.repository import ExaminationRepository
from backend.security import create_access_token

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_database()
    seed_courses()


@pytest.fixture
def admin_headers():
    token = create_access_token(data={"sub": "Admin", "role": "Admin", "token_version": 1})
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. Openpyxl Filter Bug Test
# -----------------------------------------------------------------------------
def test_openpyxl_filter_bug_handling():
    """Verify parser extracts workbook bytes cleanly without openpyxl CustomFilter Descriptor crash."""
    patch_openpyxl_filters()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sem4FilterTest"
    ws.cell(1, 1, "S.No")
    ws.cell(1, 2, "Student Name")
    ws.cell(2, 1, 1)
    ws.cell(2, 2, "Aakash Singh")
    ws.auto_filter.ref = "A1:B2"

    stream = io.BytesIO()
    wb.save(stream)
    raw_bytes = stream.getvalue()

    cleaned_bytes = clean_excel_filters_xml(raw_bytes)
    assert len(cleaned_bytes) > 0

    loaded_wb = robust_load_workbook(raw_bytes, data_only=True)
    assert "Sem4FilterTest" in loaded_wb.sheetnames
    loaded_ws = loaded_wb["Sem4FilterTest"]
    assert loaded_ws.cell(2, 2).value == "Aakash Singh"


# -----------------------------------------------------------------------------
# 2. Semester 4 Three-Part Subcomponent Split Test
# -----------------------------------------------------------------------------
def test_sem4_three_part_subcomponent_split(admin_headers):
    """
    Verify Pharmacology (38), Pathology (25), and Genetics (12) are correctly split
    and mapped into external_part_a, external_part_b, and external_part_c.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "4th Sem Tabulation"

    # Row 1: Header title
    ws.cell(1, 1, "Sanjay Gandhi Postgraduate Institute of Medical Sciences, Lucknow Data sheet B.Sc. Nursing (Fourth semester)")
    # Row 2: Subject title
    ws.cell(2, 6, "Pharmacology and Pathology (I & II) and Genetics (Code No. PHAR 205, PATH 210 & GEN 215)")
    ws.cell(2, 14, "Grand Total= 100")
    ws.cell(2, 15, "Result/ Remark")

    # Row 3: Subheaders
    headers = [
        "S.No", "Name", "Father's Name", "Enroll No", "Roll NO.",
        "Int. (25)", "Phar (38)", "Path (25)", "Gen (12)", "Total (75)", "Grand Total (100)", "Letter Grade", "Grade Point",
        "100", "Result"
    ]
    for idx, h in enumerate(headers, 1):
        ws.cell(3, idx, h)

    # Row 4: Student Data
    row = [
        1, "PRIYANKA SHARMA", "RAMESH SHARMA", "EN20240401", "202404001",
        21, 30, 20, 10, 60, 81, "A+", 9,
        81, "PASS"
    ]
    for idx, v in enumerate(row, 1):
        ws.cell(4, idx, v)

    stream = io.BytesIO()
    wb.save(stream)
    content = stream.getvalue()

    # Parse using ExcelSheetParser
    parser = ExcelSheetParser(content, "Sem4_Datasheet.xlsx", explicit_semester=4)
    parsed_res = parser.parse()
    assert len(parsed_res.results) == 1
    stu = parsed_res.results[0]
    assert stu.student.roll_no == "202404001"
    assert len(stu.courses) >= 1

    phar_comp = next((c for c in stu.courses if "PHAR" in c.course_code or "PATH" in c.course_code), None)
    assert phar_comp is not None
    assert phar_comp.internal_obtained == 21.0
    assert phar_comp.external_obtained == 60.0
    assert phar_comp.total_obtained == 81.0
    assert len(phar_comp.sub_components) == 3
    assert phar_comp.sub_components[0].obtained == 30.0  # Phar
    assert phar_comp.sub_components[1].obtained == 20.0  # Path
    assert phar_comp.sub_components[2].obtained == 10.0  # Gen

    # Persistence verification into PostgreSQL
    with SyncSessionLocal() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2022-2026")
        db_stu = repo.upsert_student(
            batch_id=batch.id,
            roll_no="202404001",
            enrollment_no="EN20240401",
            student_name="PRIYANKA SHARMA",
            father_name="RAMESH SHARMA",
            modified_by="TEST_SUITE",
        )
        reg = repo.upsert_registration(
            student_id=db_stu.id,
            semester_number=4,
            exam_month_year="JANUARY - 2026",
            exam_type="MAIN",
            modified_by="TEST_SUITE",
        )
        db_course = repo.resolve_course(semester_number=4, course_code=phar_comp.course_code)
        assert db_course is not None

        mark = repo.upsert_course_mark(
            registration_id=reg.id,
            course_id=db_course.id,
            internal_obtained=21.0,
            external_obtained=60.0,
            total_obtained=81.0,
            percentage=81.0,
            letter_grade="A+",
            grade_point=9,
            course_result="PASS",
            external_part_a=30.0,
            external_part_b=20.0,
            external_part_c=10.0,
            student_roll_no="202404001",
            modified_by="DATASHEET_REUPLOAD_UPDATE",
        )
        session.commit()

        # Query and assert parts in DB
        db_mark = session.query(StudentCourseMark).filter_by(registration_id=reg.id, course_id=db_course.id).first()
        assert db_mark is not None
        assert float(db_mark.external_part_a) == 30.0
        assert float(db_mark.external_part_b) == 20.0
        assert float(db_mark.external_part_c) == 10.0


# -----------------------------------------------------------------------------
# 3. Semester 8 Competency Assessment Test (Max 200)
# -----------------------------------------------------------------------------
def test_sem8_competency_assessment_200():
    """Verify Semester 8 Competency Assessment (Int 100 + Ext 100 = 200) maps cleanly."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "8th Sem Tabulation"

    ws.cell(1, 1, "Sanjay Gandhi Postgraduate Institute of Medical Sciences, Lucknow Data sheet B.Sc. Nursing (Eighth semester)")
    ws.cell(2, 6, "Competency Assessment (Code No. INTE - 415, 420, 425, 430 & 435)")
    ws.cell(2, 11, "Grand Total= 200")
    ws.cell(2, 12, "Result/ Remark")

    headers = [
        "S.No.", "Name", "Father's Name", "Enroll No.", "Roll No.",
        "Int. 100", "COMP ASS. (Ex. 100)", "Total (200)", "Letter Grade", "Grade Point",
        "200", "Result"
    ]
    for idx, h in enumerate(headers, 1):
        ws.cell(3, idx, h)

    row = [
        1, "SWETA PATEL", "DINESH PATEL", "EN20240801", "202408001",
        92, 94, 186, "O", 10,
        186, "PASS"
    ]
    for idx, v in enumerate(row, 1):
        ws.cell(4, idx, v)

    stream = io.BytesIO()
    wb.save(stream)
    content = stream.getvalue()

    parser = ExcelSheetParser(content, "Sem8_Datasheet.xlsx", explicit_semester=8)
    res = parser.parse()
    assert len(res.results) == 1
    stu = res.results[0]
    assert stu.student.roll_no == "202408001"
    assert stu.grand_total_max == 200.0
    assert stu.grand_total_obtained == 186.0

    comp = stu.courses[0]
    assert comp.internal_obtained == 92.0
    assert comp.external_obtained == 94.0
    assert comp.total_obtained == 186.0
    assert comp.letter_grade == "O"
    assert comp.grade_point == 10

    # Verify Course schema definition in PostgreSQL has max_total = 200
    with SyncSessionLocal() as session:
        c_db = session.query(Course).filter_by(semester_number=8, course_code="INTE 415, 420, 425, 430 & 435").first()
        assert c_db is not None
        assert float(c_db.max_internal) == 100.0
        assert float(c_db.max_external) == 100.0
        assert float(c_db.max_total) == 200.0


# -----------------------------------------------------------------------------
# 4. Idempotent Re-upload Test
# -----------------------------------------------------------------------------
def test_idempotent_reupload_and_audit():
    """
    Verify re-uploading the same datasheet for a student updates existing rows without duplication,
    and logs the action with modified_by = 'DATASHEET_REUPLOAD_UPDATE'.
    """
    with SyncSessionLocal() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2022-2026")
        stu = repo.upsert_student(
            batch_id=batch.id,
            roll_no="202402099",
            enrollment_no="EN202402099",
            student_name="IDEMPOTENCY TEST CANDIDATE",
            father_name="PARENT TEST",
            modified_by="TEST_SUITE",
        )

        initial_reg_count = session.query(StudentSemesterRegistration).filter_by(
            student_id=stu.id, semester_number=2, exam_type="MAIN"
        ).count()

        # Initial Upload
        reg1 = repo.upsert_registration(
            student_id=stu.id,
            semester_number=2,
            exam_month_year="JULY - 2026",
            exam_type="MAIN",
            grand_total_obtained=320.0,
            grand_total_max=500.0,
            sgpa=6.80,
            percentage=64.0,
            modified_by="DATASHEET_REUPLOAD_UPDATE",
        )
        c = repo.get_semester_courses(2)[0]
        m1 = repo.upsert_course_mark(
            registration_id=reg1.id,
            course_id=c.id,
            internal_obtained=18.0,
            external_obtained=42.0,
            total_obtained=60.0,
            percentage=60.0,
            letter_grade="B",
            grade_point=6,
            course_result="PASS",
            student_roll_no="202402099",
            modified_by="DATASHEET_REUPLOAD_UPDATE",
        )
        session.commit()

        # Re-upload (Update with new mark)
        reg2 = repo.upsert_registration(
            student_id=stu.id,
            semester_number=2,
            exam_month_year="JULY - 2026",
            exam_type="MAIN",
            grand_total_obtained=325.0,
            grand_total_max=500.0,
            sgpa=7.00,
            percentage=65.0,
            modified_by="DATASHEET_REUPLOAD_UPDATE",
        )
        m2 = repo.upsert_course_mark(
            registration_id=reg2.id,
            course_id=c.id,
            internal_obtained=19.0,
            external_obtained=46.0,
            total_obtained=65.0,
            percentage=65.0,
            letter_grade="B+",
            grade_point=7,
            course_result="PASS",
            student_roll_no="202402099",
            modified_by="DATASHEET_REUPLOAD_UPDATE",
        )
        session.commit()

        # Assert no duplicate registrations created
        final_reg_count = session.query(StudentSemesterRegistration).filter_by(
            student_id=stu.id, semester_number=2, exam_type="MAIN"
        ).count()
        assert final_reg_count == 1
        assert reg1.id == reg2.id

        # Assert updated values in place
        assert float(reg2.grand_total_obtained) == 325.0
        assert float(m2.total_obtained) == 65.0
        assert m2.letter_grade == "B+"

        # Assert audit trail entry was created
        audit_entry = session.query(MarksAuditLog).filter_by(
            student_roll_no="202402099",
            modified_by="DATASHEET_REUPLOAD_UPDATE"
        ).first()
        assert audit_entry is not None
        assert "Tot:60" in audit_entry.old_value
        assert "Tot:65" in audit_entry.new_value


# -----------------------------------------------------------------------------
# 5. Automated Failure Capture & Active Backlog Enrollment Test
# -----------------------------------------------------------------------------
def test_automated_backlog_capture():
    """
    Verify failing candidate is automatically queued into student_backlogs with
    status='ACTIVE', correct deficit_marks, and correct forthcoming_exam_month_year.
    """
    with SyncSessionLocal() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch("Batch 2022-2026")
        stu = repo.upsert_student(
            batch_id=batch.id,
            roll_no="202401777",
            enrollment_no="EN202401777",
            student_name="FAILED CANDIDATE TEST",
            father_name="PARENT TEST",
            modified_by="TEST_SUITE",
        )
        reg = repo.upsert_registration(
            student_id=stu.id,
            semester_number=1,
            exam_month_year="JANUARY - 2026",
            exam_type="MAIN",
            modified_by="TEST_SUITE",
        )
        # Select a standard 100-mark core course (e.g., Applied Anatomy & Applied Physiology)
        c = next(course for course in repo.get_semester_courses(1) if float(course.max_total) == 100.0)

        # Mark as failed: 8 + 22 = 30 (IA min 12.5 -> def 4.5; EA min 37.5 -> def 15.5; Tot min 50 -> def 20.0)
        repo.upsert_course_mark(
            registration_id=reg.id,
            course_id=c.id,
            internal_obtained=8.0,
            external_obtained=22.0,
            total_obtained=30.0,
            percentage=30.0,
            letter_grade="F",
            grade_point=0,
            course_result="FAIL",
            student_roll_no="202401777",
            modified_by="DATASHEET_REUPLOAD_UPDATE",
        )
        session.commit()

        # Verify active backlog record
        backlog = session.query(StudentBacklog).filter_by(
            student_id=stu.id, course_id=c.id, backlog_status="ACTIVE"
        ).first()

        assert backlog is not None
        assert backlog.backlog_status == "ACTIVE"
        assert backlog.failed_exam_month_year == "JANUARY - 2026"
        assert backlog.forthcoming_exam_month_year == "JULY - 2026"
        assert float(backlog.deficit_marks) == 20.0
        assert backlog.attempt_count == 1
        assert backlog.semester_number == 1


# -----------------------------------------------------------------------------
# 6. Re-appear Roster Endpoints Test (JSON & Excel)
# -----------------------------------------------------------------------------
def test_reappear_roster_endpoints(admin_headers):
    """
    Verify GET /api/v1/backlogs/reappear-roster and
    GET /api/v1/backlogs/export-roster-excel return HTTP 200 and accurate candidate counts and Excel bytes.
    """
    # 1. Test JSON Endpoint
    res = client.get("/api/v1/backlogs/reappear-roster", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "total_candidates" in data
    assert "roster" in data
    assert "branding" in data
    assert "VidyaLabs" in data["branding"]

    if data["total_candidates"] > 0:
        first = data["roster"][0]
        assert "roll_no" in first
        assert "enrollment_no" in first
        assert "student_name" in first
        assert "father_name" in first
        assert "failed_semester" in first
        assert "failed_subject_code" in first
        assert "failed_subject_title" in first
        assert "component_failed" in first
        assert "deficit_marks" in first
        assert "attempt_count" in first
        assert "attempt_label" in first
        assert "failed_exam_month_year" in first
        assert "forthcoming_exam_month_year" in first
        assert "backlog_status" in first

    # 2. Test Excel Export Endpoint
    excel_res = client.get("/api/v1/backlogs/export-roster-excel", headers=admin_headers)
    assert excel_res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in excel_res.headers.get("Content-Type", "")
    assert "attachment; filename=" in excel_res.headers.get("Content-Disposition", "")
    assert excel_res.content.startswith(b"PK\x03\x04")

    # Load and verify Excel sheet
    wb = openpyxl.load_workbook(io.BytesIO(excel_res.content))
    assert "Re-appear Roster" in wb.sheetnames
    ws = wb["Re-appear Roster"]
    assert "SANJAY GANDHI POSTGRADUATE INSTITUTE" in str(ws["A1"].value)
    assert "RE-APPEAR CANDIDATES ROSTER" in str(ws["A2"].value)
    assert ws.cell(4, 1).value == "S.No."
    assert ws.cell(4, 2).value == "Roll No."
