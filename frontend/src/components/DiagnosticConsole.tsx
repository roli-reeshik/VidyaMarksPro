"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Activity,
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Terminal,
  Copy,
  Download,
  Database,
  BookOpen,
  KeyRound,
  FileSpreadsheet,
  FileText,
  History,
  HardDrive,
  Wrench,
  Check,
  ShieldCheck,
  Clock,
  Sparkles,
  Info,
} from "lucide-react";

interface SubCheckResult {
  name: string;
  status: "PASS" | "FAIL" | "WARN";
  detail: string;
}

interface DiagnosticModuleResult {
  module_name: string;
  subsystem_key: string;
  status: "PASS" | "FAIL" | "WARN";
  duration_ms: number;
  details: string;
  error?: string | null;
  suggested_fix?: string | null;
  subchecks: SubCheckResult[];
}

interface DiagnosticReport {
  status: "PASSED" | "FAILED" | "WARNING";
  timestamp: string;
  duration_ms: number;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  warning_checks: number;
  modules: DiagnosticModuleResult[];
  log_report: string;
  branding: string;
}

interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
}

const SUBSYSTEM_ICON_MAP: Record<string, React.ReactNode> = {
  database_integrity: <Database className="w-5 h-5 text-sky-400" />,
  inc_rules_math: <BookOpen className="w-5 h-5 text-indigo-400" />,
  auth_rbac: <KeyRound className="w-5 h-5 text-amber-400" />,
  excel_ingestion: <FileSpreadsheet className="w-5 h-5 text-emerald-400" />,
  pdf_engine: <FileText className="w-5 h-5 text-rose-400" />,
  backlog_reappear: <History className="w-5 h-5 text-purple-400" />,
  filesystem_storage: <HardDrive className="w-5 h-5 text-teal-400" />,
};

