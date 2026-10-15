"""
FastAPI Route for Official Marksheet PDF & Bulk ZIP Generation (/api/pdf)
Phase 4: High-resolution A4 PDF print engine using Playwright.
Branding: VidyaMarksheet by VidyaLabs
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, Query, HTTPException, Response, status
from fastapi.responses import Response

from backend.schemas.canonical_models import StudentRecord
from backend.parsers.exam_cell_parser import ExamCellParserAdapter
from backend.evaluation_engine import EvaluationEngine, EvaluatedStudentRecord
from backend.audit_engine import QualityAuditGate
from backend.pdf_generator import MarksheetPdfGenerator, clean_filename_token
from backend.template_config import MarksheetTemplateConfig, get_template_config, update_template_config
from backend.debug_archetypes import get_5_debug_categories

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pdf", tags=["Marksheet PDF Generation"])
pdf_generator = MarksheetPdfGenerator()


@router.get("/template-config", response_model=MarksheetTemplateConfig)
def get_current_template_config():
    """Returns the active Marksheet Template layout, styling, and text settings."""
    return get_template_config()


@router.post("/template-config", response_model=MarksheetTemplateConfig)
def save_template_config(config: MarksheetTemplateConfig):
    """Updates and persists the active Marksheet Template configuration."""
    return update_template_config(config)


@router.get("/debug-categories")
def get_default_debug_categories():
    """Returns 5 certified debug marksheet categories (Pass, Grace, Fail, Distinction, Borderline)."""
    return get_5_debug_categories()


@router.post("/debug-categories")
def get_custom_debug_categories(students: List[EvaluatedStudentRecord]):
    """Categorizes uploaded students into the 5 debug categories, supplementing any missing ones with certified archetypes."""
    return get_5_debug_categories(students)


@router.post("/preview-html")
def preview_marksheet_html(
    student: EvaluatedStudentRecord,
    semester: int = Query(default=1, ge=1, le=8),
    session: str = Query(default="JANUARY - 2026"),
    date: Optional[str] = Query(default=None)
):
    """Returns raw HTML string of the official SGPGIMS marksheet for inline preview."""
    try:
        html_content = pdf_generator.render_html(
            student=student,
            semester_number=semester,
            session_month_year=session,
            issue_date=date
        )
        return Response(content=html_content, media_type="text/html")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error rendering marksheet HTML: {str(e)}"
        )


@router.post("/student")
def generate_single_student_pdf(
    student: EvaluatedStudentRecord,
    semester: int = Query(default=1, ge=1, le=8),
    session: str = Query(default="JANUARY - 2026"),
    date: Optional[str] = Query(default=None)
):
    """
    Generates high-resolution Legal single marksheet PDF for an individual candidate.
    Returns application/pdf with content disposition.
    """
    try:
        pdf_bytes = pdf_generator.generate_student_pdf(
            student=student,
            semester_number=semester,
            session_month_year=session,
            issue_date=date
        )

        clean_name = clean_filename_token(student.student_name)
        filename = f"Marksheet_{student.roll_no}_{clean_name}.pdf"

        headers = {
            "Content-Disposition": f'inline; filename="{filename}"'
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating marksheet PDF: {str(e)}"
        )


@router.post("/bulk")
def generate_bulk_pdf_zip(
    students: List[EvaluatedStudentRecord],
    semester: int = Query(default=1, ge=1, le=8),
    session: str = Query(default="JANUARY - 2026"),
    date: Optional[str] = Query(default=None)
):
    """
    Generates individual PDFs for all students in the batch and packages
    them into a compressed .zip archive labeled by batch and semester.
    """
    if len(students) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student list cannot be empty for bulk PDF generation."
        )

    try:
        zip_bytes = pdf_generator.generate_bulk_zip(
            students=students,
            semester_number=semester,
            session_month_year=session,
            issue_date=date
        )

        zip_filename = f"SGPGIMS_BSc_Nursing_Sem{semester}_Marksheets.zip"
        headers = {
            "Content-Disposition": f'attachment; filename="{zip_filename}"'
        }
        return Response(content=zip_bytes, media_type="application/zip", headers=headers)
    except Exception as e:
        err_msg = str(e).strip() or repr(e)
        logger.error(f"Error generating bulk ZIP archive: {err_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating bulk ZIP archive: {err_msg}"
        )


@router.post("/from-excel")
def generate_bulk_from_excel(
    file: UploadFile = File(..., description="Raw Examination Cell Excel file (.xlsx, .xls)"),
    sheet_name: Optional[str] = Form(None),
    semester: int = Form(1),
    session: str = Form("JANUARY - 2026"),
    acknowledged_override: bool = Form(False)
):
    """
    End-to-end PDF Pipeline:
    1. Ingests raw Excel file via Phase 1B parser adapter
    2. Evaluates marks and SGPA via Phase 2 evaluation engine
    3. Audits mathematical invariance via Phase 3 Quality Audit Gate
    4. If critical anomalies exist and acknowledged_override is False:
       Blocks generation with HTTP 403.
    5. If clean or acknowledged:
       Generates and returns bulk .zip archive containing all student PDFs.
    """
    filename = file.filename or "unknown.xlsx"
    if not any(filename.lower().endswith(ext) for ext in (".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only .xlsx and .xls files are supported."
        )

    try:
        content = file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    try:
        adapter = ExamCellParserAdapter(file_content=content, sheet_name=sheet_name)
        students = adapter.parse()

        engine = EvaluationEngine(semester_number=semester)
        eval_batch = engine.evaluate_batch(students)

        # Quality Audit Gate Check
        gate = QualityAuditGate(semester_number=semester)
        audit_report = gate.audit_batch(students, evaluated_students=eval_batch.results)

        if not audit_report.is_valid and not acknowledged_override:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"PDF generation locked by Quality Audit Gate: {audit_report.critical_errors_count} critical "
                    f"invariance/demographic error(s) detected. Acknowledge override required to proceed."
                )
            )

        zip_bytes = pdf_generator.generate_bulk_zip(
            students=eval_batch.results,
            semester_number=semester,
            session_month_year=session
        )

        zip_filename = f"SGPGIMS_BSc_Nursing_Sem{semester}_Marksheets.zip"
        headers = {
            "Content-Disposition": f'attachment; filename="{zip_filename}"'
        }
        return Response(content=zip_bytes, media_type="application/zip", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e).strip() or repr(e)
        logger.error(f"Error generating marksheets from Excel: {err_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error generating marksheets from Excel: {err_msg}"
        )
