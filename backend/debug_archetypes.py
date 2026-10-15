"""
5-Category Marksheet Debugging Archetypes & Categorization Engine
Phase 4: Multi-scenario debugging preview for Pass, Grace, Fail, Distinction, and Borderline cases.
Branding: VidyaMarksheet by VidyaLabs
"""

from typing import List, Dict, Optional, Any
from backend.evaluation_engine import EvaluatedStudentRecord, CourseEvaluationDetail


def create_sample_student(
    roll: str,
    name: str,
    enroll: str,
    father: str,
    anat_ia: float,
    anat_ea: float,
    anat_grace: float,
    soci_ia: float,
    soci_ea: float,
    soci_grace: float,
    engl_ia: float,
    engl_ea: float,
    engl_grace: float,
    result_status: str,
    remarks: str
) -> EvaluatedStudentRecord:
    # 1. ANAT_PHYS
    anat_tot = anat_ia + anat_ea + anat_grace
    anat_pass = (anat_ia >= 12.5) and ((anat_ea + anat_grace) >= 37.5) and (anat_tot >= 50.0)
    anat_pct = (anat_tot / 100.0) * 100.0
    if not anat_pass:
        anat_gp = 0
        anat_grade = "F"
    elif anat_pct >= 85:
        anat_gp = 10; anat_grade = "O"
    elif anat_pct >= 75:
        anat_gp = 9; anat_grade = "A+"
    elif anat_pct >= 65:
        anat_gp = 8; anat_grade = "A"
    elif anat_pct >= 55:
        anat_gp = 7; anat_grade = "B+"
    else:
        anat_gp = 6; anat_grade = "B"

    # 2. SOCI_PSYC
    soci_tot = soci_ia + soci_ea + soci_grace
    soci_pass = (soci_ia >= 12.5) and ((soci_ea + soci_grace) >= 37.5) and (soci_tot >= 50.0)
    soci_pct = (soci_tot / 100.0) * 100.0
    if not soci_pass:
        soci_gp = 0
        soci_grade = "F"
    elif soci_pct >= 85:
        soci_gp = 10; soci_grade = "O"
    elif soci_pct >= 75:
        soci_gp = 9; soci_grade = "A+"
    elif soci_pct >= 65:
        soci_gp = 8; soci_grade = "A"
    elif soci_pct >= 55:
        soci_gp = 7; soci_grade = "B+"
    else:
        soci_gp = 6; soci_grade = "B"

    # 3. ENGL 101 (College exam, 2 credits, not in SGPA)
    engl_tot = engl_ia + engl_ea + engl_grace
    engl_pass = (engl_ia >= 10.0) and ((engl_ea + engl_grace) >= 10.0) and (engl_tot >= 20.0)
    engl_pct = (engl_tot / 50.0) * 100.0
    if not engl_pass:
        engl_gp = 0
        engl_grade = "F"
    elif engl_pct >= 85:
        engl_gp = 10; engl_grade = "O"
    elif engl_pct >= 75:
        engl_gp = 9; engl_grade = "A+"
    elif engl_pct >= 65:
        engl_gp = 8; engl_grade = "A"
    elif engl_pct >= 55:
        engl_gp = 7; engl_grade = "B+"
    else:
        engl_gp = 6; engl_grade = "B"

    courses = {
        "ANAT_PHYS": CourseEvaluationDetail(
            course_key="ANAT_PHYS",
            course_code="ANAT 105 & PHYS 110",
            course_title="Applied Anatomy & Applied Physiology",
            credits=6,
            include_in_sgpa=True,
            is_english_or_elective=False,
            internal_marks=anat_ia,
            internal_max=25.0,
            internal_pass=(anat_ia >= 12.5),
            external_marks=anat_ea,
            external_max=75.0,
            external_pass=((anat_ea + anat_grace) >= 37.5),
            grace_awarded=anat_grace,
            effective_external=anat_ea + anat_grace,
            total_marks=anat_tot,
            total_max=100.0,
            aggregate_pass=anat_pass,
            percentage=anat_pct,
            letter_grade=anat_grade,
            grade_point=anat_gp,
            credit_points=6 * anat_gp,
            is_pass=anat_pass,
            is_absent=False,
            grace_notes=f"{anat_grace} Grace Marks Awarded" if anat_grace > 0 else None,
            sub_components={
                "Applied Anatomy": {"obtained": round(anat_ea * 0.49, 1), "max": 37.0},
                "Applied Physiology": {"obtained": round(anat_ea * 0.51, 1), "max": 38.0}
            }
        ),
        "SOCI_PSYC": CourseEvaluationDetail(
            course_key="SOCI_PSYC",
            course_code="SOCI 115 & PSYC 120",
            course_title="Applied Sociology & Applied Psychology",
            credits=6,
            include_in_sgpa=True,
            is_english_or_elective=False,
            internal_marks=soci_ia,
            internal_max=25.0,
            internal_pass=(soci_ia >= 12.5),
            external_marks=soci_ea,
            external_max=75.0,
            external_pass=((soci_ea + soci_grace) >= 37.5),
            grace_awarded=soci_grace,
            effective_external=soci_ea + soci_grace,
            total_marks=soci_tot,
            total_max=100.0,
            aggregate_pass=soci_pass,
            percentage=soci_pct,
            letter_grade=soci_grade,
            grade_point=soci_gp,
            credit_points=6 * soci_gp,
            is_pass=soci_pass,
            is_absent=False,
            grace_notes=f"{soci_grace} Grace Marks Awarded" if soci_grace > 0 else None,
            sub_components={
                "Applied Sociology": {"obtained": round(soci_ea * 0.49, 1), "max": 37.0},
                "Applied Psychology": {"obtained": round(soci_ea * 0.51, 1), "max": 38.0}
            }
        ),
        "ENGL": CourseEvaluationDetail(
            course_key="ENGL",
            course_code="ENGL 101",
            course_title="Communicative English",
            credits=2,
            include_in_sgpa=False,
            is_english_or_elective=True,
            internal_marks=engl_ia,
            internal_max=25.0,
            internal_pass=(engl_ia >= 10.0),
            external_marks=engl_ea,
            external_max=25.0,
            external_pass=((engl_ea + engl_grace) >= 10.0),
            grace_awarded=engl_grace,
            effective_external=engl_ea + engl_grace,
            total_marks=engl_tot,
            total_max=50.0,
            aggregate_pass=engl_pass,
            percentage=engl_pct,
            letter_grade=engl_grade,
            grade_point=engl_gp,
            credit_points=2 * engl_gp,
            is_pass=engl_pass,
            is_absent=False,
            grace_notes=None,
            sub_components={}
        )
    }

    grand_total = round(anat_tot + soci_tot + engl_tot, 2)
    overall_pct = round((grand_total / 250.0) * 100.0, 2)
    total_credit_score = (6 * anat_gp) + (6 * soci_gp)
    total_sgpa_credits = 12

    failed_courses = []
    if not anat_pass: failed_courses.append("Applied Anatomy & Applied Physiology")
    if not soci_pass: failed_courses.append("Applied Sociology & Applied Psychology")
    if not engl_pass: failed_courses.append("Communicative English")

    sgpa = round(total_credit_score / 12.0, 2) if not failed_courses else 0.0
    total_grace = anat_grace + soci_grace + engl_grace

    return EvaluatedStudentRecord(
        roll_no=roll,
        enroll_no=enroll,
        student_name=name,
        father_name=father,
        courses=courses,
        total_marks_obtained=grand_total,
        total_marks_max=250.0,
        overall_percentage=overall_pct,
        semester_credit_score=total_credit_score,
        total_sgpa_credits=total_sgpa_credits,
        sgpa=sgpa,
        result_status=result_status,
        failed_courses=failed_courses,
        total_grace=total_grace,
        grace_details={"ANAT_PHYS": anat_grace, "SOCI_PSYC": soci_grace} if total_grace > 0 else {},
        raw_remarks=remarks
    )


