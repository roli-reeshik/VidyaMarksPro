"""
Student Demographics & Semester Result Models
Compliant with INC Gazette & SGPGIMS Lucknow Regulations
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StudentDemographics(BaseModel):
    serial_no: Optional[int] = Field(default=None, description="Serial number in source sheet")
    name: str = Field(..., description="Student Full Name")
    father_name: str = Field(..., description="Father's / Guardian's Name (S/o / D/o)")
    enrollment_no: str = Field(..., description="Institutional Enrollment Number")
    roll_no: str = Field(..., description="University Roll Number")


class SubComponentMark(BaseModel):
    name: str
    code: Optional[str] = None
    obtained: Optional[float] = None
    max_marks: float
    is_absent: bool = False


class EvaluatedCourseComponent(BaseModel):
    course_code: str
    course_title: str
    component_name: str = Field(default="Theory", description="Theory, Practical, College Exam, etc.")
    credits: int
    credit_breakdown: Optional[str] = None

    # Granular Marks
    internal_obtained: Optional[float] = None
    internal_max: float = 25.0
    external_obtained: Optional[float] = None  # University / College End Sem Exam
    external_max: float = 75.0
    sub_components: List[SubComponentMark] = Field(default_factory=list)

    total_obtained: Optional[float] = None
    total_max: float = 100.0
    percentage: float = 0.0

    # Grade & Pass
    letter_grade: str = Field(..., description="O, A+, A, B+, B, C, P, F, Ab")
    grade_point: int = Field(..., ge=0, le=10)
    is_pass: bool
    grace_marks: Optional[float] = 0.0
    is_absent: bool = False

    is_english_or_elective: bool = False
    include_in_sgpa: bool = True
    footnotes: Optional[str] = None


class SemesterStudentResult(BaseModel):
    student: StudentDemographics
    semester_number: int
    degree_title: str = "B.Sc. NURSING"
    examination_session: Optional[str] = Field(default="January - 2026", description="Exam session month & year")
    college_name: str = "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH."
    college_code: str = "1313"

    courses: List[EvaluatedCourseComponent] = Field(default_factory=list)

    grand_total_obtained: float = 0.0
    grand_total_max: float = 250.0
    overall_percentage: float = 0.0
    sgpa: float = 0.0
    total_credit_score: float = 0.0
    total_sgpa_credits: int = 0

    result_status: str = Field(..., description="PASS, FAIL, PASS WITH GRACE MARKS")
    failed_courses: List[str] = Field(default_factory=list)
    remarks: Optional[str] = None


class IngestionResponse(BaseModel):
    success: bool
    filename: str
    semester: int
    examination_session: Optional[str] = None
    total_students: int
    passed_students: int
    failed_students: int
    results: List[SemesterStudentResult]
    warnings: List[str] = Field(default_factory=list)
