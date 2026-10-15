"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  X,
  Search,
  FileDown,
  Scale,
  RefreshCw,
  Check,
  AlertCircle
} from "lucide-react";
import { IncGazetteAuditReport, EvaluatedStudentRecord } from "../types/marksheet";

interface IncGazetteAuditModalProps {
  isOpen: boolean;
  onClose: () => void;
  students: EvaluatedStudentRecord[];
  semester?: number;
  onExportBulkZip: () => void;
  isExportingZip?: boolean;
}

export const IncGazetteAuditModal: React.FC<IncGazetteAuditModalProps> = ({
  isOpen,
  onClose,
  students,
  semester = 1,
  onExportBulkZip,
  isExportingZip = false
}) => {
  const [report, setReport] = useState<IncGazetteAuditReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterCategory, setFilterCategory] = useState<string>("ALL");

  useEffect(() => {
    if (!isOpen || students.length === 0) return;

    const runAudit = async () => {
      setIsLoading(true);
      setErrorMsg(null);
      try {
        const res = await fetch(`/api/audit/check-inc-gazette?semester=${semester}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(students)
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "INC Gazette verification failed.");
        }

        const data: IncGazetteAuditReport = await res.json();
        setReport(data);
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : "Error executing INC Gazette check.");
      } finally {
        setIsLoading(false);
      }
    };

    runAudit();
  }, [isOpen, students, semester]);

  if (!isOpen) return null;

  const filteredCandidates = (report?.candidates || []).filter((c) => {
    const matchesSearch =
      c.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.roll_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.father_name.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;
    if (filterCategory === "ALL") return true;
    if (filterCategory === "PASS") return c.status_category === "PASS";
    if (filterCategory === "GRACE") return c.status_category === "PASS_WITH_GRACE";
    if (filterCategory === "FAIL") return c.status_category === "FAIL";
    if (filterCategory === "FLAGGED") return c.status_category === "FLAGGED";
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-blue-600 text-white shadow-md shadow-blue-600/20">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  INC Gazette Official Regulatory Audit
                </h3>
                <span className="text-[11px] font-semibold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 px-2.5 py-0.5 rounded-full border border-emerald-300 dark:border-emerald-800">
                  Gazette Sec 7 Compliant
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Indian Nursing Council & SGPGIMS Lucknow examination rules verification
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Auditing candidate scores against INC Gazette passing thresholds & grace regulations...
              </p>
            </div>
          )}

          {errorMsg && (
            <div className="p-4 rounded-2xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600" />
              <div>
                <p className="font-bold">Audit Check Error</p>
                <p className="mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {report && !isLoading && (
            <>
              {/* Verdict Banner */}
              <div
                className={`p-4 rounded-2xl border flex items-center justify-between gap-4 ${
                  report.anomalies_count === 0
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200"
                    : "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200"
                }`}
              >
                <div className="flex items-center gap-3">
                  {report.anomalies_count === 0 ? (
                    <ShieldCheck className="w-8 h-8 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-8 h-8 text-amber-600 flex-shrink-0" />
                  )}
                  <div>
                    <h4 className="font-bold text-sm sm:text-base">
                      {report.compliance_verdict}
                    </h4>
                    <p className="text-xs opacity-90 mt-0.5">
                      {report.anomalies_count === 0
                        ? "All evaluated marks, subcomponent arithmetic, and grace allocations conform to statutory standards."
                        : `${report.anomalies_count} candidate(s) require review before final marksheet printing.`}
                    </p>
                  </div>
                </div>

                <button
                  onClick={onExportBulkZip}
                  disabled={isExportingZip}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md transition-all whitespace-nowrap"
                >
                  <FileDown className="w-4 h-4" />
                  <span>{isExportingZip ? "Archiving..." : "Export Marksheets (ZIP)"}</span>
                </button>
              </div>

              {/* KPI Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-3.5">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase">Candidates Audited</div>
                  <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white mt-1">
                    {report.total_candidates}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Total Records</div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-3.5">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase">Clean Passes</div>
                  <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                    {report.clean_passes}
                  </div>
                  <div className="text-[10px] text-emerald-600 mt-0.5 font-medium">0 Grace Marks Used</div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-3.5">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase">Passed With Grace</div>
                  <div className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-1">
                    {report.grace_passes}
                  </div>
                  <div className="text-[10px] text-amber-600 mt-0.5 font-medium">INC Sec 7 Compliant (&le; 5m)</div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-3.5">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase">Re-appear / Failed</div>
                  <div className="text-2xl font-bold font-mono text-rose-600 dark:text-rose-400 mt-1">
                    {report.failures}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Below 50% Threshold</div>
                </div>
              </div>

              {/* Clauses Checklist */}
              <div className="bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/60 rounded-2xl p-4">
                <h5 className="text-xs font-bold text-blue-900 dark:text-blue-300 uppercase tracking-wide mb-2.5">
                  Verified Statutory Clauses
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {report.gazette_clauses_applied.map((clause, i) => (
                    <div key={i} className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                      <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                      <span>{clause}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Candidate Breakdown */}
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row justify-between items-center gap-3">
                  <div className="relative w-full sm:w-72">
                    <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search candidate name or roll..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                    />
                  </div>

                  <div className="flex items-center gap-1.5 self-end sm:self-auto">
                    {(["ALL", "PASS", "GRACE", "FAIL", "FLAGGED"] as const).map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setFilterCategory(cat)}
                        className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-colors ${
                          filterCategory === cat
                            ? "bg-blue-600 text-white"
                            : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                        }`}
                      >
                        {cat === "ALL"
                          ? `All (${report.candidates.length})`
                          : cat === "PASS"
                          ? `Clean (${report.clean_passes})`
                          : cat === "GRACE"
                          ? `Grace (${report.grace_passes})`
                          : cat === "FAIL"
                          ? `Fail (${report.failures})`
                          : `Flagged (${report.anomalies_count})`}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 border-b border-slate-200 dark:border-slate-700">
                      <tr>
                        <th className="p-3">Roll No</th>
                        <th className="p-3">Candidate Name</th>
                        <th className="p-3">Result Status</th>
                        <th className="p-3">Grace</th>
                        <th className="p-3">SGPA</th>
                        <th className="p-3">Audit Details & Reasons</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {filteredCandidates.map((c) => (
                        <tr key={c.roll_no} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                          <td className="p-3 font-mono font-semibold text-slate-900 dark:text-white">
                            {c.roll_no}
                          </td>
                          <td className="p-3 font-medium text-slate-900 dark:text-white">
                            {c.student_name}
                            <div className="text-[10px] text-slate-400">{c.father_name}</div>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                c.status_category === "PASS"
                                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                                  : c.status_category === "PASS_WITH_GRACE"
                                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                                  : c.status_category === "FAIL"
                                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                                  : "bg-red-200 text-red-900 font-bold"
                              }`}
                            >
                              {c.result_status}
                            </span>
                          </td>
                          <td className="p-3 font-mono">
                            {c.grace_marks_used > 0 ? (
                              <span className="font-bold text-amber-600 dark:text-amber-400">
                                {c.grace_marks_used} m
                              </span>
                            ) : (
                              <span className="text-slate-400">-</span>
                            )}
                          </td>
                          <td className="p-3 font-mono font-semibold">
                            {c.sgpa ? c.sgpa.toFixed(2) : "N/A"}
                          </td>
                          <td className="p-3 text-[11px] text-slate-600 dark:text-slate-300">
                            {c.compliance_notes.join("; ")}
                            {c.anomalies.length > 0 && (
                              <div className="text-rose-600 font-semibold mt-0.5">
                                {c.anomalies.join("; ")}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
          <div className="text-xs text-slate-500">
            Official Indian Nursing Council Regulations &bull; SGPGIMS Lucknow
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
            >
              Close
            </button>
            <button
              onClick={onExportBulkZip}
              disabled={isExportingZip}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/20 transition-colors"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Export Marksheets (ZIP)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