export const DiagnosticConsole: React.FC = () => {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [report, setReport] = useState<DiagnosticReport | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [copied, setCopied] = useState<boolean>(false);
  const [verbose, setVerbose] = useState<boolean>(true);
  const [activeFixModal, setActiveFixModal] = useState<DiagnosticModuleResult | null>(null);
  const [selectedSubsystemFilter, setSelectedSubsystemFilter] = useState<string>("ALL");
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  // Run Test Suite via SSE Streaming with synchronous fallback
  const handleRunDiagnostics = async () => {
    setIsRunning(true);
    setLogs([]);
    setReport(null);

    const timestamp = new Date().toLocaleTimeString();
    setLogs([
      {
        level: "INFO",
        message: "Initiating Full-System Diagnostic Suite across 7 subsystems...",
        timestamp,
      },
      {
        level: "INFO",
        message: "Compliance: INC Gazette Corrigendum & SGPGIMS Lucknow Regulations",
        timestamp,
      },
    ]);

    try {
      // 1. Try SSE Streaming Endpoint
      const sseUrl = "/api/v1/admin/stream-system-tests";
      const eventSource = new EventSource(sseUrl, { withCredentials: true });

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "log") {
            setLogs((prev) => [
              ...prev,
              {
                level: data.level || "INFO",
                message: data.message || "",
                timestamp: data.timestamp || new Date().toLocaleTimeString(),
              },
            ]);
          } else if (data.type === "complete") {
            setReport(data.report);
            setIsRunning(false);
            eventSource.close();
          }
        } catch {
          // ignore parsing error
        }
      };

      eventSource.onerror = async () => {
        eventSource.close();
        // Fallback to synchronous POST if SSE is interrupted or unsupported
        try {
          const res = await fetch("/api/v1/admin/run-system-tests", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ verbose }),
          });

          if (!res.ok) {
            throw new Error(`Diagnostic API returned HTTP ${res.status}`);
          }

          const data: DiagnosticReport = await res.json();
          setReport(data);

          // Append log entries from report if logs were empty
          if (data.log_report) {
            const rawLines = data.log_report.split("\n");
            const parsedLines: LogEntry[] = rawLines.map((line) => {
              const match = line.match(/^\[(.*?)\]\s*\[(.*?)\]\s*(.*)$/);
              if (match) {
                return { timestamp: match[1], level: match[2], message: match[3] };
              }
              return { timestamp: new Date().toLocaleTimeString(), level: "INFO", message: line };
            });
            setLogs(parsedLines);
          }
        } catch (postErr: any) {
          setLogs((prev) => [
            ...prev,
            {
              level: "ERROR",
              message: `Diagnostic execution failed: ${postErr.message || postErr}`,
              timestamp: new Date().toLocaleTimeString(),
            },
          ]);
        } finally {
          setIsRunning(false);
        }
      };
    } catch (err: any) {
      setLogs((prev) => [
        ...prev,
        {
          level: "ERROR",
          message: `Unable to initialize diagnostic runner: ${err.message || err}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      setIsRunning(false);
    }
  };

  // Copy Logs to Clipboard
  const handleCopyLogs = () => {
    const textToCopy =
      report?.log_report ||
      logs.map((l) => `[${l.timestamp}] [${l.level}] ${l.message}`).join("\n");
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Download Report
  const handleDownloadReport = (format: "txt" | "json") => {
    let content = "";
    let mimeType = "text/plain";
    const filename = `VidyaMarksheet_Diagnostic_Report_${new Date().toISOString().slice(0, 10)}.${format}`;

    if (format === "json") {
      content = JSON.stringify(report || { logs }, null, 2);
      mimeType = "application/json";
    } else {
      content =
        report?.log_report ||
        logs.map((l) => `[${l.timestamp}] [${l.level}] ${l.message}`).join("\n");
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredModules =
    report?.modules.filter((m) =>
      selectedSubsystemFilter === "ALL" ? true : m.status === selectedSubsystemFilter
    ) || [];

  return (
    <div className="space-y-6">
      {/* Header & Diagnostic Control Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-blue-600/10 via-indigo-600/5 to-transparent rounded-full blur-3xl -z-10"></div>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 text-white shadow-lg shadow-emerald-600/20">
                <Activity className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                  <span>System Diagnostic & Health Suite</span>
                  <span className="text-[11px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-2 py-0.5 rounded-full">
                    LIVE
                  </span>
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated non-destructive health checker compliant with INC Gazette & SGPGIMS regulations
                </p>
              </div>
            </div>
          </div>

          {/* Action Trigger Button */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleRunDiagnostics}
              disabled={isRunning}
              className={`flex items-center gap-2.5 px-6 py-3 rounded-xl font-bold text-sm text-white shadow-xl transition-all cursor-pointer ${
                isRunning
                  ? "bg-slate-700 cursor-not-allowed opacity-80"
                  : "bg-gradient-to-r from-emerald-600 via-teal-600 to-blue-600 hover:from-emerald-500 hover:to-blue-500 shadow-emerald-600/30 active:scale-95"
              }`}
            >
              {isRunning ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin text-emerald-300" />
                  <span>Running Diagnostic Engine...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white text-white" />
                  <span>Run System Health & Functionality Test</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Status Banner */}
        {report && (
          <div className="mt-6 pt-6 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5 flex items-center gap-3">
              {report.status === "PASSED" ? (
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              ) : report.status === "WARNING" ? (
                <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  <AlertTriangle className="w-5 h-5" />
                </div>
              ) : (
                <div className="p-2 rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30">
                  <XCircle className="w-5 h-5" />
                </div>
              )}
              <div>
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Overall Verdict</div>
                <div
                  className={`text-sm font-bold ${
                    report.status === "PASSED"
                      ? "text-emerald-400"
                      : report.status === "WARNING"
                      ? "text-amber-400"
                      : "text-rose-400"
                  }`}
                >
                  {report.status === "PASSED"
                    ? "100% OPERATIONAL"
                    : report.status === "WARNING"
                    ? "WARNINGS DETECTED"
                    : "ISSUES DETECTED"}
                </div>
              </div>
            </div>

            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Subsystems Passed</div>
                <div className="text-sm font-bold text-white">
                  {report.passed_checks} / {report.total_checks} Checks OK
                </div>
              </div>
            </div>

            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Execution Time</div>
                <div className="text-sm font-bold text-white">{report.duration_ms} ms</div>
              </div>
            </div>

            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Timestamp</div>
                <div className="text-xs font-mono font-medium text-slate-300">{report.timestamp}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Split Layout: Subsystem Matrix (Left) & Real-Time Terminal (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Subsystem Cards (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Diagnostic Subsystem Matrix</span>
              {report && (
                <span className="text-xs font-normal text-slate-400">
                  ({report.passed_checks}/{report.total_checks} Passing)
                </span>
              )}
            </h2>

            {/* Status Filter */}
            {report && (
              <div className="flex items-center gap-1 bg-slate-800/60 p-1 rounded-lg border border-slate-700/60 text-xs">
                {["ALL", "PASS", "FAIL"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setSelectedSubsystemFilter(f)}
                    className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors ${
                      selectedSubsystemFilter === f
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            )}
          </div>

          {!report && !isRunning && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 text-center shadow-sm">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto mb-3">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Diagnostic Suite Idle</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
                Click <strong>Run System Health & Functionality Test</strong> above to initiate non-destructive health checks across all 7 core subsystems.
              </p>
            </div>
          )}

          {/* Subsystem Cards */}
          <div className="space-y-3">
            {filteredModules.map((mod) => (
              <div
                key={mod.subsystem_key}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shrink-0">
                      {SUBSYSTEM_ICON_MAP[mod.subsystem_key] || <Activity className="w-5 h-5 text-blue-400" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-900 dark:text-white">{mod.module_name}</h3>
                        <span className="text-[10px] font-mono text-slate-500">{mod.duration_ms}ms</span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{mod.details}</p>
                    </div>
                  </div>

                  {/* Status Pill */}
                  <div className="shrink-0 flex items-center gap-2">
                    {mod.status === "PASS" ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>OPERATIONAL</span>
                      </span>
                    ) : mod.status === "WARN" ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>WARNING</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>FAILED</span>
                      </span>
                    )}

                    {mod.status !== "PASS" && mod.suggested_fix && (
                      <button
                        onClick={() => setActiveFixModal(mod)}
                        className="px-2 py-1 rounded text-[11px] font-bold bg-amber-600/20 text-amber-300 border border-amber-500/40 hover:bg-amber-600/30 flex items-center gap-1 transition-colors cursor-pointer"
                        title="View Suggested Fix"
                      >
                        <Wrench className="w-3 h-3" />
                        <span>Fix</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Subchecks List */}
                {mod.subchecks && mod.subchecks.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {mod.subchecks.map((sc, i) => (
                      <div
                        key={i}
                        className="text-[11px] flex items-center justify-between bg-slate-50 dark:bg-slate-950/60 px-2.5 py-1 rounded border border-slate-200 dark:border-slate-800"
                      >
                        <span className="font-medium text-slate-700 dark:text-slate-300">{sc.name}</span>
                        <span
                          className={`font-semibold ${
                            sc.status === "PASS"
                              ? "text-emerald-400"
                              : sc.status === "WARN"
                              ? "text-amber-400"
                              : "text-rose-400"
                          }`}
                        >
                          {sc.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Real-Time Dark Terminal Console (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <Terminal className="w-4 h-4 text-sky-400" />
              <span>Live Diagnostic Console</span>
            </h2>

            {/* Terminal Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyLogs}
                disabled={logs.length === 0}
                className="flex items-center gap-1 text-[11px] font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded border border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
                title="Copy terminal output to clipboard"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>

              <button
                onClick={() => handleDownloadReport("txt")}
                disabled={logs.length === 0}
                className="flex items-center gap-1 text-[11px] font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded border border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
                title="Download report as .txt"
              >
                <Download className="w-3 h-3" />
                <span>Download</span>
              </button>
            </div>
          </div>

          {/* Terminal Box */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 shadow-2xl h-[560px] flex flex-col font-mono text-xs overflow-hidden">
            {/* Terminal Top Bar */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 text-[10px] text-slate-500">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block"></span>
                <span className="ml-2 font-mono text-slate-400">vidya-diagnostic-reporter.sh</span>
              </div>
              <span>{logs.length} entries</span>
            </div>

            {/* Terminal Output */}
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 select-text">
              {logs.length === 0 && !isRunning && (
                <div className="text-slate-600 text-center py-20 italic">
                  Terminal idle. Click &ldquo;Run System Health &amp; Functionality Test&rdquo; to stream diagnostic logs.
                </div>
              )}

              {logs.map((log, idx) => {
                let badgeClass = "text-sky-400";
                if (log.level === "SUCCESS") badgeClass = "text-emerald-400 font-bold";
                else if (log.level === "ERROR") badgeClass = "text-rose-400 font-bold";
                else if (log.level === "WARN") badgeClass = "text-amber-400 font-bold";

                return (
                  <div key={idx} className="leading-relaxed break-words">
                    <span className="text-slate-500 mr-2">[{log.timestamp}]</span>
                    <span className={`mr-2 ${badgeClass}`}>[{log.level}]</span>
                    <span className="text-slate-200">{log.message}</span>
                  </div>
                );
              })}

              {isRunning && (
                <div className="flex items-center gap-2 text-emerald-400 pt-2 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <span>Executing live subsystem diagnostics...</span>
                </div>
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>
        </div>
      </div>

      {/* Suggested Fix Modal / Drawer */}
      {activeFixModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
            <div className="flex items-center gap-3 text-amber-400 mb-4">
              <Wrench className="w-6 h-6" />
              <h3 className="text-base font-bold text-white">Suggested Remediation: {activeFixModal.module_name}</h3>
            </div>

            <div className="space-y-4 text-xs">
              {activeFixModal.error && (
                <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-3 text-rose-200">
                  <span className="font-bold block text-rose-300 mb-1">Diagnostic Failure:</span>
                  {activeFixModal.error}
                </div>
              )}

              <div className="bg-amber-950/30 border border-amber-800/60 rounded-xl p-3.5 text-amber-200">
                <span className="font-bold block text-amber-300 mb-1 flex items-center gap-1.5">
                  <Info className="w-4 h-4" />
                  <span>Actionable Fix Recommendation:</span>
                </span>
                <p className="leading-relaxed">{activeFixModal.suggested_fix}</p>
              </div>

              <div className="bg-slate-800/60 rounded-xl p-3 text-slate-300 space-y-1">
                <span className="font-bold text-slate-200 block">Configuration Checkpoints:</span>
                <p>• Database: Check <code className="text-blue-300">backend/.env</code> connection strings and PostgreSQL service.</p>
                <p>• INC Gazette: Confirm course seed data using <code className="text-blue-300">seed_courses()</code>.</p>
                <p>• PDF Engine: Ensure Playwright is provisioned with <code className="text-blue-300">playwright install chromium</code>.</p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setActiveFixModal(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              >
                Close Fix Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
