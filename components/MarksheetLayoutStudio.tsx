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
  Sparkles,
  HelpCircle,
  Eye,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  GraduationCap
} from "lucide-react";
import { EvaluatedStudentRecord } from "../types/marksheet";
import {
  LayoutStudioConfig,
  DEFAULT_LAYOUT_CONFIG,
  getStoredLayoutConfig,
  saveStoredLayoutConfig,
  getSampleStudentForSemester,
  MarksheetRenderer
} from "./marksheets";

interface MarksheetLayoutStudioProps {
  currentStudents?: EvaluatedStudentRecord[];
  initialSemester?: number;
  onNavigateToDebug?: () => void;
}

export const MarksheetLayoutStudio: React.FC<MarksheetLayoutStudioProps> = ({
  currentStudents = [],
  initialSemester = 1,
  onNavigateToDebug
}) => {
  const [semester, setSemester] = useState<number>(initialSemester);
  const [selectedStudentIdx, setSelectedStudentIdx] = useState<number>(0);
  const [layoutConfig, setLayoutConfig] = useState<LayoutStudioConfig>(DEFAULT_LAYOUT_CONFIG);
  const [isDirectEditing, setIsDirectEditing] = useState<boolean>(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(true);
  const [isSavedToast, setIsSavedToast] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(0.85);

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
      [key]: val
    }));
  };

  const updateDimension = updateSetting;

  const handleStep = (key: keyof LayoutStudioConfig, delta: number, min: number, max: number) => {
    setLayoutConfig((prev) => {
      const current = prev[key] as number;
      const next = Math.round((current + delta) * 10) / 10;
      if (next < min || next > max) return prev;
      return {
        ...prev,
        [key]: next
      };
    });
  };

  const handleSavePreferences = () => {
    saveStoredLayoutConfig(semester, layoutConfig);
    setIsSavedToast(true);
    setTimeout(() => setIsSavedToast(false), 2500);
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
        colWidthCode: 15,
        colWidthTitle: 25,
      });
    } else if (preset === "compact") {
      setLayoutConfig({
        ...DEFAULT_LAYOUT_CONFIG,
        rowMinHeight: 32,
        cellPadding: 3,
        fontSizeGlobal: 9.5,
        fontSizeHeader: 10.5,
        topMargin: 2.0
      });
    } else if (preset === "spacious") {
      setLayoutConfig({
        ...DEFAULT_LAYOUT_CONFIG,
        rowMinHeight: 44,
        cellPadding: 8,
        fontSizeGlobal: 10.5,
        fontSizeHeader: 12.0,
        topMargin: 2.4
      });
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const sessionLabel = semester % 2 === 0 ? "JULY - 2026" : "JANUARY - 2026";

  return (
    <div className="space-y-4">
      {/* 1. Main Layout Studio Top Bar */}
      <div className="no-print bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-0.5 rounded-full border border-blue-200 dark:border-blue-800 flex items-center gap-1.5">
                <Sliders className="w-3 h-3" />
                Marksheet Layout Studio
              </span>
              <span className="text-xs text-slate-400 font-medium">In-Browser Live Customizer</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white">
              Interactive Marksheet Dimensions & Live Content Editor
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Adjust row heights, cell padding, typography, and column widths with real-time feedback. Click into any cell to correct typos before printing.
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 self-stretch lg:self-auto">
            {/* Direct Editing Toggle */}
            <button
              onClick={() => setIsDirectEditing(!isDirectEditing)}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold rounded-2xl transition-all shadow-sm ${
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

            {/* Toggle Drawer */}
            <button
              onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-2xl border transition-all ${
                isDrawerOpen
                  ? "bg-blue-50 dark:bg-blue-950/60 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300"
                  : "bg-slate-50 dark:bg-slate-800/80 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Dimension Studio</span>
              {isDrawerOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {/* Reset */}
            <button
              onClick={handleResetToStandard}
              className="flex items-center gap-1 px-3 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-2xl transition-colors"
              title="Reset this semester to standard INC / SGPGIMS regulations"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            {/* Save Preferences */}
            <button
              onClick={handleSavePreferences}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-2xl shadow-md shadow-blue-600/25 transition-all"
            >
              {isSavedToast ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Saved Sem {semester}!</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Preferences</span>
                </>
              )}
            </button>

            {/* Print Official Sheet */}
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 rounded-2xl shadow-md transition-all"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print Marksheet</span>
            </button>
          </div>
        </div>

        {/* Semester Tabs Selector & Candidate Switcher */}
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1 overflow-x-auto py-1">
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

          <div className="flex items-center gap-3">
            {/* Student Candidate selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Candidate:</span>
              {currentStudents.length > 0 ? (
                <select
                  value={selectedStudentIdx}
                  onChange={(e) => setSelectedStudentIdx(parseInt(e.target.value, 10))}
                  className="text-xs font-medium py-1.5 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  {currentStudents.slice(0, 30).map((s, idx) => (
                    <option key={idx} value={idx}>
                      {s.student_name} ({s.roll_no})
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-1 rounded-xl border border-blue-200 dark:border-blue-800">
                  {activeStudent.student_name} ({activeStudent.roll_no}) [INC Gazette Archetype]
                </span>
              )}
            </div>

            {/* Zoom controls */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.6, Math.round((z - 0.05) * 100) / 100))}
                className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[11px] font-mono px-2 text-slate-700 dark:text-slate-300 font-semibold">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(1.2, Math.round((z + 0.05) * 100) / 100))}
                className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setZoomLevel(0.85)}
                className="p-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded ml-1"
                title="Reset Zoom to 85%"
              >
                <Maximize2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Interactive Column & Row Dimension Controls Drawer */}
      {isDrawerOpen && (
        <div className="no-print bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-5 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <Sliders className="w-4 h-4 text-blue-600" />
                <span>Live Dimension Controls (Semester {semester})</span>
              </h3>
              <p className="text-xs text-slate-400">
                Move sliders or use stepper buttons. Values update the marksheet in real-time and inherit into print.
              </p>
            </div>

            {/* Presets */}
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-400 mr-1">Presets:</span>
              <button
                onClick={() => applyPreset("standard")}
                className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg transition-all ${
                  layoutConfig.textDirectionCode === "vertical" && layoutConfig.textDirectionTitle === "vertical"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                }`}
                title="SGPGIMS Institutional standard with vertical rotated text"
              >
                Vertical 270° (SGPGIMS)
              </button>
              <button
                onClick={() => applyPreset("horizontal")}
                className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg transition-all ${
                  layoutConfig.textDirectionCode === "horizontal" && layoutConfig.textDirectionTitle === "horizontal"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                }`}
                title="Standard horizontal table text"
              >
                Horizontal Standard
              </button>
              <button
                onClick={() => applyPreset("compact")}
                className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
              >
                Compact
              </button>
              <button
                onClick={() => applyPreset("spacious")}
                className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
              >
                Spacious
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Control 1: Table Row Height */}
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-200">
                  Table Row Height
                </label>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleStep("rowMinHeight", -1, 24, 50)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[38px] text-center">
                    {layoutConfig.rowMinHeight}px
                  </span>
                  <button
                    onClick={() => handleStep("rowMinHeight", 1, 24, 50)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
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
                className="w-full accent-blue-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">Min-height: 24px - 50px</span>
            </div>

            {/* Control 2: Cell Padding */}
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-200">
                  Cell Padding
                </label>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleStep("cellPadding", -1, 2, 24)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[38px] text-center">
                    {layoutConfig.cellPadding}px
                  </span>
                  <button
                    onClick={() => handleStep("cellPadding", 1, 2, 24)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
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
                className="w-full accent-blue-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">Padding: 2px - 24px (Legal fit)</span>
            </div>

            {/* Control 3: Global Font Size */}
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-200">
                  Table Font Size
                </label>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleStep("fontSizeGlobal", -0.5, 8, 12)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[38px] text-center">
                    {layoutConfig.fontSizeGlobal}pt
                  </span>
                  <button
                    onClick={() => handleStep("fontSizeGlobal", 0.5, 8, 12)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
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
                className="w-full accent-blue-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">Global scale: 8pt - 12pt</span>
            </div>

            {/* Control 4: Letterhead Top Clearance */}
            <div className="bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-200">
                  Top Clearance (Letterhead)
                </label>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleStep("topMargin", -0.1, 1.0, 3.2)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="font-mono text-xs font-bold text-blue-600 dark:text-blue-400 min-w-[38px] text-center">
                    {layoutConfig.topMargin}in
                  </span>
                  <button
                    onClick={() => handleStep("topMargin", 0.1, 1.0, 3.2)}
                    className="w-5 h-5 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-xs font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
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
                className="w-full accent-blue-600 cursor-pointer"
              />
              <span className="text-[10px] text-slate-400 block">Clearance: 1.0in - 3.2in</span>
            </div>
          </div>

          {/* Section: Text Orientation, Typography & Page-Fit Controls */}
          <div className="border-t border-slate-100 dark:border-slate-800 pt-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Text Orientation, Typography & Page Distribution
              </h4>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    updateSetting("textDirectionCode", "vertical");
                    updateSetting("textDirectionTitle", "vertical");
                  }}
                  className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
                >
                  Both Vertical (270°)
                </button>
                <button
                  onClick={() => {
                    updateSetting("textDirectionCode", "horizontal");
                    updateSetting("textDirectionTitle", "horizontal");
                  }}
                  className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
                >
                  Both Horizontal
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Course Code Orientation */}
              <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl border border-slate-200/70 dark:border-slate-700/70 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Course Code Direction</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                    {layoutConfig.textDirectionCode === "vertical" ? "Vertical (270°)" : "Horizontal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 pt-1">
                  <button
                    onClick={() => updateSetting("textDirectionCode", "vertical")}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionCode === "vertical"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => updateSetting("textDirectionCode", "horizontal")}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionCode === "horizontal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Horizontal
                  </button>
                </div>
              </div>

              {/* Course Title Orientation */}
              <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl border border-slate-200/70 dark:border-slate-700/70 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Course Title Direction</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                    {layoutConfig.textDirectionTitle === "vertical" ? "Vertical (270°)" : "Horizontal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 pt-1">
                  <button
                    onClick={() => updateSetting("textDirectionTitle", "vertical")}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionTitle === "vertical"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => updateSetting("textDirectionTitle", "horizontal")}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textDirectionTitle === "horizontal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Horizontal
                  </button>
                </div>
              </div>

              {/* Text Wrapping & Overflow */}
              <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl border border-slate-200/70 dark:border-slate-700/70 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Text Wrapping Mode</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                    {layoutConfig.textWrapping === "nowrap" ? "nowrap" : "normal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 pt-1">
                  <button
                    onClick={() => updateSetting("textWrapping", "normal")}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textWrapping === "normal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Wrap (Normal)
                  </button>
                  <button
                    onClick={() => updateSetting("textWrapping", "nowrap")}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.textWrapping === "nowrap"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Single Line (Nowrap)
                  </button>
                </div>
              </div>

              {/* Page Distribution Layout */}
              <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-2xl border border-slate-200/70 dark:border-slate-700/70 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Page Distribution</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                    {layoutConfig.pageFitLayout !== false ? "14in Fit" : "Compact"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 pt-1">
                  <button
                    onClick={() => updateSetting("pageFitLayout", true)}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.pageFitLayout !== false
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Full-Page Fit (14in)
                  </button>
                  <button
                    onClick={() => updateSetting("pageFitLayout", false)}
                    className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                      layoutConfig.pageFitLayout === false
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    Natural Flow
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sub-row: Individual Column Widths */}
          <div className="border-t border-slate-100 dark:border-slate-800 pt-4 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Individual Table Column Widths (%)
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {/* Sl.No */}
              <div className="bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  <span>Sl.No.</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthSno", -1, 3, 10)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Decrease width"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-600 dark:text-blue-400 min-w-[28px] text-center">{layoutConfig.colWidthSno}%</span>
                    <button
                      onClick={() => handleStep("colWidthSno", 1, 3, 10)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Increase width"
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
                  className="w-full accent-blue-600"
                />
              </div>

              {/* Course Code */}
              <div className="bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  <span>Code</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthCode", -1, 8, 22)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Decrease width"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-600 dark:text-blue-400 min-w-[28px] text-center">{layoutConfig.colWidthCode}%</span>
                    <button
                      onClick={() => handleStep("colWidthCode", 1, 8, 22)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Increase width"
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
                  className="w-full accent-blue-600"
                />
              </div>

              {/* Course Title */}
              <div className="bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  <span>Title</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthTitle", -1, 18, 40)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Decrease width"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-600 dark:text-blue-400 min-w-[28px] text-center">{layoutConfig.colWidthTitle}%</span>
                    <button
                      onClick={() => handleStep("colWidthTitle", 1, 18, 40)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Increase width"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={18}
                  max={40}
                  step={1}
                  value={layoutConfig.colWidthTitle}
                  onChange={(e) => updateDimension("colWidthTitle", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600"
                />
              </div>

              {/* Credits */}
              <div className="bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  <span>Credits</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthCredits", -1, 5, 14)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Decrease width"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-600 dark:text-blue-400 min-w-[28px] text-center">{layoutConfig.colWidthCredits}%</span>
                    <button
                      onClick={() => handleStep("colWidthCredits", 1, 5, 14)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Increase width"
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
                  className="w-full accent-blue-600"
                />
              </div>

              {/* Marks Block */}
              <div className="bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  <span>Marks</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthMarks", -1, 20, 45)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Decrease width"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-600 dark:text-blue-400 min-w-[28px] text-center">{layoutConfig.colWidthMarks}%</span>
                    <button
                      onClick={() => handleStep("colWidthMarks", 1, 20, 45)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Increase width"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={20}
                  max={45}
                  step={1}
                  value={layoutConfig.colWidthMarks}
                  onChange={(e) => updateDimension("colWidthMarks", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-600"
                />
              </div>

              {/* Letter Grade */}
              <div className="bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  <span>Grade</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("colWidthGrade", -1, 4, 12)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Decrease width"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-600 dark:text-blue-400 min-w-[28px] text-center">{layoutConfig.colWidthGrade}%</span>
                    <button
                      onClick={() => handleStep("colWidthGrade", 1, 4, 12)}
                      className="w-4 h-4 rounded bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-[10px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center hover:bg-slate-100"
                      title="Increase width"
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
                  className="w-full accent-blue-600"
                />
              </div>
            </div>
          </div>
        </div>
      )}


      {/* 3. Direct Editing Status Notification Banner */}
      {isDirectEditing && (
        <div className="no-print bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-700/60 rounded-2xl p-3 flex items-center justify-between text-xs text-amber-900 dark:text-amber-200 shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
            <span className="font-bold">Direct In-Browser Editing Active:</span>
            <span>
              Click anywhere on candidate demographics, course titles, marks cells, or remarks to edit values directly.
            </span>
          </div>
          <button
            onClick={() => setIsDirectEditing(false)}
            className="text-[11px] font-bold bg-amber-200 hover:bg-amber-300 dark:bg-amber-800 dark:hover:bg-amber-700 text-amber-900 dark:text-amber-100 px-3 py-1 rounded-xl transition-colors"
          >
            Lock Layout
          </button>
        </div>
      )}

      {/* 4. Live Marksheet Canvas Container */}
      <div className="bg-slate-200 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-3xl p-4 sm:p-6 overflow-x-auto shadow-inner flex flex-col items-center min-h-[800px]">
        {/* Scale Container */}
        <div
          style={{
            transform: `scale(${zoomLevel})`,
            transformOrigin: "top center",
            transition: "transform 0.15s ease-out"
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
  );
};

export default MarksheetLayoutStudio;
