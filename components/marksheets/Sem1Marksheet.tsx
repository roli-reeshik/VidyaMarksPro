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

export const Sem1Marksheet: React.FC<MarksheetBaseProps> = ({
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

  // Match or find Semester 1 courses
  const engl = info.courses.find(
    (c) =>
      c.courseCode.includes("ENGL") ||
      c.courseTitle.toLowerCase().includes("english")
  );
  const anat = info.courses.find(
    (c) =>
      c.courseCode.includes("ANAT") ||
      c.courseTitle.toLowerCase().includes("anatomy")
  );
  const soci = info.courses.find(
    (c) =>
      c.courseCode.includes("SOCI") ||
      c.courseTitle.toLowerCase().includes("sociology")
  );

  const displayCourses = [
    {
      slNo: "01.",
      codeLines: ["ENGL 101"],
      codeText: engl?.courseCode || "ENGL 101",
      titleLines: ["*Communicative English"],
      titleText: "*Communicative English",
      credits: "2",
      iaObtd: formatMarkVal(engl?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(engl?.externalObtained ?? 0),
      eaMax: "25",
      totObtd: formatMarkVal(engl?.totalObtained ?? 0),
      totMax: "50",
      pct: formatDecimal(engl?.percentage ?? 0),
      grade: engl?.letterGrade || "C",
      gp: engl?.gradePoint ?? 0,
      pass: engl ? (engl.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "02.",
      codeLines: ["ANAT 105 &", "PHYS 110"],
      codeText: anat?.courseCode || "ANAT 105 & PHYS 110",
      titleLines: ["Applied Anatomy", "&", "Applied Physiology"],
      titleText: "Applied Anatomy & Applied Physiology",
      credits: (
        <>
          6<br />(3+3)
        </>
      ),
      iaObtd: formatMarkVal(anat?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(anat?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(anat?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(anat?.percentage ?? 0),
      grade: anat?.letterGrade || "C",
      gp: anat?.gradePoint ?? 0,
      pass: anat ? (anat.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "03.",
      codeLines: ["SOCI 115 &", "PSYC 120"],
      codeText: soci?.courseCode || "SOCI 115 & PSYC 120",
      titleLines: ["Applied Sociology", "&", "Applied Psychology"],
      titleText: "Applied Sociology & Applied Psychology",
      credits: (
        <>
          6<br />(3+3)
        </>
      ),
      iaObtd: formatMarkVal(soci?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(soci?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(soci?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(soci?.percentage ?? 0),
      grade: soci?.letterGrade || "C",
      gp: soci?.gradePoint ?? 0,
      pass: soci ? (soci.isPass ? "PASS" : "Fail") : "PASS",
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
            B.Sc. NURSING FIRST YEAR (FIRST SEMESTER) UNIVERSITY EXAMINATION {info.attemptIndicator ? `${info.attemptIndicator} ` : ""}{sessionMonthYear.toUpperCase()}
          </div>
          <DemographicsBlock info={info} collegeName={collegeName} isDirectEditing={isDirectEditing} />
        </div>

        {/* 11-Column Marks Table with Page-Fit Flex Row Distribution */}
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
                <td className="col-credits border border-black p-1 text-center font-bold">14</td>
                <td colSpan={4} className="border border-black p-1 text-center font-bold">
                  Grand Total
                </td>
                <td className="border border-black p-1 text-center font-bold">
                  {formatMarkVal(info.totalObtained)}
                </td>
                <td className="border border-black p-1 text-center font-bold">250</td>
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

        {/* Under-Table Explanatory Note, SGPA & Result/Remarks */}
        <div className="marksheet-lower-section">
          <div
            className="flex justify-between items-baseline text-[9pt] mt-1 mb-1.5 text-black"
            contentEditable={isDirectEditing}
            suppressContentEditableWarning={true}
          >
            <div className="text-left">
              * College Exam, Marks are not added for calculating SGPA, Pass marks-40% as per INC, New Delhi
            </div>
            <div className="text-right whitespace-nowrap">
              Obtd. : Obtained &nbsp;&nbsp;&nbsp;&nbsp; Max. : Maximum
            </div>
          </div>

          <SgpaSummaryBox sgpa={info.sgpa} creditScore={info.creditScore} isDirectEditing={isDirectEditing} />

          <ResultRemarksBlock
            resultStatus={info.resultStatus}
            remarks={info.remarks}
            sgpa={info.sgpa}
            isDirectEditing={isDirectEditing}
          />
        </div>
      </div>

      {/* Institutional Signatures Footer */}
      <SignaturesFooter issueDate={issueDate} isDirectEditing={isDirectEditing} />
    </div>
  );
};

export default Sem1Marksheet;
