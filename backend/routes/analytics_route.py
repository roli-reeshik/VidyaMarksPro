"""
Analytics & Longitudinal KPI Engine Route
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
Compliant with Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Regulations.

Endpoints:
- GET /api/v1/analytics/overview:
    Aggregated KPIs, passing rate, distinction rate, max/median %, Top 3 Rankers,
    backlog density, grade distribution histogram, and longitudinal YoY trend comparison.
- GET /api/v1/analytics/subject-performance:
    Course-wise pass percentage, mean internal score, mean external score, and failure count
    grouped by Course Code to identify challenging subjects.
"""

import re
import statistics
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc

from backend.db.database import get_sync_session
from backend.db.models import (
    Student,
    StudentSemesterRegistration,
    StudentCourseMark,
    Course,
    Batch,
    StudentBacklog,
)
from backend.security import require_authenticated

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Longitudinal KPI Engine"])


def _extract_year_from_session(session_text: Optional[str]) -> Optional[str]:
    """Extracts 4-digit year (e.g., '2026') from session string like 'JANUARY - 2026'."""
    if not session_text:
        return None
    match = re.search(r"\b(20\d\d)\b", str(session_text))
    return match.group(1) if match else None


def _is_passed_status(result_status: Optional[str]) -> bool:
    """Evaluates whether a registration result status indicates a passing outcome."""
    if not result_status:
        return False
    st = result_status.strip().upper()
    return "PASS" in st and "FAIL" not in st


