"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  Pencil,
  Lock,
  Save,
  RotateCcw,
  Printer,
  ZoomIn,
  ZoomOut,
  Maximize2,
  CheckCircle2,
  Eye,
  PenTool,
  ArrowLeftRight,
  Sparkles,
  Info,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { EvaluatedStudentRecord } from "../types/marksheet";
import {
  LayoutStudioConfig,
  DEFAULT_LAYOUT_CONFIG,
  getStoredLayoutConfig,
  saveStoredLayoutConfig,
  syncLayoutToBackend,
  getSampleStudentForSemester,
  MarksheetRenderer,
} from "./marksheets";

interface MarksheetLayoutStudioProps {
  currentStudents?: EvaluatedStudentRecord[];
  initialSemester?: number;
  onNavigateToDebug?: () => void;
}

export const MarksheetLayoutStudio: React.FC<MarksheetLayoutStudioProps> = ({
  currentStudents = [],
  initialSemester = 1,
  onNavigateToDebug,
}) => {
  const [semester, setSemester] = useState<number>(initialSemester);
  const [selectedStudentIdx, setSelectedStudentIdx] = useState<number>(0);
  const [layoutConfig, setLayoutConfig] = useState<LayoutStudioConfig>(DEFAULT_LAYOUT_CONFIG);
  const [isDirectEditing, setIsDirectEditing] = useState<boolean>(false);
  const [isSavedToast, setIsSavedToast] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(0.75);
  const [showLeftFlank, setShowLeftFlank] = useState<boolean>(true);
  const [showRightFlank, setShowRightFlank] = useState<boolean>(true);

  // Load semester-specific layout configuration from localStorage on semester change
  useEffect(() => {
    const stored = getStoredLayoutConfig(semester);
    setLayoutConfig(stored);
  }, [semester]);

  // Determine active student
  const activeStudent: EvaluatedStudentRecord =
    currentStudents.length > 0 && currentStudents[selectedStudentIdx]
      ? currentStudents[selectedStudentIdx]
      : getSampleStudentForSemester(semester);

  // Dimension & Orientation control helpers with steppers
  const updateSetting = <K extends keyof LayoutStudioConfig>(
    key: K,
    val: LayoutStudioConfig[K]
  ) => {
    setLayoutConfig((prev) => ({
      ...prev,
      [key]: val,
    }));
  };

  const updateDimension = updateSetting;

  const handleStep = (key: keyof LayoutStudioConfig, delta: number, min: number, max: number) => {
    setLayoutConfig((prev) => {
      const current = (prev[key] as number) ?? 0;
      const next = Math.round((current + delta) * 10) / 10;
      if (next < min || next > max) return prev;
      return {
        ...prev,
        [key]: next,
      };
    });
  };

  const handleSavePreferences = async () => {
    saveStoredLayoutConfig(semester, layoutConfig);
    await syncLayoutToBackend(layoutConfig, semester);
    setIsSavedToast(true);
    setTimeout(() => setIsSavedToast(false), 3000);
  };

  const handleResetToStandard = () => {
    if (confirm(`Reset Semester ${semester} layout dimensions to official SGPGIMS / INC regulations?`)) {
      setLayoutConfig({ ...DEFAULT_LAYOUT_CONFIG });
      if (typeof window !== "undefined") {
        localStorage.removeItem(`vidya_marksheet_layout_sem${semester}`);
        localStorage.removeItem(`vidya_layout_prefs_sem_${semester}`);
      }
    }
  };

  const applyPreset = (preset: "standard" | "horizontal" | "compact" | "spacious") => {
    if (preset === "standard") {
      setLayoutConfig({ ...DEFAULT_LAYOUT_CONFIG });
    } else if (preset === "horizontal") {
      setLayoutConfig({
        ...DEFAULT_LAYOUT_CONFIG,
        textDirectionCode: "horizontal",
        textDirectionTitle: "horizontal",
        colWidthCode: 14,
        colWidthTitle: 22,
      });
    } else if (preset === "compact") {
      setLayoutConfig({
        ...DEFAULT_LAYOUT_CONFIG,
        rowMinHeight: 32,
        cellPadding: 3,
        fontSizeGlobal: 9.5,
        fontSizeHeader: 10.5,
        topMargin: 2.0,
        signatureSpace: 35,
      });
    } else if (preset === "spacious") {
      setLayoutConfig({
        ...DEFAULT_LAYOUT_CONFIG,
        rowMinHeight: 44,
        cellPadding: 8,
        fontSizeGlobal: 10.5,
        fontSizeHeader: 12.0,
        topMargin: 2.4,
        signatureSpace: 55,
      });
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const sessionLabel = semester % 2 === 0 ? "JULY - 2026" : "JANUARY - 2026";

  const totalAdjustableWidth =
    layoutConfig.colWidthSno +
    layoutConfig.colWidthCode +
    layoutConfig.colWidthTitle +
    layoutConfig.colWidthCredits +
    layoutConfig.colWidthMarks +
    layoutConfig.colWidthGrade;

  return (
    <div className="space-y-4">
      {/* 1. Main Studio Navigation & Toolbar Header */}
      <div className="no-print bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-4 sm:p-5 shadow-sm space-y-4">
        {/* Top Header Row */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-0.5 rounded-full border border-blue-200 dark:border-blue-800 flex items-center gap-1.5">
                <Sliders className="w-3 h-3" />
                Marksheet Layout Studio
              </span>
              <span className="text-xs text-slate-400 font-medium">Split-Flank Live Customizer</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white">
              Institutional Marksheet Dimensions & Live Content Editor
            </h2>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 self-stretch lg:self-auto">
            {/* Toggle Left Controls Flank */}
            <button
              onClick={() => setShowLeftFlank(!showLeftFlank)}
              className={`hidden xl:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-2xl border transition-all ${
                showLeftFlank
                  ? "bg-blue-50 dark:bg-blue-950/60 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300"
                  : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
              }`}
              title="Toggle Left Side Controls (Dimensions, Signatures & Orientation)"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Left Controls</span>
            </button>

            {/* Toggle Right Controls Flank */}
            <button
              onClick={() => setShowRightFlank(!showRightFlank)}
              className={`hidden xl:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-2xl border transition-all ${
                showRightFlank
                  ? "bg-blue-50 dark:bg-blue-950/60 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300"
                  : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
              }`}
              title="Toggle Right Side Controls (Column Widths & Presets)"
            >
              <span>Right Controls</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>

            {/* Direct Editing Toggle */}
            <button
              onClick={() => setIsDirectEditing(!isDirectEditing)}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-bold rounded-2xl transition-all shadow-sm ${
                isDirectEditing
                  ? "bg-amber-500 hover:bg-amber-600 text-white ring-2 ring-amber-300 dark:ring-amber-700 animate-pulse"
                  : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200"
              }`}
              title="Click to toggle inline text editing across the marksheet"
            >
              {isDirectEditing ? (
                <>
                  <Pencil className="w-3.5 h-3.5" />
                  <span>Direct Edit: ACTIVE</span>
                </>
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  <span>Enable Direct Edit</span>
                </>
              )}
            </button>

            {/* Debug Archetypes shortcut */}
            {onNavigateToDebug && (
              <button
                onClick={onNavigateToDebug}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-2xl transition-colors cursor-pointer"
                title="View 5 regulatory debug marksheets"
              >
                <Eye className="w-3.5 h-3.5 text-blue-500" />
                <span>Debug</span>
              </button>
            )}

            {/* Reset to standard */}
            <button
              onClick={handleResetToStandard}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-2xl transition-colors"
              title="Reset this semester to standard INC / SGPGIMS regulations"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            {/* Save Preferences */}
            <button
              onClick={handleSavePreferences}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-2xl shadow-md shadow-blue-600/25 transition-all"
            >
              {isSavedToast ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Saved Sem {semester}!</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save</span>
                </>
              )}
            </button>

            {/* Print Official Sheet */}
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 rounded-2xl shadow-md transition-all"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>
          </div>
        </div>

        {/* Semester Tabs Selector, Candidate Switcher & Zoom Controls */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
          {/* Semester Selector */}
          <div className="flex items-center gap-1 overflow-x-auto py-0.5">
            <span className="text-xs font-semibold text-slate-500 mr-2 shrink-0">Semester:</span>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
              <button
                key={s}
                onClick={() => setSemester(s)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 ${
                  semester === s
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                Sem {s}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Student Candidate selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Candidate:</span>
              {currentStudents.length > 0 ? (
                <select
                  value={selectedStudentIdx}
                  onChange={(e) => setSelectedStudentIdx(parseInt(e.target.value, 10))}
                  className="text-xs font-medium py-1 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  {currentStudents.slice(0, 30).map((s, idx) => (
                    <option key={idx} value={idx}>
                      {s.student_name} ({s.roll_no})
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-1 rounded-xl border border-blue-200 dark:border-blue-800">
                  {activeStudent.student_name} ({activeStudent.roll_no})
                </span>
              )}
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-xl border border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.5, Math.round((z - 0.05) * 100) / 100))}
                className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[11px] font-mono px-2 text-slate-700 dark:text-slate-300 font-semibold">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(1.25, Math.round((z + 0.05) * 100) / 100))}
                className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoomLevel(0.75)}
                className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded ml-0.5"
                title="Reset Zoom to 75%"
              >
                <Maximize2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Main Flanking Workspace: Left Controls + Center Canvas + Right Controls */}
      <div className="flex flex-col xl:flex-row items-start gap-4 w-full">
        {/* ========================================================================= */}
        {/* LEFT FLANK: Geometry, Signature Space, Typography & Orientation Controls */}
        {/* ========================================================================= */}
        {showLeftFlank && (
          <div className="no-print w-full xl:w-72 2xl:w-80 shrink-0 space-y-3.5 xl:sticky xl:top-3 xl:max-h-[calc(100vh-1.5rem)] xl:overflow-y-auto pr-0.5 custom-scrollbar">
            {/* Card 1: Page Clearance & Row Spacing */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-600" />
                  Dimensions & Clearance
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Live</span>
              </div>

              {/* Letterhead Top Clearance */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">
                    Top Clearance (Letterhead)
                  </label>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("topMargin", -0.1, 1.0, 3.2)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[32px] text-center">
                      {layoutConfig.topMargin}in
                    </span>
                    <button
                      onClick={() => handleStep("topMargin", 0.1, 1.0, 3.2)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={1.0}
                  max={3.2}
                  step={0.1}
                  value={layoutConfig.topMargin}
                  onChange={(e) => updateDimension("topMargin", parseFloat(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Table Row Height */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">
                    Table Row Height
                  </label>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("rowMinHeight", -1, 24, 50)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[32px] text-center">
                      {layoutConfig.rowMinHeight}px
                    </span>
                    <button
                      onClick={() => handleStep("rowMinHeight", 1, 24, 50)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={24}
                  max={50}
                  step={1}
                  value={layoutConfig.rowMinHeight}
                  onChange={(e) => updateDimension("rowMinHeight", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Cell Padding */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">
                    Cell Padding
                  </label>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("cellPadding", -1, 2, 24)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[32px] text-center">
                      {layoutConfig.cellPadding}px
                    </span>
                    <button
                      onClick={() => handleStep("cellPadding", 1, 2, 24)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={2}
                  max={24}
                  step={1}
                  value={layoutConfig.cellPadding}
                  onChange={(e) => updateDimension("cellPadding", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>
            </div>

            {/* Card 2: Dedicated Institutional Signature Clearance Space */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <PenTool className="w-3.5 h-3.5 text-emerald-600" />
                  Signatures Clearance Space
                </span>
                <span className="text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 px-1.5 py-0.5 rounded">
                  Ample Room
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">
                    Signing Area Height
                  </label>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("signatureSpace", -2, 15, 90)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                      title="Decrease signature area"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400 min-w-[34px] text-center">
                      {layoutConfig.signatureSpace ?? 45}px
                    </span>
                    <button
                      onClick={() => handleStep("signatureSpace", 2, 15, 90)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                      title="Increase signature area"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={15}
                  max={90}
                  step={2}
                  value={layoutConfig.signatureSpace ?? 45}
                  onChange={(e) => updateDimension("signatureSpace", parseInt(e.target.value, 10))}
                  className="w-full accent-emerald-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
                <p className="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">
                  Vertical room above &ldquo;Prepared By&rdquo;, &ldquo;Checked By&rdquo; &amp; &ldquo;Sub-Dean&rdquo; for ink signatures &amp; rubber stamps.
                </p>
              </div>
            </div>

            {/* Card 3: Typography Scaling */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                  Typography Scale
                </span>
                <span className="text-[10px] text-slate-400 font-mono">pt</span>
              </div>

              {/* Global Font Size */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">
                    Table Font Size
                  </label>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("fontSizeGlobal", -0.5, 8, 12)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-purple-600 dark:text-purple-400 min-w-[32px] text-center">
                      {layoutConfig.fontSizeGlobal}pt
                    </span>
                    <button
                      onClick={() => handleStep("fontSizeGlobal", 0.5, 8, 12)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={8}
                  max={12}
                  step={0.5}
                  value={layoutConfig.fontSizeGlobal}
                  onChange={(e) => updateDimension("fontSizeGlobal", parseFloat(e.target.value))}
                  className="w-full accent-purple-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Header Font Size */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700 dark:text-slate-300">
                    Main Header Size
                  </label>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("fontSizeHeader", -0.5, 9, 14)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-purple-600 dark:text-purple-400 min-w-[32px] text-center">
                      {layoutConfig.fontSizeHeader}pt
                    </span>
                    <button
                      onClick={() => handleStep("fontSizeHeader", 0.5, 9, 14)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={9}
                  max={14}
                  step={0.5}
                  value={layoutConfig.fontSizeHeader}
                  onChange={(e) => updateDimension("fontSizeHeader", parseFloat(e.target.value))}
                  className="w-full accent-purple-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>
            </div>

            {/* Card 4: Text Orientation, Wrapping & Page Distribution */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <ArrowLeftRight className="w-3.5 h-3.5 text-indigo-600" />
                  Text Orientation & Fit
                </span>
              </div>

              {/* Course Title Orientation */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Course Title</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                    {layoutConfig.textDirectionTitle === "vertical" ? "Vertical 270°" : "Horizontal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => updateSetting("textDirectionTitle", "vertical")}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionTitle === "vertical"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => updateSetting("textDirectionTitle", "horizontal")}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionTitle === "horizontal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Horizontal
                  </button>
                </div>
              </div>

              {/* Course Code Orientation */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Course Code</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                    {layoutConfig.textDirectionCode === "vertical" ? "Vertical 270°" : "Horizontal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => updateSetting("textDirectionCode", "vertical")}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionCode === "vertical"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => updateSetting("textDirectionCode", "horizontal")}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionCode === "horizontal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Horizontal
                  </button>
                </div>
              </div>

              {/* Text Wrapping Mode */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Wrapping</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                    {layoutConfig.textWrapping === "nowrap" ? "nowrap" : "normal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => updateSetting("textWrapping", "normal")}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textWrapping === "normal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Wrap (Normal)
                  </button>
                  <button
                    onClick={() => updateSetting("textWrapping", "nowrap")}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textWrapping === "nowrap"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Single Line
                  </button>
                </div>
              </div>

              {/* Page Distribution */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Page Distribution</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                    {layoutConfig.pageFitLayout !== false ? "14in Fit" : "Compact"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <button
                    onClick={() => updateSetting("pageFitLayout", true)}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.pageFitLayout !== false
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Full 14in Fit
                  </button>
                  <button
                    onClick={() => updateSetting("pageFitLayout", false)}
                    className={`py-1 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.pageFitLayout === false
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                    }`}
                  >
                    Natural Flow
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* CENTER WORKSPACE: Live Marksheet Preview Canvas                           */}
        {/* ========================================================================= */}
        <div className="flex-1 min-w-0 flex flex-col items-center w-full space-y-3">
          {/* Direct Editing Status Notification Banner */}
          {isDirectEditing && (
            <div className="no-print w-full bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-700/60 rounded-2xl p-3 flex items-center justify-between text-xs text-amber-900 dark:text-amber-200 shadow-sm animate-fade-in">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                <span className="font-bold">Direct In-Browser Editing Active:</span>
                <span>Click any cell to edit demographics, course titles, or remarks directly.</span>
              </div>
              <button
                onClick={() => setIsDirectEditing(false)}
                className="text-[11px] font-bold bg-amber-200 hover:bg-amber-300 dark:bg-amber-800 dark:hover:bg-amber-700 text-amber-900 dark:text-amber-100 px-3 py-1 rounded-xl transition-colors"
              >
                Lock Layout
              </button>
            </div>
          )}

          {/* Marksheet Preview Canvas Container */}
          <div className="bg-slate-200 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-3xl p-3 sm:p-5 overflow-x-auto shadow-inner flex flex-col items-center w-full min-h-[850px]">
            <div
              style={{
                transform: `scale(${zoomLevel})`,
                transformOrigin: "top center",
                transition: "transform 0.15s ease-out",
              }}
              className="shadow-2xl rounded-sm transition-all"
            >
              <MarksheetRenderer
                semesterNumber={semester}
                student={activeStudent}
                sessionMonthYear={sessionLabel}
                layoutConfig={layoutConfig}
                isDirectEditing={isDirectEditing}
              />
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT FLANK: Column Widths (Reduced Title Width) & Presets                */}
        {/* ========================================================================= */}
        {showRightFlank && (
          <div className="no-print w-full xl:w-72 2xl:w-80 shrink-0 space-y-3.5 xl:sticky xl:top-3 xl:max-h-[calc(100vh-1.5rem)] xl:overflow-y-auto pl-0.5 custom-scrollbar">
            {/* Card 1: Quick Presets */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  Quick Presets
                </span>
                <span className="text-[10px] text-slate-400 font-mono">1-Click</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => applyPreset("standard")}
                  className={`text-xs font-bold py-2 px-2.5 rounded-xl transition-all text-center ${
                    layoutConfig.textDirectionCode === "vertical" && layoutConfig.textDirectionTitle === "vertical"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                  }`}
                  title="Official SGPGIMS Regulations with vertical 270° text"
                >
                  SGPGIMS 270°
                </button>
                <button
                  onClick={() => applyPreset("horizontal")}
                  className={`text-xs font-bold py-2 px-2.5 rounded-xl transition-all text-center ${
                    layoutConfig.textDirectionCode === "horizontal" && layoutConfig.textDirectionTitle === "horizontal"
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                  }`}
                  title="Horizontal standard format"
                >
                  Horizontal Standard
                </button>
                <button
                  onClick={() => applyPreset("compact")}
                  className="text-xs font-bold py-2 px-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-center"
                >
                  Compact Fit
                </button>
                <button
                  onClick={() => applyPreset("spacious")}
                  className="text-xs font-bold py-2 px-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-center"
                >
                  Spacious Fit
                </button>
              </div>
            </div>

            {/* Card 2: Individual Column Widths (%) */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-600" />
                  Column Widths (%)
                </span>
                <span className="text-[10px] font-mono font-bold text-blue-600 dark:text-blue-400">
                  Total: {totalAdjustableWidth}%
                </span>
              </div>

              {/* Title of Course Width (Reduced width requested) */}
              <div className="bg-blue-50/60 dark:bg-blue-950/30 p-2.5 rounded-xl border border-blue-200/60 dark:border-blue-900/40 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-blue-900 dark:text-blue-200 flex items-center gap-1">
                    Title of Course
                    <span className="text-[9px] bg-blue-200 dark:bg-blue-800 px-1 py-0.2 rounded font-normal">
                      Reduced
                    </span>
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthTitle", -1, 12, 35)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-800 border border-blue-300 dark:border-blue-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-blue-100"
                      title="Decrease title column width"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-700 dark:text-blue-300 min-w-[28px] text-center">
                      {layoutConfig.colWidthTitle}%
                    </span>
                    <button
                      onClick={() => handleStep("colWidthTitle", 1, 12, 35)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-800 border border-blue-300 dark:border-blue-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-blue-100"
                      title="Increase title column width"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={12}
                  max={35}
                  step={1}
                  value={layoutConfig.colWidthTitle}
                  onChange={(e) => updateDimension("colWidthTitle", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-blue-200 dark:bg-blue-900 rounded-lg"
                />
                <p className="text-[10px] text-blue-700 dark:text-blue-400 leading-tight">
                  Proportionately streamlined so vertical rotated titles fit neatly without extra whitespace.
                </p>
              </div>

              {/* Course Code */}
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Course Code</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthCode", -1, 8, 22)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[28px] text-center">
                      {layoutConfig.colWidthCode}%
                    </span>
                    <button
                      onClick={() => handleStep("colWidthCode", 1, 8, 22)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={8}
                  max={22}
                  step={1}
                  value={layoutConfig.colWidthCode}
                  onChange={(e) => updateDimension("colWidthCode", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Sl.No */}
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Sl.No.</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthSno", -1, 3, 10)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[28px] text-center">
                      {layoutConfig.colWidthSno}%
                    </span>
                    <button
                      onClick={() => handleStep("colWidthSno", 1, 3, 10)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={3}
                  max={10}
                  step={1}
                  value={layoutConfig.colWidthSno}
                  onChange={(e) => updateDimension("colWidthSno", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Course Credits */}
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Course Credits</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthCredits", -1, 5, 14)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[28px] text-center">
                      {layoutConfig.colWidthCredits}%
                    </span>
                    <button
                      onClick={() => handleStep("colWidthCredits", 1, 5, 14)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={5}
                  max={14}
                  step={1}
                  value={layoutConfig.colWidthCredits}
                  onChange={(e) => updateDimension("colWidthCredits", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Marks Sub-columns (Internal, External, Total, Pct) */}
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Marks Columns</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthMarks", -1, 20, 48)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[28px] text-center">
                      {layoutConfig.colWidthMarks}%
                    </span>
                    <button
                      onClick={() => handleStep("colWidthMarks", 1, 20, 48)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={20}
                  max={48}
                  step={1}
                  value={layoutConfig.colWidthMarks}
                  onChange={(e) => updateDimension("colWidthMarks", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>

              {/* Letter Grade */}
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Letter Grade</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthGrade", -1, 4, 12)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      -
                    </button>
                    <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[28px] text-center">
                      {layoutConfig.colWidthGrade}%
                    </span>
                    <button
                      onClick={() => handleStep("colWidthGrade", 1, 4, 12)}
                      className="w-4 h-4 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-200"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={4}
                  max={12}
                  step={1}
                  value={layoutConfig.colWidthGrade}
                  onChange={(e) => updateDimension("colWidthGrade", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg"
                />
              </div>
            </div>

            {/* Card 3: Proportions / Width Summeter */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-blue-500" />
                  Table Width Summeter
                </span>
                <span className="text-[10px] font-mono text-slate-400">100% Target</span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden flex">
                <div
                  style={{ width: `${Math.min(100, totalAdjustableWidth)}%` }}
                  className={`h-full transition-all duration-300 ${
                    totalAdjustableWidth > 92
                      ? "bg-amber-500"
                      : totalAdjustableWidth >= 80
                      ? "bg-blue-600"
                      : "bg-indigo-500"
                  }`}
                />
              </div>

              <div className="flex justify-between text-[10px] text-slate-500">
                <span>Configured: {totalAdjustableWidth}%</span>
                <span>Remaining: ~{100 - totalAdjustableWidth}% (GP & Result)</span>
              </div>

              <button
                onClick={() => {
                  setLayoutConfig((prev) => ({
                    ...prev,
                    colWidthSno: DEFAULT_LAYOUT_CONFIG.colWidthSno,
                    colWidthCode: DEFAULT_LAYOUT_CONFIG.colWidthCode,
                    colWidthTitle: DEFAULT_LAYOUT_CONFIG.colWidthTitle,
                    colWidthCredits: DEFAULT_LAYOUT_CONFIG.colWidthCredits,
                    colWidthMarks: DEFAULT_LAYOUT_CONFIG.colWidthMarks,
                    colWidthGrade: DEFAULT_LAYOUT_CONFIG.colWidthGrade,
                  }));
                }}
                className="w-full mt-1 py-1 px-2 text-[10px] font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 rounded-xl transition-colors"
              >
                Reset Column Widths Only
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarksheetLayoutStudio;
