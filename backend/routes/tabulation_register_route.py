"""
FastAPI Route for Formal Gazette Tabulation Register (TR) Export Engine
Endpoints for A3/Legal Landscape Ledger generation in PDF & Excel (.xlsx) formats.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Response, status, Body
from pydantic import BaseModel

from backend.db.database import get_sync_session
from backend.db.models import Batch
from backend.tr_generator import (
    build_tr_data_from_db,
    build_tr_data_from_evaluated_students,
    TabulationRegisterPdfGenerator,
    TabulationRegisterExcelGenerator,
    TabulationRegisterData,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tabulation-register", tags=["Tabulation Register Export Engine"])

pdf_generator = TabulationRegisterPdfGenerator()
excel_generator = TabulationRegisterExcelGenerator()


class ExportTrPayload(BaseModel):
    students: List[Dict[str, Any]]
    semester_number: int = 1
    batch_name: str = "Batch 2022-2026"
    session_month_year: str = "JANUARY - 2026"
    page_size: int = 15


# -----------------------------------------------------------------------------
# 1. Database-Bound Endpoints
# -----------------------------------------------------------------------------

@router.get("/data")
def get_tabulation_register_data(
    semester: int = Query(..., ge=1, le=8, description="Semester Number (1-8)"),
    batch_id: Optional[int] = Query(None, description="Optional cohort batch ID"),
    page_size: int = Query(15, ge=5, le=50, description="Candidates per page")
):
    """
    Returns structured JSON data for the Tabulation Register queried from PostgreSQL.
    """
    with get_sync_session() as session:
        tr_data = build_tr_data_from_db(
            session=session,
            semester_number=semester,
            batch_id=batch_id,
            page_size=page_size
        )
        return tr_data.model_dump()


@router.get("/preview-html")
def preview_tabulation_register_html(
    semester: int = Query(..., ge=1, le=8, description="Semester Number (1-8)"),
    batch_id: Optional[int] = Query(None, description="Optional cohort batch ID"),
    page_size: int = Query(15, ge=5, le=50, description="Candidates per page")
):
    """
    Renders raw HTML string of the official A3 Landscape Tabulation Register for in-browser inspection.
    """
    try:
        with get_sync_session() as session:
            tr_data = build_tr_data_from_db(
                session=session,
                semester_number=semester,
                batch_id=batch_id,
                page_size=page_size
            )
            html_content = pdf_generator.render_html(tr_data)
            return Response(content=html_content, media_type="text/html")
    except Exception as e:
        logger.error(f"Error rendering Tabulation Register preview HTML: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error rendering Tabulation Register preview: {str(e)}"
        )


@router.get("/pdf")
def download_tabulation_register_pdf(
    semester: int = Query(..., ge=1, le=8, description="Semester Number (1-8)"),
    batch_id: Optional[int] = Query(None, description="Optional cohort batch ID"),
    paper_size: str = Query("A3", description="Paper size: 'A3' or 'Legal'"),
    page_size: int = Query(15, ge=5, le=50, description="Candidates per page")
):
    """
    Generates and downloads the official high-resolution Gazette Tabulation Register PDF (A3/Legal Landscape, 300 DPI).
    """
    try:
        with get_sync_session() as session:
            tr_data = build_tr_data_from_db(
                session=session,
                semester_number=semester,
                batch_id=batch_id,
                page_size=page_size
            )
            if tr_data.total_appeared == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No student examination records found in PostgreSQL for Semester {semester}."
                )

            pdf_bytes = pdf_generator.generate_pdf(tr_data, paper_size=paper_size)
            filename = f"SGPGIMS_Tabulation_Register_Sem{semester}_{tr_data.batch_name.replace(' ', '_')}.pdf"
            headers = {
                "Content-Disposition": f'inline; filename="{filename}"'
            }
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Tabulation Register PDF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Tabulation Register PDF: {str(e)}"
        )


@router.get("/excel")
def download_tabulation_register_excel(
    semester: int = Query(..., ge=1, le=8, description="Semester Number (1-8)"),
    batch_id: Optional[int] = Query(None, description="Optional cohort batch ID"),
):
    """
    Generates and downloads the official formatted Gazette Tabulation Register in Excel (.xlsx) format.
    """
    try:
        with get_sync_session() as session:
            tr_data = build_tr_data_from_db(
                session=session,
                semester_number=semester,
                batch_id=batch_id,
                page_size=15
            )
            if tr_data.total_appeared == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No student examination records found in PostgreSQL for Semester {semester}."
                )

            excel_bytes = excel_generator.generate_excel(tr_data)
            filename = f"SGPGIMS_Tabulation_Register_Sem{semester}_{tr_data.batch_name.replace(' ', '_')}.xlsx"
            headers = {
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
            return Response(
                content=excel_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers=headers
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Tabulation Register Excel: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Tabulation Register Excel: {str(e)}"
        )


# -----------------------------------------------------------------------------
# 2. Upload / In-Memory Payload Endpoints
# -----------------------------------------------------------------------------

@router.post("/data-from-payload")
def get_tabulation_register_data_from_payload(
    payload: ExportTrPayload = Body(...)
):
    """
    Constructs and returns structured TabulationRegisterData directly from in-memory student records.
    """
    if len(payload.students) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student list cannot be empty."
        )

    try:
        tr_data = build_tr_data_from_evaluated_students(
            students=payload.students,
            semester_number=payload.semester_number,
            batch_name=payload.batch_name,
            session_month_year=payload.session_month_year,
            page_size=payload.page_size
        )
        return tr_data.model_dump()
    except Exception as e:
        logger.error(f"Error constructing Tabulation Register data from payload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error constructing Tabulation Register: {str(e)}"
        )


@router.post("/sync-to-db")
def sync_tabulation_register_to_db(
    payload: ExportTrPayload = Body(...)
):
    """
    Persists/synchronizes all provided student records and their marks into local PostgreSQL (vidya_examination_db).
    """
    if len(payload.students) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student list cannot be empty for database synchronization."
        )

    try:
        from backend.db.repository import ExaminationRepository
        with get_sync_session() as session:
            repo = ExaminationRepository(session)
            batch = repo.get_or_create_batch(batch_name=payload.batch_name)
            sem_num = payload.semester_number
            synced_count = 0

            for s in payload.students:
                s_roll = str(getattr(s, "roll_no", None) or (s.get("roll_no", "") if isinstance(s, dict) else "")).strip()
                s_enroll = str(getattr(s, "enroll_no", None) or (s.get("enroll_no", "") if isinstance(s, dict) else "")).strip()
                s_name = str(getattr(s, "student_name", None) or (s.get("student_name", "") if isinstance(s, dict) else "")).strip()
                s_father = str(getattr(s, "father_name", None) or (s.get("father_name", "") if isinstance(s, dict) else "")).strip()
                s_status = str(getattr(s, "result_status", None) or (s.get("result_status", "PASS") if isinstance(s, dict) else "PASS")).strip()
                s_remarks = str(getattr(s, "raw_remarks", None) or (s.get("raw_remarks", "") if isinstance(s, dict) else "")).strip()
                s_attempt = str(getattr(s, "attempt_label", None) or (s.get("attempt_label", "MAIN") if isinstance(s, dict) else "MAIN")).strip()

                if not s_roll:
                    continue

                student = repo.upsert_student(
                    batch_id=batch.id,
                    roll_no=s_roll,
                    enrollment_no=s_enroll or f"EN_{s_roll}",
                    student_name=s_name,
                    father_name=s_father or "N/A",
                    modified_by="TR_SYNC"
                )

                s_tot = float(getattr(s, "total_marks_obtained", None) or (s.get("total_marks_obtained", 0) if isinstance(s, dict) else 0) or 0)
                s_max = float(getattr(s, "total_marks_max", None) or (s.get("total_marks_max", 250) if isinstance(s, dict) else 250) or 250)
                s_pct = float(getattr(s, "overall_percentage", None) or (s.get("overall_percentage", 0) if isinstance(s, dict) else 0) or 0)
                s_sgpa = float(getattr(s, "sgpa", None) or (s.get("sgpa", 0) if isinstance(s, dict) else 0) or 0)
                s_credits = float(getattr(s, "sgpa_divisor_credits", None) or (s.get("sgpa_divisor_credits", 14) if isinstance(s, dict) else 14) or 14)

                reg = repo.upsert_registration(
                    student_id=student.id,
                    semester_number=sem_num,
                    exam_month_year=payload.session_month_year,
                    exam_type=s_attempt,
                    attempt_label=s_attempt,
                    total_credits=s_credits,
                    sgpa_credits=s_credits,
                    grand_total_obtained=s_tot,
                    grand_total_max=s_max,
                    percentage=s_pct,
                    sgpa=s_sgpa,
                    result_status=s_status,
                    result_remarks=s_remarks,
                    modified_by="TR_SYNC"
                )

                c_dict = getattr(s, "courses", None) or (s.get("courses", {}) if isinstance(s, dict) else {})
                if isinstance(c_dict, dict):
                    for c_key, c_val in c_dict.items():
                        c_code = getattr(c_val, "course_code", None) or (c_val.get("course_code", c_key) if isinstance(c_val, dict) else c_key)
                        db_course = repo.get_course_by_code(sem_num, str(c_code))
                        if not db_course:
                            sem_courses = repo.get_semester_courses(sem_num)
                            for sc in sem_courses:
                                if c_key.upper() in sc.course_code.upper() or any(w.lower() in sc.course_title.lower() for w in str(c_code).split()[:2]):
                                    db_course = sc
                                    break
                        if not db_course:
                            continue

                        ia_val = float(getattr(c_val, "internal_marks", None) or (c_val.get("internal_marks", 0) if isinstance(c_val, dict) else 0) or 0)
                        ea_val = float(getattr(c_val, "effective_external", None) or (c_val.get("effective_external", 0) if isinstance(c_val, dict) else 0) or 0)
                        tot_val = float(getattr(c_val, "total_marks", None) or (c_val.get("total_marks", 0) if isinstance(c_val, dict) else 0) or 0)
                        grd = str(getattr(c_val, "letter_grade", None) or (c_val.get("letter_grade", "C") if isinstance(c_val, dict) else "C"))
                        gp = int(getattr(c_val, "grade_point", 0) or (c_val.get("grade_point", 0) if isinstance(c_val, dict) else 0) or 0)
                        is_p = getattr(c_val, "is_pass", True) if hasattr(c_val, "is_pass") else (c_val.get("is_pass", True) if isinstance(c_val, dict) else True)
                        is_ex = bool(getattr(c_val, "is_exempted", False) if hasattr(c_val, "is_exempted") else (c_val.get("is_exempted", False) if isinstance(c_val, dict) else False))
                        grc = float(getattr(c_val, "grace_marks", 0.0) or (c_val.get("grace_marks", 0.0) if isinstance(c_val, dict) else 0.0) or 0.0)

                        repo.upsert_course_mark(
                            registration_id=reg.id,
                            course_id=db_course.id,
                            internal_obtained=ia_val,
                            external_obtained=ea_val,
                            total_obtained=tot_val,
                            percentage=(tot_val / float(db_course.max_total or 100)) * 100.0,
                            letter_grade=grd,
                            grade_point=gp,
                            course_result="PASS" if (is_p or is_ex) else "FAIL",
                            grace_awarded=grc,
                            is_exempted=is_ex,
                            student_roll_no=s_roll,
                            modified_by="TR_SYNC"
                        )
                repo.recalculate_cumulative_summary(student.id)
                synced_count += 1

            session.commit()
            return {
                "status": "success",
                "success": True,
                "message": f"Successfully synchronized {synced_count} student examination records into PostgreSQL.",
                "synced_count": synced_count,
                "semester_number": sem_num,
                "batch_name": payload.batch_name
            }
    except Exception as e:
        logger.error(f"Error syncing Tabulation Register to DB: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing to PostgreSQL: {str(e)}"
        )


@router.post("/export-pdf")
def export_tabulation_register_pdf_from_payload(
    payload: ExportTrPayload = Body(...)
):
    """
    Generates and downloads the Gazette Tabulation Register PDF from uploaded student records.
    """
    if len(payload.students) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student list cannot be empty for Tabulation Register export."
        )

    try:
        tr_data = build_tr_data_from_evaluated_students(
            students=payload.students,
            semester_number=payload.semester_number,
            batch_name=payload.batch_name,
            session_month_year=payload.session_month_year,
            page_size=payload.page_size
        )
        pdf_bytes = pdf_generator.generate_pdf(tr_data, paper_size="A3")
        filename = f"SGPGIMS_Tabulation_Register_Sem{payload.semester_number}.pdf"
        headers = {
            "Content-Disposition": f'inline; filename="{filename}"'
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except Exception as e:
        logger.error(f"Error generating Tabulation Register PDF from payload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Tabulation Register PDF: {str(e)}"
        )


@router.post("/export-excel")
def export_tabulation_register_excel_from_payload(
    payload: ExportTrPayload = Body(...)
):
    """
    Generates and downloads the formatted Gazette Tabulation Register Excel (.xlsx) from uploaded student records.
    """
    if len(payload.students) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student list cannot be empty for Tabulation Register export."
        )

    try:
        tr_data = build_tr_data_from_evaluated_students(
            students=payload.students,
            semester_number=payload.semester_number,
            batch_name=payload.batch_name,
            session_month_year=payload.session_month_year,
            page_size=payload.page_size
        )
        excel_bytes = excel_generator.generate_excel(tr_data)
        filename = f"SGPGIMS_Tabulation_Register_Sem{payload.semester_number}.xlsx"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error generating Tabulation Register Excel from payload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Tabulation Register Excel: {str(e)}"
        )
