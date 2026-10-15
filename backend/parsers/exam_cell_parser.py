"""
Examination Cell Ingestion, Parsing & Sanitization Engine
Phase 1B: Deterministic Merged-Cell Excel Parser Adapter
Branding: VidyaMarksheet (VidyaLabs)
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
"""

import re
import io
from typing import Dict, List, Optional, Tuple, Any, Union
import openpyxl
import pandas as pd

from backend.schemas.canonical_models import (
    StudentRecord,
    AnatPhysRecord,
    SociPsycRecord,
    EnglRecord,
    BiocNutrRecord,
    NnfTheoryRecord,
    NnfPractRecord,
    HnitRecord,
    format_numeric_token,
)

FOOTER_SIGNATURE_MARKERS = [
    "prepared by",
    "checked by",
    "teaching staff",
    "mr vinod kumar gupta",
    "mr. vinod kumar gupta",
    "dr. radha k.",
    "dr radha k",
    "dr. radha",
    "dean",
    "sub-dean (nursing)",
    "sub-dean",
    "executive registrar",
    "controller of examination",
    "controller of examinations",
    "percentage",
    "total students",
    "legend overleaf",
]


def unmerge_and_replicate_cells(ws) -> None:
    """
    Deterministic Cell Unmerging:
    Iterates over sheet.merged_cells.ranges. For every merged bounding box,
    replicates the top-left cell's value across all coordinates within the range,
    and unmerges the range.
    """
    merged_ranges = list(ws.merged_cells.ranges)
    for rng in merged_ranges:
        top_left_val = ws.cell(rng.min_row, rng.min_col).value
        ws.unmerge_cells(range_string=str(rng))
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                ws.cell(r, c).value = top_left_val


def clean_text_string(val: Any) -> str:
    """Cleans text values from cell, collapsing extra whitespaces."""
    if val is None or pd.isna(val):
        return ""
    s = str(val).strip()
    return re.sub(r'\s+', ' ', s)


def clean_demographic_id(val: Any) -> str:
    """
    Cleans demographic ID fields (Roll No, Enroll No):
    Converts scientific notation, float integers (e.g. 202501001.0, 2.02501E+08) to clean strings.
    """
    if val is None or pd.isna(val):
        return ""
    if isinstance(val, (int, float)):
        try:
            int_val = int(round(val))
            if abs(val - int_val) < 1e-4:
                return str(int_val)
        except Exception:
            pass
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    # Check scientific notation
    if re.match(r'^\d+\.?\d*[eE][+-]?\d+$', s):
        try:
            return str(int(round(float(s))))
        except Exception:
            pass
    return s


def parse_grace_expression(raw_val: Any) -> Tuple[Optional[float], float, Optional[float], bool]:
    """
    Regex extractor for raw cell scores and grace expressions:
    - Raw patterns: "35+2.5-37.5", "37+0.5=37.5", "34+3.5-37.5", "35+2.5 grace marks =38", "35+2.5", "37.5"
    - Absent: "Ab", "AB", "Absent", "A"
    Returns: (raw_score, grace_awarded, total_effective, is_absent)
    """
    if raw_val is None or pd.isna(raw_val):
        return None, 0.0, None, False

    s = str(raw_val).strip()
    if not s or s == "-":
        return None, 0.0, None, False

    if s.upper() in ["AB", "ABSENT"]:
        return None, 0.0, None, True

    # Match: base + grace [-=] total (with optional phrases like 'grace marks')
    match = re.search(r'([\d\.]+)\s*\+\s*([\d\.]+)(?:[^\d=\-]*[=\-]\s*([\d\.]+))?', s)
    if match:
        raw_score = float(match.group(1))
        grace_awarded = float(match.group(2))
        total_effective = float(match.group(3)) if match.group(3) else round(raw_score + grace_awarded, 2)
        return raw_score, grace_awarded, total_effective, False

    try:
        num = float(s)
        return num, 0.0, num, False
    except ValueError:
        return None, 0.0, None, False


def is_exempt_token(val: Any) -> bool:
    """Checks if a cell indicates an exemption token like 'Ex.', 'EX', 'X', 'Exempted'."""
    if val is None or pd.isna(val):
        return False
    s = str(val).strip().upper()
    return s in ["X", "EX", "EX.", "EXEMPTED", "NA", "N/A"]


def is_footer_marker(row_values: List[str]) -> bool:
    """
    Checks if a row contains institutional footer signature markers.
    """
    row_text = " ".join([v.lower() for v in row_values if v])
    for marker in FOOTER_SIGNATURE_MARKERS:
        if marker in row_text:
            return True
    return False


def get_cell_value_resolving_merges(ws, row: int, col: int) -> str:
    """
    Returns the cell string value, resolving merged cell spans if cell is part of a merge.
    """
    cell = ws.cell(row, col)
    val = clean_text_string(cell.value)
    if val:
        return val
    if hasattr(ws, 'merged_cells') and hasattr(ws.merged_cells, 'ranges'):
        for merged_range in ws.merged_cells.ranges:
            if (merged_range.min_row <= row <= merged_range.max_row and
                    merged_range.min_col <= col <= merged_range.max_col):
                top_left_cell = ws.cell(merged_range.min_row, merged_range.min_col)
                return clean_text_string(top_left_cell.value)
    return ""