# 5 Certified Archetypes
ARCHETYPE_PASS = create_sample_student(
    roll="202501001",
    name="ANANYA VERMA",
    enroll="2025601",
    father="SHRI RAJESH VERMA",
    anat_ia=19.0, anat_ea=54.0, anat_grace=0.0,
    soci_ia=18.0, soci_ea=56.0, soci_grace=0.0,
    engl_ia=22.0, engl_ea=24.0, engl_grace=0.0,
    result_status="PASS",
    remarks="Grading Performance - Excellent"
)

ARCHETYPE_GRACE = create_sample_student(
    roll="202501015",
    name="RAHUL KUMAR",
    enroll="2025615",
    father="SHRI SANJAY KUMAR",
    anat_ia=17.0, anat_ea=35.5, anat_grace=2.0,
    soci_ia=16.0, soci_ea=42.0, soci_grace=0.0,
    engl_ia=18.0, engl_ea=18.0, engl_grace=0.0,
    result_status="PASS WITH 2 GRACE MARKS IN APPLIED ANATOMY & PHYSIOLOGY",
    remarks="Grading Performance - Above Average"
)

ARCHETYPE_FAIL = create_sample_student(
    roll="202501028",
    name="PRIYA SINGH",
    enroll="2025628",
    father="SHRI RAMESH SINGH",
    anat_ia=15.0, anat_ea=28.0, anat_grace=0.0,
    soci_ia=17.0, soci_ea=47.0, soci_grace=0.0,
    engl_ia=19.0, engl_ea=19.0, engl_grace=0.0,
    result_status="FAIL IN APPLIED ANATOMY & APPLIED PHYSIOLOGY",
    remarks="Grading Performance - Fail"
)

