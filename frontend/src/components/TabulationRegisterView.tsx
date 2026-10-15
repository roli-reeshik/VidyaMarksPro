"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  FileSpreadsheet,
  Download,
  Printer,
  RefreshCw,
  Layers,
  ChevronLeft,
  ChevronRight,
  Database,
  CheckCircle2,
  AlertTriangle,
  Award,
  GraduationCap,
  History
} from "lucide-react";
import { EvaluatedStudentRecord } from "../types/marksheet";
import { VisualAuditLogModal } from "./VisualAuditLogModal";

interface TabulationCourseHeader {
  course_code: string;
  course_title: string;
  short_title: string;
  credits: number;
  ia_max: number;
  ea_max: number;
  total_max: number;
}

interface TabulationStudentCourseMark {
  course_code: string;
  ia: string;
  ea: string;
  total: string;
  grade: string;
  grade_point: number;
  is_pass: boolean;
  is_exempted: boolean;
  grace: number;
}

interface TabulationStudentRow {
  sl_no: number;
  roll_no: string;
  enroll_no: string;
  student_name: string;
  father_name: string;
  course_marks: Record<string, TabulationStudentCourseMark>;
  grand_total: string;
  grand_max: string;
  percentage: string;
  sgpa: string;
  result_status: string;
  remarks: string;
  attempt_label: string;
  is_pass: boolean;
  is_grace: boolean;
}

interface TabulationRegisterPage {
  page_number: number;
  students: TabulationStudentRow[];
}

interface TabulationRegisterData {
  institution_name: string;
  college_name: string;
  semester_number: number;
  semester_name: string;
  year_name: string;
  batch_name: string;
  session_month_year: string;
  exam_type: string;
  issue_date: string;
  courses: TabulationCourseHeader[];
  all_students: TabulationStudentRow[];
  pages: TabulationRegisterPage[];
  total_appeared: number;
  total_passed: number;
  total_failed: number;
  total_grace: number;
  pass_percentage: number;
}

interface TabulationRegisterViewProps {
  currentStudents?: EvaluatedStudentRecord[];
  onNavigateToUpload?: () => void;
}

