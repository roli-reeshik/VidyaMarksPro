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

export const Sem4Marksheet: React.FC<MarksheetBaseProps> = ({
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

  // Match or find Semester 4 courses
  const pharPath = info.courses.find(
    (c) =>
      c.courseCode.includes("PHAR") ||
      c.courseCode.includes("PATH") ||
      c.courseTitle.toLowerCase().includes("pharmacology")
  );
  const ahn2Theory = info.courses.find(
    (c) =>
      (c.courseCode.includes("AHN") || c.courseTitle.toLowerCase().includes("adult health")) &&
      !c.courseTitle.toLowerCase().includes("practical") &&
      c.internalMax <= 25
  );
  const ahn2Pract = info.courses.find(
    (c) =>
      (c.courseCode.includes("AHN") || c.courseTitle.toLowerCase().includes("adult health")) &&
      (c.courseTitle.toLowerCase().includes("practical") || c.internalMax >= 50)
  );
  const prof = info.courses.find(
    (c) =>
      c.courseCode.includes("PROF") ||
      c.courseTitle.toLowerCase().includes("professionalism")
  );
  const elective = info.courses.find(
    (c) =>
      c.courseCode.toLowerCase().includes("elective") ||
      c.courseTitle.toLowerCase().includes("human values") ||
      c.courseTitle.toLowerCase().includes("soft skills")
  );

  const displayCourses = [
    {
      slNo: "01.",
      codeLines: ["PHAR (I & II)-205", "AND", "PATH (I & II)-210"],
      codeText: pharPath?.courseCode || "PHAR 205 & PATH 210",
      titleLines: ["Pharmacology (I & II)", "& Pathology (I & II)", "(including Genetics)"],
      titleText: "Pharmacology & Pathology (I & II) & Genetics",
      credits: (
        <>
          6<br />(4+2)
        </>
      ),
      iaObtd: formatMarkVal(pharPath?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(pharPath?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(pharPath?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(pharPath?.percentage ?? 0),
      grade: pharPath?.letterGrade || "C",
      gp: pharPath?.gradePoint ?? 0,
      pass: pharPath ? (pharPath.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "02.",
      codeLines: ["N-AHN(II)-225"],
      codeText: ahn2Theory?.courseCode || "N-AHN (II) 225",
      titleLines: ["Adult Health Nursing II", "(Theory)"],
      titleText: "Adult Health Nursing II (Theory)",
      credits: "7",
      iaObtd: formatMarkVal(ahn2Theory?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(ahn2Theory?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(ahn2Theory?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(ahn2Theory?.percentage ?? 0),
      grade: ahn2Theory?.letterGrade || "C",
      gp: ahn2Theory?.gradePoint ?? 0,
      pass: ahn2Theory ? (ahn2Theory.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "03.",
      codeLines: ["N-AHN(II)-225"],
      codeText: ahn2Pract?.courseCode || "N-AHN (II) 225",
      titleLines: ["Adult Health Nursing II", "(Practical)"],
      titleText: "Adult Health Nursing II (Practical)",
      credits: "7",
      iaObtd: formatMarkVal(ahn2Pract?.internalObtained ?? 0),
      iaMax: "50",
      eaObtd: formatMarkVal(ahn2Pract?.externalObtained ?? 0),
      eaMax: "50",
      totObtd: formatMarkVal(ahn2Pract?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(ahn2Pract?.percentage ?? 0),
      grade: ahn2Pract?.letterGrade || "C",
      gp: ahn2Pract?.gradePoint ?? 0,
      pass: ahn2Pract ? (ahn2Pract.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "04.",
      codeLines: ["*PROF-230"],
      codeText: prof?.courseCode || "PROF 230",
      titleLines: ["Professionalism,", "Professional Values & Ethics", "including Bioethics"],
      titleText: "*Professional Values & Ethics including Bioethics",
      credits: "1",
      iaObtd: formatMarkVal(prof?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(prof?.externalObtained ?? 0),
      eaMax: "25",
      totObtd: formatMarkVal(prof?.totalObtained ?? 0),
      totMax: "50",
      pct: formatDecimal(prof?.percentage ?? 0),
      grade: prof?.letterGrade || "P",
      gp: prof?.gradePoint ?? 0,
      pass: prof ? (prof.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "05.",
      codeLines: ["**Elective"],
      codeText: elective?.courseCode || "Elective-1",
      titleLines: ["Soft", "Skills"],
      titleText: "*Elective Module / Human Values",
      credits: "1",
      iaObtd: formatMarkVal(elective?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(elective?.externalObtained ?? 0),
      eaMax: "25",
      totObtd: formatMarkVal(elective?.totalObtained ?? 0),
      totMax: "50",
      pct: formatDecimal(elective?.percentage ?? 0),
      grade: elective?.letterGrade || "P",
      gp: elective?.gradePoint ?? 0,
      pass: elective ? (elective.isPass ? "PASS" : "Fail") : "PASS",
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
            B.Sc. NURSING SECOND YEAR (FOURTH SEMESTER) UNIVERSITY EXAMINATION {info.attemptIndicator ? `${info.attemptIndicator} ` : ""}{sessionMonthYear.toUpperCase()}
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
                <td className="col-credits border border-black p-1 text-center font-bold">21</td>
                <td colSpan={4} className="border border-black p-1 text-center font-bold">
                  Grand Total
                </td>
                <td className="border border-black p-1 text-center font-bold">
                  {formatMarkVal(info.totalObtained)}
                </td>
                <td className="border border-black p-1 text-center font-bold">350</td>
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
            * College Exam & Elective Module, Marks are not added for calculating SGPA, Pass marks-40% as per INC
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

export default Sem4Marksheet;
