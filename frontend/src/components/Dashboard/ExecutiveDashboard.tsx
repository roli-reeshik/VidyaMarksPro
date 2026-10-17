"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  TrendingDown,
  Award,
  Trophy,
  Medal,
  Users,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FolderArchive,
  Download,
  BarChart3,
  Sparkles,
  Calendar,
  Layers,
  ArrowUpRight,
  HardDrive,
  RefreshCw,
  FileText,
  SlidersHorizontal,
  ChevronRight,
  MessageSquare,
  Search,
} from "lucide-react";
import { FeedbackModal } from "../FeedbackModal";
import { BacklogRosterModal } from "./BacklogRosterModal";
import { useAuth } from "../../context/AuthContext";

interface AnalyticsKPIs {
  total_registered: number;
  total_passed: number;
  total_failed: number;
  overall_passing_rate: number;
  distinction_count: number;
  distinction_rate: number;
  first_division_count: number;
  second_division_count: number;
  pass_class_count: number;
  maximum_percentage: number;
  median_percentage: number;
  minimum_percentage: number;
  average_sgpa: number;
  maximum_sgpa: number;
  backlog_density: number;
}

interface Ranker {
  rank: number;
  medal: string;
  badge_type: "gold" | "silver" | "bronze";
  student_name: string;
  roll_no: string;
  enrollment_no: string;
  semester: number;
  sgpa: number;
  percentage: number;
  has_distinction: boolean;
  distinction_badge: string;
  result_status: string;
}

interface SubjectPerformance {
  course_code: string;
  course_title: string;
  semester_number: number;
  credits: number;
  max_internal: number;
  max_external: number;
  max_total: number;
  total_students: number;
  passed_count: number;
  failed_count: number;
  pass_percentage: number;
  mean_internal_score: number;
  mean_external_score: number;
  mean_total_score: number;
  is_challenging: boolean;
  challenge_severity: string;
}

interface TrendComparison {
  has_prior_year_data: boolean;
  prior_year?: string;
  current_year?: string;
  pass_rate_drift: number;
  sgpa_drift: number;
  direction: "UP" | "DOWN" | "NEUTRAL";
  narrative: string;
}

