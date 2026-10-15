"""
Repository and Data Access Engine for VidyaMarksheet Examination Database.
Compliant with Indian Nursing Council (INC) Gazette Regulations (Gazette No. 205, April 2022)
and SGPGIMS Lucknow Regulations (College Code: 1313).
VidyaLabs Copyright © 2026.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func, select, and_, or_, desc, asc, Integer, case, cast
from sqlalchemy.orm import Session

from backend.db.models import (
    Batch,
    Student,
    Course,
    StudentSemesterRegistration,
    StudentCourseMark,
    CumulativeAcademicSummary,
    MarksAuditLog,
)
from backend.grading import calculate_inc_grade


class ExaminationRepository:
    """Repository handling ACID transactions, audit logging, and queries for examination persistence."""

    def __init__(self, session: Session):
        self.session = session

    # -------------------------------------------------------------------------
    # Batch & Demographics Operations
    # -------------------------------------------------------------------------

    def get_or_create_batch(
        self,
        batch_name: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        total_credits: int = 151
    ) -> Batch:
        """Finds or creates a student cohort batch."""
        clean_name = batch_name.strip()
        batch = self.session.query(Batch).filter_by(batch_name=clean_name).first()
        if not batch:
            batch = Batch(
                batch_name=clean_name,
                start_year=start_year,
                end_year=end_year,
                total_prescribed_credits=total_credits,
            )
            self.session.add(batch)
            self.session.flush()
        return batch

    def upsert_student(
        self,
        batch_id: int,
        roll_no: str,
        enrollment_no: str,
        student_name: str,
        father_name: str,
        institutional_status: str = "REGULAR",
        modified_by: str = "SYSTEM_ETL"
    ) -> Student:
        """
        Inserts or updates a student record.
        Logs any demographic alterations to marks_audit_log.
        """
        roll_clean = str(roll_no).strip()
        enroll_clean = str(enrollment_no).strip()
        name_clean = str(student_name).strip()
        father_clean = str(father_name).strip()

        # A student can be identified by roll number or institutional enrollment number
        student = (
            self.session.query(Student)
            .filter(or_(Student.roll_no == roll_clean, Student.enrollment_no == enroll_clean))
            .first()
        )
        if not student:
            student = Student(
                batch_id=batch_id,
                roll_no=roll_clean,
                enrollment_no=enroll_clean,
                student_name=name_clean,
                father_name=father_clean,
                institutional_status=institutional_status,
                is_active=True,
            )
            self.session.add(student)
            self.session.flush()

            # Log creation in audit trail
            audit = MarksAuditLog(
                entity_type="student",
                entity_id=student.id,
                student_roll_no=roll_clean,
                field_name="student_created",
                old_value=None,
                new_value=f"Created student {name_clean} (Enroll: {enroll_clean})",
                change_reason="Initial student record creation",
                modified_by=modified_by,
            )
            self.session.add(audit)
        else:
            # Check for demographic updates and log
            changes = []
            if student.student_name != name_clean:
                changes.append(("student_name", student.student_name, name_clean))
                student.student_name = name_clean
            if student.father_name != father_clean:
                changes.append(("father_name", student.father_name, father_clean))
                student.father_name = father_clean
            if student.enrollment_no != enroll_clean:
                changes.append(("enrollment_no", student.enrollment_no, enroll_clean))
                student.enrollment_no = enroll_clean
            if student.batch_id != batch_id:
                changes.append(("batch_id", str(student.batch_id), str(batch_id)))
                student.batch_id = batch_id
            if student.roll_no != roll_clean:
                existing_with_roll = self.session.query(Student).filter_by(roll_no=roll_clean).first()
                if not existing_with_roll:
                    changes.append(("roll_no", student.roll_no, roll_clean))
                    student.roll_no = roll_clean

            for field, old_val, new_val in changes:
                audit = MarksAuditLog(
                    entity_type="student",
                    entity_id=student.id,
                    student_roll_no=roll_clean,
                    field_name=field,
                    old_value=str(old_val),
                    new_value=str(new_val),
                    change_reason="Demographics synchronization",
                    modified_by=modified_by,
                )
                self.session.add(audit)
            self.session.flush()

        return student

    # -------------------------------------------------------------------------
    # Course Catalog Operations
    # -------------------------------------------------------------------------

    def get_course_by_code(self, semester_number: int, course_code: str) -> Optional[Course]:
        """Resolves course by exact code, fuzzy code, or canonical acronym for a semester."""
        code_clean = course_code.strip()
        course = (
            self.session.query(Course)
            .filter(
                Course.semester_number == semester_number,
                Course.course_code == code_clean,
            )
            .first()
        )
        if not course:
            # Fuzzy match (e.g., handles '(T)', '(P)' prefixes or slight space differences)
            course = (
                self.session.query(Course)
                .filter(
                    Course.semester_number == semester_number,
                    Course.course_code.ilike(f"%{code_clean}%"),
                )
                .first()
            )
        if not course:
            # Canonical token matching
            upper = code_clean.upper()
            sem_courses = self.get_semester_courses(semester_number)
            for sc in sem_courses:
                sc_up = sc.course_code.upper()
                sc_title_up = sc.course_title.upper()
                if "ENGL" in upper and "ENGL" in sc_up:
                    return sc
                if ("ANAT" in upper or "PHYS" in upper) and ("ANAT" in sc_up or "PHYS" in sc_up):
                    return sc
                if ("SOCI" in upper or "PSYC" in upper) and ("SOCI" in sc_up or "PSYC" in sc_up):
                    return sc
                if ("BIOC" in upper or "NUTR" in upper) and ("BIOC" in sc_up or "NUTR" in sc_up):
                    return sc
                if ("HNIT" in upper or "INFORMATICS" in upper) and ("HNIT" in sc_up or "INFORMATICS" in sc_title_up):
                    return sc
                if "NNF" in upper or "FOUNDATION" in upper or "N-NF" in upper:
                    is_pract = "PRACT" in upper or "(P)" in upper or "_P" in upper
                    sc_pract = "(P)" in sc_up or "PRACT" in sc_title_up
                    if is_pract == sc_pract:
                        return sc
                # Semester 3
                if "MICR" in upper and "MICR" in sc_up:
                    return sc
                if "AHN" in upper and "AHN" in sc_up and semester_number == 3:
                    is_pract = "PRACT" in upper or "(P)" in upper or "_P" in upper
                    sc_pract = "(P)" in sc_up or "PRACT" in sc_title_up
                    if is_pract == sc_pract:
                        return sc
                # Semester 4
                if ("PHAR" in upper or "PATH" in upper or "GEN" in upper) and ("PHAR" in sc_up or "PATH" in sc_up):
                    return sc
                if "AHN" in upper and "AHN" in sc_up and semester_number == 4:
                    is_pract = "PRACT" in upper or "(P)" in upper or "_P" in upper
                    sc_pract = "(P)" in sc_up or "PRACT" in sc_title_up
                    if is_pract == sc_pract:
                        return sc
                if "PROF" in upper and "PROF" in sc_up:
                    return sc
                # Semester 5
                if "COMH" in upper and "COMH" in sc_up and semester_number == 5:
                    is_pract = "PRACT" in upper or "(P)" in upper or "_P" in upper
                    sc_pract = "(P)" in sc_up or "PRACT" in sc_title_up
                    if is_pract == sc_pract:
                        return sc
                if "EDUC" in upper and "EDUC" in sc_up:
                    return sc
                if "FORN" in upper and "FORN" in sc_up:
                    return sc
                # Semester 6
                if "CHN" in upper and "CHN" in sc_up:
                    is_pract = "PRACT" in upper or "(P)" in upper or "_P" in upper
                    sc_pract = "(P)" in sc_up or "PRACT" in sc_title_up
                    if is_pract == sc_pract:
                        return sc
                if "MHN" in upper and "MHN" in sc_up:
                    is_pract = "PRACT" in upper or "(P)" in upper or "_P" in upper
                    sc_pract = "(P)" in sc_up or "PRACT" in sc_title_up
                    if is_pract == sc_pract:
                        return sc
                if "NMLE" in upper and "NMLE" in sc_up:
                    return sc
        return course

    def get_semester_courses(self, semester_number: int) -> List[Course]:
        """Returns all prescribed courses for a given semester."""
        return (
            self.session.query(Course)
            .filter_by(semester_number=semester_number)
            .order_by(Course.id)
            .all()
        )

    # -------------------------------------------------------------------------
    # Registration & Marks Upsert Operations
    # -------------------------------------------------------------------------

    def upsert_registration(
        self,
        student_id: int,
        semester_number: int,
        exam_month_year: str,
        exam_type: str = "MAIN",
        attempt_number: int = 0,
        attempt_label: str = "MAIN",
        total_credits: Optional[float] = None,
        sgpa_credits: Optional[float] = None,
        grand_total_obtained: Optional[float] = None,
        grand_total_max: Optional[float] = None,
        percentage: Optional[float] = None,
        credit_score: Optional[float] = None,
        sgpa: Optional[float] = None,
        result_status: Optional[str] = None,
        result_remarks: Optional[str] = None,
        grading_performance: Optional[str] = None,
        allow_locked_edit: bool = False,
        modified_by: str = "SYSTEM_ETL"
    ) -> StudentSemesterRegistration:
        """Upserts a semester examination registration for a student."""
        reg = (
            self.session.query(StudentSemesterRegistration)
            .filter_by(
                student_id=student_id,
                semester_number=semester_number,
                exam_type=exam_type,
            )
            .first()
        )

        to_dec = lambda x: Decimal(str(round(x, 2))) if x is not None else None

        if not reg:
            reg = StudentSemesterRegistration(
                student_id=student_id,
                semester_number=semester_number,
                exam_month_year=exam_month_year.strip(),
                exam_type=exam_type,
                attempt_number=attempt_number,
                attempt_label=attempt_label,
                total_credits_registered=to_dec(total_credits),
                sgpa_credits=to_dec(sgpa_credits),
                grand_total_obtained=to_dec(grand_total_obtained),
                grand_total_max=to_dec(grand_total_max),
                percentage=to_dec(percentage),
                credit_score=to_dec(credit_score),
                sgpa=to_dec(sgpa),
                result_status=result_status,
                result_remarks=result_remarks,
                grading_performance=grading_performance,
                workflow_status="DRAFT",
            )
            self.session.add(reg)
            self.session.flush()
        else:
            if (reg.workflow_status or "").upper() == "LOCKED" and not allow_locked_edit:
                raise PermissionError(
                    f"Registration for student ID {student_id} (Semester {semester_number}) is LOCKED. "
                    "An Administrator must issue an 'Unlock for Re-evaluation' override with a mandatory justification comment."
                )

            reg.exam_month_year = exam_month_year.strip()
            reg.attempt_number = attempt_number
            reg.attempt_label = attempt_label
            if total_credits is not None:
                reg.total_credits_registered = to_dec(total_credits)
            if sgpa_credits is not None:
                reg.sgpa_credits = to_dec(sgpa_credits)
            if grand_total_obtained is not None:
                reg.grand_total_obtained = to_dec(grand_total_obtained)
            if grand_total_max is not None:
                reg.grand_total_max = to_dec(grand_total_max)
            if percentage is not None:
                reg.percentage = to_dec(percentage)
            if credit_score is not None:
                reg.credit_score = to_dec(credit_score)
            if sgpa is not None:
                reg.sgpa = to_dec(sgpa)
            if result_status is not None:
                reg.result_status = result_status
            if result_remarks is not None:
                reg.result_remarks = result_remarks
            if grading_performance is not None:
                reg.grading_performance = grading_performance
            self.session.flush()

        return reg

    def upsert_course_mark(
        self,
        registration_id: int,
        course_id: int,
        internal_obtained: float,
        external_obtained: float,
        total_obtained: float,
        percentage: float,
        letter_grade: str,
        grade_point: int,
        course_result: str,
        grace_awarded: float = 0.0,
        external_part_a: Optional[float] = None,
        external_part_b: Optional[float] = None,
        external_part_c: Optional[float] = None,
        is_exempted: bool = False,
        original_exam_month_year: Optional[str] = None,
        student_roll_no: Optional[str] = None,
        modified_by: str = "SYSTEM_ETL"
    ) -> StudentCourseMark:
        """
        Upserts a course mark entry for a registration.
        Logs any grade or mark changes to marks_audit_log.
        """
        mark = (
            self.session.query(StudentCourseMark)
            .filter_by(registration_id=registration_id, course_id=course_id)
            .first()
        )

        to_dec = lambda x: Decimal(str(round(x, 2))) if x is not None else Decimal("0.00")

        int_dec = to_dec(internal_obtained)
        ext_dec = to_dec(external_obtained)
        tot_dec = to_dec(total_obtained)
        pct_dec = to_dec(percentage)
        grc_dec = to_dec(grace_awarded)
        part_a_dec = Decimal(str(round(external_part_a, 2))) if external_part_a is not None else None
        part_b_dec = Decimal(str(round(external_part_b, 2))) if external_part_b is not None else None
        part_c_dec = Decimal(str(round(external_part_c, 2))) if external_part_c is not None else None

        if not mark:
            mark = StudentCourseMark(
                registration_id=registration_id,
                course_id=course_id,
                internal_obtained=int_dec,
                external_part_a=part_a_dec,
                external_part_b=part_b_dec,
                external_part_c=part_c_dec,
                external_obtained=ext_dec,
                grace_awarded=grc_dec,
                total_obtained=tot_dec,
                percentage=pct_dec,
                letter_grade=letter_grade,
                grade_point=grade_point,
                course_result=course_result,
                is_exempted=is_exempted,
                original_exam_month_year=original_exam_month_year,
            )
            self.session.add(mark)
            self.session.flush()
        else:
            # Track differences for audit log
            if mark.total_obtained != tot_dec or mark.letter_grade != letter_grade:
                audit = MarksAuditLog(
                    entity_type="student_course_marks",
                    entity_id=mark.id,
                    student_roll_no=student_roll_no,
                    field_name=f"course_id_{course_id}_marks",
                    old_value=f"Tot:{mark.total_obtained}, Grd:{mark.letter_grade}, Grc:{mark.grace_awarded}",
                    new_value=f"Tot:{tot_dec}, Grd:{letter_grade}, Grc:{grc_dec}",
                    change_reason="Datasheet ingestion / marks update",
                    modified_by=modified_by,
                )
                self.session.add(audit)

            mark.internal_obtained = int_dec
            mark.external_part_a = part_a_dec
            mark.external_part_b = part_b_dec
            mark.external_part_c = part_c_dec
            mark.external_obtained = ext_dec
            mark.grace_awarded = grc_dec
            mark.total_obtained = tot_dec
            mark.percentage = pct_dec
            mark.letter_grade = letter_grade
            mark.grade_point = grade_point
            mark.course_result = course_result
            mark.is_exempted = is_exempted
            if original_exam_month_year:
                mark.original_exam_month_year = original_exam_month_year
            self.session.flush()

        return mark

    def resolve_reappear_exemptions(
        self,
        student_id: int,
        semester_number: int,
        current_registration_id: int,
        attempt_label: str = "REAPPEAR - I",
        modified_by: str = "SYSTEM_REAPPEAR"
    ) -> Optional[StudentSemesterRegistration]:
        """
        Historical resolution for Reappear attempts:
        1. Checks previous registrations in this semester for student_id.
        2. Any course passed ('PASS') in an earlier session is carried forward as is_exempted=True,
           inheriting its Grade, Grade Point, Total Marks, and original_exam_month_year.
        3. Recalculates the Semester grand total, percentage, credit score, and SGPA
           using the combined set of cleared + exempted courses.
        4. Derives the Result status:
           - If all courses are now passed:
             'PASS (CLEARED IN {attempt_label})' (or with grace if grace was awarded)
           - If still failing:
             'FAIL in {failed_courses}'
        5. Updates the longitudinal cumulative academic summary.
        """
        curr_reg = (
            self.session.query(StudentSemesterRegistration)
            .filter_by(id=current_registration_id)
            .first()
        )
        if not curr_reg:
            return None

        # Find prior registrations for this student and semester
        prior_regs = (
            self.session.query(StudentSemesterRegistration)
            .filter(
                StudentSemesterRegistration.student_id == student_id,
                StudentSemesterRegistration.semester_number == semester_number,
                StudentSemesterRegistration.id != current_registration_id,
            )
            .order_by(desc(StudentSemesterRegistration.id))
            .all()
        )

        prior_reg_ids = [pr.id for pr in prior_regs]
        prior_passed_marks = {}
        if prior_reg_ids:
            p_marks = (
                self.session.query(StudentCourseMark, StudentSemesterRegistration.exam_month_year)
                .join(StudentSemesterRegistration, StudentCourseMark.registration_id == StudentSemesterRegistration.id)
                .filter(
                    StudentCourseMark.registration_id.in_(prior_reg_ids),
                    StudentCourseMark.course_result == "PASS",
                )
                .all()
            )
            for pm, exam_session in p_marks:
                if pm.course_id not in prior_passed_marks:
                    prior_passed_marks[pm.course_id] = (pm, exam_session)

        # Prescribed courses
        all_courses = self.get_semester_courses(semester_number)
        curr_marks = {
            m.course_id: m
            for m in self.session.query(StudentCourseMark).filter_by(registration_id=current_registration_id).all()
        }

        # Inherit previously passed subjects if not re-evaluated
        for c in all_courses:
            if c.id in prior_passed_marks and c.id not in curr_marks:
                pm, exam_session = prior_passed_marks[c.id]
                self.upsert_course_mark(
                    registration_id=current_registration_id,
                    course_id=c.id,
                    internal_obtained=float(pm.internal_obtained),
                    external_obtained=float(pm.external_obtained),
                    total_obtained=float(pm.total_obtained),
                    percentage=float(pm.percentage),
                    letter_grade=pm.letter_grade,
                    grade_point=pm.grade_point,
                    course_result="PASS",
                    grace_awarded=0.0,
                    is_exempted=True,
                    original_exam_month_year=exam_session,
                    modified_by=modified_by,
                )
            elif c.id in curr_marks and c.id in prior_passed_marks:
                cm = curr_marks[c.id]
                # If current mark indicates exemption or absent/zero while passed previously
                if cm.is_exempted or (cm.total_obtained == 0 and cm.course_result in ["Ab", "FAIL"]):
                    pm, exam_session = prior_passed_marks[c.id]
                    cm.internal_obtained = pm.internal_obtained
                    cm.external_obtained = pm.external_obtained
                    cm.total_obtained = pm.total_obtained
                    cm.percentage = pm.percentage
                    cm.letter_grade = pm.letter_grade
                    cm.grade_point = pm.grade_point
                    cm.course_result = "PASS"
                    cm.is_exempted = True
                    cm.original_exam_month_year = exam_session

        self.session.flush()

        # Re-fetch all marks for current registration
        updated_marks = (
            self.session.query(StudentCourseMark, Course)
            .join(Course, StudentCourseMark.course_id == Course.id)
            .filter(StudentCourseMark.registration_id == current_registration_id)
            .all()
        )

        grand_total = Decimal("0.00")
        grand_max = Decimal("0.00")
        total_credit_points = Decimal("0.00")
        sgpa_eligible_credits = Decimal("0.00")
        failed_courses = []
        any_grace_in_reappear = False
        grace_detail_str = ""

        for m, c in updated_marks:
            grand_total += m.total_obtained
            grand_max += c.max_total
            if c.include_in_sgpa:
                sgpa_eligible_credits += c.credits
                total_credit_points += (c.credits * Decimal(str(m.grade_point)))

            if m.course_result != "PASS":
                failed_courses.append(c.course_title)

            if not m.is_exempted and m.grace_awarded > 0:
                any_grace_in_reappear = True
                grace_detail_str = f"{m.grace_awarded} GRACE MARKS IN {c.course_title}"

        calculated_sgpa = round(total_credit_points / sgpa_eligible_credits, 2) if sgpa_eligible_credits > 0 else Decimal("0.00")
        overall_percentage = round((grand_total / grand_max) * Decimal("100.00"), 2) if grand_max > 0 else Decimal("0.00")

        if len(failed_courses) == 0:
            if any_grace_in_reappear:
                curr_reg.result_status = f"PASS WITH {grace_detail_str} ({attempt_label})"
            else:
                curr_reg.result_status = f"PASS (CLEARED IN {attempt_label})"
            curr_reg.result_remarks = f"Grading Performance - PASS (SGPA: {calculated_sgpa})"
        else:
            curr_reg.result_status = f"FAIL in {', '.join(failed_courses)}"
            curr_reg.result_remarks = "Grading Performance - Fail"

        curr_reg.grand_total_obtained = grand_total
        curr_reg.grand_total_max = grand_max
        curr_reg.percentage = overall_percentage
        curr_reg.credit_score = total_credit_points
        curr_reg.sgpa = calculated_sgpa
        curr_reg.sgpa_credits = sgpa_eligible_credits
        curr_reg.attempt_label = attempt_label
        curr_reg.exam_type = attempt_label

        self.session.flush()
        self.recalculate_cumulative_summary(student_id)
        return curr_reg

    def recalculate_cumulative_summary(self, student_id: int) -> CumulativeAcademicSummary:
        """
        Recalculates longitudinal 8-semester metrics and updates cumulative_academic_summary:
        - Picks the latest/cleared registration for each Semester (1 through 8)
        - Computes CGPA = Sum(SGPA * SGPA_Credits) / Sum(SGPA_Credits) [Target prescribed divisor: 151.0]
        - Derives overall percentage = CGPA * 10
        - Determines Final Letter Grade & Division Classification per INC Gazette.
        """
        summary = (
            self.session.query(CumulativeAcademicSummary)
            .filter_by(student_id=student_id)
            .first()
        )
        if not summary:
            summary = CumulativeAcademicSummary(student_id=student_id)
            self.session.add(summary)
            self.session.flush()

        # Query all registrations for this student ordered by semester, latest attempts first
        all_regs = (
            self.session.query(StudentSemesterRegistration)
            .filter_by(student_id=student_id)
            .order_by(
                StudentSemesterRegistration.semester_number,
                desc(StudentSemesterRegistration.attempt_number),
                desc(StudentSemesterRegistration.id),
            )
            .all()
        )

        # For each semester 1-8, pick the latest registration
        latest_regs = {}
        for r in all_regs:
            if r.semester_number not in latest_regs:
                latest_regs[r.semester_number] = r

        total_earned_credits = Decimal("0.0")
        total_credit_points = Decimal("0.0")
        has_any_fail = False

        # Reset semester columns
        for sem_idx in range(1, 9):
            setattr(summary, f"sem{sem_idx}_sgpa", None)
            setattr(summary, f"sem{sem_idx}_credits", None)

        for s_num in range(1, 9):
            if s_num in latest_regs:
                r = latest_regs[s_num]
                sgpa_val = Decimal(str(r.sgpa)) if r.sgpa is not None else Decimal("0.0")
                cr_val = Decimal(str(r.sgpa_credits)) if r.sgpa_credits is not None else Decimal("0.0")

                setattr(summary, f"sem{s_num}_sgpa", sgpa_val)
                setattr(summary, f"sem{s_num}_credits", cr_val)

                if cr_val > 0 and sgpa_val is not None:
                    total_credit_points += (sgpa_val * cr_val)
                    total_earned_credits += cr_val

                if r.result_status and "FAIL" in r.result_status.upper():
                    has_any_fail = True

        summary.cumulative_earned_credits = total_earned_credits
        summary.total_prescribed_credits = Decimal("151.0")

        # CGPA computation
        if total_earned_credits > Decimal("0.0"):
            calc_cgpa = round(total_credit_points / total_earned_credits, 2)
            summary.cgpa = calc_cgpa
            summary.final_percentage = round(calc_cgpa * Decimal("10.0"), 2)

            # Determine final letter grade
            pct_float = float(summary.final_percentage)
            inc_grade_info = calculate_inc_grade(pct_float, max_marks=100.0, is_english_or_elective=False)
            summary.final_letter_grade = inc_grade_info.letter_grade

            # Classification
            if pct_float >= 75.0:
                summary.division_classification = "FIRST DIVISION WITH DISTINCTION"
            elif pct_float >= 60.0:
                summary.division_classification = "FIRST DIVISION"
            elif pct_float >= 50.0:
                summary.division_classification = "SECOND DIVISION"
            else:
                summary.division_classification = "PASS CLASS"
        else:
            summary.cgpa = None
            summary.final_percentage = None
            summary.final_letter_grade = None
            summary.division_classification = None

        if has_any_fail:
            summary.overall_result = "FAILED"
        elif len(latest_regs) == 8 and not has_any_fail:
            summary.overall_result = "PASSED"
        else:
            summary.overall_result = "IN PROGRESS"

        self.session.flush()
        return summary

    # -------------------------------------------------------------------------
    # Retrieval Operations for Marksheet & Frontend Consumption
    # -------------------------------------------------------------------------

    def get_student_marksheet_data(self, semester_number: int, roll_no: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full student marksheet record formatted specifically for the React Marksheet
        components (Sem1Marksheet through Sem8Marksheet) and the PDF generator.
        """
        student = self.session.query(Student).filter_by(roll_no=roll_no.strip()).first()
        if not student:
            return None

        reg = (
            self.session.query(StudentSemesterRegistration)
            .filter_by(student_id=student.id, semester_number=semester_number)
            .order_by(desc(StudentSemesterRegistration.id))
            .first()
        )
        if not reg:
            return None

        # Fetch course marks with course metadata
        marks = (
            self.session.query(StudentCourseMark, Course)
            .join(Course, StudentCourseMark.course_id == Course.id)
            .filter(StudentCourseMark.registration_id == reg.id)
            .order_by(Course.id)
            .all()
        )

        courses_payload = []
        failed_courses = []

        for m, c in marks:
            sub_comps = []
            if m.external_part_a is not None and m.external_part_b is not None:
                sub_comps = [
                    {
                        "name": "Section A",
                        "obtained": float(m.external_part_a),
                        "max_marks": 37.0 if "ANAT" in c.course_code else 25.0,
                    },
                    {
                        "name": "Section B",
                        "obtained": float(m.external_part_b),
                        "max_marks": 38.0 if "PHYS" in c.course_code else 50.0,
                    },
                ]

            is_p = m.course_result == "PASS"
            if not is_p:
                failed_courses.append(c.course_title)

            is_ex = bool(m.is_exempted)
            courses_payload.append({
                "course_code": c.course_code,
                "course_title": c.course_title,
                "component_name": "Practical" if c.is_practical else ("College Exam" if c.is_college_exam else "Theory"),
                "credits": int(c.credits),
                "is_exempted": is_ex,
                "original_exam_month_year": m.original_exam_month_year,
                "internal_obtained": "Ex." if is_ex else float(m.internal_obtained),
                "internal_max": float(c.max_internal),
                "external_obtained": "Ex." if is_ex else float(m.external_obtained),
                "external_max": float(c.max_external),
                "sub_components": [] if is_ex else sub_comps,
                "total_obtained": float(m.total_obtained),
                "total_max": float(c.max_total),
                "percentage": float(m.percentage),
                "letter_grade": m.letter_grade,
                "grade_point": m.grade_point,
                "is_pass": is_p,
                "grace_marks": float(m.grace_awarded) if not is_ex else 0.0,
                "is_absent": m.course_result == "Ab",
                "is_english_or_elective": not c.include_in_sgpa,
                "include_in_sgpa": c.include_in_sgpa,
            })

        # Academic summary for longitudinal display (Sem 8 especially)
        summary = (
            self.session.query(CumulativeAcademicSummary)
            .filter_by(student_id=student.id)
            .first()
        )
        summary_payload = None
        if summary:
            summary_payload = {
                "sem1_sgpa": float(summary.sem1_sgpa) if summary.sem1_sgpa else None,
                "sem1_credits": float(summary.sem1_credits) if summary.sem1_credits else None,
                "sem2_sgpa": float(summary.sem2_sgpa) if summary.sem2_sgpa else None,
                "sem2_credits": float(summary.sem2_credits) if summary.sem2_credits else None,
                "sem3_sgpa": float(summary.sem3_sgpa) if summary.sem3_sgpa else None,
                "sem3_credits": float(summary.sem3_credits) if summary.sem3_credits else None,
                "sem4_sgpa": float(summary.sem4_sgpa) if summary.sem4_sgpa else None,
                "sem4_credits": float(summary.sem4_credits) if summary.sem4_credits else None,
                "sem5_sgpa": float(summary.sem5_sgpa) if summary.sem5_sgpa else None,
                "sem5_credits": float(summary.sem5_credits) if summary.sem5_credits else None,
                "sem6_sgpa": float(summary.sem6_sgpa) if summary.sem6_sgpa else None,
                "sem6_credits": float(summary.sem6_credits) if summary.sem6_credits else None,
                "sem7_sgpa": float(summary.sem7_sgpa) if summary.sem7_sgpa else None,
                "sem7_credits": float(summary.sem7_credits) if summary.sem7_credits else None,
                "sem8_sgpa": float(summary.sem8_sgpa) if summary.sem8_sgpa else None,
                "sem8_credits": float(summary.sem8_credits) if summary.sem8_credits else None,
                "cumulative_earned_credits": float(summary.cumulative_earned_credits),
                "total_prescribed_credits": float(summary.total_prescribed_credits),
                "cgpa": float(summary.cgpa) if summary.cgpa else None,
                "final_percentage": float(summary.final_percentage) if summary.final_percentage else None,
                "final_letter_grade": summary.final_letter_grade,
                "division_classification": summary.division_classification,
                "overall_result": summary.overall_result,
            }

        batch_name = student.batch.batch_name if student.batch else "Batch 2022-2026"
        attempt_label = reg.attempt_label or "MAIN"
        attempt_num = int(reg.attempt_number or 0)
        attempt_indicator = f"({attempt_label})" if attempt_label != "MAIN" else None

        return {
            "student": {
                "name": student.student_name,
                "father_name": student.father_name,
                "enrollment_no": student.enrollment_no,
                "roll_no": student.roll_no,
                "institutional_status": student.institutional_status,
                "batch_name": batch_name,
            },
            "semester_number": semester_number,
            "degree_title": "B.Sc. NURSING",
            "examination_session": reg.exam_month_year,
            "attempt_number": attempt_num,
            "attempt_label": attempt_label,
            "attempt_indicator": attempt_indicator,
            "college_name": "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.",
            "college_code": "1313",
            "courses": courses_payload,
            "grand_total_obtained": float(reg.grand_total_obtained or 0.0),
            "grand_total_max": float(reg.grand_total_max or 250.0),
            "overall_percentage": float(reg.percentage or 0.0),
            "sgpa": float(reg.sgpa or 0.0),
            "total_credit_score": float(reg.credit_score or 0.0),
            "total_sgpa_credits": int(reg.sgpa_credits or 0),
            "result_status": reg.result_status or "PASS",
            "failed_courses": failed_courses,
            "remarks": reg.result_remarks,
            "workflow_status": reg.workflow_status or "DRAFT",
            "workflow_updated_at": reg.workflow_updated_at.isoformat() if reg.workflow_updated_at else None,
            "workflow_updated_by": reg.workflow_updated_by,
            "workflow_remarks": reg.workflow_remarks,
            "is_locked": (reg.workflow_status or "").upper() == "LOCKED",
            "cumulative_summary": summary_payload,
        }

    def get_batch_marksheets(self, semester_number: int, batch_id: int) -> List[Dict[str, Any]]:
        """Returns all students' marksheets for a specific semester and cohort batch."""
        students = (
            self.session.query(Student)
            .filter_by(batch_id=batch_id, is_active=True)
            .order_by(Student.roll_no)
            .all()
        )
        results = []
        for s in students:
            m = self.get_student_marksheet_data(semester_number, s.roll_no)
            if m:
                results.append(m)
        return results

    # -------------------------------------------------------------------------
    # Analytics Aggregation Engine
    # -------------------------------------------------------------------------

    def get_semester_analytics(self, semester_number: int, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes native SQL aggregation to compute performance KPIs, pass rates,
        grade distribution, and subject-wise failure rates directly in PostgreSQL.
        """
        query = (
            self.session.query(StudentSemesterRegistration)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(StudentSemesterRegistration.semester_number == semester_number)
        )
        if batch_id:
            query = query.filter(Student.batch_id == batch_id)

        regs = query.all()
        total_students = len(regs)

        if total_students == 0:
            return {
                "semester_number": semester_number,
                "batch_id": batch_id,
                "total_students": 0,
                "passed_count": 0,
                "pass_with_grace_count": 0,
                "failed_count": 0,
                "pass_percentage": 0.0,
                "average_sgpa": 0.0,
                "highest_sgpa": 0.0,
                "lowest_sgpa": 0.0,
                "grade_distribution": {"O": 0, "A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "P": 0, "F": 0},
                "subject_performance": [],
            }

        passed_count = sum(1 for r in regs if r.result_status == "PASS")
        grace_count = sum(1 for r in regs if "GRACE" in (r.result_status or "").upper())
        failed_count = sum(1 for r in regs if "FAIL" in (r.result_status or "").upper())

        valid_sgpas = [float(r.sgpa) for r in regs if r.sgpa is not None and r.sgpa > 0]
        avg_sgpa = round(sum(valid_sgpas) / len(valid_sgpas), 2) if valid_sgpas else 0.0
        high_sgpa = max(valid_sgpas) if valid_sgpas else 0.0
        low_sgpa = min(valid_sgpas) if valid_sgpas else 0.0
        pass_pct = round(((passed_count + grace_count) / total_students) * 100.0, 2)

        # Grade distribution query
        grade_dist = {"O": 0, "A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "P": 0, "F": 0}
        reg_ids = [r.id for r in regs]

        mark_stats = (
            self.session.query(StudentCourseMark.letter_grade, func.count(StudentCourseMark.id))
            .filter(StudentCourseMark.registration_id.in_(reg_ids))
            .group_by(StudentCourseMark.letter_grade)
            .all()
        )
        for g_letter, count in mark_stats:
            if g_letter in grade_dist:
                grade_dist[g_letter] = count

        # Subject-wise pass/fail performance
        subject_stats = (
            self.session.query(
                Course.course_code,
                Course.course_title,
                func.count(StudentCourseMark.id).label("total_appeared"),
                func.sum(case((StudentCourseMark.course_result == "PASS", 1), else_=0)).label("pass_count"),
                func.sum(case((StudentCourseMark.grace_awarded > 0, 1), else_=0)).label("grace_count"),
                func.avg(StudentCourseMark.percentage).label("avg_percentage"),
            )
            .join(Course, StudentCourseMark.course_id == Course.id)
            .filter(StudentCourseMark.registration_id.in_(reg_ids))
            .group_by(Course.course_code, Course.course_title)
            .all()
        )

        subject_perf = []
        for code, title, appeared, p_cnt, g_cnt, avg_p in subject_stats:
            p_val = int(p_cnt or 0)
            app_val = int(appeared or 0)
            subject_perf.append({
                "course_code": code,
                "course_title": title,
                "total_appeared": app_val,
                "pass_count": p_val,
                "fail_count": app_val - p_val,
                "grace_count": int(g_cnt or 0),
                "pass_rate": round((p_val / app_val * 100.0), 2) if app_val > 0 else 0.0,
                "avg_percentage": round(float(avg_p or 0.0), 2),
            })

        valid_totals = [float(r.grand_total_obtained) for r in regs if r.grand_total_obtained is not None and r.grand_total_obtained > 0]
        high_marks = max(valid_totals) if valid_totals else 0.0
        low_marks = min(valid_totals) if valid_totals else 0.0

        return {
            "semester_number": semester_number,
            "batch_id": batch_id,
            "total_students": total_students,
            "total_appeared": total_students,
            "clear_pass_count": passed_count,
            "passed_count": passed_count,
            "passed_with_grace_count": grace_count,
            "pwg_count": grace_count,
            "failed_count": failed_count,
            "pass_percentage": pass_pct,
            "average_sgpa": avg_sgpa,
            "highest_sgpa": high_sgpa,
            "lowest_sgpa": low_sgpa,
            "highest_marks": high_marks,
            "lowest_marks": low_marks,
            "grade_distribution": grade_dist,
            "batch_sgpa_distribution": grade_dist,
            "subject_performance": subject_perf,
            "subject_pass_rate_percentages": {s["course_code"]: s["pass_rate"] for s in subject_perf},
        }

    # -------------------------------------------------------------------------
    # Role-Based Workflow Approval & State Machine Operations
    # -------------------------------------------------------------------------

    def get_semester_workflow_summary(
        self,
        semester_number: int,
        batch_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Returns status counts across the workflow lifecycle:
        DRAFT -> SCRUTINIZED -> APPROVED -> LOCKED
        and individual student statuses for the semester.
        """
        query = (
            self.session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(
                StudentSemesterRegistration.semester_number == semester_number,
                Student.is_active == True,
            )
        )
        if batch_id:
            query = query.filter(Student.batch_id == batch_id)

        rows = query.order_by(Student.roll_no).all()
        counts = {"DRAFT": 0, "SCRUTINIZED": 0, "APPROVED": 0, "LOCKED": 0}
        students_summary = []

        for reg, stu in rows:
            st = (reg.workflow_status or "DRAFT").upper()
            if st not in counts:
                counts[st] = 0
            counts[st] += 1

            students_summary.append({
                "student_id": stu.id,
                "roll_no": stu.roll_no,
                "enrollment_no": stu.enrollment_no,
                "student_name": stu.student_name,
                "father_name": stu.father_name,
                "semester_number": reg.semester_number,
                "workflow_status": st,
                "sgpa": float(reg.sgpa) if reg.sgpa else None,
                "result_status": reg.result_status,
                "workflow_updated_at": reg.workflow_updated_at.isoformat() if reg.workflow_updated_at else None,
                "workflow_updated_by": reg.workflow_updated_by,
                "workflow_remarks": reg.workflow_remarks,
                "is_locked": st == "LOCKED",
            })

        total = len(rows)
        if total == 0:
            overall_status = "DRAFT"
        elif counts.get("LOCKED", 0) == total:
            overall_status = "LOCKED"
        elif counts.get("APPROVED", 0) + counts.get("LOCKED", 0) == total:
            overall_status = "APPROVED"
        elif counts.get("SCRUTINIZED", 0) + counts.get("APPROVED", 0) + counts.get("LOCKED", 0) == total:
            overall_status = "SCRUTINIZED"
        else:
            overall_status = "DRAFT"

        return {
            "semester_number": semester_number,
            "batch_id": batch_id,
            "total_students": total,
            "counts": counts,
            "overall_status": overall_status,
            "students": students_summary,
        }

    def transition_workflow_status(
        self,
        semester_number: int,
        target_status: str,
        user_role: str,
        operator_name: str,
        roll_no: Optional[str] = None,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transitions registrations from one state to another per institutional hierarchy:
        DRAFT -> SCRUTINIZED -> APPROVED -> LOCKED

        Rule:
        - Only users with 'Admin / Sub-Dean' role can transition marks from SCRUTINIZED to APPROVED.
        - Only users with 'Admin / Sub-Dean' role can transition to LOCKED.
        - Scrutiny Committee can transition DRAFT -> SCRUTINIZED.
        - If already LOCKED, cannot transition directly (must use unlock_for_reevaluation).
        """
        target_norm = target_status.strip().upper()
        if target_norm not in ["DRAFT", "SCRUTINIZED", "APPROVED", "LOCKED"]:
            raise ValueError(f"Invalid target status '{target_status}'. Must be DRAFT, SCRUTINIZED, APPROVED, or LOCKED.")

        role_norm = user_role.strip().lower()
        is_admin_or_subdean = any(keyword in role_norm for keyword in ["admin", "sub-dean", "sub dean", "controller", "dean"])

        if target_norm in ["APPROVED", "LOCKED"] and not is_admin_or_subdean:
            raise PermissionError(
                f"Unauthorized: Only users with the 'Admin / Sub-Dean' role can transition marks to '{target_norm}'. Current role: '{user_role}'."
            )

        query = (
            self.session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(StudentSemesterRegistration.semester_number == semester_number)
        )
        if roll_no:
            query = query.filter(Student.roll_no == roll_no.strip())

        records = query.all()
        if not records:
            raise ValueError(f"No student registrations found for Semester {semester_number}{f' and Roll No {roll_no}' if roll_no else ''}.")

        updated_count = 0
        now = datetime.now()
        op_label = f"{user_role} ({operator_name})" if operator_name else user_role

        for reg, stu in records:
            current_st = (reg.workflow_status or "DRAFT").upper()
            if current_st == "LOCKED" and target_norm != "LOCKED":
                raise PermissionError(
                    f"Student {stu.roll_no} marksheet is LOCKED. Unlock for Re-evaluation override with mandatory justification is required before transitions."
                )

            # Record audit log entry
            audit = MarksAuditLog(
                entity_type="student_semester_registrations",
                entity_id=reg.id,
                student_roll_no=stu.roll_no,
                field_name="workflow_status",
                old_value=current_st,
                new_value=target_norm,
                change_reason=remarks or f"Workflow transitioned from {current_st} to {target_norm}",
                modified_by=op_label,
            )
            self.session.add(audit)

            reg.workflow_status = target_norm
            reg.workflow_updated_at = now
            reg.workflow_updated_by = op_label
            reg.workflow_remarks = remarks
            if target_norm == "SCRUTINIZED":
                reg.is_verified = True
                reg.verified_at = now
                reg.verified_by = op_label
            elif target_norm == "APPROVED":
                reg.is_verified = True

            updated_count += 1

        self.session.commit()
        return {
            "success": True,
            "semester_number": semester_number,
            "roll_no": roll_no,
            "target_status": target_norm,
            "updated_count": updated_count,
            "operator": op_label,
            "remarks": remarks,
        }

    def unlock_for_reevaluation(
        self,
        semester_number: int,
        user_role: str,
        operator_name: str,
        justification: str,
        roll_no: Optional[str] = None,
        target_status: str = "DRAFT"
    ) -> Dict[str, Any]:
        """
        Administrator Override: Unlocks LOCKED marksheets for re-evaluation.
        Requires Admin/Sub-Dean role and mandatory justification comment.
        """
        role_norm = user_role.strip().lower()
        is_admin_or_subdean = any(keyword in role_norm for keyword in ["admin", "sub-dean", "sub dean", "controller", "dean"])
        if not is_admin_or_subdean:
            raise PermissionError(
                f"Unauthorized: Only users with the 'Admin / Sub-Dean' role can unlock locked examination marks. Current role: '{user_role}'."
            )

        if not justification or len(justification.strip()) < 5:
            raise ValueError("A mandatory, substantive justification comment (minimum 5 characters) is required to unlock marksheets for re-evaluation.")

        target_norm = target_status.strip().upper()
        if target_norm not in ["DRAFT", "SCRUTINIZED"]:
            target_norm = "DRAFT"

        query = (
            self.session.query(StudentSemesterRegistration, Student)
            .join(Student, StudentSemesterRegistration.student_id == Student.id)
            .filter(StudentSemesterRegistration.semester_number == semester_number)
        )
        if roll_no:
            query = query.filter(Student.roll_no == roll_no.strip())

        records = query.all()
        if not records:
            raise ValueError(f"No student registrations found for Semester {semester_number}{f' and Roll No {roll_no}' if roll_no else ''}.")

        now = datetime.now()
        op_label = f"{user_role} ({operator_name})" if operator_name else user_role
        justification_clean = justification.strip()
        unlocked_count = 0

        for reg, stu in records:
            old_st = (reg.workflow_status or "DRAFT").upper()
            audit = MarksAuditLog(
                entity_type="student_semester_registrations",
                entity_id=reg.id,
                student_roll_no=stu.roll_no,
                field_name="workflow_status",
                old_value=old_st,
                new_value=target_norm,
                change_reason=f"Unlock for Re-evaluation override: {justification_clean}",
                modified_by=op_label,
            )
            self.session.add(audit)

            reg.workflow_status = target_norm
            reg.workflow_updated_at = now
            reg.workflow_updated_by = op_label
            reg.workflow_remarks = f"Unlocked for Re-evaluation: {justification_clean}"
            unlocked_count += 1

        self.session.commit()
        return {
            "success": True,
            "semester_number": semester_number,
            "roll_no": roll_no,
            "unlocked_count": unlocked_count,
            "new_status": target_norm,
            "operator": op_label,
            "justification": justification_clean,
        }

    def get_audit_trail_for_student(self, roll_no: str) -> List[Dict[str, Any]]:
        """Returns chronological list of all audit modifications for a student."""
        logs = (
            self.session.query(MarksAuditLog)
            .filter_by(student_roll_no=roll_no.strip())
            .order_by(MarksAuditLog.timestamp.desc())
            .all()
        )
        return [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "modified_by": l.modified_by or "SYSTEM",
                "entity_type": l.entity_type,
                "field_name": l.field_name,
                "old_value": l.old_value,
                "new_value": l.new_value,
                "change_reason": l.change_reason or "System operation",
            }
            for l in logs
        ]
