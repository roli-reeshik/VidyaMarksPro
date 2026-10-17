"""
Automated Structured Marksheet File Exporter Route
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.

Endpoints:
- POST /api/v1/marksheets/export-batch:
    Batch exports structured student marksheet PDFs to organized disk directories:
    {MARKSHEET_STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/{Proper_Name}_{Roll_No}.pdf
- POST /api/v1/marksheets/export-single:
    Exports individual candidate marksheet PDF to the designated structured directory.
- GET  /api/v1/marksheets/export-config:
    Returns the active storage directory configuration, available sessions, and semesters.
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_sync_session
from backend.db.models import Student, StudentSemesterRegistration, MarksAuditLog
from backend.db.repository import ExaminationRepository
from backend.pdf_generator import (
    MarksheetPdfGenerator,
    MarksheetStudentAdapter,
    build_export_filepath,
    sanitize_proper_case_name,
)
from backend.security import require_operator, require_viewer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/marksheets", tags=["Automated Structured Marksheet File Exporter"])
pdf_generator = MarksheetPdfGenerator()


def _get_base_storage_dir(custom_dir: Optional[str] = None) -> str:
    """Resolves and returns the absolute base directory for marksheet storage."""
    if custom_dir and custom_dir.strip():
        raw_path = custom_dir.strip()
    else:
        raw_path = os.getenv("MARKSHEET_STORAGE_DIR", "./exported_marksheets")
    return os.path.abspath(raw_path)


def _extract_year(session_str: str) -> str:
    """Extracts 4-digit academic year from session string or defaults to current year."""
    match = re.search(r"\b(20\d\d)\b", str(session_str))
    return match.group(1) if match else str(datetime.now().year)


class BatchExportPayload(BaseModel):
    semester: int = Field(..., ge=1, le=8, description="Target Semester (1-8)")
    exam_month_year: str = Field(..., description="Target Examination Session (e.g. 'JANUARY - 2026')")
    custom_directory: Optional[str] = Field(None, description="Optional custom base directory path")
    watermarked_as_final: Optional[bool] = Field(False, description="Flag for watermarking as final")


class SingleExportPayload(BaseModel):
    semester: int = Field(..., ge=1, le=8, description="Target Semester (1-8)")
    roll_no: str = Field(..., description="Target Student Roll Number")
    exam_month_year: Optional[str] = Field(None, description="Optional target Examination Session")
    custom_directory: Optional[str] = Field(None, description="Optional custom base directory path")
    watermarked_as_final: Optional[bool] = Field(False, description="Flag for watermarking as final")


@router.get("/export-config")
def get_export_config(current_user: Any = Depends(require_viewer)):
    """Returns current marksheet storage directory configuration and available sessions."""
    base_dir = _get_base_storage_dir()
    with get_sync_session() as session:
        sessions = [
            row[0]
            for row in session.query(StudentSemesterRegistration.exam_month_year).distinct().all()
            if row[0]
        ]
        semesters = [
            row[0]
            for row in session.query(StudentSemesterRegistration.semester_number).distinct().all()
            if row[0]
        ]

    return {
        "status": "success",
        "default_storage_dir": base_dir,
        "available_sessions": sorted(sessions),
        "available_semesters": sorted(semesters),
        "naming_specification": "{Student_Name_In_Proper_Case}_{Roll_No}.pdf",
        "hierarchy_specification": "{STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/",
        "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
    }


@router.post("/export-batch")
def export_batch_marksheets(
    payload: BatchExportPayload,
    current_user: Any = Depends(require_operator),
):
    """
    Executes automated batch marksheet PDF generation and structured disk persistence:
    1. Reads MARKSHEET_STORAGE_DIR or custom_directory.
    2. Builds sub-directory hierarchy: {MARKSHEET_STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/.
    3. Generates high-res Legal PDFs for all registered candidates in the session.
    4. Formats file names: {Proper_Name}_{Roll_No}.pdf.
    5. Logs the export in marks_audit_log table in PostgreSQL.
    6. Returns { total_exported: int, output_directory: string, file_list: string[] }.
    """
    semester = payload.semester
    session_text = payload.exam_month_year.strip()
    base_dir = _get_base_storage_dir(payload.custom_directory)
    academic_year = _extract_year(session_text)

    with get_sync_session() as session:
        repo = ExaminationRepository(session)

        # Query all registrations for this semester and session
        query = (
            session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(StudentSemesterRegistration.semester_number == semester)
        )

        if session_text.lower() != "all":
            query = query.filter(StudentSemesterRegistration.exam_month_year.ilike(f"%{session_text}%"))

        registrations = query.order_by(Student.roll_no).all()

        if not registrations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No student registrations found for Semester {semester} with exam session '{session_text}'.",
            )

        file_list: List[str] = []
        target_dir = ""

        # Process each student marksheet
        for reg, student in registrations:
            marksheet_data = repo.get_student_marksheet_data(
                semester_number=semester,
                roll_no=student.roll_no,
            )

            if not marksheet_data:
                continue

            # Build destination path
            dir_path, filename, full_path = build_export_filepath(
                base_dir=base_dir,
                academic_year=academic_year,
                exam_session=reg.exam_month_year or session_text,
                semester=semester,
                student_name=student.student_name,
                roll_no=student.roll_no,
            )
            target_dir = dir_path

            # Render and write PDF
            try:
                adapter = MarksheetStudentAdapter(marksheet_data)
                pdf_bytes = pdf_generator.generate_student_pdf(
                    student=adapter,
                    semester_number=semester,
                    session_month_year=reg.exam_month_year or session_text,
                )
                with open(full_path, "wb") as f:
                    f.write(pdf_bytes)
                file_list.append(filename)
            except Exception as e:
                logger.error(f"Error generating marksheet for {student.roll_no}: {e}", exc_info=True)
                continue

        # Log action in marks_audit_log
        try:
            audit_entry = MarksAuditLog(
                entity_type="export_batch",
                semester_number=semester,
                field_name="batch_pdf_export",
                old_value=None,
                new_value=f"Exported {len(file_list)} marksheets to {target_dir}",
                change_reason=f"Automated structured marksheet batch file export for session '{session_text}'",
                modified_by=current_user.username,
            )
            session.add(audit_entry)
            session.commit()
        except Exception as audit_err:
            session.rollback()
            logger.warning(f"Failed to record export audit log: {audit_err}")

        return {
            "status": "success",
            "message": f"Successfully exported {len(file_list)} structured marksheet PDFs.",
            "total_exported": len(file_list),
            "output_directory": target_dir,
            "academic_year": academic_year,
            "exam_session": session_text,
            "semester": semester,
            "file_list": file_list,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.post("/export-single")
def export_single_marksheet(
    payload: SingleExportPayload,
    current_user: Any = Depends(require_operator),
):
    """
    Exports a single candidate's marksheet to the structured disk path:
    {MARKSHEET_STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/{Proper_Name}_{Roll_No}.pdf
    """
    semester = payload.semester
    roll_no = payload.roll_no.strip()
    base_dir = _get_base_storage_dir(payload.custom_directory)

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        student = session.query(Student).filter_by(roll_no=roll_no).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with Roll No '{roll_no}' not found.",
            )

        marksheet_data = repo.get_student_marksheet_data(semester_number=semester, roll_no=roll_no)
        if not marksheet_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Marksheet data not found for Roll No '{roll_no}' in Semester {semester}.",
            )

        session_str = payload.exam_month_year or marksheet_data.get("examination_session") or "JANUARY - 2026"
        academic_year = _extract_year(session_str)

        dir_path, filename, full_path = build_export_filepath(
            base_dir=base_dir,
            academic_year=academic_year,
            exam_session=session_str,
            semester=semester,
            student_name=student.student_name,
            roll_no=student.roll_no,
        )

        try:
            adapter = MarksheetStudentAdapter(marksheet_data)
            pdf_bytes = pdf_generator.generate_student_pdf(
                student=adapter,
                semester_number=semester,
                session_month_year=session_str,
            )
            with open(full_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate and write PDF: {str(e)}",
            )

        # Audit log entry
        try:
            audit_entry = MarksAuditLog(
                entity_type="student",
                student_roll_no=roll_no,
                semester_number=semester,
                field_name="single_pdf_export",
                old_value=None,
                new_value=full_path,
                change_reason=f"Structured PDF export generated for {filename}",
                modified_by=current_user.username,
            )
            session.add(audit_entry)
            session.commit()
        except Exception as audit_err:
            session.rollback()
            logger.warning(f"Failed to record single export audit log: {audit_err}")

        return {
            "status": "success",
            "message": f"Marksheet successfully exported to {full_path}",
            "filename": filename,
            "output_directory": dir_path,
            "file_path": full_path,
            "student_name": sanitize_proper_case_name(student.student_name),
            "roll_no": student.roll_no,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }
