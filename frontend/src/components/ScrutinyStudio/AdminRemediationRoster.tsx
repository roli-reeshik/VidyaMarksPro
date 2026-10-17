"use client";

import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  RotateCcw,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  UserCheck,
  Clock,
  Sparkles,
  X,
  FileCheck,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

interface SuggestedChange {
  field?: string;
  current_val?: number;
  suggested_val?: number;
  reason?: string;
}

interface PendingRemediationItem {
  verification_id: number;
  registration_id: number;
  student_id: number;
  roll_no: string;
  enrollment_no: string;
  student_name: string;
  semester_number: number;
  exam_session: string;
  scrutiny_username: string;
  iteration_number: number;
  comments?: string | null;
  highlighted_fields?: string[];
  suggested_changes?: Record<string, SuggestedChange>;
  verified_at?: string | null;
  current_sgpa?: number | null;
  current_total?: number;
}

export const AdminRemediationRoster: React.FC = () => {
  const { user } = useAuth();
  const [remediations, setRemediations] = useState<PendingRemediationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [semesterFilter, setSemesterFilter] = useState<string>("ALL");

  // Dismiss Modal State
  const [dismissTarget, setDismissTarget] = useState<PendingRemediationItem | null>(null);
  const [dismissNotes, setDismissNotes] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Toast Notification State
  const [toastMessage, setToastMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const fetchPendingRemediations = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch("/api/v1/scrutiny/pending-remediations", {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      setRemediations(data.remediations || []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load pending remediations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingRemediations();
  }, []);

  const showToast = (text: string, type: "success" | "error") => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Apply Remediation (Admin only)
  const handleApply = async (item: PendingRemediationItem) => {
    if (user?.role !== "Admin") {
      showToast("Only System Administrators can apply mark changes.", "error");
      return;
    }

    if (!confirm(`Apply Scrutiny Suggestion #${item.verification_id} for ${item.student_name} (${item.roll_no})? Marks will be updated and SGPA will be recalculated.`)) {
      return;
    }

    setIsProcessing(true);
    try {
      const res = await fetch(`/api/v1/scrutiny/apply-remediation/${item.verification_id}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to apply remediation.");
      }

      const data = await res.json();
      showToast(
        `Remediation #${item.verification_id} applied! New SGPA: ${data.updated_registration?.sgpa?.toFixed(2) || "N/A"}, Total: ${data.updated_registration?.grand_total || "N/A"}`,
        "success"
      );

      // Remove from list
      setRemediations((prev) => prev.filter((r) => r.verification_id !== item.verification_id));
    } catch (err: any) {
      showToast(err.message || "Error applying remediation", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  // Dismiss Remediation (Admin only)
  const handleDismissSubmit = async () => {
    if (!dismissTarget) return;

    setIsProcessing(true);
    try {
      const res = await fetch(`/api/v1/scrutiny/dismiss-remediation/${dismissTarget.verification_id}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          admin_notes: dismissNotes.trim() || "Dismissed by Administrator without changes.",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to dismiss remediation.");
      }

      showToast(`Scrutiny Suggestion #${dismissTarget.verification_id} dismissed with admin notes recorded.`, "success");
      setRemediations((prev) => prev.filter((r) => r.verification_id !== dismissTarget.verification_id));
      setDismissTarget(null);
      setDismissNotes("");
    } catch (err: any) {
      showToast(err.message || "Error dismissing suggestion", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  // Filtered List
  const filteredList = remediations.filter((item) => {
    const matchesSearch =
      !searchQuery ||
      item.roll_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.scrutiny_username.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSemester =
      semesterFilter === "ALL" || String(item.semester_number) === semesterFilter;

    return matchesSearch && matchesSemester;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-6 lg:p-8">
      {/* Toast Alert */}
      {toastMessage && (
        <div
          className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl shadow-2xl text-xs font-semibold flex items-center gap-2 border transition-all ${
            toastMessage.type === "success"
              ? "bg-emerald-950 text-emerald-200 border-emerald-600"
              : "bg-rose-950 text-rose-200 border-rose-600"
          }`}
        >
          {toastMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          )}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Main Container */}
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/90 p-5 rounded-2xl border border-slate-800 shadow-xl">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-amber-600 to-rose-600 flex items-center justify-center text-white shadow-lg shadow-amber-600/20">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                  Admin Remediation Resolution Roster
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">
                  {remediations.length} Pending
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Review and execute Scrutiny Officer mark correction recommendations with one-click recalculation.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchPendingRemediations}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors shadow-sm"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>

            <a
              href="/scrutiny"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors shadow-md shadow-indigo-600/20"
            >
              <span>Open Scrutiny Studio</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/70 p-3 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search Roll No, Candidate, or Scrutiny Officer..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-800/90 text-slate-200 pl-9 pr-3 py-1.5 rounded-lg text-xs border border-slate-700 focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Filter Semester:</span>
            <select
              value={semesterFilter}
              onChange={(e) => setSemesterFilter(e.target.value)}
              className="bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Semesters</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={String(s)}>
                  Semester {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* List of Pending Remediations */}
        {loading ? (
          <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800">
            <RotateCcw className="w-8 h-8 text-amber-400 animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-300 font-semibold">Loading un-actioned scrutiny recommendations...</p>
          </div>
        ) : errorMsg ? (
          <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-rose-900/40">
            <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white">Failed to Load Remediation Roster</h3>
            <p className="text-xs text-rose-300 mt-1">{errorMsg}</p>
          </div>
        ) : filteredList.length === 0 ? (
          <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800/80 space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
              <Check className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">All Scrutiny Items Resolved</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              No pending student discrepancies await administrative remediation. All marksheet reviews are up to date!
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredList.map((item) => {
              const changesList = Object.entries(item.suggested_changes || {});
              return (
                <div
                  key={item.verification_id}
                  className="bg-slate-900 rounded-xl border border-slate-800 p-5 shadow-lg space-y-4 hover:border-slate-700 transition-all"
                >
                  {/* Top Candidate & Scrutiny Metadata */}
                  <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800/80 pb-3">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="text-base font-bold text-white">{item.student_name}</span>
                        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                          {item.roll_no}
                        </span>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                          Sem {item.semester_number}
                        </span>
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-950/70 text-rose-300 border border-rose-800">
                          Iteration #{item.iteration_number}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">
                        Enrollment: {item.enrollment_no} | Exam Session: {item.exam_session}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="flex items-center gap-1.5 text-xs text-slate-300">
                        <Clock className="w-3.5 h-3.5 text-amber-400" />
                        <span>Submitted by <strong className="text-white">{item.scrutiny_username}</strong></span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                        {item.verified_at ? new Date(item.verified_at).toLocaleString() : "Recently"}
                      </span>
                    </div>
                  </div>

                  {/* Scrutiny Remarks */}
                  {item.comments && (
                    <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 text-xs">
                      <span className="text-slate-400 font-semibold block mb-0.5">Scrutiny Officer Remarks:</span>
                      <p className="text-slate-200 italic">&ldquo;{item.comments}&rdquo;</p>
                    </div>
                  )}

                  {/* Suggested Changes Diff Viewer */}
                  <div>
                    <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">
                      Proposed Mark Rectifications ({changesList.length}):
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {changesList.map(([courseCode, sc]) => {
                        const current = sc.current_val ?? 0;
                        const suggested = sc.suggested_val ?? 0;
                        const diff = Number(suggested) - Number(current);
                        return (
                          <div
                            key={courseCode}
                            className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 flex flex-col justify-between gap-2"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-indigo-300 text-xs">{courseCode}</span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                                Component: {sc.field || "marks"}
                              </span>
                            </div>

                            {/* Mark Diff Representation */}
                            <div className="flex items-center gap-2 text-xs font-mono">
                              <span className="text-slate-400">Current: <strong className="text-slate-300 line-through">{current}</strong></span>
                              <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                              <span className="text-emerald-400 font-bold">Suggested: {suggested}</span>
                              <span
                                className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                                  diff >= 0 ? "bg-emerald-950 text-emerald-300" : "bg-rose-950 text-rose-300"
                                }`}
                              >
                                {diff >= 0 ? `+${diff}` : diff}
                              </span>
                            </div>

                            {sc.reason && (
                              <p className="text-[11px] text-slate-400 italic">
                                Reason: {sc.reason}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Action Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
                    <div className="text-xs text-slate-400 font-mono">
                      Current SGPA: <strong className="text-purple-300">{item.current_sgpa?.toFixed(2) || "N/A"}</strong> | Current Total: <strong className="text-white">{item.current_total}</strong>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        disabled={isProcessing}
                        onClick={() => {
                          setDismissTarget(item);
                          setDismissNotes("");
                        }}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-colors disabled:opacity-50"
                      >
                        Dismiss Suggestion
                      </button>

                      {user?.role === "Admin" ? (
                        <button
                          disabled={isProcessing}
                          onClick={() => handleApply(item)}
                          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-600/30 disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Apply Change & Recalculate</span>
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-500 italic">
                          Admin login required to apply changes
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Dismissal Reason Modal */}
      {dismissTarget && (
        <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setDismissTarget(null)}
          />
          <div className="relative bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4 z-10">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">Dismiss Scrutiny Suggestion</h3>
              <button
                onClick={() => setDismissTarget(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Provide justification for dismissing Suggestion #{dismissTarget.verification_id} for candidate{" "}
              <strong>{dismissTarget.student_name}</strong> ({dismissTarget.roll_no}). Marks will not be modified.
            </p>

            <textarea
              rows={3}
              placeholder="e.g., Cross-verified with Chief Examiner and physical ledger. Original score verified correct."
              value={dismissNotes}
              onChange={(e) => setDismissNotes(e.target.value)}
              className="w-full bg-slate-950 text-slate-200 text-xs rounded-lg border border-slate-700 p-2.5 focus:ring-1 focus:ring-amber-500 outline-none resize-none"
            />

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDismissTarget(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isProcessing}
                onClick={handleDismissSubmit}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-md shadow-rose-600/30 disabled:opacity-50"
              >
                Confirm Dismissal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer Branding Strip */}
      <footer className="mt-12 text-center text-xs text-slate-500">
        VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari) • Institutional Scrutiny Studio Compliant with INC Gazette Corrigendum 2022
      </footer>
    </div>
  );
};
