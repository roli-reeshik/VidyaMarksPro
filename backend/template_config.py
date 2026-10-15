"""
VidyaMarksheet Marksheet Template Configuration Model
Phase 4: Template styling, layout adjustments, typography, column labels and signatures.
Persists configuration to backend/template_config.json for persistent synchronization.
"""

import os
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "template_config.json")


class MarksheetTemplateConfig(BaseModel):
    # Header & Institutional Titles
    institution_name: str = Field(
        default="SGPGIMS, LUCKNOW, UTTAR PRADESH",
        description="Institutional header text"
    )
    college_name: str = Field(
        default="COLLEGE OF NURSING",
        description="College / faculty name"
    )
    college_code: str = Field(
        default="0103",
        description="Institutional college code"
    )
    exam_title: Optional[str] = Field(
        default=None,
        description="Primary examination title in bold single line (if None, auto-generated based on semester, year, and session)"
    )
    place: str = Field(default="LUCKNOW", description="Issue place / location")
    issue_date: str = Field(default="12-10-2026", description="Date of marksheet generation / issue")

    # Dimensions, Paper & Margins
    paper_size: str = Field(default="8.5in 14in", description="Paper size e.g. '8.5in 14in' (Legal) or '8.27in 11.69in' (A4)")
    top_margin: str = Field(default="2.5in", description="Letterhead top margin clearance (default 2.5in)")
    bottom_margin: str = Field(default="0.25in", description="Bottom margin")
    left_margin: str = Field(default="0.25in", description="Left margin")
    right_margin: str = Field(default="0.25in", description="Right margin")

    # Typography & Row Spacing
    row_padding: str = Field(default="standard", description="Table row density: 'compact', 'standard', or 'relaxed'")
    row_min_height: int = Field(default=40, description="Minimum row height in pixels (e.g. 38, 40, 46)")
    cell_padding: int = Field(default=4, description="Cell vertical padding in pixels (e.g. 3, 4, 6)")
    font_size_header: str = Field(default="11pt", description="Header line font size")
    font_size_demo: str = Field(default="11pt", description="Demographics font size")
    font_size_table: str = Field(default="10pt", description="Marks table text font size")
    font_size_signatures: str = Field(default="10.5pt", description="Signatures font size")

    # Column Widths (% of total table width)
    col_width_sno: float = Field(default=4.5, description="Sl.No column width percentage")
    col_width_code: float = Field(default=14.0, description="Course Code column width percentage")
    col_width_title: float = Field(default=16.0, description="Title of Course column width percentage (narrower for fit)")
    col_width_credits: float = Field(default=7.0, description="Course Credits column width percentage")

    # Text Directions & Orientations
    text_direction_code: str = Field(default="vertical", description="Text direction for Course Code: 'vertical' or 'horizontal'")
    text_direction_title: str = Field(default="horizontal", description="Text direction for Course Title: 'horizontal' or 'vertical'")

    # Column Labels
    col_label_sno: str = Field(default="Sl.No.", description="Serial number column header")
    col_label_course_code: str = Field(default="Course Code", description="Course code column header")
    col_label_course_title: str = Field(default="Title of Course", description="Course title column header")
    col_label_credits: str = Field(default="Course Credits", description="Course credits column header")
    col_label_internal: str = Field(default="Internal Assesment Marks", description="Internal assessment header")
    col_label_external: str = Field(default="End Semester University Exam Marks", description="External exam header")
    col_label_total: str = Field(default="Total Marks", description="Total marks header")
    col_label_grade: str = Field(default="Letter Grade", description="Letter grade header")
    col_label_grade_point: str = Field(default="Grade Point", description="Grade point header")
    col_label_credit_points: str = Field(default="Credit Points", description="Credit points header")

    # Column Visibility Toggles
    show_sno: bool = Field(default=True, description="Show serial number column")
    show_course_code: bool = Field(default=True, description="Show course code column")
    show_course_title: bool = Field(default=True, description="Show course title column")
    show_credits: bool = Field(default=True, description="Show credits column")
    show_internal: bool = Field(default=True, description="Show internal assessment columns")
    show_external: bool = Field(default=True, description="Show external exam columns")
    show_total: bool = Field(default=True, description="Show total marks columns")
    show_grade: bool = Field(default=True, description="Show letter grade column")
    show_grade_point: bool = Field(default=True, description="Show grade point column")
    show_credit_points: bool = Field(default=True, description="Show credit points column")

    # Signatory Positions & Names
    sig1_title: str = Field(default="Prepared By", description="Signatory 1 label")
    sig2_title: str = Field(default="Checked By", description="Signatory 2 label")
    sig3_title: str = Field(default="Sub-Dean (Nursing)", description="Signatory 3 label")
    sig4_title: str = Field(default="Executive Registrar", description="Signatory 4 label")
    show_sig4: bool = Field(default=False, description="Display 4th signature if enabled")

    # Signature Clearance & Spacing
    signature_space: int = Field(default=65, description="Vertical height in px for physical/digital signature clearance")
    signature_margin_top: str = Field(default="28px", description="Margin above signature blocks")

    # Legal & Institutional Notes
    statutory_note: str = Field(
        default="<b>Note:</b> In case of any discrepancy in the marksheet, candidate may apply for correction within a period of four weeks from the date of issue to the office of the Executive Registrar.",
        description="Statutory disclaimer"
    )


def _load_persisted_config() -> MarksheetTemplateConfig:
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return MarksheetTemplateConfig.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to load persisted template config from {CONFIG_FILE_PATH}: {e}")
    return MarksheetTemplateConfig()


# Active singleton configuration instance initialized from persistent disk storage
_ACTIVE_CONFIG: MarksheetTemplateConfig = _load_persisted_config()


def get_template_config() -> MarksheetTemplateConfig:
    global _ACTIVE_CONFIG
    return _ACTIVE_CONFIG


def update_template_config(new_config: MarksheetTemplateConfig) -> MarksheetTemplateConfig:
    global _ACTIVE_CONFIG
    _ACTIVE_CONFIG = new_config
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_config.model_dump_json(indent=2))
        logger.info(f"Persisted updated template config to {CONFIG_FILE_PATH}")
    except Exception as e:
        logger.error(f"Failed to persist template config to {CONFIG_FILE_PATH}: {e}", exc_info=True)
    return _ACTIVE_CONFIG
