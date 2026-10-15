"""
Self-Verification, Invariance & Quality Audit Gate Engine
Phase 3: Automated integrity checks before marksheet generation.
- Arithmetic & Invariance Parity Checks
- Grace Policy & Statutory Limit Audits
- Demographics, Duplicates & Boundary Outlier Matrix
- PDF Export Gating & Lock Control

Branding: VidyaMarksheet by VidyaLabs
"""

import math
from typing import Dict, List, Optional, Any, Union
from collections import Counter
from pydantic import BaseModel, Field

from backend.schemas.canonical_models import StudentRecord
from backend.evaluation_engine import (
    EvaluationEngine,
    EvaluatedStudentRecord,
    CANONICAL_SEM1_COURSE_METADATA,
    ALL_SEMESTER_CANONICAL_METADATA,
    parse_numeric_score
)


class AuditAnomalyItem(BaseModel):
    roll_no: str = Field(..., description="University Roll Number")
    student_name: str = Field(..., description="Student Full Name")
    field: str = Field(..., description="Field or metric under audit e.g. 'External Total (Part A + Part B)'")
    raw_value: str = Field(..., description="Raw / Observed Value")
    expected_value: str = Field(..., description="Expected / Allowed Invariant Value")
    severity: str = Field(..., description="'CRITICAL' or 'WARNING'")
    category: str = Field(..., description="ARITHMETIC_INVARIANCE, GRACE_POLICY, OUTLIER_BOUNDARY, DEMOGRAPHIC")
    description: str = Field(..., description="Human-readable explanation of the issue")


class QualityAuditReport(BaseModel):
    is_valid: bool = Field(..., description="True if no CRITICAL anomalies exist")
    can_export_pdf: bool = Field(..., description="False if critical unacknowledged errors exist")
    total_candidates: int
    clean_candidates: int
    flagged_candidates: int
    critical_errors_count: int
    warnings_count: int
    anomalies: List[AuditAnomalyItem] = Field(default_factory=list)
    summary: str


