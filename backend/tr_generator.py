"""
Formal Gazette Tabulation Register (TR) Export Engine (A3/Legal Landscape)
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.

Features:
- Standard University TR Ledger layout in Legal/A3 Landscape mode.
- Repeating headers with group pagination (15-20 candidates per page).
- Running page numbers ("Page X of Y") and 4-column statutory signature blocks.
- One-click dual export: High-resolution PDF (Playwright 300 DPI) and formatted Excel (.xlsx via openpyxl).
"""

import io
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.schemas.course_schemas import SEMESTER_DEFINITIONS
from backend.db.models import Batch, Student, StudentSemesterRegistration, StudentCourseMark, Course

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


# -----------------------------------------------------------------------------
# Data Models for Tabulation Register
# -----------------------------------------------------------------------------

class TabulationCourseHeader(BaseModel):
    course_code: str
    course_title: str
    short_title: str
    credits: int
    ia_max: float
    ea_max: float
    total_max: float


class TabulationStudentCourseMark(BaseModel):
    course_code: str
    ia: str
    ea: str
    total: str
    grade: str
    grade_point: int
    is_pass: bool
    is_exempted: bool = False
    grace: float = 0.0


class TabulationStudentRow(BaseModel):
    sl_no: int
    roll_no: str
    enroll_no: str
    student_name: str
    father_name: str
    course_marks: Dict[str, TabulationStudentCourseMark] = Field(default_factory=dict)
    grand_total: str
    grand_max: str
    percentage: str
    sgpa: str
    result_status: str
    remarks: str = ""
    attempt_label: str = "MAIN"
    is_pass: bool = True
    is_grace: bool = False


class TabulationRegisterPage(BaseModel):
    page_number: int
    students: List[TabulationStudentRow]


class TabulationRegisterData(BaseModel):
    institution_name: str = "SANJAY GANDHI POSTGRADUATE INSTITUTE OF MEDICAL SCIENCES, LUCKNOW"
    college_name: str = "COLLEGE OF NURSING"
    semester_number: int
    semester_name: str
    year_name: str
    batch_name: str
    session_month_year: str
    exam_type: str = "MAIN / REAPPEAR"
    issue_date: str
    courses: List[TabulationCourseHeader]
    all_students: List[TabulationStudentRow]
    pages: List[TabulationRegisterPage]
    total_appeared: int
    total_passed: int
    total_failed: int
    total_grace: int
    pass_percentage: float


# -----------------------------------------------------------------------------
# Data Builder Helpers
# -----------------------------------------------------------------------------

def _format_cell_number(val: Any, is_ex: bool = False) -> str:
    if is_ex:
        return "Ex."
    if val is None or val == "":
        return "0"
    s = str(val).strip()
    if s.upper() in ("EX.", "EX", "EXEMPTED"):
        return "Ex."
    if s.upper() in ("AB", "ABSENT"):
        return "Ab"
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else f"{f:.1f}"
    except Exception:
        return s


def _shorten_title(title: str) -> str:
    clean = re.sub(r'[*]', '', title).strip()
    words = clean.split()
    if len(words) <= 3:
        return clean
    return " ".join(words[:3]) + "..."


