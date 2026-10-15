"use client";

import React, { useState } from "react";
import { BookOpen, CheckCircle, Download } from "lucide-react";
import { ALL_SEMESTERS_DATA } from "../data/semesterData";

export const SemesterSchemasExplorer: React.FC = () => {
  const [selectedSem, setSelectedSem] = useState<number>(1);
  const semData = ALL_SEMESTERS_DATA[selectedSem];

  const handleDownloadTemplate = (semNumber: number) => {
    // Trigger download via API or backend
    window.location.href = `/api/template/${semNumber}`;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Semester Selector Navigation */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                B.Sc. Nursing Semester Course Schemas (Semesters 1 to 8)
              </h2>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Select any semester to explore courses, granular examination components, credit hours, passing thresholds & download template.
            </p>
          </div>

          <button
            onClick={() => handleDownloadTemplate(selectedSem)}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all shadow-sm shadow-emerald-600/20"
          >
            <Download className="w-4 h-4" />
            <span>Download Semester {selectedSem} Template (.xlsx)</span>
          </button>
        </div>

        {/* 8 Semester tabs */}
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
          {([1, 2, 3, 4, 5, 6, 7, 8] as const).map((sem) => {
            const isSelected = selectedSem === sem;
            const data = ALL_SEMESTERS_DATA[sem];

            return (
              <button
                key={sem}
                onClick={() => setSelectedSem(sem)}
                className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                  isSelected
                    ? "bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-600/30 font-bold"
                    : "border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <span className="text-xs font-mono">SEM</span>
                <span className="text-xl font-black">{sem}</span>
                <span className={`text-[10px] mt-0.5 ${isSelected ? "text-blue-100" : "text-slate-400"}`}>
                  {data?.year_name?.split(" ")[0]} Yr
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Semester Details Banner */}
      <div className="bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 border border-slate-800 rounded-2xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold text-blue-300 uppercase tracking-widest mb-1.5">
              <span>{semData.degree_title}</span>
              <span>•</span>
              <span>{semData.year_name}</span>
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {semData.semester_name}
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              Affiliated Institution: <span className="font-semibold">{semData.college_name}</span> (Code: {semData.college_code})
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-3 w-full md:w-auto">
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-3 text-center min-w-[100px]">
              <div className="text-[10px] uppercase text-slate-400 font-semibold">Total Credits</div>
              <div className="text-xl font-black font-mono text-emerald-400 mt-0.5">
                {semData.total_prescribed_credits}
              </div>
            </div>

            <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-3 text-center min-w-[100px]">
              <div className="text-[10px] uppercase text-slate-400 font-semibold">SGPA Credits</div>
              <div className="text-xl font-black font-mono text-sky-400 mt-0.5">
                {semData.sgpa_eligible_credits}
              </div>
            </div>

            <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-3 text-center min-w-[100px]">
              <div className="text-[10px] uppercase text-slate-400 font-semibold">Grand Total</div>
              <div className="text-xl font-black font-mono text-amber-400 mt-0.5">
                {semData.grand_total_marks}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Course Breakdown Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
          <div>
            <h4 className="font-bold text-base text-slate-900 dark:text-white">
              Course Catalog & Examination Components
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Granular breakdown of Internal Assessment, University Exams, Practicum, and passing rules
            </p>
          </div>
          <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-3 py-1 rounded-lg font-mono">
            {semData.courses.length} Prescribed Course Units
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 text-xs font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 text-center">Sl.</th>
                <th className="px-4 py-3">Course Code & Title</th>
                <th className="px-4 py-3 text-center">Credits</th>
                <th className="px-4 py-3 text-center">IA Max (Pass)</th>
                <th className="px-4 py-3 text-center">Univ/College Exam</th>
                <th className="px-4 py-3 text-center">Total Max</th>
                <th className="px-4 py-3 text-center">Pass %</th>
                <th className="px-4 py-3 text-center">SGPA Rule</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {semData.courses.map((course) => {
                const isEnglishOrElective = course.is_english_or_elective;

                return (
                  <React.Fragment key={course.course_code}>
                    {course.components.map((comp, compIdx) => (
                      <tr
                        key={`${course.course_code}-${compIdx}`}
                        className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                          isEnglishOrElective ? "bg-amber-50/30 dark:bg-amber-950/10" : ""
                        }`}
                      >
                        <td className="px-4 py-3 text-center font-mono text-xs font-semibold text-slate-500">
                          {compIdx === 0 ? `0${course.sl_no}.` : ""}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <span className="font-mono text-xs text-blue-600 dark:text-blue-400">
                              {course.course_code}
                            </span>
                            {course.components.length > 1 && (
                              <span className="text-[11px] bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded font-mono">
                                {comp.name}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-slate-600 dark:text-slate-300 font-medium mt-0.5">
                            {course.title}
                          </div>
                          {comp.sub_components && comp.sub_components.length > 0 && (
                            <div className="text-[11px] text-slate-500 mt-1 flex flex-wrap gap-2">
                              {comp.sub_components.map((sub, sIdx) => (
                                <span key={sIdx} className="bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded">
                                  {sub.name}: Max {sub.max_marks}
                                </span>
                              ))}
                            </div>
                          )}
                          {course.footnotes && compIdx === 0 && (
                            <div className="text-[11px] text-amber-600 dark:text-amber-400 mt-1 italic">
                              {course.footnotes}
                            </div>
                          )}
                        </td>

                        <td className="px-4 py-3 text-center font-mono font-bold text-slate-800 dark:text-slate-200">
                          {comp.credits || course.credits}
                          {course.credit_breakdown && (
                            <div className="text-[10px] text-slate-400 font-normal">
                              {course.credit_breakdown}
                            </div>
                          )}
                        </td>

                        <td className="px-4 py-3 text-center font-mono">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">
                            {comp.ia_max}
                          </span>
                          {comp.ia_min_pass !== undefined && (
                            <span className="text-xs text-slate-400 ml-1">
                              (Min {comp.ia_min_pass})
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-3 text-center font-mono">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">
                            {comp.ea_max}
                          </span>
                          {comp.ea_min_pass !== undefined && (
                            <span className="text-xs text-slate-400 ml-1">
                              (Min {comp.ea_min_pass})
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-3 text-center font-mono font-bold text-slate-900 dark:text-white">
                          {comp.total_max}
                        </td>

                        <td className="px-4 py-3 text-center">
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                              course.passing_threshold_percent === 40
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300"
                                : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300"
                            }`}
                          >
                            {course.passing_threshold_percent}% Pass
                          </span>
                        </td>

                        <td className="px-4 py-3 text-center text-xs">
                          {course.include_in_sgpa ? (
                            <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center justify-center gap-1">
                              <CheckCircle className="w-3.5 h-3.5" />
                              <span>Added</span>
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">
                              Excluded from SGPA
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