export const TabulationRegisterView: React.FC<TabulationRegisterViewProps> = ({
  currentStudents = [],
}) => {
  const [semester, setSemester] = useState<number>(1);
  const [sourceMode, setSourceMode] = useState<"database" | "current">(
    currentStudents.length > 0 ? "current" : "database"
  );
  const [pageSize, setPageSize] = useState<number>(15);
  const [activePageIndex, setActivePageIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [trData, setTrData] = useState<TabulationRegisterData | null>(null);

  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [downloadingExcel, setDownloadingExcel] = useState<boolean>(false);
  const [isSyncingDb, setIsSyncingDb] = useState<boolean>(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState<string | null>(null);

  // Field-level audit modal state
  const [isAuditOpen, setIsAuditOpen] = useState<boolean>(false);
  const [selectedAuditStudent, setSelectedAuditStudent] = useState<{
    roll_no: string;
    name: string;
    enrollment_no?: string;
  } | null>(null);

  // Fetch or construct Tabulation Register data
  const loadTabulationData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (sourceMode === "current" && currentStudents.length > 0) {
        // Construct directly from in-memory student records via payload endpoint
        const res = await fetch("http://127.0.0.1:8000/api/v1/tabulation-register/data-from-payload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            students: currentStudents,
            semester_number: semester,
            batch_name: "Batch 2022-2026",
            session_month_year: "JANUARY - 2026",
            page_size: pageSize,
          }),
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Failed to load Tabulation Register from current uploaded students.");
        }
        const data: TabulationRegisterData = await res.json();
        setTrData(data);
        setActivePageIndex(0);

        // Auto-sync in background so PostgreSQL is automatically updated
        fetch("http://127.0.0.1:8000/api/v1/tabulation-register/sync-to-db", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            students: currentStudents,
            semester_number: semester,
            batch_name: "Batch 2022-2026",
            session_month_year: "JANUARY - 2026",
            page_size: pageSize,
          }),
        }).catch(() => {});
      } else {
        const res = await fetch(
          `http://127.0.0.1:8000/api/v1/tabulation-register/data?semester=${semester}&page_size=${pageSize}`
        );
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Failed to load Tabulation Register from database.");
        }
        const data: TabulationRegisterData = await res.json();
        setTrData(data);
        setActivePageIndex(0);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setTrData(null);
    } finally {
      setLoading(false);
    }
  }, [semester, sourceMode, pageSize, currentStudents]);

  const handleSyncToDatabase = async () => {
    const listToSync = (sourceMode === "current" && currentStudents.length > 0)
      ? currentStudents
      : (trData?.all_students || []);
    if (listToSync.length === 0) return;

    setIsSyncingDb(true);
    setSyncSuccessMsg(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/tabulation-register/sync-to-db", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          students: listToSync,
          semester_number: semester,
          batch_name: trData?.batch_name || "Batch 2022-2026",
          session_month_year: trData?.session_month_year || "JANUARY - 2026",
          page_size: pageSize,
        }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to sync student marks to database.");
      }
      const data = await res.json();
      setSyncSuccessMsg(`✓ Stored ${data.synced_count} student marks into vidya_examination_db!`);
      setTimeout(() => setSyncSuccessMsg(null), 6000);
      if (sourceMode === "database") {
        await loadTabulationData();
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSyncingDb(false);
    }
  };

  useEffect(() => {
    loadTabulationData();
  }, [loadTabulationData]);

  // Download PDF Handler (A3 Landscape 300 DPI)
  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      if (sourceMode === "current" && currentStudents.length > 0) {
        const response = await fetch("http://127.0.0.1:8000/api/v1/tabulation-register/export-pdf", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            students: currentStudents,
            semester_number: semester,
            batch_name: trData?.batch_name || "Batch 2022-2026",
            session_month_year: trData?.session_month_year || "JANUARY - 2026",
            page_size: pageSize,
          }),
        });
        if (!response.ok) throw new Error("PDF generation failed.");
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `SGPGIMS_Tabulation_Register_Sem${semester}_A3_Landscape.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        const url = `http://127.0.0.1:8000/api/v1/tabulation-register/pdf?semester=${semester}&paper_size=A3&page_size=${pageSize}`;
        window.open(url, "_blank");
      }
    } catch (err) {
      alert("Error downloading Tabulation Register PDF: " + err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Download Excel Handler (.xlsx via openpyxl)
  const handleDownloadExcel = async () => {
    setDownloadingExcel(true);
    try {
      if (sourceMode === "current" && currentStudents.length > 0) {
        const response = await fetch("http://127.0.0.1:8000/api/v1/tabulation-register/export-excel", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            students: currentStudents,
            semester_number: semester,
            batch_name: trData?.batch_name || "Batch 2022-2026",
            session_month_year: trData?.session_month_year || "JANUARY - 2026",
            page_size: pageSize,
          }),
        });
        if (!response.ok) throw new Error("Excel generation failed.");
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `SGPGIMS_Tabulation_Register_Sem${semester}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        const url = `http://127.0.0.1:8000/api/v1/tabulation-register/excel?semester=${semester}`;
        window.open(url, "_blank");
      }
    } catch (err) {
      alert("Error downloading Tabulation Register Excel: " + err);
    } finally {
      setDownloadingExcel(false);
    }
  };

  // Browser Print Preview Handler
  const handleBrowserPrint = () => {
    const url = `http://127.0.0.1:8000/api/v1/tabulation-register/preview-html?semester=${semester}&page_size=${pageSize}`;
    const printWin = window.open(url, "_blank");
    if (printWin) {
      printWin.focus();
    }
  };

  const totalPages = Math.max(1, trData?.pages?.length || 1);
  const safePageIndex = Math.min(Math.max(0, activePageIndex), totalPages - 1);
  const currentPage = trData?.pages?.[safePageIndex] || trData?.pages?.[0];

  const getCourseMark = (s: TabulationStudentRow, courseCode: string) => {
    if (!s.course_marks) return undefined;
    if (s.course_marks[courseCode]) return s.course_marks[courseCode];
    const norm = courseCode.replace(/[^\w]/g, "").toUpperCase();
    for (const [k, v] of Object.entries(s.course_marks)) {
      const kNorm = k.replace(/[^\w]/g, "").toUpperCase();
      if (kNorm === norm) return v;
      if (kNorm.includes(norm) || norm.includes(kNorm)) return v;
    }
    return undefined;
  };

  return (
    <div className="space-y-6">
      {/* Top Title Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-500 rounded-xl shadow-lg shadow-blue-500/25">
              <GraduationCap className="w-8 h-8 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-xl font-bold tracking-tight">Formal Gazette Tabulation Register (TR)</h2>
                <span className="text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold uppercase">
                  A3 / Legal Landscape
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Sanjay Gandhi Postgraduate Institute of Medical Sciences &bull; College of Nursing Institutional Archival Ledger
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf || !trData}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-blue-600/25 transition-all disabled:opacity-50"
            >
              <Download className={`w-4 h-4 ${downloadingPdf ? "animate-bounce" : ""}`} />
              <span>{downloadingPdf ? "Generating A3 PDF..." : "Download TR (PDF)"}</span>
            </button>

            <button
              onClick={handleDownloadExcel}
              disabled={downloadingExcel || !trData}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-emerald-600/25 transition-all disabled:opacity-50"
            >
              <FileSpreadsheet className={`w-4 h-4 ${downloadingExcel ? "animate-bounce" : ""}`} />
              <span>{downloadingExcel ? "Generating Excel..." : "Download TR (Excel .xlsx)"}</span>
            </button>

            <button
              onClick={handleBrowserPrint}
              disabled={!trData}
              className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-all disabled:opacity-50"
            >
              <Printer className="w-4 h-4" />
              <span>Print Preview</span>
            </button>
          </div>
        </div>

        {/* Controls Bar: Semester, Source, Page Size */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 font-medium">Semester:</span>
              <select
                value={semester}
                onChange={(e) => setSemester(Number(e.target.value))}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s} className="bg-slate-900 text-white">
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 font-medium">Source:</span>
              <select
                value={sourceMode}
                onChange={(e) => setSourceMode(e.target.value as "database" | "current")}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                <option value="database" className="bg-slate-900 text-white">
                  Database Roster (vidya_examination_db)
                </option>
                {currentStudents.length > 0 && (
                  <option value="current" className="bg-slate-900 text-white">
                    Current Uploaded File ({currentStudents.length} Students)
                  </option>
                )}
              </select>
            </div>

            <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <span className="text-slate-400 font-medium">Page Size:</span>
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                {[10, 15, 20, 25, 30].map((ps) => (
                  <option key={ps} value={ps} className="bg-slate-900 text-white">
                    {ps} Students / Page
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={loadTabulationData}
              disabled={loading}
              className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition-all cursor-pointer"
              title="Refresh Data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>

            {currentStudents.length > 0 && (
              <button
                onClick={handleSyncToDatabase}
                disabled={isSyncingDb}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold transition-all shadow-sm cursor-pointer disabled:opacity-50"
                title="Save all current student marks into local PostgreSQL database"
              >
                {isSyncingDb ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Syncing...</span>
                  </>
                ) : (
                  <>
                    <Database className="w-3.5 h-3.5" />
                    <span>Save to DB</span>
                  </>
                )}
              </button>
            )}

            {syncSuccessMsg && (
              <span className="text-emerald-400 font-medium text-[11px] flex items-center gap-1 animate-fadeIn">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                {syncSuccessMsg}
              </span>
            )}
          </div>

          {/* Ledger Metadata */}
          {trData && (
            <div className="flex items-center gap-4 text-slate-300">
              <span><b>Batch:</b> {trData.batch_name}</span>
              <span>&bull;</span>
              <span><b>Session:</b> {trData.session_month_year}</span>
              <span>&bull;</span>
              <span><b>Exam Cycle:</b> {trData.exam_type}</span>
            </div>
          )}
        </div>
      </div>

      {/* KPI Cards Strip */}
      {trData && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Total Appeared</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{trData.total_appeared}</p>
            </div>
            <div className="p-2.5 bg-blue-50 dark:bg-blue-950/50 text-blue-600 rounded-lg">
              <Layers className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Passed (Clear)</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">{trData.total_passed - trData.total_grace}</p>
            </div>
            <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Passed w/ Grace</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">{trData.total_grace}</p>
            </div>
            <div className="p-2.5 bg-amber-50 dark:bg-amber-950/50 text-amber-600 rounded-lg">
              <Award className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Backlog / Failed</p>
              <p className="text-2xl font-bold text-rose-600 mt-1">{trData.total_failed}</p>
            </div>
            <div className="p-2.5 bg-rose-50 dark:bg-rose-950/50 text-rose-600 rounded-lg">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between col-span-2 sm:col-span-1">
            <div>
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Pass Percentage</p>
              <p className="text-2xl font-bold text-indigo-600 mt-1">{trData.pass_percentage}%</p>
            </div>
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 rounded-lg">
              <Database className="w-5 h-5" />
            </div>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && !trData && (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-3" />
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            Constructing Tabulation Register Ledger...
          </p>
        </div>
      )}

      {/* Main Tabulation Register Preview (A3 Landscape View) */}
      {trData && currentPage && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md overflow-hidden">
          {/* Pagination bar */}
          <div className="px-6 py-3.5 bg-slate-50 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 dark:text-slate-400 font-semibold">
              <span>Gazette Page View:</span>
              <span className="bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2.5 py-0.5 rounded font-mono font-bold">
                Page {safePageIndex + 1} of {totalPages}
              </span>
              <span>
                &bull; Showing candidates {trData.total_appeared === 0 ? 0 : safePageIndex * pageSize + 1} to{" "}
                {Math.min((safePageIndex + 1) * pageSize, trData.total_appeared)} of {trData.total_appeared}
              </span>
              {totalPages <= 1 && (
                <span className="text-[11px] font-normal text-slate-500 bg-slate-200/60 dark:bg-slate-800 px-2 py-0.5 rounded">
                  All {trData.total_appeared} candidates on single page
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Quick page size buttons */}
              <div className="flex items-center gap-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-0.5 mr-2">
                <span className="text-[10px] text-slate-400 px-1 font-medium">Page Size:</span>
                {[10, 15, 20, 25, 50].map((size) => (
                  <button
                    key={size}
                    onClick={() => {
                      setPageSize(size);
                      setActivePageIndex(0);
                    }}
                    className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all cursor-pointer ${
                      pageSize === size
                        ? "bg-blue-600 text-white shadow-xs"
                        : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>

              {/* First Page */}
              <button
                onClick={() => setActivePageIndex(0)}
                disabled={safePageIndex === 0}
                className="px-2 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all cursor-pointer disabled:cursor-not-allowed"
                title="First Page"
              >
                &laquo;
              </button>

              {/* Prev Page */}
              <button
                onClick={() => setActivePageIndex((p) => Math.max(0, p - 1))}
                disabled={safePageIndex === 0}
                className="flex items-center gap-1 px-3 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all cursor-pointer disabled:cursor-not-allowed"
                title={safePageIndex === 0 ? "Already on first page" : "Go to previous page"}
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Prev Page</span>
              </button>

              {/* Page numbers */}
              <div className="flex items-center gap-1">
                {trData.pages.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActivePageIndex(idx)}
                    className={`w-7 h-7 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                      idx === safePageIndex
                        ? "bg-blue-600 text-white shadow-sm ring-2 ring-blue-400/30"
                        : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>

              {/* Next Page */}
              <button
                onClick={() => setActivePageIndex((p) => Math.min(totalPages - 1, p + 1))}
                disabled={safePageIndex >= totalPages - 1}
                className="flex items-center gap-1 px-3 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all cursor-pointer disabled:cursor-not-allowed"
                title={safePageIndex >= totalPages - 1 ? "Already on last page" : "Go to next page"}
              >
                <span>Next Page</span>
                <ChevronRight className="w-4 h-4" />
              </button>

              {/* Last Page */}
              <button
                onClick={() => setActivePageIndex(totalPages - 1)}
                disabled={safePageIndex >= totalPages - 1}
                className="px-2 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all cursor-pointer disabled:cursor-not-allowed"
                title="Last Page"
              >
                &raquo;
              </button>
            </div>
          </div>

          {/* Interactive Ledger Scrollable Table */}
          <div className="overflow-x-auto p-4">
            <table className="w-full border-collapse border border-slate-800 text-center text-[11px] leading-tight select-text">
              <thead>
                {/* Tier 1 Headers */}
                <tr className="bg-slate-900 text-white font-bold text-[11px]">
                  <th rowSpan={2} className="border border-slate-700 px-2 py-2 w-10">S.No</th>
                  <th rowSpan={2} className="border border-slate-700 px-2 py-2 w-24">Roll No</th>
                  <th rowSpan={2} className="border border-slate-700 px-2 py-2 w-28">Enrollment No</th>
                  <th rowSpan={2} className="border border-slate-700 px-3 py-2 text-left min-w-[150px]">Candidate Name</th>
                  <th rowSpan={2} className="border border-slate-700 px-3 py-2 text-left min-w-[140px]">Father&apos;s Name</th>

                  {trData.courses.map((c, i) => (
                    <th key={i} colSpan={4} className="border border-slate-700 px-2 py-1.5 bg-slate-800">
                      <div className="font-bold text-[11px]">{c.course_code}</div>
                      <div className="font-normal text-[10px] text-slate-300">{c.short_title} (Cr:{c.credits})</div>
                    </th>
                  ))}

                  <th rowSpan={2} className="border border-slate-700 px-2 py-2 w-16 bg-slate-900">Grand Tot</th>
                  <th rowSpan={2} className="border border-slate-700 px-2 py-2 w-14 bg-slate-900">%</th>
                  <th rowSpan={2} className="border border-slate-700 px-2 py-2 w-14 bg-blue-900 text-blue-200">SGPA</th>
                  <th rowSpan={2} className="border border-slate-700 px-3 py-2 min-w-[120px] bg-slate-900">Result Status</th>
                </tr>

                {/* Tier 2 Sub-Headers */}
                <tr className="bg-slate-800 text-slate-200 font-semibold text-[10px]">
                  {trData.courses.map((c, i) => (
                    <React.Fragment key={i}>
                      <th className="border border-slate-700 px-1 py-1 w-9" title={`IA Max: ${c.ia_max}`}>IA</th>
                      <th className="border border-slate-700 px-1 py-1 w-9" title={`EA Max: ${c.ea_max}`}>EA</th>
                      <th className="border border-slate-700 px-1 py-1 w-10 font-bold" title={`Tot Max: ${c.total_max}`}>Tot</th>
                      <th className="border border-slate-700 px-1 py-1 w-8 font-bold">Grd</th>
                    </React.Fragment>
                  ))}
                </tr>
              </thead>
              <tbody>
                {currentPage.students.map((s, idx) => (
                  <tr
                    key={`${s.roll_no}-${s.attempt_label || "MAIN"}-${idx}`}
                    className={`hover:bg-blue-50/50 dark:hover:bg-blue-950/20 transition-colors ${
                      idx % 2 === 0 ? "bg-white dark:bg-slate-900" : "bg-slate-50/60 dark:bg-slate-800/40"
                    }`}
                  >
                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-medium">{s.sl_no}.</td>
                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-bold font-mono text-slate-900 dark:text-white">
                      {s.roll_no}
                    </td>
                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-mono text-slate-700 dark:text-slate-300 text-[10.5px]">
                      {s.enroll_no}
                    </td>
                    <td className="border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-left font-bold text-slate-900 dark:text-white">
                      <div className="flex items-center justify-between gap-1">
                        <span>{s.student_name}</span>
                        <button
                          onClick={() => {
                            setSelectedAuditStudent({
                              roll_no: s.roll_no,
                              name: s.student_name,
                              enrollment_no: s.enroll_no,
                            });
                            setIsAuditOpen(true);
                          }}
                          className="no-print p-1 rounded hover:bg-purple-100 dark:hover:bg-purple-950/60 text-slate-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors cursor-pointer"
                          title="View Field-Level Audit History"
                        >
                          <History className="w-3 h-3" />
                        </button>
                      </div>
                      {s.attempt_label && s.attempt_label !== "MAIN" && (
                        <span className="inline-block mt-0.5 text-[9px] bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-1.5 py-0.2 rounded font-mono font-semibold">
                          {s.attempt_label}
                        </span>
                      )}
                    </td>
                    <td className="border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-left text-slate-600 dark:text-slate-400">
                      {s.father_name}
                    </td>

                    {/* Course components */}
                    {trData.courses.map((c, i) => {
                      const m = getCourseMark(s, c.course_code);
                      return (
                        <React.Fragment key={i}>
                          <td className={`border border-slate-300 dark:border-slate-700 px-1 py-1 ${m?.is_exempted ? "font-bold text-sky-600 dark:text-sky-400" : ""}`}>
                            {m ? m.ia : "-"}
                          </td>
                          <td className={`border border-slate-300 dark:border-slate-700 px-1 py-1 ${m?.is_exempted ? "font-bold text-sky-600 dark:text-sky-400" : ""}`}>
                            {m ? m.ea : "-"}
                          </td>
                          <td className="border border-slate-300 dark:border-slate-700 px-1 py-1 font-bold">
                            {m ? m.total : "-"}
                          </td>
                          <td className={`border border-slate-300 dark:border-slate-700 px-1 py-1 font-bold ${
                            m?.grade === "F" ? "text-rose-600" : "text-slate-900 dark:text-white"
                          }`}>
                            {m ? m.grade : "-"}
                          </td>
                        </React.Fragment>
                      );
                    })}

                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-bold bg-slate-100 dark:bg-slate-800">
                      {s.grand_total}
                    </td>
                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-semibold">
                      {s.percentage}%
                    </td>
                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-bold font-mono text-blue-700 dark:text-blue-300 bg-blue-50/60 dark:bg-blue-950/40">
                      {s.sgpa}
                    </td>
                    <td className="border border-slate-300 dark:border-slate-700 px-2 py-1.5 font-bold text-[10.5px]">
                      {s.result_status.includes("CLEARED IN REAPPEAR") ? (
                        <span className="text-blue-600 dark:text-blue-400">{s.result_status}</span>
                      ) : s.result_status.includes("PASS WITH") || s.result_status.includes("PWG") ? (
                        <span className="text-amber-600 dark:text-amber-400">{s.result_status}</span>
                      ) : s.result_status.includes("PASS") ? (
                        <span className="text-emerald-600 dark:text-emerald-400">PASS</span>
                      ) : (
                        <span className="text-rose-600 dark:text-rose-400">{s.result_status}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Statutory Signatures Block Preview */}
          <div className="p-6 bg-slate-50/80 dark:bg-slate-950/60 border-t border-slate-200 dark:border-slate-800">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center text-xs">
              <div className="pt-6 border-t-2 border-slate-400 dark:border-slate-600">
                <p className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">Tabulated By</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Dealing Assistant / Tabulator</p>
              </div>

              <div className="pt-6 border-t-2 border-slate-400 dark:border-slate-600">
                <p className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">Verified By</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Scrutinizer / Section Officer</p>
              </div>

              <div className="pt-6 border-t-2 border-slate-400 dark:border-slate-600">
                <p className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">Assistant Registrar (Exams)</p>
                <p className="text-[11px] text-slate-500 mt-0.5">SGPGIMS Examination Section</p>
              </div>

              <div className="pt-6 border-t-2 border-slate-400 dark:border-slate-600">
                <p className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">Controller of Examinations / Sub-Dean</p>
                <p className="text-[11px] text-slate-500 mt-0.5">SGPGI College of Nursing, Lucknow</p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 flex flex-wrap justify-between items-center">
              <span><b>VidyaMarksheet</b> &bull; Gazette Tabulation Register (A3/Legal Landscape Mode) &bull; Copyright &copy; VidyaLabs</span>
              <span>Running Page {activePageIndex + 1} of {trData.pages.length}</span>
            </div>
          </div>
        </div>
      )}

      {/* Field-Level Chronological Audit Trail Modal */}
      <VisualAuditLogModal
        isOpen={isAuditOpen}
        onClose={() => {
          setIsAuditOpen(false);
          setSelectedAuditStudent(null);
        }}
        rollNo={selectedAuditStudent?.roll_no || null}
        studentName={selectedAuditStudent?.name || "Candidate"}
        enrollmentNo={selectedAuditStudent?.enrollment_no}
        semesterNumber={semester}
      />
    </div>
  );
};