def build_tr_data_from_db(
    session,
    semester_number: int,
    batch_id: Optional[int] = None,
    page_size: int = 15
) -> TabulationRegisterData:
    """
    Constructs TabulationRegisterData by querying local PostgreSQL database (vidya_examination_db).
    """
    # 1. Fetch Semester Catalog
    db_courses = (
        session.query(Course)
        .filter_by(semester_number=semester_number)
        .order_by(Course.id)
        .all()
    )
    
    courses_header = [
        TabulationCourseHeader(
            course_code=c.course_code,
            course_title=c.course_title,
            short_title=_shorten_title(c.course_title),
            credits=int(c.credits),
            ia_max=float(c.max_internal),
            ea_max=float(c.max_external),
            total_max=float(c.max_total),
        )
        for c in db_courses
    ]

    # 2. Query Students & Registrations
    q_regs = (
        session.query(StudentSemesterRegistration, Student)
        .join(Student, StudentSemesterRegistration.student_id == Student.id)
        .filter(StudentSemesterRegistration.semester_number == semester_number)
    )
    if batch_id:
        q_regs = q_regs.filter(Student.batch_id == batch_id)

    regs = q_regs.order_by(Student.roll_no).all()

    # Determine batch name and session
    batch_name = "Batch 2022-2026"
    session_text = "JANUARY - 2026"
    if regs:
        first_stu = regs[0][1]
        first_reg = regs[0][0]
        if first_stu.batch:
            batch_name = first_stu.batch.batch_name
        if first_reg.exam_month_year:
            session_text = first_reg.exam_month_year

    sem_def = SEMESTER_DEFINITIONS.get(semester_number)
    sem_name = sem_def.semester_name if sem_def else f"SEMESTER {semester_number}"
    year_name = sem_def.year_name if sem_def else "ACADEMIC YEAR"

    # 3. Build Student Rows
    students_rows: List[TabulationStudentRow] = []
    passed_count = 0
    failed_count = 0
    grace_count = 0

    for idx, (reg, stu) in enumerate(regs, start=1):
        marks = (
            session.query(StudentCourseMark, Course)
            .join(Course, StudentCourseMark.course_id == Course.id)
            .filter(StudentCourseMark.registration_id == reg.id)
            .all()
        )

        course_marks_map: Dict[str, TabulationStudentCourseMark] = {}
        for m, c in marks:
            is_ex = bool(m.is_exempted)
            ia_str = "Ex." if is_ex else _format_cell_number(m.internal_obtained)
            ea_str = "Ex." if is_ex else _format_cell_number(m.external_obtained)
            tot_str = _format_cell_number(m.total_obtained)
            grc = float(m.grace_awarded or 0.0)

            course_marks_map[c.course_code] = TabulationStudentCourseMark(
                course_code=c.course_code,
                ia=ia_str,
                ea=ea_str,
                total=tot_str,
                grade=m.letter_grade or "C",
                grade_point=int(m.grade_point or 0),
                is_pass=(m.course_result == "PASS"),
                is_exempted=is_ex,
                grace=grc
            )

        res_stat = reg.result_status or "PASS"
        is_p = "PASS" in res_stat.upper()
        is_g = ("GRACE" in res_stat.upper() or "PWG" in res_stat.upper())

        if is_p:
            passed_count += 1
            if is_g:
                grace_count += 1
        else:
            failed_count += 1

        tot_obtd = f"{float(reg.grand_total_obtained):.1f}" if reg.grand_total_obtained is not None else "0.0"
        tot_max = f"{float(reg.grand_total_max):.0f}" if reg.grand_total_max is not None else "250"
        pct_str = f"{float(reg.percentage):.2f}" if reg.percentage is not None else "0.00"
        sgpa_str = f"{float(reg.sgpa):.2f}" if reg.sgpa is not None else "0.00"

        students_rows.append(
            TabulationStudentRow(
                sl_no=idx,
                roll_no=stu.roll_no,
                enroll_no=stu.enrollment_no,
                student_name=stu.student_name,
                father_name=stu.father_name,
                course_marks=course_marks_map,
                grand_total=tot_obtd,
                grand_max=tot_max,
                percentage=pct_str,
                sgpa=sgpa_str,
                result_status=res_stat,
                remarks=reg.result_remarks or "",
                attempt_label=reg.attempt_label or "MAIN",
                is_pass=is_p,
                is_grace=is_g,
            )
        )

    # 4. Group into Paginated Pages
    total_students = len(students_rows)
    pages: List[TabulationRegisterPage] = []
    if total_students == 0:
        pages.append(TabulationRegisterPage(page_number=1, students=[]))
    else:
        for p_idx in range(0, total_students, page_size):
            chunk = students_rows[p_idx:p_idx + page_size]
            pages.append(
                TabulationRegisterPage(
                    page_number=len(pages) + 1,
                    students=chunk
                )
            )

    pass_pct = round((passed_count / total_students * 100.0), 2) if total_students > 0 else 0.0

    return TabulationRegisterData(
        semester_number=semester_number,
        semester_name=sem_name,
        year_name=year_name,
        batch_name=batch_name,
        session_month_year=session_text,
        issue_date=datetime.now().strftime("%d/%m/%Y"),
        courses=courses_header,
        all_students=students_rows,
        pages=pages,
        total_appeared=total_students,
        total_passed=passed_count,
        total_failed=failed_count,
        total_grace=grace_count,
        pass_percentage=pass_pct
    )


