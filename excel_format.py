import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_marksheet_master_workbook():
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styling definitions
    font_title = Font(name="Calibri", size=13, bold=True, color="1B365D")
    font_sub = Font(name="Calibri", size=9, italic=True, color="4A5568")
    font_header_course = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_header_sub = Font(name="Calibri", size=9, bold=True, color="1A202C")
    font_data = Font(name="Calibri", size=9)
    font_bold_data = Font(name="Calibri", size=9, bold=True)

    fill_course_blue = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    fill_course_teal = PatternFill(start_color="0D5C75", end_color="0D5C75", fill_type="solid")
    fill_summary_navy = PatternFill(start_color="2A4365", end_color="2A4365", fill_type="solid")
    fill_sub_light = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
    fill_grace_highlight = PatternFill(start_color="FEFCBF", end_color="FEFCBF", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E0")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")

    # Semester Course Blueprint Definitions as per INC Gazette & SGPGIMS marksheets
    sem_blueprints = {
        "Semester_1": {
            "title": "B.Sc. NURSING FIRST YEAR (FIRST SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 250,
            "total_credits": 12, # 6 (Anat+Phys) + 6 (Soci+Psyc), English excluded from SGPA
            "courses": [
                {
                    "title": "Applied Anatomy & Applied Physiology (ANAT 105 & PHYS 110) [6 Credits]",
                    "subs": ["Int. (25)", "Anat Ex. (37)", "Phys Ex. (38)", "Ex. Total (75)", "Grace", "Course Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Applied Sociology & Applied Psychology (SOCI 115 & PSYC 120) [6 Credits]",
                    "subs": ["Int. (25)", "Soci Ex. (37)", "Psyc Ex. (38)", "Ex. Total (75)", "Grace", "Course Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Communicative English (ENGL 101) [2 Credits - College Exam, Not in SGPA]",
                    "subs": ["Int. (25)", "Ex. (25)", "Total (50)", "Grade", "GP"],
                    "fill": fill_course_blue
                }
            ],
            "sample_rows": [
                [1, "ADITI SHARMA", "SATISH KUMAR SHARMA", "2025629", "202501001", 19, 24, 27, 51, 0, 70, "B+", 7, 19, 31, 17, 48, 0, 67, "B+", 7, 21, 24, 45, "O", 10],
                [2, "ADITYA KUMAR KATHERIYA", "VIJAY KUMAR", "2025630", "202501002", 20, 19, 20, 39, 0, 59, "C", 5, 20, 20, 15, 35, 2.5, 58, "C", 5, 21, 23, 44, "O", 10],
                [3, "VANSH KUMAR", "MUKESH KUMAR", "2025692", "202501064", 13, 9, 4, 13, 0, 26, "F", 0, 10, 15, 9, 24, 0, 34, "F", 0, 13, 16, 29, "C", 5]
            ]
        },
        "Semester_2": {
            "title": "B.Sc. NURSING FIRST YEAR (SECOND SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 350,
            "total_credits": 31,
            "courses": [
                {
                    "title": "Applied Biochemistry & Applied Nutrition (BIOC 135 & NUTR 140) [5 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Nursing Foundation (I & II) Theory (N-NF 125) [12 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Nursing Foundation (I & II) Practical [11 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Health/Nursing Informatics & Technology (HNIT 145) [3 Credits - College Exam]",
                    "subs": ["Int. (25)", "College Ex. (25)", "Grace", "Total (50)", "Grade", "GP"],
                    "fill": fill_course_teal
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2025601", "202502001", 18, 45, 0, 63, "B", 6, 20, 55, 0, 75, "A", 8, 38, 37, 0, 75, "A", 8, 19, 20, 0, 39, "A", 8]
            ]
        },
        "Semester_3": {
            "title": "B.Sc. NURSING SECOND YEAR (THIRD SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 300,
            "total_credits": 17,
            "courses": [
                {
                    "title": "Applied Microbiology & Infection Control (MICR 201) [3 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Adult Health Nursing I Theory (N-AHN I 215) [7 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Adult Health Nursing I Practical [7 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2024601", "202403001", 18, 57, 0, 75, "A", 8, 20, 58, 0, 78, "A", 8, 35, 35, 0, 70, "B+", 7]
            ]
        },
        "Semester_4": {
            "title": "B.Sc. NURSING SECOND YEAR (FOURTH SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 350,
            "total_credits": 21,
            "courses": [
                {
                    "title": "Pharmacology & Pathology (PHAR 205 & PATH 210) [6 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Adult Health Nursing II Theory (N-AHN II 225) [7 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Adult Health Nursing II Practical [7 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Professionalism, Values & Ethics (PROF 230) [1 Credit - College Exam]",
                    "subs": ["Int. (25)", "College Ex. (25)", "Total (50)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Elective 1 (Human Values) [1 Credit - Not in SGPA]",
                    "subs": ["Exam (100)", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2024601", "202404001", 18, 57, 0, 75, "A", 8, 20, 58, 0, 78, "A", 8, 35, 35, 0, 70, "B+", 7, 18, 20, 38, "A", 8, 70, 70, "B+", 7]
            ]
        },
        "Semester_5": {
            "title": "B.Sc. NURSING THIRD YEAR (FIFTH SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 350,
            "total_credits": 11,
            "courses": [
                {
                    "title": "Community Health Nursing I Theory (N-COMH I 310) [5 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Community Health Nursing I Practical [2 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Educational Technology / Nursing Education (EDUC 315) [3 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Introduction to Forensic Nursing (N-FORN 320) [1 Credit - College Exam]",
                    "subs": ["Int. (25)", "College Ex. (25)", "Total (50)", "Grade", "GP"],
                    "fill": fill_course_teal
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2023601", "202305001", 18, 57, 0, 75, "A", 8, 35, 35, 0, 70, "B+", 7, 20, 58, 0, 78, "A", 8, 18, 20, 38, "A", 8]
            ]
        },
        "Semester_6": {
            "title": "B.Sc. NURSING THIRD YEAR (SIXTH SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 500,
            "total_credits": 21,
            "courses": [
                {
                    "title": "Child Health Nursing (I & II) Theory (N-CHN 301) [5 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Child Health Nursing Practical [4 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Mental Health Nursing (I & II) Theory (N-MHN 305) [5 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Mental Health Nursing Practical [3 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Nursing Management & Leadership (NMLE 330) [4 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Elective 2 (Menopausal Health) [1 Credit - Not in SGPA]",
                    "subs": ["Exam (100)", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2023601", "202306001", 20, 60, 0, 80, "A+", 9, 38, 38, 0, 76, "A", 8, 20, 58, 0, 78, "A", 8, 35, 35, 0, 70, "B+", 7, 19, 54, 0, 73, "B+", 7, 76, 76, "A", 8]
            ]
        },
        "Semester_7": {
            "title": "B.Sc. NURSING FOURTH YEAR (SEVENTH SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 500,
            "total_credits": 26,
            "courses": [
                {
                    "title": "Community Health Nursing II Theory (N-COMH II 401) [5 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Community Health Nursing II Practical [2 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Nursing Research & Statistics (NRST 405) [4 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Midwifery / OBG Nursing (I & II) Theory (N-MIDW 335 & 410) [6 Credits]",
                    "subs": ["Int. (25)", "Univ Ex. (75)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Midwifery / OBG Nursing Practical [9 Credits]",
                    "subs": ["Int. (50)", "Univ Ex. (50)", "Grace", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_blue
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2022601", "202207001", 19, 60, 0, 79, "A", 8, 40, 42, 0, 82, "A+", 9, 20, 58, 0, 78, "A", 8, 19, 58, 0, 77, "A", 8, 32, 42, 0, 74, "B+", 7]
            ]
        },
        "Semester_8": {
            "title": "B.Sc. NURSING FOURTH YEAR (EIGHTH SEMESTER) UNIVERSITY EXAMINATION",
            "max_marks": 200,
            "total_credits": 12,
            "courses": [
                {
                    "title": "Core Competency Assessment Practical (INTE 415-435) [12 Credits]",
                    "subs": ["Int. (100)", "Univ Ex. (100)", "Grace", "Total (200)", "Final %", "Grade", "GP"],
                    "fill": fill_course_blue
                },
                {
                    "title": "Elective 3 (Scientific Writing Skills) [1 Credit - Not in SGPA]",
                    "subs": ["Exam (100)", "Total (100)", "Grade", "GP"],
                    "fill": fill_course_teal
                },
                {
                    "title": "Cumulative History (Sem 1 to 7 SGPA & Credits for CGPA)",
                    "subs": ["S1_SGPA", "S2_SGPA", "S3_SGPA", "S4_SGPA", "S5_SGPA", "S6_SGPA", "S7_SGPA", "CGPA"],
                    "fill": fill_course_blue
                }
            ],
            "sample_rows": [
                [1, "SAMPLE CANDIDATE 1", "FATHER NAME", "2022601", "202208001", 70, 76, 0, 146, 73.0, "B+", 7, 79, 79, "A", 8, 7.50, 6.97, 7.59, 7.67, 7.82, 7.90, 7.73, 7.50]
            ]
        }
    }

    # Generate Semester Worksheets
    for sem_key, sem_data in sem_blueprints.items():
        ws = wb.create_sheet(title=sem_key)
        ws.views.sheetView[0].showGridLines = True

        # Sheet Header Branding
        ws.merge_cells("A1:AC1")
        ws["A1"] = f"VIDYAMARKSHEET :: COLLEGE OF NURSING, SGPGIMS, LUCKNOW"
        ws["A1"].font = font_title
        ws["A1"].alignment = align_left

        ws.merge_cells("A2:AC2")
        ws["A2"] = f"{sem_data['title']} — MASTER TABULATION SHEET"
        ws["A2"].font = Font(name="Calibri", size=10, bold=True, color="2D3748")
        ws["A2"].alignment = align_left

        ws.merge_cells("A3:AC3")
        ws["A3"] = "VidyaLabs Quality Gate: Ensure Internal >= 50%, End Sem >= 50% (40% for English/Electives). Grace cap is 5 marks."
        ws["A3"].font = font_sub
        ws["A3"].alignment = align_left

        # Row 5: Course Level Group Headers
        # Demographics
        ws.merge_cells("A5:E5")
        ws["A5"] = "CANDIDATE DEMOGRAPHICS"
        ws["A5"].fill = fill_summary_navy
        ws["A5"].font = font_header_course
        ws["A5"].alignment = align_center

        curr_col = 6
        for course in sem_data["courses"]:
            num_subs = len(course["subs"])
            end_col = curr_col + num_subs - 1
            start_cell = f"{get_column_letter(curr_col)}5"
            end_cell = f"{get_column_letter(end_col)}5"
            ws.merge_cells(f"{start_cell}:{end_cell}")
            ws[start_cell] = course["title"]
            ws[start_cell].fill = course["fill"]
            ws[start_cell].font = font_header_course
            ws[start_cell].alignment = align_center
            curr_col = end_col + 1

        # Summary Header
        summary_cols = ["Grand Total", "Percentage", "Credit Score", "SGPA", "Result / Remarks"]
        sum_start = curr_col
        sum_end = curr_col + len(summary_cols) - 1
        ws.merge_cells(f"{get_column_letter(sum_start)}5:{get_column_letter(sum_end)}5")
        ws[f"{get_column_letter(sum_start)}5"] = "FINAL SEMESTER EVALUATION & AUDIT"
        ws[f"{get_column_letter(sum_start)}5"].fill = fill_summary_navy
        ws[f"{get_column_letter(sum_start)}5"].font = font_header_course
        ws[f"{get_column_letter(sum_start)}5"].alignment = align_center

        # Row 6: Detailed Column Sub-Headers
        sub_headers_demographics = ["S.No.", "Student Name", "Father's Name", "Enroll No.", "Roll No."]
        for i, h in enumerate(sub_headers_demographics, start=1):
            cell = ws.cell(row=6, column=i, value=h)
            cell.fill = fill_sub_light
            cell.font = font_header_sub
            cell.alignment = align_center
            cell.border = border_cell

        curr_col = 6
        for course in sem_data["courses"]:
            for sub in course["subs"]:
                cell = ws.cell(row=6, column=curr_col, value=sub)
                cell.fill = fill_grace_highlight if "Grace" in sub else fill_sub_light
                cell.font = font_header_sub
                cell.alignment = align_center
                cell.border = border_cell
                curr_col += 1

        for h in summary_cols:
            cell = ws.cell(row=6, column=curr_col, value=h)
            cell.fill = fill_sub_light
            cell.font = font_header_sub
            cell.alignment = align_center
            cell.border = border_cell
            curr_col += 1

        # Populate Sample Rows
        row_idx = 7
        for sample in sem_data.get("sample_rows", []):
            for col_idx, val in enumerate(sample, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = font_data
                cell.border = border_cell
                cell.alignment = align_left if col_idx in [2, 3] else align_center

            # Add sample evaluation formula/values for the summary block
            c_gt = ws.cell(row=row_idx, column=curr_col - 5, value=182 if sem_key=="Semester_1" else sem_data["max_marks"] * 0.72)
            c_pct = ws.cell(row=row_idx, column=curr_col - 4, value=72.80)
            c_cs = ws.cell(row=row_idx, column=curr_col - 3, value=84)
            c_sgpa = ws.cell(row=row_idx, column=curr_col - 2, value=7.00)
            c_res = ws.cell(row=row_idx, column=curr_col - 1, value="PASS" if sample[0] != 3 else "FAIL")

            for c in [c_gt, c_pct, c_cs, c_sgpa, c_res]:
                c.font = font_bold_data
                c.border = border_cell
                c.alignment = align_center

            row_idx += 1

        # Adjust Column Widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row >= 5 and cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)
        ws.column_dimensions["B"].width = 24  # Student Name
        ws.column_dimensions["C"].width = 24  # Father's Name

    # Create Grading Reference Sheet
    ws_ref = wb.create_sheet(title="Grading_Scale_Reference")
    ws_ref.views.sheetView[0].showGridLines = True
    ws_ref.merge_cells("A1:F1")
    ws_ref["A1"] = "VIDYAMARKSHEET: INC & SGPGIMS OFFICIAL GRADING REFERENCE"
    ws_ref["A1"].font = font_title

    ref_headers = ["Percentage Range", "Letter Grade", "Grade Point", "Performance Level", "Pass Mark Applicable To"]
    for i, h in enumerate(ref_headers, start=1):
        c = ws_ref.cell(row=3, column=i, value=h)
        c.fill = fill_summary_navy
        c.font = font_header_course
        c.alignment = align_center
        c.border = border_cell

    ref_data = [
        ["85.00% & Above", "O", 10, "Outstanding", "All Courses"],
        ["80.00% to 84.99%", "A+", 9, "Excellent", "All Courses"],
        ["75.00% to 79.99%", "A", 8, "Very Good", "All Courses"],
        ["65.00% to 74.99%", "B+", 7, "Good", "All Courses"],
        ["60.00% to 64.99%", "B", 6, "Above Average", "All Courses"],
        ["50.00% to 59.99%", "C", 5, "Average (Minimum Pass)", "All Standard Courses"],
        ["40.00% to 49.99%", "P", 4, "Pass", "Only Communicative English & Elective Modules"],
        ["Below 50.00%", "F", 0, "Fail", "Standard Courses (<40% for English/Electives)"],
        ["Absent", "Ab", 0, "Absent", "All Courses"]
    ]

    for r_idx, row in enumerate(ref_data, start=4):
        for c_idx, val in enumerate(row, start=1):
            cell = ws_ref.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            cell.alignment = align_center

    for col in ws_ref.columns:
        col_letter = get_column_letter(col[0].column)
        ws_ref.column_dimensions[col_letter].width = 22

    # Save Workbook
    filename = "VidyaMarksheet_Master_DataSheet.xlsx"
    wb.save(filename)
    print(f"Master Workbook successfully generated: {filename}")

if __name__ == "__main__":
    build_marksheet_master_workbook()