@router.get("/overview")
def get_analytics_overview(
    exam_session: Optional[str] = Query(None, description="e.g. 'JANUARY - 2026', 'July 2026'"),
    academic_year: Optional[str] = Query(None, description="e.g. '2025', '2026'"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Target Semester 1-8"),
    current_user: Any = Depends(require_authenticated),
):
    """
    Computes institutional cohort analytics & longitudinal KPIs.
    Supports filtering by exam_session, academic_year, and semester.
    Returns:
    - Overall Passing Rate
    - Distinction / First Class Rate (Percentage >= 75%)
    - Max Percentage & Median Percentage
    - Top 3 Rankers with distinctions and medals
    - Backlog Density (students needing Re-appear in next cycle)
    - Grade Distribution histogram (O, A+, A, B+, B, C, F)
    - Longitudinal Trend Comparison (Year-over-year progression & SGPA drift)
    """
    with get_sync_session() as session:
        # Base query joining registrations with students
        query = session.query(
            StudentSemesterRegistration,
            Student.student_name,
            Student.roll_no,
            Student.enrollment_no,
        ).join(Student, StudentSemesterRegistration.student_id == Student.id)

        # Apply filters
        if semester:
            query = query.filter(StudentSemesterRegistration.semester_number == semester)

        if exam_session and exam_session.strip() and exam_session.strip().lower() != "all sessions":
            # Normalize match
            clean_sess = exam_session.strip()
            query = query.filter(StudentSemesterRegistration.exam_month_year.ilike(f"%{clean_sess}%"))

        if academic_year and academic_year.strip() and academic_year.strip().lower() != "all years":
            clean_year = academic_year.strip()
            query = query.filter(StudentSemesterRegistration.exam_month_year.ilike(f"%{clean_year}%"))

        records = query.all()
        total_registered = len(records)

        # 1. Passing & Distinction Metrics
        passed_records = []
        failed_records = []
        percentages: List[float] = []
        sgpas: List[float] = []
        distinction_count = 0
        first_division_count = 0
        second_division_count = 0
        pass_class_count = 0

        reg_ids = []
        student_rank_candidates = []

        for reg, name, roll_no, enroll_no in records:
            reg_ids.append(reg.id)
            is_pass = _is_passed_status(reg.result_status)
            if is_pass:
                passed_records.append(reg)
            else:
                failed_records.append(reg)

            pct = float(reg.percentage) if reg.percentage is not None else 0.0
            sgpa_val = float(reg.sgpa) if reg.sgpa is not None else 0.0

            if reg.percentage is not None:
                percentages.append(pct)
            if reg.sgpa is not None:
                sgpas.append(sgpa_val)

            # Distinction & Division classifications
            if pct >= 75.0:
                distinction_count += 1
            elif pct >= 60.0:
                first_division_count += 1
            elif pct >= 50.0:
                second_division_count += 1
            elif is_pass:
                pass_class_count += 1

            student_rank_candidates.append({
                "student_name": name,
                "roll_no": roll_no,
                "enrollment_no": enroll_no,
                "semester_number": reg.semester_number,
                "exam_session": reg.exam_month_year,
                "sgpa": sgpa_val,
                "percentage": pct,
                "is_pass": is_pass,
                "result_status": reg.result_status or ("PASS" if is_pass else "FAIL"),
            })

        total_passed = len(passed_records)
        total_failed = len(failed_records)
        passing_rate = round((total_passed / total_registered * 100.0), 2) if total_registered > 0 else 0.0
        distinction_rate = round((distinction_count / total_registered * 100.0), 2) if total_registered > 0 else 0.0

        max_percentage = round(max(percentages), 2) if percentages else 0.0
        median_percentage = round(statistics.median(percentages), 2) if percentages else 0.0
        min_percentage = round(min(percentages), 2) if percentages else 0.0
        avg_sgpa = round(statistics.mean(sgpas), 2) if sgpas else 0.0
        max_sgpa = round(max(sgpas), 2) if sgpas else 0.0

        # 2. Top 3 Rankers across semesters
        # Filter for candidates who passed (or high achievers), ranked by SGPA desc, percentage desc
        # Deduplicate students if multiple attempts/semesters
        eligible_for_rank = [c for c in student_rank_candidates if c["is_pass"]]
        if not eligible_for_rank and student_rank_candidates:
            eligible_for_rank = student_rank_candidates

        eligible_for_rank.sort(key=lambda x: (x["sgpa"], x["percentage"]), reverse=True)

        top_3_rankers = []
        seen_rolls = set()
        medals = ["Gold Medalist", "Silver Medalist", "Bronze Medalist"]
        badge_types = ["gold", "silver", "bronze"]

        for cand in eligible_for_rank:
            if cand["roll_no"] in seen_rolls:
                continue
            seen_rolls.add(cand["roll_no"])
            rank_idx = len(top_3_rankers)
            top_3_rankers.append({
                "rank": rank_idx + 1,
                "medal": medals[rank_idx],
                "badge_type": badge_types[rank_idx],
                "student_name": cand["student_name"],
                "roll_no": cand["roll_no"],
                "enrollment_no": cand["enrollment_no"],
                "semester": cand["semester_number"],
                "sgpa": cand["sgpa"],
                "percentage": cand["percentage"],
                "has_distinction": cand["percentage"] >= 75.0,
                "distinction_badge": "Distinction Achiever" if cand["percentage"] >= 75.0 else "First Class",
                "result_status": cand["result_status"],
            })
            if len(top_3_rankers) == 3:
                break

        # 3. Backlog Density (students needing Re-appear in the forthcoming cycle)
        # Count of students with FAIL in current registration cohort or active in student_backlogs
        backlog_student_ids = set()
        for reg in failed_records:
            backlog_student_ids.add(reg.student_id)

        # Query explicit active backlog table
        active_db_backlogs = session.query(StudentBacklog.student_id).filter(
            StudentBacklog.backlog_status == "ACTIVE"
        )
        if semester:
            active_db_backlogs = active_db_backlogs.filter(StudentBacklog.semester_number == semester)
        for row in active_db_backlogs.all():
            backlog_student_ids.add(row[0])

        backlog_density_count = len(backlog_student_ids)

        # 4. Grade Distribution (Histogram counts for O, A+, A, B+, B, C, F)
        grade_distribution = {
            "O": 0,
            "A+": 0,
            "A": 0,
            "B+": 0,
            "B": 0,
            "C": 0,
            "F": 0,
            "Ab": 0,
        }

        if reg_ids:
            marks_query = (
                session.query(
                    StudentCourseMark.letter_grade,
                    func.count(StudentCourseMark.id),
                )
                .filter(StudentCourseMark.registration_id.in_(reg_ids))
                .group_by(StudentCourseMark.letter_grade)
                .all()
            )
            for l_grade, cnt in marks_query:
                norm_grade = str(l_grade).strip().upper() if l_grade else "F"
                if norm_grade in grade_distribution:
                    grade_distribution[norm_grade] += cnt
                elif "A+" in norm_grade:
                    grade_distribution["A+"] += cnt
                elif "B+" in norm_grade:
                    grade_distribution["B+"] += cnt
                elif "AB" in norm_grade:
                    grade_distribution["Ab"] += cnt
                else:
                    grade_distribution["F"] += cnt

        # 5. Longitudinal Trend Comparison (Year-over-Year Progression)
        all_registrations = (
            session.query(
                StudentSemesterRegistration.exam_month_year,
                StudentSemesterRegistration.result_status,
                StudentSemesterRegistration.sgpa,
                StudentSemesterRegistration.percentage,
            ).all()
        )

        year_groups: Dict[str, Dict[str, Any]] = {}
        for r_session, r_res, r_sgpa, r_pct in all_registrations:
            yr = _extract_year_from_session(r_session) or "2026"
            if yr not in year_groups:
                year_groups[yr] = {"total": 0, "passed": 0, "sgpas": [], "percentages": []}
            year_groups[yr]["total"] += 1
            if _is_passed_status(r_res):
                year_groups[yr]["passed"] += 1
            if r_sgpa is not None:
                year_groups[yr]["sgpas"].append(float(r_sgpa))
            if r_pct is not None:
                year_groups[yr]["percentages"].append(float(r_pct))

        yearly_trends = []
        for yr in sorted(year_groups.keys()):
            yg = year_groups[yr]
            y_tot = yg["total"]
            y_pass = yg["passed"]
            y_rate = round(y_pass / y_tot * 100.0, 2) if y_tot > 0 else 0.0
            y_avg_sgpa = round(statistics.mean(yg["sgpas"]), 2) if yg["sgpas"] else 0.0
            y_avg_pct = round(statistics.mean(yg["percentages"]), 2) if yg["percentages"] else 0.0
            yearly_trends.append({
                "year": yr,
                "total_candidates": y_tot,
                "passed_candidates": y_pass,
                "pass_percentage": y_rate,
                "avg_sgpa": y_avg_sgpa,
                "avg_percentage": y_avg_pct,
            })

        # Calculate Year-over-Year comparison drift
        trend_comparison = {
            "has_prior_year_data": False,
            "pass_rate_drift": 0.0,
            "sgpa_drift": 0.0,
            "direction": "NEUTRAL",
            "narrative": "Baseline cohort established for examination tracking.",
        }

        # Compare latest year vs previous year if available
        if len(yearly_trends) >= 2:
            prior_yr_data = yearly_trends[-2]
            curr_yr_data = yearly_trends[-1]
            p_drift = round(curr_yr_data["pass_percentage"] - prior_yr_data["pass_percentage"], 2)
            s_drift = round(curr_yr_data["avg_sgpa"] - prior_yr_data["avg_sgpa"], 2)
            direction = "UP" if p_drift >= 0 else "DOWN"
            trend_comparison = {
                "has_prior_year_data": True,
                "prior_year": prior_yr_data["year"],
                "current_year": curr_yr_data["year"],
                "pass_rate_drift": p_drift,
                "sgpa_drift": s_drift,
                "direction": direction,
                "narrative": (
                    f"Overall pass rate changed by {p_drift:+.2f}% with SGPA drift of {s_drift:+.2f} "
                    f"compared to academic cycle {prior_yr_data['year']}."
                ),
            }

        # Metadata for frontend dropdown filters
        available_sessions = [
            row[0]
            for row in session.query(StudentSemesterRegistration.exam_month_year)
            .distinct()
            .order_by(StudentSemesterRegistration.exam_month_year)
            .all()
            if row[0]
        ]
        available_semesters = [
            row[0]
            for row in session.query(StudentSemesterRegistration.semester_number)
            .distinct()
            .order_by(StudentSemesterRegistration.semester_number)
            .all()
            if row[0]
        ]
        available_years = sorted(list({_extract_year_from_session(s) for s in available_sessions if _extract_year_from_session(s)}))

        return {
            "status": "success",
            "filters_applied": {
                "exam_session": exam_session,
                "academic_year": academic_year,
                "semester": semester,
            },
            "kpis": {
                "total_registered": total_registered,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_passing_rate": passing_rate,
                "distinction_count": distinction_count,
                "distinction_rate": distinction_rate,
                "first_division_count": first_division_count,
                "second_division_count": second_division_count,
                "pass_class_count": pass_class_count,
                "maximum_percentage": max_percentage,
                "median_percentage": median_percentage,
                "minimum_percentage": min_percentage,
                "average_sgpa": avg_sgpa,
                "maximum_sgpa": max_sgpa,
                "backlog_density": backlog_density_count,
            },
            "top_3_rankers": top_3_rankers,
            "grade_distribution": grade_distribution,
            "longitudinal_trends": yearly_trends,
            "trend_comparison": trend_comparison,
            "meta": {
                "available_sessions": available_sessions,
                "available_semesters": available_semesters,
                "available_years": available_years,
            },
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.get("/subject-performance")
def get_subject_performance(
    exam_session: Optional[str] = Query(None, description="e.g. 'JANUARY - 2026'"),
    academic_year: Optional[str] = Query(None, description="e.g. '2025', '2026'"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Target Semester 1-8"),
    current_user: Any = Depends(require_authenticated),
):
    """
    Returns course-wise passing percentage, mean internal score, mean external score,
    and failure counts grouped by Course Code to identify challenging subjects.
    """
    with get_sync_session() as session:
        query = (
            session.query(
                Course.course_code,
                Course.course_title,
                Course.semester_number,
                Course.credits,
                Course.max_internal,
                Course.max_external,
                Course.max_total,
                func.count(StudentCourseMark.id).label("total_students"),
                func.sum(
                    case((StudentCourseMark.course_result == "PASS", 1), else_=0)
                ).label("passed_count"),
                func.sum(
                    case((StudentCourseMark.course_result != "PASS", 1), else_=0)
                ).label("failed_count"),
                func.avg(StudentCourseMark.internal_obtained).label("avg_internal"),
                func.avg(StudentCourseMark.external_obtained).label("avg_external"),
                func.avg(StudentCourseMark.total_obtained).label("avg_total"),
            )
            .join(StudentCourseMark, StudentCourseMark.course_id == Course.id)
            .join(
                StudentSemesterRegistration,
                StudentCourseMark.registration_id == StudentSemesterRegistration.id,
            )
        )

        if semester:
            query = query.filter(Course.semester_number == semester)

        if exam_session and exam_session.strip() and exam_session.strip().lower() != "all sessions":
            query = query.filter(StudentSemesterRegistration.exam_month_year.ilike(f"%{exam_session.strip()}%"))

        if academic_year and academic_year.strip() and academic_year.strip().lower() != "all years":
            query = query.filter(StudentSemesterRegistration.exam_month_year.ilike(f"%{academic_year.strip()}%"))

        query = query.group_by(
            Course.course_code,
            Course.course_title,
            Course.semester_number,
            Course.credits,
            Course.max_internal,
            Course.max_external,
            Course.max_total,
        ).order_by(
            desc("failed_count"),
            Course.semester_number,
            Course.course_code,
        )

        rows = query.all()
        results = []

        for r in rows:
            tot = int(r.total_students or 0)
            p_cnt = int(r.passed_count or 0)
            f_cnt = int(r.failed_count or 0)
            pass_pct = round((p_cnt / tot * 100.0), 2) if tot > 0 else 0.0
            avg_int = round(float(r.avg_internal or 0), 2)
            avg_ext = round(float(r.avg_external or 0), 2)
            avg_tot = round(float(r.avg_total or 0), 2)

            # Identification of challenging subjects (e.g. failure count > 0 or pass percentage < 85%)
            is_challenging = (f_cnt > 0) or (pass_pct < 85.0 and tot >= 3)

            results.append({
                "course_code": r.course_code,
                "course_title": r.course_title,
                "semester_number": r.semester_number,
                "credits": float(r.credits),
                "max_internal": float(r.max_internal),
                "max_external": float(r.max_external),
                "max_total": float(r.max_total),
                "total_students": tot,
                "passed_count": p_cnt,
                "failed_count": f_cnt,
                "pass_percentage": pass_pct,
                "mean_internal_score": avg_int,
                "mean_external_score": avg_ext,
                "mean_total_score": avg_tot,
                "is_challenging": is_challenging,
                "challenge_severity": "HIGH" if f_cnt >= 5 or pass_pct < 60.0 else ("MODERATE" if f_cnt > 0 else "LOW"),
            })

        return {
            "status": "success",
            "total_courses_evaluated": len(results),
            "challenging_subjects_count": sum(1 for c in results if c["is_challenging"]),
            "courses": results,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }


@router.get("/backlog-roster")
def get_backlog_roster_endpoint(
    semester: Optional[int] = Query(None, ge=1, le=8, description="Target Semester 1-8"),
    status: Optional[str] = Query("ACTIVE", description="'ACTIVE', 'CLEARED', or 'ALL'"),
    current_user: Any = Depends(require_authenticated),
):
    """
    Retrieves the authoritative roster of students with active or cleared backlogs,
    including deficit marks, failed component, attempt count, and forthcoming examination sitting tags.
    """
    with get_sync_session() as session:
        from backend.db.repository import ExaminationRepository
        repo = ExaminationRepository(session)
        # Ensure any historical unregistered failed marks are synchronized
        repo.sync_all_unregistered_backlogs()
        roster = repo.get_backlog_roster(semester_number=semester, backlog_status=status or "ACTIVE")
        return {
            "status": "success",
            "total_candidates": len(roster),
            "semester_filter": semester,
            "status_filter": status,
            "roster": roster,
            "branding": "VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)",
        }