def build_tr_data_from_evaluated_students(
    students: List[Any],
    semester_number: int = 1,
    batch_name: str = "Batch 2022-2026",
    session_month_year: str = "JANUARY - 2026",
    page_size: int = 15
) -> TabulationRegisterData:
    """
    Constructs TabulationRegisterData from in-memory EvaluatedStudentRecord objects.
    """
    sem_def = SEMESTER_DEFINITIONS.get(semester_number)
    sem_name = sem_def.semester_name if sem_def else f"SEMESTER {semester_number}"
    year_name = sem_def.year_name if sem_def else "ACADEMIC YEAR"

    courses_header: List[TabulationCourseHeader] = []
    if sem_def:
        for c in sem_def.courses:
            ia_m = 25.0
            ea_m = 75.0
            tot_m = 100.0
            if c.components:
                comp = c.components[0]
                ia_m = comp.ia_max
                ea_m = comp.ea_max
                tot_m = comp.total_max
            courses_header.append(
                TabulationCourseHeader(
                    course_code=c.course_code,
                    course_title=c.title,
                    short_title=_shorten_title(c.title),
                    credits=c.credits,
                    ia_max=ia_m,
                    ea_max=ea_m,
                    total_max=tot_m
                )
            )

    students_rows: List[TabulationStudentRow] = []
    passed_count = 0
    failed_count = 0
    grace_count = 0

    for idx, s in enumerate(students, start=1):
        # Support dict or Pydantic object
        s_roll = getattr(s, "roll_no", None) or s.get("roll_no", "")
        s_enroll = getattr(s, "enroll_no", None) or s.get("enroll_no", "")
        s_name = getattr(s, "student_name", None) or s.get("student_name", "")
        s_father = getattr(s, "father_name", None) or s.get("father_name", "")
        s_status = getattr(s, "result_status", None) or s.get("result_status", "PASS")
        s_remarks = getattr(s, "raw_remarks", None) or s.get("raw_remarks", "")
        s_attempt = getattr(s, "attempt_label", None) or s.get("attempt_label", "MAIN")
        s_tot = f"{float(getattr(s, 'total_marks_obtained', None) or s.get('total_marks_obtained', 0)):.1f}"
        s_max = f"{float(getattr(s, 'total_marks_max', None) or s.get('total_marks_max', 250)):.0f}"
        s_pct = f"{float(getattr(s, 'overall_percentage', None) or s.get('overall_percentage', 0)):.2f}"
        s_sgpa = f"{float(getattr(s, 'sgpa', None) or s.get('sgpa', 0)):.2f}"

        is_p = "PASS" in s_status.upper()
        is_g = ("GRACE" in s_status.upper() or "PWG" in s_status.upper())
        if is_p:
            passed_count += 1
            if is_g:
                grace_count += 1
        else:
            failed_count += 1

        course_marks_map: Dict[str, TabulationStudentCourseMark] = {}
        c_dict = getattr(s, "courses", None) or s.get("courses", {})
        if isinstance(c_dict, dict):
            for c_key, c_val in c_dict.items():
                code = getattr(c_val, "course_code", None) or c_val.get("course_code", c_key)
                is_ex = bool(getattr(c_val, "is_exempted", False) or c_val.get("is_exempted", False))
                ia_val = getattr(c_val, "internal_marks", None) or c_val.get("internal_marks", 0)
                ea_val = getattr(c_val, "effective_external", None) or c_val.get("effective_external", 0)
                tot_val = getattr(c_val, "total_marks", None) or c_val.get("total_marks", 0)
                grd = getattr(c_val, "letter_grade", None) or c_val.get("letter_grade", "C")
                gp = int(getattr(c_val, "grade_point", 0) or c_val.get("grade_point", 0))
                grc = float(getattr(c_val, "grace_marks", 0.0) or c_val.get("grace_marks", 0.0))

                mark_obj = TabulationStudentCourseMark(
                    course_code=str(code),
                    ia="Ex." if is_ex else _format_cell_number(ia_val),
                    ea="Ex." if is_ex else _format_cell_number(ea_val),
                    total=_format_cell_number(tot_val),
                    grade=str(grd),
                    grade_point=gp,
                    is_pass=bool(getattr(c_val, "is_pass", True) or c_val.get("is_pass", True)),
                    is_exempted=is_ex,
                    grace=grc
                )
                course_marks_map[str(code)] = mark_obj
                course_marks_map[str(c_key)] = mark_obj

                # Match against defined course headers
                for hdr in courses_header:
                    hdr_code_up = hdr.course_code.upper()
                    c_up = str(code).upper()
                    k_up = str(c_key).upper()
                    if hdr_code_up == c_up or hdr_code_up == k_up:
                        course_marks_map[hdr.course_code] = mark_obj
                    elif "ENGL" in hdr_code_up and ("ENGL" in c_up or "ENGL" in k_up):
                        course_marks_map[hdr.course_code] = mark_obj
                    elif ("ANAT" in hdr_code_up or "PHYS" in hdr_code_up) and ("ANAT" in c_up or "PHYS" in c_up or "ANAT" in k_up or "PHYS" in k_up):
                        course_marks_map[hdr.course_code] = mark_obj
                    elif ("SOCI" in hdr_code_up or "PSYC" in hdr_code_up) and ("SOCI" in c_up or "PSYC" in c_up or "SOCI" in k_up or "PSYC" in k_up):
                        course_marks_map[hdr.course_code] = mark_obj
                    elif ("BIOC" in hdr_code_up or "NUTR" in hdr_code_up) and ("BIOC" in c_up or "NUTR" in c_up or "BIOC" in k_up or "NUTR" in k_up):
                        course_marks_map[hdr.course_code] = mark_obj
                    elif ("HNIT" in hdr_code_up or "INFORMATICS" in hdr_code_up) and ("HNIT" in c_up or "HNIT" in k_up or "INFORMATICS" in c_up):
                        course_marks_map[hdr.course_code] = mark_obj
                    elif ("FOUNDATION" in hdr_code_up or "NNF" in hdr_code_up or "N-NF" in hdr_code_up):
                        is_p = "PRACT" in c_up or "(P)" in c_up or "PRACT" in k_up or "(P)" in k_up
                        hdr_p = "(P)" in hdr_code_up or "PRACT" in hdr.course_title.upper()
                        if is_p == hdr_p:
                            course_marks_map[hdr.course_code] = mark_obj

        students_rows.append(
            TabulationStudentRow(
                sl_no=idx,
                roll_no=s_roll,
                enroll_no=s_enroll,
                student_name=s_name,
                father_name=s_father,
                course_marks=course_marks_map,
                grand_total=s_tot,
                grand_max=s_max,
                percentage=s_pct,
                sgpa=s_sgpa,
                result_status=s_status,
                remarks=s_remarks,
                attempt_label=s_attempt,
                is_pass=is_p,
                is_grace=is_g,
            )
        )

    total_students = len(students_rows)
    pages: List[TabulationRegisterPage] = []
    if total_students == 0:
        pages.append(TabulationRegisterPage(page_number=1, students=[]))
    else:
        for p_idx in range(0, total_students, page_size):
            chunk = students_rows[p_idx:p_idx + page_size]
            pages.append(
                TabulationRegisterPage(
                    page_number=len(pages) + 1,
                    students=chunk
                )
            )

    pass_pct = round((passed_count / total_students * 100.0), 2) if total_students > 0 else 0.0

    return TabulationRegisterData(
        semester_number=semester_number,
        semester_name=sem_name,
        year_name=year_name,
        batch_name=batch_name,
        session_month_year=session_month_year,
        issue_date=datetime.now().strftime("%d/%m/%Y"),
        courses=courses_header,
        all_students=students_rows,
        pages=pages,
        total_appeared=total_students,
        total_passed=passed_count,
        total_failed=failed_count,
        total_grace=grace_count,
        pass_percentage=pass_pct
    )


