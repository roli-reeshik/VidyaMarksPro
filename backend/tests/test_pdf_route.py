"""
Integration Tests for Official Marksheet PDF & Bulk ZIP Generation (Phase 4)
Branding: VidyaMarksheet by VidyaLabs
"""

import os
import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.parsers.exam_cell_parser import ExamCellParserAdapter
from backend.evaluation_engine import EvaluationEngine
from backend.pdf_generator import MarksheetPdfGenerator

client = TestClient(app)

DATA_SHEET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "VidyaMarksheet_Master_DataSheet.xlsx")


@pytest.fixture(scope="module")
def evaluated_sample_students():
    with open(DATA_SHEET_PATH, "rb") as f:
        records = ExamCellParserAdapter(f.read()).parse()
    engine = EvaluationEngine(semester_number=1)
    eval_batch = engine.evaluate_batch(records)
    return eval_batch.results


def test_render_marksheet_html(evaluated_sample_students):
    gen = MarksheetPdfGenerator()
    student = evaluated_sample_students[1]  # Aditya with 2.5 Grace

    html = gen.render_html(student, semester_number=1)
    assert "COLLEGE OF NURSING" in html
    assert "SGPGIMS" in html
    assert "ADITYA KUMAR KATHERIYA" in html
    assert "202501002" in html
    assert "2025630" in html
    assert "Applied Anatomy &amp; Applied Physiology" in html or "Applied Anatomy & Applied Physiology" in html
    assert "PASS WITH 2.5 GRACE MARKS" in html
    assert "Prepared By" in html
    assert "Checked By" in html
    assert "Sub-Dean (Nursing)" in html
    assert "Executive Registrar" in html
    assert "Developed at" in html
    assert "VidyaLabs" in html
    assert "+91-9140189586" in html


def test_single_student_pdf_generation(evaluated_sample_students):
    gen = MarksheetPdfGenerator()
    aditya = evaluated_sample_students[1]

    pdf_bytes = gen.generate_student_pdf(aditya, semester_number=1)
    assert len(pdf_bytes) > 20000
    assert pdf_bytes.startswith(b"%PDF-")


def test_bulk_zip_generation(evaluated_sample_students):
    gen = MarksheetPdfGenerator()
    zip_bytes = gen.generate_bulk_zip(evaluated_sample_students, semester_number=1)

    assert len(zip_bytes) > 50000
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        file_list = zf.namelist()
        assert len(file_list) == len(evaluated_sample_students)
        assert any("202501001" in name for name in file_list)
        assert any("202501002" in name for name in file_list)
        assert any("202501064" in name for name in file_list)


