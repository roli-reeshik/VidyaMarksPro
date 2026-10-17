"""
Scrutiny Verification & Remediation Route
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.

Endpoints:
- GET  /api/v1/scrutiny/session-context:
    Fetches raw spreadsheet rows, candidate roster, and active INC Gazette rules for the target semester.
- POST /api/v1/scrutiny/verify-student:
    Submits a scrutiny verification record (VERIFIED_CORRECT or NEEDS_CORRECTION),
    supporting multiple iterations, highlighted fields, and structured change recommendations.
- GET  /api/v1/scrutiny/pending-remediations:
    Lists all un-actioned scrutiny suggestions for Admin and Sub-Dean review.
- POST /api/v1/scrutiny/apply-remediation/{verification_id}:
    Admin-only endpoint that updates student course marks, recalculates grand totals, grades, and SGPA,
    and logs the action in marks_audit_log.
- POST /api/v1/scrutiny/dismiss-remediation/{verification_id}:
    Admin-only endpoint to dismiss a recommendation with internal admin notes.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.db.database import get_sync_session
from backend.db.models import (
    Student,
    StudentSemesterRegistration,
    StudentCourseMark,
    Course,
    ScrutinyVerification,
    MarksAuditLog,
)
from backend.db.repository import ExaminationRepository
from backend.grading import calculate_inc_grade
from backend.schemas.course_schemas import SEMESTER_DEFINITIONS, CourseType
from backend.security import require_scrutiny, require_subdean, require_admin

router = APIRouter(prefix="/api/v1/scrutiny", tags=["Scrutiny Verification Studio & Remediation"])


class StudentVerificationPayload(BaseModel):
    registration_id: int
    student_id: int
    semester_number: int
    verification_status: str = Field(..., description="'VERIFIED_CORRECT' or 'NEEDS_CORRECTION'")
    comments: Optional[str] = None
    highlighted_fields: Optional[List[str]] = Field(default_factory=list)
    suggested_changes: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DismissRemediationPayload(BaseModel):
    admin_notes: Optional[str] = Field("Dismissed by Administrator without changes.", description="Admin notes")


@router.get("/session-context")
def get_scrutiny_session_context(
    semester: int = Query(..., ge=1, le=8, description="Target Semester Number (1-8)"),
    exam_month_year: Optional[str] = Query(None, description="Examination Session Filter (e.g. 'JANUARY - 2026')"),
    current_user: Any = Depends(require_scrutiny),
):
    """
    Returns complete context for the Scrutiny Verification Studio:
    1. Active INC Gazette rules dictionary (divisor credits, course splits, min passing thresholds, 10-point scale).
    2. Student roster with scrutiny statuses, registration IDs, roll numbers, and names.
    3. Raw tabular datasheet rows representing the original spreadsheet for the left-pane viewer.
    """
    # 1. INC Gazette Rules for Semester
    sem_def = SEMESTER_DEFINITIONS.get(semester)
    inc_rules = {
        "semester_number": semester,
        "semester_name": sem_def.semester_name if sem_def else f"SEMESTER {semester}",
        "total_prescribed_credits": sem_def.total_prescribed_credits if sem_def else 21,
        "sgpa_divisor_credits": sem_def.sgpa_eligible_credits if sem_def else 21,
        "grand_total_marks": sem_def.grand_total_marks if sem_def else 400.0,
        "program_total_credits": 151.0,
        "courses": [],
        "grading_scale": [
            {"grade": "O", "grade_point": 10, "range": "85.00% & Above", "desc": "Outstanding"},
            {"grade": "A+", "grade_point": 9, "range": "80.00% to 84.99%", "desc": "Excellent"},
            {"grade": "A", "grade_point": 8, "range": "75.00% to 79.99%", "desc": "Very Good"},
            {"grade": "B+", "grade_point": 7, "range": "65.00% to 74.99%", "desc": "Good"},
            {"grade": "B", "grade_point": 6, "range": "60.00% to 64.99%", "desc": "Above Average"},
            {"grade": "C", "grade_point": 5, "range": "50.00% to 59.99%", "desc": "Pass / Average"},
            {"grade": "P", "grade_point": 4, "range": "40.00% to 49.99%", "desc": "Pass (English/Electives)"},
            {"grade": "F", "grade_point": 0, "range": "< 50.00% (<40% for Eng/El)", "desc": "Fail"},
        ],
    }

    # 2. Query Student Registrations and Catalog Courses from Database
    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        db_courses = repo.get_semester_courses(semester)

        if db_courses:
            for idx, dbc in enumerate(db_courses, start=1):
                sem_c = None
                if sem_def:
                    for sc in sem_def.courses:
                        if sc.course_code in dbc.course_code or dbc.course_code.startswith(sc.course_code.split()[0]):
                            sem_c = sc
                            break

                ia_min_pass = float(round(dbc.max_internal * (dbc.min_pass_pct / Decimal("100.0")), 2))
                ea_min_pass = float(round(dbc.max_external * (dbc.min_pass_pct / Decimal("100.0")), 2))

                subs = []
                if sem_c and sem_c.components:
                    for comp in sem_c.components:
                        if comp.sub_components:
                            subs = [
                                {
                                    "name": sub.name,
                                    "code": sub.code,
                                    "max_marks": sub.max_marks,
                                    "min_pass_marks": sub.min_pass_marks,
                                }
                                for sub in comp.sub_components
                            ]

                inc_rules["courses"].append({
                    "sl_no": idx,
                    "course_code": dbc.course_code,
                    "title": dbc.course_title,
                    "credits": float(dbc.credits),
                    "credit_breakdown": f"{dbc.credits} Cr {'(Theory)' if dbc.is_theory else '(Practical)' if dbc.is_practical else ''}".strip(),
                    "passing_threshold_percent": float(dbc.min_pass_pct),
                    "is_english_or_elective": not dbc.include_in_sgpa,
                    "include_in_sgpa": dbc.include_in_sgpa,
                    "is_college_exam": dbc.is_college_exam,
                    "ia_max": float(dbc.max_internal),
                    "ia_min_pass": ia_min_pass,
                    "ea_max": float(dbc.max_external),
                    "ea_min_pass": ea_min_pass,
                    "total_max": float(dbc.max_total),
                    "subcomponents": subs,
                    "footnotes": sem_c.footnotes if sem_c else None,
                })
        elif sem_def:
            for c in sem_def.courses:
                first_comp = c.components[0] if c.components else None
                subs = []
                if first_comp and first_comp.sub_components:
                    subs = [
                        {
                            "name": sub.name,
                            "code": sub.code,
                            "max_marks": sub.max_marks,
                            "min_pass_marks": sub.min_pass_marks,
                        }
                        for sub in first_comp.sub_components
                    ]

                inc_rules["courses"].append({
                    "sl_no": c.sl_no,
                    "course_code": c.course_code,
                    "title": c.title,
                    "credits": c.credits,
                    "credit_breakdown": c.credit_breakdown,
                    "passing_threshold_percent": c.passing_threshold_percent,
                    "is_english_or_elective": c.is_english_or_elective,
                    "include_in_sgpa": c.include_in_sgpa,
                    "is_college_exam": c.course_type == CourseType.COLLEGE_EXAM,
                    "ia_max": first_comp.ia_max if first_comp else 25.0,
                    "ia_min_pass": first_comp.ia_min_pass if first_comp else 12.5,
                    "ea_max": first_comp.ea_max if first_comp else 75.0,
                    "ea_min_pass": first_comp.ea_min_pass if first_comp else 37.5,
                    "total_max": first_comp.total_max if first_comp else 100.0,
                    "subcomponents": subs,
                    "footnotes": c.footnotes,
                })

        q = (
            session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(StudentSemesterRegistration.semester_number == semester)
        )

        if exam_month_year and exam_month_year.strip() and exam_month_year.strip().lower() != "all sessions":
            clean_session = exam_month_year.strip()
            q = q.filter(StudentSemesterRegistration.exam_month_year.ilike(f"%{clean_session}%"))

        registrations = q.order_by(Student.roll_no).all()

        students_roster = []
        datasheet_rows = []

        for idx, (reg, stu) in enumerate(registrations, start=1):
            # Fetch latest verification record if any
            latest_verif = (
                session.query(ScrutinyVerification)
                .filter_by(registration_id=reg.id)
                .order_by(desc(ScrutinyVerification.iteration_number))
                .first()
            )

            # Fetch course marks
            marks = (
                session.query(StudentCourseMark, Course)
                .join(Course, StudentCourseMark.course_id == Course.id)
                .filter(StudentCourseMark.registration_id == reg.id)
                .order_by(Course.id)
                .all()
            )

            courses_map = {}
            for m, c in marks:
                mark_entry = {
                    "course_id": c.id,
                    "course_code": c.course_code,
                    "course_title": c.course_title,
                    "internal": float(m.internal_obtained),
                    "external_a": float(m.external_part_a) if m.external_part_a is not None else None,
                    "external_b": float(m.external_part_b) if m.external_part_b is not None else None,
                    "external_c": float(m.external_part_c) if m.external_part_c is not None else None,
                    "external": float(m.external_obtained),
                    "total": float(m.total_obtained),
                    "grade": m.letter_grade,
                    "gp": m.grade_point,
                    "result": m.course_result,
                    "is_exempted": m.is_exempted,
                }
                courses_map[c.course_code] = mark_entry
                # Fallback base code alias without (T)/(P) suffix
                base_code = c.course_code.replace(" (T)", "").replace(" (P)", "").strip()
                if base_code not in courses_map:
                    courses_map[base_code] = mark_entry

            students_roster.append({
                "student_id": stu.id,
                "registration_id": reg.id,
                "roll_no": stu.roll_no,
                "enrollment_no": stu.enrollment_no,
                "student_name": stu.student_name,
                "father_name": stu.father_name,
                "semester_number": reg.semester_number,
                "exam_month_year": reg.exam_month_year,
                "grand_total_obtained": float(reg.grand_total_obtained or 0),
                "grand_total_max": float(reg.grand_total_max or 0),
                "percentage": float(reg.percentage or 0),
                "sgpa": float(reg.sgpa) if reg.sgpa is not None else None,
                "result_status": reg.result_status,
                "scrutiny_status": reg.scrutiny_status or "PENDING",
                "last_scrutinized_at": reg.last_scrutinized_at.isoformat() if reg.last_scrutinized_at else None,
                "latest_verification": {
                    "id": latest_verif.id,
                    "status": latest_verif.verification_status,
                    "comments": latest_verif.comments,
                    "highlighted_fields": latest_verif.highlighted_fields,
                    "suggested_changes": latest_verif.suggested_changes,
                    "iteration_number": latest_verif.iteration_number,
                    "verified_at": latest_verif.verified_at.isoformat() if latest_verif.verified_at else None,
                    "is_actioned_by_admin": latest_verif.is_actioned_by_admin,
                } if latest_verif else None,
            })

            datasheet_rows.append({
                "sl_no": idx,
                "registration_id": reg.id,
                "student_id": stu.id,
                "roll_no": stu.roll_no,
                "enrollment_no": stu.enrollment_no,
                "student_name": stu.student_name,
                "father_name": stu.father_name,
                "courses": courses_map,
                "grand_total": float(reg.grand_total_obtained or 0),
                "percentage": float(reg.percentage or 0),
                "sgpa": float(reg.sgpa) if reg.sgpa is not None else None,
                "result_status": reg.result_status,
                "scrutiny_status": reg.scrutiny_status or "PENDING",
            })

        return {
            "status": "success",
            "semester": semester,
            "exam_month_year": exam_month_year,
            "total_students": len(students_roster),
            "inc_rules": inc_rules,
            "students": students_roster,
            "datasheet_rows": datasheet_rows,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.post("/verify-student")
def verify_student_marksheet(
    payload: StudentVerificationPayload,
    current_user: Any = Depends(require_scrutiny),
):
    """
    Submits a scrutiny verification record for an individual student marksheet.
    Supports iterative revisions (iteration_number 1, 2, ...), comments,
    interactive field highlights, and proposed score corrections.
    Updates student_semester_registrations.scrutiny_status to 'VERIFIED' or 'FLAGGED'.
    """
    status_val = payload.verification_status.strip().upper()
    if status_val not in ("VERIFIED_CORRECT", "NEEDS_CORRECTION"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="verification_status must be either 'VERIFIED_CORRECT' or 'NEEDS_CORRECTION'.",
        )

    with get_sync_session() as session:
        reg = (
            session.query(StudentSemesterRegistration)
            .filter_by(id=payload.registration_id)
            .first()
        )
        if not reg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registration #{payload.registration_id} not found.",
            )

        # Compute next iteration number
        current_max_iter = (
            session.query(func.coalesce(func.max(ScrutinyVerification.iteration_number), 0))
            .filter(ScrutinyVerification.registration_id == payload.registration_id)
            .scalar()
            or 0
        )
        next_iter = int(current_max_iter) + 1

        new_verification = ScrutinyVerification(
            registration_id=payload.registration_id,
            student_id=payload.student_id,
            semester_number=payload.semester_number,
            scrutiny_user_id=getattr(current_user, "id", None),
            scrutiny_username=current_user.username,
            verification_status=status_val,
            comments=payload.comments.strip() if payload.comments else None,
            highlighted_fields=payload.highlighted_fields or [],
            suggested_changes=payload.suggested_changes or {},
            iteration_number=next_iter,
            verified_at=datetime.now(timezone.utc),
            is_actioned_by_admin=False,
            actioned_by_admin_username=None,
            actioned_at=None,
        )
        session.add(new_verification)

        # Update registration scrutiny status
        new_reg_status = "VERIFIED" if status_val == "VERIFIED_CORRECT" else "FLAGGED"
        reg.scrutiny_status = new_reg_status
        reg.last_scrutinized_at = datetime.now(timezone.utc)

        if status_val == "VERIFIED_CORRECT":
            reg.is_verified = True
            reg.verified_at = datetime.now(timezone.utc)
            reg.verified_by = current_user.username
            reg.workflow_status = "SCRUTINIZED"

        session.commit()
        session.refresh(new_verification)

        return {
            "status": "success",
            "message": (
                f"Student marksheet successfully verified as '{new_reg_status}' (Iteration #{next_iter})."
            ),
            "verification_id": new_verification.id,
            "iteration_number": next_iter,
            "scrutiny_status": new_reg_status,
            "verified_at": new_verification.verified_at.isoformat() if new_verification.verified_at else None,
            "scrutiny_officer": current_user.username,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.get("/pending-remediations")
def get_pending_remediations(
    current_user: Any = Depends(require_subdean),
):
    """
    Returns all active suggestions where is_actioned_by_admin == FALSE and
    verification_status == 'NEEDS_CORRECTION', ordered by submission date descending.
    Protected: Accessible by Administrator and Sub-Dean roles.
    """
    with get_sync_session() as session:
        records = (
            session.query(ScrutinyVerification, Student, StudentSemesterRegistration)
            .join(Student, ScrutinyVerification.student_id == Student.id)
            .join(
                StudentSemesterRegistration,
                ScrutinyVerification.registration_id == StudentSemesterRegistration.id,
            )
            .filter(ScrutinyVerification.is_actioned_by_admin == False)
            .filter(ScrutinyVerification.verification_status == "NEEDS_CORRECTION")
            .order_by(desc(ScrutinyVerification.verified_at))
            .all()
        )

        results = []
        for verif, stu, reg in records:
            results.append({
                "verification_id": verif.id,
                "registration_id": reg.id,
                "student_id": stu.id,
                "roll_no": stu.roll_no,
                "enrollment_no": stu.enrollment_no,
                "student_name": stu.student_name,
                "semester_number": verif.semester_number,
                "exam_session": reg.exam_month_year,
                "scrutiny_username": verif.scrutiny_username,
                "iteration_number": verif.iteration_number,
                "comments": verif.comments,
                "highlighted_fields": verif.highlighted_fields,
                "suggested_changes": verif.suggested_changes,
                "verified_at": verif.verified_at.isoformat() if verif.verified_at else None,
                "current_sgpa": float(reg.sgpa) if reg.sgpa is not None else None,
                "current_total": float(reg.grand_total_obtained or 0),
            })

        return {
            "status": "success",
            "count": len(results),
            "remediations": results,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.post("/apply-remediation/{verification_id}")
def apply_scrutiny_remediation(
    verification_id: int,
    current_user: Any = Depends(require_admin),
):
    """
    Administrator-exclusive endpoint:
    Applies the Scrutiny Officer's proposed corrections directly into student_course_marks,
    recalculates course grades, GP, grand totals, percentage, and SGPA, logs an audit entry,
    and marks the verification record as actioned.
    """
    with get_sync_session() as session:
        verif = session.query(ScrutinyVerification).filter_by(id=verification_id).first()
        if not verif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scrutiny verification #{verification_id} not found.",
            )

        if verif.is_actioned_by_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Verification #{verification_id} has already been actioned by {verif.actioned_by_admin_username}.",
            )

        reg = (
            session.query(StudentSemesterRegistration)
            .filter_by(id=verif.registration_id)
            .first()
        )
        if not reg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registration #{verif.registration_id} not found.",
            )

        stu = session.query(Student).filter_by(id=verif.student_id).first()
        suggested = verif.suggested_changes or {}

        # Normalize suggested changes dictionary:
        # Format A: {"PHAR 205": {"field": "external_part_b", "suggested_val": 25, "reason": "..."}}
        # Format B: {"course_code": "PHAR 205", "field": "external_part_b", "suggested_val": 25}
        applied_items = []

        # If dictionary has top-level course keys:
        for key, val in suggested.items():
            if isinstance(val, dict):
                course_search = key
                field_name = val.get("field")
                new_val = val.get("suggested_val")
                reason = val.get("reason", "Scrutiny recommendation")
            else:
                course_search = suggested.get("course_code") or key
                field_name = suggested.get("field")
                new_val = suggested.get("suggested_val")
                reason = suggested.get("reason", "Scrutiny recommendation")

            if not field_name or new_val is None:
                continue

            # Find matching course in registration
            course_mark_row = (
                session.query(StudentCourseMark, Course)
                .join(Course, StudentCourseMark.course_id == Course.id)
                .filter(StudentCourseMark.registration_id == reg.id)
                .filter(Course.course_code.ilike(f"%{course_search.strip()}%"))
                .first()
            )

            if not course_mark_row:
                # Try title search
                course_mark_row = (
                    session.query(StudentCourseMark, Course)
                    .join(Course, StudentCourseMark.course_id == Course.id)
                    .filter(StudentCourseMark.registration_id == reg.id)
                    .filter(Course.course_title.ilike(f"%{course_search.strip()}%"))
                    .first()
                )

            if not course_mark_row:
                continue

            c_mark, c_def = course_mark_row
            num_val = Decimal(str(new_val))

            # Update targeted component mark
            if field_name == "internal_obtained" or field_name == "internal":
                c_mark.internal_obtained = num_val
            elif field_name == "external_part_a":
                c_mark.external_part_a = num_val
            elif field_name == "external_part_b":
                c_mark.external_part_b = num_val
            elif field_name == "external_part_c":
                c_mark.external_part_c = num_val
            elif field_name == "external_obtained" or field_name == "external":
                c_mark.external_obtained = num_val

            # If subcomponents exist, aggregate external_obtained
            has_subcomponents = (
                c_mark.external_part_a is not None or c_mark.external_part_b is not None or c_mark.external_part_c is not None
            )
            if has_subcomponents and field_name != "external_obtained":
                part_a = c_mark.external_part_a or Decimal("0.00")
                part_b = c_mark.external_part_b or Decimal("0.00")
                part_c = c_mark.external_part_c or Decimal("0.00")
                c_mark.external_obtained = part_a + part_b + part_c

            # Total obtained
            c_mark.total_obtained = c_mark.internal_obtained + c_mark.external_obtained + c_mark.grace_awarded
            c_pct = (
                round((c_mark.total_obtained / c_def.max_total) * Decimal("100.00"), 2)
                if c_def.max_total > Decimal("0.00")
                else Decimal("0.00")
            )
            c_mark.percentage = c_pct

            # Calculate grade and GP
            is_eng_el = not c_def.include_in_sgpa
            grade_res = calculate_inc_grade(
                obtained_marks=float(c_mark.total_obtained),
                max_marks=float(c_def.max_total),
                is_english_or_elective=is_eng_el,
            )
            c_mark.letter_grade = grade_res.letter_grade
            c_mark.grade_point = grade_res.grade_point
            c_mark.course_result = "PASS" if grade_res.is_pass else "FAIL"

            applied_items.append({
                "course_code": c_def.course_code,
                "field": field_name,
                "new_val": float(num_val),
                "new_total": float(c_mark.total_obtained),
                "letter_grade": c_mark.letter_grade,
                "grade_point": c_mark.grade_point,
            })

        # Recalculate Registration Totals & SGPA
        all_marks = (
            session.query(StudentCourseMark, Course)
            .join(Course, StudentCourseMark.course_id == Course.id)
            .filter(StudentCourseMark.registration_id == reg.id)
            .all()
        )

        grand_total = Decimal("0.00")
        grand_max = Decimal("0.00")
        total_credit_points = Decimal("0.00")
        sgpa_divisor_credits = Decimal("0.00")
        has_failure = False
        failed_course_names = []

        for m, c in all_marks:
            grand_total += m.total_obtained
            grand_max += c.max_total
            if c.include_in_sgpa:
                sgpa_divisor_credits += c.credits
                total_credit_points += (c.credits * Decimal(str(m.grade_point)))

            if m.course_result != "PASS":
                has_failure = True
                failed_course_names.append(c.course_title)

        calculated_sgpa = (
            round(total_credit_points / sgpa_divisor_credits, 2)
            if sgpa_divisor_credits > Decimal("0.00")
            else Decimal("0.00")
        )
        overall_pct = (
            round((grand_total / grand_max) * Decimal("100.00"), 2)
            if grand_max > Decimal("0.00")
            else Decimal("0.00")
        )

        reg.grand_total_obtained = grand_total
        reg.grand_total_max = grand_max
        reg.percentage = overall_pct
        reg.credit_score = total_credit_points
        reg.sgpa = calculated_sgpa
        reg.sgpa_credits = sgpa_divisor_credits

        if has_failure:
            reg.result_status = f"FAIL in {', '.join(failed_course_names)}"
            reg.grading_performance = f"SGPA {calculated_sgpa}"
        else:
            reg.result_status = "PASS"
            reg.grading_performance = f"SGPA {calculated_sgpa}"

        reg.scrutiny_status = "VERIFIED"
        reg.is_verified = True
        reg.verified_at = datetime.now(timezone.utc)
        reg.verified_by = current_user.username

        # Mark verification as actioned
        verif.is_actioned_by_admin = True
        verif.actioned_at = datetime.now(timezone.utc)
        verif.actioned_by_admin_username = current_user.username

        # Audit Log Entry
        audit = MarksAuditLog(
            entity_type="scrutiny_remediation",
            entity_id=verif.id,
            student_roll_no=stu.roll_no if stu else None,
            semester_number=verif.semester_number,
            field_name="apply_remediation",
            old_value=None,
            new_value=str(applied_items),
            change_reason=(
                f"Applied Scrutiny Suggestion #{verif.id} (Iter #{verif.iteration_number}) "
                f"submitted by {verif.scrutiny_username}"
            ),
            modified_by=current_user.username,
        )
        session.add(audit)

        # Update Longitudinal Cumulative Academic Summary
        repo = ExaminationRepository(session)
        if stu:
            repo.recalculate_cumulative_summary(student_id=stu.id)

        session.commit()

        return {
            "status": "success",
            "message": f"Scrutiny remediation #{verification_id} successfully applied and recalculated.",
            "verification_id": verification_id,
            "applied_changes": applied_items,
            "updated_registration": {
                "grand_total": float(reg.grand_total_obtained),
                "percentage": float(reg.percentage),
                "sgpa": float(reg.sgpa),
                "result_status": reg.result_status,
                "scrutiny_status": reg.scrutiny_status,
            },
            "updated_courses": applied_items,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.post("/dismiss-remediation/{verification_id}")
def dismiss_scrutiny_remediation(
    verification_id: int,
    payload: DismissRemediationPayload,
    current_user: Any = Depends(require_admin),
):
    """
    Administrator-exclusive endpoint:
    Dismisses a scrutiny suggestion without modifying marks.
    Records admin notes and marks the item as actioned.
    """
    with get_sync_session() as session:
        verif = session.query(ScrutinyVerification).filter_by(id=verification_id).first()
        if not verif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scrutiny verification #{verification_id} not found.",
            )

        verif.is_actioned_by_admin = True
        verif.actioned_at = datetime.now(timezone.utc)
        verif.actioned_by_admin_username = current_user.username
        if payload.admin_notes:
            verif.comments = (
                f"{verif.comments} | [Admin Note: {payload.admin_notes}]"
                if verif.comments
                else f"[Admin Note: {payload.admin_notes}]"
            )

        # Update registration scrutiny status back to VERIFIED
        reg = (
            session.query(StudentSemesterRegistration)
            .filter_by(id=verif.registration_id)
            .first()
        )
        if reg:
            reg.scrutiny_status = "VERIFIED"

        stu = session.query(Student).filter_by(id=verif.student_id).first()

        # Audit Log Entry
        audit = MarksAuditLog(
            entity_type="scrutiny_remediation",
            entity_id=verif.id,
            student_roll_no=stu.roll_no if stu else None,
            semester_number=verif.semester_number,
            field_name="dismiss_remediation",
            old_value=None,
            new_value=payload.admin_notes,
            change_reason=f"Dismissed Scrutiny Suggestion #{verif.id}: {payload.admin_notes}",
            modified_by=current_user.username,
        )
        session.add(audit)
        session.commit()

        return {
            "status": "success",
            "message": f"Scrutiny suggestion #{verification_id} dismissed with admin notes recorded.",
            "verification_id": verification_id,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }
