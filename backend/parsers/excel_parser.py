"""
Dynamic Excel Ingestion Parser for B.Sc. Nursing Examination Data
Supports .xlsx and .xls formats with multi-row headers and dynamic schema mapping.
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
"""

import re
import io
from typing import Dict, List, Optional, Tuple, Any, Union
import openpyxl
import pandas as pd

from backend.grading import calculate_inc_grade, compute_sgpa
from backend.parsers.exam_cell_parser import (
    unmerge_and_replicate_cells,
    robust_load_workbook,
    clean_excel_filters_xml,
    patch_openpyxl_filters,
)
from backend.schemas.course_schemas import (
    SEMESTER_DEFINITIONS,
    SemesterDefinition,
    CourseDefinition,
)
from backend.schemas.student_schemas import (
    StudentDemographics,
    SubComponentMark,
    EvaluatedCourseComponent,
    SemesterStudentResult,
    IngestionResponse,
)


def clean_str(val: Any) -> str:
    """Clean string values from Excel cells."""
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip()
    # Normalize excessive internal whitespace
    return re.sub(r'\s+', ' ', s)


def is_exempt_token(val: Any) -> bool:
    """Checks whether a cell contains an exemption marker (e.g. 'X', 'Ex.')."""
    if val is None or pd.isna(val):
        return False
    s = str(val).strip().upper()
    return s in ["X", "EX", "EX.", "EXEMPTED", "NA", "N/A"]


def parse_numeric_with_grace(val: Any) -> Tuple[Optional[float], float, bool]:
    """
    Parses cell values that may contain:
    - Pure numbers: 23, 23.5
    - Strings with formulas: '37+0.5=37.5' or '37+1'
    - Absent indicators: 'Ab', 'AB', 'Absent', '-'
    Returns: (obtained_float, grace_marks, is_absent)
    """
    if val is None or pd.isna(val):
        return None, 0.0, False

    s = str(val).strip()
    if not s:
        return None, 0.0, False

    if s.upper() in ["AB", "ABSENT", "A"]:
        return None, 0.0, True

    if s.upper() in ["-", "X", "EX", "EX.", "EXEMPTED", "NA", "N/A"]:
        return None, 0.0, False

    # Check for grace mark pattern e.g. "35+2.5 grace marks =38", "37+0.5=37.5", "35+2.5-37.5", "37+0.5"
    grace_match = re.search(r'([\d\.]+)\s*\+\s*([\d\.]+)(?:[^\d=\-]*[=\-]\s*([\d\.]+))?', s, re.IGNORECASE)
    if grace_match:
        base = float(grace_match.group(1))
        grace = float(grace_match.group(2))
        total = float(grace_match.group(3)) if grace_match.group(3) else (base + grace)
        return total, grace, False

    try:
        num = float(s)
        return num, 0.0, False
    except ValueError:
        return None, 0.0, False


def compute_pure_total(internal_obtd: Optional[float], external_obtd: Optional[float], course_grace: float = 0.0) -> Optional[float]:
    """
    Ingestion Isolation Rule:
    Strictly calculates total marks from raw components (IA + EA + Grace).
    Never trusts pre-calculated Excel sheet totals.
    """
    if internal_obtd is None and external_obtd is None:
        return None
    return round((internal_obtd or 0.0) + (external_obtd or 0.0) + (course_grace or 0.0), 2)


