import React from "react";
import { SemesterStudentResult, EvaluatedStudentRecord } from "../../types/marksheet";

export interface NormalizedCourseRow {
  slNo: number;
  courseCode: string;
  courseTitle: string;
  credits: number;
  creditBreakdown?: string;
  internalObtained: number | string;
  internalMax: number;
  externalObtained: number | string;
  externalMax: number;
  totalObtained: number | string;
  totalMax: number;
  percentage: number;
  letterGrade: string;
  gradePoint: number;
  isPass: boolean;
  isEnglishOrElective: boolean;
  isExempted?: boolean;
  originalExamMonthYear?: string;
}

export interface NormalizedStudentInfo {
  name: string;
  fatherName: string;
  rollNo: string;
  enrollNo: string;
  collegeName: string;
  totalObtained: number;
  totalMax: number;
  percentage: number;
  sgpa: number;
  creditScore: number;
  resultStatus: string;
  remarks: string;
  attemptNumber?: number;
  attemptLabel?: string;
  attemptIndicator?: string;
  courses: NormalizedCourseRow[];
}

export function formatMarkVal(val: unknown, isExempted?: boolean): string {
  if (isExempted) return "Ex.";
  if (val === null || val === undefined || val === "") return "0";
  if (typeof val === "string") {
    const s = val.trim();
    if (s.toUpperCase() === "EX." || s.toUpperCase() === "EX" || s.toUpperCase() === "EXEMPTED") return "Ex.";
    if (s.toUpperCase() === "AB" || s.toUpperCase() === "ABSENT") return "Ab";
    if (s === "-") return "0";
    const n = parseFloat(s);
    if (!isNaN(n)) return Number.isInteger(n) ? String(n) : n.toFixed(1);
    return s;
  }
  if (typeof val === "number") {
    return Number.isInteger(val) ? String(val) : val.toFixed(1);
  }
  return String(val);
}

export function formatDecimal(val: unknown, places = 2): string {
  if (val === null || val === undefined || val === "") return "0.00";
  const n = typeof val === "number" ? val : parseFloat(String(val));
  if (isNaN(n)) return "0.00";
  return n.toFixed(places);
}

export function getQualitativeDescriptor(sgpa: number, isPass: boolean): string {
  if (!isPass) return "Fail";
  if (sgpa >= 8.5) return "Outstanding";
  if (sgpa >= 8.0) return "Excellent";
  if (sgpa >= 7.5) return "Very Good";
  if (sgpa >= 6.5) return "Good";
  if (sgpa >= 6.0) return "Above Average";
  if (sgpa >= 5.0) return "Average";
  return "Pass";
}