export const ExecutiveDashboard: React.FC = () => {
  const { user } = useAuth();

  // Filter States
  const [selectedSession, setSelectedSession] = useState<string>("All Sessions");
  const [selectedSemester, setSelectedSemester] = useState<number | null>(null);
  const [yearComparisonEnabled, setYearComparisonEnabled] = useState<boolean>(true);

  // Data States
  const [kpis, setKpis] = useState<AnalyticsKPIs | null>(null);
  const [topRankers, setTopRankers] = useState<Ranker[]>([]);
  const [gradeDistribution, setGradeDistribution] = useState<Record<string, number>>({});
  const [trendComparison, setTrendComparison] = useState<TrendComparison | null>(null);
  const [subjects, setSubjects] = useState<SubjectPerformance[]>([]);
  const [availableSessions, setAvailableSessions] = useState<string[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Storage & Batch Export Drawer State
  const [storageDir, setStorageDir] = useState<string>("./exported_marksheets");
  const [exporting, setExporting] = useState<boolean>(false);
  const [exportProgress, setExportProgress] = useState<number>(0);
  const [exportResult, setExportResult] = useState<{
    total_exported: number;
    output_directory: string;
    file_list: string[];
  } | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Feedback & Backlog Modal States
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState<boolean>(false);
  const [isBacklogModalOpen, setIsBacklogModalOpen] = useState<boolean>(false);

  // Fetch Analytics & Subject Data
  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedSession !== "All Sessions") params.append("exam_session", selectedSession);
      if (selectedSemester !== null) params.append("semester", selectedSemester.toString());

      // 1. Fetch Analytics Overview
      const overviewRes = await fetch(`/api/v1/analytics/overview?${params.toString()}`, {
        credentials: "include",
      });
      if (!overviewRes.ok) {
        const err = await overviewRes.json();
        throw new Error(err.detail || "Failed to fetch analytics overview.");
      }
      const overviewData = await overviewRes.json();
      setKpis(overviewData.kpis);
      setTopRankers(overviewData.top_3_rankers || []);
      setGradeDistribution(overviewData.grade_distribution || {});
      setTrendComparison(overviewData.trend_comparison);
      if (overviewData.meta?.available_sessions) {
        setAvailableSessions(overviewData.meta.available_sessions);
      }

      // 2. Fetch Subject Performance
      const subjRes = await fetch(`/api/v1/analytics/subject-performance?${params.toString()}`, {
        credentials: "include",
      });
      if (subjRes.ok) {
        const subjData = await subjRes.json();
        setSubjects(subjData.courses || []);
      }

      // 3. Fetch Storage Config
      const configRes = await fetch("/api/v1/marksheets/export-config", { credentials: "include" });
      if (configRes.ok) {
        const cfgData = await configRes.json();
        if (cfgData.default_storage_dir) {
          setStorageDir(cfgData.default_storage_dir);
        }
      }
    } catch (err: any) {
      setError(err.message || "An error occurred while loading executive analytics.");
    } finally {
      setLoading(false);
    }
  }, [selectedSession, selectedSemester]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Handle Structured Batch Marksheet Export
  const handleBatchExport = async () => {
    setExporting(true);
    setExportProgress(10);
    setExportResult(null);
    setExportError(null);

    const targetSem = selectedSemester || 1;
    const targetSession = selectedSession === "All Sessions" ? "JANUARY - 2026" : selectedSession;

    try {
      setExportProgress(35);
      const res = await fetch("/api/v1/marksheets/export-batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          semester: targetSem,
          exam_month_year: targetSession,
          custom_directory: storageDir.trim(),
          watermarked_as_final: true,
        }),
      });

      setExportProgress(80);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to execute batch marksheet export.");
      }

      setExportProgress(100);
      setExportResult(data);
    } catch (err: any) {
      setExportError(err.message || "Failed to export marksheets.");
    } finally {
      setExporting(false);
    }
  };

  const getMedalColor = (type: "gold" | "silver" | "bronze") => {
    switch (type) {
      case "gold":
        return {
          bg: "from-amber-500/20 via-yellow-500/10 to-amber-600/20",
          border: "border-amber-400/50",
          text: "text-amber-300",
          icon: "text-amber-400",
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
        };
      case "silver":
        return {
          bg: "from-slate-400/20 via-slate-300/10 to-slate-500/20",
          border: "border-slate-300/50",
          text: "text-slate-200",
          icon: "text-slate-300",
          badge: "bg-slate-400/20 text-slate-200 border-slate-400/40",
        };
      case "bronze":
        return {
          bg: "from-orange-600/20 via-amber-700/10 to-orange-700/20",
          border: "border-orange-500/50",
          text: "text-orange-300",
          icon: "text-orange-400",
          badge: "bg-orange-600/20 text-orange-300 border-orange-500/40",
        };
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* 1. Header & Dynamic Temporal Controls */}
      <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-indigo-600 via-blue-600 to-sky-500 shadow-lg shadow-indigo-500/30 text-white flex items-center justify-center">
              <BarChart3 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                  Institutional Analytics Dashboard
                </h1>
                <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Live PostgreSQL Engine
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                VidyaMarksheet Longitudinal KPI & Batch Marksheet File Exporter | Priyanka Kumari
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={() => setIsFeedbackModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-amber-600/30 transition-all cursor-pointer"
            >
              <MessageSquare className="w-4 h-4" />
              <span>Feedback & Suggestions</span>
            </button>

            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-semibold border border-slate-700 transition-all shadow-sm"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Sync KPIs</span>
            </button>
          </div>
        </div>

        {/* Dynamic Controls Bar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 pt-4 border-t border-slate-800/80 items-center">
          {/* Session Filter */}
          <div className="md:col-span-4 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="text-xs font-semibold text-slate-300 shrink-0">Session:</span>
            <select
              value={selectedSession}
              onChange={(e) => setSelectedSession(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="All Sessions">All Academic Sessions</option>
              {availableSessions.map((sess) => (
                <option key={sess} value={sess}>
                  {sess}
                </option>
              ))}
            </select>
          </div>

          {/* Semester Filter Pills */}
          <div className="md:col-span-6 flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            <span className="text-xs font-semibold text-slate-300 shrink-0 mr-1">Semester:</span>
            <button
              onClick={() => setSelectedSemester(null)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all shrink-0 ${
                selectedSemester === null
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-800"
              }`}
            >
              All
            </button>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
              <button
                key={sem}
                onClick={() => setSelectedSemester(sem)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all shrink-0 ${
                  selectedSemester === sem
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Sem {sem}
              </button>
            ))}
          </div>

          {/* Year Comparison Switcher */}
          <div className="md:col-span-2 flex items-center justify-end gap-2">
            <span className="text-xs font-semibold text-slate-400">YoY Drift:</span>
            <button
              onClick={() => setYearComparisonEnabled(!yearComparisonEnabled)}
              className={`px-3 py-1 rounded-xl text-xs font-bold border transition-all ${
                yearComparisonEnabled
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                  : "bg-slate-800 text-slate-400 border-slate-700"
              }`}
            >
              {yearComparisonEnabled ? "Active" : "Disabled"}
            </button>
          </div>
        </div>
      </div>

      {/* 2. KPI Metric Cards (Glassmorphism & Micro-Interactions) */}
      {kpis && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1: Pass Rate (%) */}
          <div className="relative group bg-slate-900/80 border border-slate-800/90 hover:border-indigo-500/50 rounded-3xl p-5 shadow-xl transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all pointer-events-none" />
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
              <span className="uppercase tracking-wider">Overall Pass Rate</span>
              <span className="p-1.5 rounded-xl bg-emerald-500/20 text-emerald-400">
                <TrendingUp className="w-4 h-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-white font-mono">
                {kpis.overall_passing_rate}%
              </span>
              {trendComparison && trendComparison.has_prior_year_data && yearComparisonEnabled && (
                <span
                  className={`text-xs font-bold flex items-center ${
                    trendComparison.pass_rate_drift >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {trendComparison.pass_rate_drift >= 0 ? (
                    <TrendingUp className="w-3.5 h-3.5 mr-0.5 inline" />
                  ) : (
                    <TrendingDown className="w-3.5 h-3.5 mr-0.5 inline" />
                  )}
                  {trendComparison.pass_rate_drift > 0 ? "+" : ""}
                  {trendComparison.pass_rate_drift}% vs prior
                </span>
              )}
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
              <span>Passed: <strong className="text-slate-200">{kpis.total_passed}</strong> / {kpis.total_registered}</span>
              <span className="text-emerald-400 font-bold">{kpis.distinction_count} Distinctions</span>
            </div>
          </div>

          {/* Card 2: Highest Score / Max Percentage */}
          <div className="relative group bg-slate-900/80 border border-slate-800/90 hover:border-amber-500/50 rounded-3xl p-5 shadow-xl transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl group-hover:bg-amber-500/20 transition-all pointer-events-none" />
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
              <span className="uppercase tracking-wider">Top Percentage</span>
              <span className="p-1.5 rounded-xl bg-amber-500/20 text-amber-400">
                <Trophy className="w-4 h-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-amber-300 font-mono">
                {kpis.maximum_percentage}%
              </span>
              <span className="text-xs text-slate-400">Median: <strong className="text-slate-200">{kpis.median_percentage}%</strong></span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
              <span>Distinction Rate:</span>
              <span className="text-amber-400 font-bold">{kpis.distinction_rate}%</span>
            </div>
          </div>

          {/* Card 3: Batch Average SGPA */}
          <div className="relative group bg-slate-900/80 border border-slate-800/90 hover:border-indigo-500/50 rounded-3xl p-5 shadow-xl transition-all duration-300 overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all pointer-events-none" />
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
              <span className="uppercase tracking-wider">Batch Average SGPA</span>
              <span className="p-1.5 rounded-xl bg-indigo-500/20 text-indigo-400">
                <Award className="w-4 h-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-indigo-300 font-mono">
                {kpis.average_sgpa}
              </span>
              <span className="text-xs text-slate-400">Peak: <strong className="text-indigo-200">{kpis.maximum_sgpa}</strong></span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
              <span>Division I (60%+):</span>
              <span className="text-indigo-400 font-bold">{kpis.first_division_count} Candidates</span>
            </div>
          </div>

          {/* Card 4: Active Reappear / Backlog Count */}
          <div
            onClick={() => setIsBacklogModalOpen(true)}
            className="relative group bg-slate-900/80 border border-slate-800/90 hover:border-rose-500/60 rounded-3xl p-5 shadow-xl transition-all duration-300 overflow-hidden cursor-pointer hover:shadow-rose-950/20 hover:scale-[1.01]"
            title="Click to view full candidate backlog roster"
          >
            <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/10 rounded-full blur-2xl group-hover:bg-rose-500/25 transition-all pointer-events-none" />
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
              <span className="uppercase tracking-wider group-hover:text-rose-300 transition-colors">Backlog Density</span>
              <span className="p-1.5 rounded-xl bg-rose-500/20 text-rose-400 group-hover:bg-rose-500/30 transition-colors">
                <AlertTriangle className="w-4 h-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-rose-300 font-mono">
                {kpis.backlog_density}
              </span>
              <span className="text-xs text-rose-400/80 font-semibold">Candidates</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
              <span>Upcoming Cycle:</span>
              <span className="text-rose-400 font-bold group-hover:underline flex items-center gap-1">
                View Roster &rarr;
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 3. Visual Ranks & Podium Section ("Top 3 Achievers") */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Top 3 Achievers & Institutional Merit List
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Gazette Merit
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Top rankers determined by SGPA and percentage performance across evaluated semesters.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1 rounded-xl border border-slate-800">
            Gold / Silver / Bronze Accolades
          </span>
        </div>

        {topRankers.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No rankers calculated for selected cohort filters.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {topRankers.map((ranker) => {
              const style = getMedalColor(ranker.badge_type);
              return (
                <div
                  key={ranker.roll_no}
                  className={`relative bg-gradient-to-br ${style.bg} border ${style.border} rounded-2xl p-5 shadow-xl flex flex-col justify-between transition-all hover:scale-[1.02]`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-black uppercase tracking-wider px-2.5 py-1 rounded-lg ${style.badge}`}>
                        {ranker.medal}
                      </span>
                      <Medal className={`w-6 h-6 ${style.icon}`} />
                    </div>

                    <div className="mt-4">
                      <h3 className="text-base font-black text-white">{ranker.student_name}</h3>
                      <p className="text-xs text-slate-300 mt-0.5 font-mono">
                        Roll: {ranker.roll_no} | Enr: {ranker.enrollment_no}
                      </p>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-2 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                      <div>
                        <span className="text-[10px] uppercase font-semibold text-slate-400">SGPA Score</span>
                        <div className="text-lg font-black text-white font-mono">{ranker.sgpa}</div>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-semibold text-slate-400">Percentage</span>
                        <div className={`text-lg font-black font-mono ${style.text}`}>
                          {ranker.percentage}%
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Semester {ranker.semester}</span>
                    <span className={`text-[11px] font-bold ${style.text}`}>
                      {ranker.distinction_badge}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Grade Distribution & Challenging Subjects Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Grade Distribution Histogram */}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>INC Grade Distribution Histogram</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-400">O to F Scales</span>
          </div>

          <div className="grid grid-cols-4 gap-2.5 pt-2">
            {Object.entries(gradeDistribution).map(([grade, count]) => (
              <div
                key={grade}
                className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 text-center transition-all hover:border-slate-700"
              >
                <div
                  className={`text-sm font-black font-mono ${
                    grade === "O"
                      ? "text-amber-400"
                      : grade === "A+" || grade === "A"
                      ? "text-emerald-400"
                      : grade === "B+" || grade === "B"
                      ? "text-blue-400"
                      : grade === "C"
                      ? "text-indigo-400"
                      : "text-rose-400"
                  }`}
                >
                  Grade {grade}
                </div>
                <div className="text-xl font-bold text-white font-mono mt-1">{count}</div>
                <span className="text-[10px] text-slate-500">Subject Marks</span>
              </div>
            ))}
          </div>
        </div>

        {/* Challenging Subjects Summary */}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-md space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white">
                Challenging Subject Performance Index
              </h3>
            </div>
            <span className="text-[11px] font-mono text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              Identified Difficult Courses
            </span>
          </div>

          <div className="overflow-x-auto max-h-[260px] overflow-y-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="sticky top-0 bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px] font-semibold">
                <tr>
                  <th className="py-2 px-3">Course Code</th>
                  <th className="py-2 px-3">Title</th>
                  <th className="py-2 px-3">Pass %</th>
                  <th className="py-2 px-3">Mean Ext</th>
                  <th className="py-2 px-3">Failures</th>
                  <th className="py-2 px-3">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {subjects.slice(0, 5).map((subj) => (
                  <tr key={subj.course_code} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 font-mono font-bold text-white">
                      {subj.course_code}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 max-w-[180px] truncate" title={subj.course_title}>
                      {subj.course_title}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-semibold">
                      <span className={subj.pass_percentage >= 80 ? "text-emerald-400" : "text-rose-400"}>
                        {subj.pass_percentage}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">
                      {subj.mean_external_score}
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-rose-400">
                      {subj.failed_count}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                          subj.challenge_severity === "HIGH"
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                            : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                        }`}
                      >
                        {subj.challenge_severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 5. Marksheet Storage & Batch Exporter Drawer Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-600/20 border border-blue-500/40 text-blue-400">
              <HardDrive className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Automated Structured Marksheet File Exporter
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  Legal 8.5x14 Engine
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Writes PDFs to structured path: {"{STORAGE_DIR}/{Academic_Year}/{Exam_Session}/Semester_{N}/{Proper_Name}_{Roll_No}.pdf"}
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            <div className="md:col-span-8">
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">
                Target Marksheet Base Storage Directory (Server Disk or Mounted Drive)
              </label>
              <input
                type="text"
                value={storageDir}
                onChange={(e) => setStorageDir(e.target.value)}
                placeholder="./exported_marksheets"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="md:col-span-4 flex items-end">
              <button
                onClick={handleBatchExport}
                disabled={exporting}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
              >
                {exporting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Writing PDFs to Disk ({exportProgress}%)...</span>
                  </>
                ) : (
                  <>
                    <FolderArchive className="w-4 h-4" />
                    <span>Export Marksheets with Naming Pattern</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Progress bar */}
          {exporting && (
            <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
              <div
                className="bg-gradient-to-r from-blue-500 to-emerald-400 h-2 transition-all duration-300"
                style={{ width: `${exportProgress}%` }}
              />
            </div>
          )}

          {/* Export Output Report */}
          {exportResult && (
            <div className="p-4 bg-emerald-950/30 border border-emerald-500/40 rounded-xl space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between text-xs font-bold text-emerald-300">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Successfully Exported {exportResult.total_exported} Student Marksheets
                </span>
                <span className="font-mono text-[11px] text-emerald-200">
                  Audit Log Registered
                </span>
              </div>
              <p className="text-xs text-slate-300 font-mono">
                Directory: <strong>{exportResult.output_directory}</strong>
              </p>
              {exportResult.file_list && exportResult.file_list.length > 0 && (
                <div className="pt-2 border-t border-emerald-800/40">
                  <span className="text-[11px] font-semibold text-slate-400">Exported Files Sample:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {exportResult.file_list.slice(0, 6).map((fname) => (
                      <span
                        key={fname}
                        className="text-[10px] font-mono px-2 py-0.5 bg-slate-900 text-slate-200 rounded border border-slate-800"
                      >
                        {fname}
                      </span>
                    ))}
                    {exportResult.file_list.length > 6 && (
                      <span className="text-[10px] text-slate-400">
                        +{exportResult.file_list.length - 6} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {exportError && (
            <div className="p-3 bg-rose-500/15 border border-rose-500/40 text-rose-200 text-xs rounded-xl flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{exportError}</span>
            </div>
          )}
        </div>
      </div>

      {/* Feedback Modal Trigger */}
      <FeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
      />

      {/* Backlog Roster Modal */}
      <BacklogRosterModal
        isOpen={isBacklogModalOpen}
        onClose={() => setIsBacklogModalOpen(false)}
        initialSemester={selectedSemester}
      />
    </div>
  );
};
