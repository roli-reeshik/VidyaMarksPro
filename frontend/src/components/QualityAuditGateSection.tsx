"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Unlock,
  CheckCircle2,
  Search,
  FileDown,
  Info,
  ChevronDown,
  ChevronUp,
  RefreshCw
} from "lucide-react";
import { QualityAuditReport, EvaluatedStudentRecord } from "../types/marksheet";

interface QualityAuditGateProps {
  auditReport: QualityAuditReport | null;
  evaluatedStudents?: EvaluatedStudentRecord[];
  onAcknowledgeToggle?: (acknowledged: boolean) => void;
  onExportPdf?: () => void;
  isExporting?: boolean;
}

export const QualityAuditGateSection: React.FC<QualityAuditGateProps> = ({
  auditReport,
  onAcknowledgeToggle,
  onExportPdf,
  isExporting = false,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<"ALL" | "CRITICAL" | "WARNING">("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isAcknowledged, setIsAcknowledged] = useState<boolean>(false);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!auditReport) {
    return null;
  }

  const hasCriticalErrors = auditReport.critical_errors_count > 0;
  const isPdfLocked = hasCriticalErrors && !isAcknowledged;

  const handleToggleAcknowledge = () => {
    const nextVal = !isAcknowledged;
    setIsAcknowledged(nextVal);
    if (onAcknowledgeToggle) {
      onAcknowledgeToggle(nextVal);
    }
  };

  // Filter anomalies
  const filteredAnomalies = auditReport.anomalies.filter((a) => {
    if (filterSeverity === "CRITICAL" && a.severity !== "CRITICAL") return false;
    if (filterSeverity === "WARNING" && a.severity !== "WARNING") return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchRoll = a.roll_no.toLowerCase().includes(q);
      const matchName = a.student_name.toLowerCase().includes(q);
      const matchField = a.field.toLowerCase().includes(q);
      const matchDesc = a.description.toLowerCase().includes(q);
      return matchRoll || matchName || matchField || matchDesc;
    }
    return true;
  });

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
      {/* Header with Title and Gating Status */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold tracking-wider text-blue-600 dark:text-blue-400 uppercase bg-blue-50 dark:bg-blue-950/60 px-2.5 py-1 rounded-md">
              Phase 3 Quality Gate
            </span>
            <span className="text-xs text-slate-400">Institutional Verification</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white mt-1">
            Self-Verification, Invariance & Quality Audit Gate
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Automated integrity verification of subcomponent additions, grace thresholds, boundary limits, and SGPA invariance.
          </p>
        </div>

        {/* Audit Status Badge */}
        <div className="flex items-center gap-2 shrink-0">
          {hasCriticalErrors ? (
            <div className="flex items-center gap-2 bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-300 text-xs font-bold px-3 py-1.5 rounded-xl">
              <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />
              <span>{auditReport.critical_errors_count} Critical Violation(s)</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-900/60 text-emerald-700 dark:text-emerald-300 text-xs font-bold px-3 py-1.5 rounded-xl">
              <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>100% Invariance Verified</span>
            </div>
          )}
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Audited Candidates</div>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-1">
            {auditReport.total_candidates}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Total Rows Analyzed</div>
        </div>

        <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Clean Records</div>
          <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
            {auditReport.clean_candidates}
          </div>
          <div className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5 font-semibold">
            {Math.round((auditReport.clean_candidates / (auditReport.total_candidates || 1)) * 100)}% Error-Free
          </div>
        </div>

        <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Flagged Candidates</div>
          <div className={`text-xl font-bold font-mono mt-1 ${auditReport.flagged_candidates > 0 ? "text-rose-600 dark:text-rose-400" : "text-slate-400"}`}>
            {auditReport.flagged_candidates}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Need Verification</div>
        </div>

        <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Critical Errors</div>
          <div className={`text-xl font-bold font-mono mt-1 ${auditReport.critical_errors_count > 0 ? "text-rose-600 dark:text-rose-400" : "text-emerald-600"}`}>
            {auditReport.critical_errors_count}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Gating PDF Export</div>
        </div>

        <div className="col-span-2 sm:col-span-1 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase">Audit Warnings</div>
          <div className={`text-xl font-bold font-mono mt-1 ${auditReport.warnings_count > 0 ? "text-amber-600 dark:text-amber-400" : "text-slate-400"}`}>
            {auditReport.warnings_count}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Discrepancy Flags</div>
        </div>
      </div>

      {/* PDF Export Lock & Override Banner */}
      <div className={`p-5 rounded-2xl border transition-all ${
        isPdfLocked
          ? "bg-rose-50/80 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900/60"
          : isAcknowledged
          ? "bg-amber-50/80 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/60"
          : "bg-emerald-50/80 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900/60"
      }`}>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              isPdfLocked
                ? "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300"
                : isAcknowledged
                ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
            }`}>
              {isPdfLocked ? (
                <Lock className="w-5 h-5 text-rose-600 dark:text-rose-400" />
              ) : isAcknowledged ? (
                <Unlock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              )}
            </div>

            <div>
              <h3 className={`text-sm font-bold ${
                isPdfLocked
                  ? "text-rose-900 dark:text-rose-200"
                  : isAcknowledged
                  ? "text-amber-900 dark:text-amber-200"
                  : "text-emerald-900 dark:text-emerald-200"
              }`}>
                {isPdfLocked
                  ? "PDF Export Locked: Critical Integrity Violations Detected"
                  : isAcknowledged
                  ? "Audit Warning Acknowledged: PDF Export Unlocked (Manual Override)"
                  : "Quality Audit Gate Passed: Marksheet PDF Generation Approved"}
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                {isPdfLocked
                  ? "Examination regulations prohibit marksheet generation when subcomponent arithmetic, grace limits, or demographics fail verification. Review the matrix below or explicitly acknowledge."
                  : isAcknowledged
                  ? "You have manually acknowledged the discrepancies. High-resolution PDF generation is now accessible."
                  : "All arithmetic additions, INC 10-point scale grade boundaries, and SGPA calculations are mathematically sound."}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
            {hasCriticalErrors && (
              <button
                onClick={handleToggleAcknowledge}
                className={`flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-xl transition-all ${
                  isAcknowledged
                    ? "bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-300"
                    : "bg-amber-600 hover:bg-amber-700 text-white shadow-md shadow-amber-600/30"
                }`}
              >
                {isAcknowledged ? (
                  <>
                    <Lock className="w-3.5 h-3.5" />
                    <span>Relock Export</span>
                  </>
                ) : (
                  <>
                    <Unlock className="w-3.5 h-3.5" />
                    <span>Acknowledge & Unlock PDF</span>
                  </>
                )}
              </button>
            )}

            <button
              onClick={onExportPdf}
              disabled={isPdfLocked || isExporting}
              className={`flex items-center gap-2 text-xs font-bold px-5 py-2 rounded-xl shadow-md transition-all ${
                isPdfLocked || isExporting
                  ? "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/30 cursor-pointer"
              }`}
            >
              {isExporting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Generating Marksheets (ZIP)...</span>
                </>
              ) : (
                <>
                  <FileDown className="w-4 h-4" />
                  <span>Generate Marksheets (PDF ZIP)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Outlier & Error Matrix UI Table */}
      {auditReport.anomalies.length > 0 ? (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pt-2">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Interactive Error Matrix ({auditReport.anomalies.length} Flagged Items)
              </h3>
            </div>

            {/* Filters & Search */}
            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-60">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter by roll, name, field..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 text-slate-800 dark:text-slate-200"
                />
              </div>

              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
                {(["ALL", "CRITICAL", "WARNING"] as const).map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setFilterSeverity(sev)}
                    className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg transition-all ${
                      filterSeverity === sev
                        ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs"
                        : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                    }`}
                  >
                    {sev === "ALL"
                      ? `All (${auditReport.anomalies.length})`
                      : sev === "CRITICAL"
                      ? `Critical (${auditReport.critical_errors_count})`
                      : `Warnings (${auditReport.warnings_count})`}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-slate-800/70 border-b border-slate-200 dark:border-slate-800 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-4">Roll No</th>
                    <th className="py-3 px-4">Student Name</th>
                    <th className="py-3 px-4">Field / Metric</th>
                    <th className="py-3 px-4">Raw Value</th>
                    <th className="py-3 px-4">Expected Value</th>
                    <th className="py-3 px-4 text-center">Severity</th>
                    <th className="py-3 px-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {filteredAnomalies.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400">
                        No violations match the search filter.
                      </td>
                    </tr>
                  ) : (
                    filteredAnomalies.map((item, idx) => {
                      const isCritical = item.severity === "CRITICAL";
                      const isExpanded = expandedIndex === idx;

                      return (
                        <React.Fragment key={idx}>
                          <tr className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors ${
                            isCritical ? "bg-rose-50/20" : ""
                          }`}>
                            <td className="py-3 px-4 font-mono font-bold text-slate-900 dark:text-slate-100">
                              {item.roll_no}
                            </td>
                            <td className="py-3 px-4 font-semibold text-slate-800 dark:text-slate-200">
                              {item.student_name}
                            </td>
                            <td className="py-3 px-4 font-medium text-slate-700 dark:text-slate-300">
                              {item.field}
                            </td>
                            <td className="py-3 px-4 font-mono text-rose-600 dark:text-rose-400 font-semibold">
                              {item.raw_value}
                            </td>
                            <td className="py-3 px-4 font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                              {item.expected_value}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <span className={`inline-flex items-center gap-1 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full ${
                                isCritical
                                  ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300 border border-rose-300"
                                  : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border border-amber-300"
                              }`}>
                                {isCritical ? "CRITICAL" : "WARNING"}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                                className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 p-1"
                              >
                                {isExpanded ? (
                                  <ChevronUp className="w-4 h-4" />
                                ) : (
                                  <ChevronDown className="w-4 h-4" />
                                )}
                              </button>
                            </td>
                          </tr>

                          {/* Expanded Detail Row */}
                          {isExpanded && (
                            <tr className="bg-slate-50 dark:bg-slate-800/60">
                              <td colSpan={7} className="p-4 text-xs text-slate-600 dark:text-slate-300">
                                <div className="flex items-start gap-2 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                                  <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                                  <div>
                                    <span className="font-semibold text-slate-800 dark:text-slate-100">
                                      Audit Description:{" "}
                                    </span>
                                    <span>{item.description}</span>
                                    <div className="mt-1 text-[11px] text-slate-400">
                                      Category: <span className="font-mono">{item.category}</span>
                                    </div>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-6 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40 text-center">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
          <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-200">
            Zero Discrepancies or Outliers Detected
          </h4>
          <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-1">
            All subcomponents (Part A + Part B == External), internal assessments, grace ceilings, and SGPA formulas strictly satisfy statutory guidelines.
          </p>
        </div>
      )}
    </div>
  );
};
