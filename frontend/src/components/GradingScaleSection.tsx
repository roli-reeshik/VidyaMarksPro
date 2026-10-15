"use client";

import React, { useState } from "react";
import { Scale, CheckCircle2, Calculator, AlertCircle } from "lucide-react";
import { INC_GRADING_SCALE } from "../data/semesterData";

export const GradingScaleSection: React.FC = () => {
  // Live Simulator state
  const [testObtained, setTestObtained] = useState<number>(65);
  const [testMax, setTestMax] = useState<number>(100);
  const [isEnglishOrElective, setIsEnglishOrElective] = useState<boolean>(false);
  const [isAbsent, setIsAbsent] = useState<boolean>(false);

  // Client-side simulation of the INC 10-Point Engine
  const calculateSimulatedGrade = () => {
    if (isAbsent) {
      return { grade: "Ab", gp: 0, pass: false, desc: "Absent", pct: 0 };
    }
    if (testMax <= 0) {
      return { grade: "F", gp: 0, pass: false, desc: "Invalid Max", pct: 0 };
    }
    const pct = Math.round((testObtained / testMax) * 10000) / 100;

    if (pct >= 85.0) return { grade: "O", gp: 10, pass: true, desc: "Outstanding", pct };
    if (pct >= 80.0) return { grade: "A+", gp: 9, pass: true, desc: "Excellent", pct };
    if (pct >= 75.0) return { grade: "A", gp: 8, pass: true, desc: "Very Good", pct };
    if (pct >= 65.0) return { grade: "B+", gp: 7, pass: true, desc: "Good", pct };
    if (pct >= 60.0) return { grade: "B", gp: 6, pass: true, desc: "Above Average", pct };
    if (pct >= 50.0) return { grade: "C", gp: 5, pass: true, desc: "Average / Pass", pct };
    if (pct >= 40.0) {
      if (isEnglishOrElective) {
        return { grade: "P", gp: 4, pass: true, desc: "Pass", pct };
      }
      return { grade: "F", gp: 0, pass: false, desc: "Fail (<50% in standard course)", pct };
    }
    return { grade: "F", gp: 0, pass: false, desc: "Fail", pct };
  };

  const simResult = calculateSimulatedGrade();

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header card */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold mb-3 border border-blue-500/30">
              <Scale className="w-3.5 h-3.5" />
              <span>Statutory Grading Framework</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              INC 10-Point Grading Scale Engine
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Standardized evaluation framework prescribed by the Indian Nursing Council (INC) Gazette Notification and SGPGIMS Lucknow Examination Byelaws.
            </p>
          </div>

          <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-4 text-xs space-y-1.5 min-w-[280px]">
            <div className="font-semibold text-slate-200 flex items-center gap-1.5 pb-1 border-b border-slate-700">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Passing Thresholds Summary</span>
            </div>
            <div className="flex justify-between text-slate-300 pt-1">
              <span>Standard Nursing Courses:</span>
              <strong className="text-emerald-400 font-mono">Min 50.00% (Grade C)</strong>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>English & Electives:</span>
              <strong className="text-sky-400 font-mono">Min 40.00% (Grade P)</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Official Table + Interactive Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Official 10-Point Table */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Statutory 10-Point Grade Matrix
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Percentages, Letter Grades, Grade Points & Conditions
              </p>
            </div>
            <span className="text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2.5 py-1 rounded-md font-mono font-semibold">
              9 Evaluation Tiers
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Percentage Range</th>
                  <th className="px-4 py-3 text-center">Letter Grade</th>
                  <th className="px-4 py-3 text-center">Grade Point</th>
                  <th className="px-4 py-3">Qualitative Performance</th>
                  <th className="px-4 py-3">Applicability / Rule</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {INC_GRADING_SCALE.map((tier, idx) => {
                  const isP = tier.letter_grade === "P";
                  const isFail = tier.letter_grade === "F" || tier.letter_grade === "Ab";
                  const isHigh = tier.grade_point >= 8;

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors ${
                        isP ? "bg-amber-500/5" : isFail ? "bg-red-500/5" : ""
                      }`}
                    >
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white font-mono text-xs">
                        {tier.percentage_range}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-block w-8 py-0.5 text-center font-bold font-mono rounded text-xs ${
                            isHigh
                              ? "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700"
                              : isP
                              ? "bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-700"
                              : isFail
                              ? "bg-red-100 dark:bg-red-950/60 text-red-700 dark:text-red-300 border border-red-300 dark:border-red-700"
                              : "bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-700"
                          }`}
                        >
                          {tier.letter_grade}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center font-bold font-mono text-slate-800 dark:text-slate-200">
                        {tier.grade_point}
                      </td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-medium">
                        {tier.qualitative_description}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400 leading-snug">
                        {tier.notes}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-900/60 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <span>
              <strong>Crucial Regulatory Restriction:</strong> Grade &apos;P&apos; (Grade Point 4) is legally restricted strictly to Communicative English (Sem 1) and Elective Modules. Any candidate scoring 40.00% to 49.99% in standard nursing courses (Anatomy, Nursing Foundation, Pharmacology, Medical-Surgical, etc.) receives Grade &apos;F&apos; (Grade Point 0) and is declared FAIL.
            </span>
          </div>
        </div>

        {/* Live Simulator Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
                <Calculator className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">
                  Interactive Grade Simulator
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Test score against the INC regulatory engine
                </p>
              </div>
            </div>

            {/* Form controls */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Marks Obtained: <span className="font-mono text-blue-600 dark:text-blue-400">{testObtained}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max={testMax}
                  step="0.5"
                  value={testObtained}
                  disabled={isAbsent}
                  onChange={(e) => setTestObtained(parseFloat(e.target.value) || 0)}
                  className="w-full accent-blue-600"
                />
                <div className="flex justify-between text-[11px] text-slate-400 font-mono mt-0.5">
                  <span>0</span>
                  <span>{testMax / 2} (50%)</span>
                  <span>{testMax} (100%)</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Maximum Marks:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[50, 75, 100, 200].slice(0, 3).map((m) => (
                    <button
                      key={m}
                      onClick={() => {
                        setTestMax(m);
                        if (testObtained > m) setTestObtained(m);
                      }}
                      className={`py-1.5 rounded-lg text-xs font-mono font-medium border transition-colors ${
                        testMax === m
                          ? "bg-blue-600 text-white border-blue-600"
                          : "border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                      }`}
                    >
                      {m} Marks
                    </button>
                  ))}
                </div>
              </div>

              {/* Toggles */}
              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <label className="flex items-center gap-2.5 cursor-pointer text-xs text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={isEnglishOrElective}
                    onChange={(e) => setIsEnglishOrElective(e.target.checked)}
                    className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span>Communicative English or Elective Module (Pass: 40%)</span>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer text-xs text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={isAbsent}
                    onChange={(e) => setIsAbsent(e.target.checked)}
                    className="w-4 h-4 rounded text-rose-600 focus:ring-rose-500"
                  />
                  <span className="text-rose-600 dark:text-rose-400 font-medium">Candidate was Absent</span>
                </label>
              </div>
            </div>
          </div>

          {/* Result card */}
          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-4 rounded-xl">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400">
                Evaluation Output
              </span>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                  simResult.pass
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300"
                    : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 border border-red-300"
                }`}
              >
                {simResult.pass ? "QUALIFIED / PASS" : "FAIL / REAPPEAR"}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Percentage</div>
                <div className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                  {simResult.pct}%
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Grade</div>
                <div
                  className={`text-lg font-black font-mono ${
                    simResult.pass ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                  }`}
                >
                  {simResult.grade}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Grade Point</div>
                <div className="text-lg font-bold font-mono text-blue-600 dark:text-blue-400">
                  {simResult.gp} / 10
                </div>
              </div>
            </div>

            <div className="mt-3 text-xs text-center text-slate-600 dark:text-slate-400 font-medium">
              Performance: <strong className="text-slate-900 dark:text-white">{simResult.desc}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
