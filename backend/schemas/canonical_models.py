"""
Canonical Data Models for Examination Cell Ingestion Engine
Phase 1B: Clean, normalized schema compliant with VidyaMarksheet regulations.
"""

from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field


def format_numeric_token(val: Optional[Union[float, int, str]]) -> Union[int, float, str]:
    """
    Normalizes numeric values:
    - If None or empty -> 0
    - If absent string ('Ab', 'Absent') -> 'Ab'
    - If integer equivalent (e.g. 20.0) -> 20
    - If decimal (e.g. 57.5) -> 57.5
    """
    if val is None or val == "":
        return 0
    if isinstance(val, str):
        val_clean = val.strip()
        if val_clean.upper() in ["AB", "ABSENT"]:
            return "Ab"
        if val_clean == "-":
            return 0
        try:
            num = float(val_clean)
            return int(num) if round(num, 4) == int(num) else round(num, 2)
        except ValueError:
            return val_clean
    if isinstance(val, (int, float)):
        return int(val) if round(val, 4) == int(val) else round(val, 2)
    return str(val)


class AnatPhysRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_part_a: Union[int, float, str] = Field(..., description="Applied Anatomy Section A (Max 37)")
    ex_part_b: Union[int, float, str] = Field(..., description="Applied Physiology Section B (Max 38)")
    ex_total: Union[int, float, str] = Field(..., description="University Exam Total (Max 75)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 100)")


class SociPsycRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_part_a: Union[int, float, str] = Field(..., description="Applied Sociology Section A (Max 37)")
    ex_part_b: Union[int, float, str] = Field(..., description="Applied Psychology Section B (Max 38)")
    ex_total: Union[int, float, str] = Field(..., description="University Exam Total (Max 75)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 100)")


class EnglRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_marks: Union[int, float, str] = Field(..., description="College / End Sem Exam (Max 25)")
    grace: Optional[Union[int, float]] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 50)")


class BiocNutrRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_part_a: Union[int, float, str] = Field(..., description="Applied Biochemistry Section A (Max 25)")
    ex_part_b: Union[int, float, str] = Field(..., description="Applied Nutrition & Dietetics Section B (Max 50)")
    ex_total: Union[int, float, str] = Field(..., description="University Exam Total (Max 75)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 100)")


class NnfTheoryRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_marks: Union[int, float, str] = Field(..., description="University Exam Theory (Max 75)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 100)")


class NnfPractRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 50)")
    ex_marks: Union[int, float, str] = Field(..., description="University Exam Practical (Max 50)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 100)")


class HnitRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_marks: Union[int, float, str] = Field(..., description="College Exam (Max 25)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 50)")


class PharPathGenRecord(BaseModel):
    int_marks: Union[int, float, str] = Field(..., description="Internal Assessment (Max 25)")
    ex_part_a: Union[int, float, str] = Field(..., description="Pharmacology Section A (Max 38)")
    ex_part_b: Union[int, float, str] = Field(..., description="Pathology Section B (Max 25)")
    ex_part_c: Union[int, float, str] = Field(..., description="Genetics Section C (Max 12)")
    ex_total: Union[int, float, str] = Field(..., description="University Exam Total (Max 75)")
    grace: Union[int, float] = Field(default=0, description="Grace marks awarded")
    total: Union[int, float, str] = Field(..., description="Course Total (Max 100)")


class GenericCourseRecord(BaseModel):
    int_marks: Optional[Union[int, float, str]] = None
    ex_marks: Optional[Union[int, float, str]] = None
    ex_part_a: Optional[Union[int, float, str]] = None
    ex_part_b: Optional[Union[int, float, str]] = None
    ex_part_c: Optional[Union[int, float, str]] = None
    ex_total: Optional[Union[int, float, str]] = None
    grace: Union[int, float] = 0
    total: Union[int, float, str]
    extra: Dict[str, Any] = Field(default_factory=dict)


class StudentRecord(BaseModel):
    roll_no: str = Field(..., description="Normalized University Roll Number (e.g. '202501002')")
    enroll_no: str = Field(..., description="Institutional Enrollment Number (e.g. '2025630')")
    student_name: str = Field(..., description="Clean Student Full Name (e.g. 'ADITYA KUMAR KATHERIYA')")
    father_name: str = Field(..., description="Clean Father's Name (e.g. 'VIJAY KUMAR')")
    courses: Dict[str, Any] = Field(
        ...,
        description="Dictionary of normalized course marks (e.g. ANAT_PHYS, SOCI_PSYC, ENGL)"
    )
    raw_remarks: Optional[str] = Field(
        default=None,
        description="Examination Cell remark string (e.g. 'PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY')"
    )


class ExamCellIngestionBatchResponse(BaseModel):
    success: bool
    branding: str = "VidyaMarksheet by VidyaLabs"
    total_records: int
    records: List[StudentRecord]
    warnings: List[str] = Field(default_factory=list)
