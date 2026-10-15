"use client";

import React, { useState, useEffect } from "react";
import {
  History,
  X,
  Search,
  Filter,
  UserCheck,
  ShieldCheck,
  AlertCircle,
  FileText,
  Clock,
  Download,
  RefreshCw,
  Lock,
  Unlock,
  CheckCircle2
} from "lucide-react";
import { AuditLogEntry } from "../types/marksheet";

interface VisualAuditLogModalProps {
  isOpen: boolean;
  onClose: () => void;
  rollNo: string | null;
  studentName?: string;
  enrollmentNo?: string;
  semesterNumber?: number;
}

export const VisualAuditLogModal: React.FC<VisualAuditLogModalProps> = ({
  isOpen,
  onClose,
  rollNo,
  studentName = "Candidate",
  enrollmentNo = "",
  semesterNumber = 1,
}) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [fieldFilter, setFieldFilter] = useState<string>("ALL");

  useEffect(() => {
    if (!isOpen || !rollNo) return;

    const fetchAuditHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const cleanRoll = rollNo.trim();
        // Try workflow audit endpoint first, fallback to standard audit trail
        let res = await fetch(`http://127.0.0.1:8000/api/v1/workflow/audit-history/${encodeURIComponent(cleanRoll)}`);
        if (!res.ok) {
          res = await fetch(`http://127.0.0.1:8000/api/v1/audit-trail/${encodeURIComponent(cleanRoll)}`);
        }

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Failed to fetch audit history for Roll No ${cleanRoll}`);
        }

        const data = await res.json();
        // Normalize array from either structure
        const historyItems: AuditLogEntry[] = Array.isArray(data)
          ? data
          : data.history || [];
        setLogs(historyItems);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
        setLogs([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAuditHistory();
  }, [isOpen, rollNo]);

  if (!isOpen) return null;

  // Filter logs by search query and field type
  const filteredLogs = logs.filter((l) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      (l.field_name && l.field_name.toLowerCase().includes(q)) ||
      (l.modified_by && l.modified_by.toLowerCase().includes(q)) ||
      (l.change_reason && l.change_reason.toLowerCase().includes(q)) ||
      (l.old_value && l.old_value.toLowerCase().includes(q)) ||
      (l.new_value && l.new_value.toLowerCase().includes(q));

    const matchesField =
      fieldFilter === "ALL" ||
      (fieldFilter === "WORKFLOW" && l.field_name === "workflow_status") ||
      (fieldFilter === "MARKS" && l.field_name.includes("marks") || l.field_name.includes("obtained")) ||
      (fieldFilter === "DEMOGRAPHICS" && (l.field_name === "student_name" || l.field_name === "father_name" || l.field_name === "student_created"));

    return matchesSearch && matchesField;
  });

  const formatTimestamp = (ts: string | null) => {
    if (!ts) return "—";
    try {
      const d = new Date(ts);
      return d.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      });
    } catch {
      return ts;
    }
  };

  const getRoleBadgeStyle = (operator: string) => {
    const lower = (operator || "").toLowerCase();
    if (lower.includes("admin") || lower.includes("sub-dean") || lower.includes("dean")) {
      return "bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200 dark:border-purple-800";
    }
    if (lower.includes("scrutiny") || lower.includes("committee") || lower.includes("verified")) {
      return "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-800";
    }
    if (lower.includes("system")) {
      return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700";
    }
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";
  };

  const handleExportJson = () => {
    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Audit_History_${rollNo}_Sem${semesterNumber}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white p-5 border-b border-slate-800 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-blue-600/30 rounded-xl border border-blue-500/30 text-blue-300">
                <History className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Field-Level Examination Audit History
              </h2>
              <span className="text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-2.5 py-0.5 rounded-full">
                PostgreSQL Immutable Ledger
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-300 pt-1">
              <span className="font-semibold text-white">{studentName}</span>
              <span>•</span>
              <span className="font-mono bg-white/10 px-2 py-0.5 rounded border border-white/10">
                Roll No: {rollNo}
              </span>
              {enrollmentNo && (
                <>
                  <span>•</span>
                  <span className="font-mono bg-white/10 px-2 py-0.5 rounded border border-white/10">
                    Enroll: {enrollmentNo}
                  </span>
                </>
              )}
              <span>•</span>
              <span>Semester: {semesterNumber}</span>
              <span>•</span>
              <span className="text-blue-300">
                Total Audit Events: {logs.length}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-xl transition-colors cursor-pointer"
            title="Close Modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="p-4 bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by field, operator, or reason..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500 font-medium">Filter:</span>
              <select
                value={fieldFilter}
                onChange={(e) => setFieldFilter(e.target.value)}
                className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1 text-slate-700 dark:text-slate-300 focus:outline-none"
              >
                <option value="ALL">All Event Types</option>
                <option value="WORKFLOW">Workflow State Machine</option>
                <option value="MARKS">Marks & Grades Alterations</option>
                <option value="DEMOGRAPHICS">Demographics / Bio</option>
              </select>
            </div>

            {logs.length > 0 && (
              <button
                onClick={handleExportJson}
                className="flex items-center gap-1.5 text-xs font-semibold bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm transition-all cursor-pointer"
                title="Export raw JSON log"
              >
                <Download className="w-3.5 h-3.5 text-blue-500" />
                <span>Export JSON</span>
              </button>
            )}
          </div>
        </div>

        {/* Modal Body / Table */}
        <div className="flex-1 overflow-y-auto p-4 select-text">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-500">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
              <span className="text-sm font-semibold">Querying PostgreSQL marks_audit_log...</span>
            </div>
          ) : error ? (
            <div className="p-6 m-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-2xl text-red-700 dark:text-red-300 text-xs flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 text-red-500 mt-0.5" />
              <div>
                <p className="font-bold">Audit Query Failed</p>
                <p className="mt-1">{error}</p>
              </div>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="py-20 text-center text-slate-400">
              <CheckCircle2 className="w-12 h-12 text-emerald-500/60 mx-auto mb-3" />
              <p className="text-sm font-bold text-slate-700 dark:text-slate-300">
                {logs.length === 0 ? "Initial Record — No Modifications Logged" : "No logs match current filter"}
              </p>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                {logs.length === 0
                  ? "This candidate record currently reflects the original verified ingested scores without any post-upload manual overrides or re-evaluations."
                  : "Try clearing search queries or selecting 'All Event Types' above."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                    <th className="py-3 px-3.5 w-36">Timestamp</th>
                    <th className="py-3 px-3.5 w-44">User / Operator</th>
                    <th className="py-3 px-3.5 w-40">Subject / Field</th>
                    <th className="py-3 px-3.5 min-w-[140px]">Old Value</th>
                    <th className="py-3 px-3.5 min-w-[140px]">New Value</th>
                    <th className="py-3 px-4 min-w-[200px]">Reason / Justification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {filteredLogs.map((log, idx) => {
                    const isWorkflow = log.field_name === "workflow_status";
                    const isUnlock = log.change_reason && log.change_reason.toLowerCase().includes("unlock");

                    return (
                      <tr
                        key={log.id || idx}
                        className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors ${
                          isUnlock ? "bg-amber-50/40 dark:bg-amber-950/10" : ""
                        }`}
                      >
                        {/* Timestamp */}
                        <td className="py-3 px-3.5 font-mono text-[11px] text-slate-600 dark:text-slate-400 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span>{formatTimestamp(log.timestamp)}</span>
                          </div>
                        </td>

                        {/* User / Operator */}
                        <td className="py-3 px-3.5">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${getRoleBadgeStyle(
                              log.modified_by
                            )}`}
                          >
                            <UserCheck className="w-3 h-3 shrink-0" />
                            <span className="truncate max-w-[140px]" title={log.modified_by}>
                              {log.modified_by || "System"}
                            </span>
                          </span>
                        </td>

                        {/* Subject / Field */}
                        <td className="py-3 px-3.5 font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
                          <div className="flex items-center gap-1.5">
                            {isWorkflow ? (
                              isUnlock ? (
                                <Unlock className="w-3.5 h-3.5 text-amber-500" />
                              ) : (
                                <Lock className="w-3.5 h-3.5 text-blue-500" />
                              )
                            ) : (
                              <FileText className="w-3.5 h-3.5 text-slate-400" />
                            )}
                            <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                              {log.field_name}
                            </span>
                          </div>
                        </td>

                        {/* Old Value */}
                        <td className="py-3 px-3.5 font-mono text-[11px]">
                          {log.old_value !== null && log.old_value !== undefined ? (
                            <span className="inline-block px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60 break-all line-through">
                              {log.old_value}
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">None (Initial)</span>
                          )}
                        </td>

                        {/* New Value */}
                        <td className="py-3 px-3.5 font-mono text-[11px]">
                          {log.new_value !== null && log.new_value !== undefined ? (
                            <span className="inline-block px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/60 break-all font-bold">
                              {log.new_value}
                            </span>
                          ) : (
                            <span className="text-slate-400 italic">—</span>
                          )}
                        </td>

                        {/* Reason / Justification */}
                        <td className="py-3 px-4 text-xs text-slate-700 dark:text-slate-300">
                          <p className={`leading-relaxed ${isUnlock ? "font-semibold text-amber-700 dark:text-amber-300" : ""}`}>
                            {log.change_reason || "Institutional update"}
                          </p>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>INC Gazette Regulation & SGPGIMS Examination Audit Standard</span>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 text-white font-semibold rounded-xl transition-all cursor-pointer"
          >
            Close Window
          </button>
        </div>

      </div>
    </div>
  );
};