ARCHETYPE_DISTINCTION = create_sample_student(
    roll="202501035",
    name="SHREYA MISHRA",
    enroll="2025635",
    father="SHRI ALOK MISHRA",
    anat_ia=23.0, anat_ea=69.0, anat_grace=0.0,
    soci_ia=22.0, soci_ea=67.0, soci_grace=0.0,
    engl_ia=24.0, engl_ea=24.0, engl_grace=0.0,
    result_status="PASS",
    remarks="Grading Performance - Outstanding"
)

ARCHETYPE_BORDERLINE = create_sample_student(
    roll="202501050",
    name="VIKAS YADAV",
    enroll="2025650",
    father="SHRI RAMESH YADAV",
    anat_ia=13.0, anat_ea=38.0, anat_grace=0.0,
    soci_ia=13.0, soci_ea=37.5, soci_grace=0.0,
    engl_ia=11.0, engl_ea=11.5, engl_grace=0.0,
    result_status="PASS",
    remarks="Grading Performance - Average"
)


def get_5_debug_categories(uploaded_students: Optional[List[EvaluatedStudentRecord]] = None) -> List[Dict[str, Any]]:
    """
    Selects 5 representative candidates (Pass, Grace, Fail, Distinction, Borderline).
    Prefers actual uploaded students; fills any missing category with certified archetypes.
    """
    selected_pass = None
    selected_grace = None
    selected_fail = None
    selected_distinction = None
    selected_borderline = None

    if uploaded_students:
        for s in uploaded_students:
            is_p = "PASS" in s.result_status.upper()
            has_g = (s.total_grace or 0) > 0

            # Distinction: percentage >= 75% or SGPA >= 8.0
            if is_p and not has_g and s.overall_percentage >= 75.0:
                if not selected_distinction or s.overall_percentage > selected_distinction.overall_percentage:
                    selected_distinction = s

            # Grace
            if has_g and is_p and not selected_grace:
                selected_grace = s

            # Fail
            if not is_p and not selected_fail:
                selected_fail = s

            # Borderline: closest to 50%
            if is_p and 50.0 <= s.overall_percentage <= 55.0 and not selected_borderline:
                selected_borderline = s

            # Regular clean Pass
            if is_p and not has_g and 55.0 < s.overall_percentage < 75.0 and not selected_pass:
                selected_pass = s

    return [
        {
            "category": "PASS",
            "category_title": "1. Clear Regular Pass",
            "badge_color": "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
            "description": "Candidate cleared all theory, practical, and internal assessments above the 50% threshold without requiring grace marks.",
            "source": "Uploaded Dataset" if (selected_pass and uploaded_students) else "INC Certified Standard Archetype",
            "student": selected_pass or ARCHETYPE_PASS,
            "telemetry": {
                "rule": "INC Gazette 2021: Theory & IA >= 50%",
                "grace_used": (selected_pass or ARCHETYPE_PASS).total_grace or 0.0,
                "sgpa": (selected_pass or ARCHETYPE_PASS).sgpa or 0.0,
                "percentage": (selected_pass or ARCHETYPE_PASS).overall_percentage,
                "verdict": "Clear Pass - Eligible for Standard Marksheet"
            }
        },
        {
            "category": "GRACE",
            "category_title": "2. Pass With Grace Marks",
            "badge_color": "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
            "description": "Candidate scored slightly below 50% in theory and was awarded statutory grace marks (<= 5 marks) as per INC Gazette Section 7.",
            "source": "Uploaded Dataset" if (selected_grace and uploaded_students) else "INC Certified Standard Archetype",
            "student": selected_grace or ARCHETYPE_GRACE,
            "telemetry": {
                "rule": "INC Gazette Sec 7: Max 5 Grace Marks across max 2 courses",
                "grace_used": (selected_grace or ARCHETYPE_GRACE).total_grace or 2.0,
                "sgpa": (selected_grace or ARCHETYPE_GRACE).sgpa or 0.0,
                "percentage": (selected_grace or ARCHETYPE_GRACE).overall_percentage,
                "verdict": "Pass With Grace - Marksheet displays official grace notation"
            }
        },
        {
            "category": "FAIL",
            "category_title": "3. Fail / Re-appear",
            "badge_color": "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950 dark:text-rose-300 dark:border-rose-800",
            "description": "Candidate failed one or more courses where marks were below 50% and deficit exceeded maximum allowable 5 grace marks.",
            "source": "Uploaded Dataset" if (selected_fail and uploaded_students) else "INC Certified Standard Archetype",
            "student": selected_fail or ARCHETYPE_FAIL,
            "telemetry": {
                "rule": "INC Regulation: Deficit exceeds 5.0 marks cap; candidate must re-appear",
                "grace_used": (selected_fail or ARCHETYPE_FAIL).total_grace or 0.0,
                "sgpa": None,
                "percentage": (selected_fail or ARCHETYPE_FAIL).overall_percentage,
                "verdict": "Re-appear Required - Marksheet displays FAIL with subject codes"
            }
        },
        {
            "category": "DISTINCTION",
            "category_title": "4. Distinction / High Scorer",
            "badge_color": "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800",
            "description": "Top academic achiever scoring >= 75% aggregate marks with Grade Points 9–10 ('A+' / 'O') and SGPA >= 8.0.",
            "source": "Uploaded Dataset" if (selected_distinction and uploaded_students) else "INC Certified Standard Archetype",
            "student": selected_distinction or ARCHETYPE_DISTINCTION,
            "telemetry": {
                "rule": "SGPGIMS Honours Criterion: Aggregate >= 75% without grace marks",
                "grace_used": 0.0,
                "sgpa": (selected_distinction or ARCHETYPE_DISTINCTION).sgpa or 0.0,
                "percentage": (selected_distinction or ARCHETYPE_DISTINCTION).overall_percentage,
                "verdict": "Distinction Achieved - Outstanding Academic Performance"
            }
        },
        {
            "category": "BORDERLINE",
            "category_title": "5. Borderline Passing Candidate",
            "badge_color": "bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-800",
            "description": "Candidate on exact passing boundary (50.0% aggregate) demonstrating numerical precision and cutoff boundaries.",
            "source": "Uploaded Dataset" if (selected_borderline and uploaded_students) else "INC Certified Standard Archetype",
            "student": selected_borderline or ARCHETYPE_BORDERLINE,
            "telemetry": {
                "rule": "Boundary Condition: Aggregate exactly satisfies 50.0% cutoff",
                "grace_used": (selected_borderline or ARCHETYPE_BORDERLINE).total_grace or 0.0,
                "sgpa": (selected_borderline or ARCHETYPE_BORDERLINE).sgpa or 0.0,
                "percentage": (selected_borderline or ARCHETYPE_BORDERLINE).overall_percentage,
                "verdict": "Borderline Pass - Clean Pass at Cutoff"
            }
        }
    ]
