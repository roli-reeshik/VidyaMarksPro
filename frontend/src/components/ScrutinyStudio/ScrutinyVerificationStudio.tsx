"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Search,
  Filter,
  Info,
  Clock,
  Sparkles,
  ExternalLink,
  Plus,
  Trash2,
  X,
  HelpCircle,
  Award,
  Layers,
  ArrowRight,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

interface CourseSubcomponent {
  name: string;
  code?: string;
  max_marks: number;
  min_pass_marks?: number;
}

interface IncCourseRule {
  sl_no: number;
  course_code: string;
  title: string;
  credits: number;
  credit_breakdown?: string;
  passing_threshold_percent: number;
  is_english_or_elective: boolean;
  include_in_sgpa: boolean;
  is_college_exam: boolean;
  ia_max: number;
  ia_min_pass: number;
  ea_max: number;
  ea_min_pass: number;
  total_max: number;
  subcomponents?: CourseSubcomponent[];
  footnotes?: string;
}

interface IncRules {
  semester_number: number;
  semester_name: string;
  total_prescribed_credits: number;
  sgpa_divisor_credits: number;
  grand_total_marks: number;
  program_total_credits: number;
  courses: IncCourseRule[];
  grading_scale: Array<{
    grade: string;
    grade_point: number;
    range: string;
    desc: string;
  }>;
}

interface StudentCourseData {
  course_id: number;
  course_code: string;
  course_title: string;
  internal: number;
  external_a?: number | null;
  external_b?: number | null;
  external_c?: number | null;
  external: number;
  total: number;
  grade: string;
  gp: number;
  result: string;
  is_exempted?: boolean;
}

interface StudentRosterItem {
  student_id: number;
  registration_id: number;
  roll_no: string;
  enrollment_no: string;
  student_name: string;
  father_name: string;
  semester_number: number;
  exam_month_year: string;
  grand_total_obtained: number;
  grand_total_max: number;
  percentage: number;
  sgpa: number | null;
  result_status: string;
  scrutiny_status: "PENDING" | "FLAGGED" | "VERIFIED" | string;
  last_scrutinized_at?: string | null;
  latest_verification?: {
    id: number;
    status: string;
    comments?: string | null;
    highlighted_fields?: string[];
    suggested_changes?: Record<string, any>;
    iteration_number: number;
    verified_at?: string | null;
    is_actioned_by_admin: boolean;
  } | null;
}

interface DatasheetRowItem {
  sl_no: number;
  registration_id: number;
  student_id: number;
  roll_no: string;
  enrollment_no: string;
  student_name: string;
  father_name: string;
  courses: Record<string, StudentCourseData>;
  grand_total: number;
  percentage: number;
  sgpa: number | null;
  result_status: string;
  scrutiny_status: string;
}

interface SuggestedChangeItem {
  course_code: string;
  field: string;
  current_val: number | string;
  suggested_val: number | string;
  reason: string;
}