def detect_semester_from_text(text: str) -> Optional[int]:
    """Detects semester number (1-8) from sheet text, sheet names, or filenames."""
    t = text.lower()

    # 1. Distinct course codes and subjects first (unambiguous across semesters)
    if any(k in t for k in ['inte 415', 'inte - 415', 'intensive clinical', 'competency assessment', 'elective-3', 'scientific writing']):
        return 8
    if any(k in t for k in ['midw/obgn', 'midw', 'obgn', 'nrst 405', 'nrst', 'nursing research & statistics', 'nursing research and statistics', 'n-comh (ii)', 'comh (ii)', 'comh-ii']):
        return 7
    if any(k in t for k in ['child health', 'n-chn', 'n-mhn', 'nmle 330', 'nmle', 'mental health nursing']):
        return 6
    if any(k in t for k in ['community health', 'n-comh', 'n-educ', 'educ 315', 'n-forn', 'forn 320', 'forensic nursing', 'educational technology']):
        return 5
    if any(k in t for k in ['phar 205', 'path 210', 'ahn (ii)', 'ahn ii', 'prof 230', 'pharmacology']):
        return 4
    if any(k in t for k in ['micr-201', 'micr 201', 'ahn (i)', 'ahn i', 'microbiology']) and 'ahn (ii)' not in t and 'ahn ii' not in t:
        return 3
    if any(k in t for k in ['bioc 135', 'nutr 140', 'biochemistry', 'n-nf', 'hnit 145', 'hnit']):
        return 2
    if any(k in t for k in ['anat', 'phys', 'soci', 'psyc', 'engl', 'anatomy', 'physiology', 'sociology', 'psychology', 'communicative english']):
        return 1

    # 2. Standard semester keywords
    mapping = {
        "eighth semester": 8, "8th semester": 8, "sem 8": 8, "sem-8": 8, "sem 08": 8, "sem-08": 8, "semester 8": 8, "semester viii": 8, "8th sem": 8,
        "seventh semester": 7, "7th semester": 7, "sem 7": 7, "sem-7": 7, "sem 07": 7, "sem-07": 7, "semester 7": 7, "semester vii": 7, "7th sem": 7,
        "sixth semester": 6, "6th semester": 6, "sem 6": 6, "sem-6": 6, "sem 06": 6, "sem-06": 6, "semester 6": 6, "semester vi": 6, "6th sem": 6,
        "fifth semester": 5, "5th semester": 5, "sem 5": 5, "sem-5": 5, "sem 05": 5, "sem-05": 5, "semester 5": 5, "semester v": 5, "5th sem": 5,
        "fourth semester": 4, "4th semester": 4, "sem 4": 4, "sem-4": 4, "sem 04": 4, "sem-04": 4, "semester 4": 4, "semester iv": 4, "4th sem": 4,
        "third semester": 3, "3rd semester": 3, "sem 3": 3, "sem-3": 3, "sem 03": 3, "sem-03": 3, "semester 3": 3, "semester iii": 3, "3rd sem": 3,
        "second semester": 2, "2nd semester": 2, "sem 2": 2, "sem-2": 2, "sem 02": 2, "sem-02": 2, "semester 2": 2, "semester ii": 2, "2nd sem": 2,
        "first semester": 1, "1st semester": 1, "sem 1": 1, "sem-1": 1, "sem 01": 1, "sem-01": 1, "semester 1": 1, "semester i": 1, "1st sem": 1,
    }
    for k, v in mapping.items():
        if k in t:
            return v
    return None


