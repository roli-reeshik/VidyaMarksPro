"use client";

import React, { useState, useEffect } from "react";
import {
  FileDown,
  Printer,
  Eye,
  RefreshCw,
} from "lucide-react";
import { DebugCategoryItem, EvaluatedStudentRecord } from "../types/marksheet";

interface MarksheetDebugCategoriesViewProps {
  currentStudents?: EvaluatedStudentRecord[];
  onNavigateToTemplate?: () => void;
  onNavigateToCheck?: () => void;
}

export const MarksheetDebugCategoriesView: React.FC<MarksheetDebugCategoriesViewProps> = ({
  currentStudents = [],
  onNavigateToTemplate,
  onNavigateToCheck
}) => {
  const [categories, setCategories] = useState<DebugCategoryItem[]>([]);
  const [selectedCategoryIdx, setSelectedCategoryIdx] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [isLoadingPreview, setIsLoadingPreview] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // Fetch or evaluate 5 categories
  useEffect(() => {
    const fetchCategories = async () => {
      setIsLoading(true);
      try {
        let res: Response;
        if (currentStudents.length > 0) {
          res = await fetch("/api/pdf/debug-categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentStudents)
          });
        } else {
          res = await fetch("/api/pdf/debug-categories");
        }

        if (res.ok) {
          const data: DebugCategoryItem[] = await res.json();
          setCategories(data);
        }
      } catch (err) {
        console.error("Failed to load debug categories:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCategories();
  }, [currentStudents]);

  // When selected category changes, fetch preview HTML
  useEffect(() => {
    if (categories.length === 0 || !categories[selectedCategoryIdx]) return;

    const student = categories[selectedCategoryIdx].student;
    const fetchHtml = async () => {
      setIsLoadingPreview(true);
      try {
        const res = await fetch("/api/pdf/preview-html?semester=1", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(student)
        });
        if (res.ok) {
          const html = await res.text();
          setPreviewHtml(html);
        }
      } catch (err) {
        console.error("Preview load failed:", err);
      } finally {
        setIsLoadingPreview(false);
      }
    };

    fetchHtml();
  }, [categories, selectedCategoryIdx]);

  const handleDownloadPdf = async () => {
    if (categories.length === 0 || !categories[selectedCategoryIdx]) return;
    const student = categories[selectedCategoryIdx].student;

    setIsDownloading(true);
    try {
      const res = await fetch("/api/pdf/student?semester=1", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(student)
      });
      if (!res.ok) throw new Error("Could not download marksheet PDF.");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Debug_Marksheet_${categories[selectedCategoryIdx].category}_${student.roll_no}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert("Error generating PDF: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsDownloading(false);
    }
  };

  const handlePrint = () => {
    const iframe = document.getElementById("debug-preview-iframe") as HTMLIFrameElement;
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    }
  };

  const activeItem = categories[selectedCategoryIdx];

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/60 px-2.5 py-0.5 rounded-full border border-purple-200 dark:border-purple-800">
                Debugging Telemetry
              </span>
              <span className="text-xs text-slate-400">Institutional Visual QA</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
              5-Category Marksheet Debugging & Preview Engine
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Inspect 5 distinct marksheet scenarios (Pass, Grace, Fail, Distinction, and Borderline) to visually audit formatting and INC regulations.
            </p>
          </div>

          <div className="flex items-center gap-2.5 self-end sm:self-auto">
            {onNavigateToTemplate && (
              <button
                onClick={onNavigateToTemplate}
                className="text-xs font-semibold px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
              >
                Customize Template
              </button>
            )}
            {onNavigateToCheck && (
              <button
                onClick={onNavigateToCheck}
                className="text-xs font-semibold px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors"
              >
                Run INC Gazette Check
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Category Selection Cards Strip */}
      {isLoading && categories.length === 0 ? (
        <div className="py-6 text-center text-xs text-slate-400">Loading audit categories...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {categories.map((cat, idx) => {
          const isSelected = idx === selectedCategoryIdx;
          return (
            <button
              key={cat.category}
              onClick={() => setSelectedCategoryIdx(idx)}
              className={`p-3.5 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                isSelected
                  ? "bg-white dark:bg-slate-900 border-blue-500 shadow-md ring-2 ring-blue-500/20"
                  : "bg-white/80 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 hover:border-slate-300 hover:bg-white"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cat.badge_color}`}>
                    {cat.category}
                  </span>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping"></span>
                  )}
                </div>
                <div className="font-bold text-xs sm:text-sm text-slate-900 dark:text-white line-clamp-1">
                  {cat.category_title}
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                  {cat.student.student_name} ({cat.student.roll_no})
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-[10px] font-mono text-slate-500">
                <span>{cat.student.overall_percentage}%</span>
                <span>SGPA: {cat.student.sgpa ?? "N/A"}</span>
              </div>
            </button>
          );
        })}
        </div>
      )}

      {/* Main Debug View Area: Telemetry & Live Marksheet Viewer */}
      {activeItem && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Details & Diagnostics (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Category Telemetry Card */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${activeItem.badge_color}`}>
                  {activeItem.category_title}
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  {activeItem.source}
                </span>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {activeItem.description}
              </p>

              {/* Student Demographics Info */}
              <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3 border border-slate-100 dark:border-slate-800 space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Candidate:</span>
                  <span className="font-semibold text-slate-900 dark:text-white font-mono">{activeItem.student.student_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Roll Number:</span>
                  <span className="font-mono text-slate-800 dark:text-slate-200">{activeItem.student.roll_no}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Enrollment No:</span>
                  <span className="font-mono text-slate-800 dark:text-slate-200">{activeItem.student.enroll_no}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Father&apos;s Name:</span>
                  <span className="text-slate-800 dark:text-slate-200">{activeItem.student.father_name}</span>
                </div>
              </div>

              {/* Regulatory Telemetry */}
              <div className="space-y-2 border-t border-slate-100 dark:border-slate-800 pt-3 text-xs">
                <div className="font-bold text-slate-800 dark:text-slate-200 text-[11px] uppercase tracking-wide">
                  Regulatory Telemetry
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Result Verdict:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{activeItem.student.result_status}</span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Grace Awarded:</span>
                  <span className={`font-mono font-bold ${activeItem.student.total_grace > 0 ? "text-amber-600 dark:text-amber-400" : "text-slate-700"}`}>
                    {activeItem.student.total_grace || 0} marks
                  </span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Grand Total:</span>
                  <span className="font-mono font-bold text-slate-900 dark:text-white">
                    {activeItem.student.total_marks_obtained} / {activeItem.student.total_marks_max} ({activeItem.student.overall_percentage}%)
                  </span>
                </div>

                <div className="flex justify-between items-center py-1 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Calculated SGPA:</span>
                  <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                    {activeItem.student.sgpa ? activeItem.student.sgpa.toFixed(2) : "N/A (Failed)"}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500">Applicable Rule:</span>
                  <span className="text-[11px] text-slate-600 dark:text-slate-300 text-right max-w-[200px]">
                    {activeItem.telemetry.rule}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-2 pt-2">
                <button
                  onClick={handleDownloadPdf}
                  disabled={isDownloading}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-xs font-semibold py-2.5 rounded-xl shadow-md transition-all"
                >
                  {isDownloading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Generating High-Res PDF...</span>
                    </>
                  ) : (
                    <>
                      <FileDown className="w-4 h-4" />
                      <span>Download {activeItem.category} Marksheet (PDF)</span>
                    </>
                  )}
                </button>

                <button
                  onClick={handlePrint}
                  className="w-full flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold py-2 rounded-xl transition-all"
                >
                  <Printer className="w-4 h-4" />
                  <span>Print Print Preview</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Marksheet Preview (8 cols) */}
          <div className="lg:col-span-8 space-y-3">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-xs font-bold text-slate-900 dark:text-white">
                  Visual Layout Inspection &mdash; {activeItem.student.student_name}
                </span>
                {isLoadingPreview && (
                  <span className="text-[11px] text-blue-500 animate-pulse font-medium">
                    Rendering...
                  </span>
                )}
              </div>

              <div className="text-xs text-slate-400 font-mono">
                Legal 8.5&quot; &times; 14&quot; &bull; 2.5&quot; Top Clearance
              </div>
            </div>

            <div className="bg-slate-200 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-2xl p-4 overflow-hidden shadow-inner flex justify-center">
              <div className="w-full max-w-[850px] bg-white rounded-lg shadow-xl overflow-hidden min-h-[750px] border border-slate-300">
                {previewHtml ? (
                  <iframe
                    id="debug-preview-iframe"
                    srcDoc={previewHtml}
                    className="w-full h-[780px] border-none"
                    title={`Marksheet Preview - ${activeItem.student.student_name}`}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-[650px] text-slate-400 text-xs">
                    <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2"></div>
                    <span>Rendering official marksheet layout...</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