# -----------------------------------------------------------------------------
# Tabulation Register PDF Generator (Playwright A3 Landscape)
# -----------------------------------------------------------------------------

class TabulationRegisterPdfGenerator:
    """
    Renders high-resolution official Gazette Tabulation Register PDFs in A3 landscape.
    Uses Playwright and Jinja2 with 8mm margins and 300 DPI print fidelity.
    """

    def __init__(self, template_dir: str = TEMPLATES_DIR):
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        self.template = self.jinja_env.get_template("tabulation_register_template.html")

    def render_html(self, data: TabulationRegisterData) -> str:
        """Renders raw HTML string for in-browser preview or Playwright compilation."""
        return self.template.render(data=data)

    def generate_pdf(self, data: TabulationRegisterData, paper_size: str = "A3") -> bytes:
        """Generates high-res A3 Landscape PDF bytes matching institutional Gazette standards."""
        html_content = self.render_html(data)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            try:
                page = browser.new_page()
                page.set_content(html_content, wait_until="load", timeout=30000)
                pdf_bytes = page.pdf(
                    format=paper_size,  # "A3" or "Legal"
                    landscape=True,
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={"top": "8mm", "bottom": "8mm", "left": "8mm", "right": "8mm"}
                )
            finally:
                browser.close()

        return pdf_bytes


