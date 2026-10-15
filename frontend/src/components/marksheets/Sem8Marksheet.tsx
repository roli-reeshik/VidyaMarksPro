"use client";

import React from "react";
import {
  MarksheetBaseProps,
  normalizeStudentData,
  formatMarkVal,
  formatDecimal,
  DemographicsBlock,
  SignaturesFooter,
  getLayoutCssVariables,
  MarksheetStyles,
  VerticalOrHorizontalText,
} from "./shared";

export interface CumulativeSemesterRecord {
  semesterNumber: number;
  semesterName: string;
  prescribedCredits: number;
  sgpaCredits: number;
  obtainedMarks?: number;
  maxMarks: number;
  sgpa?: number;
  resultStatus?: string;
}

export interface Sem8MarksheetProps extends MarksheetBaseProps {
  cumulativeHistory?: CumulativeSemesterRecord[];
  finalCgpa?: number;
  finalClassification?: string;
}

export const Sem8Marksheet: React.FC<Sem8MarksheetProps> = ({
  student,
  sessionMonthYear = "JULY - 2026",
  issueDate,
  collegeName,
  cumulativeHistory,
  finalCgpa,
  finalClassification,
  layoutConfig,
  isDirectEditing = false,
  className = "",
}) => {
  const info = normalizeStudentData(student);
  const layoutStyle = getLayoutCssVariables(layoutConfig);

  const isCodeVertical = layoutConfig?.textDirectionCode !== "horizontal";
  const isTitleVertical = layoutConfig?.textDirectionTitle !== "horizontal";
  const isNowrap = layoutConfig?.textWrapping === "nowrap";

  // Match or find Semester 8 courses
  const competency = info.courses.find(
    (c) =>
      c.courseCode.includes("INTE") ||
      c.courseTitle.toLowerCase().includes("competency") ||
      c.courseTitle.toLowerCase().includes("internship") ||
      c.totalMax >= 150
  );
  const elective = info.courses.find(
    (c) =>
      c.courseCode.toLowerCase().includes("elective") ||
      c.courseTitle.toLowerCase().includes("scientific") ||
      c.totalMax <= 50
  );

  const displayCourses = [
    {
      slNo: "01.",
      codeLines: ["INTE 415,420,425,", "430 & 435"],
      codeText: competency?.courseCode || "INTE 415 - 435",
      titleLines: [
        "Competency Assessment",
        "1. Community Health Nursing, 2. Adult Health Nursing,",
        "3. Child Health Nursing, 4. Mental Health Nursing,",
        "5. Midwifery/OBG Nursing",
      ],
      titleText: "Competency Assessment (Internship / Intensive Clinical Practicum)",
      credits: "12",
      iaObtd: formatMarkVal(competency?.internalObtained ?? 85),
      iaMax: "100",
      eaObtd: formatMarkVal(competency?.externalObtained ?? 86),
      eaMax: "100",
      totObtd: formatMarkVal(competency?.totalObtained ?? 171),
      totMax: "200",
      pct: formatDecimal(competency?.percentage ?? 85.5),
      grade: competency?.letterGrade || "O",
      gp: competency?.gradePoint ?? 10,
      pass: competency ? (competency.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "02.",
      codeLines: ["*Elective-3"],
      codeText: elective?.courseCode || "Elective-3",
      titleLines: ["Scientific Writing", "Skills"],
      titleText: "*Scientific Writing Skills (Elective)",
      credits: "1",
      iaObtd: formatMarkVal(elective?.internalObtained ?? 21),
      iaMax: "25",
      eaObtd: formatMarkVal(elective?.externalObtained ?? 22),
      eaMax: "25",
      totObtd: formatMarkVal(elective?.totalObtained ?? 43),
      totMax: "50",
      pct: formatDecimal(elective?.percentage ?? 86.0),
      grade: elective?.letterGrade || "P",
      gp: elective?.gradePoint ?? 0,
      pass: elective ? (elective.isPass ? "PASS" : "Fail") : "PASS",
    },
  ];

  // Default Cumulative History for B.Sc. Nursing Semesters 1 to 8 if not externally injected
  const defaultHistory: CumulativeSemesterRecord[] = [
    { semesterNumber: 1, semesterName: "Semester I", prescribedCredits: 14, sgpaCredits: 12, maxMarks: 250, obtainedMarks: 185, sgpa: 7.00, resultStatus: "PASS" },
    { semesterNumber: 2, semesterName: "Semester II", prescribedCredits: 31, sgpaCredits: 31, maxMarks: 350, obtainedMarks: 247, sgpa: 7.55, resultStatus: "PASS" },
    { semesterNumber: 3, semesterName: "Semester III", prescribedCredits: 17, sgpaCredits: 17, maxMarks: 300, obtainedMarks: 228, sgpa: 7.65, resultStatus: "PASS" },
    { semesterNumber: 4, semesterName: "Semester IV", prescribedCredits: 21, sgpaCredits: 20, maxMarks: 350, obtainedMarks: 262, sgpa: 7.70, resultStatus: "PASS" },
    { semesterNumber: 5, semesterName: "Semester V", prescribedCredits: 11, sgpaCredits: 11, maxMarks: 350, obtainedMarks: 260, sgpa: 7.82, resultStatus: "PASS" },
    { semesterNumber: 6, semesterName: "Semester VI", prescribedCredits: 22, sgpaCredits: 21, maxMarks: 500, obtainedMarks: 375, sgpa: 7.52, resultStatus: "PASS" },
    { semesterNumber: 7, semesterName: "Semester VII", prescribedCredits: 26, sgpaCredits: 26, maxMarks: 500, obtainedMarks: 380, sgpa: 7.77, resultStatus: "PASS" },
    {
      semesterNumber: 8,
      semesterName: "Semester VIII",
      prescribedCredits: 13,
      sgpaCredits: 12,
      maxMarks: 250,
      obtainedMarks: info.totalObtained || 214,
      sgpa: info.sgpa || 8.00,
      resultStatus: "PASS",
    },
  ];

  const history = cumulativeHistory && cumulativeHistory.length > 0 ? cumulativeHistory : defaultHistory;

  const totalPrescribed = history.reduce((sum, h) => sum + h.prescribedCredits, 0);
  const totalSgpaCredits = history.reduce((sum, h) => sum + h.sgpaCredits, 0);
  const totalObtainedMarks = history.reduce((sum, h) => sum + (h.obtainedMarks || 0), 0);
  const totalProgramMaxMarks = history.reduce((sum, h) => sum + h.maxMarks, 0);

  const weightedSgpaProduct = history.reduce(
    (sum, h) => sum + (h.sgpa || 0) * h.sgpaCredits,
    0
  );
  const calculatedCgpa = finalCgpa || (totalSgpaCredits > 0 ? weightedSgpaProduct / totalSgpaCredits : 7.65);
  const cumulativePct = totalProgramMaxMarks > 0 ? (totalObtainedMarks / totalProgramMaxMarks) * 100 : 76.5;

  const degreeClassification =
    finalClassification ||
    (calculatedCgpa >= 8.0
      ? "Distinction"
      : calculatedCgpa >= 6.5
      ? "First Division"
      : calculatedCgpa >= 5.5
      ? "Second Division"
      : "Pass Division");

  return (
    <div
      className={`marksheet-page ${layoutConfig?.pageFitLayout !== false ? "page-fit-active" : ""} ${isDirectEditing ? "direct-editing-active" : ""} ${className}`}
      data-direct-editing={isDirectEditing ? "true" : "false"}
      style={layoutStyle}
    >
      <style>{MarksheetStyles}</style>

      {/* Main Printable Content Container */}
      <div className="marksheet-content-body">
        {/* Top Header & Demographics */}
        <div className="marksheet-header-demographics">
          <div
            className="header-title-text text-center font-bold text-[10.5pt] uppercase tracking-wide whitespace-nowrap mb-2.5 text-black"
            contentEditable={isDirectEditing}
            suppressContentEditableWarning={true}
          >
            B.Sc. NURSING FOURTH YEAR (EIGHTH SEMESTER) UNIVERSITY EXAMINATION {info.attemptIndicator ? `${info.attemptIndicator} ` : ""}{sessionMonthYear.toUpperCase()}
          </div>
          <DemographicsBlock info={info} collegeName={collegeName} isDirectEditing={isDirectEditing} />
        </div>

        {/* Section 1: Semester VIII Marks Table */}
        <div
          className="text-[9.5pt] font-bold mb-0.5 uppercase tracking-wider text-black"
          contentEditable={isDirectEditing}
          suppressContentEditableWarning={true}
        >
          Semester VIII Examination Marks
        </div>
        <div className="marksheet-table-wrapper" style={{ flex: "0 0 auto", minHeight: "auto" }}>
          <table
            className="marksheet-main-table w-full border-collapse border border-black text-center text-[9.5pt] leading-tight mb-1"
            contentEditable={isDirectEditing}
            suppressContentEditableWarning={true}
          >
            <thead>
              <tr>
                <th rowSpan={2} className="col-sno border border-black p-1 text-[9pt] font-bold w-[5%] bg-white text-black">
                  Sl.No.
                </th>
                <th rowSpan={2} className="col-code border border-black p-1 text-[9pt] font-bold w-[15%] bg-white text-black">
                  Course Code
                </th>
                <th rowSpan={2} className="col-title border border-black p-1 text-[9pt] font-bold w-[22%] bg-white text-black">
                  Title of Course
                </th>
                <th rowSpan={2} className="col-credits border border-black p-1 text-[9pt] font-bold w-[7%] bg-white text-black">
                  Credits
                </th>
                <th colSpan={2} className="col-marks border border-black p-1 text-[9pt] font-bold w-[10%] bg-white text-black">
                  Internal Assessment
                </th>
                <th colSpan={2} className="col-marks border border-black p-1 text-[9pt] font-bold w-[10%] bg-white text-black">
                  University Exam
                </th>
                <th colSpan={2} className="col-marks border border-black p-1 text-[9pt] font-bold w-[10%] bg-white text-black">
                  Total Marks
                </th>
                <th rowSpan={2} className="col-grade border border-black p-1 text-[9pt] font-bold w-[5%] bg-white text-black">
                  Grade
                </th>
                <th rowSpan={2} className="border border-black p-1 text-[9pt] font-bold w-[4%] bg-white text-black">
                  GP
                </th>
                <th rowSpan={2} className="border border-black p-1 text-[9pt] font-bold w-[4%] bg-white text-black">
                  Result
                </th>
              </tr>
              <tr>
                <th className="border border-black p-0.5 text-[8.5pt] font-bold w-[5%] bg-white text-black">Obtd</th>
                <th className="border border-black p-0.5 text-[8.5pt] font-bold w-[5%] bg-white text-black">Max</th>
                <th className="border border-black p-0.5 text-[8.5pt] font-bold w-[5%] bg-white text-black">Obtd</th>
                <th className="border border-black p-0.5 text-[8.5pt] font-bold w-[5%] bg-white text-black">Max</th>
                <th className="border border-black p-0.5 text-[8.5pt] font-bold w-[5%] bg-white text-black">Obtd</th>
                <th className="border border-black p-0.5 text-[8.5pt] font-bold w-[5%] bg-white text-black">Max</th>
              </tr>
            </thead>
            <tbody>
              {displayCourses.map((row, idx) => (
                <tr key={idx} className="marksheet-course-row">
                  <td className="col-sno border border-black p-0.5 text-center font-normal">{row.slNo}</td>
                  <td className="col-code border border-black p-0.5 text-center font-bold">
                    <VerticalOrHorizontalText
                      lines={row.codeLines}
                      horizontalText={row.codeText}
                      isVertical={isCodeVertical}
                      isNowrap={isNowrap}
                    />
                  </td>
                  <td className="col-title border border-black p-0.5 text-center font-bold px-1">
                    <VerticalOrHorizontalText
                      lines={row.titleLines}
                      horizontalText={row.titleText}
                      isVertical={isTitleVertical}
                      isNowrap={isNowrap}
                    />
                  </td>
                  <td className="col-credits border border-black p-0.5 text-center font-normal">{row.credits}</td>
                  <td className="border border-black p-0.5 text-center">{row.iaObtd}</td>
                  <td className="border border-black p-0.5 text-center">{row.iaMax}</td>
                  <td className="border border-black p-0.5 text-center">{row.eaObtd}</td>
                  <td className="border border-black p-0.5 text-center">{row.eaMax}</td>
                  <td className="border border-black p-0.5 text-center">{row.totObtd}</td>
                  <td className="border border-black p-0.5 text-center">{row.totMax}</td>
                  <td className="col-grade border border-black p-0.5 text-center font-bold">{row.grade}</td>
                  <td className="border border-black p-0.5 text-center">{row.gp}</td>
                  <td className="border border-black p-0.5 text-center font-bold">{row.pass}</td>
                </tr>
              ))}
              <tr className="marksheet-total-row font-bold border-t border-black">
                <td colSpan={3} className="border border-black p-0.5 text-center font-bold">
                  Sem VIII Total Credit: 13 (SGPA: 12)
                </td>
                <td className="col-credits border border-black p-0.5 text-center font-bold">13</td>
                <td colSpan={4} className="border border-black p-0.5 text-center font-bold">
                  Sem VIII Total Marks
                </td>
                <td className="border border-black p-0.5 text-center font-bold">
                  {formatMarkVal(info.totalObtained || 214)}
                </td>
                <td className="border border-black p-0.5 text-center font-bold">250</td>
                <td colSpan={3} className="border border-black p-0.5 text-center font-bold">
                  SGPA: {formatDecimal(info.sgpa || 8.00)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Section 2: Multi-Year Cumulative Transcript Grid (Semesters I to VIII) */}
        <div
          className="mt-2 mb-0.5 flex justify-between items-baseline"
          contentEditable={isDirectEditing}
          suppressContentEditableWarning={true}
        >
          <div className="text-[9.5pt] font-bold uppercase tracking-wider text-black">
            Consolidated Grade Transcript (Semesters I Through VIII)
          </div>
          <div className="text-[8pt] font-normal text-slate-700">
            Degree: B.Sc. Nursing (Four Year Program)
          </div>
        </div>

        <table
          className="w-full border-collapse border border-black text-center text-[8.5pt] leading-tight mb-1.5"
          contentEditable={isDirectEditing}
          suppressContentEditableWarning={true}
        >
          <thead>
            <tr className="bg-slate-50">
              <th className="border border-black p-0.5 font-bold text-black w-[16%]">Semester</th>
              <th className="border border-black p-0.5 font-bold text-black w-[13%]">Prescribed Credits</th>
              <th className="border border-black p-0.5 font-bold text-black w-[13%]">SGPA Credits</th>
              <th className="border border-black p-0.5 font-bold text-black w-[14%]">Marks Obtd</th>
              <th className="border border-black p-0.5 font-bold text-black w-[14%]">Max Marks</th>
              <th className="border border-black p-0.5 font-bold text-black w-[12%]">Percentage</th>
              <th className="border border-black p-0.5 font-bold text-black w-[9%]">SGPA</th>
              <th className="border border-black p-0.5 font-bold text-black w-[9%]">Status</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h) => {
              const semPct = h.maxMarks > 0 ? ((h.obtainedMarks || 0) / h.maxMarks) * 100 : 0;
              return (
                <tr key={h.semesterNumber}>
                  <td className="border border-black p-0.5 font-bold text-center">{h.semesterName}</td>
                  <td className="border border-black p-0.5 text-center">{h.prescribedCredits}</td>
                  <td className="border border-black p-0.5 text-center">{h.sgpaCredits}</td>
                  <td className="border border-black p-0.5 text-center">{h.obtainedMarks ?? "-"}</td>
                  <td className="border border-black p-0.5 text-center">{h.maxMarks}</td>
                  <td className="border border-black p-0.5 text-center">{formatDecimal(semPct)}%</td>
                  <td className="border border-black p-0.5 font-bold text-center">{formatDecimal(h.sgpa)}</td>
                  <td className="border border-black p-0.5 font-bold text-center">{h.resultStatus || "PASS"}</td>
                </tr>
              );
            })}

            {/* Program Cumulative Summary Row */}
            <tr className="font-bold bg-slate-100 border-t-2 border-black">
              <td className="border border-black p-0.5 font-bold text-center">Grand Cumulative</td>
              <td className="border border-black p-0.5 font-bold text-center">{totalPrescribed}</td>
              <td className="border border-black p-0.5 font-bold text-center">{totalSgpaCredits}</td>
              <td className="border border-black p-0.5 font-bold text-center">{totalObtainedMarks}</td>
              <td className="border border-black p-0.5 font-bold text-center">{totalProgramMaxMarks}</td>
              <td className="border border-black p-0.5 font-bold text-center">{formatDecimal(cumulativePct)}%</td>
              <td className="border border-black p-0.5 font-bold text-center text-blue-950">
                {formatDecimal(calculatedCgpa)}
              </td>
              <td className="border border-black p-0.5 font-bold text-center text-emerald-950">PASSED</td>
            </tr>
          </tbody>
        </table>

        {/* Section 3: Final Degree Evaluation Summary Box */}
        <table
          className="w-[78%] mx-auto my-1.5 border-collapse border border-black text-center"
          contentEditable={isDirectEditing}
          suppressContentEditableWarning={true}
        >
          <tbody>
            <tr>
              <td className="border border-black font-bold text-[9pt] py-0.5 px-2 bg-white text-black">
                Semester VIII SGPA
              </td>
              <td className="border border-black font-bold text-[9pt] py-0.5 px-2 bg-white text-black">
                Cumulative Grade Point Average (CGPA)
              </td>
              <td className="border border-black font-bold text-[9pt] py-0.5 px-2 bg-white text-black">
                Final Degree Classification
              </td>
            </tr>
            <tr>
              <td className="border border-black font-bold text-[10.5pt] py-0.5 px-2 bg-white text-black">
                {formatDecimal(info.sgpa || 8.00)}
              </td>
              <td className="border border-black font-bold text-[10.5pt] py-0.5 px-2 bg-white text-black text-blue-900">
                {formatDecimal(calculatedCgpa)}
              </td>
              <td className="border border-black font-bold text-[10pt] py-0.5 px-2 bg-white text-black uppercase text-emerald-800">
                {degreeClassification}
              </td>
            </tr>
          </tbody>
        </table>

        {/* Distinct 2-row, 2-column Bordered Results & Remarks Table */}
        <table
          className="result-remarks-table w-full border-collapse my-1.5 text-[10pt] leading-normal"
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
                className="col-label font-bold text-center py-1 px-3 bg-white text-black"
                style={{
                  width: "18%",
                  borderRight: "1.5px solid #000000",
                }}
              >
                Result
              </td>
              <td className="col-value font-bold text-center py-1 px-3 bg-white text-black text-emerald-900">
                PASS - QUALIFIED FOR THE AWARD OF B.Sc. NURSING DEGREE
              </td>
            </tr>
            <tr>
              <td
                className="col-label font-bold text-center py-1 px-3 bg-white text-black"
                style={{
                  width: "18%",
                  borderRight: "1.5px solid #000000",
                }}
              >
                Remarks
              </td>
              <td className="col-value font-bold text-center py-1 px-3 bg-white text-black">
                Grading Performance - {degreeClassification} (Cumulative: {formatDecimal(cumulativePct)}%)
              </td>
            </tr>
          </tbody>
        </table>

        {/* Statutory Note */}
      </div>

      {/* Institutional Signatures Footer with Controller of Examinations */}
      <SignaturesFooter
        noteText="Note: This Consolidated Marksheet & Grade Transcript is an authentic record of the candidate's academic performance across all eight semesters of the four-year B.Sc. Nursing Degree Program at SGPGIMS, Lucknow."
        sig1="Prepared By"
        sig2="Checked By"
        sig3="Sub-Dean (Nursing)"
        sig4="Controller of Examinations"
        issueDate={issueDate}
        isDirectEditing={isDirectEditing}
      />
    </div>
  );
};

export default Sem8Marksheet;