class ExamCellParserAdapter:
    """
    Deterministic Merged-Cell Excel Parser Adapter for raw Examination Cell Excel files.
    Branding: VidyaMarksheet (VidyaLabs)

    1. Cell Unmerging:
       - Loads the workbook using openpyxl.load_workbook(file, data_only=True).
       - Iterates over sheet.merged_cells.ranges, replicates top-left cell values across all coordinates, and unmerges.

    2. Data Row Identification:
       - Scans column 1 or column 5 for numeric Serial Numbers (1, 2, 3...) and Roll Numbers starting with '202'.
       - Terminates row reading immediately upon encountering institutional footer markers:
         'Prepared By', 'Checked by', 'Teaching Staff', 'Dr. Radha K.', 'DEAN'.

    3. Grace String Sanitizer:
       - Handles expression strings ('35+2.5-37.5', '37+0.5=37.5', '35+2.5 grace marks =38', '35+2.5').
       - Converts missing cells, empty strings, and '-' to 0. Preserves 'Ab' for absentees.
       - Flags student status with grace remarks.

    4. Output:
       - Returns an array of fully-populated StudentRecord objects containing exact numbers.
    """

    def __init__(self, file_content: bytes, sheet_name: Optional[str] = None, semester: Optional[int] = None):
        self.file_content = file_content
        self.sheet_name = sheet_name
        self.explicit_semester = semester
        self.warnings: List[str] = []

    def parse(self) -> List[StudentRecord]:
        wb = openpyxl.load_workbook(io.BytesIO(self.file_content), data_only=True)
        if self.sheet_name and self.sheet_name in wb.sheetnames:
            ws = wb[self.sheet_name]
        else:
            ws = None
            # Smart sheet detection: prefer sheet with 'semester', 'sem', 'master', 'data'
            for s_name in wb.sheetnames:
                s_lower = s_name.lower()
                if any(k in s_lower for k in ["semester", "sem", "data", "master"]) and "sample" not in s_lower:
                    ws = wb[s_name]
                    break
            if not ws:
                best_sheet = wb.active
                max_rows = best_sheet.max_row if best_sheet else 0
                for s_name in wb.sheetnames:
                    if wb[s_name].max_row > max_rows:
                        best_sheet = wb[s_name]
                        max_rows = wb[s_name].max_row
                ws = best_sheet or wb.active

        # 1. Deterministic Cell Unmerging
        unmerge_and_replicate_cells(ws)

        # 2. Detect Semester (1 to 6)
        detected_sem = self.explicit_semester or self._detect_semester(ws)
        self.detected_semester = detected_sem

        # 3. Dynamic Header Anchor Detection across rows 1 to 10
        anchors = self._detect_anchors(ws, detected_sem)
        data_start_row = anchors["data_start_row"]

        records: List[StudentRecord] = []

        # 4. Iterate data rows with footer truncation and page-break skipping
        for r in range(data_start_row, ws.max_row + 1):
            row_cells = [clean_text_string(ws.cell(r, c).value) for c in range(1, ws.max_column + 1)]

            # Check footer signature truncation
            if is_footer_marker(row_cells):
                # Check if there are further student records below this page footer
                has_more_students = False
                for future_r in range(r + 1, min(r + 15, ws.max_row + 1)):
                    fut_sno = clean_text_string(ws.cell(future_r, anchors["cols"].get("sno", 1)).value)
                    fut_roll = clean_demographic_id(ws.cell(future_r, anchors["cols"]["roll_no"]).value)
                    fut_name = clean_text_string(ws.cell(future_r, anchors["cols"]["student_name"]).value)
                    is_fut_sno = fut_sno.isdigit() and int(fut_sno) >= 1
                    is_fut_roll = fut_roll.startswith("202") or (fut_roll.isdigit() and len(fut_roll) >= 5)
                    if (is_fut_sno or is_fut_roll) and fut_name:
                        has_more_students = True
                        break
                if has_more_students:
                    continue  # Skip intermediate page-break signature block
                else:
                    break  # Final institutional footer reached: terminate row reading immediately

            # Demographics
            roll_raw = ws.cell(r, anchors["cols"]["roll_no"]).value
            name_raw = ws.cell(r, anchors["cols"]["student_name"]).value

            roll_clean = clean_demographic_id(roll_raw)
            name_clean = clean_text_string(name_raw)

            c1_raw = clean_text_string(ws.cell(r, anchors["cols"].get("sno", 1)).value)
            is_sno_valid = c1_raw.isdigit() and int(c1_raw) >= 1
            is_roll_valid = roll_clean.startswith("202") or (roll_clean.isdigit() and len(roll_clean) >= 5)

            # Skip rows that are neither roll starting with 202 nor valid serial number
            if not (is_sno_valid or is_roll_valid) or not name_clean:
                continue

            # Skip header, label, and template rows that are not real student candidates
            header_label_tokens = [
                "s/o", "d/o", "name of college", "college of nursing", "sgpgims",
                "course code", "title of course", "sl.no", "sl no", "serial no",
                "course credits", "internal assesment", "end semester", "total marks",
                "letter grade", "grade point", "legend overleaf", "college exam",
                "date :", "date:", "sub-dean", "prepared by", "checked by",
                "communicative english", "applied anatomy", "applied physiology",
                "applied sociology", "applied psychology", "applied biochemistry",
                "nursing foundation", "examination held in", "master tabulation",
                "result", "remark", "obtd", "max", "total", "percentage"
            ]
            nl = name_clean.lower().strip()
            if any(tok in nl for tok in header_label_tokens):
                continue
            if re.match(r'^\d+\.?$', nl):
                continue

            enroll_raw = ws.cell(r, anchors["cols"]["enroll_no"]).value if anchors["cols"].get("enroll_no") else ""
            father_raw = ws.cell(r, anchors["cols"]["father_name"]).value if anchors["cols"].get("father_name") else ""

            enroll_clean = clean_demographic_id(enroll_raw)
            father_clean = clean_text_string(father_raw)

            # Remarks cell
            remarks_col = anchors["cols"].get("remarks")
            raw_remarks = clean_text_string(ws.cell(r, remarks_col).value) if remarks_col else None

            # Course Marks Extraction based on detected semester
            if detected_sem == 8:
                courses_dict, enriched_remarks = self._extract_sem8_course_marks(ws, r, anchors, raw_remarks)
            elif detected_sem == 7:
                courses_dict, enriched_remarks = self._extract_sem7_course_marks(ws, r, anchors, raw_remarks)
            elif detected_sem == 6:
                courses_dict, enriched_remarks = self._extract_sem6_course_marks(ws, r, anchors, raw_remarks)
            elif detected_sem == 5:
                courses_dict, enriched_remarks = self._extract_sem5_course_marks(ws, r, anchors, raw_remarks)
            elif detected_sem == 4:
                courses_dict, enriched_remarks = self._extract_sem4_course_marks(ws, r, anchors, raw_remarks)
            elif detected_sem == 3:
                courses_dict, enriched_remarks = self._extract_sem3_course_marks(ws, r, anchors, raw_remarks)
            elif detected_sem == 2:
                courses_dict, enriched_remarks = self._extract_sem2_course_marks(ws, r, anchors, raw_remarks)
            else:
                courses_dict, enriched_remarks = self._extract_sem1_course_marks(ws, r, anchors, raw_remarks)

            student_rec = StudentRecord(
                roll_no=roll_clean,
                enroll_no=enroll_clean,
                student_name=name_clean,
                father_name=father_clean,
                courses=courses_dict,
                raw_remarks=enriched_remarks or "PASS"
            )
            records.append(student_rec)

        return records

    def _detect_semester(self, ws) -> int:
        """
        Detects whether the sheet is Semester 1 through 8 based on subject codes and headers.
        """
        # First check distinct subject code tokens across header rows 1 to 6
        header_tokens = []
        for r in range(1, min(7, ws.max_row + 1)):
            for c in range(1, min(35, ws.max_column + 1)):
                val = clean_text_string(ws.cell(r, c).value).lower()
                if val:
                    header_tokens.append(val)
        hdr_text = " ".join(header_tokens)

        # Subject code detection (highest confidence)
        if any(k in hdr_text for k in ["inte - 415", "inte 415", "competency assessment", "competency", "intensive clinical practicum"]):
            return 8
        if any(k in hdr_text for k in ["midw", "obgn", "nrst", "obstetrical", "nursing research"]):
            return 7
        if any(k in hdr_text for k in ["comh(ii)", "comh (ii)", "comh-ii", "community health nursing ii", "community health nursing-ii"]):
            return 7
        if any(k in hdr_text for k in ["nmle", "n-chn", "n-mhn", "child health", "mental health"]):
            return 6
        if any(k in hdr_text for k in ["comh", "educ", "forn", "forensic", "educational technology", "community health"]):
            return 5
        if any(k in hdr_text for k in ["phar", "path", "ahn (ii)", "prof 230", "pharmacology", "genetics"]):
            return 4
        if any(k in hdr_text for k in ["micr", "ahn (i)", "microbiology", "infection control"]):
            return 3
        if any(k in hdr_text for k in ["bioc", "nutr", "biochemistry", "n-nf", "hnit"]):
            return 2
        if any(k in hdr_text for k in ["anat", "phys", "soci", "psyc", "engl", "communicative english"]):
            return 1

        # Title & sheet name fallback
        tokens: List[str] = [clean_text_string(ws.title).lower(), hdr_text]
        full_text = " ".join(tokens)

        if any(k in full_text for k in ["eighth semester", "8th semester", "8th sem", "sem 8", "sem-8", "semester 8", "semester viii"]):
            return 8
        if any(k in full_text for k in ["seventh semester", "7th semester", "7th sem", "sem 7", "sem-7", "semester 7", "semester vii"]):
            return 7
        if any(k in full_text for k in ["sixth semester", "6th semester", "6th sem", "sem 6", "sem-6", "semester 6", "semester vi"]):
            return 6
        if any(k in full_text for k in ["fifth semester", "5th semester", "5th sem", "sem 5", "sem-5", "semester 5", "semester v"]):
            return 5
        if any(k in full_text for k in ["fourth semester", "4th semester", "4th sem", "sem 4", "sem-4", "semester 4", "semester iv"]):
            return 4
        if any(k in full_text for k in ["third semester", "3rd semester", "3rd sem", "sem 3", "sem-3", "semester 3", "semester iii"]):
            return 3
        if any(k in full_text for k in ["second semester", "2nd semester", "2nd sem", "sem 2", "sem-2", "semester 2", "semester ii"]):
            return 2
        if any(k in full_text for k in ["first semester", "1st semester", "1st sem", "sem 1", "sem-1", "semester 1", "semester i"]):
            return 1

        return 1

    def _detect_anchors(self, ws, semester: int) -> Dict[str, Any]:
        """
        Scans rows 1 to 10 for demographic and course anchors.
        """
        anchor_info = {
            "header_rows": [],
            "data_start_row": 4,
            "cols": {}
        }

        # 1. Detect data_start_row
        data_start_row = None
        for r in range(1, min(15, ws.max_row + 1)):
            c1_val = clean_text_string(ws.cell(r, 1).value)
            c2_val = clean_text_string(ws.cell(r, 2).value).lower()
            c5_val = clean_demographic_id(ws.cell(r, 5).value)

            has_sno = c1_val.isdigit() and int(c1_val) >= 1
            has_roll = c5_val.startswith("202") or (c5_val.isdigit() and len(c5_val) >= 5)

            if (has_sno or has_roll) and c2_val:
                if not any(k in c2_val for k in ["name", "roll", "course", "subject", "applied", "int", "ex"]):
                    data_start_row = r
                    break

        if not data_start_row:
            data_start_row = 4

        anchor_info["data_start_row"] = data_start_row
        sub_row = data_start_row - 1
        course_row = data_start_row - 2 if data_start_row >= 3 else sub_row
        anchor_info["header_rows"] = [course_row, sub_row]

        # 2. Map demographic columns
        cols: Dict[str, Any] = {}
        for r in [course_row, sub_row]:
            for c in range(1, ws.max_column + 1):
                val = clean_text_string(ws.cell(r, c).value).lower()
                if ("s.no" in val or "sl.no" in val or "sr.no" in val) and "sno" not in cols:
                    cols["sno"] = c
                elif ("student name" in val or "name" in val) and "father" not in val and "college" not in val and "student_name" not in cols:
                    cols["student_name"] = c
                elif ("father" in val or "s/o" in val or "d/o" in val) and "father_name" not in cols:
                    cols["father_name"] = c
                elif "enroll" in val and "enroll_no" not in cols:
                    cols["enroll_no"] = c
                elif "roll" in val and "roll_no" not in cols:
                    cols["roll_no"] = c
                elif ("result" in val or "remark" in val) and "remarks" not in cols:
                    cols["remarks"] = c

        # Fallbacks for standard demographic positions
        if "student_name" not in cols:
            cols["student_name"] = 2
        if "father_name" not in cols:
            cols["father_name"] = 3
        if "enroll_no" not in cols:
            cols["enroll_no"] = 4
        if "roll_no" not in cols:
            cols["roll_no"] = 5
        if "sno" not in cols:
            cols["sno"] = 1

        # 3. Map Course Columns based on semester
        if semester == 8:
            course_cols = self._map_sem8_course_columns(ws, course_row, sub_row)
        elif semester == 7:
            course_cols = self._map_sem7_course_columns(ws, course_row, sub_row)
        elif semester == 6:
            course_cols = self._map_sem6_course_columns(ws, course_row, sub_row)
        elif semester == 5:
            course_cols = self._map_sem5_course_columns(ws, course_row, sub_row)
        elif semester == 4:
            course_cols = self._map_sem4_course_columns(ws, course_row, sub_row)
        elif semester == 3:
            course_cols = self._map_sem3_course_columns(ws, course_row, sub_row)
        elif semester == 2:
            course_cols = self._map_sem2_course_columns(ws, course_row, sub_row)
        else:
            course_cols = self._map_sem1_course_columns(ws, course_row, sub_row)

        cols.update(course_cols)
        anchor_info["cols"] = cols
        return anchor_info

    def _map_sem1_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 1 courses (ANAT_PHYS, SOCI_PSYC, ENGL)."""
        col_map: Dict[str, Any] = {
            "ANAT_PHYS": {},
            "SOCI_PSYC": {},
            "ENGL": {}
        }
        current_course = None

        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()

            if any(k in p_val for k in ["applied anatomy", "anat 105", "anat"]):
                current_course = "ANAT_PHYS"
            elif any(k in p_val for k in ["applied sociology", "soci 115", "soci"]):
                current_course = "SOCI_PSYC"
            elif any(k in p_val for k in ["communicative english", "engl 101", "english", "engl"]):
                current_course = "ENGL"
            elif any(k in p_val for k in ["grand total", "result", "remarks"]):
                current_course = None

            if "anat" in s_val:
                current_course = "ANAT_PHYS"
            elif "soci" in s_val:
                current_course = "SOCI_PSYC"
            elif any(k in s_val for k in ["communicative", "english", "engl"]):
                current_course = "ENGL"

            if not current_course:
                continue

            if current_course == "ANAT_PHYS":
                if ("int" in s_val or "internal" in s_val) and "int" not in col_map["ANAT_PHYS"]:
                    col_map["ANAT_PHYS"]["int"] = c
                elif ("anat" in s_val or "37" in s_val or "part a" in s_val) and "ex_part_a" not in col_map["ANAT_PHYS"]:
                    col_map["ANAT_PHYS"]["ex_part_a"] = c
                elif ("phys" in s_val or "38" in s_val or "part b" in s_val) and "ex_part_b" not in col_map["ANAT_PHYS"]:
                    col_map["ANAT_PHYS"]["ex_part_b"] = c
                elif ("ex. total" in s_val or "75" in s_val) and "ex_total" not in col_map["ANAT_PHYS"]:
                    col_map["ANAT_PHYS"]["ex_total"] = c
                elif "grace" in s_val and "grace" not in col_map["ANAT_PHYS"]:
                    col_map["ANAT_PHYS"]["grace"] = c
                elif ("course total" in s_val or "100" in s_val) and "total" not in col_map["ANAT_PHYS"]:
                    col_map["ANAT_PHYS"]["total"] = c

            elif current_course == "SOCI_PSYC":
                if ("int" in s_val or "internal" in s_val) and "int" not in col_map["SOCI_PSYC"]:
                    col_map["SOCI_PSYC"]["int"] = c
                elif ("soci" in s_val or "37" in s_val or "part a" in s_val) and "ex_part_a" not in col_map["SOCI_PSYC"]:
                    col_map["SOCI_PSYC"]["ex_part_a"] = c
                elif ("psyc" in s_val or "38" in s_val or "part b" in s_val) and "ex_part_b" not in col_map["SOCI_PSYC"]:
                    col_map["SOCI_PSYC"]["ex_part_b"] = c
                elif ("ex. total" in s_val or "75" in s_val) and "ex_total" not in col_map["SOCI_PSYC"]:
                    col_map["SOCI_PSYC"]["ex_total"] = c
                elif "grace" in s_val and "grace" not in col_map["SOCI_PSYC"]:
                    col_map["SOCI_PSYC"]["grace"] = c
                elif ("course total" in s_val or "100" in s_val) and "total" not in col_map["SOCI_PSYC"]:
                    col_map["SOCI_PSYC"]["total"] = c

            elif current_course == "ENGL":
                if ("int" in s_val or "internal" in s_val) and "int" not in col_map["ENGL"]:
                    col_map["ENGL"]["int"] = c
                elif ("ex" in s_val or "25" in s_val) and "ex" not in col_map["ENGL"]:
                    col_map["ENGL"]["ex"] = c
                elif ("total" in s_val or "50" in s_val) and "total" not in col_map["ENGL"]:
                    col_map["ENGL"]["total"] = c

        return col_map

    def _map_sem2_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 2 courses (BIOC_NUTR, NNF_THEORY, NNF_PRACT, HNIT)."""
        col_map: Dict[str, Any] = {
            "BIOC_NUTR": {},
            "NNF_THEORY": {},
            "NNF_PRACT": {},
            "HNIT": {}
        }

        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            if "bioc" in combined or "nutr" in combined:
                if ("int" in s_val or "25" in s_val and "bioc" not in s_val) and "int" not in col_map["BIOC_NUTR"]:
                    col_map["BIOC_NUTR"]["int"] = c
                elif "bioc" in s_val and "bioc_ex" not in col_map["BIOC_NUTR"]:
                    col_map["BIOC_NUTR"]["bioc_ex"] = c
                elif "nutr" in s_val and "nutr_ex" not in col_map["BIOC_NUTR"]:
                    col_map["BIOC_NUTR"]["nutr_ex"] = c
                elif ("total (75)" in s_val or "75" in s_val or "ex. total" in s_val) and "ex_total" not in col_map["BIOC_NUTR"]:
                    col_map["BIOC_NUTR"]["ex_total"] = c
                elif ("total (100)" in s_val or "100" in s_val or "course total" in s_val) and "total" not in col_map["BIOC_NUTR"]:
                    col_map["BIOC_NUTR"]["total"] = c

            elif ("n-nf" in combined or "nursing foundation" in combined) and "pract" in combined:
                if "int" in s_val and "int" not in col_map["NNF_PRACT"]:
                    col_map["NNF_PRACT"]["int"] = c
                elif "ex" in s_val and "ex" not in col_map["NNF_PRACT"]:
                    col_map["NNF_PRACT"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["NNF_PRACT"]:
                    col_map["NNF_PRACT"]["total"] = c

            elif "n-nf" in combined or "nursing foundation" in combined:
                if "int" in s_val and "int" not in col_map["NNF_THEORY"]:
                    col_map["NNF_THEORY"]["int"] = c
                elif ("ex" in s_val or "75" in s_val) and "ex" not in col_map["NNF_THEORY"]:
                    col_map["NNF_THEORY"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["NNF_THEORY"]:
                    col_map["NNF_THEORY"]["total"] = c

            elif "hnit" in combined or "informatics" in combined or "technology" in combined:
                if "int" in s_val and "int" not in col_map["HNIT"]:
                    col_map["HNIT"]["int"] = c
                elif "ex" in s_val and "ex" not in col_map["HNIT"]:
                    col_map["HNIT"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["HNIT"]:
                    col_map["HNIT"]["total"] = c

        # Deterministic fallbacks matching official SGPGIMS Sem 2 tabular layout
        bn = col_map["BIOC_NUTR"]
        if "int" not in bn: bn["int"] = 6
        if "bioc_ex" not in bn: bn["bioc_ex"] = 7
        if "nutr_ex" not in bn: bn["nutr_ex"] = 8
        if "ex_total" not in bn: bn["ex_total"] = 9
        if "total" not in bn: bn["total"] = 10

        nt = col_map["NNF_THEORY"]
        if "int" not in nt: nt["int"] = 13
        if "ex" not in nt: nt["ex"] = 14
        if "total" not in nt: nt["total"] = 15

        np_ = col_map["NNF_PRACT"]
        if "int" not in np_: np_["int"] = 18
        if "ex" not in np_: np_["ex"] = 19
        if "total" not in np_: np_["total"] = 20

        hn = col_map["HNIT"]
        if "int" not in hn: hn["int"] = 23
        if "ex" not in hn: hn["ex"] = 24
        if "total" not in hn: hn["total"] = 25

        return col_map

    def _extract_sem1_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 1 courses with grace expression sanitization."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. ANAT_PHYS
        anat_cols = cols.get("ANAT_PHYS", {})
        int_c = anat_cols.get("int", 6)
        pa_c = anat_cols.get("ex_part_a", 7)
        pb_c = anat_cols.get("ex_part_b", 8)
        extot_c = anat_cols.get("ex_total", 9)
        grace_c = anat_cols.get("grace")
        tot_c = anat_cols.get("total", 10)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_pa, g_pa, tot_pa, ab_pa = parse_grace_expression(ws.cell(row_idx, pa_c).value)
        raw_pb, g_pb, tot_pb, ab_pb = parse_grace_expression(ws.cell(row_idx, pb_c).value)
        raw_extot, g_extot, tot_extot, ab_extot = parse_grace_expression(ws.cell(row_idx, extot_c).value)

        explicit_grace = 0.0
        if grace_c:
            _, eg, _, _ = parse_grace_expression(ws.cell(row_idx, grace_c).value)
            if eg > 0:
                explicit_grace = eg
            elif ws.cell(row_idx, grace_c).value is not None:
                try:
                    explicit_grace = float(ws.cell(row_idx, grace_c).value)
                except Exception:
                    pass

        anat_grace = g_int + g_pa + g_pb + g_extot + explicit_grace

        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_pa = format_numeric_token(tot_pa if not ab_pa else "Ab")
        v_pb = format_numeric_token(tot_pb if not ab_pb else "Ab")

        if tot_extot is not None:
            v_extot = tot_extot
        elif isinstance(v_pa, (int, float)) and isinstance(v_pb, (int, float)):
            v_extot = v_pa + v_pb
        else:
            v_extot = 0

        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
        if anat_grace > 0 and tot_final is not None:
            v_total = tot_final
        elif isinstance(v_int, (int, float)) and isinstance(v_extot, (int, float)):
            v_total = round(v_int + v_extot + anat_grace, 2)
        elif tot_final is not None:
            v_total = tot_final
        else:
            v_total = 0

        courses["ANAT_PHYS"] = {
            "int_marks": v_int,
            "ex_part_a": v_pa,
            "ex_part_b": v_pb,
            "ex_total": format_numeric_token(v_extot),
            "grace": format_numeric_token(anat_grace),
            "total": format_numeric_token(v_total)
        }

        # 2. SOCI_PSYC
        soci_cols = cols.get("SOCI_PSYC", {})
        int_c = soci_cols.get("int", 13)
        pa_c = soci_cols.get("ex_part_a", 14)
        pb_c = soci_cols.get("ex_part_b", 15)
        extot_c = soci_cols.get("ex_total", 16)
        grace_c = soci_cols.get("grace")
        tot_c = soci_cols.get("total", 17)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_pa, g_pa, tot_pa, ab_pa = parse_grace_expression(ws.cell(row_idx, pa_c).value)
        raw_pb, g_pb, tot_pb, ab_pb = parse_grace_expression(ws.cell(row_idx, pb_c).value)
        raw_extot, g_extot, tot_extot, ab_extot = parse_grace_expression(ws.cell(row_idx, extot_c).value)

        explicit_grace = 0.0
        if grace_c:
            val_gc = ws.cell(row_idx, grace_c).value
            if val_gc is not None:
                try:
                    explicit_grace = float(val_gc)
                except Exception:
                    _, eg, _, _ = parse_grace_expression(val_gc)
                    explicit_grace = eg

        soci_grace = g_int + g_pa + g_pb + g_extot + explicit_grace

        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_pa = format_numeric_token(tot_pa if not ab_pa else "Ab")
        v_pb = format_numeric_token(tot_pb if not ab_pb else "Ab")

        if isinstance(v_pa, (int, float)) and isinstance(v_pb, (int, float)):
            v_extot = v_pa + v_pb
        elif raw_extot is not None:
            v_extot = raw_extot
        elif tot_extot is not None:
            v_extot = round(tot_extot - soci_grace, 2) if soci_grace > 0 else tot_extot
        else:
            v_extot = 0

        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
        if isinstance(v_int, (int, float)) and isinstance(v_extot, (int, float)):
            v_total = round(v_int + v_extot + soci_grace, 2)
        elif tot_final is not None:
            v_total = tot_final
        else:
            v_total = 0

        courses["SOCI_PSYC"] = {
            "int_marks": v_int,
            "ex_part_a": v_pa,
            "ex_part_b": v_pb,
            "ex_total": format_numeric_token(v_extot),
            "grace": format_numeric_token(soci_grace),
            "total": format_numeric_token(v_total)
        }

        # 3. ENGL
        engl_cols = cols.get("ENGL", {})
        int_c = engl_cols.get("int", 20)
        ex_c = engl_cols.get("ex", 21)
        tot_c = engl_cols.get("total", 22)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)

        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")

        if tot_final is not None:
            v_total = tot_final
        elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
            v_total = round(v_int + v_ex, 2)
        else:
            v_total = 0

        courses["ENGL"] = {
            "int_marks": v_int,
            "ex_marks": v_ex,
            "total": format_numeric_token(v_total)
        }

        # Check if grace was extracted to enrich remarks
        total_grace = anat_grace + soci_grace
        if total_grace > 0 and (not raw_remarks or "GRACE" not in raw_remarks.upper()):
            formatted_grace = int(total_grace) if round(total_grace, 2) == int(total_grace) else round(total_grace, 2)
            grace_courses = []
            if soci_grace > 0:
                grace_courses.append("APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY")
            if anat_grace > 0:
                grace_courses.append("APPLIED ANATOMY & APPLIED PHYSIOLOGY")
            course_str = " & ".join(grace_courses) if grace_courses else "EXAMINATION"
            raw_remarks = f"PASS WITH {formatted_grace} GRACE MARKS IN {course_str}"

        return courses, raw_remarks

    def _extract_sem2_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 2 courses with grace expression sanitization."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. BIOC_NUTR
        bn_cols = cols.get("BIOC_NUTR", {})
        int_c = bn_cols.get("int", 6)
        pa_c = bn_cols.get("bioc_ex", 7)
        pb_c = bn_cols.get("nutr_ex", 8)
        extot_c = bn_cols.get("ex_total", 9)
        tot_c = bn_cols.get("total", 10)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_pa, g_pa, tot_pa, ab_pa = parse_grace_expression(ws.cell(row_idx, pa_c).value)
        raw_pb, g_pb, tot_pb, ab_pb = parse_grace_expression(ws.cell(row_idx, pb_c).value)
        raw_extot, g_extot, tot_extot, ab_extot = parse_grace_expression(ws.cell(row_idx, extot_c).value)
        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)

        bioc_grace = g_int + g_pa + g_pb + g_extot + g_tot

        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_pa = format_numeric_token(tot_pa if not ab_pa else "Ab")
        v_pb = format_numeric_token(tot_pb if not ab_pb else "Ab")

        if isinstance(v_pa, (int, float)) and isinstance(v_pb, (int, float)):
            v_extot = v_pa + v_pb
        elif raw_extot is not None:
            v_extot = raw_extot
        elif tot_extot is not None:
            v_extot = round(tot_extot - bioc_grace, 2) if bioc_grace > 0 else tot_extot
        else:
            v_extot = 0

        if tot_final is not None:
            v_total = tot_final
        elif isinstance(v_int, (int, float)) and isinstance(v_extot, (int, float)):
            v_total = round(v_int + v_extot, 2)
        else:
            v_total = 0

        courses["BIOC_NUTR"] = {
            "int_marks": v_int,
            "ex_part_a": v_pa,
            "ex_part_b": v_pb,
            "ex_total": format_numeric_token(v_extot),
            "grace": format_numeric_token(bioc_grace),
            "total": format_numeric_token(v_total),
        }

        # 2. NNF_THEORY
        nnf_t_cols = cols.get("NNF_THEORY", {})
        int_c = nnf_t_cols.get("int", 13)
        ex_c = nnf_t_cols.get("ex", 14)
        tot_c = nnf_t_cols.get("total", 15)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)

        nnf_t_grace = g_int + g_ex + g_tot
        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")

        if tot_final is not None:
            v_total = tot_final
        elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
            v_total = round(v_int + v_ex, 2)
        else:
            v_total = 0

        courses["NNF_THEORY"] = {
            "int_marks": v_int,
            "ex_marks": v_ex,
            "grace": format_numeric_token(nnf_t_grace),
            "total": format_numeric_token(v_total),
        }

        # 3. NNF_PRACT
        nnf_p_cols = cols.get("NNF_PRACT", {})
        int_c = nnf_p_cols.get("int", 18)
        ex_c = nnf_p_cols.get("ex", 19)
        tot_c = nnf_p_cols.get("total", 20)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)

        nnf_p_grace = g_int + g_ex + g_tot
        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")

        if tot_final is not None:
            v_total = tot_final
        elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
            v_total = round(v_int + v_ex, 2)
        else:
            v_total = 0

        courses["NNF_PRACT"] = {
            "int_marks": v_int,
            "ex_marks": v_ex,
            "grace": format_numeric_token(nnf_p_grace),
            "total": format_numeric_token(v_total),
        }

        # 4. HNIT
        hnit_cols = cols.get("HNIT", {})
        int_c = hnit_cols.get("int", 23)
        ex_c = hnit_cols.get("ex", 24)
        tot_c = hnit_cols.get("total", 25)

        raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
        raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
        raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)

        hnit_grace = g_int + g_ex + g_tot
        v_int = format_numeric_token(tot_int if not ab_int else "Ab")
        v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")

        if tot_final is not None:
            v_total = tot_final
        elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
            v_total = round(v_int + v_ex, 2)
        else:
            v_total = 0

        courses["HNIT"] = {
            "int_marks": v_int,
            "ex_marks": v_ex,
            "grace": format_numeric_token(hnit_grace),
            "total": format_numeric_token(v_total),
        }

        # Grace enrichment
        total_grace = bioc_grace + nnf_t_grace + nnf_p_grace + hnit_grace
        if total_grace > 0 and (not raw_remarks or "GRACE" not in raw_remarks.upper()):
            formatted_g = int(total_grace) if round(total_grace, 2) == int(total_grace) else round(total_grace, 2)
            grace_subs = []
            if bioc_grace > 0:
                grace_subs.append("APPLIED BIOCHEMISTRY & APPLIED NUTRITION & DIETETICS")
            if nnf_t_grace > 0:
                grace_subs.append("NURSING FOUNDATION THEORY")
            if nnf_p_grace > 0:
                grace_subs.append("NURSING FOUNDATION PRACTICAL")
            if hnit_grace > 0:
                grace_subs.append("HEALTH/ NURSING INFORMATICS & TECHNOLOGY")
            sub_name = " & ".join(grace_subs) if grace_subs else "EXAMINATION"
            raw_remarks = f"PASS WITH {formatted_g} GRACE MARKS IN {sub_name}"

        return courses, raw_remarks

    def _map_sem3_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 3 courses (MICR, AHN_I_THEORY, AHN_I_PRACT)."""
        col_map: Dict[str, Any] = {
            "MICR": {},
            "AHN_I_THEORY": {},
            "AHN_I_PRACT": {}
        }
        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            if "micr" in combined or "micro" in combined:
                if ("int" in s_val or "25" in s_val and "micr" not in s_val) and "int" not in col_map["MICR"]:
                    col_map["MICR"]["int"] = c
                elif ("micr" in s_val or "37" in s_val) and "ex_part_a" not in col_map["MICR"]:
                    col_map["MICR"]["ex_part_a"] = c
                elif ("infc" in s_val or "38" in s_val) and "ex_part_b" not in col_map["MICR"]:
                    col_map["MICR"]["ex_part_b"] = c
                elif ("75" in s_val or "ex. total" in s_val) and "ex_total" not in col_map["MICR"]:
                    col_map["MICR"]["ex_total"] = c
                elif ("100" in s_val or "total" in s_val) and "total" not in col_map["MICR"]:
                    col_map["MICR"]["total"] = c
            elif "ahn" in combined or "adult" in combined:
                if "pract" in combined:
                    if "int" in s_val and "int" not in col_map["AHN_I_PRACT"]:
                        col_map["AHN_I_PRACT"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["AHN_I_PRACT"]:
                        col_map["AHN_I_PRACT"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["AHN_I_PRACT"]:
                        col_map["AHN_I_PRACT"]["total"] = c
                else:
                    if "int" in s_val and "int" not in col_map["AHN_I_THEORY"]:
                        col_map["AHN_I_THEORY"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["AHN_I_THEORY"]:
                        col_map["AHN_I_THEORY"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["AHN_I_THEORY"]:
                        col_map["AHN_I_THEORY"]["total"] = c

        m = col_map["MICR"]
        if "int" not in m: m["int"] = 6
        if "ex_part_a" not in m: m["ex_part_a"] = 7
        if "ex_part_b" not in m: m["ex_part_b"] = 8
        if "ex_total" not in m: m["ex_total"] = 9
        if "total" not in m: m["total"] = 10

        at = col_map["AHN_I_THEORY"]
        if "int" not in at: at["int"] = 13
        if "ex" not in at: at["ex"] = 14
        if "total" not in at: at["total"] = 15

        ap = col_map["AHN_I_PRACT"]
        if "int" not in ap: ap["int"] = 18
        if "ex" not in ap: ap["ex"] = 19
        if "total" not in ap: ap["total"] = 20

        return col_map

    def _extract_sem3_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 3 courses."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. MICR
        m_cols = cols.get("MICR", {})
        int_c = m_cols.get("int", 6)
        pa_c = m_cols.get("ex_part_a", 7)
        pb_c = m_cols.get("ex_part_b", 8)
        extot_c = m_cols.get("ex_total", 9)
        tot_c = m_cols.get("total", 10)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, pa_c, pb_c, extot_c, tot_c]):
            courses["MICR"] = {
                "int_marks": "Ex.",
                "ex_part_a": "Ex.",
                "ex_part_b": "Ex.",
                "ex_total": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_pa, g_pa, tot_pa, ab_pa = parse_grace_expression(ws.cell(row_idx, pa_c).value)
            raw_pb, g_pb, tot_pb, ab_pb = parse_grace_expression(ws.cell(row_idx, pb_c).value)
            raw_extot, g_extot, tot_extot, ab_extot = parse_grace_expression(ws.cell(row_idx, extot_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            m_grace = g_int + g_pa + g_pb + g_extot + g_tot

            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_pa = format_numeric_token(tot_pa if not ab_pa else "Ab")
            v_pb = format_numeric_token(tot_pb if not ab_pb else "Ab")
            if tot_extot is not None:
                v_extot = tot_extot
            elif isinstance(v_pa, (int, float)) and isinstance(v_pb, (int, float)):
                v_extot = v_pa + v_pb
            else:
                v_extot = 0
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_extot, (int, float)):
                v_total = round(v_int + v_extot, 2)
            else:
                v_total = 0

            courses["MICR"] = {
                "int_marks": v_int,
                "ex_part_a": v_pa,
                "ex_part_b": v_pb,
                "ex_total": format_numeric_token(v_extot),
                "grace": format_numeric_token(m_grace),
                "total": format_numeric_token(v_total),
            }

        # 2. AHN_I_THEORY
        at_cols = cols.get("AHN_I_THEORY", {})
        int_c = at_cols.get("int", 13)
        ex_c = at_cols.get("ex", 14)
        tot_c = at_cols.get("total", 15)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["AHN_I_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            at_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
                v_total = round(v_int + v_ex, 2)
            else:
                v_total = 0

            courses["AHN_I_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(at_grace),
                "total": format_numeric_token(v_total),
            }

        # 3. AHN_I_PRACT
        ap_cols = cols.get("AHN_I_PRACT", {})
        int_c = ap_cols.get("int", 18)
        ex_c = ap_cols.get("ex", 19)
        tot_c = ap_cols.get("total", 20)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["AHN_I_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ap_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
                v_total = round(v_int + v_ex, 2)
            else:
                v_total = 0

            courses["AHN_I_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ap_grace),
                "total": format_numeric_token(v_total),
            }

        return courses, raw_remarks

    def _map_sem4_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 4 courses (PHAR_PATH, AHN_II_THEORY, AHN_II_PRACT, PROF)."""
        col_map: Dict[str, Any] = {
            "PHAR_PATH": {},
            "AHN_II_THEORY": {},
            "AHN_II_PRACT": {},
            "PROF": {}
        }
        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            if "phar" in combined or "path" in combined:
                if ("int" in s_val or "25" in s_val and "phar" not in s_val) and "int" not in col_map["PHAR_PATH"]:
                    col_map["PHAR_PATH"]["int"] = c
                elif ("phar" in s_val or "38" in s_val) and "ex_part_a" not in col_map["PHAR_PATH"]:
                    col_map["PHAR_PATH"]["ex_part_a"] = c
                elif ("path" in s_val or "25" in s_val and "path" in s_val) and "ex_part_b" not in col_map["PHAR_PATH"]:
                    col_map["PHAR_PATH"]["ex_part_b"] = c
                elif ("gen" in s_val or "12" in s_val) and "ex_part_c" not in col_map["PHAR_PATH"]:
                    col_map["PHAR_PATH"]["ex_part_c"] = c
                elif ("75" in s_val or "ex. total" in s_val) and "ex_total" not in col_map["PHAR_PATH"]:
                    col_map["PHAR_PATH"]["ex_total"] = c
                elif ("100" in s_val or "total" in s_val) and "total" not in col_map["PHAR_PATH"]:
                    col_map["PHAR_PATH"]["total"] = c
            elif "ahn" in combined or "adult" in combined:
                if "pract" in combined:
                    if "int" in s_val and "int" not in col_map["AHN_II_PRACT"]:
                        col_map["AHN_II_PRACT"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["AHN_II_PRACT"]:
                        col_map["AHN_II_PRACT"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["AHN_II_PRACT"]:
                        col_map["AHN_II_PRACT"]["total"] = c
                else:
                    if "int" in s_val and "int" not in col_map["AHN_II_THEORY"]:
                        col_map["AHN_II_THEORY"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["AHN_II_THEORY"]:
                        col_map["AHN_II_THEORY"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["AHN_II_THEORY"]:
                        col_map["AHN_II_THEORY"]["total"] = c
            elif "prof" in combined or "ethics" in combined or "values" in combined:
                if "int" in s_val and "int" not in col_map["PROF"]:
                    col_map["PROF"]["int"] = c
                elif "ex" in s_val and "ex" not in col_map["PROF"]:
                    col_map["PROF"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["PROF"]:
                    col_map["PROF"]["total"] = c

        pp = col_map["PHAR_PATH"]
        if "int" not in pp: pp["int"] = 6
        if "ex_part_a" not in pp: pp["ex_part_a"] = 7
        if "ex_part_b" not in pp: pp["ex_part_b"] = 8
        if "ex_part_c" not in pp: pp["ex_part_c"] = 9
        if "ex_total" not in pp: pp["ex_total"] = 10
        if "total" not in pp: pp["total"] = 11

        at = col_map["AHN_II_THEORY"]
        if "int" not in at: at["int"] = 14
        if "ex" not in at: at["ex"] = 15
        if "total" not in at: at["total"] = 16

        ap = col_map["AHN_II_PRACT"]
        if "int" not in ap: ap["int"] = 19
        if "ex" not in ap: ap["ex"] = 20
        if "total" not in ap: ap["total"] = 21

        pr = col_map["PROF"]
        if "int" not in pr: pr["int"] = 24
        if "ex" not in pr: pr["ex"] = 25
        if "total" not in pr: pr["total"] = 26

        return col_map

    def _extract_sem4_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 4 courses."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. PHAR_PATH
        pp_cols = cols.get("PHAR_PATH", {})
        int_c = pp_cols.get("int", 6)
        pa_c = pp_cols.get("ex_part_a", 7)
        pb_c = pp_cols.get("ex_part_b", 8)
        pc_c = pp_cols.get("ex_part_c", 9)
        extot_c = pp_cols.get("ex_total", 10)
        tot_c = pp_cols.get("total", 11)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, pa_c, pb_c, pc_c, extot_c, tot_c]):
            courses["PHAR_PATH"] = {
                "int_marks": "Ex.",
                "ex_part_a": "Ex.",
                "ex_part_b": "Ex.",
                "ex_part_c": "Ex.",
                "ex_total": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_pa, g_pa, tot_pa, ab_pa = parse_grace_expression(ws.cell(row_idx, pa_c).value)
            raw_pb, g_pb, tot_pb, ab_pb = parse_grace_expression(ws.cell(row_idx, pb_c).value)
            raw_pc, g_pc, tot_pc, ab_pc = parse_grace_expression(ws.cell(row_idx, pc_c).value)
            raw_extot, g_extot, tot_extot, ab_extot = parse_grace_expression(ws.cell(row_idx, extot_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            pp_grace = g_int + g_pa + g_pb + g_pc + g_extot + g_tot

            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_pa = format_numeric_token(tot_pa if not ab_pa else "Ab")
            v_pb = format_numeric_token(tot_pb if not ab_pb else "Ab")
            v_pc = format_numeric_token(tot_pc if not ab_pc else "Ab")
            if raw_extot is not None and (g_extot > 0 or pp_grace > 0):
                v_extot = raw_extot
            elif tot_extot is not None:
                v_extot = tot_extot
            elif isinstance(v_pa, (int, float)) and isinstance(v_pb, (int, float)) and isinstance(v_pc, (int, float)):
                v_extot = v_pa + v_pb + v_pc
            else:
                v_extot = 0
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_extot, (int, float)):
                v_total = round(v_int + v_extot, 2)
            else:
                v_total = 0

            courses["PHAR_PATH"] = {
                "int_marks": v_int,
                "ex_part_a": v_pa,
                "ex_part_b": v_pb,
                "ex_part_c": v_pc,
                "ex_total": format_numeric_token(v_extot),
                "grace": format_numeric_token(pp_grace),
                "total": format_numeric_token(v_total),
            }

        # 2. AHN_II_THEORY
        at_cols = cols.get("AHN_II_THEORY", {})
        int_c = at_cols.get("int", 14)
        ex_c = at_cols.get("ex", 15)
        tot_c = at_cols.get("total", 16)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["AHN_II_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            at_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            if raw_ex is not None and g_ex > 0:
                v_ex = format_numeric_token(raw_ex)
            else:
                v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
                v_total = round(v_int + v_ex, 2)
            else:
                v_total = 0

            courses["AHN_II_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(at_grace),
                "total": format_numeric_token(v_total),
            }

        # 3. AHN_II_PRACT
        ap_cols = cols.get("AHN_II_PRACT", {})
        int_c = ap_cols.get("int", 19)
        ex_c = ap_cols.get("ex", 20)
        tot_c = ap_cols.get("total", 21)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["AHN_II_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ap_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            if raw_ex is not None and g_ex > 0:
                v_ex = format_numeric_token(raw_ex)
            else:
                v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
                v_total = round(v_int + v_ex, 2)
            else:
                v_total = 0

            courses["AHN_II_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ap_grace),
                "total": format_numeric_token(v_total),
            }

        # 4. PROF
        pr_cols = cols.get("PROF", {})
        int_c = pr_cols.get("int", 24)
        ex_c = pr_cols.get("ex", 25)
        tot_c = pr_cols.get("total", 26)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["PROF"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            pr_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            if raw_ex is not None and g_ex > 0:
                v_ex = format_numeric_token(raw_ex)
            else:
                v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            if tot_final is not None:
                v_total = tot_final
            elif isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)):
                v_total = round(v_int + v_ex, 2)
            else:
                v_total = 0

            courses["PROF"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(pr_grace),
                "total": format_numeric_token(v_total),
            }

        return courses, raw_remarks

    def _map_sem5_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 5 courses (COMH_I_THEORY, EDUC, FORN, COMH_I_PRACT)."""
        col_map: Dict[str, Any] = {
            "COMH_I_THEORY": {},
            "EDUC": {},
            "FORN": {},
            "COMH_I_PRACT": {}
        }
        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            if "comh" in combined or "community" in combined:
                if "pract" in combined:
                    if "int" in s_val and "int" not in col_map["COMH_I_PRACT"]:
                        col_map["COMH_I_PRACT"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["COMH_I_PRACT"]:
                        col_map["COMH_I_PRACT"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["COMH_I_PRACT"]:
                        col_map["COMH_I_PRACT"]["total"] = c
                else:
                    if "int" in s_val and "int" not in col_map["COMH_I_THEORY"]:
                        col_map["COMH_I_THEORY"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["COMH_I_THEORY"]:
                        col_map["COMH_I_THEORY"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["COMH_I_THEORY"]:
                        col_map["COMH_I_THEORY"]["total"] = c
            elif "educ" in combined or "education" in combined:
                if "int" in s_val and "int" not in col_map["EDUC"]:
                    col_map["EDUC"]["int"] = c
                elif "ex" in s_val and "ex" not in col_map["EDUC"]:
                    col_map["EDUC"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["EDUC"]:
                    col_map["EDUC"]["total"] = c
            elif "forn" in combined or "forensic" in combined:
                if "int" in s_val and "int" not in col_map["FORN"]:
                    col_map["FORN"]["int"] = c
                elif "ex" in s_val and "ex" not in col_map["FORN"]:
                    col_map["FORN"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["FORN"]:
                    col_map["FORN"]["total"] = c

        ct = col_map["COMH_I_THEORY"]
        if "int" not in ct: ct["int"] = 6
        if "ex" not in ct: ct["ex"] = 7
        if "total" not in ct: ct["total"] = 8

        ed = col_map["EDUC"]
        if "int" not in ed: ed["int"] = 11
        if "ex" not in ed: ed["ex"] = 12
        if "total" not in ed: ed["total"] = 13

        fn = col_map["FORN"]
        if "int" not in fn: fn["int"] = 16
        if "ex" not in fn: fn["ex"] = 17
        if "total" not in fn: fn["total"] = 18

        cp = col_map["COMH_I_PRACT"]
        if "int" not in cp: cp["int"] = 21
        if "ex" not in cp: cp["ex"] = 22
        if "total" not in cp: cp["total"] = 23

        return col_map

    def _extract_sem5_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 5 courses."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. COMH_I_THEORY
        ct_cols = cols.get("COMH_I_THEORY", {})
        int_c = ct_cols.get("int", 6)
        ex_c = ct_cols.get("ex", 7)
        tot_c = ct_cols.get("total", 8)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["COMH_I_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ct_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["COMH_I_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ct_grace),
                "total": format_numeric_token(v_total),
            }

        # 2. EDUC
        ed_cols = cols.get("EDUC", {})
        int_c = ed_cols.get("int", 11)
        ex_c = ed_cols.get("ex", 12)
        tot_c = ed_cols.get("total", 13)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["EDUC"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ed_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["EDUC"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ed_grace),
                "total": format_numeric_token(v_total),
            }

        # 3. FORN
        fn_cols = cols.get("FORN", {})
        int_c = fn_cols.get("int", 16)
        ex_c = fn_cols.get("ex", 17)
        tot_c = fn_cols.get("total", 18)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["FORN"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            fn_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["FORN"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(fn_grace),
                "total": format_numeric_token(v_total),
            }

        # 4. COMH_I_PRACT
        cp_cols = cols.get("COMH_I_PRACT", {})
        int_c = cp_cols.get("int", 21)
        ex_c = cp_cols.get("ex", 22)
        tot_c = cp_cols.get("total", 23)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["COMH_I_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            cp_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["COMH_I_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(cp_grace),
                "total": format_numeric_token(v_total),
            }

        return courses, raw_remarks

    def _map_sem6_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 6 courses (CHN_THEORY, MHN_THEORY, NMLE, CHN_PRACT, MHN_PRACT)."""
        col_map: Dict[str, Any] = {
            "CHN_THEORY": {},
            "MHN_THEORY": {},
            "NMLE": {},
            "CHN_PRACT": {},
            "MHN_PRACT": {}
        }
        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            if "chn" in combined or "child health" in combined:
                if "pract" in combined:
                    if "int" in s_val and "int" not in col_map["CHN_PRACT"]:
                        col_map["CHN_PRACT"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["CHN_PRACT"]:
                        col_map["CHN_PRACT"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["CHN_PRACT"]:
                        col_map["CHN_PRACT"]["total"] = c
                else:
                    if "int" in s_val and "int" not in col_map["CHN_THEORY"]:
                        col_map["CHN_THEORY"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["CHN_THEORY"]:
                        col_map["CHN_THEORY"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["CHN_THEORY"]:
                        col_map["CHN_THEORY"]["total"] = c
            elif "mhn" in combined or "mental health" in combined:
                if "pract" in combined:
                    if "int" in s_val and "int" not in col_map["MHN_PRACT"]:
                        col_map["MHN_PRACT"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["MHN_PRACT"]:
                        col_map["MHN_PRACT"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["MHN_PRACT"]:
                        col_map["MHN_PRACT"]["total"] = c
                else:
                    if "int" in s_val and "int" not in col_map["MHN_THEORY"]:
                        col_map["MHN_THEORY"]["int"] = c
                    elif "ex" in s_val and "ex" not in col_map["MHN_THEORY"]:
                        col_map["MHN_THEORY"]["ex"] = c
                    elif "total" in s_val and "total" not in col_map["MHN_THEORY"]:
                        col_map["MHN_THEORY"]["total"] = c
            elif "nmle" in combined or "leadership" in combined or "management" in combined:
                if "int" in s_val and "int" not in col_map["NMLE"]:
                    col_map["NMLE"]["int"] = c
                elif "ex" in s_val and "ex" not in col_map["NMLE"]:
                    col_map["NMLE"]["ex"] = c
                elif "total" in s_val and "total" not in col_map["NMLE"]:
                    col_map["NMLE"]["total"] = c

        ct = col_map["CHN_THEORY"]
        if "int" not in ct: ct["int"] = 6
        if "ex" not in ct: ct["ex"] = 7
        if "total" not in ct: ct["total"] = 8

        mt = col_map["MHN_THEORY"]
        if "int" not in mt: mt["int"] = 11
        if "ex" not in mt: mt["ex"] = 12
        if "total" not in mt: mt["total"] = 13

        nl = col_map["NMLE"]
        if "int" not in nl: nl["int"] = 16
        if "ex" not in nl: nl["ex"] = 17
        if "total" not in nl: nl["total"] = 18

        cp = col_map["CHN_PRACT"]
        if "int" not in cp: cp["int"] = 21
        if "ex" not in cp: cp["ex"] = 22
        if "total" not in cp: cp["total"] = 23

        mp = col_map["MHN_PRACT"]
        if "int" not in mp: mp["int"] = 26
        if "ex" not in mp: mp["ex"] = 27
        if "total" not in mp: mp["total"] = 28

        return col_map

    def _extract_sem6_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 6 courses."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. CHN_THEORY
        ct_cols = cols.get("CHN_THEORY", {})
        int_c = ct_cols.get("int", 6)
        ex_c = ct_cols.get("ex", 7)
        tot_c = ct_cols.get("total", 8)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["CHN_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ct_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["CHN_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ct_grace),
                "total": format_numeric_token(v_total),
            }

        # 2. MHN_THEORY
        mt_cols = cols.get("MHN_THEORY", {})
        int_c = mt_cols.get("int", 11)
        ex_c = mt_cols.get("ex", 12)
        tot_c = mt_cols.get("total", 13)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["MHN_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            mt_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["MHN_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(mt_grace),
                "total": format_numeric_token(v_total),
            }

        # 3. NMLE
        nl_cols = cols.get("NMLE", {})
        int_c = nl_cols.get("int", 16)
        ex_c = nl_cols.get("ex", 17)
        tot_c = nl_cols.get("total", 18)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["NMLE"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            nl_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["NMLE"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(nl_grace),
                "total": format_numeric_token(v_total),
            }

        # 4. CHN_PRACT
        cp_cols = cols.get("CHN_PRACT", {})
        int_c = cp_cols.get("int", 21)
        ex_c = cp_cols.get("ex", 22)
        tot_c = cp_cols.get("total", 23)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["CHN_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            cp_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["CHN_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(cp_grace),
                "total": format_numeric_token(v_total),
            }

        # 5. MHN_PRACT
        mp_cols = cols.get("MHN_PRACT", {})
        int_c = mp_cols.get("int", 26)
        ex_c = mp_cols.get("ex", 27)
        tot_c = mp_cols.get("total", 28)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["MHN_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            mp_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(tot_int if not ab_int else "Ab")
            v_ex = format_numeric_token(tot_ex if not ab_ex else "Ab")
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["MHN_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(mp_grace),
                "total": format_numeric_token(v_total),
            }

        return courses, raw_remarks

    def _map_sem7_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 7 courses (COMH_II_THEORY, NRST, OBGN_THEORY, OBGN_PRACT, COMH_II_PRACT)."""
        col_map: Dict[str, Any] = {
            "COMH_II_THEORY": {},
            "NRST": {},
            "OBGN_THEORY": {},
            "OBGN_PRACT": {},
            "COMH_II_PRACT": {}
        }
        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            is_int = bool(re.search(r'\bint\b|\bint\.', s_val) or s_val.startswith("int"))
            is_ex = bool(re.search(r'\bex\b|\bex\.', s_val) or s_val.startswith("ex") or "mid ex" in s_val or "comh (i)" in s_val or "comh (ii)" in s_val)
            is_tot = bool("total" in s_val or "grand total" in s_val)

            if "comh" in combined or "community" in combined:
                if "pract" in combined:
                    if is_int and "int" not in col_map["COMH_II_PRACT"]: col_map["COMH_II_PRACT"]["int"] = c
                    elif is_ex and "ex" not in col_map["COMH_II_PRACT"]: col_map["COMH_II_PRACT"]["ex"] = c
                    elif is_tot and "total" not in col_map["COMH_II_PRACT"]: col_map["COMH_II_PRACT"]["total"] = c
                else:
                    if is_int and "int" not in col_map["COMH_II_THEORY"]: col_map["COMH_II_THEORY"]["int"] = c
                    elif is_ex and "ex" not in col_map["COMH_II_THEORY"]: col_map["COMH_II_THEORY"]["ex"] = c
                    elif is_tot and "total" not in col_map["COMH_II_THEORY"]: col_map["COMH_II_THEORY"]["total"] = c
            elif "nrst" in combined or "research" in combined or "statist" in combined:
                if is_int and "int" not in col_map["NRST"]: col_map["NRST"]["int"] = c
                elif ("nur" in s_val or "part a" in s_val) and "part_a" not in col_map["NRST"]: col_map["NRST"]["part_a"] = c
                elif ("stat" in s_val or "part b" in s_val) and "part_b" not in col_map["NRST"]: col_map["NRST"]["part_b"] = c
                elif is_ex and "ex" not in col_map["NRST"]: col_map["NRST"]["ex"] = c
                elif is_tot and "total" not in col_map["NRST"]: col_map["NRST"]["total"] = c
            elif "midw" in combined or "obgn" in combined or "obg" in combined or "obstetrical" in combined or "gynecology" in combined:
                if "pract" in combined:
                    if is_int and "int" not in col_map["OBGN_PRACT"]: col_map["OBGN_PRACT"]["int"] = c
                    elif is_ex and "ex" not in col_map["OBGN_PRACT"]: col_map["OBGN_PRACT"]["ex"] = c
                    elif is_tot and "total" not in col_map["OBGN_PRACT"]: col_map["OBGN_PRACT"]["total"] = c
                else:
                    if is_int and "int" not in col_map["OBGN_THEORY"]: col_map["OBGN_THEORY"]["int"] = c
                    elif is_ex and "ex" not in col_map["OBGN_THEORY"]: col_map["OBGN_THEORY"]["ex"] = c
                    elif is_tot and "total" not in col_map["OBGN_THEORY"]: col_map["OBGN_THEORY"]["total"] = c

        ct = col_map["COMH_II_THEORY"]
        if "int" not in ct: ct["int"] = 6
        if "ex" not in ct: ct["ex"] = 7
        if "total" not in ct: ct["total"] = 8

        nr = col_map["NRST"]
        if "int" not in nr: nr["int"] = 11
        if "part_a" not in nr: nr["part_a"] = 12
        if "part_b" not in nr: nr["part_b"] = 13
        if "ex" not in nr: nr["ex"] = 14
        if "total" not in nr: nr["total"] = 15

        ot = col_map["OBGN_THEORY"]
        if "int" not in ot: ot["int"] = 18
        if "ex" not in ot: ot["ex"] = 19
        if "total" not in ot: ot["total"] = 20

        op = col_map["OBGN_PRACT"]
        if "int" not in op: op["int"] = 23
        if "ex" not in op: op["ex"] = 24
        if "total" not in op: op["total"] = 25

        cp = col_map["COMH_II_PRACT"]
        if "int" not in cp: cp["int"] = 28
        if "ex" not in cp: cp["ex"] = 29
        if "total" not in cp: cp["total"] = 30

        return col_map

    def _extract_sem7_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 7 courses."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. COMH_II_THEORY
        ct_cols = cols.get("COMH_II_THEORY", {})
        int_c = ct_cols.get("int", 6)
        ex_c = ct_cols.get("ex", 7)
        tot_c = ct_cols.get("total", 8)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["COMH_II_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ct_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(raw_int if raw_int is not None else (tot_int if not ab_int else "Ab"))
            v_ex = format_numeric_token(raw_ex if raw_ex is not None else (tot_ex if not ab_ex else "Ab"))
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["COMH_II_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ct_grace),
                "total": format_numeric_token(v_total),
            }

        # 2. NRST
        nr_cols = cols.get("NRST", {})
        int_c = nr_cols.get("int", 11)
        pa_c = nr_cols.get("part_a", 12)
        pb_c = nr_cols.get("part_b", 13)
        ex_c = nr_cols.get("ex", 14)
        tot_c = nr_cols.get("total", 15)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["NRST"] = {
                "int_marks": "Ex.",
                "ex_part_a": "Ex.",
                "ex_part_b": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_pa, g_pa, tot_pa, ab_pa = parse_grace_expression(ws.cell(row_idx, pa_c).value)
            raw_pb, g_pb, tot_pb, ab_pb = parse_grace_expression(ws.cell(row_idx, pb_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)

            nr_grace = g_int + g_pa + g_pb + g_ex + g_tot
            v_int = format_numeric_token(raw_int if raw_int is not None else (tot_int if not ab_int else "Ab"))
            v_pa = format_numeric_token(raw_pa if raw_pa is not None else (tot_pa if not ab_pa else "Ab"))
            v_pb = format_numeric_token(raw_pb if raw_pb is not None else (tot_pb if not ab_pb else "Ab"))
            v_ex = format_numeric_token(raw_ex if raw_ex is not None else (tot_ex if not ab_ex else "Ab"))
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["NRST"] = {
                "int_marks": v_int,
                "ex_part_a": v_pa,
                "ex_part_b": v_pb,
                "ex_marks": v_ex,
                "grace": format_numeric_token(nr_grace),
                "total": format_numeric_token(v_total),
            }

        # 3. OBGN_THEORY
        ot_cols = cols.get("OBGN_THEORY", {})
        int_c = ot_cols.get("int", 18)
        ex_c = ot_cols.get("ex", 19)
        tot_c = ot_cols.get("total", 20)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["OBGN_THEORY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            ot_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(raw_int if raw_int is not None else (tot_int if not ab_int else "Ab"))
            v_ex = format_numeric_token(raw_ex if raw_ex is not None else (tot_ex if not ab_ex else "Ab"))
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["OBGN_THEORY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(ot_grace),
                "total": format_numeric_token(v_total),
            }

        # 4. OBGN_PRACT
        op_cols = cols.get("OBGN_PRACT", {})
        int_c = op_cols.get("int", 23)
        ex_c = op_cols.get("ex", 24)
        tot_c = op_cols.get("total", 25)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["OBGN_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            op_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(raw_int if raw_int is not None else (tot_int if not ab_int else "Ab"))
            v_ex = format_numeric_token(raw_ex if raw_ex is not None else (tot_ex if not ab_ex else "Ab"))
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["OBGN_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(op_grace),
                "total": format_numeric_token(v_total),
            }

        # 5. COMH_II_PRACT
        cp_cols = cols.get("COMH_II_PRACT", {})
        int_c = cp_cols.get("int", 28)
        ex_c = cp_cols.get("ex", 29)
        tot_c = cp_cols.get("total", 30)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["COMH_II_PRACT"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            cp_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(raw_int if raw_int is not None else (tot_int if not ab_int else "Ab"))
            v_ex = format_numeric_token(raw_ex if raw_ex is not None else (tot_ex if not ab_ex else "Ab"))
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["COMH_II_PRACT"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(cp_grace),
                "total": format_numeric_token(v_total),
            }

        return courses, raw_remarks

    def _map_sem8_course_columns(self, ws, course_row: int, sub_row: int) -> Dict[str, Any]:
        """Maps columns for Semester 8 courses (COMPETENCY, and optional ELECTIVE_3)."""
        col_map: Dict[str, Any] = {
            "COMPETENCY": {},
            "ELECTIVE_3": {}
        }
        for c in range(1, ws.max_column + 1):
            p_val = clean_text_string(ws.cell(course_row, c).value).lower()
            s_val = clean_text_string(ws.cell(sub_row, c).value).lower()
            combined = f"{p_val} {s_val}"

            is_int = bool(re.search(r'\bint\b|\bint\.', s_val) or s_val.startswith("int"))
            is_ex = bool(re.search(r'\bex\b|\bex\.', s_val) or "comp ass" in s_val or s_val.startswith("ex"))
            is_tot = bool("total" in s_val)

            if "inte" in combined or "competency" in combined or "internship" in combined:
                if is_int and "int" not in col_map["COMPETENCY"]: col_map["COMPETENCY"]["int"] = c
                elif is_ex and "ex" not in col_map["COMPETENCY"]: col_map["COMPETENCY"]["ex"] = c
                elif is_tot and "total" not in col_map["COMPETENCY"]: col_map["COMPETENCY"]["total"] = c
            elif "elective" in combined or "scientific writing" in combined:
                if is_int and "int" not in col_map["ELECTIVE_3"]: col_map["ELECTIVE_3"]["int"] = c
                elif is_ex and "ex" not in col_map["ELECTIVE_3"]: col_map["ELECTIVE_3"]["ex"] = c
                elif is_tot and "total" not in col_map["ELECTIVE_3"]: col_map["ELECTIVE_3"]["total"] = c

        comp = col_map["COMPETENCY"]
        if "int" not in comp: comp["int"] = 6
        if "ex" not in comp: comp["ex"] = 7
        if "total" not in comp: comp["total"] = 8

        return col_map

    def _extract_sem8_course_marks(
        self,
        ws,
        row_idx: int,
        anchors: Dict[str, Any],
        raw_remarks: Optional[str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Extracts marks for Semester 8 courses."""
        cols = anchors["cols"]
        courses: Dict[str, Any] = {}

        # 1. COMPETENCY (Max IA 100, EA 100, Total 200)
        c_cols = cols.get("COMPETENCY", {})
        int_c = c_cols.get("int", 6)
        ex_c = c_cols.get("ex", 7)
        tot_c = c_cols.get("total", 8)

        if any(is_exempt_token(ws.cell(row_idx, c).value) for c in [int_c, ex_c, tot_c]):
            courses["COMPETENCY"] = {
                "int_marks": "Ex.",
                "ex_marks": "Ex.",
                "grace": 0,
                "total": "Ex.",
                "is_exempted": True,
                "letter_grade": "Ex.",
                "is_pass": True
            }
        else:
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value)
            c_grace = g_int + g_ex + g_tot
            v_int = format_numeric_token(raw_int if raw_int is not None else (tot_int if not ab_int else "Ab"))
            v_ex = format_numeric_token(raw_ex if raw_ex is not None else (tot_ex if not ab_ex else "Ab"))
            v_total = tot_final if tot_final is not None else (round(v_int + v_ex, 2) if isinstance(v_int, (int, float)) and isinstance(v_ex, (int, float)) else 0)

            courses["COMPETENCY"] = {
                "int_marks": v_int,
                "ex_marks": v_ex,
                "grace": format_numeric_token(c_grace),
                "total": format_numeric_token(v_total),
            }

        # 2. ELECTIVE_3 (Optional)
        el_cols = cols.get("ELECTIVE_3", {})
        if el_cols and "total" in el_cols:
            int_c = el_cols.get("int", 0)
            ex_c = el_cols.get("ex", 0)
            tot_c = el_cols.get("total", 0)
            raw_int, g_int, tot_int, ab_int = parse_grace_expression(ws.cell(row_idx, int_c).value) if int_c else (0, 0, 0, False)
            raw_ex, g_ex, tot_ex, ab_ex = parse_grace_expression(ws.cell(row_idx, ex_c).value) if ex_c else (0, 0, 0, False)
            raw_tot, g_tot, tot_final, _ = parse_grace_expression(ws.cell(row_idx, tot_c).value) if tot_c else (0, 0, 0, False)
            courses["ELECTIVE_3"] = {
                "int_marks": format_numeric_token(tot_int if not ab_int else "Ab"),
                "ex_marks": format_numeric_token(tot_ex if not ab_ex else "Ab"),
                "grace": format_numeric_token(g_int + g_ex + g_tot),
                "total": format_numeric_token(tot_final or (tot_int + tot_ex)),
            }

        return courses, raw_remarks
