"""
Official SGPGIMS Marksheet Template & Bulk PDF Generation Engine
Phase 4: High-resolution PDF rendering matching official institutional format.
- Jinja2 Template rendering
- Playwright Headless Chromium Engine with Legal (8.5" x 14") 0.25" margins print tuning
- In-memory ZIP archiver for bulk export

Branding: VidyaMarksheet by VidyaLabs
"""

import os
import re
import io
import sys
import types
import asyncio
import zipfile
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader

from playwright.sync_api import sync_playwright

from backend.evaluation_engine import EvaluatedStudentRecord
from backend.schemas.course_schemas import SEMESTER_DEFINITIONS
from backend.template_config import MarksheetTemplateConfig, get_template_config

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


@contextmanager
def _ensure_proactor_loop_on_windows():
    """
    On Windows, Playwright requires ProactorEventLoop to spawn browser subprocesses.
    Uvicorn in --reload mode sets WindowsSelectorEventLoopPolicy, which lacks
    subprocess transport support and causes NotImplementedError.
    This temporarily switches to WindowsProactorEventLoopPolicy for the Playwright run.
    """
    old_policy = None
    if sys.platform == "win32":
        try:
            old_policy = asyncio.get_event_loop_policy()
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass
    try:
        yield
    finally:
        if sys.platform == "win32" and old_policy is not None:
            try:
                asyncio.set_event_loop_policy(old_policy)
            except Exception:
                pass


def clean_filename_token(val: str) -> str:
    """Sanitizes strings for safe cross-platform filenames."""
    s = re.sub(r'[^\w\s-]', '', str(val)).strip()
    return re.sub(r'[-\s]+', '_', s)


def sanitize_proper_case_name(name: str) -> str:
    """
    Sanitizes candidate names for structured marksheet file export:
    - Strips characters forbidden in Windows/Linux file paths (\\ / : * ? " < > |)
    - Replaces consecutive spaces with a single space
    - Converts to Proper Title Case
    """
    if not name:
        return "Student"
    cleaned = re.sub(r'[\\/:*?"<>|]', '', str(name))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.title()


def build_export_filepath(
    base_dir: str,
    academic_year: str,
    exam_session: str,
    semester: int,
    student_name: str,
    roll_no: str
) -> tuple[str, str, str]:
    """
    Builds the standardized structured marksheet path:
    {MARKSHEET_STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/{Proper_Name}_{Roll_No}.pdf
    Returns (directory_path, filename, full_path).
    Ensures missing directories are created automatically via os.makedirs(..., exist_ok=True).
    """
    clean_name = sanitize_proper_case_name(student_name)
    clean_roll = re.sub(r'[\\/:*?"<>|\s]', '', str(roll_no)).strip()
    filename = f"{clean_name}_{clean_roll}.pdf"

    # Clean session for directory name (e.g., 'JANUARY - 2026' -> 'JANUARY_2026')
    clean_session = re.sub(r'[^A-Za-z0-9]+', '_', str(exam_session)).strip('_') or "SESSION"
    year_str = str(academic_year).strip()

    dir_path = os.path.join(base_dir, year_str, clean_session, f"Semester_{semester}")
    os.makedirs(dir_path, exist_ok=True)
    full_path = os.path.join(dir_path, filename)
    return dir_path, filename, full_path


