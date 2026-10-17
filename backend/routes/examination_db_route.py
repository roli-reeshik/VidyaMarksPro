"""
FastAPI Route for Persistent Examination Database Operations.
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.
Endpoints:
- POST /api/v1/examination/upload-datasheet
- GET  /api/v1/marksheets/{semester}/{roll_no}
- GET  /api/v1/marksheets/{semester}/batch/{batch_id}
- GET  /api/v1/analytics/{semester}/{batch_id}
- GET  /api/v1/batches
- GET  /api/v1/audit-trail/{roll_no}
VidyaLabs Copyright © 2026.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.db.database import get_sync_session
from backend.db.models import Batch, Student, StudentSemesterRegistration, MarksAuditLog
from backend.db.repository import ExaminationRepository
from backend.parsers.excel_parser import ExcelSheetParser
from backend.parsers.exam_cell_parser import ExamCellParserAdapter
from backend.evaluation_engine import EvaluationEngine
from backend.security import require_subdean, require_authenticated, require_operator, require_viewer


router = APIRouter(prefix="/api/v1", tags=["PostgreSQL Examination Persistence Engine"])


def get_repo():
    """Dependency provider for ExaminationRepository."""
    with get_sync_session() as session:
        yield ExaminationRepository(session)


# -----------------------------------------------------------------------------
# 1. Upload & Ingestion Endpoint
# -----------------------------------------------------------------------------

@router.post("/examination/upload")
@router.post("/examination/upload-datasheet")
async def upload_examination_datasheet(
    file: UploadFile = File(..., description="Excel Marks Ledger / Datasheet (.xlsx, .xls, .xlsm)"),
    semester_number: int = Form(..., ge=1, le=8, description="Target Semester (1-8)"),
    batch_name: str = Form("Batch 2022-2026", description="Cohort Batch Name"),
    exam_month_year: Optional[str] = Form(None, description="Examination Session (e.g. 'JANUARY - 2026')"),
    exam_type: str = Form("MAIN", description="Exam type ('MAIN' or 'RE-APPEAR')"),
    sheet_name: Optional[str] = Form(None, description="Optional sheet name to parse"),
    attempt_number: Optional[int] = Form(None, description="Attempt number (0 for MAIN, 1 for REAPPEAR - I, etc.)"),
    attempt_label: Optional[str] = Form(None, description="Attempt label ('MAIN', 'REAPPEAR - I', 'REAPPEAR - II', etc.)"),
    current_user: Any = Depends(require_operator),
):
    """
    Ingests an Excel examination datasheet, evaluates candidate component scores,
    and atomically persists records into local PostgreSQL (vidya_examination_db).
    Supports Reappear cycles (REAPPEAR - I, REAPPEAR - II) and automatic subject exemption ('Ex.') carryover.
    Tracks demographics, course marks, and updates longitudinal CGPA summaries.
    """
    filename = file.filename or "datasheet.xlsx"
    valid_exts = (".xlsx", ".xls", ".xlsm")
    if not any(filename.lower().endswith(ext) for ext in valid_exts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: '{filename}'. Only .xlsx, .xls, and .xlsm files are supported."
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # Parsing strategy: Try standard ExcelSheetParser first; if no results, try ExamCellParserAdapter
    parsed_results = []
    session_text = exam_month_year

    try:
        excel_parser = ExcelSheetParser(file_content=content, filename=filename, sheet_name=sheet_name)
        excel_res = excel_parser.parse()
        if excel_res.success and excel_res.results:
            parsed_results = excel_res.results
            if not session_text and excel_res.examination_session:
                session_text = excel_res.examination_session
    except Exception:
        pass

    if not parsed_results:
        try:
            adapter = ExamCellParserAdapter(file_content=content, sheet_name=sheet_name)
            raw_records = adapter.parse()
            engine = EvaluationEngine(semester=semester_number)
            for r in raw_records:
                eval_res = engine.evaluate_record(r)
                parsed_results.append(eval_res)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse examination spreadsheet: {str(e)}"
            )

    if not parsed_results:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid student examination records could be extracted from the file."
        )

    if not session_text:
        session_text = f"SESSION - 2026"

    # Reappear cycle detection
    resolved_attempt_num = 0
    resolved_attempt_label = "MAIN"

    if attempt_number is not None:
        resolved_attempt_num = int(attempt_number)
        if attempt_label:
            resolved_attempt_label = attempt_label.strip()
        else:
            if resolved_attempt_num == 0:
                resolved_attempt_label = "MAIN"
            elif resolved_attempt_num == 1:
                resolved_attempt_label = "REAPPEAR - I"
            elif resolved_attempt_num == 2:
                resolved_attempt_label = "REAPPEAR - II"
            elif resolved_attempt_num == 3:
                resolved_attempt_label = "REAPPEAR - III"
            else:
                resolved_attempt_label = f"REAPPEAR - {resolved_attempt_num}"
    elif attempt_label:
        norm_label = attempt_label.strip().upper()
        if "REAPPEAR" in norm_label or "RE-APPEAR" in norm_label:
            if "II" in norm_label or "2" in norm_label:
                resolved_attempt_num = 2
                resolved_attempt_label = "REAPPEAR - II"
            elif "III" in norm_label or "3" in norm_label:
                resolved_attempt_num = 3
                resolved_attempt_label = "REAPPEAR - III"
            else:
                resolved_attempt_num = 1
                resolved_attempt_label = "REAPPEAR - I"
        else:
            resolved_attempt_num = 0
            resolved_attempt_label = "MAIN"
    else:
        # Probe from filename, sheet_name, exam_type, session_text
        probe_str = f"{filename} {sheet_name or ''} {exam_type or ''} {session_text or ''}".upper()
        if "-S2" in probe_str or "REAPPEAR - II" in probe_str or "REAPPEAR 2" in probe_str or "RE-APPEAR 2" in probe_str or "REAPPEAR-2" in probe_str:
            resolved_attempt_num = 2
            resolved_attempt_label = "REAPPEAR - II"
        elif "-S3" in probe_str or "REAPPEAR - III" in probe_str or "REAPPEAR 3" in probe_str or "RE-APPEAR 3" in probe_str or "REAPPEAR-3" in probe_str:
            resolved_attempt_num = 3
            resolved_attempt_label = "REAPPEAR - III"
        elif "-S1" in probe_str or "REAPPEAR" in probe_str or "RE-APPEAR" in probe_str or "SUPPLE" in probe_str:
            resolved_attempt_num = 1
            resolved_attempt_label = "REAPPEAR - I"
        else:
            resolved_attempt_num = 0
            resolved_attempt_label = "MAIN"

    final_exam_type = resolved_attempt_label if resolved_attempt_num > 0 else "MAIN"

    def _safe_float(val: Any) -> float:
        if val is None or val == "" or str(val).strip().upper() in ["EX.", "EX", "EXEMPTED", "AB", "ABSENT", "-"]:
            return 0.0
        try:
            return float(val)
        except Exception:
            return 0.0

    # Atomic DB Persistence
    saved_students = []
    passed_count = 0
    failed_count = 0

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch(batch_name=batch_name)

        for rec in parsed_results:
            # Handle both SemesterStudentResult and EvaluatedStudentRecord types
            if hasattr(rec, "student"):
                # SemesterStudentResult structure
                stu_info = rec.student
                roll_no = stu_info.roll_no.strip()
                enroll_no = stu_info.enrollment_no.strip()
                name = stu_info.name.strip()
                father_name = stu_info.father_name.strip()
                courses_list = rec.courses
                sgpa = float(rec.sgpa)
                sgpa_credits = float(rec.total_sgpa_credits)
                grand_tot = float(rec.grand_total_obtained)
                grand_max = float(rec.grand_total_max)
                pct = float(rec.overall_percentage)
                credit_score = float(rec.total_credit_score)
                res_status = rec.result_status
                res_remarks = rec.remarks
            else:
                # EvaluatedStudentRecord structure
                stu_info = rec.student
                roll_no = stu_info.roll_no.strip()
                enroll_no = stu_info.enroll_no.strip()
                name = stu_info.student_name.strip()
                father_name = stu_info.father_name.strip()
                courses_list = rec.courses
                sgpa = float(rec.sgpa)
                sgpa_credits = float(rec.sgpa_divisor_credits)
                grand_tot = float(rec.grand_total_obtained)
                grand_max = float(rec.grand_total_max)
                pct = float(rec.percentage)
                credit_score = float(rec.credit_score)
                res_status = rec.result_status
                res_remarks = rec.result_remarks

            # 1. Upsert Student
            student = repo.upsert_student(
                batch_id=batch.id,
                roll_no=roll_no,
                enrollment_no=enroll_no,
                student_name=name,
                father_name=father_name,
                institutional_status="REGULAR",
                modified_by="API_UPLOAD"
            )

            # 2. Upsert Registration
            try:
                reg = repo.upsert_registration(
                    student_id=student.id,
                    semester_number=semester_number,
                    exam_month_year=session_text,
                    exam_type=final_exam_type,
                    attempt_number=resolved_attempt_num,
                    attempt_label=resolved_attempt_label,
                    total_credits=sgpa_credits,
                    sgpa_credits=sgpa_credits,
                    grand_total_obtained=grand_tot,
                    grand_total_max=grand_max,
                    percentage=pct,
                    credit_score=credit_score,
                    sgpa=sgpa,
                    result_status=res_status,
                    result_remarks=res_remarks,
                    grading_performance=f"SGPA {sgpa}",
                    modified_by="API_UPLOAD"
                )
            except PermissionError as pe:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Candidate {roll_no} (Semester {semester_number}) is LOCKED. An Administrator must issue an 'Unlock for Re-evaluation' override with mandatory justification before records can be altered."
                )

            # 3. Upsert Course Marks
            for comp in courses_list:
                c_code = comp.course_code
                comp_name = getattr(comp, "component_name", None)
                comp_title = getattr(comp, "course_title", None)
                comp_cr = getattr(comp, "credits", None)
                db_course = repo.resolve_course(
                    semester_number=semester_number,
                    course_code=c_code,
                    component_name=comp_name,
                    course_title=comp_title,
                    credits=comp_cr
                )
                if not db_course:
                    continue

                part_a = None
                part_b = None
                part_c = None
                if hasattr(comp, "sub_components") and comp.sub_components:
                    if isinstance(comp.sub_components, dict):
                        for sub_k, sub_v in comp.sub_components.items():
                            k_up = str(sub_k).upper()
                            if any(x in k_up for x in ["PHAR", "ANAT", "MICR", "SECTION A", "PART A"]) and sub_v is not None:
                                part_a = _safe_float(sub_v)
                            elif any(x in k_up for x in ["PATH", "PHYS", "INFC", "NUTR", "SECTION B", "PART B"]) and sub_v is not None:
                                part_b = _safe_float(sub_v)
                            elif any(x in k_up for x in ["GEN", "SECTION C", "PART C"]) and sub_v is not None:
                                part_c = _safe_float(sub_v)
                    elif isinstance(comp.sub_components, list):
                        for sub in comp.sub_components:
                            sub_name = str(getattr(sub, "name", "")).upper()
                            sub_code = str(getattr(sub, "code", "")).upper()
                            sub_ob = getattr(sub, "obtained", None)
                            combined_sub = f"{sub_name} {sub_code}"
                            if any(x in combined_sub for x in ["PHAR", "ANAT", "MICR", "PART A", "SECTION A"]) and sub_ob is not None:
                                part_a = _safe_float(sub_ob)
                            elif any(x in combined_sub for x in ["PATH", "PHYS", "INFC", "NUTR", "PART B", "SECTION B"]) and sub_ob is not None:
                                part_b = _safe_float(sub_ob)
                            elif any(x in combined_sub for x in ["GEN", "PART C", "SECTION C"]) and sub_ob is not None:
                                part_c = _safe_float(sub_ob)

                is_pass = getattr(comp, "is_pass", False)
                grace = float(getattr(comp, "grace_marks", 0.0) or 0.0)
                is_ex = (
                    getattr(comp, "is_exempted", False)
                    or str(getattr(comp, "internal_obtained", "")).strip().upper() in ["EX.", "EX", "EXEMPTED"]
                    or str(getattr(comp, "external_obtained", "")).strip().upper() in ["EX.", "EX", "EXEMPTED"]
                )

                repo.upsert_course_mark(
                    registration_id=reg.id,
                    course_id=db_course.id,
                    internal_obtained=_safe_float(comp.internal_obtained),
                    external_obtained=_safe_float(comp.external_obtained),
                    total_obtained=_safe_float(comp.total_obtained),
                    percentage=_safe_float(getattr(comp, "percentage", 0.0)),
                    letter_grade=getattr(comp, "letter_grade", "F") or ("P" if is_ex else "F"),
                    grade_point=int(getattr(comp, "grade_point", 0) or 0),
                    course_result="PASS" if (is_pass or is_ex) else "FAIL",
                    grace_awarded=grace,
                    external_part_a=part_a,
                    external_part_b=part_b,
                    external_part_c=part_c,
                    is_exempted=is_ex,
                    student_roll_no=roll_no,
                    modified_by="API_UPLOAD"
                )

            # 4. Handle Reappear exemptions carry-over or recalculate cumulative summary
            if resolved_attempt_num > 0:
                updated_reg = repo.resolve_reappear_exemptions(
                    student_id=student.id,
                    semester_number=semester_number,
                    current_registration_id=reg.id,
                    attempt_label=resolved_attempt_label,
                    modified_by="API_UPLOAD"
                )
                if updated_reg:
                    sgpa = float(updated_reg.sgpa or 0.0)
                    res_status = updated_reg.result_status
            else:
                repo.recalculate_cumulative_summary(student.id)

            if "PASS" in res_status.upper():
                passed_count += 1
            else:
                failed_count += 1

            saved_students.append({
                "roll_no": roll_no,
                "student_name": name,
                "sgpa": sgpa,
                "result_status": res_status,
                "attempt_label": resolved_attempt_label,
            })

        session.commit()

    return {
        "success": True,
        "message": f"Successfully ingested {len(saved_students)} records into PostgreSQL database ({resolved_attempt_label}).",
        "database": "vidya_examination_db",
        "semester_number": semester_number,
        "batch_name": batch_name,
        "attempt_number": resolved_attempt_num,
        "attempt_label": resolved_attempt_label,
        "total_students": len(saved_students),
        "passed_students": passed_count,
        "failed_students": failed_count,
        "students": saved_students,
    }


# -----------------------------------------------------------------------------
# 2. Marksheet Retrieval Route (Single Student)
# -----------------------------------------------------------------------------

@router.get("/marksheets/{semester}/{roll_no}")
def get_marksheet_by_roll_no(
    semester: int,
    roll_no: str,
    current_user: Any = Depends(require_viewer),
):
    """
    Returns verified marksheet JSON data for a specific student and semester.
    Directly binds to Next.js Marksheet components (Sem1Marksheet to Sem8Marksheet).
    """
    if not (1 <= semester <= 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester must be an integer between 1 and 8."
        )

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        data = repo.get_student_marksheet_data(semester_number=semester, roll_no=roll_no)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Marksheet not found for Roll No '{roll_no}' in Semester {semester}."
            )
        return data


# -----------------------------------------------------------------------------
# 3. Batch Marksheet Retrieval Route (Whole Class)
# -----------------------------------------------------------------------------

@router.get("/marksheets/{semester}/batch/{batch_id}")
def get_batch_marksheets(
    semester: int,
    batch_id: int,
    current_user: Any = Depends(require_viewer),
):
    """
    Returns array of complete marksheet objects for all students in a batch cohort.
    Used for batch printing and bulk PDF compilation.
    """
    if not (1 <= semester <= 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester must be an integer between 1 and 8."
        )

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = session.query(Batch).filter_by(id=batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with ID {batch_id} not found."
            )

        marksheets = repo.get_batch_marksheets(semester_number=semester, batch_id=batch_id)
        return {
            "semester_number": semester,
            "batch_id": batch_id,
            "batch_name": batch.batch_name,
            "count": len(marksheets),
            "marksheets": marksheets,
        }


# -----------------------------------------------------------------------------
# 4. SQL-Aggregated Analytics Route
# -----------------------------------------------------------------------------

@router.get("/analytics/{semester}")
@router.get("/analytics/{semester}/{batch_id}")
def get_semester_analytics(
    semester: int,
    batch_id: Optional[int] = None,
    current_user: Any = Depends(require_viewer),
):
    """
    Returns SQL-aggregated performance analytics:
    - Pass rates and grace marks frequencies
    - Grade distribution (O, A+, A, B+, B, C, P, F)
    - Average / Highest / Lowest SGPA
    - Subject-wise pass/fail rates directly computed in PostgreSQL.
    """
    if not (1 <= semester <= 8):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester must be an integer between 1 and 8."
        )

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch_name = "All Batches"
        if batch_id:
            batch = session.query(Batch).filter_by(id=batch_id).first()
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Batch with ID {batch_id} not found."
                )
            batch_name = batch.batch_name

        analytics = repo.get_semester_analytics(semester_number=semester, batch_id=batch_id)
        analytics["batch_name"] = batch_name
        return analytics


# -----------------------------------------------------------------------------
# 5. Cohort Batches & Students Roster Routes
# -----------------------------------------------------------------------------

@router.get("/batches")
def list_batches(current_user: Any = Depends(require_viewer)):
    """Lists all registered student cohorts / batches."""
    with get_sync_session() as session:
        batches = session.query(Batch).order_by(Batch.id).all()
        return [
            {
                "id": b.id,
                "batch_name": b.batch_name,
                "start_year": b.start_year,
                "end_year": b.end_year,
                "total_prescribed_credits": b.total_prescribed_credits,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in batches
        ]


@router.get("/students")
def list_students(
    batch_id: Optional[int] = Query(None),
    current_user: Any = Depends(require_viewer),
):
    """Lists students, optionally filtered by cohort batch ID."""
    with get_sync_session() as session:
        q = session.query(Student).filter(Student.is_active == True)
        if batch_id:
            q = q.filter(Student.batch_id == batch_id)
        students = q.order_by(Student.roll_no).all()
        return [
            {
                "id": s.id,
                "roll_no": s.roll_no,
                "enrollment_no": s.enrollment_no,
                "student_name": s.student_name,
                "father_name": s.father_name,
                "institutional_status": s.institutional_status,
                "batch_id": s.batch_id,
                "batch_name": s.batch.batch_name if s.batch else None,
            }
            for s in students
        ]


# -----------------------------------------------------------------------------
# 6. Audit Trail Route
# -----------------------------------------------------------------------------

@router.get("/audit-trail/{roll_no}")
def get_student_audit_trail(roll_no: str):
    """Returns chronological audit log of all demographic and marks modifications."""
    with get_sync_session() as session:
        logs = (
            session.query(MarksAuditLog)
            .filter_by(student_roll_no=roll_no.strip())
            .order_by(MarksAuditLog.timestamp.desc())
            .all()
        )
        return [
            {
                "id": l.id,
                "entity_type": l.entity_type,
                "student_roll_no": l.student_roll_no,
                "field_name": l.field_name,
                "old_value": l.old_value,
                "new_value": l.new_value,
                "change_reason": l.change_reason,
                "modified_by": l.modified_by,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ]


# -----------------------------------------------------------------------------
# 7. Final Delivery Lifecycle Route (SubDean / Admin Authority)
# -----------------------------------------------------------------------------

class MarkAsFinalRequest(BaseModel):
    semester: int = Field(..., ge=1, le=8, description="Target Semester (1-8)")
    roll_numbers: List[str] = Field(default_factory=list, description="Target student roll numbers")
    delivered_by: Optional[str] = Field("Sub-Dean Examinations", description="Official delivering authority")


@router.post("/marksheets/mark-as-final")
def mark_marksheets_as_final(
    payload: MarkAsFinalRequest,
    current_user: Any = Depends(require_subdean),
):
    """
    Institutional Delivery State Transition:
    Marks specified student semester registrations as FINAL copy delivered.
    Protected by RBAC: Requires 'SubDean' or 'Admin' role.
    """
    from datetime import datetime, timezone
    from backend.db.models import Student, StudentSemesterRegistration

    with get_sync_session() as session:
        now_utc = datetime.now(timezone.utc)
        q = (
            session.query(StudentSemesterRegistration)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(StudentSemesterRegistration.semester_number == payload.semester)
        )
        if payload.roll_numbers:
            q = q.filter(Student.roll_no.in_(payload.roll_numbers))

        records = q.all()
        for reg in records:
            reg.delivery_status = "FINAL"
            reg.delivered_at = now_utc
            reg.delivered_by = payload.delivered_by or getattr(current_user, "full_name", "Sub-Dean Examinations")
        session.commit()

        return {
            "success": True,
            "message": f"Successfully marked {len(records)} marksheets as FINAL.",
            "total_updated": len(records),
            "delivered_at": now_utc.isoformat(),
            "delivered_by": payload.delivered_by or getattr(current_user, "full_name", "Sub-Dean Examinations")
        }

