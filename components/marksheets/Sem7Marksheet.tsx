"use client";

import React from "react";
import {
  MarksheetBaseProps,
  normalizeStudentData,
  formatMarkVal,
  formatDecimal,
  DemographicsBlock,
  SgpaSummaryBox,
  ResultRemarksBlock,
  SignaturesFooter,
  getLayoutCssVariables,
  MarksheetStyles,
  VerticalOrHorizontalText,
} from "./shared";

export const Sem7Marksheet: React.FC<MarksheetBaseProps> = ({
  student,
  sessionMonthYear = "JANUARY - 2026",
  issueDate,
  collegeName,
  layoutConfig,
  isDirectEditing = false,
  className = "",
}) => {
  const info = normalizeStudentData(student);
  const layoutStyle = getLayoutCssVariables(layoutConfig);

  const isCodeVertical = layoutConfig?.textDirectionCode !== "horizontal";
  const isTitleVertical = layoutConfig?.textDirectionTitle !== "horizontal";
  const isNowrap = layoutConfig?.textWrapping === "nowrap";

  // Match or find Semester 7 courses
  const comh2Theory = info.courses.find(
    (c) =>
      (c.courseCode.includes("COMH") || c.courseTitle.toLowerCase().includes("community")) &&
      !c.courseTitle.toLowerCase().includes("practical") &&
      c.internalMax <= 25
  );
  const comh2Pract = info.courses.find(
    (c) =>
      (c.courseCode.includes("COMH") || c.courseTitle.toLowerCase().includes("community")) &&
      (c.courseTitle.toLowerCase().includes("practical") || c.internalMax >= 50)
  );
  const nrst = info.courses.find(
    (c) =>
      c.courseCode.includes("NRST") ||
      c.courseCode.includes("NRES") ||
      c.courseTitle.toLowerCase().includes("research") ||
      c.courseTitle.toLowerCase().includes("statistics")
  );
  const obgTheory = info.courses.find(
    (c) =>
      (c.courseCode.includes("OBG") ||
        c.courseCode.includes("MIDW") ||
        c.courseTitle.toLowerCase().includes("midwifery") ||
        c.courseTitle.toLowerCase().includes("obstetrics")) &&
      !c.courseTitle.toLowerCase().includes("practical") &&
      c.internalMax <= 25
  );
  const obgPract = info.courses.find(
    (c) =>
      (c.courseCode.includes("OBG") ||
        c.courseCode.includes("MIDW") ||
        c.courseTitle.toLowerCase().includes("midwifery") ||
        c.courseTitle.toLowerCase().includes("obstetrics")) &&
      (c.courseTitle.toLowerCase().includes("practical") || c.internalMax >= 50)
  );

  const displayCourses = [
    {
      slNo: "01.",
      codeLines: ["N-COMH (II) 401"],
      codeText: comh2Theory?.courseCode || "N-CHN (II) 401",
      titleLines: ["Community Health", "Nursing II (Theory)"],
      titleText: "Community Health Nursing II (Theory)",
      credits: "5",
      iaObtd: formatMarkVal(comh2Theory?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(comh2Theory?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(comh2Theory?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(comh2Theory?.percentage ?? 0),
      grade: comh2Theory?.letterGrade || "C",
      gp: comh2Theory?.gradePoint ?? 0,
      pass: comh2Theory ? (comh2Theory.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "02.",
      codeLines: ["N-COMH (II) 401"],
      codeText: comh2Pract?.courseCode || "N-CHN (II) 401",
      titleLines: ["Community Health", "Nursing II (Practical)"],
      titleText: "Community Health Nursing II (Practical)",
      credits: "2",
      iaObtd: formatMarkVal(comh2Pract?.internalObtained ?? 0),
      iaMax: "50",
      eaObtd: formatMarkVal(comh2Pract?.externalObtained ?? 0),
      eaMax: "50",
      totObtd: formatMarkVal(comh2Pract?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(comh2Pract?.percentage ?? 0),
      grade: comh2Pract?.letterGrade || "C",
      gp: comh2Pract?.gradePoint ?? 0,
      pass: comh2Pract ? (comh2Pract.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "03.",
      codeLines: ["NRST (405)"],
      codeText: nrst?.courseCode || "N-NRES 405",
      titleLines: ["Nursing Research", "& Statistics"],
      titleText: "Nursing Research & Statistics",
      credits: "4",
      iaObtd: formatMarkVal(nrst?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(nrst?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(nrst?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(nrst?.percentage ?? 0),
      grade: nrst?.letterGrade || "C",
      gp: nrst?.gradePoint ?? 0,
      pass: nrst ? (nrst.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "04.",
      codeLines: ["N-MIDW/OBGN", "I & II", "335 & 410"],
      codeText: obgTheory?.courseCode || "MIDW 410",
      titleLines: ["Midwifery/Obstetrics", "and Gynaecology (OBG)", "Nursing I & II (Theory)"],
      titleText: "Midwifery/Obstetrics & Gynaecology (OBG) Nursing I & II (Theory)",
      credits: "6",
      iaObtd: formatMarkVal(obgTheory?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(obgTheory?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(obgTheory?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(obgTheory?.percentage ?? 0),
      grade: obgTheory?.letterGrade || "C",
      gp: obgTheory?.gradePoint ?? 0,
      pass: obgTheory ? (obgTheory.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "05.",
      codeLines: ["N-MIDW/OBGN", "I & II", "335 & 410"],
      codeText: obgPract?.courseCode || "MIDW 410",
      titleLines: ["Midwifery/Obstetrics", "and Gynaecology (OBG)", "Nursing I & II (Practical)"],
      titleText: "Midwifery/Obstetrics & Gynaecology (OBG) Nursing I & II (Practical)",
      credits: "9",
      iaObtd: formatMarkVal(obgPract?.internalObtained ?? 0),
      iaMax: "50",
      eaObtd: formatMarkVal(obgPract?.externalObtained ?? 0),
      eaMax: "50",
      totObtd: formatMarkVal(obgPract?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(obgPract?.percentage ?? 0),
      grade: obgPract?.letterGrade || "C",
      gp: obgPract?.gradePoint ?? 0,
      pass: obgPract ? (obgPract.isPass ? "PASS" : "Fail") : "PASS",
    },
  ];

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
            className="header-title-text text-center font-bold text-[11pt] uppercase tracking-wide whitespace-nowrap mb-2.5 text-black"
            contentEditable={isDirectEditing}
            suppressContentEditableWarning={true}
          >
            B.Sc. NURSING FOURTH YEAR (SEVENTH SEMESTER) UNIVERSITY EXAMINATION {info.attemptIndicator ? `${info.attemptIndicator} ` : ""}{sessionMonthYear.toUpperCase()}
          </div>
          <DemographicsBlock info={info} collegeName={collegeName} isDirectEditing={isDirectEditing} />
        </div>

        {/* 11-Column Marks Table with Page-Fit Proportional Row Height */}
        <div className="marksheet-table-wrapper">
          <table
            className="marksheet-main-table w-full border-collapse border border-black text-center text-[10pt] leading-tight"
            contentEditable={isDirectEditing}
            suppressContentEditableWarning={true}
          >
            <thead>
              <tr>
                <th rowSpan={2} className="col-sno border border-black p-1 text-[9.5pt] font-bold w-[5%] bg-white text-black">
                  Sl.No.
                </th>
                <th rowSpan={2} className="col-code border border-black p-1 text-[9.5pt] font-bold w-[14%] bg-white text-black">
                  Course Code
                </th>
                <th rowSpan={2} className="col-title border border-black p-1 text-[9.5pt] font-bold w-[26%] bg-white text-black">
                  Title of Course
                </th>
                <th rowSpan={2} className="col-credits border border-black p-1 text-[9.5pt] font-bold w-[7%] bg-white text-black">
                  Course Credits
                </th>
                <th colSpan={2} className="col-marks border border-black p-1 text-[9.5pt] font-bold w-[10%] bg-white text-black">
                  Internal Assesment Marks
                </th>
                <th colSpan={2} className="col-marks border border-black p-1 text-[9.5pt] font-bold w-[11%] bg-white text-black">
                  End Semester University Exam Marks
                </th>
                <th colSpan={2} className="col-marks border border-black p-1 text-[9.5pt] font-bold w-[11%] bg-white text-black">
                  Total Marks
                </th>
                <th rowSpan={2} className="border border-black p-1 text-[9.5pt] font-bold w-[6%] bg-white text-black">
                  Final Marks (%)
                </th>
                <th rowSpan={2} className="col-grade border border-black p-1 text-[9.5pt] font-bold w-[5%] bg-white text-black">
                  Letter Grade
                </th>
                <th rowSpan={2} className="border border-black p-1 text-[9.5pt] font-bold w-[5%] bg-white text-black">
                  Grade Point
                </th>
                <th rowSpan={2} className="border border-black p-1 text-[9.5pt] font-bold w-[5%] bg-white text-black">
                  Result
                </th>
              </tr>
              <tr>
                <th className="border border-black p-0.5 text-[9pt] font-bold w-[5%] bg-white text-black">Obtd</th>
                <th className="border border-black p-0.5 text-[9pt] font-bold w-[5%] bg-white text-black">Max</th>
                <th className="border border-black p-0.5 text-[9pt] font-bold w-[5.5%] bg-white text-black">Obtd</th>
                <th className="border border-black p-0.5 text-[9pt] font-bold w-[5.5%] bg-white text-black">Max</th>
                <th className="border border-black p-0.5 text-[9pt] font-bold w-[5.5%] bg-white text-black">Obtd</th>
                <th className="border border-black p-0.5 text-[9pt] font-bold w-[5.5%] bg-white text-black">Max</th>
              </tr>
            </thead>
            <tbody>
              {displayCourses.map((row, idx) => (
                <tr key={idx} className="marksheet-course-row">
                  <td className="col-sno border border-black p-1 text-center font-normal">{row.slNo}</td>
                  <td className="col-code border border-black p-1 text-center font-bold">
                    <VerticalOrHorizontalText
                      lines={row.codeLines}
                      horizontalText={row.codeText}
                      isVertical={isCodeVertical}
                      isNowrap={isNowrap}
                    />
                  </td>
                  <td className="col-title border border-black p-1 text-center font-bold px-1.5">
                    <VerticalOrHorizontalText
                      lines={row.titleLines}
                      horizontalText={row.titleText}
                      isVertical={isTitleVertical}
                      isNowrap={isNowrap}
                    />
                  </td>
                  <td className="col-credits border border-black p-1 text-center font-normal leading-tight">{row.credits}</td>
                  <td className="border border-black p-1 text-center">{row.iaObtd}</td>
                  <td className="border border-black p-1 text-center">{row.iaMax}</td>
                  <td className="border border-black p-1 text-center">{row.eaObtd}</td>
                  <td className="border border-black p-1 text-center">{row.eaMax}</td>
                  <td className="border border-black p-1 text-center">{row.totObtd}</td>
                  <td className="border border-black p-1 text-center">{row.totMax}</td>
                  <td className="border border-black p-1 text-center">{row.pct}</td>
                  <td className="col-grade border border-black p-1 text-center font-bold">{row.grade}</td>
                  <td className="border border-black p-1 text-center">{row.gp}</td>
                  <td className="border border-black p-1 text-center font-bold">{row.pass}</td>
                </tr>
              ))}

              {/* Total Row */}
              <tr className="marksheet-total-row font-bold border-t border-black">
                <td colSpan={3} className="border border-black p-1 text-center font-bold">
                  Total Credit
                </td>
                <td className="col-credits border border-black p-1 text-center font-bold">26</td>
                <td colSpan={4} className="border border-black p-1 text-center font-bold">
                  Grand Total
                </td>
                <td className="border border-black p-1 text-center font-bold">
                  {formatMarkVal(info.totalObtained)}
                </td>
                <td className="border border-black p-1 text-center font-bold">500</td>
                <td className="border border-black p-1 text-center font-bold">
                  {formatDecimal(info.percentage)}
                </td>
                <td className="border border-black p-1 text-center font-bold">-</td>
                <td className="border border-black p-1 text-center font-bold">-</td>
                <td className="border border-black p-1 text-center font-bold">-</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Under-Table Explanatory Note & Abbreviations */}
        <div
          className="flex justify-end items-baseline text-[9pt] mt-1 mb-1.5 text-black"
          contentEditable={isDirectEditing}
          suppressContentEditableWarning={true}
        >
          <div className="text-right whitespace-nowrap">
            Obtd. : Obtained &nbsp;&nbsp;&nbsp;&nbsp; Max. : Maximum
          </div>
        </div>

        {/* SGPA / Credit Score Box */}
        <SgpaSummaryBox sgpa={info.sgpa} creditScore={info.creditScore} isDirectEditing={isDirectEditing} />

        {/* Result & Remarks Block */}
        <ResultRemarksBlock
          resultStatus={info.resultStatus}
          remarks={info.remarks}
          sgpa={info.sgpa}
          isDirectEditing={isDirectEditing}
        />

        {/* Statutory Note */}
      </div>

      {/* Institutional Signatures Footer */}
      <SignaturesFooter issueDate={issueDate} isDirectEditing={isDirectEditing} />
    </div>
  );
};

export default Sem7Marksheet;