class MarksheetStudentAdapter:
    """
    Adapts database marksheet dictionary (from ExaminationRepository.get_student_marksheet_data)
    into a dot-accessible structure compatible with MarksheetPdfGenerator and Jinja2 templates.
    """
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        stu = data.get("student", {})
        self.student_name = stu.get("name") or stu.get("student_name", "")
        self.enroll_no = stu.get("enrollment_no") or stu.get("enroll_no", "")
        self.father_name = stu.get("father_name", "")
        self.roll_no = stu.get("roll_no", "")
        self.institutional_status = stu.get("institutional_status", "REGULAR")
        self.batch_name = stu.get("batch_name", "Batch 2022-2026")

        self.total_marks_obtained = data.get("grand_total_obtained", 0.0)
        self.total_marks_max = data.get("grand_total_max", 0.0)
        self.overall_percentage = data.get("percentage", 0.0)
        self.sgpa = data.get("sgpa")
        self.semester_credit_score = data.get("credit_score", 0.0)
        self.result_status = data.get("result_status", "PASS")
        self.failed_courses = data.get("failed_courses", [])
        self.attempt_label = data.get("attempt_label", "MAIN")
        self.attempt_number = data.get("attempt_number", 0)
        self.attempt_indicator = data.get("attempt_indicator")

        # Adapt courses
        courses_dict = {}
        for idx, c in enumerate(data.get("courses", [])):
            ci = types.SimpleNamespace()
            for k, v in c.items():
                setattr(ci, k, v)
            if not hasattr(ci, "internal_marks"):
                ci.internal_marks = c.get("internal_obtained", 0.0)
            if not hasattr(ci, "effective_external"):
                ci.effective_external = c.get("external_obtained", 0.0)
            if not hasattr(ci, "total_marks"):
                ci.total_marks = c.get("total_obtained", 0.0)
            if not hasattr(ci, "credit_breakdown"):
                ci.credit_breakdown = None
            code_key = c.get("course_code", f"c_{idx}")
            courses_dict[code_key] = ci

        self.courses = courses_dict


def format_mark(val: Any) -> str:
    """Formats numeric or absent or exempted mark value cleanly."""
    if val is None or val == "":
        return "0"
    s = str(val).strip()
    if s.upper() in ("EX.", "EX", "EXEMPTED"):
        return "Ex."
    if s.upper() in ("AB", "ABSENT"):
        return "Ab"
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return f"{f:.1f}"
    except (ValueError, TypeError):
        return str(val)


def format_decimal(val: Any, places: int = 2) -> str:
    """Safely formats floating point numbers with specified decimal places."""
    if val is None or val == "":
        return "0.00"
    try:
        f = float(val)
        return f"{f:.{places}f}"
    except (ValueError, TypeError):
        return str(val)


def get_performance_description(sgpa: Optional[float], is_pass: bool) -> str:
    """Computes qualitative performance descriptor from SGPA."""
    if not is_pass:
        return "Fail"
    if sgpa is None:
        return "Pass"
    if sgpa >= 8.50:
        return "Outstanding"
    elif sgpa >= 8.00:
        return "Excellent"
    elif sgpa >= 7.50:
        return "Very Good"
    elif sgpa >= 6.50:
        return "Good"
    elif sgpa >= 6.00:
        return "Above Average"
    elif sgpa >= 5.00:
        return "Average"
    else:
        return "Pass"


