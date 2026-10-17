"""
Core Calculation, Grace Logic & Evaluation Rules Engine
Phase 2: Evaluates normalized StudentRecord data from Phase 1B compliant with:
- Indian Nursing Council (INC) Gazette Regulations
- SGPGIMS Lucknow Regulations (College Code: 1313)
- INC 10-Point Grading Scale & SGPA Credit Matrix

Branding: VidyaMarksheet by VidyaLabs
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Union
from pydantic import BaseModel, Field

from backend.grading import calculate_inc_grade, compute_sgpa
from backend.schemas.canonical_models import StudentRecord, format_numeric_token
from backend.schemas.course_schemas import SEMESTER_DEFINITIONS


# Standard Course Meta mapping for Semester 1 Canonical Keys
CANONICAL_SEM1_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "ANAT_PHYS": {
        "course_code": "ANAT 105 & PHYS 110",
        "course_title": "Applied Anatomy & Applied Physiology",
        "subject_name": "APPLIED ANATOMY & APPLIED PHYSIOLOGY",
        "credits": 6,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "SOCI_PSYC": {
        "course_code": "SOCI 115 & PSYC 120",
        "course_title": "Applied Sociology & Applied Psychology",
        "subject_name": "APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY",
        "credits": 6,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "ENGL": {
        "course_code": "ENGL 101",
        "course_title": "Communicative English",
        "subject_name": "COMMUNICATIVE ENGLISH",
        "credits": 2,
        "ia_max": 25.0,
        "ia_min_pass": 10.0,
        "ea_max": 25.0,
        "ea_min_pass": 10.0,
        "total_max": 50.0,
        "min_pass_pct": 40.0,
        "is_english_or_elective": True,
        "include_in_sgpa": False,
    }
}


# Standard Course Meta mapping for Semester 2 Canonical Keys
CANONICAL_SEM2_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "BIOC_NUTR": {
        "course_code": "BIOC 135 & NUTR 140",
        "course_title": "Applied Biochemistry & Applied Nutrition & Dietetics",
        "subject_name": "APPLIED BIOCHEMISTRY & APPLIED NUTRITION & DIETETICS",
        "credits": 5,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "sec_a_max": 25.0,
        "sec_b_max": 50.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "NNF_THEORY": {
        "course_code": "N-NF (I & II) 125",
        "course_title": "Nursing Foundation I & II (Theory)",
        "subject_name": "NURSING FOUNDATION I & II (THEORY)",
        "credits": 12,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "NNF_PRACT": {
        "course_code": "N-NF (I & II) 125",
        "course_title": "Nursing Foundation I & II (Practical)",
        "subject_name": "NURSING FOUNDATION I & II (PRACTICAL)",
        "credits": 11,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "HNIT": {
        "course_code": "HNIT 145",
        "course_title": "Health/ Nursing Informatics & Technology",
        "subject_name": "HEALTH/ NURSING INFORMATICS & TECHNOLOGY",
        "credits": 3,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 25.0,
        "ea_min_pass": 12.5,
        "total_max": 50.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    }
}


# Standard Course Meta mapping for Semester 3 Canonical Keys
CANONICAL_SEM3_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "MICR": {
        "course_code": "MICR 201",
        "course_title": "Applied Microbiology and Infection Control including Safety",
        "subject_name": "APPLIED MICROBIOLOGY & INFECTION CONTROL",
        "credits": 3,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "AHN_I_THEORY": {
        "course_code": "N-AHN (I) 215",
        "course_title": "Adult Health Nursing I with Integrated Pathophysiology (Theory)",
        "subject_name": "ADULT HEALTH NURSING I (THEORY)",
        "credits": 7,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "AHN_I_PRACT": {
        "course_code": "N-AHN (I) 215",
        "course_title": "Adult Health Nursing I with Integrated Pathophysiology (Practical)",
        "subject_name": "ADULT HEALTH NURSING I (PRACTICAL)",
        "credits": 7,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    }
}


# Standard Course Meta mapping for Semester 4 Canonical Keys
CANONICAL_SEM4_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "PHAR_PATH": {
        "course_code": "PHAR 205 & PATH 210",
        "course_title": "Pharmacology (I & II) & Pathology (I & II) (including Genetics)",
        "subject_name": "PHARMACOLOGY, PATHOLOGY & GENETICS",
        "credits": 6,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "sec_a_max": 38.0,
        "sec_b_max": 25.0,
        "sec_c_max": 12.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "AHN_II_THEORY": {
        "course_code": "N-AHN (II) 225",
        "course_title": "Adult Health Nursing II with Integrated Pathophysiology (Theory)",
        "subject_name": "ADULT HEALTH NURSING II (THEORY)",
        "credits": 7,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "AHN_II_PRACT": {
        "course_code": "N-AHN (II) 225",
        "course_title": "Adult Health Nursing II with Integrated Pathophysiology (Practical)",
        "subject_name": "ADULT HEALTH NURSING II (PRACTICAL)",
        "credits": 7,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "PROF": {
        "course_code": "PROF 230",
        "course_title": "Professionalism, Professional Values & Ethics including Bioethics",
        "subject_name": "PROFESSIONALISM, ETHICS AND PROFESSIONAL VALUES",
        "credits": 1,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 25.0,
        "ea_min_pass": 12.5,
        "total_max": 50.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    }
}


# Standard Course Meta mapping for Semester 5 Canonical Keys
CANONICAL_SEM5_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "COMH_I_THEORY": {
        "course_code": "N-COMH (I) 310",
        "course_title": "Community Health Nursing I including Environmental Science & Epidemiology (Theory)",
        "subject_name": "COMMUNITY HEALTH NURSING I (THEORY)",
        "credits": 5,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "EDUC": {
        "course_code": "N-EDUC 315",
        "course_title": "Educational Technology / Nursing Education",
        "subject_name": "EDUCATIONAL TECHNOLOGY / NURSING EDUCATION",
        "credits": 3,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "FORN": {
        "course_code": "N-FORN 320",
        "course_title": "Introduction to Forensic Nursing",
        "subject_name": "INTRODUCTION TO FORENSIC NURSING",
        "credits": 1,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 25.0,
        "ea_min_pass": 12.5,
        "total_max": 50.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "COMH_I_PRACT": {
        "course_code": "N-COMH (I) 310",
        "course_title": "Community Health Nursing I (Practical)",
        "subject_name": "COMMUNITY HEALTH NURSING I (PRACTICAL)",
        "credits": 2,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    }
}


# Standard Course Meta mapping for Semester 6 Canonical Keys
CANONICAL_SEM6_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "CHN_THEORY": {
        "course_code": "N-CHN (I & II) 301",
        "course_title": "Child Health Nursing (I & II) (Theory)",
        "subject_name": "CHILD HEALTH NURSING (I & II) (THEORY)",
        "credits": 5,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "MHN_THEORY": {
        "course_code": "N-MHN (I & II) 305",
        "course_title": "Mental Health Nursing (I & II) (Theory)",
        "subject_name": "MENTAL HEALTH NURSING (I & II) (THEORY)",
        "credits": 5,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "NMLE": {
        "course_code": "NMLE 330",
        "course_title": "Nursing Management & Leadership",
        "subject_name": "NURSING MANAGEMENT & LEADERSHIP",
        "credits": 4,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "CHN_PRACT": {
        "course_code": "N-CHN (I & II) 301",
        "course_title": "Child Health Nursing (I & II) (Practical)",
        "subject_name": "CHILD HEALTH NURSING (I & II) (PRACTICAL)",
        "credits": 4,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "MHN_PRACT": {
        "course_code": "N-MHN (I & II) 305",
        "course_title": "Mental Health Nursing (I & II) (Practical)",
        "subject_name": "MENTAL HEALTH NURSING (I & II) (PRACTICAL)",
        "credits": 3,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    }
}


# Standard Course Meta mapping for Semester 7 Canonical Keys
CANONICAL_SEM7_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "COMH_II_THEORY": {
        "course_code": "N-COMH (II) 401",
        "course_title": "Community Health Nursing II (Theory)",
        "subject_name": "COMMUNITY HEALTH NURSING II (THEORY)",
        "credits": 5,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "NRST": {
        "course_code": "NRST 405",
        "course_title": "Nursing Research & Statistics",
        "subject_name": "NURSING RESEARCH & STATISTICS",
        "credits": 4,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "sec_a_max": 55.0,
        "sec_b_max": 20.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "OBGN_THEORY": {
        "course_code": "N-MIDW/OBGN (I & II) 335 & 410",
        "course_title": "Midwifery/Obstetrics and Gynaecology (OBG) Nursing I & II (Theory)",
        "subject_name": "MIDWIFERY/OBSTETRICS AND GYNAECOLOGY (OBG) NURSING I & II (THEORY)",
        "credits": 6,
        "ia_max": 25.0,
        "ia_min_pass": 12.5,
        "ea_max": 75.0,
        "ea_min_pass": 37.5,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "OBGN_PRACT": {
        "course_code": "N-MIDW/OBGN (I & II) 335 & 410",
        "course_title": "Midwifery/Obstetrics and Gynaecology (OBG) Nursing I & II (Practical)",
        "subject_name": "MIDWIFERY/OBSTETRICS AND GYNAECOLOGY (OBG) NURSING I & II (PRACTICAL)",
        "credits": 9,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "COMH_II_PRACT": {
        "course_code": "N-COMH (II) 401",
        "course_title": "Community Health Nursing II (Practical)",
        "subject_name": "COMMUNITY HEALTH NURSING II (PRACTICAL)",
        "credits": 2,
        "ia_max": 50.0,
        "ia_min_pass": 25.0,
        "ea_max": 50.0,
        "ea_min_pass": 25.0,
        "total_max": 100.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
}


# Standard Course Meta mapping for Semester 8 Canonical Keys
CANONICAL_SEM8_COURSE_METADATA: Dict[str, Dict[str, Any]] = {
    "COMPETENCY": {
        "course_code": "INTE 415, 420, 425, 430 & 435",
        "course_title": "Competency Assessment (Internship / Intensive Clinical Practicum)",
        "subject_name": "COMPETENCY ASSESSMENT (INTERNSHIP / INTENSIVE CLINICAL PRACTICUM)",
        "credits": 12,
        "ia_max": 100.0,
        "ia_min_pass": 50.0,
        "ea_max": 100.0,
        "ea_min_pass": 50.0,
        "total_max": 200.0,
        "min_pass_pct": 50.0,
        "is_english_or_elective": False,
        "include_in_sgpa": True,
    },
    "ELECTIVE_3": {
        "course_code": "Elective-3",
        "course_title": "Scientific Writing Skills (Elective)",
        "subject_name": "SCIENTIFIC WRITING SKILLS (ELECTIVE)",
        "credits": 1,
        "ia_max": 0.0,
        "ia_min_pass": 0.0,
        "ea_max": 100.0,
        "ea_min_pass": 40.0,
        "total_max": 100.0,
        "min_pass_pct": 40.0,
        "is_english_or_elective": True,
        "include_in_sgpa": False,
    },
}


ALL_SEMESTER_CANONICAL_METADATA: Dict[int, Dict[str, Dict[str, Any]]] = {
    1: CANONICAL_SEM1_COURSE_METADATA,
    2: CANONICAL_SEM2_COURSE_METADATA,
    3: CANONICAL_SEM3_COURSE_METADATA,
    4: CANONICAL_SEM4_COURSE_METADATA,
    5: CANONICAL_SEM5_COURSE_METADATA,
    6: CANONICAL_SEM6_COURSE_METADATA,
    7: CANONICAL_SEM7_COURSE_METADATA,
    8: CANONICAL_SEM8_COURSE_METADATA,
}


STATUTORY_SGPA_CREDITS: Dict[int, int] = {
    1: 12,
    2: 31,
    3: 17,
    4: 21,
    5: 11,
    6: 21,
    7: 26,
    8: 12,
}


class SemesterEvaluationResult(dict):
    """
    Standardized semester evaluation result container.
    Supports both dictionary access (res['sgpa']) and attribute access (res.sgpa).
    """
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'SemesterEvaluationResult' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def format_grace_string(val: float) -> str:
    """
    Formats grace value into clean representation conforming to [X.X]:
    e.g. 2.5 -> '2.5', 0.5 -> '0.5', 2.0 -> '2.0' (or '2' if integer).
    """
    if round(val, 2) != int(val):
        return f"{round(val, 2):g}"
    return f"{val:.1f}"


class CourseEvaluationDetail(BaseModel):
    course_key: str = Field(..., description="Canonical key e.g. ANAT_PHYS, SOCI_PSYC, ENGL")
    course_code: str = Field(..., description="Official Course Code")
    course_title: str = Field(..., description="Official Course Title")
    credits: int
    include_in_sgpa: bool
    is_english_or_elective: bool

    # Component Marks
    internal_marks: Union[int, float, str]
    internal_max: float
    internal_pass: bool

    external_marks: Union[int, float, str]
    external_max: float
    external_pass: bool
    grace_awarded: float = 0.0
    effective_external: Union[int, float, str]

    total_marks: Union[int, float, str]
    total_max: float
    aggregate_pass: bool

    percentage: float
    letter_grade: str
    grade_point: int
    credit_points: float

    is_pass: bool
    is_absent: bool = False
    is_exempted: bool = False
    grace_notes: Optional[str] = None
    sub_components: Dict[str, Any] = Field(default_factory=dict)


class EvaluatedStudentRecord(BaseModel):
    roll_no: str
    enroll_no: str
    student_name: str
    father_name: str
    courses: Dict[str, CourseEvaluationDetail]

    # Grand Aggregate
    total_marks_obtained: float
    total_marks_max: float
    overall_percentage: float

    # SGPA Metrics
    semester_credit_score: float
    total_sgpa_credits: int
    sgpa: float

    # Result Status
    result_status: str = Field(..., description="PASS, FAIL, or PASS WITH [X.X] GRACE MARKS IN [SUBJECT]")
    failed_courses: List[str] = Field(default_factory=list)
    total_grace: float = 0.0
    grace_details: Dict[str, float] = Field(default_factory=dict)
    raw_remarks: Optional[str] = None


class EvaluationBatchResult(BaseModel):
    success: bool
    branding: str = "VidyaMarksheet by VidyaLabs"
    total_candidates: int
    passed_count: int
    failed_count: int
    grace_awarded_count: int
    results: List[EvaluatedStudentRecord]
    warnings: List[str] = Field(default_factory=list)


def parse_numeric_score(val: Any) -> Tuple[Optional[float], bool]:
    """Helper to convert cell values to numeric float or flag absent."""
    if val is None or val == "":
        return 0.0, False
    if isinstance(val, (int, float)):
        return float(val), False
    s = str(val).strip()
    if s.upper() in ["AB", "ABSENT"]:
        return None, True
    if s == "-":
        return 0.0, False
    try:
        return float(s), False
    except ValueError:
        return 0.0, False


class EvaluationEngine:
    """
    Core Evaluation Engine for VidyaMarksheet.
    Evaluates StudentRecord items according to INC regulations:
    1. Passing thresholds (IA >= 50%, EA >= 50%, Total >= 50%, English/Electives >= 40%)
    2. Grace Marks Engine (Pre-specified verification and Auto-Grace mode)
    3. 10-Point Grade & SGPA calculation.
    """

    def __init__(self, semester_number: int = 1, auto_grace: bool = False):
        self.semester_number = semester_number
        self.auto_grace = auto_grace
        self.semester_def = SEMESTER_DEFINITIONS.get(semester_number)

    def evaluate_student(self, student: StudentRecord) -> EvaluatedStudentRecord:
        """Evaluates a single StudentRecord."""
        raw_courses = student.courses

        # Determine active metadata dictionary based on semester or courses
        active_sem = self.semester_number
        if any(k in raw_courses for k in ["COMPETENCY"]):
            active_sem = 8
        elif any(k in raw_courses for k in ["COMH_II_THEORY", "NRST", "OBGN_THEORY", "OBGN_PRACT", "COMH_II_PRACT"]):
            active_sem = 7
        elif any(k in raw_courses for k in ["CHN_THEORY", "MHN_THEORY", "NMLE", "CHN_PRACT", "MHN_PRACT"]):
            active_sem = 6
        elif any(k in raw_courses for k in ["COMH_I_THEORY", "EDUC", "FORN", "COMH_I_PRACT"]):
            active_sem = 5
        elif any(k in raw_courses for k in ["PHAR_PATH", "AHN_II_THEORY", "AHN_II_PRACT", "PROF"]):
            active_sem = 4
        elif any(k in raw_courses for k in ["MICR", "AHN_I_THEORY", "AHN_I_PRACT"]):
            active_sem = 3
        elif any(k in raw_courses for k in ["BIOC_NUTR", "NNF_THEORY", "NNF_PRACT", "HNIT"]):
            active_sem = 2
        elif any(k in raw_courses for k in ["ANAT_PHYS", "SOCI_PSYC", "ENGL"]):
            active_sem = 1

        meta_dict = ALL_SEMESTER_CANONICAL_METADATA.get(active_sem, CANONICAL_SEM1_COURSE_METADATA)

        sem_def = SEMESTER_DEFINITIONS.get(active_sem) or self.semester_def

        # 1. Parse and extract raw course data
        course_candidates: Dict[str, Dict[str, Any]] = {}
        for c_key, c_meta in meta_dict.items():
            if c_key in raw_courses:
                c_data = raw_courses[c_key]
                course_candidates[c_key] = self._parse_course_data(c_key, c_data, c_meta)

        # 2. Check and Apply Grace Logic (Pre-specified verification or Auto-Grace)
        grace_info = self._process_grace_logic(course_candidates, student.raw_remarks)

        # 3. Finalize course evaluations with INC grades
        evaluated_courses: Dict[str, CourseEvaluationDetail] = {}
        failed_courses: List[str] = []
        total_obtained = 0.0
        total_max = 0.0

        for c_key, c_eval in course_candidates.items():
            evaluated_detail = self._build_course_evaluation(c_eval)
            evaluated_courses[c_key] = evaluated_detail

            if isinstance(evaluated_detail.total_marks, (int, float)):
                total_obtained += float(evaluated_detail.total_marks)
            total_max += evaluated_detail.total_max

            if not evaluated_detail.is_pass:
                failed_courses.append(evaluated_detail.course_title)

        # 4. SGPA & Credit Calculation
        credit_points_sum = 0.0
        total_applicable_credits = 0

        for c_key, c_eval in evaluated_courses.items():
            if c_eval.include_in_sgpa and c_eval.credits > 0:
                total_applicable_credits += c_eval.credits
                credit_points_sum += c_eval.credit_points

        # Target applicable credits from semester catalog
        expected_sgpa_credits = (
            sem_def.sgpa_eligible_credits if sem_def else total_applicable_credits
        )
        final_sgpa_credits = max(expected_sgpa_credits, total_applicable_credits, 1)
        sgpa = round(credit_points_sum / final_sgpa_credits, 2)

        # Overall Percentage
        overall_pct = round((total_obtained / total_max) * 100.0, 2) if total_max > 0 else 0.0

        # 5. Format Result Status
        if len(failed_courses) > 0:
            result_status = "FAIL"
        elif grace_info["total_grace"] > 0:
            grace_courses_str = " & ".join(grace_info["grace_courses"])
            grace_str = format_grace_string(grace_info["total_grace"])
            result_status = f"PASS WITH {grace_str} GRACE MARKS IN {grace_courses_str}"
        else:
            result_status = "PASS"

        return EvaluatedStudentRecord(
            roll_no=student.roll_no,
            enroll_no=student.enroll_no,
            student_name=student.student_name,
            father_name=student.father_name,
            courses=evaluated_courses,
            total_marks_obtained=round(total_obtained, 2),
            total_marks_max=round(total_max, 2),
            overall_percentage=overall_pct,
            semester_credit_score=round(credit_points_sum, 2),
            total_sgpa_credits=final_sgpa_credits,
            sgpa=sgpa,
            result_status=result_status,
            failed_courses=failed_courses,
            total_grace=grace_info["total_grace"],
            grace_details=grace_info["grace_details"],
            raw_remarks=student.raw_remarks or result_status
        )

    def evaluate_batch(self, students: List[StudentRecord]) -> EvaluationBatchResult:
        """Evaluates an array of StudentRecord objects."""
        results = [self.evaluate_student(s) for s in students]

        passed = sum(1 for r in results if "PASS" in r.result_status)
        failed = sum(1 for r in results if r.result_status == "FAIL")
        grace_count = sum(1 for r in results if r.total_grace > 0 and "PASS" in r.result_status)

        return EvaluationBatchResult(
            success=True,
            branding="VidyaMarksheet by VidyaLabs",
            total_candidates=len(students),
            passed_count=passed,
            failed_count=failed,
            grace_awarded_count=grace_count,
            results=results
        )

    def _parse_course_data(self, c_key: str, c_data: Any, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Parses raw course dict into numeric scores."""
        if hasattr(c_data, "dict"):
            c_dict = c_data.dict()
        elif isinstance(c_data, dict):
            c_dict = c_data
        else:
            c_dict = {}

        int_raw = c_dict.get("int_marks")
        ex_raw = c_dict.get("ex_total") or c_dict.get("ex_marks")
        grace_raw = c_dict.get("grace", 0)

        int_score, int_ab = parse_numeric_score(int_raw)
        ex_score, ex_ab = parse_numeric_score(ex_raw)
        grace_score, _ = parse_numeric_score(grace_raw)

        is_exempt = (
            bool(c_dict.get("is_exempted", False)) or
            c_dict.get("letter_grade") == "Ex." or
            str(int_raw).strip().upper() in ["EX.", "EX", "X", "EXEMPTED"] or
            str(ex_raw).strip().upper() in ["EX.", "EX", "X", "EXEMPTED"]
        )

        sub_components = {}
        if "ex_part_a" in c_dict:
            pa_score, pa_ab = parse_numeric_score(c_dict["ex_part_a"])
            sec_a_name = (
                "Applied Biochemistry" if c_key == "BIOC_NUTR"
                else ("Pharmacology (I & II)" if c_key == "PHAR_PATH"
                else ("Microbiology" if c_key == "MICR"
                else ("Nursing Research" if c_key == "NRST"
                else "Section A")))
            )
            sub_components[sec_a_name] = format_numeric_token("Ab" if pa_ab else pa_score)
        if "ex_part_b" in c_dict:
            pb_score, pb_ab = parse_numeric_score(c_dict["ex_part_b"])
            sec_b_name = (
                "Applied Nutrition & Dietetics" if c_key == "BIOC_NUTR"
                else ("Pathology (I & II)" if c_key == "PHAR_PATH"
                else ("Infection Control" if c_key == "MICR"
                else ("Statistics" if c_key == "NRST"
                else "Section B")))
            )
            sub_components[sec_b_name] = format_numeric_token("Ab" if pb_ab else pb_score)
        if "ex_part_c" in c_dict:
            pc_score, pc_ab = parse_numeric_score(c_dict["ex_part_c"])
            sec_c_name = "Genetics" if c_key == "PHAR_PATH" else "Section C"
            sub_components[sec_c_name] = format_numeric_token("Ab" if pc_ab else pc_score)

        return {
            "meta": meta,
            "int_score": int_score,
            "int_ab": int_ab,
            "ex_score": ex_score,
            "ex_ab": ex_ab,
            "grace": grace_score or 0.0,
            "effective_external": ex_score,
            "sub_components": sub_components,
            "applied_grace": 0.0,
            "grace_rejected": False,
            "grace_reason": None,
            "is_exempted": is_exempt,
            "raw_total": c_dict.get("total"),
        }

    def _process_grace_logic(
        self,
        course_candidates: Dict[str, Dict[str, Any]],
        raw_remarks: Optional[str]
    ) -> Dict[str, Any]:
        """
        Implements Requirement 2:
        - If pre-specified grace is present:
            1. Post-grace external marks must meet exact 50% pass threshold (e.g. 35 + 2.5 = 37.5).
            2. Total grace marks awarded must not exceed 5.0 marks total.
        - If auto-grace mode enabled:
            1. Internal Assessment >= 12.5 (>= 50%).
            2. External is between 32.5 and 37.0 (deficit <= 5.0).
            3. Award required delta (37.5 - external_marks) IF student passed all other subjects.
        """
        grace_details: Dict[str, float] = {}
        grace_courses: List[str] = []

        total_prespecified_grace = sum(c["grace"] for c in course_candidates.values())

        # If grace was not explicitly in course cell but noted in raw_remarks (e.g. 'Pass with 1.5 Grace Mark in Nursing Research & Statistics')
        if total_prespecified_grace == 0 and raw_remarks:
            m = re.search(r'pass\s+with\s+([\d.]+)\s+grace\s+marks?\s+in\s+([^,;\n]+)', raw_remarks, re.I)
            if m:
                g_val = float(m.group(1))
                subj_str = m.group(2).strip().upper()
                for c_key, c in course_candidates.items():
                    c_title = c["meta"].get("course_title", "").upper()
                    c_subj = c["meta"].get("subject_name", "").upper()
                    # 1. Exact or substring match
                    if (subj_str in c_subj or c_subj in subj_str or 
                        subj_str in c_title or c_title in subj_str):
                        c["grace"] = g_val
                        total_prespecified_grace = g_val
                        break
                    # 2. Distinctive non-generic token match (exclude common words like NURSING)
                    stopwords = {"NURSING", "THEORY", "PRACTICAL", "AND", "WITH", "FOR", "THE", "INCL"}
                    distinctive_tokens = [w for w in re.split(r'[^A-Z0-9]+', subj_str) if len(w) > 3 and w not in stopwords]
                    if distinctive_tokens and all(tok in c_subj or tok in c_title for tok in distinctive_tokens):
                        c["grace"] = g_val
                        total_prespecified_grace = g_val
                        break

        # CASE 1: Pre-specified grace from Examination Cell
        if total_prespecified_grace > 0:
            is_valid_grace = True
            rejection_reason = None

            # Verify total grace does not exceed 5.0 marks
            if total_prespecified_grace > 5.0:
                is_valid_grace = False
                rejection_reason = f"Total grace ({total_prespecified_grace}) exceeds maximum INC limit of 5.0 marks."

            for c_key, c in course_candidates.items():
                g_val = c["grace"]
                if g_val > 0:
                    meta = c["meta"]
                    post_grace_external = (c["ex_score"] or 0.0) + g_val
                    pass_threshold = meta["ea_min_pass"]  # 37.5

                    # Verify post-grace external marks meet 50% pass threshold (37.5)
                    if post_grace_external < pass_threshold:
                        is_valid_grace = False
                        rejection_reason = (
                            f"Post-grace external marks ({post_grace_external}) in {meta['subject_name']} "
                            f"do not meet 50% pass threshold ({pass_threshold})."
                        )

            if is_valid_grace:
                for c_key, c in course_candidates.items():
                    if c["grace"] > 0:
                        c["applied_grace"] = c["grace"]
                        c["effective_external"] = round((c["ex_score"] or 0.0) + c["applied_grace"], 2)
                        grace_details[c_key] = c["applied_grace"]
                        grace_courses.append(c["meta"]["subject_name"])
            else:
                for c_key, c in course_candidates.items():
                    if c["grace"] > 0:
                        c["grace_rejected"] = True
                        c["grace_reason"] = rejection_reason

            return {
                "total_grace": sum(grace_details.values()),
                "grace_details": grace_details,
                "grace_courses": grace_courses
            }

        # CASE 2: Auto-Grace Calculation Mode
        if self.auto_grace:
            # Check passing status of each course without grace
            unpassed_courses: List[str] = []
            for c_key, c in course_candidates.items():
                meta = c["meta"]
                int_sc = c["int_score"] or 0.0
                ex_sc = c["ex_score"] or 0.0
                tot_sc = int_sc + ex_sc

                int_pass = not c["int_ab"] and int_sc >= meta["ia_min_pass"]
                ex_pass = not c["ex_ab"] and ex_sc >= meta["ea_min_pass"]
                tot_pass = tot_sc >= (meta["min_pass_pct"] / 100.0) * meta["total_max"]

                if not (int_pass and ex_pass and tot_pass):
                    unpassed_courses.append(c_key)

            # Auto-grace rule: eligible if exactly 1 subject is failing due to external deficit <= 5.0
            if len(unpassed_courses) == 1:
                failing_key = unpassed_courses[0]
                fc = course_candidates[failing_key]
                meta = fc["meta"]

                int_sc = fc["int_score"] or 0.0
                ex_sc = fc["ex_score"] or 0.0

                # Conditions: Internal >= 12.5 and External between 32.5 and 37.0 (deficit <= 5.0)
                if int_sc >= meta["ia_min_pass"] and 32.5 <= ex_sc < meta["ea_min_pass"]:
                    grace_needed = round(meta["ea_min_pass"] - ex_sc, 2)
                    if grace_needed <= 5.0:
                        fc["applied_grace"] = grace_needed
                        fc["effective_external"] = round(ex_sc + grace_needed, 2)
                        grace_details[failing_key] = grace_needed
                        grace_courses.append(meta["subject_name"])

            return {
                "total_grace": sum(grace_details.values()),
                "grace_details": grace_details,
                "grace_courses": grace_courses
            }

        return {
            "total_grace": 0.0,
            "grace_details": {},
            "grace_courses": []
        }

    def _build_course_evaluation(self, c_data: Dict[str, Any]) -> CourseEvaluationDetail:
        """Evaluates thresholds, INC grade, grade points, and credits for a single course."""
        meta = c_data["meta"]
        if c_data.get("is_exempted"):
            return CourseEvaluationDetail(
                course_key=meta["course_code"],
                course_code=meta["course_code"],
                course_title=meta["course_title"],
                credits=meta["credits"],
                include_in_sgpa=False,
                is_english_or_elective=meta["is_english_or_elective"],
                internal_marks="Ex.",
                internal_max=meta["ia_max"],
                internal_pass=True,
                external_marks="Ex.",
                external_max=meta["ea_max"],
                external_pass=True,
                grace_awarded=0.0,
                effective_external="Ex.",
                total_marks=format_numeric_token(c_data.get("raw_total") or "Ex."),
                total_max=meta["total_max"],
                aggregate_pass=True,
                percentage=0.0,
                letter_grade="Ex.",
                grade_point=0,
                credit_points=0.0,
                is_pass=True,
                is_absent=False,
                is_exempted=True,
                grace_notes=None,
                sub_components=c_data["sub_components"]
            )

        int_sc = c_data["int_score"] or 0.0
        ex_eff = c_data["effective_external"] or 0.0
        applied_grace = c_data["applied_grace"]
        is_absent = c_data["int_ab"] or c_data["ex_ab"]

        effective_total = round(int_sc + ex_eff, 2) if not is_absent else 0.0

        # Threshold checks
        ia_pass = not c_data["int_ab"] and int_sc >= meta["ia_min_pass"]
        ea_pass = not c_data["ex_ab"] and ex_eff >= meta["ea_min_pass"]
        total_pass_threshold = (meta["min_pass_pct"] / 100.0) * meta["total_max"]
        agg_pass = not is_absent and effective_total >= total_pass_threshold

        # If grace was rejected or absent or any threshold failed
        course_is_pass = (
            not is_absent and
            not c_data.get("grace_rejected", False) and
            ia_pass and
            ea_pass and
            agg_pass
        )

        has_failed_threshold = not course_is_pass and not is_absent

        # Calculate INC 10-Point Grade
        grade_res = calculate_inc_grade(
            obtained_marks=effective_total if not is_absent else None,
            max_marks=meta["total_max"],
            is_english_or_elective=meta["is_english_or_elective"],
            is_absent=is_absent,
            has_failed_threshold=has_failed_threshold
        )

        credit_points = (
            round(meta["credits"] * grade_res.grade_point, 2)
            if (meta["include_in_sgpa"] and course_is_pass)
            else 0.0
        )

        grace_notes = None
        if applied_grace > 0:
            grace_notes = f"Awarded {format_grace_string(applied_grace)} grace marks in University Exam"
        elif c_data.get("grace_rejected"):
            grace_notes = f"Grace rejected: {c_data.get('grace_reason')}"

        return CourseEvaluationDetail(
            course_key=meta["course_code"],
            course_code=meta["course_code"],
            course_title=meta["course_title"],
            credits=meta["credits"],
            include_in_sgpa=meta["include_in_sgpa"],
            is_english_or_elective=meta["is_english_or_elective"],
            internal_marks=format_numeric_token("Ab" if c_data["int_ab"] else int_sc),
            internal_max=meta["ia_max"],
            internal_pass=ia_pass,
            external_marks=format_numeric_token("Ab" if c_data["ex_ab"] else (c_data["ex_score"] or 0)),
            external_max=meta["ea_max"],
            external_pass=ea_pass,
            grace_awarded=applied_grace,
            effective_external=format_numeric_token("Ab" if c_data["ex_ab"] else ex_eff),
            total_marks=format_numeric_token("Ab" if is_absent else effective_total),
            total_max=meta["total_max"],
            aggregate_pass=agg_pass,
            percentage=grade_res.percentage,
            letter_grade=grade_res.letter_grade,
            grade_point=grade_res.grade_point,
            credit_points=credit_points,
            is_pass=course_is_pass,
            is_absent=is_absent,
            grace_notes=grace_notes,
            sub_components=c_data["sub_components"]
        )


