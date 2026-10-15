"""
FastAPI Routes for Semester Schemas, Regulations & Templates
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Response, status
from backend.schemas.course_schemas import SEMESTER_DEFINITIONS, SemesterDefinition
from backend.parsers.template_generator import generate_semester_template

router = APIRouter(prefix="/api", tags=["Schemas & Regulations"])

INSTITUTIONAL_METADATA = {
    "application_name": "VidyaMarksheet",
    "application_subtitle": "B.Sc. Nursing Marksheet Generation System",
    "institution_name": "College of Nursing, Sanjay Gandhi Postgraduate Institute of Medical Sciences (SGPGIMS)",
    "location": "Lucknow, Uttar Pradesh, India",
    "college_code": "1313",
    "regulatory_framework": "Indian Nursing Council (INC) Gazette & SGPGIMS Lucknow Academic Regulations",
    "branding": {
        "developed_by": "VidyaLabs",
        "copyright": "Copyright © 2026 VidyaLabs. All Rights Reserved.",
        "contact_person": "Priyanka Kumari",
        "contact_mobile": "+91-9140189586"
    }
}

INC_GRADING_SCALE = [
    {
        "percentage_range": "85.00% & Above",
        "letter_grade": "O",
        "grade_point": 10,
        "qualitative_description": "Outstanding",
        "notes": "Qualifies for Distinction"
    },
    {
        "percentage_range": "80.00% to 84.99%",
        "letter_grade": "A+",
        "grade_point": 9,
        "qualitative_description": "Excellent",
        "notes": "First Class with Distinction"
    },
    {
        "percentage_range": "75.00% to 79.99%",
        "letter_grade": "A",
        "grade_point": 8,
        "qualitative_description": "Very Good",
        "notes": "First Class"
    },
    {
        "percentage_range": "65.00% to 74.99%",
        "letter_grade": "B+",
        "grade_point": 7,
        "qualitative_description": "Good",
        "notes": "Higher Second Class"
    },
    {
        "percentage_range": "60.00% to 64.99%",
        "letter_grade": "B",
        "grade_point": 6,
        "qualitative_description": "Above Average",
        "notes": "Second Class"
    },
    {
        "percentage_range": "50.00% to 59.99%",
        "letter_grade": "C",
        "grade_point": 5,
        "qualitative_description": "Pass / Average",
        "notes": "Minimum passing threshold for standard nursing courses"
    },
    {
        "percentage_range": "40.00% to 49.99%",
        "letter_grade": "P",
        "grade_point": 4,
        "qualitative_description": "Pass",
        "notes": "Restricted strictly to Communicative English and Elective modules"
    },
    {
        "percentage_range": "Below 50.00% (or < 40.00% for English/Electives)",
        "letter_grade": "F",
        "grade_point": 0,
        "qualitative_description": "Fail",
        "notes": "Candidate must reappear for failed component"
    },
    {
        "percentage_range": "Absent in Examination",
        "letter_grade": "Ab",
        "grade_point": 0,
        "qualitative_description": "Absent",
        "notes": "Treated as zero grade point"
    }
]


@router.get("/metadata")
def get_institutional_metadata():
    """Returns application branding, institutional affiliations and footer data."""
    return INSTITUTIONAL_METADATA


@router.get("/grading-scale")
def get_inc_grading_scale():
    """Returns official INC 10-point grading scale definitions."""
    return {
        "scale": INC_GRADING_SCALE,
        "passing_thresholds": {
            "standard_courses": "50.00% (Minimum Grade: C, Grade Point: 5)",
            "english_and_electives": "40.00% (Minimum Grade: P, Grade Point: 4)"
        },
        "sgpa_formula": "SGPA = Sum(Credit * Grade Point) / Sum(Eligible Credits)"
    }


@router.get("/schemas")
def list_semester_schemas() -> Dict[str, Any]:
    """Returns all semester definitions (1 to 8) with courses and credit breakdowns."""
    return {
        "metadata": INSTITUTIONAL_METADATA,
        "semesters": {sem_id: sem_def.model_dump() for sem_id, sem_def in SEMESTER_DEFINITIONS.items()}
    }


@router.get("/schemas/{semester_id}")
def get_semester_schema(semester_id: int):
    """Returns details for a specific semester."""
    if semester_id not in SEMESTER_DEFINITIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester {semester_id} not found. Valid semesters are 1 through 8."
        )
    return SEMESTER_DEFINITIONS[semester_id].model_dump()


@router.get("/template/{semester_id}")
def download_semester_template(semester_id: int):
    """Generates and downloads formatted Excel template for a specific semester."""
    if semester_id not in SEMESTER_DEFINITIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester {semester_id} not found."
        )

    file_bytes = generate_semester_template(semester_id)
    headers = {
        "Content-Disposition": f"attachment; filename=SGPGIMS_BSc_Nursing_Semester_{semester_id}_Template.xlsx"
    }
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