export function normalizeStudentData(
  raw: SemesterStudentResult | EvaluatedStudentRecord | Record<string, unknown>
): NormalizedStudentInfo {
  const isEvalRecord = "student_name" in (raw as Record<string, unknown>);
  const evalRec = isEvalRecord ? (raw as EvaluatedStudentRecord) : null;
  const semRec = !isEvalRecord ? (raw as SemesterStudentResult) : null;

  const rawObj = raw as Record<string, unknown>;
  const name = evalRec ? evalRec.student_name : semRec?.student?.name || "";
  const fatherName = evalRec ? evalRec.father_name : semRec?.student?.father_name || "";
  const rollNo = evalRec ? evalRec.roll_no : semRec?.student?.roll_no || "";
  const enrollNo = evalRec ? evalRec.enroll_no : semRec?.student?.enrollment_no || "";
  const collegeName = (rawObj.college_name as string) || "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH.";

  const totalObtained = evalRec
    ? evalRec.total_marks_obtained || 0
    : semRec?.grand_total_obtained || 0;
  const totalMax = evalRec
    ? evalRec.total_marks_max || 0
    : semRec?.grand_total_max || 0;
  const percentage = evalRec
    ? evalRec.overall_percentage || 0
    : semRec?.overall_percentage || 0;
  const sgpa = evalRec ? evalRec.sgpa || 0 : semRec?.sgpa || 0;
  const creditScore = evalRec
    ? evalRec.semester_credit_score || 0
    : semRec?.total_credit_score || 0;
  const resultStatus = evalRec ? evalRec.result_status || "PASS" : semRec?.result_status || "PASS";
  const remarks = evalRec
    ? evalRec.raw_remarks || ""
    : semRec?.remarks || "";

  const evalObj = evalRec as unknown as Record<string, unknown> | null;
  const semObj = semRec as unknown as Record<string, unknown> | null;

  const attemptNumber =
    (rawObj.attempt_number as number) ??
    (evalObj?.attempt_number as number) ??
    (semObj?.attempt_number as number) ??
    0;
  const attemptLabel =
    (rawObj.attempt_label as string) ??
    (evalObj?.attempt_label as string) ??
    (semObj?.attempt_label as string) ??
    (attemptNumber > 0 ? `REAPPEAR - ${attemptNumber}` : "MAIN");
  const attemptIndicator =
    (rawObj.attempt_indicator as string) ??
    (attemptLabel && attemptLabel !== "MAIN" ? `(${attemptLabel})` : undefined);

  const courseList: NormalizedCourseRow[] = [];

  if (evalRec && evalRec.courses) {
    let idx = 1;
    for (const [key, c] of Object.entries(evalRec.courses)) {
      if (!c) continue;
      const cObj = c as unknown as Record<string, unknown>;
      const isEx = Boolean(cObj.is_exempted || cObj.isExempted);
      const origSession = (cObj.original_exam_month_year as string) || (cObj.originalExamMonthYear as string);
      courseList.push({
        slNo: idx++,
        courseCode: c.course_code || key,
        courseTitle: c.course_title || key,
        credits: c.credits || 0,
        creditBreakdown: c.credit_breakdown || undefined,
        internalObtained: isEx ? "Ex." : (Number(c.internal_marks) || 0),
        internalMax: Number(c.internal_max) || 25,
        externalObtained: isEx ? "Ex." : (Number(c.effective_external ?? c.external_marks) || 0),
        externalMax: Number(c.external_max) || 75,
        totalObtained: Number(c.total_marks) || 0,
        totalMax: Number(c.total_max) || 100,
        percentage: Number(c.percentage) || 0,
        letterGrade: String(c.letter_grade || "C"),
        gradePoint: Number(c.grade_point) || 0,
        isPass: Boolean(c.is_pass ?? true),
        isEnglishOrElective: Boolean(c.is_english_or_elective || false),
        isExempted: isEx,
        originalExamMonthYear: origSession,
      });
    }
  } else if (semRec && Array.isArray(semRec.courses)) {
    (raw.courses as unknown as Record<string, unknown>[]).forEach((c, idx) => {
      const isEx = Boolean(c.is_exempted || c.isExempted || c.internal_obtained === "Ex." || c.external_obtained === "Ex.");
      const origSession = (c.original_exam_month_year as string) || (c.originalExamMonthYear as string);
      courseList.push({
        slNo: idx + 1,
        courseCode: String(c.course_code || ""),
        courseTitle: String(c.course_title || ""),
        credits: Number(c.credits || 0),
        creditBreakdown: c.credit_breakdown as string | undefined,
        internalObtained: isEx ? "Ex." : ((c.internal_obtained as number | string) ?? 0),
        internalMax: Number(c.internal_max || 25),
        externalObtained: isEx ? "Ex." : ((c.external_obtained as number | string) ?? 0),
        externalMax: Number(c.external_max || 75),
        totalObtained: Number(c.total_obtained || 0),
        totalMax: Number(c.total_max || 100),
        percentage: Number(c.percentage || 0),
        letterGrade: String(c.letter_grade || "C"),
        gradePoint: Number(c.grade_point || 0),
        isPass: Boolean(c.is_pass ?? true),
        isEnglishOrElective: Boolean(c.is_english_or_elective || false),
        isExempted: isEx,
        originalExamMonthYear: origSession,
      });
    });
  }

  return {
    name,
    fatherName,
    rollNo,
    enrollNo,
    collegeName,
    totalObtained,
    totalMax,
    percentage,
    sgpa,
    creditScore,
    resultStatus,
    remarks,
    attemptNumber,
    attemptLabel,
    attemptIndicator,
    courses: courseList,
  };
}

export interface LayoutStudioConfig {
  rowMinHeight: number; // in px (24 to 60)
  cellPadding: number; // in px (2 to 24)
  fontSizeGlobal: number; // in pt (8 to 12)
  fontSizeHeader: number; // in pt (9 to 14)
  topMargin: number; // in inches (1.0 to 3.2)
  signatureSpace: number; // in px (15 to 90)
  colWidthSno: number; // in % (3 to 10)
  colWidthCode: number; // in % (8 to 22)
  colWidthTitle: number; // in % (12 to 40)
  colWidthCredits: number; // in % (5 to 14)
  colWidthMarks: number; // in % (20 to 48)
  colWidthGrade: number; // in % (4 to 12)
  textDirectionCode: "horizontal" | "vertical";
  textDirectionTitle: "horizontal" | "vertical";
  textWrapping: "normal" | "nowrap";
  pageFitLayout: boolean;
}

export const DEFAULT_LAYOUT_CONFIG: LayoutStudioConfig = {
  rowMinHeight: 38,
  cellPadding: 4,
  fontSizeGlobal: 10,
  fontSizeHeader: 11,
  topMargin: 2.2,
  signatureSpace: 45,
  colWidthSno: 5,
  colWidthCode: 14,
  colWidthTitle: 18,
  colWidthCredits: 7,
  colWidthMarks: 38,
  colWidthGrade: 5,
  textDirectionCode: "vertical",
  textDirectionTitle: "vertical",
  textWrapping: "normal",
  pageFitLayout: true,
};

export function getStoredLayoutConfig(semester: number): LayoutStudioConfig {
  if (typeof window === "undefined") return { ...DEFAULT_LAYOUT_CONFIG };
  try {
    const raw =
      localStorage.getItem(`vidya_marksheet_layout_sem${semester}`) ||
      localStorage.getItem(`vidya_layout_prefs_sem_${semester}`);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        ...DEFAULT_LAYOUT_CONFIG,
        ...parsed,
        // Ensure signatureSpace fallback for existing saved configs
        signatureSpace: typeof parsed.signatureSpace === "number" ? parsed.signatureSpace : 45,
        // If user previously had 26 as title width, keep or migrate gracefully
        colWidthTitle: typeof parsed.colWidthTitle === "number" ? parsed.colWidthTitle : 18,
      };
    }
  } catch {}
  return { ...DEFAULT_LAYOUT_CONFIG };
}