def detect_exam_session_from_text(text: str) -> Optional[str]:
    """Detects exam session string like 'January - 2026', 'July, 2026', or 'August 2025'."""
    months = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)'
    match = re.search(rf'({months}[\s,\-]+20\d\d)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


class ExcelSheetParser:
    """
    Parser for SGPGIMS B.Sc. Nursing Examination Sheets.
    """

    def __init__(
        self,
        file_content: bytes,
        filename: str,
        explicit_semester: Optional[int] = None,
        sheet_name: Optional[str] = None
    ):
        self.file_content = file_content
        self.filename = filename
        self.explicit_semester = explicit_semester
        self.sheet_name = sheet_name
        self.warnings: List[str] = []

    def parse(self) -> IngestionResponse:
        wb = robust_load_workbook(self.file_content, data_only=True)
        if self.sheet_name and self.sheet_name in wb.sheetnames:
            sheet = wb[self.sheet_name]
        else:
            sheet = None
            for s_name in wb.sheetnames:
                s_lower = s_name.lower()
                if any(k in s_lower for k in ["semester", "sem", "data", "master"]) and "sample" not in s_lower:
                    sheet = wb[s_name]
                    break
            if not sheet:
                sheet = wb.active

        # 0. Deterministic Cell Unmerging
        unmerge_and_replicate_cells(sheet)

        # 1. Detect semester & exam session
        detected_sem = self.explicit_semester
        exam_session = "January - 2026"

        # Read top header tokens across rows 1 to 6 and columns 1 to 32
        hdr_tokens: List[str] = []
        for r in range(1, min(7, sheet.max_row + 1)):
            for c in range(1, min(32, sheet.max_column + 1)):
                val = clean_str(sheet.cell(r, c).value)
                if val:
                    hdr_tokens.append(val)
                    es = detect_exam_session_from_text(val)
                    if es:
                        exam_session = es
        full_hdr_text = " ".join(hdr_tokens)

        if not detected_sem:
            # First check for distinct course codes/titles in sheet header content
            hdr_sem = detect_semester_from_text(full_hdr_text)
            fn_sem = detect_semester_from_text(self.filename) if self.filename else None
            title_sem = detect_semester_from_text(sheet.title) if sheet.title else None

            if hdr_sem:
                detected_sem = hdr_sem
            elif fn_sem:
                detected_sem = fn_sem
            elif title_sem:
                detected_sem = title_sem

        if not detected_sem:
            detected_sem = 1  # Default fallback if not found
            self.warnings.append("Semester could not be explicitly detected from header. Defaulting to Semester 1.")

        if exam_session == "January - 2026":
            es = detect_exam_session_from_text(self.filename) or detect_exam_session_from_text(sheet.title)
            if es:
                exam_session = es

        sem_def = SEMESTER_DEFINITIONS.get(detected_sem, SEMESTER_DEFINITIONS[1])

        # 2. Locate header row containing 'Roll No' or 'Name' or 'Enroll'
        header_row_idx = None
        col_map: Dict[str, int] = {}

        for r in range(1, min(10, sheet.max_row + 1)):
            row_vals = [clean_str(sheet.cell(r, c).value).lower() for c in range(1, sheet.max_column + 1)]
            has_roll = any("roll" in v for v in row_vals)
            has_name = any("name" in v for v in row_vals)
            if has_roll and has_name:
                header_row_idx = r
                break

        if not header_row_idx:
            header_row_idx = 3  # typical default
            self.warnings.append("Exact table header row not recognized automatically. Assuming data starts after row 3.")

        # Map demographic columns
        for c in range(1, sheet.max_column + 1):
            val = clean_str(sheet.cell(header_row_idx, c).value).lower()
            if "s.no" in val or "sl.no" in val or "sr.no" in val:
                col_map["sno"] = c
            elif "name" in val and "father" not in val and "college" not in val:
                if "name" not in col_map:
                    col_map["name"] = c
            elif "father" in val or "s/o" in val or "d/o" in val:
                col_map["father_name"] = c
            elif "enroll" in val:
                col_map["enroll_no"] = c
            elif "roll" in val:
                col_map["roll_no"] = c

        # Fallback if demographic columns are standard positions
        if "name" not in col_map:
            col_map["name"] = 2
        if "father_name" not in col_map:
            col_map["father_name"] = 3
        if "enroll_no" not in col_map:
            col_map["enroll_no"] = 4
        if "roll_no" not in col_map:
            col_map["roll_no"] = 5
        if "sno" not in col_map:
            col_map["sno"] = 1

        # 3. Parse student records row by row
        results: List[SemesterStudentResult] = []
        data_start_row = header_row_idx + 1

        # Check if row data_start_row is a subheader (like Int, Ex, etc.)
        row_check = [clean_str(sheet.cell(data_start_row, c).value).lower() for c in range(1, 10)]
        if any("int" in v or "ex" in v or "total" in v for v in row_check):
            data_start_row += 1

        for r in range(data_start_row, sheet.max_row + 1):
            name_val = clean_str(sheet.cell(r, col_map["name"]).value)
            roll_val = clean_str(sheet.cell(r, col_map["roll_no"]).value)

            # Skip empty rows, footer rows, header repeats, or summary rows
            if not name_val and not roll_val:
                continue
            nl = name_val.lower().replace(" ", "").replace("-", "")
            if nl in ["reappear", "main", "supplementary", "backlog", "preparedby", "checkedby"]:
                continue
            if any(k in name_val.lower() for k in ["total", "percentage", "prepared by", "checked by", "re - appear", "re-appear", "sub-dean", "principal", "controller", "batch 20"]):
                continue
            # A valid candidate record MUST have a roll number containing digits
            if not roll_val or not any(ch.isdigit() for ch in roll_val):
                continue

            sno_val = sheet.cell(r, col_map["sno"]).value
            try:
                sno = int(sno_val) if sno_val is not None and str(sno_val).isdigit() else None
            except Exception:
                sno = None

            father_val = clean_str(sheet.cell(r, col_map["father_name"]).value)
            enroll_val = clean_str(sheet.cell(r, col_map["enroll_no"]).value)

            # Clean roll number (handle float formatted rolls like 202201001.0)
            if roll_val.endswith(".0"):
                roll_val = roll_val[:-2]
            if enroll_val.endswith(".0"):
                enroll_val = enroll_val[:-2]

            demographics = StudentDemographics(
                serial_no=sno,
                name=name_val,
                father_name=father_val,
                enrollment_no=enroll_val,
                roll_no=roll_val
            )

            # Parse marks for this semester
            student_result = self._parse_student_semester_marks(sheet, r, demographics, sem_def, exam_session)
            results.append(student_result)

        passed_count = sum(1 for res in results if "PASS" in res.result_status.upper())
        failed_count = len(results) - passed_count

        return IngestionResponse(
            success=True,
            filename=self.filename,
            semester=detected_sem,
            examination_session=exam_session,
            total_students=len(results),
            passed_students=passed_count,
            failed_students=failed_count,
            results=results,
            warnings=self.warnings
        )

    def _parse_student_semester_marks(
        self,
        sheet,
        row_idx: int,
        demographics: StudentDemographics,
        sem_def: SemesterDefinition,
        exam_session: str
    ) -> SemesterStudentResult:
        """
        Parses marks for a student based on semester definition.
        Handles both column-relative layouts and standard column order.
        """
        eval_components: List[EvaluatedCourseComponent] = []
        failed_courses: List[str] = []
        has_grace_marks = False

        # Gather row values starting from col 6 (marks columns)
        # We also check for explicit column headers if available
        current_col = 6

        for course in sem_def.courses:
            for comp in course.components:
                # Based on course and component, extract internal and external marks
                # Default extraction looks at subsequent columns:
                # E.g. for Semester 1:
                # Course 1 (ANAT & PHYS): Int (col 6), Anat Ex (col 7), Phys Ex (col 8), Total (col 10)
                # Let's inspect sub-components
                sub_marks: List[SubComponentMark] = []
                internal_obtd: Optional[float] = None
                external_obtd: Optional[float] = None
                total_obtd: Optional[float] = None
                course_grace: float = 0.0
                is_absent = False

                if sem_def.semester_number == 1 and course.course_code == "ANAT 105 & PHYS 110":
                    # Anat & Phys: Int (col 6), Anat Ex (col 7), Phys Ex (col 8)
                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_anat, g_anat, ab_anat = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    v_phys, g_phys, ab_phys = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)

                    internal_obtd = v_int
                    course_grace = g_int + g_anat + g_phys
                    is_absent = ab_int or ab_anat or ab_phys

                    sub_marks.append(SubComponentMark(name="Applied Anatomy", code="ANAT 105", obtained=v_anat, max_marks=37.0, is_absent=ab_anat))
                    sub_marks.append(SubComponentMark(name="Applied Physiology", code="PHYS 110", obtained=v_phys, max_marks=38.0, is_absent=ab_phys))

                    # Total from cell 10 or sum
                    v_ext_tot, g_ext, _ = parse_numeric_with_grace(sheet.cell(row_idx, 9).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 10).value)
                    course_grace = g_int + g_anat + g_phys + g_ext + g_tot

                    if v_anat is not None and v_phys is not None:
                        external_obtd = v_anat + v_phys
                    elif v_ext_tot is not None:
                        external_obtd = v_ext_tot

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 13  # Next course starts around col 13 in DataSheet

                elif sem_def.semester_number == 1 and course.course_code == "SOCI 115 & PSYC 120":
                    # Int (col 13), Soci Ex (col 14), Psyc Ex (col 15), Ext Total (col 16), Total (col 17)
                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)
                    v_soci, g_soci, ab_soci = parse_numeric_with_grace(sheet.cell(row_idx, 14).value)
                    v_psyc, g_psyc, ab_psyc = parse_numeric_with_grace(sheet.cell(row_idx, 15).value)
                    v_ext_tot, g_ext, _ = parse_numeric_with_grace(sheet.cell(row_idx, 16).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 17).value)

                    course_grace = g_int + g_soci + g_psyc + g_ext + g_tot
                    internal_obtd = v_int
                    is_absent = ab_int or ab_soci or ab_psyc

                    sub_marks.append(SubComponentMark(name="Applied Sociology", code="SOCI 115", obtained=v_soci, max_marks=37.0, is_absent=ab_soci))
                    sub_marks.append(SubComponentMark(name="Applied Psychology", code="PSYC 120", obtained=v_psyc, max_marks=38.0, is_absent=ab_psyc))

                    if v_soci is not None and v_psyc is not None:
                        external_obtd = v_soci + v_psyc
                    elif v_ext_tot is not None:
                        external_obtd = v_ext_tot

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 20

                elif sem_def.semester_number == 1 and course.course_code == "ENGL 101":
                    # Communicative English: Int (col 20), Ex (col 21), Total (col 22)
                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 20).value)
                    v_ex, g_ex, ab_ex = parse_numeric_with_grace(sheet.cell(row_idx, 21).value)
                    internal_obtd = v_int
                    external_obtd = v_ex
                    course_grace = g_int + g_ex
                    is_absent = ab_int or ab_ex

                    tot_cell, _, _ = parse_numeric_with_grace(sheet.cell(row_idx, 22).value)
                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                elif sem_def.semester_number == 2 and course.course_code == "BIOC 135 & NUTR 140":
                    # Check if master tabulation layout (Int at 6, Univ Ex at 7, Grace at 8, Total at 9)
                    is_master_layout = False
                    for hr in range(4, 7):
                        c8_val = clean_str(sheet.cell(hr, 8).value).lower()
                        c7_val = clean_str(sheet.cell(hr, 7).value).lower()
                        if "grace" in c8_val or ("univ" in c7_val and "75" in c7_val):
                            is_master_layout = True
                            break

                    if is_master_layout:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                        v_gr, _, _ = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 9).value)

                        internal_obtd = v_int
                        external_obtd = v_ext
                        course_grace = g_int + g_ext + (v_gr or 0.0) + g_tot
                        is_absent = ab_int or ab_ext

                        total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)
                    else:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                        v_bioc, g_bioc, ab_bioc = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                        v_nutr, g_nutr, ab_nutr = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)
                        v_ext_tot, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 9).value)
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 10).value)

                        internal_obtd = v_int
                        course_grace = g_int + g_bioc + g_nutr + g_ext + g_tot
                        is_absent = ab_int or ab_bioc or ab_nutr or ab_ext

                        sub_marks.append(SubComponentMark(name="Applied Biochemistry", code="BIOC 135", obtained=v_bioc, max_marks=25.0, is_absent=ab_bioc))
                        sub_marks.append(SubComponentMark(name="Applied Nutrition & Dietetics", code="NUTR 140", obtained=v_nutr, max_marks=50.0, is_absent=ab_nutr))

                        if v_ext_tot is not None:
                            external_obtd = v_ext_tot
                        elif v_bioc is not None and v_nutr is not None:
                            external_obtd = v_bioc + v_nutr

                        total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 12

                elif sem_def.semester_number == 2 and course.course_code == "N-NF (I & II) 125" and comp.name == "Theory":
                    is_master_layout = False
                    for hr in range(4, 7):
                        c14_val = clean_str(sheet.cell(hr, 14).value).lower()
                        c8_val = clean_str(sheet.cell(hr, 8).value).lower()
                        if "grace" in c14_val or "grace" in c8_val:
                            is_master_layout = True
                            break

                    if is_master_layout:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 12).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)
                        v_gr, _, _ = parse_numeric_with_grace(sheet.cell(row_idx, 14).value)
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 15).value)
                    else:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 14).value)
                        v_gr = 0.0
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 15).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + (v_gr or 0.0) + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 18

                elif sem_def.semester_number == 2 and course.course_code == "N-NF (I & II) 125" and comp.name == "Practical":
                    is_master_layout = False
                    for hr in range(4, 7):
                        c20_val = clean_str(sheet.cell(hr, 20).value).lower()
                        c8_val = clean_str(sheet.cell(hr, 8).value).lower()
                        if "grace" in c20_val or "grace" in c8_val:
                            is_master_layout = True
                            break

                    if is_master_layout:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 18).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 19).value)
                        v_gr, _, _ = parse_numeric_with_grace(sheet.cell(row_idx, 20).value)
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 21).value)
                    else:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 18).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 19).value)
                        v_gr = 0.0
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 20).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + (v_gr or 0.0) + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 24

                elif sem_def.semester_number == 2 and (course.course_code == "HNIT 145" or "HNIT" in course.course_code):
                    is_master_layout = False
                    for hr in range(4, 7):
                        c26_val = clean_str(sheet.cell(hr, 26).value).lower()
                        c8_val = clean_str(sheet.cell(hr, 8).value).lower()
                        if "grace" in c26_val or "grace" in c8_val:
                            is_master_layout = True
                            break

                    if is_master_layout:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 24).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 25).value)
                        v_gr, _, _ = parse_numeric_with_grace(sheet.cell(row_idx, 26).value)
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 27).value)
                    else:
                        v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 23).value)
                        v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 24).value)
                        v_gr = 0.0
                        tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 25).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + (v_gr or 0.0) + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 30

                # SEMESTER 3 COURSES
                elif sem_def.semester_number == 3 and ("MICR" in course.course_code or "MICRO" in course.title.upper()):
                    # Applied Microbiology: Col 6: Int (25), Col 7: Micro (37), Col 8: Infc (38), Col 9: Total (75), Col 10: Total (100)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [6, 7, 8, 9, 10]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 13
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_micr, g_micr, ab_micr = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    v_infc, g_infc, ab_infc = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)
                    v_ext_tot, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 9).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 10).value)

                    internal_obtd = v_int
                    course_grace = g_int + g_micr + g_infc + g_ext + g_tot
                    is_absent = ab_int or ab_micr or ab_infc or ab_ext

                    sub_marks.append(SubComponentMark(name="Microbiology", code="MICR", obtained=v_micr, max_marks=37.0, is_absent=ab_micr))
                    sub_marks.append(SubComponentMark(name="Infection Control", code="INFC", obtained=v_infc, max_marks=38.0, is_absent=ab_infc))

                    if v_ext_tot is not None:
                        external_obtd = v_ext_tot
                    elif v_micr is not None and v_infc is not None:
                        external_obtd = v_micr + v_infc

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 13

                elif sem_def.semester_number == 3 and ("AHN" in course.course_code or "ADULT HEALTH" in course.title.upper()) and comp.name == "Theory":
                    # Adult Health Nursing I Theory: Int (col 13), Total Ex (col 14), Total (col 15)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [13, 14, 15]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 18
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 14).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 15).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 18

                elif sem_def.semester_number == 3 and ("AHN" in course.course_code or "ADULT HEALTH" in course.title.upper()) and comp.name == "Practical":
                    # Adult Health Nursing I Practical: Int (col 18), Ex (col 19), Total (col 20)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [18, 19, 20]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 23
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 18).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 19).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 20).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 23

                # SEMESTER 4 COURSES
                elif sem_def.semester_number == 4 and ("PHAR" in course.course_code or "PATH" in course.course_code or "PHARMACOLOGY" in course.title.upper()):
                    # Pharmacology, Pathology & Genetics:
                    # Col 6: Int (25), Col 7: PHAR Ex (38), Col 8: PATH Ex (25), Col 9: GEN (12), Col 10: Total (75), Col 11: Total (100)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [6, 7, 8, 9, 10, 11]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 14
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_phar, g_phar, ab_phar = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    v_path, g_path, ab_path = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)
                    v_gen, g_gen, ab_gen = parse_numeric_with_grace(sheet.cell(row_idx, 9).value)
                    v_ext_tot, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 10).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 11).value)

                    internal_obtd = v_int
                    course_grace = g_int + g_phar + g_path + g_gen + g_ext + g_tot
                    is_absent = ab_int or ab_phar or ab_path or ab_gen or ab_ext

                    sub_marks.append(SubComponentMark(name="Pharmacology (I & II)", code="PHAR 205", obtained=v_phar, max_marks=38.0, is_absent=ab_phar))
                    sub_marks.append(SubComponentMark(name="Pathology (I & II)", code="PATH 210", obtained=v_path, max_marks=25.0, is_absent=ab_path))
                    sub_marks.append(SubComponentMark(name="Genetics", code="GEN", obtained=v_gen, max_marks=12.0, is_absent=ab_gen))

                    if v_ext_tot is not None:
                        external_obtd = v_ext_tot
                    elif v_phar is not None and v_path is not None and v_gen is not None:
                        external_obtd = v_phar + v_path + v_gen

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 14

                elif sem_def.semester_number == 4 and ("AHN" in course.course_code or "ADULT HEALTH" in course.title.upper()) and comp.name == "Theory":
                    # Adult Health Nursing II Theory: Int (col 14), Univ Exam (col 15), Total (col 16)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [14, 15, 16]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 19
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 14).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 15).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 16).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 19

                elif sem_def.semester_number == 4 and ("AHN" in course.course_code or "ADULT HEALTH" in course.title.upper()) and comp.name == "Practical":
                    # Adult Health Nursing II Practical: Int (col 19), Univ Exam (col 20), Total (col 21)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [19, 20, 21]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 24
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 19).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 20).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 21).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 24

                elif sem_def.semester_number == 4 and ("PROF" in course.course_code or "PROFESSIONALISM" in course.title.upper()):
                    # Professionalism, Ethics & Professional Values: Int (col 24), College Exam (col 25), Total (col 26)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [24, 25, 26]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 29
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 24).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 25).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 26).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 29

                elif sem_def.semester_number == 4 and course.is_english_or_elective:
                    # Elective module - skip if not examined in sheet
                    if sheet.max_column < 33:
                        continue

                # SEMESTER 5 COURSES
                elif sem_def.semester_number == 5 and ("COMH" in course.course_code or "COMMUNITY" in course.title.upper()) and comp.name == "Theory":
                    # Community Health Nursing I Theory: Int (col 6), Ex (col 7), Total (col 8)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [6, 7, 8]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 11
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 11

                elif sem_def.semester_number == 5 and ("EDUC" in course.course_code or "EDUCATION" in course.title.upper()):
                    # Educational Technology: Int (col 11), Ex (col 12), Total (col 13)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [11, 12, 13]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 16
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 11).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 12).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 16

                elif sem_def.semester_number == 5 and ("FORN" in course.course_code or "FORENSIC" in course.title.upper()):
                    # Forensic Nursing: Int (col 16), Ex (col 17), Total (col 18)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [16, 17, 18]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 21
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 16).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 17).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 18).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 21

                elif sem_def.semester_number == 5 and ("COMH" in course.course_code or "COMMUNITY" in course.title.upper()) and comp.name == "Practical":
                    # Community Health Nursing I Practical: Int (col 21), Ex (col 22), Total (col 23)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [21, 22, 23]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 26
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 21).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 22).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 23).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 26

                # SEMESTER 6 COURSES
                elif sem_def.semester_number == 6 and ("CHN" in course.course_code or "CHILD" in course.title.upper()) and comp.name == "Theory":
                    # Child Health Nursing Theory: Int (col 6), Ex (col 7), Total (col 8)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [6, 7, 8]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 11
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 11

                elif sem_def.semester_number == 6 and ("MHN" in course.course_code or "MENTAL" in course.title.upper()) and comp.name == "Theory":
                    # Mental Health Nursing Theory: Int (col 11), Ex (col 12), Total (col 13)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [11, 12, 13]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 16
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 11).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 12).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 16

                elif sem_def.semester_number == 6 and ("NMLE" in course.course_code or "MANAGEMENT" in course.title.upper()):
                    # Nursing Management & Leadership: Int (col 16), Ex (col 17), Total (col 18)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [16, 17, 18]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 21
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 16).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 17).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 18).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 21

                elif sem_def.semester_number == 6 and ("CHN" in course.course_code or "CHILD" in course.title.upper()) and comp.name == "Practical":
                    # Child Health Nursing Practical: Int (col 21), Ex (col 22), Total (col 23)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [21, 22, 23]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 26
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 21).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 22).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 23).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 26

                elif sem_def.semester_number == 6 and ("MHN" in course.course_code or "MENTAL" in course.title.upper()) and comp.name == "Practical":
                    # Mental Health Nursing Practical: Int (col 26), Ex (col 27), Total (col 28)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [26, 27, 28]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 31
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 26).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 27).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 28).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 31

                elif sem_def.semester_number == 6 and course.is_english_or_elective:
                    # Elective module - skip if not in sheet
                    if sheet.max_column < 36:
                        continue

                # SEMESTER 7 COURSES
                elif sem_def.semester_number == 7 and ("COMH" in course.course_code or "COMMUNITY" in course.title.upper()) and comp.name == "Theory":
                    # Community Health Nursing II Theory: Int (col 6), Ex (col 7), Total (col 8)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [6, 7, 8]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 11
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 11

                elif sem_def.semester_number == 7 and ("NRST" in course.course_code or "RESEARCH" in course.title.upper()):
                    # Nursing Research & Statistics: Int (col 11), NUR (col 12), STAT (col 13), Ex Tot (col 14), Total (col 15)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [11, 12, 13, 14, 15]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 18
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 11).value)
                    v_nur, g_nur, ab_nur = parse_numeric_with_grace(sheet.cell(row_idx, 12).value)
                    v_stat, g_stat, ab_stat = parse_numeric_with_grace(sheet.cell(row_idx, 13).value)
                    v_ext_tot, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 14).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 15).value)

                    internal_obtd = v_int
                    course_grace = g_int + g_nur + g_stat + g_ext + g_tot
                    is_absent = ab_int or ab_nur or ab_stat or ab_ext

                    sub_marks.append(SubComponentMark(name="Nursing Research", code="NRST 405 (NUR)", obtained=v_nur, max_marks=55.0, is_absent=ab_nur))
                    sub_marks.append(SubComponentMark(name="Statistics", code="NRST 405 (STAT)", obtained=v_stat, max_marks=20.0, is_absent=ab_stat))

                    if v_ext_tot is not None:
                        external_obtd = v_ext_tot
                    elif v_nur is not None and v_stat is not None:
                        external_obtd = v_nur + v_stat

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 18

                elif sem_def.semester_number == 7 and ("MIDW" in course.course_code or "OBGN" in course.course_code or "OBG" in course.title.upper()) and comp.name == "Theory":
                    # Midwifery/OBG Nursing Theory: Int (col 18), Ex (col 19), Total (col 20)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [18, 19, 20]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 23
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 18).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 19).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 20).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 23

                elif sem_def.semester_number == 7 and ("MIDW" in course.course_code or "OBGN" in course.course_code or "OBG" in course.title.upper()) and comp.name == "Practical":
                    # Midwifery/OBG Nursing Practical: Int (col 23), Ex (col 24), Total (col 25)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [23, 24, 25]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 28
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 23).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 24).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 25).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 28

                elif sem_def.semester_number == 7 and ("COMH" in course.course_code or "COMMUNITY" in course.title.upper()) and comp.name == "Practical":
                    # Community Health Nursing II Practical: Int (col 28), Ex (col 29), Total (col 30)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [28, 29, 30]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 33
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 28).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 29).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 30).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 33

                # SEMESTER 8 COURSES
                elif sem_def.semester_number == 8 and ("INTE" in course.course_code or "COMPETENCY" in course.title.upper() or "CLINICAL" in course.title.upper()):
                    # Competency Assessment: Int (col 6), Ex (col 7), Total (col 8)
                    if any(is_exempt_token(sheet.cell(row_idx, c).value) for c in [6, 7, 8]):
                        eval_comp = EvaluatedCourseComponent(
                            course_code=course.course_code,
                            course_title=course.title,
                            component_name=comp.name,
                            credits=comp.credits or course.credits,
                            credit_breakdown=course.credit_breakdown,
                            internal_obtained=None,
                            internal_max=comp.ia_max,
                            external_obtained=None,
                            external_max=comp.ea_max,
                            total_obtained=None,
                            total_max=comp.total_max,
                            percentage=0.0,
                            letter_grade="Ex.",
                            grade_point=0,
                            is_pass=True,
                            grace_marks=0.0,
                            is_absent=False,
                            is_exempted=True,
                            is_english_or_elective=course.is_english_or_elective,
                            include_in_sgpa=False,
                            footnotes=course.footnotes
                        )
                        eval_components.append(eval_comp)
                        current_col = 11
                        continue

                    v_int, g_int, ab_int = parse_numeric_with_grace(sheet.cell(row_idx, 6).value)
                    v_ext, g_ext, ab_ext = parse_numeric_with_grace(sheet.cell(row_idx, 7).value)
                    tot_cell, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, 8).value)

                    internal_obtd = v_int
                    external_obtd = v_ext
                    course_grace = g_int + g_ext + g_tot
                    is_absent = ab_int or ab_ext

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col = 11

                elif sem_def.semester_number == 8 and course.is_english_or_elective:
                    # Elective module - skip if not in sheet
                    if sheet.max_column < 15:
                        continue

                else:
                    # General / dynamic extraction for any other semester course
                    v_ia, g_ia, ab_ia = parse_numeric_with_grace(sheet.cell(row_idx, current_col).value)
                    v_ea, g_ea, ab_ea = parse_numeric_with_grace(sheet.cell(row_idx, current_col + 1).value)
                    v_tot, g_tot, _ = parse_numeric_with_grace(sheet.cell(row_idx, current_col + 2).value)

                    internal_obtd = v_ia
                    external_obtd = v_ea
                    course_grace = g_ia + g_ea + g_tot
                    is_absent = ab_ia or ab_ea

                    total_obtd = compute_pure_total(internal_obtd, external_obtd, course_grace)

                    current_col += 3

                # Passing threshold verification
                pass_cutoff_pct = 0.40 if course.is_english_or_elective else 0.50
                ia_pass = (internal_obtd is not None) and (internal_obtd >= (comp.ia_max or 25.0) * pass_cutoff_pct)
                ea_pass = (external_obtd is not None) and ((external_obtd + course_grace) >= (comp.ea_max or 75.0) * pass_cutoff_pct)
                has_failed_threshold = not (ia_pass and ea_pass) if not is_absent else False

                # Grade Evaluation via INC 10-Point Scale Engine
                grade_res = calculate_inc_grade(
                    obtained_marks=total_obtd,
                    max_marks=comp.total_max,
                    is_english_or_elective=course.is_english_or_elective,
                    is_absent=is_absent,
                    has_failed_threshold=has_failed_threshold
                )

                if not grade_res.is_pass:
                    failed_courses.append(f"{course.title} ({comp.name})" if len(course.components) > 1 else course.title)

                eval_comp = EvaluatedCourseComponent(
                    course_code=course.course_code,
                    course_title=course.title,
                    component_name=comp.name,
                    credits=comp.credits or course.credits,
                    credit_breakdown=course.credit_breakdown,
                    internal_obtained=internal_obtd,
                    internal_max=comp.ia_max,
                    external_obtained=external_obtd,
                    external_max=comp.ea_max,
                    sub_components=sub_marks,
                    total_obtained=total_obtd,
                    total_max=comp.total_max,
                    percentage=grade_res.percentage,
                    letter_grade=grade_res.letter_grade,
                    grade_point=grade_res.grade_point,
                    is_pass=grade_res.is_pass,
                    grace_marks=course_grace,
                    is_absent=is_absent,
                    is_english_or_elective=course.is_english_or_elective,
                    include_in_sgpa=course.include_in_sgpa,
                    footnotes=course.footnotes
                )
                eval_components.append(eval_comp)

        # Semester totals & SGPA
        grand_total_obtd = sum(c.total_obtained or 0.0 for c in eval_components)
        grand_total_max = sum(c.total_max for c in eval_components)
        overall_pct = round((grand_total_obtd / grand_total_max) * 100.0, 2) if grand_total_max > 0 else 0.0

        sgpa, credit_score, eval_credits = compute_sgpa([
            {
                "credits": c.credits,
                "grade_point": c.grade_point,
                "include_in_sgpa": c.include_in_sgpa
            }
            for c in eval_components
        ])

        # Overall Status & Remarks from sheet
        sheet_remark: Optional[str] = None
        for col_idx in range(current_col, min(sheet.max_column + 1, current_col + 10)):
            cell_txt = clean_str(sheet.cell(row_idx, col_idx).value)
            if cell_txt:
                if "grace" in cell_txt.lower():
                    has_grace_marks = True
                    sheet_remark = cell_txt
                elif "pass" in cell_txt.lower() or "fail" in cell_txt.lower():
                    if not sheet_remark:
                        sheet_remark = cell_txt

        if any(c.grace_marks > 0 for c in eval_components):
            has_grace_marks = True

        if len(failed_courses) == 0:
            if has_grace_marks:
                result_status = "PASS WITH GRACE MARKS"
            else:
                result_status = "PASS"
        else:
            result_status = "FAIL"

        final_remarks = sheet_remark or (f"Fail in {', '.join(failed_courses)}" if failed_courses else None)

        return SemesterStudentResult(
            student=demographics,
            semester_number=sem_def.semester_number,
            degree_title="B.Sc. NURSING",
            examination_session=exam_session,
            college_name=sem_def.college_name,
            college_code=sem_def.college_code or "1313",
            courses=eval_components,
            grand_total_obtained=grand_total_obtd,
            grand_total_max=grand_total_max,
            overall_percentage=overall_pct,
            sgpa=sgpa,
            total_credit_score=credit_score,
            total_sgpa_credits=eval_credits,
            result_status=result_status,
            failed_courses=failed_courses,
            remarks=final_remarks
        )
