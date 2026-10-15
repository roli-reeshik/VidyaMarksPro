"""
Semester Course Schemas for Semesters 1 through 8
B.Sc. Nursing Program (INC Gazette & SGPGIMS Lucknow Regulations)
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CourseType(str, Enum):
    CORE = "CORE"
    COLLEGE_EXAM = "COLLEGE_EXAM"
    ELECTIVE = "ELECTIVE"
    CLINICAL_COMPETENCY = "CLINICAL_COMPETENCY"


class ComponentType(str, Enum):
    THEORY = "THEORY"
    PRACTICAL = "PRACTICAL"
    THEORY_AND_PRACTICAL = "THEORY_AND_PRACTICAL"
    COMPETENCY = "COMPETENCY"


class SubComponentDefinition(BaseModel):
    name: str = Field(..., description="Sub-component name e.g. Section A: Applied Anatomy")
    code: Optional[str] = None
    max_marks: float
    min_pass_marks: Optional[float] = None


class ExamComponentSchema(BaseModel):
    name: str = Field(..., description="Component name e.g. Theory or Practical")
    credits: int = Field(default=0)
    ia_max: float = Field(default=25.0, description="Internal Assessment Maximum Marks")
    ia_min_pass: Optional[float] = Field(default=12.5, description="Internal Assessment Pass Threshold")
    ea_max: float = Field(default=75.0, description="End Semester / University Exam Maximum Marks")
    ea_min_pass: Optional[float] = Field(default=37.5, description="End Semester Pass Threshold")
    total_max: float = Field(default=100.0, description="Total Maximum Marks")
    min_pass_percentage: float = Field(default=50.0, description="Minimum Passing Percentage")
    sub_components: List[SubComponentDefinition] = Field(default_factory=list)


class CourseDefinition(BaseModel):
    sl_no: int = Field(..., description="Serial number on marksheet")
    course_code: str = Field(..., description="Course code e.g. ANAT 105 & PHYS 110")
    title: str = Field(..., description="Full official course title")
    credits: int = Field(..., description="Total course credit hours")
    credit_breakdown: Optional[str] = Field(default=None, description="e.g. (3+3), T-12, P-11, (T-3, P-1)")
    course_type: CourseType = Field(default=CourseType.CORE)
    component_type: ComponentType = Field(default=ComponentType.THEORY)
    passing_threshold_percent: float = Field(
        default=50.0,
        description="Minimum overall passing % (50% standard, 40% Communicative English/Electives)"
    )
    is_english_or_elective: bool = Field(
        default=False,
        description="True strictly for Communicative English and Electives (qualifies for 'P' grade)"
    )
    include_in_sgpa: bool = Field(
        default=True,
        description="Whether this course is added when computing SGPA as per INC regulations"
    )
    components: List[ExamComponentSchema] = Field(
        default_factory=list,
        description="Exam components (e.g. separate Theory & Practical lines, or single combined line)"
    )
    footnotes: Optional[str] = Field(default=None)


class SemesterDefinition(BaseModel):
    semester_number: int = Field(..., ge=1, le=8)
    year: int = Field(..., ge=1, le=4)
    semester_name: str = Field(..., description="e.g. FIRST SEMESTER")
    year_name: str = Field(..., description="e.g. FIRST YEAR")
    degree_title: str = Field(default="B.Sc. NURSING")
    college_name: str = Field(
        default="COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH."
    )
    college_code: Optional[str] = Field(default="1313")
    total_prescribed_credits: int
    sgpa_eligible_credits: int
    grand_total_marks: float
    courses: List[CourseDefinition]


# Master Course Catalog for Semesters 1 to 8 as per INC Gazette & SGPGIMS Lucknow
SEMESTER_DEFINITIONS: Dict[int, SemesterDefinition] = {
    1: SemesterDefinition(
        semester_number=1,
        year=1,
        semester_name="FIRST SEMESTER",
        year_name="FIRST YEAR",
        total_prescribed_credits=14,
        sgpa_eligible_credits=12,
        grand_total_marks=250.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="ENGL 101",
                title="Communicative English",
                credits=2,
                credit_breakdown="2",
                course_type=CourseType.COLLEGE_EXAM,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=40.0,
                is_english_or_elective=True,
                include_in_sgpa=False,
                footnotes="* College Exam, Marks are not added for calculating SGPA, Pass marks-40% as per INC, New Delhi",
                components=[
                    ExamComponentSchema(
                        name="College Exam",
                        credits=2,
                        ia_max=25.0,
                        ia_min_pass=10.0,
                        ea_max=25.0,
                        ea_min_pass=10.0,
                        total_max=50.0,
                        min_pass_percentage=40.0,
                        sub_components=[]
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="ANAT 105 & PHYS 110",
                title="Applied Anatomy & Applied Physiology",
                credits=6,
                credit_breakdown="(3+3)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=6,
                        ia_max=25.0,
                        ia_min_pass=12.5,
                        ea_max=75.0,
                        ea_min_pass=37.5,
                        total_max=100.0,
                        min_pass_percentage=50.0,
                        sub_components=[
                            SubComponentDefinition(name="Applied Anatomy", code="ANAT 105", max_marks=37.0),
                            SubComponentDefinition(name="Applied Physiology", code="PHYS 110", max_marks=38.0),
                        ]
                    )
                ]
            ),
            CourseDefinition(
                sl_no=3,
                course_code="SOCI 115 & PSYC 120",
                title="Applied Sociology & Applied Psychology",
                credits=6,
                credit_breakdown="(3+3)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=6,
                        ia_max=25.0,
                        ia_min_pass=12.5,
                        ea_max=75.0,
                        ea_min_pass=37.5,
                        total_max=100.0,
                        min_pass_percentage=50.0,
                        sub_components=[
                            SubComponentDefinition(name="Applied Sociology", code="SOCI 115", max_marks=37.0),
                            SubComponentDefinition(name="Applied Psychology", code="PSYC 120", max_marks=38.0),
                        ]
                    )
                ]
            )
        ]
    ),

    2: SemesterDefinition(
        semester_number=2,
        year=1,
        semester_name="SECOND SEMESTER",
        year_name="FIRST YEAR",
        total_prescribed_credits=31,
        sgpa_eligible_credits=31,
        grand_total_marks=350.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="BIOC 135 & NUTR 140",
                title="Applied Biochemistry & Applied Nutrition & Dietetics",
                credits=5,
                credit_breakdown="(2+3)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=5,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0,
                        sub_components=[
                            SubComponentDefinition(name="Applied Biochemistry", code="BIOC 135", max_marks=25.0),
                            SubComponentDefinition(name="Applied Nutrition & Dietetics", code="NUTR 140", max_marks=50.0),
                        ]
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="N-NF (I & II) 125",
                title="Nursing Foundation I & II Incl. Health Assessment Module",
                credits=23,
                credit_breakdown="T-12 (6+6), P-11 (4+7)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=12,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=11,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=3,
                course_code="HNIT 145",
                title="Health/Nursing Informatics & Technology",
                credits=3,
                credit_breakdown="3",
                course_type=CourseType.COLLEGE_EXAM,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                footnotes="*HNIT 145 College Exam T-Theory. P-Practical. Presc. : Prescribed Obtd. : Obtained",
                components=[
                    ExamComponentSchema(
                        name="College Exam",
                        credits=3,
                        ia_max=25.0,
                        ea_max=25.0,
                        total_max=50.0,
                        min_pass_percentage=50.0
                    )
                ]
            )
        ]
    ),

    3: SemesterDefinition(
        semester_number=3,
        year=2,
        semester_name="THIRD SEMESTER",
        year_name="SECOND YEAR",
        total_prescribed_credits=17,
        sgpa_eligible_credits=17,
        grand_total_marks=300.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="MICR 201",
                title="Applied Microbiology and Infection Control including Safety",
                credits=3,
                credit_breakdown="3",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=3,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="N-AHN (I) 215",
                title="Adult Health Nursing I with Integrated Pathophysiology including BCLS module",
                credits=14,
                credit_breakdown="T-7, P-7",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=7,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=7,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            )
        ]
    ),

    4: SemesterDefinition(
        semester_number=4,
        year=2,
        semester_name="FOURTH SEMESTER",
        year_name="SECOND YEAR",
        total_prescribed_credits=21,
        sgpa_eligible_credits=20,
        grand_total_marks=350.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="PHAR (I & II)-205 & PATH (I & II)-210",
                title="Pharmacology (I & II) & Pathology (I & II) (including Genetics)",
                credits=6,
                credit_breakdown="(4+2)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=6,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0,
                        sub_components=[
                            SubComponentDefinition(name="Pharmacology (I & II)", code="PHAR 205", max_marks=38.0),
                            SubComponentDefinition(name="Pathology (I & II) & Genetics", code="PATH 210", max_marks=37.0),
                        ]
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="N-AHN (II) 225",
                title="Adult Health Nursing II with Integrated Pathophysiology",
                credits=14,
                credit_breakdown="T-7, P-7",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=7,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=7,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=3,
                course_code="PROF 230",
                title="Professionalism, Professional Values & Ethics including Bioethics",
                credits=1,
                credit_breakdown="1",
                course_type=CourseType.COLLEGE_EXAM,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                footnotes="* Prof 230-College Exam",
                components=[
                    ExamComponentSchema(
                        name="College Exam",
                        credits=1,
                        ia_max=25.0,
                        ea_max=25.0,
                        total_max=50.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=4,
                course_code="Elective-1",
                title="Elective Module (Soft Skills)",
                credits=1,
                credit_breakdown="1",
                course_type=CourseType.ELECTIVE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=40.0,
                is_english_or_elective=True,
                include_in_sgpa=False,
                footnotes="**Elective 1-College Exam, Marks are not Added for Calculating SGPA, Pass Mark-40%",
                components=[
                    ExamComponentSchema(
                        name="Elective Assessment",
                        credits=1,
                        ia_max=0.0,
                        ea_max=100.0,
                        total_max=100.0,
                        min_pass_percentage=40.0
                    )
                ]
            )
        ]
    ),

    5: SemesterDefinition(
        semester_number=5,
        year=3,
        semester_name="FIFTH SEMESTER",
        year_name="THIRD YEAR",
        total_prescribed_credits=11,
        sgpa_eligible_credits=11,
        grand_total_marks=350.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="N-COMH (I) 310",
                title="Community Health Nursing I including Environmental Science & Epidemiology",
                credits=7,
                credit_breakdown="T-5, P-2",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=5,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=2,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="EDUC 315",
                title="Educational Technology / Nursing Education",
                credits=3,
                credit_breakdown="3",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=3,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=3,
                course_code="N-FORN 320",
                title="Introduction to Forensic Nursing",
                credits=1,
                credit_breakdown="1",
                course_type=CourseType.COLLEGE_EXAM,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                footnotes="*N-FORN 320 - College Exam",
                components=[
                    ExamComponentSchema(
                        name="College Exam",
                        credits=1,
                        ia_max=25.0,
                        ea_max=25.0,
                        total_max=50.0,
                        min_pass_percentage=50.0
                    )
                ]
            )
        ]
    ),

    6: SemesterDefinition(
        semester_number=6,
        year=3,
        semester_name="SIXTH SEMESTER",
        year_name="THIRD YEAR",
        total_prescribed_credits=22,
        sgpa_eligible_credits=21,
        grand_total_marks=500.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="N-CHN (I & II) 301",
                title="Child Health Nursing (I & II)",
                credits=9,
                credit_breakdown="T-5 (3+2), P-4 (3+1)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=5,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=4,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="N-MHN (I & II) 305",
                title="Mental Health Nursing (I & II)",
                credits=8,
                credit_breakdown="T-5 (3+2), P-3 (1+2)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=5,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=3,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=3,
                course_code="NMLE 330",
                title="Nursing Management & Leadership",
                credits=4,
                credit_breakdown="4 (T-3, P-1)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=4,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=4,
                course_code="Elective-2",
                title="Accreditation and Practice Standards (Elective)",
                credits=1,
                credit_breakdown="1",
                course_type=CourseType.ELECTIVE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=40.0,
                is_english_or_elective=True,
                include_in_sgpa=False,
                footnotes="*Elective-2-College Exam, Marks are not added for calculating SGPA, Pass mark-40%",
                components=[
                    ExamComponentSchema(
                        name="Elective Assessment",
                        credits=1,
                        ia_max=0.0,
                        ea_max=100.0,
                        total_max=100.0,
                        min_pass_percentage=40.0
                    )
                ]
            )
        ]
    ),

    7: SemesterDefinition(
        semester_number=7,
        year=4,
        semester_name="SEVENTH SEMESTER",
        year_name="FOURTH YEAR",
        total_prescribed_credits=26,
        sgpa_eligible_credits=26,
        grand_total_marks=500.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="N-COMH (II) 401",
                title="Community Health Nursing II",
                credits=7,
                credit_breakdown="T-5, P-2",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=5,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=2,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="NRST 405",
                title="Nursing Research & Statistics",
                credits=4,
                credit_breakdown="4 (T-2, P-2)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=4,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=3,
                course_code="N-MIDW/OBGN (I & II) 335 & 410",
                title="Midwifery/Obstetrics and Gynaecology (OBG) Nursing I & II",
                credits=15,
                credit_breakdown="T-6 (3+3), P-9 (4+5)",
                course_type=CourseType.CORE,
                component_type=ComponentType.THEORY_AND_PRACTICAL,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Theory",
                        credits=6,
                        ia_max=25.0,
                        ea_max=75.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    ),
                    ExamComponentSchema(
                        name="Practical",
                        credits=9,
                        ia_max=50.0,
                        ea_max=50.0,
                        total_max=100.0,
                        min_pass_percentage=50.0
                    )
                ]
            )
        ]
    ),

    8: SemesterDefinition(
        semester_number=8,
        year=4,
        semester_name="EIGHTH SEMESTER",
        year_name="FOURTH YEAR",
        total_prescribed_credits=13,
        sgpa_eligible_credits=12,
        grand_total_marks=300.0,
        courses=[
            CourseDefinition(
                sl_no=1,
                course_code="INTE 415, 420, 425, 430 & 435",
                title="Competency Assessment (Internship / Intensive Clinical Practicum: 1. Community Health Nursing, 2. Adult Health Nursing, 3. Child Health Nursing, 4. Mental Health Nursing, 5. Midwifery/OBG Nursing)",
                credits=12,
                credit_breakdown="P-12",
                course_type=CourseType.CLINICAL_COMPETENCY,
                component_type=ComponentType.COMPETENCY,
                passing_threshold_percent=50.0,
                is_english_or_elective=False,
                include_in_sgpa=True,
                components=[
                    ExamComponentSchema(
                        name="Competency Assessment (C1)",
                        credits=12,
                        ia_max=100.0,
                        ia_min_pass=50.0,
                        ea_max=100.0,
                        ea_min_pass=50.0,
                        total_max=200.0,
                        min_pass_percentage=50.0
                    )
                ]
            ),
            CourseDefinition(
                sl_no=2,
                course_code="Elective-3",
                title="Scientific Writing Skills (Elective)",
                credits=1,
                credit_breakdown="1",
                course_type=CourseType.ELECTIVE,
                component_type=ComponentType.THEORY,
                passing_threshold_percent=40.0,
                is_english_or_elective=True,
                include_in_sgpa=False,
                footnotes="*Elective 3-Marks are not added for calculating SGPA, Pass Mark-40%",
                components=[
                    ExamComponentSchema(
                        name="Elective Assessment",
                        credits=1,
                        ia_max=0.0,
                        ea_max=100.0,
                        total_max=100.0,
                        min_pass_percentage=40.0
                    )
                ]
            )
        ]
    )
}