export async function syncLayoutToBackend(config: LayoutStudioConfig, _semester?: number): Promise<boolean> {
  void _semester;
  try {
    const payload = {
      col_width_sno: config.colWidthSno,
      col_width_code: config.colWidthCode,
      col_width_title: config.colWidthTitle,
      col_width_credits: config.colWidthCredits,
      row_min_height: config.rowMinHeight,
      cell_padding: config.cellPadding,
      signature_space: config.signatureSpace,
      top_margin: `${config.topMargin}in`,
      font_size_table: `${config.fontSizeGlobal}pt`,
      font_size_header: `${config.fontSizeHeader}pt`,
      text_direction_code: config.textDirectionCode,
      text_direction_title: config.textDirectionTitle,
    };

    let res: Response | null = await fetch("http://127.0.0.1:8000/api/pdf/template-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => null);

    if (!res || !res.ok) {
      res = await fetch("/api/pdf/template-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch(() => null);
    }
    return !!(res && res.ok);
  } catch (err) {
    console.warn("Failed to sync layout config to backend:", err);
    return false;
  }
}

export function saveStoredLayoutConfig(semester: number, config: LayoutStudioConfig): void {
  if (typeof window === "undefined") return;
  try {
    const json = JSON.stringify(config);
    localStorage.setItem(`vidya_marksheet_layout_sem${semester}`, json);
    localStorage.setItem(`vidya_layout_prefs_sem_${semester}`, json);
    syncLayoutToBackend(config, semester);
  } catch {}
}

export function getLayoutCssVariables(config?: LayoutStudioConfig): React.CSSProperties {
  const c = config || DEFAULT_LAYOUT_CONFIG;
  return {
    "--table-row-height": `${c.rowMinHeight}px`,
    "--cell-padding": `${c.cellPadding}px`,
    "--global-font-size": `${c.fontSizeGlobal}pt`,
    "--header-font-size": `${c.fontSizeHeader}pt`,
    "--top-margin": `${c.topMargin}in`,
    "--sig-space": `${c.signatureSpace ?? 45}px`,
    "--col-width-sno": `${c.colWidthSno}%`,
    "--col-width-code": `${c.colWidthCode}%`,
    "--col-width-title": `${c.colWidthTitle}%`,
    "--col-width-credits": `${c.colWidthCredits}%`,
    "--col-width-marks": `${c.colWidthMarks}%`,
    "--col-width-grade": `${c.colWidthGrade}%`,
  } as React.CSSProperties;
}

export interface MarksheetBaseProps {
  student: SemesterStudentResult | EvaluatedStudentRecord | Record<string, unknown>;
  sessionMonthYear?: string;
  issueDate?: string;
  collegeName?: string;
  className?: string;
  layoutConfig?: LayoutStudioConfig;
  isDirectEditing?: boolean;
}

export interface VerticalTextProps {
  lines: string | string[];
  isVertical: boolean;
  isNowrap?: boolean;
  horizontalText?: string;
  className?: string;
}

export const VerticalOrHorizontalText: React.FC<VerticalTextProps> = ({
  lines,
  isVertical,
  isNowrap = false,
  horizontalText,
  className = "",
}) => {
  const lineArray = Array.isArray(lines) ? lines : [lines];

  if (!isVertical) {
    return (
      <div className={`horizontal-cell-text font-bold text-center leading-tight ${className}`}>
        {horizontalText || lineArray.join(" ")}
      </div>
    );
  }

  return (
    <div className={`vertical-cell-wrapper flex items-center justify-center text-center w-full h-full my-auto ${className}`}>
      <div
        className={`vertical-text ${isNowrap ? "nowrap" : ""}`}
        style={{
          writingMode: "vertical-rl",
          transform: "rotate(180deg)",
          textOrientation: "mixed",
          whiteSpace: isNowrap ? "nowrap" : "normal",
          display: "inline-block",
          textAlign: "center",
          lineHeight: 1.15,
        }}
      >
        {lineArray.map((line, idx) => (
          <span
            key={idx}
            className="vertical-text-subline block font-bold tracking-normal px-0.5"
            style={{
              whiteSpace: isNowrap ? "nowrap" : "normal",
            }}
          >
            {line}
          </span>
        ))}
      </div>
    </div>
  );
};

export const MarksheetStyles = `
  .marksheet-page {
    width: 8.5in;
    min-height: 14in;
    height: 14in;
    max-height: 14in;
    padding-top: var(--top-margin, 2.2in) !important;
    padding-bottom: 0.25in;
    padding-left: 0.25in;
    padding-right: 0.25in;
    margin: 0 auto;
    background: #ffffff;
    color: #000000;
    font-family: Calibri, 'Segoe UI', Arial, sans-serif;
    font-size: var(--global-font-size, 10pt) !important;
    line-height: 1.25;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
    transition: padding 0.15s ease-out;
  }

  /* Full-Page Even Distribution (Page-Fit Layout) */
  .marksheet-page.page-fit-active .marksheet-content-body {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 0;
  }

  .marksheet-page.page-fit-active .marksheet-table-wrapper {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    justify-content: stretch;
    min-height: 0;
    margin: 4px 0;
  }

  .marksheet-page.page-fit-active .marksheet-table-wrapper table.marksheet-main-table {
    height: 100% !important;
    flex: 1 1 auto;
    display: table;
  }

  .marksheet-page.page-fit-active .marksheet-table-wrapper table.marksheet-main-table tbody {
    height: 100%;
  }

  .marksheet-page.page-fit-active .marksheet-table-wrapper table.marksheet-main-table tbody tr.marksheet-course-row {
    height: 100% !important;
    min-height: var(--table-row-height, 38px) !important;
  }

  .marksheet-page.page-fit-active .marksheet-table-wrapper table.marksheet-main-table tbody tr.marksheet-total-row {
    height: var(--table-row-height, 38px) !important;
    max-height: 44px;
  }

  .marksheet-page .header-title-text {
    font-size: var(--header-font-size, 11pt) !important;
  }

  .marksheet-page table tr {
    min-height: var(--table-row-height, 38px) !important;
  }

  .marksheet-page table td,
  .marksheet-page table th {
    padding: var(--cell-padding, 4px) !important;
    font-size: var(--global-font-size, 10pt) !important;
  }

  /* Vertical text cell alignments */
  .vertical-cell-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 100%;
    height: 100%;
  }

  .vertical-text {
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    text-orientation: mixed;
    white-space: normal;
    display: inline-block;
    text-align: center;
    line-height: 1.15;
  }

  .vertical-text.nowrap {
    white-space: nowrap !important;
  }

  .vertical-text-subline {
    display: block;
    margin: 0 1px;
  }

  /* 2-row, 2-column Distinct Bordered Results & Remarks Table */
  .result-remarks-table {
    border: 1.5px solid #000000 !important;
    width: 100% !important;
    border-collapse: collapse !important;
    margin-top: 6px;
    margin-bottom: 6px;
  }

  .result-remarks-table td {
    padding: var(--cell-padding, 4px) 8px !important;
    font-size: var(--global-font-size, 10.5pt) !important;
    line-height: 1.35;
    color: #000000;
    background: #ffffff;
  }

  .result-remarks-table tr:first-child {
    border-bottom: 1.5px solid #000000 !important;
  }

  .result-remarks-table td.col-label {
    width: 18% !important;
    border-right: 1.5px solid #000000 !important;
    font-weight: bold !important;
    text-align: center !important;
  }

  .result-remarks-table td.col-value {
    font-weight: bold !important;
    text-align: center !important;
  }

  .marksheet-page table td,
  .marksheet-page table th {
    padding: var(--cell-padding, 4px) !important;
    font-size: var(--global-font-size, 10pt) !important;
  }

  .marksheet-page .col-sno,
  .marksheet-page table thead tr:first-child th:nth-child(1) {
    width: var(--col-width-sno, 5%) !important;
  }
  .marksheet-page .col-code,
  .marksheet-page table thead tr:first-child th:nth-child(2) {
    width: var(--col-width-code, 14%) !important;
  }
  .marksheet-page .col-title,
  .marksheet-page table thead tr:first-child th:nth-child(3) {
    width: var(--col-width-title, 18%) !important;
  }
  .marksheet-page .col-credits,
  .marksheet-page table thead tr:first-child th:nth-child(4) {
    width: var(--col-width-credits, 7%) !important;
  }
  .marksheet-page .col-marks {
    width: var(--col-width-marks, 38%) !important;
  }
  .marksheet-page .col-grade {
    width: var(--col-width-grade, 5%) !important;
  }

  /* Direct Editing visual affordance */
  .marksheet-page[data-direct-editing="true"] [contenteditable="true"],
  .marksheet-page.direct-editing-active [contenteditable="true"] {
    outline: 1px dashed rgba(59, 130, 246, 0.45);
    border-radius: 2px;
    cursor: text;
    transition: all 0.12s ease-in-out;
  }

  .marksheet-page[data-direct-editing="true"] [contenteditable="true"]:hover,
  .marksheet-page.direct-editing-active [contenteditable="true"]:hover {
    outline: 1.5px dashed #2563eb;
    background-color: rgba(239, 246, 255, 0.65);
  }

  .marksheet-page[data-direct-editing="true"] [contenteditable="true"]:focus,
  .marksheet-page.direct-editing-active [contenteditable="true"]:focus {
    outline: 2px solid #2563eb;
    background-color: #ffffff;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
  }

  @media print {
    @page {
      size: 8.5in 14in;
      margin: 0;
    }
    body {
      margin: 0 !important;
      padding: 0 !important;
    }
    .marksheet-page {
      width: 100% !important;
      min-height: 100% !important;
      padding-top: var(--top-margin, 2.2in) !important;
      padding-bottom: 0.25in !important;
      padding-left: 0.25in !important;
      padding-right: 0.25in !important;
      margin: 0 !important;
      box-shadow: none !important;
      border: none !important;
    }
    .marksheet-page table tr {
      min-height: var(--table-row-height, 38px) !important;
      height: var(--table-row-height, 38px) !important;
    }
    .marksheet-page table td,
    .marksheet-page table th {
      padding: var(--cell-padding, 4px) !important;
      font-size: var(--global-font-size, 10pt) !important;
    }
    .marksheet-page [contenteditable="true"] {
      outline: none !important;
      background-color: transparent !important;
      box-shadow: none !important;
    }
    .no-print, .marksheet-studio-toolbar, .marksheet-studio-drawer {
      display: none !important;
    }
  }
`;

export const DemographicsBlock: React.FC<{
  info: NormalizedStudentInfo;
  collegeName?: string;
  isDirectEditing?: boolean;
}> = ({ info, collegeName, isDirectEditing }) => (
  <table
    className="w-full border-collapse mb-3.5 text-[11pt] leading-snug"
    contentEditable={isDirectEditing}
    suppressContentEditableWarning={true}
  >
    <tbody>
      <tr>
        <td className="text-left font-bold py-0.5 text-black">
          NAME: {info.name}
        </td>
        <td className="text-right font-bold py-0.5 text-black">
          ENROLLMENT NO: {info.enrollNo}
        </td>
      </tr>
      <tr>
        <td className="text-left font-bold py-0.5 text-black">
          S/o/D/o: {info.fatherName}
        </td>
        <td className="text-right font-bold py-0.5 text-black">
          ROLL NO: {info.rollNo}
        </td>
      </tr>
      <tr>
        <td colSpan={2} className="text-left font-bold py-0.5 text-black">
          NAME OF COLLEGE: {collegeName || "COLLEGE OF NURSING, SGPGIMS, LUCKNOW, UTTAR PRADESH."}
        </td>
      </tr>
    </tbody>
  </table>
);

export const SgpaSummaryBox: React.FC<{
  sgpa: number;
  creditScore: number;
  labelSgpa?: string;
  labelScore?: string;
  isDirectEditing?: boolean;
}> = ({
  sgpa,
  creditScore,
  labelSgpa = "Semester Grade Point Average (SGPA)",
  labelScore = "Semester Credit Score Average",
  isDirectEditing,
}) => (
  <table
    className="w-[65%] mx-auto my-2.5 border-collapse border border-black text-center"
    contentEditable={isDirectEditing}
    suppressContentEditableWarning={true}
  >
    <tbody>
      <tr>
        <td className="border border-black font-bold text-[10.5pt] py-1.5 px-3 bg-white text-black">
          {labelSgpa}
        </td>
        <td className="border border-black font-bold text-[10.5pt] py-1.5 px-3 bg-white text-black">
          {labelScore}
        </td>
      </tr>
      <tr>
        <td className="border border-black font-bold text-[11.5pt] py-1 px-3 bg-white text-black">
          {formatDecimal(sgpa)}
        </td>
        <td className="border border-black font-bold text-[11.5pt] py-1 px-3 bg-white text-black">
          {formatDecimal(creditScore)}
        </td>
      </tr>
    </tbody>
  </table>
);

export const ResultRemarksBlock: React.FC<{
  resultStatus: string;
  remarks?: string;
  sgpa: number;
  isDirectEditing?: boolean;
}> = ({ resultStatus, remarks, sgpa, isDirectEditing }) => {
  const isPass = resultStatus.toUpperCase().includes("PASS");
  const descriptor = getQualitativeDescriptor(sgpa, isPass);
  const displayResult = resultStatus.toUpperCase().startsWith("PASS WITH")
    ? resultStatus
    : isPass
    ? "PASS"
    : resultStatus || "FAIL";

  const displayRemarks = `Grading Performance - ${descriptor}${
    remarks && !remarks.toUpperCase().includes("PASS") ? ` (${remarks})` : ""
  }`;

  return (
    <table
      className="result-remarks-table w-full border-collapse my-2 text-[10.5pt] leading-normal"
      style={{
        border: "1.5px solid #000000",
        borderCollapse: "collapse",
        width: "100%",
      }}
      contentEditable={isDirectEditing}
      suppressContentEditableWarning={true}
    >
      <tbody>
        <tr style={{ borderBottom: "1.5px solid #000000" }}>
          <td
            className="col-label font-bold text-center py-1.5 px-3 bg-white text-black"
            style={{
              width: "18%",
              borderRight: "1.5px solid #000000",
            }}
          >
            Result
          </td>
          <td className="col-value font-bold text-center py-1.5 px-3 bg-white text-black">
            {displayResult}
          </td>
        </tr>
        <tr>
          <td
            className="col-label font-bold text-center py-1.5 px-3 bg-white text-black"
            style={{
              width: "18%",
              borderRight: "1.5px solid #000000",
            }}
          >
            Remarks
          </td>
          <td className="col-value font-bold text-center py-1.5 px-3 bg-white text-black">
            {displayRemarks}
          </td>
        </tr>
      </tbody>
    </table>
  );
};

export const StatutoryNote: React.FC<{
  noteText?: string;
  isDirectEditing?: boolean;
}> = ({
  noteText = "Note: In case of any discrepancy in the marksheet, candidate may apply for correction within a period of four weeks from the date of issue to the office of the Executive Registrar.",
  isDirectEditing,
}) => (
  <div
    className="my-1.5 text-[9.5pt] leading-tight text-justify text-black"
    contentEditable={isDirectEditing}
    suppressContentEditableWarning={true}
  >
    <span className="font-bold">Note:</span> {noteText.replace(/^Note:\s*/i, "")}
  </div>
);

export const SignaturesFooter: React.FC<{
  sig1?: string;
  sig2?: string;
  sig3?: string;
  sig4?: string;
  issueDate?: string;
  noteText?: string;
  isDirectEditing?: boolean;
}> = ({
  sig1 = "Prepared By",
  sig2 = "Checked By",
  sig3 = "Sub-Dean (Nursing)",
  sig4,
  issueDate,
  noteText = "Note: In case of any discrepancy in the marksheet, candidate may apply for correction within a period of four weeks from the date of issue to the office of the Executive Registrar.",
  isDirectEditing,
}) => {
  const today = issueDate || new Date().toLocaleDateString("en-GB");

  return (
    <div className="mt-3 pt-1">
      {/* Signatures Row */}
      <div
        className="flex justify-between items-end mb-2.5 px-2 text-center"
        contentEditable={isDirectEditing}
        suppressContentEditableWarning={true}
      >
        <div className="w-[28%] text-center flex flex-col justify-end">
          <div
            className="signature-clearance-area w-full"
            style={{ minHeight: "var(--sig-space, 45px)", height: "var(--sig-space, 45px)" }}
          />
          <div className="border-t border-black mb-1 w-full" />
          <div className="text-[10.5pt] font-bold text-black">{sig1}</div>
        </div>
        <div className="w-[28%] text-center flex flex-col justify-end">
          <div
            className="signature-clearance-area w-full"
            style={{ minHeight: "var(--sig-space, 45px)", height: "var(--sig-space, 45px)" }}
          />
          <div className="border-t border-black mb-1 w-full" />
          <div className="text-[10.5pt] font-bold text-black">{sig2}</div>
        </div>
        <div className="w-[28%] text-center flex flex-col justify-end">
          <div
            className="signature-clearance-area w-full"
            style={{ minHeight: "var(--sig-space, 45px)", height: "var(--sig-space, 45px)" }}
          />
          <div className="border-t border-black mb-1 w-full" />
          <div className="text-[10.5pt] font-bold text-black">{sig3}</div>
        </div>
        {sig4 && (
          <div className="w-[24%] text-center flex flex-col justify-end">
            <div
              className="signature-clearance-area w-full"
              style={{ minHeight: "var(--sig-space, 45px)", height: "var(--sig-space, 45px)" }}
            />
            <div className="border-t border-black mb-1 w-full" />
            <div className="text-[10.5pt] font-bold text-black">{sig4}</div>
          </div>
        )}
      </div>

      {/* Statutory Note - Placed strictly AFTER all signature lines and BEFORE Date/Legend Overleaf */}
      <div
        className="my-1.5 text-[9.5pt] leading-tight text-justify text-black"
        contentEditable={isDirectEditing}
        suppressContentEditableWarning={true}
      >
        <span className="font-bold">Note:</span> {noteText.replace(/^Note:\s*/i, "")}
      </div>

      {/* Date & Legend Overleaf Row */}
      <div
        className="flex justify-between items-center text-[10pt] font-bold px-1 text-black mb-1"
        contentEditable={isDirectEditing}
        suppressContentEditableWarning={true}
      >
        <div>Date: {today}</div>
        <div>Legend Overleaf</div>
      </div>

      {/* Platform Branding */}
      <div className="border-t border-dotted border-gray-400 pt-1 text-center text-[7.5pt] text-gray-600">
        VidyaMarksheet (Developed at <span className="font-bold">VidyaLabs</span> | <span className="font-bold">Priyanka Kumari</span>)
      </div>
    </div>
  );
};

export function getSampleStudentForSemester(sem: number): EvaluatedStudentRecord {
  const baseStudents: Record<number, Record<string, unknown>> = {
    1: {
      roll_no: "202601001",
      enroll_no: "CON/2026/001",
      student_name: "Swati Shukla",
      father_name: "Mr. R. K. Shukla",
      result_status: "PASS",
      sgpa: 7.00,
      total_marks_obtained: 185,
      total_marks_max: 250,
      overall_percentage: 74.0,
      semester_credit_score: 84.0,
      courses: {
        ENGL: { course_code: "ENGL 101", course_title: "Communicative English", credits: 2, internal_marks: 20, internal_max: 25, external_marks: 20, external_max: 25, total_marks: 40, total_max: 50, percentage: 80.0, letter_grade: "A", grade_point: 8, is_pass: true, is_english_or_elective: true },
        ANAT: { course_code: "ANAT 105 & PHYS 110", course_title: "Applied Anatomy & Applied Physiology", credits: 6, credit_breakdown: "3+3", internal_marks: 18, internal_max: 25, external_marks: 54, external_max: 75, total_marks: 72, total_max: 100, percentage: 72.0, letter_grade: "B+", grade_point: 7, is_pass: true, is_english_or_elective: false },
        SOCI: { course_code: "SOCI 115 & PSYC 120", course_title: "Applied Sociology & Applied Psychology", credits: 6, credit_breakdown: "3+3", internal_marks: 19, internal_max: 25, external_marks: 54, external_max: 75, total_marks: 73, total_max: 100, percentage: 73.0, letter_grade: "B+", grade_point: 7, is_pass: true, is_english_or_elective: false }
      }
    },
    2: {
      roll_no: "202601002",
      enroll_no: "CON/2026/002",
      student_name: "Km Roli",
      father_name: "Mr. Santosh Kumar",
      result_status: "PASS",
      sgpa: 7.55,
      total_marks_obtained: 247,
      total_marks_max: 350,
      overall_percentage: 70.57,
      semester_credit_score: 234.0,
      courses: {
        BIOC: { course_code: "BIOC 135 & NUTR 140", course_title: "Applied Biochemistry & Applied Nutrition & Dietetics", credits: 5, credit_breakdown: "2+3", internal_marks: 19, internal_max: 25, external_marks: 52, external_max: 75, total_marks: 71, total_max: 100, percentage: 71.0, letter_grade: "B+", grade_point: 7, is_pass: true },
        NNF_TH: { course_code: "N-NF (I & II) 125", course_title: "Nursing Foundation I & II (Theory)", credits: 12, credit_breakdown: "6+6", internal_marks: 18, internal_max: 25, external_marks: 54, external_max: 75, total_marks: 72, total_max: 100, percentage: 72.0, letter_grade: "B+", grade_point: 7, is_pass: true },
        NNF_PR: { course_code: "N-NF (I & II) 125", course_title: "Nursing Foundation I & II (Practical)", credits: 11, credit_breakdown: "4+7", internal_marks: 38, internal_max: 50, external_marks: 38, external_max: 50, total_marks: 76, total_max: 100, percentage: 76.0, letter_grade: "A", grade_point: 8, is_pass: true },
        HNIT: { course_code: "HNIT 145", course_title: "Health/Nursing Informatics & Technology", credits: 3, internal_marks: 14, internal_max: 25, external_marks: 14, external_max: 25, total_marks: 28, total_max: 50, percentage: 56.0, letter_grade: "P", grade_point: 0, is_pass: true, is_english_or_elective: true }
      }
    },
    3: {
      roll_no: "202601003",
      enroll_no: "CON/2026/003",
      student_name: "Pooja Verma",
      father_name: "Mr. Ramesh Verma",
      result_status: "PASS",
      sgpa: 7.65,
      total_marks_obtained: 228,
      total_marks_max: 300,
      overall_percentage: 76.0,
      semester_credit_score: 130.0,
      courses: {
        MICR: { course_code: "MICR 201", course_title: "Applied Microbiology & Infection Control", credits: 4, internal_marks: 19, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        AHN1_TH: { course_code: "N-AHN (I) 215", course_title: "Adult Health Nursing I (Theory)", credits: 7, internal_marks: 18, internal_max: 25, external_marks: 57, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        AHN1_PR: { course_code: "N-AHN (I) 215", course_title: "Adult Health Nursing I (Practical)", credits: 6, internal_marks: 39, internal_max: 50, external_marks: 39, external_max: 50, total_marks: 78, total_max: 100, percentage: 78.0, letter_grade: "A", grade_point: 8, is_pass: true }
      }
    },
    4: {
      roll_no: "202601004",
      enroll_no: "CON/2026/004",
      student_name: "Akanksha Mishra",
      father_name: "Mr. Devendra Mishra",
      result_status: "PASS",
      sgpa: 7.70,
      total_marks_obtained: 262,
      total_marks_max: 350,
      overall_percentage: 74.86,
      semester_credit_score: 154.0,
      courses: {
        PHAR_PATH: { course_code: "PHAR 205 & PATH 210", course_title: "Pharmacology & Pathology (I & II) & Genetics", credits: 6, credit_breakdown: "3+3", internal_marks: 19, internal_max: 25, external_marks: 53, external_max: 75, total_marks: 72, total_max: 100, percentage: 72.0, letter_grade: "B+", grade_point: 7, is_pass: true },
        AHN2_TH: { course_code: "N-AHN (II) 225", course_title: "Adult Health Nursing II (Theory)", credits: 7, internal_marks: 19, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        AHN2_PR: { course_code: "N-AHN (II) 225", course_title: "Adult Health Nursing II (Practical)", credits: 7, internal_marks: 39, internal_max: 50, external_marks: 39, external_max: 50, total_marks: 78, total_max: 100, percentage: 78.0, letter_grade: "A", grade_point: 8, is_pass: true },
        PROF: { course_code: "PROF 230", course_title: "Professional Values & Ethics including Bioethics", credits: 1, internal_marks: 19, internal_max: 25, external_marks: 18, external_max: 25, total_marks: 37, total_max: 50, percentage: 74.0, letter_grade: "P", grade_point: 0, is_pass: true, is_english_or_elective: true }
      }
    },
    5: {
      roll_no: "202601005",
      enroll_no: "CON/2026/005",
      student_name: "Shivani Pandey",
      father_name: "Mr. Anand Pandey",
      result_status: "PASS",
      sgpa: 7.82,
      total_marks_obtained: 260,
      total_marks_max: 350,
      overall_percentage: 74.29,
      semester_credit_score: 86.0,
      courses: {
        CHN1_TH: { course_code: "N-CHN (I) 301", course_title: "Community Health Nursing I (Theory)", credits: 5, internal_marks: 19, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        CHN1_PR: { course_code: "N-CHN (I) 301", course_title: "Community Health Nursing I (Practical)", credits: 2, internal_marks: 38, internal_max: 50, external_marks: 38, external_max: 50, total_marks: 76, total_max: 100, percentage: 76.0, letter_grade: "A", grade_point: 8, is_pass: true },
        EDUC: { course_code: "EDUC 305", course_title: "Educational Technology / Nursing Education", credits: 3, internal_marks: 18, internal_max: 25, external_marks: 54, external_max: 75, total_marks: 72, total_max: 100, percentage: 72.0, letter_grade: "B+", grade_point: 7, is_pass: true },
        FORE: { course_code: "FORE 310", course_title: "Forensic Nursing & Indian Laws", credits: 1, internal_marks: 18, internal_max: 25, external_marks: 19, external_max: 25, total_marks: 37, total_max: 50, percentage: 74.0, letter_grade: "P", grade_point: 0, is_pass: true, is_english_or_elective: true }
      }
    },
    6: {
      roll_no: "202601006",
      enroll_no: "CON/2026/006",
      student_name: "Anjali Gupta",
      father_name: "Mr. Vinod Gupta",
      result_status: "PASS",
      sgpa: 7.52,
      total_marks_obtained: 375,
      total_marks_max: 500,
      overall_percentage: 75.0,
      semester_credit_score: 158.0,
      courses: {
        CHN_CHILD_TH: { course_code: "N-CHN (I & II) 315", course_title: "Child Health Nursing I & II (Theory)", credits: 4, internal_marks: 18, internal_max: 25, external_marks: 55, external_max: 75, total_marks: 73, total_max: 100, percentage: 73.0, letter_grade: "B+", grade_point: 7, is_pass: true },
        CHN_CHILD_PR: { course_code: "N-CHN (I & II) 315", course_title: "Child Health Nursing I & II (Practical)", credits: 3, internal_marks: 38, internal_max: 50, external_marks: 37, external_max: 50, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        MHN_TH: { course_code: "N-MHN (I & II) 325", course_title: "Mental Health Nursing I & II (Theory)", credits: 4, internal_marks: 19, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        MHN_PR: { course_code: "N-MHN (I & II) 325", course_title: "Mental Health Nursing I & II (Practical)", credits: 3, internal_marks: 38, internal_max: 50, external_marks: 39, external_max: 50, total_marks: 77, total_max: 100, percentage: 77.0, letter_grade: "A", grade_point: 8, is_pass: true },
        LEAD: { course_code: "N-LEAD 330", course_title: "Nursing Management & Leadership", credits: 7, internal_marks: 19, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true }
      }
    },
    7: {
      roll_no: "202601007",
      enroll_no: "CON/2026/007",
      student_name: "Divya Singh",
      father_name: "Mr. Rajendra Singh",
      result_status: "PASS",
      sgpa: 7.77,
      total_marks_obtained: 380,
      total_marks_max: 500,
      overall_percentage: 76.0,
      semester_credit_score: 202.0,
      courses: {
        CHN2_TH: { course_code: "N-CHN (II) 401", course_title: "Community Health Nursing II (Theory)", credits: 5, internal_marks: 19, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 75, total_max: 100, percentage: 75.0, letter_grade: "A", grade_point: 8, is_pass: true },
        CHN2_PR: { course_code: "N-CHN (II) 401", course_title: "Community Health Nursing II (Practical)", credits: 2, internal_marks: 38, internal_max: 50, external_marks: 39, external_max: 50, total_marks: 77, total_max: 100, percentage: 77.0, letter_grade: "A", grade_point: 8, is_pass: true },
        RES: { course_code: "N-NRES 405", course_title: "Nursing Research & Statistics", credits: 4, internal_marks: 19, internal_max: 25, external_marks: 57, external_max: 75, total_marks: 76, total_max: 100, percentage: 76.0, letter_grade: "A", grade_point: 8, is_pass: true },
        MIDW_TH: { course_code: "MIDW 410", course_title: "Midwifery/Obstetrics & Gynaecology I & II (Theory)", credits: 6, internal_marks: 18, internal_max: 25, external_marks: 56, external_max: 75, total_marks: 74, total_max: 100, percentage: 74.0, letter_grade: "B+", grade_point: 7, is_pass: true },
        MIDW_PR: { course_code: "MIDW 410", course_title: "Midwifery/Obstetrics & Gynaecology I & II (Practical)", credits: 9, internal_marks: 39, internal_max: 50, external_marks: 39, external_max: 50, total_marks: 78, total_max: 100, percentage: 78.0, letter_grade: "A", grade_point: 8, is_pass: true }
      }
    },
    8: {
      roll_no: "202601008",
      enroll_no: "CON/2026/008",
      student_name: "Sneha Yadav",
      father_name: "Mr. Harish Chandra Yadav",
      result_status: "PASS",
      sgpa: 8.50,
      total_marks_obtained: 214,
      total_marks_max: 250,
      overall_percentage: 85.6,
      semester_credit_score: 102.0,
      courses: {
        INTE: { course_code: "INTE 415 - 435", course_title: "Competency Assessment (Internship / Intensive Clinical Practicum)", credits: 12, internal_marks: 85, internal_max: 100, external_marks: 86, external_max: 100, total_marks: 171, total_max: 200, percentage: 85.5, letter_grade: "O", grade_point: 10, is_pass: true },
        ELEC: { course_code: "Elective-3", course_title: "*Scientific Writing Skills (Elective)", credits: 1, internal_marks: 21, internal_max: 25, external_marks: 22, external_max: 25, total_marks: 43, total_max: 50, percentage: 86.0, letter_grade: "P", grade_point: 0, is_pass: true, is_english_or_elective: true }
      }
    }
  };

  const candidate = baseStudents[sem] || baseStudents[1];
  return {
    ...candidate,
    is_overall_pass: true,
    failed_courses: [],
    grace_awarded: null,
    distinction_courses: [],
    raw_remarks: "Grading Performance - Excellent"
  } as unknown as EvaluatedStudentRecord;
}

