"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Shield,
  UserCheck,
  CheckCircle2,
  Lock,
  Unlock,
  AlertTriangle,
  RefreshCw,
  FileCheck,
  ShieldCheck,
  ShieldAlert,
  Info
} from "lucide-react";
import { WorkflowStatus, UserRole, SemesterWorkflowSummary } from "../types/marksheet";

interface WorkflowControlPanelProps {
  semesterNumber: number;
  onWorkflowUpdated?: () => void;
  selectedRollNo?: string | null;
  selectedStudentName?: string | null;
  onClearSelectedStudent?: () => void;
}

export const WorkflowControlPanel: React.FC<WorkflowControlPanelProps> = ({
  semesterNumber,
  onWorkflowUpdated,
  selectedRollNo = null,
  selectedStudentName = null,
  onClearSelectedStudent
}) => {
  // Active role selector
  const [activeRole, setActiveRole] = useState<UserRole>("Scrutiny Committee");
  const [operatorName, setOperatorName] = useState<string>("Dr. Scrutiny In-Charge");

  // Workflow Summary from DB
  const [summary, setSummary] = useState<SemesterWorkflowSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Unlock Modal State
  const [isUnlockModalOpen, setIsUnlockModalOpen] = useState<boolean>(false);
  const [unlockJustification, setUnlockJustification] = useState<string>("");
  const [unlockError, setUnlockError] = useState<string | null>(null);

  // Fetch workflow state summary for the semester
  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/workflow/status/${semesterNumber}`);
      if (res.ok) {
        const data: SemesterWorkflowSummary = await res.json();
        setSummary(data);
      }
    } catch {
      // Ignore network errors on initial mount if backend not responding yet
    } finally {
      setLoading(false);
    }
  }, [semesterNumber]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  // Adjust default operator name when role switches
  const handleRoleChange = (role: UserRole) => {
    setActiveRole(role);
    if (role === "Admin / Sub-Dean") {
      setOperatorName("Sub-Dean Examinations");
    } else if (role === "Scrutiny Committee") {
      setOperatorName("Dr. Scrutiny In-Charge");
    } else {
      setOperatorName("Data Entry Operator");
    }
  };

  // Determine current active status
  const currentStatus: WorkflowStatus = selectedRollNo && summary
    ? (summary.students.find((s) => s.roll_no === selectedRollNo)?.workflow_status || "DRAFT")
    : (summary?.overall_status || "DRAFT");

  const isLocked = currentStatus === "LOCKED";

  // Transition Handler
  const handleTransition = async (targetStatus: WorkflowStatus, remarksNote?: string) => {
    setActionLoading(true);
    setErrorMsg(null);

    // Frontend validation for Sub-Dean approval
    if (targetStatus === "APPROVED" && activeRole !== "Admin / Sub-Dean") {
      setErrorMsg(
        "Unauthorized Action: Only users with the 'Admin / Sub-Dean' role can approve examination marks. Please switch to Admin / Sub-Dean role."
      );
      setActionLoading(false);
      return;
    }

    try {
      const payload = {
        semester_number: semesterNumber,
        target_status: targetStatus,
        user_role: activeRole,
        operator_name: operatorName,
        roll_no: selectedRollNo || null,
        remarks: remarksNote || `Transitioned to ${targetStatus} by ${activeRole}`,
      };

      const res = await fetch("http://127.0.0.1:8000/api/v1/workflow/transition", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Failed to transition workflow to ${targetStatus}`);
      }

      setSuccessToast(`Successfully moved to ${targetStatus}!`);
      setTimeout(() => setSuccessToast(null), 3000);
      await fetchSummary();
      if (onWorkflowUpdated) onWorkflowUpdated();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setErrorMsg(msg);
    } finally {
      setActionLoading(false);
    }
  };

  // Unlock Override Handler
  const handleUnlockSubmit = async () => {
    if (!unlockJustification || unlockJustification.trim().length < 5) {
      setUnlockError("A mandatory justification comment (minimum 5 characters) is required.");
      return;
    }

    if (activeRole !== "Admin / Sub-Dean") {
      setUnlockError("Only users with the 'Admin / Sub-Dean' role can unlock locked examination marks.");
      return;
    }

    setActionLoading(true);
    setUnlockError(null);

    try {
      const payload = {
        semester_number: semesterNumber,
        user_role: activeRole,
        operator_name: operatorName,
        justification: unlockJustification.trim(),
        roll_no: selectedRollNo || null,
        target_status: "DRAFT",
      };

      const res = await fetch("http://127.0.0.1:8000/api/v1/workflow/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to unlock marksheets for re-evaluation.");
      }

      setIsUnlockModalOpen(false);
      setUnlockJustification("");
      setSuccessToast("Marksheet unlocked for re-evaluation. Reverted to DRAFT.");
      setTimeout(() => setSuccessToast(null), 3000);
      await fetchSummary();
      if (onWorkflowUpdated) onWorkflowUpdated();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setUnlockError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  // Stepper definition
  const steps: { key: WorkflowStatus; label: string; desc: string }[] = [
    { key: "DRAFT", label: "Draft", desc: "Uploaded / Raw Data" },
    { key: "SCRUTINIZED", label: "Scrutinized", desc: "Scrutiny Committee Verified" },
    { key: "APPROVED", label: "Approved", desc: "Sub-Dean Approval" },
    { key: "LOCKED", label: "Locked / Published", desc: "Immutable Archival" },
  ];

  const getStepState = (stepKey: WorkflowStatus) => {
    const order: WorkflowStatus[] = ["DRAFT", "SCRUTINIZED", "APPROVED", "LOCKED"];
    const currentIdx = order.indexOf(currentStatus);
    const stepIdx = order.indexOf(stepKey);
    if (stepIdx < currentIdx) return "COMPLETED";
    if (stepIdx === currentIdx) return "ACTIVE";
    return "UPCOMING";
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4 mb-6">
      
      {/* Top Bar: Role Selector, Operator & Scope */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 dark:bg-indigo-950/60 rounded-xl border border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>Workflow Approval State Machine</span>
              <span className="text-[10px] font-semibold bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full border border-blue-200 dark:border-blue-800">
                Semester {semesterNumber}
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Role-based governance: Draft ➔ Scrutiny ➔ Sub-Dean Approval ➔ Immutable Lock
            </p>
          </div>
        </div>

        {/* Role & Operator Switcher */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-slate-200 dark:border-slate-700">
            <span className="text-[11px] font-semibold text-slate-500 px-2 flex items-center gap-1">
              <UserCheck className="w-3.5 h-3.5 text-blue-500" />
              <span>Role:</span>
            </span>
            <select
              value={activeRole}
              onChange={(e) => handleRoleChange(e.target.value as UserRole)}
              className="text-xs font-bold bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 px-2.5 py-1 rounded-lg border-none focus:outline-none shadow-sm cursor-pointer"
            >
              <option value="Scrutiny Committee">Scrutiny Committee</option>
              <option value="Admin / Sub-Dean">Admin / Sub-Dean</option>
              <option value="Operator / Data Entry">Operator / Data Entry</option>
            </select>
          </div>

          <div className="text-xs text-slate-500 hidden sm:flex items-center gap-1">
            <span className="text-[11px] text-slate-400">Operator:</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
              {operatorName}
            </span>
          </div>

          <button
            onClick={fetchSummary}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Refresh status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Selected Student Scope Notification (if targeting a single student) */}
      {selectedRollNo && (
        <div className="p-2.5 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 rounded-xl text-xs flex items-center justify-between gap-2 text-blue-800 dark:text-blue-300">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-500 shrink-0" />
            <span>
              Targeting individual candidate: <strong>{selectedStudentName || "Student"}</strong> (Roll No:{" "}
              <span className="font-mono font-bold">{selectedRollNo}</span>)
            </span>
          </div>
          {onClearSelectedStudent && (
            <button
              onClick={onClearSelectedStudent}
              className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 dark:text-blue-400 underline cursor-pointer"
            >
              Switch to Whole Batch
            </button>
          )}
        </div>
      )}

      {/* Error & Success Messages */}
      {errorMsg && (
        <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-500 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successToast && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-xl text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Visual Workflow Stepper Bar */}
      <div className="pt-2">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {steps.map((st, i) => {
            const state = getStepState(st.key);
            const isCurr = state === "ACTIVE";
            const isDone = state === "COMPLETED";

            return (
              <div
                key={st.key}
                className={`p-3 rounded-2xl border transition-all ${
                  isCurr
                    ? "bg-blue-50/70 dark:bg-blue-950/50 border-blue-400 dark:border-blue-600 shadow-sm"
                    : isDone
                    ? "bg-slate-50 dark:bg-slate-800/40 border-emerald-300 dark:border-emerald-800"
                    : "bg-slate-50/40 dark:bg-slate-800/20 border-slate-200 dark:border-slate-800 opacity-60"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono font-bold text-slate-400">
                    STEP 0{i + 1}
                  </span>
                  {isDone ? (
                    <span className="flex items-center gap-0.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Verified</span>
                    </span>
                  ) : isCurr ? (
                    <span className="text-[10px] font-bold bg-blue-600 text-white px-2 py-0.5 rounded-full animate-pulse">
                      Active
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-400">Pending</span>
                  )}
                </div>

                <div className="font-bold text-xs text-slate-900 dark:text-white flex items-center gap-1.5">
                  {st.key === "LOCKED" && <Lock className="w-3.5 h-3.5 text-amber-500" />}
                  <span>{st.label}</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">{st.desc}</div>

                {summary && (
                  <div className="mt-2 pt-2 border-t border-slate-200/50 dark:border-slate-700/50 text-[10px] text-slate-400 font-mono">
                    Candidates: {summary.counts[st.key] || 0}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Control Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Current Status:</span>
          <span
            className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1.5 ${
              isLocked
                ? "bg-rose-100 dark:bg-rose-950/80 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800"
                : currentStatus === "APPROVED"
                ? "bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800"
                : currentStatus === "SCRUTINIZED"
                ? "bg-purple-100 dark:bg-purple-950/80 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
                : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
            }`}
          >
            {isLocked && <Lock className="w-3.5 h-3.5 text-rose-500" />}
            <span>{currentStatus}</span>
          </span>
        </div>

        {/* Transition Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Step 1: DRAFT -> SCRUTINIZED */}
          {currentStatus === "DRAFT" && (
            <button
              onClick={() => handleTransition("SCRUTINIZED", "Scrutiny committee verified all marks calculations")}
              disabled={actionLoading}
              className="flex items-center gap-1.5 text-xs font-semibold bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer"
            >
              <FileCheck className="w-3.5 h-3.5" />
              <span>Verify & Mark as Scrutinized</span>
            </button>
          )}

          {/* Step 2: SCRUTINIZED -> APPROVED (Admin/Sub-Dean only) */}
          {currentStatus === "SCRUTINIZED" && (
            <button
              onClick={() => handleTransition("APPROVED", "Sub-Dean formal marksheet approval")}
              disabled={actionLoading}
              className={`flex items-center gap-1.5 text-xs font-semibold px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer ${
                activeRole === "Admin / Sub-Dean"
                  ? "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/30"
                  : "bg-slate-200 dark:bg-slate-800 text-slate-500 cursor-not-allowed"
              }`}
              title={
                activeRole === "Admin / Sub-Dean"
                  ? "Approve marksheet as Sub-Dean"
                  : "Only Admin / Sub-Dean can approve examination marks (Switch role above)"
              }
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Approve Marksheets (Sub-Dean)</span>
            </button>
          )}

          {/* Step 3: APPROVED -> LOCKED */}
          {currentStatus === "APPROVED" && (
            <button
              onClick={() => handleTransition("LOCKED", "Final official marksheet publication and locking")}
              disabled={actionLoading}
              className="flex items-center gap-1.5 text-xs font-semibold bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 text-white px-4 py-2 rounded-xl shadow-sm transition-all cursor-pointer"
            >
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>Lock & Publish Marksheets</span>
            </button>
          )}

          {/* Step 4: LOCKED -> Unlock for Re-evaluation Override */}
          {isLocked && (
            <button
              onClick={() => {
                setUnlockJustification("");
                setUnlockError(null);
                setIsUnlockModalOpen(true);
              }}
              className="flex items-center gap-1.5 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-xl shadow-sm shadow-amber-600/30 transition-all cursor-pointer"
            >
              <Unlock className="w-3.5 h-3.5" />
              <span>Unlock for Re-evaluation</span>
            </button>
          )}
        </div>
      </div>

      {/* Unlock for Re-evaluation Modal */}
      {isUnlockModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-6 space-y-4">
            
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 bg-amber-100 dark:bg-amber-950/60 rounded-xl text-amber-600 dark:text-amber-400">
                  <Unlock className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Unlock for Re-evaluation Override
                  </h3>
                  <p className="text-xs text-slate-400">
                    Administrator Re-evaluation Override Protocol
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsUnlockModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 rounded-2xl text-xs text-amber-800 dark:text-amber-300 space-y-1">
              <p className="font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Statutory Examination Warning</span>
              </p>
              <p className="leading-relaxed">
                Unlocking will revert the status from <strong>LOCKED</strong> back to <strong>DRAFT</strong>.
                This action is permanently logged to the <strong>marks_audit_log</strong> with the operator name and justification.
              </p>
            </div>

            {unlockError && (
              <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl text-xs text-red-700 dark:text-red-300">
                {unlockError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Administrator / Role:
                </label>
                <input
                  type="text"
                  value={`${activeRole} (${operatorName})`}
                  disabled
                  className="w-full text-xs font-mono bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-600 dark:text-slate-300"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Mandatory Justification / Reason: <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Re-evaluation approved following grievance appeal #482; clerical tabulation correction..."
                  value={unlockJustification}
                  onChange={(e) => setUnlockJustification(e.target.value)}
                  className="w-full text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
                <span className="text-[10px] text-slate-400">
                  Minimum 5 characters required for administrative audit integrity.
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                onClick={() => setIsUnlockModalOpen(false)}
                className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleUnlockSubmit}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white rounded-xl shadow-md transition-all cursor-pointer"
              >
                {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm Unlock Override</span>
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