class MarksheetPdfGenerator:
    """
    Renders high-resolution official SGPGIMS marksheet PDFs.
    Uses Jinja2 and Playwright with exact Legal 8.5" x 14" (0.25in margins) print specifications.
    """

    def __init__(self, template_dir: str = TEMPLATES_DIR):
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        self.jinja_env.filters["format_mark"] = format_mark
        self.jinja_env.filters["format_decimal"] = format_decimal
        self.template = self.jinja_env.get_template("marksheet_template.html")

    def render_html(
        self,
        student: EvaluatedStudentRecord,
        semester_number: int = 1,
        session_month_year: str = "JANUARY - 2026",
        issue_date: Optional[str] = None,
        template_config: Optional[MarksheetTemplateConfig] = None
    ) -> str:
        """Renders HTML marksheet string for a candidate matching approved SGPGIMS format."""
        cfg = template_config or get_template_config()
        sem_def = SEMESTER_DEFINITIONS.get(semester_number)
        total_prescribed = sem_def.total_prescribed_credits if sem_def else 14

        is_passed = "PASS" in student.result_status
        perf_descriptor = get_performance_description(student.sgpa, is_passed)

        # Build clean display result status
        if student.failed_courses:
            failed_str = ", ".join(student.failed_courses).upper()
            display_result = f"FAIL IN {failed_str}"
        elif "PASS WITH" in student.result_status:
            display_result = student.result_status
        elif is_passed:
            display_result = "PASS"
        else:
            display_result = student.result_status or "FAIL"

        # Explicit Course Ordering:
        # Row 01: ENGL 101 | Communicative English
        # Row 02: ANAT 105 & PHYS 110 | Applied Anatomy & Applied Physiology
        # Row 03: SOCI 115 & PSYC 120 | Applied Sociology & Applied Psychology
        def sem_course_sort_order(c) -> int:
            code = (getattr(c, "course_code", None) or "").upper()
            title = (getattr(c, "course_title", None) or "").upper()
            comp = (str(getattr(c, "component_name", "")) + "_" + str(getattr(c, "course_key", ""))).upper()
            # Semester 1
            if "ENGL" in code or "ENGLISH" in title or getattr(c, "is_english_or_elective", False):
                return 1
            if "ANAT" in code or "ANATOMY" in title:
                return 2
            if "SOCI" in code or "SOCIOLOGY" in title:
                return 3
            # Semester 2
            if "BIOC" in code or "NUTR" in code or "BIOCHEMISTRY" in title:
                return 10
            if "N-NF" in code or "FOUNDATION" in title:
                if "PRACT" in comp or "PRACT" in title:
                    return 12
                return 11
            if "HNIT" in code or "INFORMATICS" in title:
                return 13
            # Semester 3
            if "MICR" in code or "MICROBIOLOGY" in title:
                return 20
            if ("AHN" in code or "ADULT HEALTH" in title) and ("PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50):
                return 22
            if "AHN" in code or "ADULT HEALTH" in title:
                return 21
            # Semester 4
            if "PHAR" in code or "PATH" in code or "PHARMACOLOGY" in title:
                return 30
            if ("AHN" in code or "ADULT HEALTH" in title) and ("PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50):
                return 32
            if "AHN" in code or "ADULT HEALTH" in title:
                return 31
            if "PROF" in code or "PROFESSIONALISM" in title:
                return 33
            if "ELECTIVE" in code or "ELECTIVE" in title:
                return 34
            # Semester 5
            if ("COMH" in code or "COMMUNITY" in title) and ("PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50):
                return 43
            if "COMH" in code or "COMMUNITY" in title:
                return 40
            if "EDUC" in code or "EDUCATION" in title:
                return 41
            if "FORN" in code or "FORENSIC" in title:
                return 42
            # Semester 6
            if ("CHN" in code or "CHILD HEALTH" in title) and ("PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50):
                return 53
            if "CHN" in code or "CHILD HEALTH" in title:
                return 50
            if ("MHN" in code or "MENTAL HEALTH" in title) and ("PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50):
                return 54
            if "MHN" in code or "MENTAL HEALTH" in title:
                return 51
            if "NMLE" in code or "LEADERSHIP" in title or "MANAGEMENT" in title:
                return 52
            # Semester 7
            if ("(II)" in code or "401" in code or "COMH_II" in comp) and ("COMH" in code or "COMMUNITY" in title):
                if "PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50:
                    return 64
                return 60
            if "NRST" in code or "RESEARCH" in title or "STATISTICS" in title:
                return 61
            if "OBGN" in code or "MIDW" in code or "OBSTETRICS" in title or "OBG" in title:
                if "PRACT" in comp or "PRACT" in title or getattr(c, "internal_max", 0) >= 50:
                    return 63
                return 62
            # Semester 8
            if "INTE" in code or "COMPETENCY" in title or "COMPETENCY" in comp:
                return 70
            if "ELECTIVE-3" in code or "SCIENTIFIC WRITING" in title or "ELECTIVE_3" in comp:
                return 71
            return 99

        course_list = list(student.courses.values()) if student.courses else []
        course_list.sort(key=sem_course_sort_order)

        if not issue_date:
            issue_date = cfg.issue_date or datetime.now().strftime("%d/%m/%Y")

        attempt_label = getattr(student, "attempt_label", None)
        attempt_indicator = getattr(student, "attempt_indicator", None)
        if not attempt_indicator and attempt_label and attempt_label != "MAIN":
            attempt_indicator = f"({attempt_label})"

        html_content = self.template.render(
            student=student,
            course_rows=course_list,
            semester_number=semester_number,
            session_month_year=session_month_year,
            attempt_label=attempt_label,
            attempt_indicator=attempt_indicator,
            total_prescribed_credits=total_prescribed,
            performance_descriptor=perf_descriptor,
            display_result=display_result,
            issue_date=issue_date,
            format_mark=format_mark,
            format_decimal=format_decimal,
            template_config=cfg
        )
        return html_content

    def generate_student_pdf(
        self,
        student: EvaluatedStudentRecord,
        semester_number: int = 1,
        session_month_year: str = "JANUARY - 2026",
        issue_date: Optional[str] = None,
        template_config: Optional[MarksheetTemplateConfig] = None
    ) -> bytes:
        """Generates single high-res Legal (8.5x14) PDF bytes using Playwright."""
        cfg = template_config or get_template_config()
        html_content = self.render_html(student, semester_number, session_month_year, issue_date, cfg)

        with _ensure_proactor_loop_on_windows():
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                try:
                    page = browser.new_page()
                    page.set_content(html_content, wait_until="load", timeout=15000)
                    pdf_bytes = page.pdf(
                        format="Legal",
                        print_background=True,
                        prefer_css_page_size=True,
                        margin={"top": cfg.top_margin, "bottom": cfg.bottom_margin, "left": cfg.left_margin, "right": cfg.right_margin}
                    )
                finally:
                    browser.close()

        return pdf_bytes

    def generate_bulk_zip(
        self,
        students: List[EvaluatedStudentRecord],
        semester_number: int = 1,
        session_month_year: str = "JANUARY - 2026",
        issue_date: Optional[str] = None,
        template_config: Optional[MarksheetTemplateConfig] = None
    ) -> bytes:
        """
        Renders all student marksheets in batch and packages them
        into a compressed .zip archive in-memory.
        """
        cfg = template_config or get_template_config()
        zip_buffer = io.BytesIO()

        with _ensure_proactor_loop_on_windows():
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                context = browser.new_context()

                try:
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        used_filenames = set()
                        page = context.new_page()

                        for idx, student in enumerate(students, start=1):
                            try:
                                html_content = self.render_html(student, semester_number, session_month_year, issue_date, cfg)
                                page.set_content(html_content, wait_until="load", timeout=15000)
                                pdf_bytes = page.pdf(
                                    format="Legal",
                                    print_background=True,
                                    prefer_css_page_size=True,
                                    margin={"top": cfg.top_margin, "bottom": cfg.bottom_margin, "left": cfg.left_margin, "right": cfg.right_margin}
                                )

                                clean_name = clean_filename_token(student.student_name) or f"STUDENT_{idx}"
                                clean_roll = clean_filename_token(student.roll_no) or f"ROLL_{idx}"
                                base_filename = f"Marksheet_{clean_roll}_{clean_name}.pdf"

                                pdf_filename = base_filename
                                counter = 1
                                while pdf_filename in used_filenames:
                                    pdf_filename = f"Marksheet_{clean_roll}_{clean_name}_{counter}.pdf"
                                    counter += 1
                                used_filenames.add(pdf_filename)

                                zf.writestr(pdf_filename, pdf_bytes)
                            except Exception as item_err:
                                logger.warning(f"Error rendering marksheet for student {student.roll_no}: {item_err}", exc_info=True)
                                # If page crashed, recreate it for remaining students
                                try:
                                    page.close()
                                except Exception:
                                    pass
                                page = context.new_page()

                        try:
                            page.close()
                        except Exception:
                            pass
                finally:
                    context.close()
                    browser.close()

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
