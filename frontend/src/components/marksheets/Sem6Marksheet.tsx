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

export const Sem6Marksheet: React.FC<MarksheetBaseProps> = ({
  student,
  sessionMonthYear = "JULY - 2026",
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

  // Match or find Semester 6 courses
  const chnTheory = info.courses.find(
    (c) =>
      (c.courseCode.includes("CHN") || c.courseTitle.toLowerCase().includes("child")) &&
      !c.courseTitle.toLowerCase().includes("practical") &&
      c.internalMax <= 25
  );
  const chnPract = info.courses.find(
    (c) =>
      (c.courseCode.includes("CHN") || c.courseTitle.toLowerCase().includes("child")) &&
      (c.courseTitle.toLowerCase().includes("practical") || c.internalMax >= 50)
  );
  const mhnTheory = info.courses.find(
    (c) =>
      (c.courseCode.includes("MHN") || c.courseTitle.toLowerCase().includes("mental")) &&
      !c.courseTitle.toLowerCase().includes("practical") &&
      c.internalMax <= 25
  );
  const mhnPract = info.courses.find(
    (c) =>
      (c.courseCode.includes("MHN") || c.courseTitle.toLowerCase().includes("mental")) &&
      (c.courseTitle.toLowerCase().includes("practical") || c.internalMax >= 50)
  );
  const nmle = info.courses.find(
    (c) =>
      c.courseCode.includes("NMLE") ||
      c.courseCode.includes("LEAD") ||
      c.courseTitle.toLowerCase().includes("leadership") ||
      c.courseTitle.toLowerCase().includes("management")
  );
  const elective = info.courses.find(
    (c) =>
      c.courseCode.toLowerCase().includes("elective") ||
      c.courseTitle.toLowerCase().includes("accreditation")
  );

  const baseCourses = [
    {
      slNo: "01.",
      codeLines: ["N-CHN (I&II) 301"],
      codeText: chnTheory?.courseCode || "N-CHN (I & II) 301",
      titleLines: ["Child Health", "Nursing (I & II) (Theory)"],
      titleText: "Child Health Nursing I & II (Theory)",
      credits: "4",
      iaObtd: formatMarkVal(chnTheory?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(chnTheory?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(chnTheory?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(chnTheory?.percentage ?? 0),
      grade: chnTheory?.letterGrade || "C",
      gp: chnTheory?.gradePoint ?? 0,
      pass: chnTheory ? (chnTheory.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "02.",
      codeLines: ["N-CHN (I&II) 301"],
      codeText: chnPract?.courseCode || "N-CHN (I & II) 301",
      titleLines: ["Child Health", "Nursing (I & II) (Practical)"],
      titleText: "Child Health Nursing I & II (Practical)",
      credits: "3",
      iaObtd: formatMarkVal(chnPract?.internalObtained ?? 0),
      iaMax: "50",
      eaObtd: formatMarkVal(chnPract?.externalObtained ?? 0),
      eaMax: "50",
      totObtd: formatMarkVal(chnPract?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(chnPract?.percentage ?? 0),
      grade: chnPract?.letterGrade || "C",
      gp: chnPract?.gradePoint ?? 0,
      pass: chnPract ? (chnPract.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "03.",
      codeLines: ["N-MHN (I & II)", "305"],
      codeText: mhnTheory?.courseCode || "N-MHN (I & II) 305",
      titleLines: ["Mental Health", "Nursing (I & II) (Theory)"],
      titleText: "Mental Health Nursing I & II (Theory)",
      credits: "4",
      iaObtd: formatMarkVal(mhnTheory?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(mhnTheory?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(mhnTheory?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(mhnTheory?.percentage ?? 0),
      grade: mhnTheory?.letterGrade || "C",
      gp: mhnTheory?.gradePoint ?? 0,
      pass: mhnTheory ? (mhnTheory.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "04.",
      codeLines: ["N-MHN (I & II)", "305"],
      codeText: mhnPract?.courseCode || "N-MHN (I & II) 305",
      titleLines: ["Mental Health", "Nursing (I & II) (Practical)"],
      titleText: "Mental Health Nursing I & II (Practical)",
      credits: "3",
      iaObtd: formatMarkVal(mhnPract?.internalObtained ?? 0),
      iaMax: "50",
      eaObtd: formatMarkVal(mhnPract?.externalObtained ?? 0),
      eaMax: "50",
      totObtd: formatMarkVal(mhnPract?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(mhnPract?.percentage ?? 0),
      grade: mhnPract?.letterGrade || "C",
      gp: mhnPract?.gradePoint ?? 0,
      pass: mhnPract ? (mhnPract.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "05.",
      codeLines: ["NMLE 330"],
      codeText: nmle?.courseCode || "NMLE 330",
      titleLines: ["Nursing Management", "& Leadership"],
      titleText: "Nursing Management & Leadership",
      credits: "7",
      iaObtd: formatMarkVal(nmle?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(nmle?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(nmle?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(nmle?.percentage ?? 0),
      grade: nmle?.letterGrade || "C",
      gp: nmle?.gradePoint ?? 0,
      pass: nmle ? (nmle.isPass ? "PASS" : "Fail") : "PASS",
    },
  ];

  const displayCourses = elective
    ? [
        ...baseCourses,
        {
          slNo: "06.",
          codeLines: ["*Elective-2"],
          codeText: elective.courseCode || "Elective-2",
          titleLines: ["Accreditation And", "Practice Standards"],
          titleText: "*Accreditation and Practice Standards (Elective)",
          credits: "1",
          iaObtd: formatMarkVal(elective.internalObtained ?? 0),
          iaMax: "25",
          eaObtd: formatMarkVal(elective.externalObtained ?? 0),
          eaMax: "25",
          totObtd: formatMarkVal(elective.totalObtained ?? 0),
          totMax: "50",
          pct: formatDecimal(elective.percentage ?? 0),
          grade: elective.letterGrade || "P",
          gp: elective.gradePoint ?? 0,
          pass: elective.isPass ? "PASS" : "Fail",
        },
      ]
    : baseCourses;

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
            B.Sc. NURSING THIRD YEAR (SIXTH SEMESTER) UNIVERSITY EXAMINATION {info.attemptIndicator ? `${info.attemptIndicator} ` : ""}{sessionMonthYear.toUpperCase()}
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
                <th rowSpan={2} className="col-title border border-black p-1 text-[9.5pt] font-bold w-[18%] bg-white text-black">
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
                <td className="col-credits border border-black p-1 text-center font-bold">22</td>
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
          className="flex justify-between items-baseline text-[9pt] mt-1 mb-1.5 text-black"
          contentEditable={isDirectEditing}
          suppressContentEditableWarning={true}
        >
          <div className="text-left">
            * Elective Module, Marks are not added for calculating SGPA, Pass marks-40% as per INC
          </div>
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

export default Sem6Marksheet;