# -----------------------------------------------------------------------------
# Tabulation Register Excel Generator (openpyxl)
# -----------------------------------------------------------------------------

class TabulationRegisterExcelGenerator:
    """
    Generates fully formatted executive .xlsx Gazette Tabulation Registers using openpyxl.
    Features:
    - 3-tier merged title banners with SGPGIMS branding
    - 2-tier table headers with subject grouping
    - Thin cell borders, alternating zebra fills, color-coded results
    - Statistical cohort summary and statutory 4-column signature blocks
    - Auto-fitted column widths and landscape print setup.
    """

    def generate_excel(self, data: TabulationRegisterData) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"TR_Sem_{data.semester_number}"

        # Page Setup: Landscape, A3 / Legal
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0

        # Styles
        thin_side = Side(border_style="thin", color="0F172A")
        thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        double_bottom = Border(left=thin_side, right=thin_side, top=thin_side, bottom=Side(border_style="double", color="0F172A"))

        font_inst = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        font_coll = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_banner = Font(name="Calibri", size=10.5, bold=True, color="FFFFFF")
        font_meta = Font(name="Calibri", size=9, bold=True, color="1E293B")

        font_th_tier1 = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        font_th_tier2 = Font(name="Calibri", size=8.5, bold=True, color="FFFFFF")

        font_data_bold = Font(name="Calibri", size=8.5, bold=True, color="0F172A")
        font_data_normal = Font(name="Calibri", size=8.5, bold=False, color="0F172A")
        font_pass = Font(name="Calibri", size=8.5, bold=True, color="15803D")
        font_fail = Font(name="Calibri", size=8.5, bold=True, color="B91C1C")
        font_grace = Font(name="Calibri", size=8.5, bold=True, color="B45309")
        font_reappear = Font(name="Calibri", size=8.5, bold=True, color="1D4ED8")

        fill_navy_top = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        fill_slate_top = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        fill_blue_banner = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        fill_meta = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

        fill_th1 = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        fill_th_course = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        fill_th2 = PatternFill(start_color="334155", end_color="334155", fill_type="solid")

        fill_zebra_even = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        fill_zebra_odd = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        fill_sgpa = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")

        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

        # Calculate Total Columns: 5 Demographics + (4 * num_courses) + 4 Summary = Total
        num_courses = len(data.courses)
        total_cols = 5 + (num_courses * 4) + 4
        last_col_letter = get_column_letter(total_cols)

        # 1. Top Banners (Rows 1-4)
        ws.merge_cells(f"A1:{last_col_letter}1")
        cell_1 = ws["A1"]
        cell_1.value = "SANJAY GANDHI POSTGRADUATE INSTITUTE OF MEDICAL SCIENCES, LUCKNOW"
        cell_1.font = font_inst
        cell_1.fill = fill_navy_top
        cell_1.alignment = align_center

        ws.merge_cells(f"A2:{last_col_letter}2")
        cell_2 = ws["A2"]
        cell_2.value = "COLLEGE OF NURSING"
        cell_2.font = font_coll
        cell_2.fill = fill_slate_top
        cell_2.alignment = align_center

        ws.merge_cells(f"A3:{last_col_letter}3")
        cell_3 = ws["A3"]
        cell_3.value = f"TABULATION REGISTER FOR B.Sc. NURSING {data.semester_name.upper()} EXAMINATION {data.session_month_year.upper()}"
        cell_3.font = font_banner
        cell_3.fill = fill_blue_banner
        cell_3.alignment = align_center

        # Metadata Row (Row 4)
        ws.merge_cells(f"A4:{last_col_letter}4")
        cell_4 = ws["A4"]
        cell_4.value = (
            f"COHORT: {data.batch_name}   |   DEGREE: B.Sc. NURSING (4-YEAR DEGREE)   |   "
            f"COLLEGE CODE: 1313   |   CYCLE: {data.exam_type}   |   DATE: {data.issue_date}"
        )
        cell_4.font = font_meta
        cell_4.fill = fill_meta
        cell_4.alignment = align_center

        ws.row_dimensions[1].height = 28
        ws.row_dimensions[2].height = 22
        ws.row_dimensions[3].height = 24
        ws.row_dimensions[4].height = 20

        # 2. Table Headers (Rows 6 & 7)
        row_th1 = 6
        row_th2 = 7

        ws.row_dimensions[row_th1].height = 25
        ws.row_dimensions[row_th2].height = 20

        # Demographics Tier 1
        demo_headers = [
            ("A", "B", "S.No", 8),
            ("B", "B", "Roll No", 14),
            ("C", "C", "Enrollment No", 16),
            ("D", "D", "Candidate Name", 24),
            ("E", "E", "Father's Name", 22),
        ]
        for col_l, _, title, _ in demo_headers:
            ws.merge_cells(f"{col_l}{row_th1}:{col_l}{row_th2}")
            c = ws[f"{col_l}{row_th1}"]
            c.value = title
            c.font = font_th_tier1
            c.fill = fill_th1
            c.alignment = align_center
            c.border = thin_border
            ws[f"{col_l}{row_th2}"].border = thin_border

        # Course Headers (Tier 1 & Tier 2)
        curr_col_idx = 6
        for course in data.courses:
            start_col = get_column_letter(curr_col_idx)
            end_col = get_column_letter(curr_col_idx + 3)

            ws.merge_cells(f"{start_col}{row_th1}:{end_col}{row_th1}")
            cell_ch = ws[f"{start_col}{row_th1}"]
            cell_ch.value = f"{course.course_code} - {course.short_title} (Cr:{course.credits})"
            cell_ch.font = font_th_tier1
            cell_ch.fill = fill_th_course
            cell_ch.alignment = align_center
            cell_ch.border = thin_border

            sub_cols = ["IA", "EA", "Tot", "Grd"]
            for sub_i, sub_name in enumerate(sub_cols):
                sub_col_letter = get_column_letter(curr_col_idx + sub_i)
                c_sub = ws[f"{sub_col_letter}{row_th2}"]
                c_sub.value = sub_name
                c_sub.font = font_th_tier2
                c_sub.fill = fill_th2
                c_sub.alignment = align_center
                c_sub.border = thin_border
                ws[f"{sub_col_letter}{row_th1}"].border = thin_border

            curr_col_idx += 4

        # Summary Headers Tier 1 (Grand Total, %, SGPA, Result)
        summary_headers = ["Grand Tot", "%", "SGPA", "Result Status"]
        for s_idx, s_title in enumerate(summary_headers):
            s_col_letter = get_column_letter(curr_col_idx + s_idx)
            ws.merge_cells(f"{s_col_letter}{row_th1}:{s_col_letter}{row_th2}")
            c_s = ws[f"{s_col_letter}{row_th1}"]
            c_s.value = s_title
            c_s.font = font_th_tier1
            c_s.fill = fill_th1
            c_s.alignment = align_center
            c_s.border = thin_border
            ws[f"{s_col_letter}{row_th2}"].border = thin_border

        # 3. Data Rows
        curr_row = 8
        for s in data.all_students:
            ws.row_dimensions[curr_row].height = 20
            row_fill = fill_zebra_even if (curr_row % 2 == 0) else fill_zebra_odd

            # Demographics
            ws[f"A{curr_row}"] = s.sl_no
            ws[f"A{curr_row}"].alignment = align_center
            ws[f"A{curr_row}"].font = font_data_normal

            ws[f"B{curr_row}"] = s.roll_no
            ws[f"B{curr_row}"].alignment = align_center
            ws[f"B{curr_row}"].font = font_data_bold

            ws[f"C{curr_row}"] = s.enroll_no
            ws[f"C{curr_row}"].alignment = align_center
            ws[f"C{curr_row}"].font = font_data_normal

            ws[f"D{curr_row}"] = s.student_name + (f" ({s.attempt_label})" if s.attempt_label != "MAIN" else "")
            ws[f"D{curr_row}"].alignment = align_left
            ws[f"D{curr_row}"].font = font_data_bold

            ws[f"E{curr_row}"] = s.father_name
            ws[f"E{curr_row}"].alignment = align_left
            ws[f"E{curr_row}"].font = font_data_normal

            for col_c in ["A", "B", "C", "D", "E"]:
                ws[f"{col_c}{curr_row}"].fill = row_fill
                ws[f"{col_c}{curr_row}"].border = thin_border

            # Course Marks
            col_mark_idx = 6
            for course in data.courses:
                m = s.course_marks.get(course.course_code)
                ia_cell = ws.cell(row=curr_row, column=col_mark_idx)
                ea_cell = ws.cell(row=curr_row, column=col_mark_idx + 1)
                tot_cell = ws.cell(row=curr_row, column=col_mark_idx + 2)
                grd_cell = ws.cell(row=curr_row, column=col_mark_idx + 3)

                if m:
                    ia_cell.value = m.ia
                    ea_cell.value = m.ea
                    tot_cell.value = m.total
                    grd_cell.value = m.grade

                    grd_color = font_fail if m.grade == "F" else font_data_bold
                    grd_cell.font = grd_color
                else:
                    ia_cell.value = "-"
                    ea_cell.value = "-"
                    tot_cell.value = "-"
                    grd_cell.value = "-"
                    grd_cell.font = font_data_normal

                for cell_item in [ia_cell, ea_cell, tot_cell, grd_cell]:
                    cell_item.alignment = align_center
                    cell_item.fill = row_fill
                    cell_item.border = thin_border
                    if cell_item != grd_cell:
                        cell_item.font = font_data_normal

                tot_cell.font = font_data_bold
                col_mark_idx += 4

            # Summaries
            gt_cell = ws.cell(row=curr_row, column=col_mark_idx)
            pct_cell = ws.cell(row=curr_row, column=col_mark_idx + 1)
            sgpa_cell = ws.cell(row=curr_row, column=col_mark_idx + 2)
            res_cell = ws.cell(row=curr_row, column=col_mark_idx + 3)

            gt_cell.value = s.grand_total
            pct_cell.value = s.percentage
            sgpa_cell.value = s.sgpa
            res_cell.value = s.result_status

            gt_cell.font = font_data_bold
            gt_cell.alignment = align_center
            gt_cell.fill = row_fill
            gt_cell.border = thin_border

            pct_cell.font = font_data_bold
            pct_cell.alignment = align_center
            pct_cell.fill = row_fill
            pct_cell.border = thin_border

            sgpa_cell.font = font_data_bold
            sgpa_cell.alignment = align_center
            sgpa_cell.fill = fill_sgpa
            sgpa_cell.border = thin_border

            # Status styling
            if "CLEARED IN REAPPEAR" in s.result_status:
                res_cell.font = font_reappear
            elif "PASS WITH" in s.result_status or "PWG" in s.result_status:
                res_cell.font = font_grace
            elif "PASS" in s.result_status:
                res_cell.font = font_pass
            else:
                res_cell.font = font_fail

            res_cell.alignment = align_center
            res_cell.fill = row_fill
            res_cell.border = thin_border

            curr_row += 1

        # 4. Statistical Summary Box (Row curr_row + 1)
        curr_row += 1
        ws.row_dimensions[curr_row].height = 22
        ws.merge_cells(f"A{curr_row}:{last_col_letter}{curr_row}")
        box_cell = ws[f"A{curr_row}"]
        box_cell.value = (
            f"TOTAL APPEARED: {data.total_appeared}    |    "
            f"TOTAL PASSED: {data.total_passed}    |    "
            f"PASSED WITH GRACE: {data.total_grace}    |    "
            f"TOTAL FAILED: {data.total_failed}    |    "
            f"OVERALL PASS PERCENTAGE: {data.pass_percentage}%"
        )
        box_cell.font = Font(name="Calibri", size=9.5, bold=True, color="1E3A8A")
        box_cell.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
        box_cell.alignment = align_center
        box_cell.border = double_bottom

        # 5. Statutory Signatures Block (Row curr_row + 4)
        curr_row += 3
        ws.row_dimensions[curr_row].height = 18
        ws.row_dimensions[curr_row + 1].height = 16

        sig_positions = [
            ("B", "D", "Tabulated By", "Dealing Assistant / Tabulator"),
            ("F", "I", "Verified By", "Scrutinizer / Section Officer"),
            ("K", "N", "Assistant Registrar (Exams)", "SGPGIMS Examination Section"),
            ("P", last_col_letter, "Controller of Examinations / Sub-Dean", "SGPGI College of Nursing, Lucknow")
        ]

        for s_start, s_end, title, sub in sig_positions:
            ws.merge_cells(f"{s_start}{curr_row}:{s_end}{curr_row}")
            sig_c = ws[f"{s_start}{curr_row}"]
            sig_c.value = title
            sig_c.font = Font(name="Calibri", size=9, bold=True, color="0F172A")
            sig_c.alignment = align_center
            sig_c.border = Border(top=Side(border_style="thin", color="0F172A"))

            ws.merge_cells(f"{s_start}{curr_row + 1}:{s_end}{curr_row + 1}")
            sub_c = ws[f"{s_start}{curr_row + 1}"]
            sub_c.value = sub
            sub_c.font = Font(name="Calibri", size=7.5, italic=True, color="475569")
            sub_c.alignment = align_center

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            # Skip checking merged title banners (rows 1-4)
            for cell in col[5:min(len(col), curr_row - 4)]:
                if cell.value:
                    val_str = str(cell.value)
                    if len(val_str) > max_len:
                        max_len = len(val_str)
            min_w = 6
            if col_letter in ["A"]:
                min_w = 5
            elif col_letter in ["B", "C"]:
                min_w = 14
            elif col_letter in ["D"]:
                min_w = 26
            elif col_letter in ["E"]:
                min_w = 22
            elif col_letter == last_col_letter:
                min_w = 20
            ws.column_dimensions[col_letter].width = max(max_len + 2, min_w)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()
