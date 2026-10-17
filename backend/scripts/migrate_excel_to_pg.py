"""
Historical Examination Data Migration Script.
Migrates student records, semester registrations, component marks, and longitudinal summaries
from Excel (.xlsx / .xlsm) ledgers into PostgreSQL (vidya_examination_db).
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
VidyaLabs Copyright © 2026.
"""

import argparse
import os
import sys
from decimal import Decimal
from typing import List, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import openpyxl
from backend.db.database import get_sync_session
from backend.db.init_db import init_database, seed_courses
from backend.db.repository import ExaminationRepository
from backend.parsers.excel_parser import ExcelSheetParser


def migrate_workbook(
    file_path: str,
    batch_name: str = "Batch 2022-2026",
    start_year: int = 2022,
    end_year: int = 2026,
    target_semester: Optional[int] = None
):
    """
    Reads all semester sheets from the provided workbook and persists them into PostgreSQL.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"\n================================================================================")
    print(f"Starting VidyaMarksheet Migration: Excel -> PostgreSQL (vidya_examination_db)")
    print(f"Target File: {file_path}")
    print(f"Cohort Batch: {batch_name} ({start_year}-{end_year})")
    print(f"================================================================================\n")

    # Step 1: Ensure database schema and course definitions are initialized
    init_database()
    seed_courses()

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    wb = openpyxl.load_workbook(file_path, read_only=True)
    all_sheet_names = wb.sheetnames

    # Determine sheets to process
    semester_sheets = []
    for sname in all_sheet_names:
        sname_lower = sname.lower()
        if "semester" in sname_lower or sname_lower.startswith("sem"):
            # Extract number if possible
            for num in range(1, 9):
                if str(num) in sname:
                    if target_semester is None or target_semester == num:
                        semester_sheets.append((num, sname))
                    break

    if not semester_sheets:
        print("No semester sheets detected in workbook.")
        return

    total_migrated_students = set()
    total_registrations = 0
    total_course_marks = 0

    with get_sync_session() as session:
        repo = ExaminationRepository(session)
        batch = repo.get_or_create_batch(
            batch_name=batch_name,
            start_year=start_year,
            end_year=end_year,
            total_credits=151
        )

        for sem_num, sheet_name in semester_sheets:
            print(f"\nProcessing Semester {sem_num} (Sheet: '{sheet_name}')...")
            try:
                parser = ExcelSheetParser(
                    file_content=file_bytes,
                    filename=os.path.basename(file_path),
                    sheet_name=sheet_name
                )
                parse_result = parser.parse()
            except Exception as e:
                print(f"  Warning: Parser error on sheet '{sheet_name}': {e}. Continuing...")
                continue

            if not parse_result.success or not parse_result.results:
                print(f"  No student records found in sheet '{sheet_name}'.")
                continue

            sem_students_count = 0
            for record in parse_result.results:
                stu_info = record.student
                roll_no = stu_info.roll_no.strip()
                enroll_no = stu_info.enrollment_no.strip()
                name = stu_info.name.strip()
                father_name = stu_info.father_name.strip()

                # Upsert Student
                student = repo.upsert_student(
                    batch_id=batch.id,
                    roll_no=roll_no,
                    enrollment_no=enroll_no,
                    student_name=name,
                    father_name=father_name,
                    institutional_status="REGULAR",
                    modified_by="MIGRATE_EXCEL_CLI"
                )
                total_migrated_students.add(student.id)

                # Upsert Registration
                reg = repo.upsert_registration(
                    student_id=student.id,
                    semester_number=sem_num,
                    exam_month_year=record.examination_session or f"JANUARY - {start_year + (sem_num // 2)}",
                    exam_type="MAIN",
                    total_credits=float(record.total_sgpa_credits),
                    sgpa_credits=float(record.total_sgpa_credits),
                    grand_total_obtained=float(record.grand_total_obtained),
                    grand_total_max=float(record.grand_total_max),
                    percentage=float(record.overall_percentage),
                    credit_score=float(record.total_credit_score),
                    sgpa=float(record.sgpa),
                    result_status=record.result_status,
                    result_remarks=record.remarks,
                    grading_performance=f"SGPA {record.sgpa}",
                    modified_by="MIGRATE_EXCEL_CLI"
                )
                total_registrations += 1

                # Upsert Course Marks
                for comp in record.courses:
                    comp_name = getattr(comp, "component_name", None)
                    comp_title = getattr(comp, "course_title", None)
                    comp_cr = getattr(comp, "credits", None)
                    db_course = repo.resolve_course(
                        semester_number=sem_num,
                        course_code=comp.course_code,
                        component_name=comp_name,
                        course_title=comp_title,
                        credits=comp_cr
                    )

                    if not db_course:
                        print(f"  Warning: Course {comp.course_code} not found in catalog for Sem {sem_num}. Skipping course mark.")
                        continue

                    # Extract subcomponents if any (Part A / Part B)
                    part_a = None
                    part_b = None
                    for sub in comp.sub_components:
                        if "A" in sub.name.upper() and sub.obtained is not None:
                            part_a = sub.obtained
                        elif "B" in sub.name.upper() and sub.obtained is not None:
                            part_b = sub.obtained

                    repo.upsert_course_mark(
                        registration_id=reg.id,
                        course_id=db_course.id,
                        internal_obtained=float(comp.internal_obtained or 0.0),
                        external_obtained=float(comp.external_obtained or 0.0),
                        total_obtained=float(comp.total_obtained or 0.0),
                        percentage=float(comp.percentage),
                        letter_grade=comp.letter_grade,
                        grade_point=comp.grade_point,
                        course_result="PASS" if comp.is_pass else "FAIL",
                        grace_awarded=float(comp.grace_marks or 0.0),
                        external_part_a=part_a,
                        external_part_b=part_b,
                        student_roll_no=roll_no,
                        modified_by="MIGRATE_EXCEL_CLI"
                    )
                    total_course_marks += 1

                # Recalculate longitudinal academic summary
                repo.recalculate_cumulative_summary(student.id)
                sem_students_count += 1

            print(f"  -> Ingested {sem_students_count} student records for Semester {sem_num}.")

        session.commit()

    print(f"\n================================================================================")
    print(f"Migration Complete!")
    print(f"Total Unique Students:    {len(total_migrated_students)}")
    print(f"Total Registrations:      {total_registrations}")
    print(f"Total Course Marks:       {total_course_marks}")
    print(f"PostgreSQL Database:      vidya_examination_db")
    print(f"================================================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Migrate VidyaMarksheet Excel Ledger to PostgreSQL")
    parser.add_argument(
        "--file",
        default=os.path.join(BASE_DIR, "VidyaMarksheet_Master_DataSheet.xlsx"),
        help="Path to Excel datasheet workbook (.xlsx / .xlsm)"
    )
    parser.add_argument(
        "--batch",
        default="Batch 2022-2026",
        help="Name of Cohort Batch (e.g., 'Batch 2022-2026')"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2022,
        help="Batch start year"
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2026,
        help="Batch end year"
    )
    parser.add_argument(
        "--semester",
        type=int,
        default=None,
        help="Specific semester number (1-8) to migrate (default: all)"
    )

    args = parser.parse_args()
    migrate_workbook(
        file_path=args.file,
        batch_name=args.batch,
        start_year=args.start_year,
        end_year=args.end_year,
        target_semester=args.semester
    )


if __name__ == "__main__":
    main()
