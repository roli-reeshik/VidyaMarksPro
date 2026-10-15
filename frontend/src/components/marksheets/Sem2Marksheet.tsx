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

export const Sem2Marksheet: React.FC<MarksheetBaseProps> = ({
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

  // Match or find Semester 2 courses
  const bioc = info.courses.find(
    (c) =>
      c.courseCode.includes("BIOC") ||
      c.courseCode.includes("NUTR") ||
      c.courseTitle.toLowerCase().includes("biochemistry")
  );
  const nnfTheory = info.courses.find(
    (c) =>
      (c.courseCode.includes("N-NF") || c.courseTitle.toLowerCase().includes("foundation")) &&
      !c.courseTitle.toLowerCase().includes("practical") &&
      c.internalMax <= 25
  );
  const nnfPract = info.courses.find(
    (c) =>
      (c.courseCode.includes("N-NF") || c.courseTitle.toLowerCase().includes("foundation")) &&
      (c.courseTitle.toLowerCase().includes("practical") || c.internalMax >= 50)
  );
  const hnit = info.courses.find(
    (c) =>
      c.courseCode.includes("HNIT") ||
      c.courseTitle.toLowerCase().includes("informatics")
  );

  const displayCourses = [
    {
      slNo: "01.",
      codeLines: ["BIOC 135 &", "NUTR 140"],
      codeText: bioc?.courseCode || "BIOC 135 & NUTR 140",
      titleLines: ["Applied Biochemistry &", "Applied Nutrition &", "Dietetics"],
      titleText: "Applied Biochemistry & Applied Nutrition & Dietetics",
      credits: (
        <>
          5<br />(2+3)
        </>
      ),
      iaObtd: formatMarkVal(bioc?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(bioc?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(bioc?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(bioc?.percentage ?? 0),
      grade: bioc?.letterGrade || "C",
      gp: bioc?.gradePoint ?? 0,
      pass: bioc ? (bioc.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "02.",
      codeLines: ["N-NF (I & II)", "125"],
      codeText: nnfTheory?.courseCode || "N-NF (I & II) 125",
      titleLines: ["Nursing Foundation", "I & II (Theory)"],
      titleText: "Nursing Foundation I & II (Theory)",
      credits: (
        <>
          12<br />(6+6)
        </>
      ),
      iaObtd: formatMarkVal(nnfTheory?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(nnfTheory?.externalObtained ?? 0),
      eaMax: "75",
      totObtd: formatMarkVal(nnfTheory?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(nnfTheory?.percentage ?? 0),
      grade: nnfTheory?.letterGrade || "C",
      gp: nnfTheory?.gradePoint ?? 0,
      pass: nnfTheory ? (nnfTheory.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "03.",
      codeLines: ["N-NF (I & II)", "125"],
      codeText: nnfPract?.courseCode || "N-NF (I & II) 125",
      titleLines: ["Nursing Foundation", "I & II (Practical)"],
      titleText: "Nursing Foundation I & II (Practical)",
      credits: (
        <>
          11<br />(4+7)
        </>
      ),
      iaObtd: formatMarkVal(nnfPract?.internalObtained ?? 0),
      iaMax: "50",
      eaObtd: formatMarkVal(nnfPract?.externalObtained ?? 0),
      eaMax: "50",
      totObtd: formatMarkVal(nnfPract?.totalObtained ?? 0),
      totMax: "100",
      pct: formatDecimal(nnfPract?.percentage ?? 0),
      grade: nnfPract?.letterGrade || "C",
      gp: nnfPract?.gradePoint ?? 0,
      pass: nnfPract ? (nnfPract.isPass ? "PASS" : "Fail") : "PASS",
    },
    {
      slNo: "04.",
      codeLines: ["*HNIT 145"],
      codeText: hnit?.courseCode || "*HNIT 145",
      titleLines: ["Health/ Nursing", "Informatics", "& Technology"],
      titleText: "*Health/ Nursing Informatics & Technology",
      credits: "3",
      iaObtd: formatMarkVal(hnit?.internalObtained ?? 0),
      iaMax: "25",
      eaObtd: formatMarkVal(hnit?.externalObtained ?? 0),
      eaMax: "25",
      totObtd: formatMarkVal(hnit?.totalObtained ?? 0),
      totMax: "50",
      pct: formatDecimal(hnit?.percentage ?? 0),
      grade: hnit?.letterGrade || "C",
      gp: hnit?.gradePoint ?? 0,
      pass: hnit ? (hnit.isPass ? "PASS" : "Fail") : "PASS",
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
            B.Sc. NURSING FIRST YEAR (SECOND SEMESTER) UNIVERSITY EXAMINATION {info.attemptIndicator ? `${info.attemptIndicator} ` : ""}{sessionMonthYear.toUpperCase()}
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
                <td className="col-credits border border-black p-1 text-center font-bold">31</td>
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
            * HNIT 145 College Exam, Pass marks-50% as per INC & SGPGIMS regulations
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

export default Sem2Marksheet;