class QualityAuditGate:
    """
    Quality Audit Gate for VidyaMarksheet.
    Enforces strict mathematical invariance and INC regulatory compliance:
    1. Arithmetic Invariance:
       - Part A + Part B == External Total
       - Internal + External (with Grace) == Course Total
       - Grand Total and Percentage Parity
       - Independent SGPA recalculation parity
    2. Grace Policy Audit:
       - <= 5.0 marks cap across all courses
       - Only applied to achieve passing cutoff (37.5), never to inflate grades
       - Remarks and computed status parity
    3. Outliers & Boundaries:
       - Missing father names, empty roll numbers, duplicate roll numbers
       - Marks exceeding maximum thresholds (IA > 25, Part A > 37, Part B > 38, EA > 75, etc.)
    """

    def __init__(self, semester_number: int = 1, auto_grace: bool = False):
        self.semester_number = semester_number
        self.auto_grace = auto_grace
        self.evaluation_engine = EvaluationEngine(semester_number=semester_number, auto_grace=auto_grace)

    def audit_batch(
        self,
        students: List[StudentRecord],
        evaluated_students: Optional[List[EvaluatedStudentRecord]] = None
    ) -> QualityAuditReport:
        """Runs full audit checks across an array of StudentRecord objects."""
        if evaluated_students is None:
            eval_batch_res = self.evaluation_engine.evaluate_batch(students)
            evaluated_students = eval_batch_res.results

        anomalies: List[AuditAnomalyItem] = []
        flagged_rolls = set()

        # 1. Demographics & Duplicate Roll Number Check
        roll_counts = Counter(s.roll_no for s in students if s.roll_no.strip())
        for roll, count in roll_counts.items():
            if count > 1:
                matching = [s for s in students if s.roll_no == roll]
                for m in matching:
                    flagged_rolls.add(m.roll_no)
                    anomalies.append(
                        AuditAnomalyItem(
                            roll_no=m.roll_no,
                            student_name=m.student_name,
                            field="Roll Number (Duplicate)",
                            raw_value=f"Appears {count} times",
                            expected_value="Unique Roll Number",
                            severity="CRITICAL",
                            category="DEMOGRAPHIC",
                            description=f"Duplicate roll number '{roll}' detected across {count} student records."
                        )
                    )

        # 2. Iterate each student for granular checks
        eval_map = {e.roll_no: e for e in evaluated_students}

        for student in students:
            eval_record = eval_map.get(student.roll_no)

            # Check Missing Demographics
            if not student.father_name or not student.father_name.strip():
                flagged_rolls.add(student.roll_no)
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field="Father's Name",
                        raw_value="MISSING / EMPTY",
                        expected_value="Non-empty Name",
                        severity="CRITICAL",
                        category="DEMOGRAPHIC",
                        description="Student father/guardian name is missing in Examination Cell records."
                    )
                )

            if not student.student_name or not student.student_name.strip():
                flagged_rolls.add(student.roll_no)
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name="UNKNOWN",
                        field="Student Name",
                        raw_value="MISSING / EMPTY",
                        expected_value="Non-empty Name",
                        severity="CRITICAL",
                        category="DEMOGRAPHIC",
                        description="Candidate full name is blank or missing."
                    )
                )

            # Course-level audits
            student_anomalies = self._audit_student_courses(student, eval_record)
            if student_anomalies:
                flagged_rolls.add(student.roll_no)
                anomalies.extend(student_anomalies)

            # Grand Total & Percentage Parity
            if eval_record:
                gt_anomalies = self._audit_grand_aggregates(student, eval_record)
                if gt_anomalies:
                    flagged_rolls.add(student.roll_no)
                    anomalies.extend(gt_anomalies)

        critical_count = sum(1 for a in anomalies if a.severity == "CRITICAL")
        warning_count = sum(1 for a in anomalies if a.severity == "WARNING")
        is_valid = (critical_count == 0)

        total_students = len(students)
        flagged_count = len(flagged_rolls)
        clean_count = total_students - flagged_count

        if is_valid:
            summary = (
                f"Audit Gate Passed: All {total_students} student records verified with zero arithmetic, "
                f"grace, or boundary violations. Ready for marksheet PDF generation."
            )
        else:
            summary = (
                f"Audit Gate Flagged {critical_count} critical error(s) and {warning_count} warning(s) "
                f"across {flagged_count} candidate records. PDF export locked until resolved."
            )

        return QualityAuditReport(
            is_valid=is_valid,
            can_export_pdf=is_valid,
            total_candidates=total_students,
            clean_candidates=clean_count,
            flagged_candidates=flagged_count,
            critical_errors_count=critical_count,
            warnings_count=warning_count,
            anomalies=anomalies,
            summary=summary
        )

    def _audit_student_courses(
        self,
        student: StudentRecord,
        eval_record: Optional[EvaluatedStudentRecord]
    ) -> List[AuditAnomalyItem]:
        anomalies: List[AuditAnomalyItem] = []
        raw_courses = student.courses

        total_grace_awarded = 0.0

        sem_meta = ALL_SEMESTER_CANONICAL_METADATA.get(self.semester_number, CANONICAL_SEM1_COURSE_METADATA)

        for c_key, c_meta in sem_meta.items():
            if c_key not in raw_courses:
                continue

            c_raw = raw_courses[c_key]
            if hasattr(c_raw, "dict"):
                c_dict = c_raw.dict()
            elif isinstance(c_raw, dict):
                c_dict = c_raw
            else:
                c_dict = {}

            # Skip exemption auditing
            if c_dict.get("is_exempted") or str(c_dict.get("int_marks")).strip().upper() in ["EX.", "EX", "X"]:
                continue

            int_m, int_ab = parse_numeric_score(c_dict.get("int_marks"))
            ex_tot, ex_ab = parse_numeric_score(c_dict.get("ex_total") or c_dict.get("ex_marks"))
            pa_m, pa_ab = parse_numeric_score(c_dict.get("ex_part_a")) if "ex_part_a" in c_dict else (None, False)
            pb_m, pb_ab = parse_numeric_score(c_dict.get("ex_part_b")) if "ex_part_b" in c_dict else (None, False)
            pc_m, pc_ab = parse_numeric_score(c_dict.get("ex_part_c")) if "ex_part_c" in c_dict else (None, False)
            grace_val, _ = parse_numeric_score(c_dict.get("grace", 0))
            tot_m, tot_ab = parse_numeric_score(c_dict.get("total"))

            grace_val = grace_val or 0.0
            total_grace_awarded += grace_val

            # A. Boundary & Maximum Limits Check
            ia_max = c_meta["ia_max"]
            ea_max = c_meta["ea_max"]
            tot_max = c_meta["total_max"]

            if int_m is not None and int_m > ia_max:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field=f"{c_meta['course_code']} Internal Marks",
                        raw_value=str(int_m),
                        expected_value=f"<= {ia_max}",
                        severity="CRITICAL",
                        category="OUTLIER_BOUNDARY",
                        description=f"Internal Assessment marks ({int_m}) exceed maximum allowable marks ({ia_max})."
                    )
                )

            sec_a_max = c_meta.get("sec_a_max", 37.0)
            sec_b_max = c_meta.get("sec_b_max", 38.0)
            sec_c_max = c_meta.get("sec_c_max", 12.0)

            if pa_m is not None and pa_m > sec_a_max:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field=f"{c_meta['course_code']} Section A Marks",
                        raw_value=str(pa_m),
                        expected_value=f"<= {sec_a_max}",
                        severity="CRITICAL",
                        category="OUTLIER_BOUNDARY",
                        description=f"Section A marks ({pa_m}) exceed maximum allowable score ({sec_a_max})."
                    )
                )

            if pb_m is not None and pb_m > sec_b_max:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field=f"{c_meta['course_code']} Section B Marks",
                        raw_value=str(pb_m),
                        expected_value=f"<= {sec_b_max}",
                        severity="CRITICAL",
                        category="OUTLIER_BOUNDARY",
                        description=f"Section B marks ({pb_m}) exceed maximum allowable score ({sec_b_max})."
                    )
                )

            if pc_m is not None and pc_m > sec_c_max:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field=f"{c_meta['course_code']} Section C Marks",
                        raw_value=str(pc_m),
                        expected_value=f"<= {sec_c_max}",
                        severity="CRITICAL",
                        category="OUTLIER_BOUNDARY",
                        description=f"Section C marks ({pc_m}) exceed maximum allowable score ({sec_c_max})."
                    )
                )

            if ex_tot is not None and ex_tot > ea_max:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field=f"{c_meta['course_code']} External Exam",
                        raw_value=str(ex_tot),
                        expected_value=f"<= {ea_max}",
                        severity="CRITICAL",
                        category="OUTLIER_BOUNDARY",
                        description=f"External exam marks ({ex_tot}) exceed maximum allowable ({ea_max})."
                    )
                )

            if tot_m is not None and tot_m > tot_max:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field=f"{c_meta['course_code']} Total Marks",
                        raw_value=str(tot_m),
                        expected_value=f"<= {tot_max}",
                        severity="CRITICAL",
                        category="OUTLIER_BOUNDARY",
                        description=f"Course total marks ({tot_m}) exceed maximum allowable ({tot_max})."
                    )
                )

            # B. Arithmetic Invariance Check 1: Subcomponents (Part A + Part B [+ Part C]) == External Total
            if pc_m is not None and pa_m is not None and pb_m is not None and ex_tot is not None and not pa_ab and not pb_ab and not pc_ab and not ex_ab:
                sum_parts = round(pa_m + pb_m + pc_m, 2)
                if abs(sum_parts - ex_tot) > 0.05:
                    anomalies.append(
                        AuditAnomalyItem(
                            roll_no=student.roll_no,
                            student_name=student.student_name,
                            field=f"{c_meta['course_code']} Subcomponent Parity",
                            raw_value=f"PHAR ({pa_m}) + PATH ({pb_m}) + GEN ({pc_m}) = {sum_parts}",
                            expected_value=f"External Total ({ex_tot})",
                            severity="CRITICAL",
                            category="ARITHMETIC_INVARIANCE",
                            description=(
                                f"Arithmetic mismatch in {c_meta['course_title']}: "
                                f"PHAR ({pa_m}) + PATH ({pb_m}) + GEN ({pc_m}) != External Total ({ex_tot})."
                            )
                        )
                    )
            elif pa_m is not None and pb_m is not None and ex_tot is not None and not pa_ab and not pb_ab and not ex_ab:
                sum_parts = round(pa_m + pb_m, 2)
                if abs(sum_parts - ex_tot) > 0.05:
                    anomalies.append(
                        AuditAnomalyItem(
                            roll_no=student.roll_no,
                            student_name=student.student_name,
                            field=f"{c_meta['course_code']} Subcomponent Parity",
                            raw_value=f"Part A ({pa_m}) + Part B ({pb_m}) = {sum_parts}",
                            expected_value=f"External Total ({ex_tot})",
                            severity="CRITICAL",
                            category="ARITHMETIC_INVARIANCE",
                            description=(
                                f"Arithmetic mismatch in {c_meta['course_title']}: "
                                f"Part A ({pa_m}) + Part B ({pb_m}) != External Total ({ex_tot})."
                            )
                        )
                    )

            # C. Arithmetic Invariance Check 2: Internal + External (with Grace) == Course Total
            if int_m is not None and ex_tot is not None and tot_m is not None and not int_ab and not ex_ab and not tot_ab:
                expected_course_total = round(int_m + ex_tot + grace_val, 2)
                # Allow tolerance for standard half-mark rounding to integer in university ledgers (e.g. 13 + 35 + 2.5 = 50.5 -> 51)
                is_sum_valid = (
                    abs(expected_course_total - tot_m) <= 0.05
                    or abs(round(expected_course_total) - tot_m) <= 0.05
                    or abs(math.ceil(expected_course_total) - tot_m) <= 0.05
                    or (abs(expected_course_total - tot_m) <= 0.55 and float(tot_m).is_integer())
                )
                if not is_sum_valid:
                    anomalies.append(
                        AuditAnomalyItem(
                            roll_no=student.roll_no,
                            student_name=student.student_name,
                            field=f"{c_meta['course_code']} Total Sum Parity",
                            raw_value=f"Total in Sheet = {tot_m}",
                            expected_value=f"IA ({int_m}) + EA ({ex_tot}) + Grace ({grace_val}) = {expected_course_total}",
                            severity="CRITICAL",
                            category="ARITHMETIC_INVARIANCE",
                            description=(
                                f"Summation parity violated in {c_meta['course_title']}: "
                                f"Internal ({int_m}) + External ({ex_tot}) + Grace ({grace_val}) != Total ({tot_m})."
                            )
                        )
                    )

            # D. Grace Policy Audit: Inflation vs Passing Cutoff
            if grace_val > 0:
                pass_cutoff = c_meta["ea_min_pass"]  # 37.5 for standard courses
                if ex_tot is not None and ex_tot >= pass_cutoff:
                    # Grace given when raw marks already passed
                    anomalies.append(
                        AuditAnomalyItem(
                            roll_no=student.roll_no,
                            student_name=student.student_name,
                            field=f"{c_meta['course_code']} Grace Inflation",
                            raw_value=f"Raw EA = {ex_tot}, Grace = {grace_val}",
                            expected_value="Grace = 0 (Candidate already passed)",
                            severity="CRITICAL",
                            category="GRACE_POLICY",
                            description=(
                                f"Grace marks ({grace_val}) awarded in {c_meta['course_title']} despite candidate "
                                f"already meeting the {pass_cutoff} passing cutoff ({ex_tot}). Grade inflation prohibited."
                            )
                        )
                    )
                elif ex_tot is not None:
                    post_grace_ea = round(ex_tot + grace_val, 2)
                    if post_grace_ea < pass_cutoff:
                        anomalies.append(
                            AuditAnomalyItem(
                                roll_no=student.roll_no,
                                student_name=student.student_name,
                                field=f"{c_meta['course_code']} Grace Insufficient",
                                raw_value=f"Post-grace EA = {post_grace_ea}",
                                expected_value=f">= {pass_cutoff}",
                                severity="CRITICAL",
                                category="GRACE_POLICY",
                                description=(
                                    f"Grace marks ({grace_val}) fail to bring external score ({ex_tot}) to the "
                                    f"statutory passing cutoff ({pass_cutoff}). Post-grace score is {post_grace_ea}."
                                )
                            )
                        )
                    elif post_grace_ea > pass_cutoff:
                        # Extra grace exceeding cutoff
                        anomalies.append(
                            AuditAnomalyItem(
                                roll_no=student.roll_no,
                                student_name=student.student_name,
                                field=f"{c_meta['course_code']} Grace Over-Award",
                                raw_value=f"Post-grace EA = {post_grace_ea}",
                                expected_value=f"Exactly {pass_cutoff}",
                                severity="WARNING",
                                category="GRACE_POLICY",
                                description=(
                                    f"Grace marks ({grace_val}) exceeded the deficit to reach {pass_cutoff} cutoff "
                                    f"(resulting in {post_grace_ea}). Grace should strictly equalize cutoff."
                                )
                            )
                        )

        # E. Total Grace Cap Audit (<= 5.0 marks total)
        if total_grace_awarded > 5.0:
            anomalies.append(
                AuditAnomalyItem(
                    roll_no=student.roll_no,
                    student_name=student.student_name,
                    field="Statutory Grace Cap",
                    raw_value=f"Total Grace = {total_grace_awarded}",
                    expected_value="<= 5.0 marks total",
                    severity="CRITICAL",
                    category="GRACE_POLICY",
                    description=(
                        f"Cumulative grace awarded ({total_grace_awarded}) exceeds the Indian Nursing Council (INC) "
                        f"statutory upper limit of 5.0 marks per candidate."
                    )
                )
            )

        # F. Examination Cell Remarks Consistency Check
        if eval_record and student.raw_remarks:
            computed_pass = "PASS" in eval_record.result_status
            remark_upper = student.raw_remarks.upper()

            if not computed_pass and "PASS" in remark_upper and "FAIL" not in remark_upper:
                anomalies.append(
                    AuditAnomalyItem(
                        roll_no=student.roll_no,
                        student_name=student.student_name,
                        field="Status Remark Discrepancy",
                        raw_value=student.raw_remarks,
                        expected_value="FAIL",
                        severity="CRITICAL",
                        category="GRACE_POLICY",
                        description=(
                            f"Discrepancy: Examination cell remarks say '{student.raw_remarks}', but calculated "
                            f"evaluation determines student FAILED ({', '.join(eval_record.failed_courses)})."
                        )
                    )
                )

        return anomalies

    def _audit_grand_aggregates(
        self,
        student: StudentRecord,
        eval_record: EvaluatedStudentRecord
    ) -> List[AuditAnomalyItem]:
        anomalies: List[AuditAnomalyItem] = []

        # Recompute Grand Total independently
        recomputed_gt = 0.0
        for c_eval in eval_record.courses.values():
            if isinstance(c_eval.total_marks, (int, float)):
                recomputed_gt += float(c_eval.total_marks)

        recomputed_gt = round(recomputed_gt, 2)
        if abs(recomputed_gt - eval_record.total_marks_obtained) > 0.05:
            anomalies.append(
                AuditAnomalyItem(
                    roll_no=student.roll_no,
                    student_name=student.student_name,
                    field="Grand Total Parity",
                    raw_value=str(eval_record.total_marks_obtained),
                    expected_value=str(recomputed_gt),
                    severity="CRITICAL",
                    category="ARITHMETIC_INVARIANCE",
                    description=f"Grand total marks ({eval_record.total_marks_obtained}) do not match sum of courses ({recomputed_gt})."
                )
            )

        # Recompute SGPA independently from credits and grade points
        recomputed_credit_points = 0.0
        recomputed_sgpa_credits = 0

        for c_eval in eval_record.courses.values():
            if c_eval.include_in_sgpa and c_eval.credits > 0:
                recomputed_sgpa_credits += c_eval.credits
                if c_eval.is_pass:
                    recomputed_credit_points += c_eval.credits * c_eval.grade_point

        target_credits = max(eval_record.total_sgpa_credits, recomputed_sgpa_credits, 1)
        recomputed_sgpa = round(recomputed_credit_points / target_credits, 2)

        if abs(recomputed_sgpa - eval_record.sgpa) > 0.02:
            anomalies.append(
                AuditAnomalyItem(
                    roll_no=student.roll_no,
                    student_name=student.student_name,
                    field="SGPA Recomputation Invariance",
                    raw_value=str(eval_record.sgpa),
                    expected_value=str(recomputed_sgpa),
                    severity="CRITICAL",
                    category="ARITHMETIC_INVARIANCE",
                    description=(
                        f"SGPA calculation parity check failed: Evaluated SGPA is {eval_record.sgpa}, "
                        f"but independent recomputation yields {recomputed_sgpa}."
                    )
                )
            )

        return anomalies