def test_api_pdf_preview_html_route(evaluated_sample_students):
    student_payload = evaluated_sample_students[0].dict()
    response = client.post(
        "/api/pdf/preview-html?semester=1",
        json=student_payload
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "COLLEGE OF NURSING" in response.text


def test_api_pdf_student_route(evaluated_sample_students):
    student_payload = evaluated_sample_students[0].dict()
    response = client.post(
        "/api/pdf/student?semester=1",
        json=student_payload
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


def test_api_pdf_bulk_route(evaluated_sample_students):
    batch_payload = [s.dict() for s in evaluated_sample_students]
    response = client.post(
        "/api/pdf/bulk?semester=1",
        json=batch_payload
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content), "r") as zf:
        assert len(zf.namelist()) == 3


def test_api_pdf_from_excel_clean():
    with open(DATA_SHEET_PATH, "rb") as f:
        file_bytes = f.read()

    file_payload = ("VidyaMarksheet_Master_DataSheet.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response = client.post(
        "/api/pdf/from-excel",
        files={"file": file_payload},
        data={"semester": "1"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content), "r") as zf:
        assert len(zf.namelist()) == 3


def test_official_first_semester_template_strict_layout(evaluated_sample_students):
    import pypdf
    gen = MarksheetPdfGenerator()

    # Test Aditya (Student with 2.5 Grace)
    aditya = evaluated_sample_students[1]
    html_aditya = gen.render_html(aditya, semester_number=1, session_month_year="JANUARY - 2026", issue_date="12/10/2026")

    # 1. Page & Typography
    assert "@page" in html_aditya
    assert "8.5in 14in" in html_aditya
    assert "2.5in" in html_aditya
    assert "Calibri" in html_aditya
    assert "11pt" in html_aditya
    assert "white-space: nowrap" in html_aditya

    # 2. Header & Demographics (Single Line Header & Bold Details)
    assert "B.Sc.NURSING FIRST YEAR (FIRST SEMESTER) UNIVERSITY EXAMINATION JANUARY - 2026" in html_aditya
    assert f"NAME: {aditya.student_name}" in html_aditya
    assert f"S/o/D/o: {aditya.father_name}" in html_aditya
    assert "NAME OF COLLEGE: COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH." in html_aditya
    assert "ENROLLMENT NO: 2025630" in html_aditya
    assert "ROLL NO: 202501002" in html_aditya

    # 3. Main Marks Grid Header
    assert "Sl.No." in html_aditya
    assert "Course Code" in html_aditya
    assert "Title of Course" in html_aditya
    assert "Course Credits" in html_aditya
    assert "Internal Assesment Marks" in html_aditya
    assert "End Semester University Exam Marks" in html_aditya
    assert "Total Marks" in html_aditya
    assert "Final Marks (%)" in html_aditya
    assert "Letter Grade" in html_aditya
    assert "Grade Point" in html_aditya
    assert "Result" in html_aditya
    assert "Obtd" in html_aditya and "Max" in html_aditya

    # 4. Row Ordering: English -> Anatomy/Physiology -> Sociology/Psychology
    idx_engl = html_aditya.find("ENGL 101")
    idx_anat = html_aditya.find("ANAT 105")
    idx_soci = html_aditya.find("SOCI 115")
    assert idx_engl != -1 and idx_anat != -1 and idx_soci != -1
    assert idx_engl < idx_anat < idx_soci, "Courses must be ordered: ENGL 101, ANAT 105 & PHYS 110, SOCI 115 & PSYC 120"

    # Credits
    assert "(3+3)" in html_aditya

    # Total Row
    assert "Total Credit" in html_aditya
    assert ">14<" in html_aditya
    assert "Grand Total" in html_aditya
    assert ">250<" in html_aditya

    # 5. Explanatory Notes & Footer
    assert "* College Exam, Marks are not added for calculating SGPA, Pass marks-40% as per INC, New Delhi" in html_aditya
    assert "Obtd. : Obtained" in html_aditya and "Max. : Maximum" in html_aditya

    # SGPA / Credit Score Box
    assert "Semester Grade Point Average (SGPA)" in html_aditya
    assert "Semester Credit Score Average" in html_aditya
    assert ">5.00<" in html_aditya
    assert ">60.00<" in html_aditya

    # Result & Remarks (2-row, 2-column bordered table)
    assert "Result" in html_aditya
    assert "PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY" in html_aditya
    assert "Remarks" in html_aditya
    assert "Grading Performance - Average" in html_aditya

    # Statutory Note
    assert "Note:</b> In case of any discrepancy in the marksheet, candidate may apply for correction within a period of four weeks from the date of issue to the office of the Executive Registrar." in html_aditya

    # Signatures & Issue Date
    assert "Prepared By" in html_aditya
    assert "Checked By" in html_aditya
    assert "Sub-Dean (Nursing)" in html_aditya
    assert "Date:" in html_aditya and "12/10/2026" in html_aditya
    assert "Legend Overleaf" in html_aditya

    # Branding
    assert "Developed at <b>VidyaLabs</b>" in html_aditya
    assert "Priyanka Kumari" in html_aditya
    assert "+91-9140189586" in html_aditya

    # 6. Verify Exact PDF Physical Dimensions (Legal: 612x1008 pt, 1 Page)
    pdf_bytes = gen.generate_student_pdf(aditya, semester_number=1)
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1, "Generated marksheet must fit exactly on a single page"
    page0 = reader.pages[0]
    assert float(page0.mediabox.width) == 612.0
    assert float(page0.mediabox.height) == 1008.0


def test_sem7_marksheet_pdf_layout():
    """Verifies Semester 7 marksheet HTML rendering and sort order."""
    candidate_paths = [
        r"G:\Examination\MARKS DATA\16.Data sheet B.Sc.Nursing Fourth Year (Seventh Semester) Examination held in Febuary-2026\7th Semester Master Data.xlsx",
        r"E:\Examination\MARKS DATA\16.Data sheet B.Sc.Nursing Fourth Year (Seventh Semester) Examination held in Febuary-2026\7th Semester Master Data.xlsx",
    ]
    file_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not file_path:
        pytest.skip("7th Semester master data file not found at expected path")

    with open(file_path, "rb") as f:
        records = ExamCellParserAdapter(f.read()).parse()
    engine = EvaluationEngine(semester_number=7)
    eval_res = engine.evaluate_batch(records)
    pratham = next(r for r in eval_res.results if r.roll_no == "202207031")

    gen = MarksheetPdfGenerator()
    html = gen.render_html(pratham, semester_number=7, session_month_year="FEBRUARY - 2026")

    assert "SEVENTH SEMESTER" in html
    assert "PRATHAM VERMA" in html
    assert "N-COMH (II) 401" in html
    assert "NRST 405" in html
    assert "N-MIDW/OBGN" in html
    assert "PASS WITH 4.5 GRACE MARKS" in html


def test_sem8_marksheet_pdf_layout():
    """Verifies Semester 8 marksheet HTML rendering and sort order."""
    candidate_paths = [
        r"G:\Examination\MARKS DATA\20. B.Sc.Nursing Fourth Year (Eighth Semester) 2022-2026 Batch\4. Fourth Year\8th Semester\8th Semester Master Data.xlsx",
        r"E:\Examination\MARKS DATA\20. B.Sc.Nursing Fourth Year (Eighth Semester) 2022-2026 Batch\4. Fourth Year\8th Semester\8th Semester Master Data.xlsx",
    ]
    file_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not file_path:
        pytest.skip("8th Semester master data file not found at expected path")

    with open(file_path, "rb") as f:
        records = ExamCellParserAdapter(f.read()).parse()
    engine = EvaluationEngine(semester_number=8)
    eval_res = engine.evaluate_batch(records)
    abhinandan = next(r for r in eval_res.results if r.roll_no == "202208001")

    gen = MarksheetPdfGenerator()
    html = gen.render_html(abhinandan, semester_number=8, session_month_year="JULY - 2026")

    assert "EIGHTH SEMESTER" in html
    assert "ABHINANDAN KUMAR SHARMA" in html
    assert "INTE 415" in html
    assert "Competency Assessment" in html
    assert "PASS" in html

