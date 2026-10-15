"""
FastAPI Route for Raw Examination Cell Ingestion (/api/exam-cell/ingest)
Phase 1B: Parser adapter compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Branding: VidyaMarksheet by VidyaLabs
"""

from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from backend.parsers.exam_cell_parser import ExamCellParserAdapter
from backend.schemas.canonical_models import StudentRecord, ExamCellIngestionBatchResponse

router = APIRouter(prefix="/api/exam-cell", tags=["Examination Cell Ingestion"])


@router.post("/ingest", response_model=List[StudentRecord])
async def ingest_exam_cell_sheet(
    file: UploadFile = File(..., description="Raw Examination Cell Excel file (.xlsx, .xls)"),
    sheet_name: Optional[str] = Form(None, description="Optional sheet name to parse")
):
    """
    Ingests raw Examination Cell Excel file, automatically detects multi-level headers,
    sanitizes demographic IDs, extracts grace string formulas (e.g., '35+2.5-37.5'),
    truncates institutional footer signatures, and returns a normalized array of StudentRecord objects.
    """
    filename = file.filename or "unknown.xlsx"
    valid_extensions = (".xlsx", ".xls")
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only .xlsx and .xls files are supported."
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    try:
        adapter = ExamCellParserAdapter(file_content=content, sheet_name=sheet_name)
        records = adapter.parse()
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error parsing raw Examination Cell spreadsheet: {str(e)}"
        )


@router.post("/batch", response_model=ExamCellIngestionBatchResponse)
async def ingest_exam_cell_batch(
    file: UploadFile = File(..., description="Raw Examination Cell Excel file (.xlsx, .xls)"),
    sheet_name: Optional[str] = Form(None, description="Optional sheet name to parse")
):
    """
    Envelope response variant containing metadata, branding, record counts, and normalized StudentRecord list.
    """
    filename = file.filename or "unknown.xlsx"
    if not any(filename.lower().endswith(ext) for ext in (".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only .xlsx and .xls files are supported."
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    try:
        adapter = ExamCellParserAdapter(file_content=content, sheet_name=sheet_name)
        records = adapter.parse()
        return ExamCellIngestionBatchResponse(
            success=True,
            branding="VidyaMarksheet by VidyaLabs",
            total_records=len(records),
            records=records,
            warnings=adapter.warnings
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error parsing raw Examination Cell spreadsheet: {str(e)}"
        )