export const ScrutinyVerificationStudio: React.FC = () => {
  const { user } = useAuth();
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [selectedSession, setSelectedSession] = useState<string>("All Sessions");
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [incRules, setIncRules] = useState<IncRules | null>(null);
  const [studentsRoster, setStudentsRoster] = useState<StudentRosterItem[]>([]);
  const [datasheetRows, setDatasheetRows] = useState<DatasheetRowItem[]>([]);

  // Navigation & selection
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Interactive verification state
  const [highlightedFields, setHighlightedFields] = useState<string[]>([]);
  const [comments, setComments] = useState<string>("");
  const [suggestedChangesList, setSuggestedChangesList] = useState<SuggestedChangeItem[]>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // New suggestion builder inputs
  const [builderCourse, setBuilderCourse] = useState<string>("");
  const [builderField, setBuilderField] = useState<string>("internal");
  const [builderSuggestedVal, setBuilderSuggestedVal] = useState<string>("");
  const [builderReason, setBuilderReason] = useState<string>("");

  // INC Drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);

  // Auto-scroll ref for datasheet row
  const activeRowRef = useRef<HTMLTableRowElement | null>(null);

  const fetchSessionContext = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      let url = `/api/v1/scrutiny/session-context?semester=${selectedSemester}`;
      if (selectedSession && selectedSession !== "All Sessions") {
        url += `&exam_month_year=${encodeURIComponent(selectedSession)}`;
      }

      const res = await fetch(url, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}: Failed to load scrutiny data.`);
      }

      const data = await res.json();
      setIncRules(data.inc_rules);
      setStudentsRoster(data.students || []);
      setDatasheetRows(data.datasheet_rows || []);
      setCurrentIndex(0);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to connect to scrutiny service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionContext();
  }, [selectedSemester, selectedSession]);

  // When active student changes, prefill verification history
  const activeStudent = studentsRoster[currentIndex] || null;
  const activeDatasheetRow = datasheetRows[currentIndex] || null;

  useEffect(() => {
    if (activeStudent) {
      if (activeStudent.latest_verification) {
        setComments(activeStudent.latest_verification.comments || "");
        setHighlightedFields(activeStudent.latest_verification.highlighted_fields || []);
        const changesMap = activeStudent.latest_verification.suggested_changes || {};
        const parsedList: SuggestedChangeItem[] = [];
        for (const [code, info] of Object.entries(changesMap)) {
          parsedList.push({
            course_code: code,
            field: (info as any).field || "marks",
            current_val: (info as any).current_val ?? "",
            suggested_val: (info as any).suggested_val ?? "",
            reason: (info as any).reason || "",
          });
        }
        setSuggestedChangesList(parsedList);
      } else {
        setComments("");
        setHighlightedFields([]);
        setSuggestedChangesList([]);
      }
    }
  }, [currentIndex, studentsRoster]);

  // Auto-scroll active row in datasheet table
  useEffect(() => {
    if (activeRowRef.current) {
      activeRowRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [currentIndex]);

  const showToast = (text: string, type: "success" | "error") => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Toggle field highlighting
  const toggleHighlight = (fieldKey: string, courseCode?: string, fieldName?: string, currentVal?: number | string) => {
    setHighlightedFields((prev) => {
      const exists = prev.includes(fieldKey);
      if (exists) {
        return prev.filter((k) => k !== fieldKey);
      } else {
        // Prepopulate suggestion builder
        if (courseCode) {
          setBuilderCourse(courseCode);
          if (fieldName) setBuilderField(fieldName);
          if (currentVal !== undefined) setBuilderSuggestedVal(String(currentVal));
        }
        return [...prev, fieldKey];
      }
    });
  };

  // Add suggested change
  const handleAddSuggestedChange = () => {
    if (!builderCourse || !builderSuggestedVal || !builderReason) {
      showToast("Please select a course, enter a suggested mark, and provide a discrepancy reason.", "error");
      return;
    }

    const currentMark =
      activeDatasheetRow?.courses[builderCourse]
        ? (activeDatasheetRow.courses[builderCourse] as any)[builderField] ?? 0
        : 0;

    const newItem: SuggestedChangeItem = {
      course_code: builderCourse,
      field: builderField,
      current_val: currentMark,
      suggested_val: builderSuggestedVal,
      reason: builderReason,
    };

    setSuggestedChangesList((prev) => [...prev, newItem]);
    setBuilderReason("");
    showToast(`Suggestion added for ${builderCourse} (${builderField})`, "success");
  };

  const handleRemoveSuggestedChange = (idx: number) => {
    setSuggestedChangesList((prev) => prev.filter((_, i) => i !== idx));
  };

  // Submit verification: VERIFIED_CORRECT or NEEDS_CORRECTION
  const handleVerifySubmit = async (status: "VERIFIED_CORRECT" | "NEEDS_CORRECTION") => {
    if (!activeStudent) return;
    setIsSubmitting(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("vidya_token") : null;

      const formattedChanges: Record<string, any> = {};
      suggestedChangesList.forEach((item) => {
        formattedChanges[item.course_code] = {
          field: item.field,
          current_val: Number(item.current_val),
          suggested_val: Number(item.suggested_val),
          reason: item.reason,
        };
      });

      const payload = {
        registration_id: activeStudent.registration_id,
        student_id: activeStudent.student_id,
        semester_number: selectedSemester,
        verification_status: status,
        comments: comments.trim() || (status === "VERIFIED_CORRECT" ? "Marksheet verified correct against raw ledger." : "Flagged for administrative review."),
        highlighted_fields: highlightedFields,
        suggested_changes: formattedChanges,
      };

      const res = await fetch("/api/v1/scrutiny/verify-student", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to submit verification audit.");
      }

      const resData = await res.json();
      showToast(
        status === "VERIFIED_CORRECT"
          ? `Marksheet verified successfully (Iteration #${resData.iteration_number})`
          : `Discrepancy flagged and suggestion queued for Admin remediation (Iteration #${resData.iteration_number})`,
        "success"
      );

      // Optimistically update status in state
      setStudentsRoster((prev) =>
        prev.map((s, idx) =>
          idx === currentIndex
            ? {
                ...s,
                scrutiny_status: resData.scrutiny_status,
                last_scrutinized_at: resData.verified_at,
                latest_verification: {
                  id: resData.verification_id,
                  status: status,
                  comments: payload.comments,
                  highlighted_fields: highlightedFields,
                  suggested_changes: formattedChanges,
                  iteration_number: resData.iteration_number,
                  verified_at: resData.verified_at,
                  is_actioned_by_admin: false,
                },
              }
            : s
        )
      );

      // Auto-advance to next student if verified
      if (status === "VERIFIED_CORRECT" && currentIndex < studentsRoster.length - 1) {
        setTimeout(() => setCurrentIndex((prev) => prev + 1), 700);
      }
    } catch (err: any) {
      showToast(err.message || "Submission failed", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter students roster for Jump-To and count
  const filteredStudents = studentsRoster.filter((stu) => {
    const matchesSearch =
      !searchFilter ||
      stu.roll_no.toLowerCase().includes(searchFilter.toLowerCase()) ||
      stu.student_name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      stu.enrollment_no.toLowerCase().includes(searchFilter.toLowerCase());

    const matchesStatus =
      statusFilter === "ALL" ||
      stu.scrutiny_status.toUpperCase() === statusFilter.toUpperCase();

    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "VERIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Verified
          </span>
        );
      case "FLAGGED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            Needs Correction
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/15 text-slate-400 border border-slate-600/30">
            <Clock className="w-3 h-3 text-slate-400" />
            Pending
          </span>
        );
    }
  };

  const getResultBadge = (result: string) => {
    const isPass = result?.toUpperCase().includes("PASS");
    return (
      <span
        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
          isPass
            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
            : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
        }`}
      >
        {result}
      </span>
    );
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Toast Alert */}
      {toastMessage && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl shadow-2xl text-xs font-semibold flex items-center gap-2 border transition-all transform animate-bounce ${
            toastMessage.type === "success"
              ? "bg-emerald-950 text-emerald-200 border-emerald-600"
              : "bg-rose-950 text-rose-200 border-rose-600"
          }`}
        >
          {toastMessage.type === "success" ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Top Command Bar */}
      <div className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-4 py-3 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
          {/* Title & Branding */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 via-blue-600 to-sky-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-white tracking-tight">Scrutiny Verification Studio</h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  INC Gazette 2022
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Dual-Pane Ledger Reconciliation & Marksheet Verification Engine
              </p>
            </div>
          </div>

          {/* Session & Semester Pickers */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700">
              <span className="text-xs text-slate-400 font-medium">Semester:</span>
              <select
                value={selectedSemester}
                onChange={(e) => setSelectedSemester(Number(e.target.value))}
                className="bg-slate-900 text-xs text-white border-0 rounded px-1.5 py-0.5 font-bold focus:ring-1 focus:ring-blue-500 outline-none cursor-pointer"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
                  <option key={sem} value={sem}>
                    Semester {sem}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700">
              <span className="text-xs text-slate-400 font-medium">Session:</span>
              <select
                value={selectedSession}
                onChange={(e) => setSelectedSession(e.target.value)}
                className="bg-slate-900 text-xs text-white border-0 rounded px-1.5 py-0.5 font-semibold focus:ring-1 focus:ring-blue-500 outline-none cursor-pointer"
              >
                <option value="All Sessions">All Sessions</option>
                <option value="JANUARY - 2026">JANUARY - 2026</option>
                <option value="JULY - 2025">JULY - 2025</option>
                <option value="JANUARY - 2025">JANUARY - 2025</option>
              </select>
            </div>

            {/* Rules Drawer Toggle Button */}
            <button
              onClick={() => setIsDrawerOpen(true)}
              className="flex items-center gap-1.5 bg-gradient-to-r from-blue-600/30 to-indigo-600/30 hover:from-blue-600/50 hover:to-indigo-600/50 text-blue-200 border border-blue-500/40 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm"
            >
              <BookOpen className="w-3.5 h-3.5 text-blue-300" />
              <span>INC Rules Drawer</span>
            </button>

            {/* Pending Remediations Direct Link for Admin / Sub-Dean */}
            {(user?.role === "Admin" || user?.role === "Sub-Dean" || user?.role === "SubDean") && (
              <a
                href="/admin/scrutiny-suggestions"
                className="flex items-center gap-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 border border-amber-500/40 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all shadow-sm"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Remediation Roster</span>
              </a>
            )}
          </div>
        </div>

        {/* Sub-bar: Student Navigation, Quick Jump, Counter */}
        <div className="max-w-7xl mx-auto mt-2 pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Candidate Index & Buttons */}
          <div className="flex items-center gap-2">
            <button
              disabled={currentIndex <= 0}
              onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800 text-slate-300 transition-colors"
              title="Previous Student (Left Arrow)"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <span className="font-mono text-slate-300 font-bold px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700">
              Student {studentsRoster.length > 0 ? currentIndex + 1 : 0} of {studentsRoster.length}
            </span>

            <button
              disabled={currentIndex >= studentsRoster.length - 1}
              onClick={() => setCurrentIndex((prev) => Math.min(studentsRoster.length - 1, prev + 1))}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800 text-slate-300 transition-colors"
              title="Next Student (Right Arrow)"
            >
              <ChevronRight className="w-4 h-4" />
            </button>

            {/* Jump To Dropdown */}
            <select
              value={currentIndex}
              onChange={(e) => setCurrentIndex(Number(e.target.value))}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-2 py-1 text-xs font-medium focus:ring-1 focus:ring-blue-500 outline-none max-w-xs"
            >
              {studentsRoster.map((stu, idx) => (
                <option key={stu.registration_id} value={idx}>
                  {idx + 1}. {stu.roll_no} - {stu.student_name} ({stu.scrutiny_status})
                </option>
              ))}
            </select>
          </div>

          {/* Filters & Status Tally */}
          <div className="flex items-center gap-2">
            {/* Search filter */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2" />
              <input
                type="text"
                placeholder="Search Roll No / Name..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="bg-slate-800/90 text-slate-200 pl-7 pr-2 py-1 rounded text-xs border border-slate-700 focus:outline-none focus:border-blue-500 w-44"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded px-2 py-1 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Statuses ({studentsRoster.length})</option>
              <option value="PENDING">
                Pending ({studentsRoster.filter((s) => s.scrutiny_status === "PENDING").length})
              </option>
              <option value="FLAGGED">
                Needs Correction ({studentsRoster.filter((s) => s.scrutiny_status === "FLAGGED").length})
              </option>
              <option value="VERIFIED">
                Verified ({studentsRoster.filter((s) => s.scrutiny_status === "VERIFIED").length})
              </option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Dual-Pane Content View */}
      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12">
          <RotateCcw className="w-8 h-8 text-blue-400 animate-spin mb-3" />
          <p className="text-sm text-slate-300">Loading semester examination context and raw datasheets...</p>
          <span className="text-xs text-slate-500 mt-1">Connecting to PostgreSQL vidya_examination_db</span>
        </div>
      ) : errorMsg ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
          <AlertTriangle className="w-10 h-10 text-rose-500 mb-3" />
          <h2 className="text-base font-bold text-white">Error Loading Scrutiny Context</h2>
          <p className="text-xs text-rose-300 mt-1 max-w-md">{errorMsg}</p>
          <button
            onClick={fetchSessionContext}
            className="mt-4 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow"
          >
            Retry Connection
          </button>
        </div>
      ) : studentsRoster.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-slate-400">
          <FileSpreadsheet className="w-10 h-10 text-slate-600 mb-2" />
          <p className="text-sm font-semibold">No registered students found for Semester {selectedSemester} ({selectedSession})</p>
          <p className="text-xs text-slate-500 mt-1">Try selecting a different semester or examination session above.</p>
        </div>
      ) : (
        <div className="flex-1 max-w-7xl w-full mx-auto p-4 flex flex-col lg:flex-row gap-4">
          {/* =========================================================================
              LEFT PANE: Raw Tabular Datasheet Grid (50% Width)
              ========================================================================= */}
          <div className="w-full lg:w-1/2 flex flex-col bg-slate-900 rounded-xl border border-slate-800 shadow-xl overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                  Raw Excel Datasheet Ledger (Sem {selectedSemester})
                </h2>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                {datasheetRows.length} Rows Ingested
              </span>
            </div>

            {/* Datasheet Table Container */}
            <div className="flex-1 overflow-x-auto overflow-y-auto max-h-[620px] scrollbar-thin scrollbar-thumb-slate-700">
              <table className="w-full text-left border-collapse text-[11px] font-mono whitespace-nowrap">
                <thead className="bg-slate-950/80 sticky top-0 z-10 border-b border-slate-800 text-slate-300 font-bold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-2 border-r border-slate-800 text-center w-10">Sl</th>
                    <th className="p-2 border-r border-slate-800">Roll No</th>
                    <th className="p-2 border-r border-slate-800">Student Name</th>
                    {incRules?.courses.map((c) => (
                      <th key={c.course_code} className="p-2 border-r border-slate-800 text-center" colSpan={3}>
                        {c.course_code}
                      </th>
                    ))}
                    <th className="p-2 border-r border-slate-800 text-right">Grand Total</th>
                    <th className="p-2 border-r border-slate-800 text-right">SGPA</th>
                    <th className="p-2 text-center">Status</th>
                  </tr>
                  <tr className="bg-slate-900/90 text-slate-400 text-[9px] border-b border-slate-800">
                    <th className="p-1 border-r border-slate-800"></th>
                    <th className="p-1 border-r border-slate-800"></th>
                    <th className="p-1 border-r border-slate-800"></th>
                    {incRules?.courses.map((c) => (
                      <React.Fragment key={`sub-${c.course_code}`}>
                        <th className="p-1 border-r border-slate-800 text-center text-amber-300/80">IA</th>
                        <th className="p-1 border-r border-slate-800 text-center text-sky-300/80">EA</th>
                        <th className="p-1 border-r border-slate-800 text-center text-white">Tot</th>
                      </React.Fragment>
                    ))}
                    <th className="p-1 border-r border-slate-800"></th>
                    <th className="p-1 border-r border-slate-800"></th>
                    <th className="p-1"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {datasheetRows.map((row, idx) => {
                    const isActive = idx === currentIndex;
                    return (
                      <tr
                        key={row.registration_id}
                        ref={isActive ? activeRowRef : null}
                        onClick={() => setCurrentIndex(idx)}
                        className={`cursor-pointer transition-colors ${
                          isActive
                            ? "bg-indigo-950/80 border-l-4 border-indigo-500 font-semibold text-white shadow-inner"
                            : "hover:bg-slate-800/50 text-slate-300"
                        }`}
                      >
                        <td className="p-2 border-r border-slate-800/60 text-center text-slate-400">{row.sl_no}</td>
                        <td className="p-2 border-r border-slate-800/60 font-bold text-indigo-300">{row.roll_no}</td>
                        <td className="p-2 border-r border-slate-800/60 font-sans truncate max-w-[130px]" title={row.student_name}>
                          {row.student_name}
                        </td>
                        {incRules?.courses.map((c) => {
                          const cm = row.courses[c.course_code];
                          return (
                            <React.Fragment key={`cell-${row.registration_id}-${c.course_code}`}>
                              <td className="p-2 border-r border-slate-800/60 text-center text-amber-300/90">
                                {cm ? cm.internal : "-"}
                              </td>
                              <td className="p-2 border-r border-slate-800/60 text-center text-sky-300/90">
                                {cm ? cm.external : "-"}
                              </td>
                              <td className="p-2 border-r border-slate-800/60 text-center font-bold text-white">
                                {cm ? cm.total : "-"}
                              </td>
                            </React.Fragment>
                          );
                        })}
                        <td className="p-2 border-r border-slate-800/60 text-right font-bold text-emerald-300">
                          {row.grand_total}
                        </td>
                        <td className="p-2 border-r border-slate-800/60 text-right font-mono font-bold text-purple-300">
                          {row.sgpa !== null ? row.sgpa.toFixed(2) : "-"}
                        </td>
                        <td className="p-2 text-center">{getStatusBadge(row.scrutiny_status)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Footer instruction */}
            <div className="px-4 py-2 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
              <span>Click any row to load into the scrutiny inspector</span>
              <span className="text-indigo-400">Selected: {activeStudent?.roll_no}</span>
            </div>
          </div>

          {/* =========================================================================
              RIGHT PANE: High-Fidelity Marksheet Preview & Interactive Cell Tagging (50% Width)
              ========================================================================= */}
          <div className="w-full lg:w-1/2 flex flex-col bg-slate-900 rounded-xl border border-slate-800 shadow-xl overflow-hidden">
            {/* Header Banner */}
            <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-indigo-400" />
                <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                  Live Marksheet Inspection & Cell Tagging
                </h2>
              </div>
              <div className="flex items-center gap-2">
                {activeStudent && getStatusBadge(activeStudent.scrutiny_status)}
                {activeStudent?.latest_verification && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    Iter #{activeStudent.latest_verification.iteration_number}
                  </span>
                )}
              </div>
            </div>

            {/* Scrollable Inspector Body */}
            <div className="flex-1 overflow-y-auto max-h-[620px] p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700">
              {activeStudent && (
                <>
                  {/* Candidate Identity Card */}
                  <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800 flex flex-wrap justify-between items-center gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-white">{activeStudent.student_name}</h3>
                        <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                          {activeStudent.roll_no}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        F/N: {activeStudent.father_name} | Enroll: {activeStudent.enrollment_no}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-[11px] font-semibold text-slate-300 block">
                        Sem {activeStudent.semester_number} ({activeStudent.exam_month_year})
                      </span>
                      <div className="mt-1">{getResultBadge(activeStudent.result_status)}</div>
                    </div>
                  </div>

                  {/* Marksheet Table with Clickable Cell Highlights */}
                  <div className="overflow-x-auto border border-slate-800 rounded-lg">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-950 text-slate-300 font-semibold border-b border-slate-800 text-[11px]">
                        <tr>
                          <th className="p-2 border-r border-slate-800">Course Code & Title</th>
                          <th className="p-2 border-r border-slate-800 text-center">IA (25)</th>
                          <th className="p-2 border-r border-slate-800 text-center">EA (75)</th>
                          <th className="p-2 border-r border-slate-800 text-center">Total (100)</th>
                          <th className="p-2 border-r border-slate-800 text-center">Grade</th>
                          <th className="p-2 text-center">Result</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {incRules?.courses.map((c) => {
                          const cm = activeDatasheetRow?.courses[c.course_code];
                          const internalKey = `course_${c.course_code}_internal`;
                          const externalKey = `course_${c.course_code}_external`;
                          const totalKey = `course_${c.course_code}_total`;

                          const isInternalHighlighted = highlightedFields.includes(internalKey);
                          const isExternalHighlighted = highlightedFields.includes(externalKey);
                          const isTotalHighlighted = highlightedFields.includes(totalKey);

                          return (
                            <tr key={c.course_code} className="hover:bg-slate-800/30">
                              <td className="p-2 border-r border-slate-800 font-sans">
                                <div className="font-bold text-white">{c.course_code}</div>
                                <div className="text-[10px] text-slate-400 truncate max-w-[200px]" title={c.title}>
                                  {c.title}
                                </div>
                                {c.is_college_exam && (
                                  <span className="text-[9px] text-amber-400 bg-amber-950/60 px-1 py-0.2 rounded border border-amber-800/50 mt-0.5 inline-block">
                                    College Exam (Min 40%)
                                  </span>
                                )}
                              </td>

                              {/* Internal Mark Cell - Clickable */}
                              <td
                                onClick={() => toggleHighlight(internalKey, c.course_code, "internal", cm?.internal)}
                                title="Click to highlight discrepancy / suggest correction"
                                className={`p-2 border-r border-slate-800 text-center cursor-pointer transition-all ${
                                  isInternalHighlighted
                                    ? "bg-rose-950/90 text-rose-300 ring-2 ring-rose-500 font-bold"
                                    : "text-amber-300 hover:bg-slate-800"
                                }`}
                              >
                                {cm ? cm.internal : "-"}
                              </td>

                              {/* External Mark Cell - Clickable */}
                              <td
                                onClick={() => toggleHighlight(externalKey, c.course_code, "external", cm?.external)}
                                title="Click to highlight discrepancy / suggest correction"
                                className={`p-2 border-r border-slate-800 text-center cursor-pointer transition-all ${
                                  isExternalHighlighted
                                    ? "bg-rose-950/90 text-rose-300 ring-2 ring-rose-500 font-bold"
                                    : "text-sky-300 hover:bg-slate-800"
                                }`}
                              >
                                {cm ? cm.external : "-"}
                                {cm && (cm.external_a !== null || cm.external_b !== null) && (
                                  <div className="text-[9px] text-slate-400 font-sans">
                                    {cm.external_a !== null && `A:${cm.external_a} `}
                                    {cm.external_b !== null && `B:${cm.external_b}`}
                                  </div>
                                )}
                              </td>

                              {/* Total Mark Cell - Clickable */}
                              <td
                                onClick={() => toggleHighlight(totalKey, c.course_code, "total", cm?.total)}
                                title="Click to highlight discrepancy"
                                className={`p-2 border-r border-slate-800 text-center font-bold cursor-pointer transition-all ${
                                  isTotalHighlighted
                                    ? "bg-rose-950/90 text-rose-300 ring-2 ring-rose-500"
                                    : "text-white hover:bg-slate-800"
                                }`}
                              >
                                {cm ? cm.total : "-"}
                              </td>

                              {/* Grade */}
                              <td className="p-2 border-r border-slate-800 text-center font-bold text-purple-300">
                                {cm?.grade || "-"}
                              </td>

                              {/* Pass/Fail Result */}
                              <td className="p-2 text-center">
                                <span
                                  className={`text-[10px] font-bold ${
                                    cm?.result === "PASS" ? "text-emerald-400" : "text-rose-400"
                                  }`}
                                >
                                  {cm?.result || "-"}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Computed Institutional Metrics Card */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 bg-slate-950/90 p-3 rounded-lg border border-slate-800">
                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Grand Total</span>
                      <div className="text-sm font-bold text-white font-mono mt-0.5">
                        {activeStudent.grand_total_obtained} / {activeStudent.grand_total_max}
                      </div>
                    </div>

                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Percentage</span>
                      <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">
                        {activeStudent.percentage.toFixed(2)}%
                      </div>
                    </div>

                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">SGPA (INC Divisor)</span>
                      <div className="text-sm font-bold text-indigo-400 font-mono mt-0.5">
                        {activeStudent.sgpa !== null ? activeStudent.sgpa.toFixed(2) : "0.00"}
                      </div>
                      <span className="text-[9px] text-slate-500 font-mono">
                        Divisor: {incRules?.sgpa_divisor_credits} Credits
                      </span>
                    </div>

                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Verification</span>
                      <div className="text-xs font-bold text-slate-200 mt-1">
                        {getStatusBadge(activeStudent.scrutiny_status)}
                      </div>
                    </div>
                  </div>

                  {/* Highlighted Discrepancy Chips */}
                  {highlightedFields.length > 0 && (
                    <div className="bg-rose-950/30 p-2.5 rounded-lg border border-rose-900/50">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] font-bold text-rose-300 flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                          Tagged Cells for Audit ({highlightedFields.length}):
                        </span>
                        <button
                          onClick={() => setHighlightedFields([])}
                          className="text-[10px] text-rose-400 hover:text-rose-200 underline"
                        >
                          Clear All Tags
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {highlightedFields.map((k) => (
                          <span
                            key={k}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-900/60 text-rose-200 border border-rose-700/60 flex items-center gap-1"
                          >
                            <span>{k}</span>
                            <X
                              className="w-3 h-3 cursor-pointer hover:text-white"
                              onClick={() => setHighlightedFields((prev) => prev.filter((item) => item !== k))}
                            />
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggestion List & Form */}
                  <div className="bg-slate-950/80 p-3 rounded-lg border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        Correction Suggestions Roster
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {suggestedChangesList.length} Proposed Changes
                      </span>
                    </div>

                    {/* Queued Suggestions */}
                    {suggestedChangesList.length > 0 && (
                      <div className="space-y-1.5">
                        {suggestedChangesList.map((sc, sIdx) => (
                          <div
                            key={sIdx}
                            className="flex items-center justify-between gap-2 p-2 rounded bg-slate-900 border border-slate-700/70 text-xs"
                          >
                            <div>
                              <span className="font-bold text-indigo-300">{sc.course_code}</span>{" "}
                              <span className="text-slate-400 font-mono">[{sc.field}]</span>:{" "}
                              <span className="line-through text-slate-400">{sc.current_val}</span> →{" "}
                              <span className="font-bold text-emerald-400">{sc.suggested_val}</span>
                              <div className="text-[10px] text-slate-400 italic mt-0.5">
                                Reason: {sc.reason}
                              </div>
                            </div>
                            <button
                              onClick={() => handleRemoveSuggestedChange(sIdx)}
                              className="text-slate-500 hover:text-rose-400 p-1"
                              title="Delete suggestion"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Add Suggestion Builder Box */}
                    <div className="bg-slate-900/90 p-2.5 rounded border border-slate-700/60 space-y-2">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        + Propose Score Rectification
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        <select
                          value={builderCourse}
                          onChange={(e) => setBuilderCourse(e.target.value)}
                          className="bg-slate-800 text-xs text-white border border-slate-700 rounded px-2 py-1 outline-none"
                        >
                          <option value="">Select Course...</option>
                          {incRules?.courses.map((c) => (
                            <option key={c.course_code} value={c.course_code}>
                              {c.course_code}
                            </option>
                          ))}
                        </select>

                        <select
                          value={builderField}
                          onChange={(e) => setBuilderField(e.target.value)}
                          className="bg-slate-800 text-xs text-white border border-slate-700 rounded px-2 py-1 outline-none"
                        >
                          <option value="internal">Internal Assessment (IA)</option>
                          <option value="external">External Total (EA)</option>
                          <option value="external_part_a">External Part A</option>
                          <option value="external_part_b">External Part B</option>
                          <option value="total">Course Total</option>
                        </select>

                        <input
                          type="number"
                          placeholder="Suggested Mark"
                          value={builderSuggestedVal}
                          onChange={(e) => setBuilderSuggestedVal(e.target.value)}
                          className="bg-slate-800 text-xs text-white border border-slate-700 rounded px-2 py-1 outline-none font-mono"
                        />
                      </div>

                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Discrepancy Reason (e.g., Retotaling mismatch in Part B)"
                          value={builderReason}
                          onChange={(e) => setBuilderReason(e.target.value)}
                          className="flex-1 bg-slate-800 text-xs text-white border border-slate-700 rounded px-2 py-1 outline-none"
                        />
                        <button
                          type="button"
                          onClick={handleAddSuggestedChange}
                          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1 shadow-sm"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>Add</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Bottom Verification Dock */}
            <div className="bg-slate-950 border-t border-slate-800 p-3 space-y-2.5">
              <textarea
                placeholder="Scrutiny Officer Observation & Register Audit Remarks..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={2}
                className="w-full bg-slate-900 text-slate-200 text-xs rounded-lg border border-slate-700 p-2 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
              />

              <div className="flex items-center justify-between gap-2">
                <div className="text-[10px] text-slate-500">
                  Officer: <strong className="text-slate-300">{user?.full_name || user?.username}</strong> ({user?.role})
                </div>

                <div className="flex items-center gap-2">
                  <button
                    disabled={isSubmitting || !activeStudent}
                    onClick={() => handleVerifySubmit("NEEDS_CORRECTION")}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white transition-all shadow-md shadow-rose-600/30 disabled:opacity-50"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Flag Discrepancy & Save</span>
                  </button>

                  <button
                    disabled={isSubmitting || !activeStudent}
                    onClick={() => handleVerifySubmit("VERIFIED_CORRECT")}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-600/30 disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Verify Marksheet (Record Timestamp)</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          SLIDING DRAWER: INC Gazette Corrigendum 2022 Rules
          ========================================================================= */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity"
            onClick={() => setIsDrawerOpen(false)}
          />

          {/* Drawer Panel */}
          <div className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full z-10 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-white">INC Gazette Rules Drawer</h3>
              </div>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs scrollbar-thin scrollbar-thumb-slate-700">
              {/* Program Regulations Card */}
              <div className="bg-slate-950/90 p-3 rounded-lg border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="font-semibold">Curriculum Framework:</span>
                  <span className="font-bold text-blue-400">INC Gazette Corrigendum 2022</span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="font-semibold">Cumulative Total Credits:</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {incRules?.program_total_credits || 151.0} Credits
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="font-semibold">Sem {selectedSemester} SGPA Divisor:</span>
                  <span className="font-mono font-bold text-purple-400">
                    {incRules?.sgpa_divisor_credits} Credits
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="font-semibold">Semester Grand Total Marks:</span>
                  <span className="font-mono font-bold text-white">
                    {incRules?.grand_total_marks} Marks
                  </span>
                </div>
                {selectedSemester === 1 && (
                  <p className="text-[11px] text-amber-300 bg-amber-950/40 p-2 rounded border border-amber-900/60 mt-1">
                    <strong>Note:</strong> Communicative English (2 Credits) is evaluated internally as a College Exam. Per INC Gazette, its credits are excluded from the SGPA divisor (Divisor = 12 Credits, not 14).
                  </p>
                )}
              </div>

              {/* Course Splits & Pass Thresholds */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Course Subcomponents & Passing Criteria
                </h4>
                {incRules?.courses.map((c) => (
                  <div key={c.course_code} className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{c.course_code}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {c.credits} Credits ({c.credit_breakdown || "N/A"})
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{c.title}</p>

                    <div className="grid grid-cols-2 gap-2 text-[10px] font-mono pt-1 text-slate-300">
                      <div>IA Min/Max: {c.ia_min_pass} / {c.ia_max}</div>
                      <div>EA Min/Max: {c.ea_min_pass} / {c.ea_max}</div>
                      <div>Passing Threshold: {c.passing_threshold_percent}%</div>
                      <div>Include in SGPA: {c.include_in_sgpa ? "Yes" : "No"}</div>
                    </div>

                    {c.subcomponents && c.subcomponents.length > 0 && (
                      <div className="mt-1 pt-1 border-t border-slate-800/80">
                        <span className="text-[10px] text-slate-400 block mb-0.5 font-semibold">
                          Paper Component Split:
                        </span>
                        <div className="space-y-0.5">
                          {c.subcomponents.map((sub, sIdx) => (
                            <div key={sIdx} className="flex justify-between text-[10px] text-slate-300">
                              <span>{sub.name}:</span>
                              <span className="font-mono text-sky-400">Max {sub.max_marks} (Min {sub.min_pass_marks || "N/A"})</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* 10-Point Grading Scale Table */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  10-Point Relative Grading Scale
                </h4>
                <div className="overflow-x-auto border border-slate-800 rounded-lg">
                  <table className="w-full text-left text-[11px] font-mono">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="p-1.5">Grade</th>
                        <th className="p-1.5 text-center">GP</th>
                        <th className="p-1.5">Percentage Range</th>
                        <th className="p-1.5">Descriptor</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                      {incRules?.grading_scale.map((gs) => (
                        <tr key={gs.grade} className="hover:bg-slate-800/30">
                          <td className="p-1.5 font-bold text-purple-300">{gs.grade}</td>
                          <td className="p-1.5 text-center font-bold text-white">{gs.grade_point}</td>
                          <td className="p-1.5 text-slate-300">{gs.range}</td>
                          <td className="p-1.5 text-slate-400">{gs.desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-3 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-400 text-center">
              Indian Nursing Council & SGPGIMS Lucknow Regulations
            </div>
          </div>
        </div>
      )}

      {/* Footer Branding Strip */}
      <footer className="mt-auto bg-slate-950 border-t border-slate-800/80 px-4 py-2.5 text-center text-xs text-slate-500">
        VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari) • Institutional Scrutiny Studio Compliant with INC Gazette Corrigendum 2022
      </footer>
    </div>
  );
};
