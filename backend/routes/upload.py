"""
FastAPI Route for Excel Ingestion (/api/upload)
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
"""

import io
from typing import Optional, List, Any
import openpyxl
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from pydantic import BaseModel

from backend.parsers.excel_parser import ExcelSheetParser, clean_str, detect_semester_from_text
from backend.schemas.student_schemas import IngestionResponse

router = APIRouter(prefix="/api", tags=["Excel Ingestion"])


class SheetInfo(BaseModel):
    name: str
    row_count: int
    col_count: int


class FileInspectionResponse(BaseModel):
    filename: str
    sheets: List[SheetInfo]
    recommended_sheet: str
    detected_semester: int
    preview_rows: List[List[Any]]


@router.post("/inspect-file", response_model=FileInspectionResponse)
async def inspect_uploaded_file(
    file: UploadFile = File(..., description="Excel file to inspect")
):
    """
    Fast inspection of uploaded Excel file structure.
    Returns all sheet names, row counts, recommended sheet, and a 10-row preview grid.
    """
    filename = file.filename or "unknown.xlsx"
    if not any(filename.lower().endswith(ext) for ext in (".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only .xlsx and .xls files are supported."
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheets_info: List[SheetInfo] = []
        recommended_sheet = None
        detected_sem = None

        for s_name in wb.sheetnames:
            ws = wb[s_name]
            sheets_info.append(SheetInfo(
                name=s_name,
                row_count=ws.max_row,
                col_count=ws.max_column
            ))
            s_lower = s_name.lower()
            if any(k in s_lower for k in ["semester", "sem", "data", "master"]) and "sample" not in s_lower:
                if not recommended_sheet:
                    recommended_sheet = s_name
            if not detected_sem:
                for r in range(1, min(6, ws.max_row + 1)):
                    row_text = " ".join([clean_str(ws.cell(r, c).value) for c in range(1, min(10, ws.max_column + 1))])
                    s = detect_semester_from_text(row_text) or detect_semester_from_text(s_name)
                    if s:
                        detected_sem = s
                        break

        if not recommended_sheet and wb.sheetnames:
            recommended_sheet = wb.sheetnames[0]

        primary_ws = wb[recommended_sheet]
        preview_rows: List[List[Any]] = []
        for r in range(1, min(12, primary_ws.max_row + 1)):
            row_vals = [clean_str(primary_ws.cell(r, c).value) for c in range(1, min(15, primary_ws.max_column + 1))]
            if any(row_vals):
                preview_rows.append(row_vals)

        return FileInspectionResponse(
            filename=filename,
            sheets=sheets_info,
            recommended_sheet=recommended_sheet,
            detected_semester=detected_sem or 1,
            preview_rows=preview_rows
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error inspecting Excel file: {str(e)}"
        )


@router.post("/upload", response_model=IngestionResponse)
async def upload_examination_sheet(
    file: UploadFile = File(..., description="Excel marksheet file (.xlsx, .xls)"),
    semester: Optional[int] = Form(None, ge=1, le=8, description="Optional explicit semester number (1-8)"),
    sheet_name: Optional[str] = Form(None, description="Optional sheet name to parse")
):
    """
    Ingests B.Sc. Nursing Examination Excel sheet (.xlsx / .xls),
    dynamically extracts student demographics, component marks,
    evaluates INC 10-point grades, passing thresholds, SGPA,
    and returns structured JSON data mapped directly to the semester course schema.
    """
    # 1. Validate file extension
    filename = file.filename or "unknown.xlsx"
    valid_extensions = (".xlsx", ".xls")
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only .xlsx and .xls files are supported."
        )

    # 2. Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # 3. Parse with dynamic sheet parser
    try:
        parser = ExcelSheetParser(
            file_content=content,
            filename=filename,
            explicit_semester=semester,
            sheet_name=sheet_name
        )
        response = parser.parse()

        # Synchronize into persistent PostgreSQL database (vidya_examination_db)
        if response.success and response.results:
            try:
                from backend.db.database import get_sync_session
                from backend.db.repository import ExaminationRepository
                with get_sync_session() as session:
                    repo = ExaminationRepository(session)
                    batch = repo.get_or_create_batch("Batch 2022-2026")
                    for rec in response.results:
                        try:
                            stu_info = rec.student
                            clean_roll = str(stu_info.roll_no).strip()
                            clean_enroll = str(stu_info.enrollment_no).strip() or f"EN_{clean_roll}"
                            student = repo.upsert_student(
                                batch_id=batch.id,
                                roll_no=clean_roll,
                                enrollment_no=clean_enroll,
                                student_name=str(stu_info.name).strip(),
                                father_name=str(stu_info.father_name).strip() or "N/A",
                                modified_by="API_UPLOAD_SYNC"
                            )
                            reg = repo.upsert_registration(
                                student_id=student.id,
                                semester_number=response.semester,
                                exam_month_year=rec.examination_session or "JANUARY - 2026",
                                total_credits=float(rec.total_sgpa_credits or 14),
                                sgpa_credits=float(rec.total_sgpa_credits or 14),
                                grand_total_obtained=float(rec.grand_total_obtained or 0),
                                grand_total_max=float(rec.grand_total_max or 250),
                                percentage=float(rec.overall_percentage or 0),
                                credit_score=float(rec.total_credit_score or 0),
                                sgpa=float(rec.sgpa or 0),
                                result_status=rec.result_status,
                                result_remarks=rec.remarks,
                                modified_by="API_UPLOAD_SYNC"
                            )
                            for comp in rec.courses:
                                db_course = repo.get_course_by_code(response.semester, comp.course_code)
                                if not db_course:
                                    sem_courses = repo.get_semester_courses(response.semester)
                                    for sc in sem_courses:
                                        if any(w.lower() in sc.course_title.lower() for w in comp.course_title.split()[:2]):
                                            db_course = sc
                                            break
                                if db_course:
                                    repo.upsert_course_mark(
                                        registration_id=reg.id,
                                        course_id=db_course.id,
                                        internal_obtained=float(comp.internal_obtained or 0.0),
                                        external_obtained=float(comp.external_obtained or 0.0),
                                        total_obtained=float(comp.total_obtained or 0.0),
                                        percentage=float(comp.percentage or 0.0),
                                        letter_grade=comp.letter_grade or "C",
                                        grade_point=int(comp.grade_point or 0),
                                        course_result="PASS" if comp.is_pass else "FAIL",
                                        grace_awarded=float(comp.grace_marks or 0.0),
                                        student_roll_no=clean_roll,
                                        modified_by="API_UPLOAD_SYNC"
                                    )
                            repo.recalculate_cumulative_summary(student.id)
                            session.commit()
                        except Exception as item_err:
                            session.rollback()
                            print(f"Notice: Failed to sync student {rec.student.roll_no}: {item_err}")
            except Exception as db_err:
                print(f"Notice: PostgreSQL background sync: {db_err}")

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error parsing examination sheet: {str(e)}"
        )