def evaluate_student_semester(
    registration_data: Any,
    course_catalog: Optional[Any] = None,
    semester_number: Optional[int] = None
) -> SemesterEvaluationResult:
    """
    Standardized In-App Re-Calculation Pipeline for B.Sc. Nursing Semesters 1 to 8.
    Compliant with INC Gazette Corrigendum (April 19, 2022 / No. 205).
    
    Ingestion Isolation Rule:
    Strictly calculates totals, percentages, grade points, letter grades, credit points,
    SGPA, and backlog queue using raw components ONLY. Never trusts pre-calculated totals
    or grades from sheets or incoming payloads.
    
    Statutory SGPA Credits:
      Sem 1: 12, Sem 2: 31, Sem 3: 17, Sem 4: 21,
      Sem 5: 11, Sem 6: 21, Sem 7: 26, Sem 8: 12
    """
    # 1. Demographic extraction
    if isinstance(registration_data, dict):
        roll_no = str(registration_data.get("roll_no") or "").strip()
        enroll_no = str(registration_data.get("enroll_no") or registration_data.get("enrollment_no") or "").strip()
        student_name = str(registration_data.get("student_name") or registration_data.get("name") or "").strip()
        father_name = str(registration_data.get("father_name") or "").strip()
        raw_remarks = registration_data.get("raw_remarks") or registration_data.get("remarks")
        courses_raw = registration_data.get("courses") or registration_data.get("course_marks") or {}
        inferred_sem = semester_number or registration_data.get("semester_number") or registration_data.get("semester")
    else:
        if hasattr(registration_data, "student") and registration_data.student:
            stu = registration_data.student
            roll_no = str(getattr(stu, "roll_no", "") or "").strip()
            enroll_no = str(getattr(stu, "enrollment_no", getattr(stu, "enroll_no", "")) or "").strip()
            student_name = str(getattr(stu, "name", getattr(stu, "student_name", "")) or "").strip()
            father_name = str(getattr(stu, "father_name", "") or "").strip()
        else:
            roll_no = str(getattr(registration_data, "roll_no", "") or "").strip()
            enroll_no = str(getattr(registration_data, "enroll_no", getattr(registration_data, "enrollment_no", "")) or "").strip()
            student_name = str(getattr(registration_data, "student_name", getattr(registration_data, "name", "")) or "").strip()
            father_name = str(getattr(registration_data, "father_name", "") or "").strip()

        raw_remarks = getattr(registration_data, "raw_remarks", getattr(registration_data, "remarks", None))
        courses_raw = getattr(registration_data, "courses", getattr(registration_data, "course_marks", {}))
        inferred_sem = semester_number or getattr(registration_data, "semester_number", getattr(registration_data, "semester", None))

    # 2. Convert courses into dictionary of items
    courses_dict: Dict[str, Dict[str, Any]] = {}
    if isinstance(courses_raw, dict):
        for k, v in courses_raw.items():
            if hasattr(v, "model_dump"):
                cd = v.model_dump()
            elif hasattr(v, "dict"):
                cd = v.dict()
            elif isinstance(v, dict):
                cd = dict(v)
            else:
                cd = {"total": v}
            courses_dict[k] = cd
    elif isinstance(courses_raw, (list, tuple)):
        for idx, item in enumerate(courses_raw):
            if hasattr(item, "model_dump"):
                cd = item.model_dump()
            elif hasattr(item, "dict"):
                cd = item.dict()
            elif isinstance(item, dict):
                cd = dict(item)
            else:
                continue
            k = cd.get("course_code") or cd.get("course_key") or cd.get("code") or f"COURSE_{idx+1}"
            courses_dict[k] = cd

    # 3. Semester detection
    if inferred_sem:
        try:
            sem_num = int(inferred_sem)
        except (ValueError, TypeError):
            sem_num = 1
    else:
        keys_str = " ".join([str(k) + " " + str(v.get("course_code", "")) + " " + str(v.get("course_title", "")) for k, v in courses_dict.items()]).upper()
        if "COMPETENCY" in keys_str or "INTE 415" in keys_str:
            sem_num = 8
        elif "COMH (II)" in keys_str or "COMH_II" in keys_str or "NRST" in keys_str or "OBGN" in keys_str:
            sem_num = 7
        elif "CHN" in keys_str or "MHN" in keys_str or "NMLE" in keys_str:
            sem_num = 6
        elif "COMH (I)" in keys_str or "COMH_I" in keys_str or "EDUC" in keys_str or "FORN" in keys_str:
            sem_num = 5
        elif "PHAR" in keys_str or "PATH" in keys_str or "AHN (II)" in keys_str or "AHN_II" in keys_str or "PROF" in keys_str:
            sem_num = 4
        elif "MICR" in keys_str or "AHN (I)" in keys_str or "AHN_I" in keys_str:
            sem_num = 3
        elif "BIOC" in keys_str or "NUTR" in keys_str or "N-NF" in keys_str or "NNF" in keys_str or "HNIT" in keys_str:
            sem_num = 2
        else:
            sem_num = 1

    from backend.schemas.course_schemas import SemesterDefinition
    sem_def = course_catalog if isinstance(course_catalog, SemesterDefinition) else SEMESTER_DEFINITIONS.get(sem_num)
    meta_dict = ALL_SEMESTER_CANONICAL_METADATA.get(sem_num, {})

    evaluated_courses: Dict[str, Dict[str, Any]] = {}
    failed_courses: List[str] = []
    backlog_queue: List[Dict[str, Any]] = []

    # Map candidate courses against metadata
    for c_key, c_data in courses_dict.items():
        # Match metadata
        matched_meta = meta_dict.get(c_key)
        if not matched_meta:
            c_code_input = str(c_data.get("course_code", "")).strip().upper()
            c_title_input = str(c_data.get("course_title", "")).strip().upper()
            for mk, mv in meta_dict.items():
                if c_code_input and (mv["course_code"].upper() in c_code_input or c_code_input in mv["course_code"].upper()):
                    comp_name = str(c_data.get("component_name", "")).upper()
                    if comp_name:
                        if "PRACT" in comp_name and "PRACT" in mk:
                            matched_meta = mv
                            break
                        elif "THEORY" in comp_name and "THEORY" in mk:
                            matched_meta = mv
                            break
                    if not matched_meta:
                        matched_meta = mv
                elif c_title_input and (mv["course_title"].upper() in c_title_input or c_title_input in mv["course_title"].upper()):
                    matched_meta = mv
                    break

        course_code = matched_meta["course_code"] if matched_meta else (c_data.get("course_code") or c_key)
        course_title = matched_meta["course_title"] if matched_meta else (c_data.get("course_title") or c_data.get("subject_name") or course_code)
        credits = matched_meta["credits"] if matched_meta else int(c_data.get("credits") or 0)
        ia_max = float(matched_meta["ia_max"] if matched_meta else (c_data.get("ia_max") or c_data.get("internal_max") or 25.0))
        ea_max = float(matched_meta["ea_max"] if matched_meta else (c_data.get("ea_max") or c_data.get("external_max") or 75.0))
        total_max = float(matched_meta["total_max"] if matched_meta else (c_data.get("total_max") or (ia_max + ea_max)))
        is_eng_el = (
            matched_meta["is_english_or_elective"] if matched_meta
            else (bool(c_data.get("is_english_or_elective", False)) or any(x in str(course_code).upper() for x in ["ENGL", "ELECTIVE"]) or "SCIENTIFIC WRITING" in str(course_title).upper())
        )
        include_in_sgpa = (
            matched_meta["include_in_sgpa"] if matched_meta
            else (False if is_eng_el else bool(c_data.get("include_in_sgpa", True)))
        )

        # Raw component extraction (NEVER trust pre-calculated sheet total or grades)
        raw_ia = c_data.get("int_marks") if "int_marks" in c_data else (c_data.get("internal_obtained") if "internal_obtained" in c_data else c_data.get("ia"))
        int_sc, int_ab = parse_numeric_score(raw_ia)

        pa = c_data.get("ex_part_a") or c_data.get("external_part_a")
        pb = c_data.get("ex_part_b") or c_data.get("external_part_b")
        pc = c_data.get("ex_part_c") or c_data.get("external_part_c")
        raw_ea = c_data.get("ex_total") if "ex_total" in c_data else (c_data.get("ex_marks") if "ex_marks" in c_data else (c_data.get("external_obtained") if "external_obtained" in c_data else c_data.get("ea")))

        if (pa is not None or pb is not None or pc is not None) and (raw_ea is None or raw_ea == 0):
            spa, pa_ab = parse_numeric_score(pa)
            spb, pb_ab = parse_numeric_score(pb)
            spc, pc_ab = parse_numeric_score(pc)
            ex_sc = round((spa or 0.0) + (spb or 0.0) + (spc or 0.0), 2)
            ex_ab = (pa_ab if pa is not None else False) or (pb_ab if pb is not None else False) or (pc_ab if pc is not None else False)
        else:
            ex_sc, ex_ab = parse_numeric_score(raw_ea)

        g_val, _ = parse_numeric_score(c_data.get("grace") or c_data.get("grace_marks") or c_data.get("grace_awarded") or 0.0)
        course_grace = float(g_val or 0.0)

        is_exempt = (
            bool(c_data.get("is_exempted", False)) or
            str(c_data.get("letter_grade", "")).strip() == "Ex." or
            str(raw_ia).strip().upper() in ["EX.", "EX", "X", "EXEMPTED"] or
            str(raw_ea).strip().upper() in ["EX.", "EX", "X", "EXEMPTED"]
        )
        is_absent = (int_ab or ex_ab) and not is_exempt

        # Pure in-app calculation: Total = IA + EA + Grace
        if is_absent:
            total_obtained = 0.0
        elif is_exempt:
            total_obtained = round((int_sc or 0.0) + (ex_sc or 0.0) + course_grace, 2)
        else:
            total_obtained = round((int_sc or 0.0) + (ex_sc or 0.0) + course_grace, 2)

        # Threshold verification
        pass_cutoff_pct = 0.40 if is_eng_el else 0.50
        ia_thresh = round(ia_max * pass_cutoff_pct, 2)
        ea_thresh = round(ea_max * pass_cutoff_pct, 2)
        tot_thresh = round(total_max * pass_cutoff_pct, 2)

        ia_pass = (int_sc is not None) and (int_sc >= ia_thresh) if not is_absent else False
        ea_pass = (ex_sc is not None) and ((ex_sc + course_grace) >= ea_thresh) if not is_absent else False
        tot_pass = (total_obtained >= tot_thresh) if not is_absent else False

        course_is_pass = (ia_pass and ea_pass and tot_pass) or is_exempt
        has_failed_threshold = (not course_is_pass) and (not is_absent) and (not is_exempt)

        if is_exempt:
            letter_grade = "Ex."
            grade_point = 0
            percentage = 0.0
            course_is_pass = True
        else:
            grade_res = calculate_inc_grade(
                obtained_marks=total_obtained if not is_absent else None,
                max_marks=total_max,
                is_english_or_elective=is_eng_el,
                is_absent=is_absent,
                has_failed_threshold=has_failed_threshold
            )
            letter_grade = grade_res.letter_grade
            grade_point = grade_res.grade_point
            percentage = grade_res.percentage
            course_is_pass = grade_res.is_pass

        credit_points = round(credits * grade_point, 2) if (course_is_pass and include_in_sgpa) else 0.0

        if (not course_is_pass or letter_grade == "F") and not is_exempt:
            failed_courses.append(course_title)
            if not ia_pass and not ea_pass:
                failed_comp = "Both IA and EA"
                def_ia = max(0.0, ia_thresh - (int_sc or 0.0))
                def_ea = max(0.0, ea_thresh - ((ex_sc or 0.0) + course_grace))
                deficit = round(def_ia + def_ea, 2)
            elif not ea_pass:
                failed_comp = "Theory/External"
                deficit = round(max(0.0, ea_thresh - ((ex_sc or 0.0) + course_grace)), 2)
            elif not ia_pass:
                failed_comp = "Internal"
                deficit = round(max(0.0, ia_thresh - (int_sc or 0.0)), 2)
            else:
                failed_comp = "Aggregate"
                deficit = round(max(0.0, tot_thresh - total_obtained), 2)

            backlog_queue.append({
                "course_code": course_code,
                "course_title": course_title,
                "failed_component": failed_comp,
                "deficit_marks": deficit,
                "attempt_count": 1,
                "backlog_status": "ACTIVE",
                "semester_number": sem_num,
                "roll_no": roll_no,
                "student_name": student_name,
            })

        evaluated_courses[c_key] = {
            "course_key": c_key,
            "course_code": course_code,
            "course_title": course_title,
            "credits": credits,
            "include_in_sgpa": include_in_sgpa,
            "is_english_or_elective": is_eng_el,
            "internal_obtained": "Ab" if int_ab else int_sc,
            "internal_max": ia_max,
            "internal_pass": ia_pass,
            "external_obtained": "Ab" if ex_ab else ex_sc,
            "external_max": ea_max,
            "external_pass": ea_pass,
            "grace_marks": course_grace,
            "total_obtained": "Ab" if is_absent else total_obtained,
            "total_max": total_max,
            "percentage": percentage,
            "letter_grade": letter_grade,
            "grade_point": grade_point,
            "credit_points": credit_points,
            "is_pass": course_is_pass,
            "is_absent": is_absent,
            "is_exempted": is_exempt,
        }

    # 4. Semester Summary Metrics
    numeric_totals = [c["total_obtained"] for c in evaluated_courses.values() if isinstance(c["total_obtained"], (int, float))]
    grand_total_obtained = round(sum(numeric_totals), 2)
    grand_total_max = round(sum(c["total_max"] for c in evaluated_courses.values()), 2)
    overall_percentage = round((grand_total_obtained / grand_total_max) * 100.0, 2) if grand_total_max > 0 else 0.0

    statutory_credits = STATUTORY_SGPA_CREDITS.get(sem_num, sem_def.sgpa_eligible_credits if sem_def else 1)
    total_credit_score = round(sum(c["credit_points"] for c in evaluated_courses.values() if c["include_in_sgpa"]), 2)
    sgpa = round(total_credit_score / max(statutory_credits, 1), 2)

    total_grace = sum(c["grace_marks"] for c in evaluated_courses.values())
    is_all_pass = (len(failed_courses) == 0)

    if not is_all_pass:
        result_status = "FAIL"
    elif total_grace > 0:
        g_courses = [c["course_title"] for c in evaluated_courses.values() if c["grace_marks"] > 0]
        result_status = f"PASS WITH {format_grace_string(total_grace)} GRACE MARKS IN {' & '.join(g_courses)}"
    else:
        result_status = "PASS"

    return SemesterEvaluationResult({
        "roll_no": roll_no,
        "enroll_no": enroll_no,
        "student_name": student_name,
        "father_name": father_name,
        "semester_number": sem_num,
        "courses": evaluated_courses,
        "grand_total_obtained": grand_total_obtained,
        "grand_total_max": grand_total_max,
        "overall_percentage": overall_percentage,
        "total_credit_score": total_credit_score,
        "total_sgpa_credits": statutory_credits,
        "sgpa": sgpa,
        "result_status": result_status,
        "is_pass": is_all_pass,
        "failed_courses": failed_courses,
        "backlog_queue": backlog_queue,
        "total_grace": round(total_grace, 2),
        "raw_remarks": raw_remarks or result_status,
    })

