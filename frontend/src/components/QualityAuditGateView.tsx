"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Bug,
  RefreshCw
} from "lucide-react";
import { QualityAuditReport, EvaluatedStudentRecord, UploadAuditResponse } from "../types/marksheet";
import { QualityAuditGateSection } from "./QualityAuditGateSection";

export const QualityAuditGateView: React.FC = () => {
  const [auditReport, setAuditReport] = useState<QualityAuditReport | null>(null);
  const [evaluatedStudents, setEvaluatedStudents] = useState<EvaluatedStudentRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeScenario, setActiveScenario] = useState<"none" | "clean" | "anomalies">("none");

  const handleExportPdf = async () => {
    if (evaluatedStudents.length === 0) {
      alert("No evaluated students available in this dataset to export.");
      return;
    }
    setIsExporting(true);
    try {
      const res = await fetch("/api/pdf/bulk?semester=1", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(evaluatedStudents),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Bulk PDF export failed.");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "SGPGIMS_BSc_Nursing_Sem1_Marksheets.zip";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error exporting marksheets.";
      alert(msg);
    } finally {
      setIsExporting(false);
    }
  };

  // Load clean verification by default or on demand
  const handleRunCleanAudit = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    setActiveScenario("clean");

    try {
      // Ingest canonical Master DataSheet
      const res = await fetch("/api/template/1");
      if (!res.ok) throw new Error("Could not fetch master workbook template.");

      const blob = await res.blob();
      const formData = new FormData();
      formData.append("file", blob, "SGPGIMS_Clean_Audit_Master.xlsx");
      formData.append("semester", "1");

      const auditRes = await fetch("/api/audit/upload-and-audit", {
        method: "POST",
        body: formData,
      });

      if (!auditRes.ok) {
        throw new Error(`Audit failed with status ${auditRes.status}`);
      }

      const data: UploadAuditResponse = await auditRes.json();
      setAuditReport(data.audit_report);
      setEvaluatedStudents(data.evaluation.results);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error executing Quality Audit Gate.";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunAnomaliesAudit = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    setActiveScenario("anomalies");

    // Synthetic payload containing the exact violations required by Phase 3:
    // 1. Part A + Part B != External Total
    // 2. IA + EA + Grace != Course Total
    // 3. Grace > 5.0 marks cap
    // 4. Missing father name
    // 5. Duplicate roll number
    // 6. IA marks > 25 limit
    const syntheticFlawedRecords = [
      {
        roll_no: "202501002",
        enroll_no: "2025630",
        student_name: "ADITYA KUMAR KATHERIYA",
        father_name: "", // Missing Father's Name!
        courses: {
          ANAT_PHYS: {
            int_marks: 20,
            ex_part_a: 19,
            ex_part_b: 20,
            ex_total: 45, // Mismatch! 19 + 20 = 39 != 45
            grace: 0,
            total: 65
          },
          SOCI_PSYC: {
            int_marks: 20,
            ex_part_a: 20,
            ex_part_b: 15,
            ex_total: 35,
            grace: 2.5,
            total: 57.5
          },
          ENGL: { int_marks: 21, ex_marks: 23, total: 44 }
        },
        raw_remarks: "PASS WITH 2.5 GRACE MARKS IN APPLIED SOCIOLOGY & APPLIED PSYCHOLOGY"
      },
      {
        roll_no: "202501002", // Duplicate Roll Number!
        enroll_no: "2025631",
        student_name: "DUPLICATE ENTRY CANDIDATE",
        father_name: "VIJAY KUMAR",
        courses: {
          ANAT_PHYS: {
            int_marks: 30, // Exceeds Max 25 IA boundary!
            ex_part_a: 20,
            ex_part_b: 20,
            ex_total: 40,
            grace: 0,
            total: 70
          },
          SOCI_PSYC: {
            int_marks: 20,
            ex_part_a: 20,
            ex_part_b: 20,
            ex_total: 40,
            grace: 0,
            total: 60
          },
          ENGL: { int_marks: 20, ex_marks: 20, total: 40 }
        },
        raw_remarks: "PASS"
      },
      {
        roll_no: "202501009",
        enroll_no: "2025639",
        student_name: "EXCESS GRACE CANDIDATE",
        father_name: "RAMESH CHANDRA",
        courses: {
          ANAT_PHYS: {
            int_marks: 18,
            ex_part_a: 20,
            ex_part_b: 20,
            ex_total: 40,
            grace: 0,
            total: 58
          },
          SOCI_PSYC: {
            int_marks: 20,
            ex_part_a: 15,
            ex_part_b: 15,
            ex_total: 30,
            grace: 7.5, // Exceeds statutory 5.0 marks limit!
            total: 57.5
          },
          ENGL: { int_marks: 20, ex_marks: 20, total: 40 }
        },
        raw_remarks: "PASS WITH 7.5 GRACE MARKS"
      }
    ];

    try {
      const res = await fetch("/api/audit/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(syntheticFlawedRecords),
      });

      if (!res.ok) throw new Error("Failed to verify audit test scenario.");
      const report: QualityAuditReport = await res.json();
      setAuditReport(report);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error executing anomaly audit scenario.";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Automatically load clean verification on component mount
    handleRunCleanAudit();
  }, []);

  return (
    <div className="space-y-6">
      {/* Control Banner for Scenarios */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <span className="text-[11px] font-bold tracking-wider text-blue-600 dark:text-blue-400 uppercase bg-blue-50 dark:bg-blue-950/60 px-2.5 py-1 rounded-md">
            Interactive Quality Gate Controller
          </span>
          <h2 className="text-xl font-black text-slate-900 dark:text-white mt-1.5">
            Integrity Verification & Anomaly Simulator
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Select a verification scenario to observe mathematical invariance and PDF export gating in real-time.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            onClick={handleRunCleanAudit}
            disabled={isLoading}
            className={`flex items-center gap-2 text-xs font-bold px-4 py-2.5 rounded-xl transition-all ${
              activeScenario === "clean"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                : "bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300"
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Clean Dataset (100% Invariant)</span>
          </button>

          <button
            onClick={handleRunAnomaliesAudit}
            disabled={isLoading}
            className={`flex items-center gap-2 text-xs font-bold px-4 py-2.5 rounded-xl transition-all ${
              activeScenario === "anomalies"
                ? "bg-rose-600 text-white shadow-md shadow-rose-600/30"
                : "bg-rose-50 dark:bg-rose-950/60 hover:bg-rose-100 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/60"
            }`}
          >
            <Bug className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            <span>Test Injected Anomalies (Error Matrix)</span>
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            Running Automated Mathematical & Regulatory Invariance Checks...
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Validating subcomponents, statutory grace caps, boundary limits, and SGPA formulas.
          </p>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 text-red-700 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Render the Quality Audit Gate Section */}
      {!isLoading && auditReport && (
        <QualityAuditGateSection
          auditReport={auditReport}
          evaluatedStudents={evaluatedStudents}
          isExporting={isExporting}
          onExportPdf={handleExportPdf}
        />
      )}
    </div>
  );
};
