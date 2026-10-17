"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  X,
  Download,
  AlertTriangle,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  RefreshCw,
  FileSpreadsheet,
} from "lucide-react";

export interface BacklogCandidate {
  backlog_id: number;
  student_id: number;
  roll_no: string;
  enrollment_no: string;
  student_name: string;
  father_name: string;
  course_id: number;
  course_code: string;
  course_title: string;
  semester_number: number;
  failed_component: string;
  deficit_marks: number;
  attempt_count: number;
  backlog_status: string;
  failed_exam_month_year: string;
  forthcoming_exam_month_year: string;
  created_at?: string;
  cleared_at?: string;
}

interface BacklogRosterModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialSemester?: number | null;
}

export const BacklogRosterModal: React.FC<BacklogRosterModalProps> = ({
  isOpen,
  onClose,
  initialSemester = null,
}) => {
  const [roster, setRoster] = useState<BacklogCandidate[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedSemester, setSelectedSemester] = useState<number | null>(initialSemester);
  const [selectedStatus, setSelectedStatus] = useState<string>("ACTIVE");

  const fetchRoster = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedSemester !== null) {
        params.append("semester", selectedSemester.toString());
      }
      if (selectedStatus) {
        params.append("status", selectedStatus);
      }

      const res = await fetch(`/api/v1/analytics/backlog-roster?${params.toString()}`, {
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setRoster(data.roster || []);
    } catch (err: any) {
      setError(err.message || "Failed to load backlog roster.");
    } finally {
      setLoading(false);
    }
  }, [selectedSemester, selectedStatus]);

  useEffect(() => {
    if (isOpen) {
      setSelectedSemester(initialSemester);
      fetchRoster();
    }
  }, [isOpen, initialSemester, fetchRoster]);

  if (!isOpen) return null;

  // Filtered rows based on search term
  const filteredRoster = roster.filter((item) => {
    const q = searchTerm.toLowerCase().trim();
    if (!q) return true;
    return (
      item.roll_no.toLowerCase().includes(q) ||
      item.student_name.toLowerCase().includes(q) ||
      item.enrollment_no.toLowerCase().includes(q) ||
      item.course_code.toLowerCase().includes(q) ||
      item.course_title.toLowerCase().includes(q) ||
      (item.failed_component && item.failed_component.toLowerCase().includes(q))
    );
  });

  const exportToCSV = () => {
    if (!filteredRoster.length) return;

    const headers = [
      "Sl No",
      "Roll No",
      "Student Name",
      "Father Name",
      "Enrollment No",
      "Semester",
      "Course Code",
      "Course Title",
      "Failed Component",
      "Deficit Marks",
      "Attempt Count",
      "Failed Sitting",
      "Forthcoming Sitting",
      "Status",
    ];

    const rows = filteredRoster.map((item, idx) => [
      idx + 1,
      `"${item.roll_no}"`,
      `"${item.student_name}"`,
      `"${item.father_name || ""}"`,
      `"${item.enrollment_no}"`,
      item.semester_number,
      `"${item.course_code}"`,
      `"${item.course_title}"`,
      `"${item.failed_component}"`,
      item.deficit_marks,
      item.attempt_count,
      `"${item.failed_exam_month_year}"`,
      `"${item.forthcoming_exam_month_year}"`,
      item.backlog_status,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `Backlog_Roster_Sem${selectedSemester || "All"}_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between gap-4 bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-rose-500/20 text-rose-400 rounded-2xl border border-rose-500/30">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Re-appear Candidate Backlog Engine & Roster
                </h2>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/30">
                  {filteredRoster.length} Records
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Automated re-examination tagging compliant with Indian Nursing Council (INC) regulations.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={exportToCSV}
              disabled={filteredRoster.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-all shadow-sm"
              title="Download CSV Roster"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={fetchRoster}
              disabled={loading}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-all"
              title="Refresh Roster"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 bg-slate-800 hover:bg-rose-500/20 hover:text-rose-400 text-slate-400 rounded-xl border border-slate-700 transition-all"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-950/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-[240px]">
            <div className="relative w-full max-w-sm">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search by Roll No, Name, Subject..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-xl pl-9 pr-3 py-2 focus:outline-none focus:border-rose-500 transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              <span>Semester:</span>
              <select
                value={selectedSemester === null ? "" : selectedSemester}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedSemester(val === "" ? null : parseInt(val, 10));
                }}
                className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none focus:border-rose-500"
              >
                <option value="">All Semesters (1-8)</option>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <span>Status:</span>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none focus:border-rose-500"
              >
                <option value="ACTIVE">Active Backlogs Only</option>
                <option value="CLEARED">Cleared Backlogs Only</option>
                <option value="ALL">All Records</option>
              </select>
            </div>
          </div>
        </div>

        {/* Content Table */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {loading ? (
            <div className="h-64 flex flex-col items-center justify-center gap-3 text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin text-rose-400" />
              <p className="text-xs">Loading institutional backlog roster...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs rounded-2xl flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          ) : filteredRoster.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center gap-2 text-slate-500">
              <CheckCircle2 className="w-8 h-8 text-emerald-400/60" />
              <p className="text-sm font-semibold text-slate-300">No Backlog Candidates Found</p>
              <p className="text-xs text-slate-500">
                {searchTerm
                  ? "No matching records found for the current search filter."
                  : "All students have satisfied passing criteria for the selected criteria."}
              </p>
            </div>
          ) : (
            <div className="border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] font-bold tracking-wider">
                  <tr>
                    <th className="py-3 px-3">Roll No & Name</th>
                    <th className="py-3 px-3">Sem</th>
                    <th className="py-3 px-3">Subject / Paper</th>
                    <th className="py-3 px-3">Failed Component</th>
                    <th className="py-3 px-3 text-right">Deficit</th>
                    <th className="py-3 px-3 text-center">Attempt</th>
                    <th className="py-3 px-3">Forthcoming Sitting</th>
                    <th className="py-3 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/60 font-medium">
                  {filteredRoster.map((item) => (
                    <tr
                      key={item.backlog_id}
                      className="hover:bg-slate-800/40 transition-colors"
                    >
                      <td className="py-3 px-3">
                        <div className="font-mono font-bold text-white text-xs">
                          {item.roll_no}
                        </div>
                        <div className="text-[11px] text-slate-300 truncate max-w-[170px]" title={item.student_name}>
                          {item.student_name}
                        </div>
                      </td>

                      <td className="py-3 px-3 font-mono text-slate-400">
                        <span className="px-2 py-0.5 bg-slate-800 rounded font-semibold text-slate-300">
                          Sem {item.semester_number}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        <div className="font-mono font-semibold text-rose-300">
                          {item.course_code}
                        </div>
                        <div
                          className="text-[11px] text-slate-400 truncate max-w-[200px]"
                          title={item.course_title}
                        >
                          {item.course_title}
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          {item.failed_component}
                        </span>
                      </td>

                      <td className="py-3 px-3 text-right font-mono font-bold">
                        {item.deficit_marks > 0 ? (
                          <span className="text-rose-400">-{item.deficit_marks.toFixed(1)}</span>
                        ) : (
                          <span className="text-slate-400">0.0</span>
                        )}
                      </td>

                      <td className="py-3 px-3 text-center">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          #{item.attempt_count}
                        </span>
                      </td>

                      <td className="py-3 px-3 font-mono text-emerald-400 font-semibold text-xs">
                        {item.forthcoming_exam_month_year}
                      </td>

                      <td className="py-3 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wide border ${
                            item.backlog_status === "ACTIVE"
                              ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                              : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                          }`}
                        >
                          {item.backlog_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-300">
              VidyaMarksheet
            </span>
            <span>• Developed at VidyaLabs | Priyanka Kumari</span>
          </div>
          <div>
            Showing <strong className="text-white font-mono">{filteredRoster.length}</strong> of{" "}
            <span className="font-mono">{roster.length}</span> candidates
          </div>
        </div>
      </div>
    </div>
  );
};
