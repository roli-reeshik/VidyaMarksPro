"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Printer,
  FileDown,
  RefreshCw,
  GraduationCap,
  LayoutTemplate,
  FileText,
  Pencil,
  Sliders,
  ChevronDown,
  ChevronUp,
  Save,
  RotateCcw,
  CheckCircle2,
} from "lucide-react";
import { EvaluatedStudentRecord } from "../types/marksheet";
import {
  MarksheetRenderer,
  LayoutStudioConfig,
  DEFAULT_LAYOUT_CONFIG,
  getStoredLayoutConfig,
  saveStoredLayoutConfig,
} from "./marksheets";

interface MarksheetPreviewModalProps {
  student: EvaluatedStudentRecord | null;
  semester?: number;
  isOpen: boolean;
  onClose: () => void;
}

export const MarksheetPreviewModal: React.FC<MarksheetPreviewModalProps> = ({
  student,
  semester = 1,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<"react" | "print">("react");
  const [isDirectEditing, setIsDirectEditing] = useState<boolean>(false);
  const [layoutConfig, setLayoutConfig] = useState<LayoutStudioConfig>(DEFAULT_LAYOUT_CONFIG);
  const [showLayoutDrawer, setShowLayoutDrawer] = useState<boolean>(false);
  const [isSavedToast, setIsSavedToast] = useState<boolean>(false);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const updateSetting = <K extends keyof LayoutStudioConfig>(
    key: K,
    val: LayoutStudioConfig[K]
  ) => {
    setLayoutConfig((prev) => ({
      ...prev,
      [key]: val,
    }));
  };

  const handleStep = (key: keyof LayoutStudioConfig, delta: number, min: number, max: number) => {
    setLayoutConfig((prev) => {
      const current = prev[key] as number;
      const next = Math.round((current + delta) * 10) / 10;
      if (next < min || next > max) return prev;
      return {
        ...prev,
        [key]: next,
      };
    });
  };

  const handleSavePreferences = () => {
    saveStoredLayoutConfig(semester, layoutConfig);
    setIsSavedToast(true);
    setTimeout(() => setIsSavedToast(false), 2500);
  };

  const handleResetToStandard = () => {
    if (confirm(`Reset Semester ${semester} layout dimensions to standard INC / SGPGIMS regulations?`)) {
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
        topMargin: 2.0,
      });
    } else if (preset === "spacious") {
      setLayoutConfig({
        ...DEFAULT_LAYOUT_CONFIG,
        rowMinHeight: 44,
        cellPadding: 8,
        fontSizeGlobal: 10.5,
        fontSizeHeader: 12.0,
        topMargin: 2.4,
      });
    }
  };

  useEffect(() => {
    setLayoutConfig(getStoredLayoutConfig(semester));
  }, [semester]);

  useEffect(() => {
    if (!isOpen || !student) {
      setHtmlContent(null);
      return;
    }

    const fetchHtmlPreview = async () => {
      setIsLoading(true);
      setErrorMsg(null);
      try {
        const res = await fetch(`/api/pdf/preview-html?semester=${semester}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(student),
        });

        if (!res.ok) {
          throw new Error(`Failed to load marksheet preview (Status ${res.status})`);
        }

        const html = await res.text();
        setHtmlContent(html);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Error rendering marksheet preview.";
        setErrorMsg(msg);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHtmlPreview();
  }, [isOpen, student, semester]);

  if (!isOpen || !student) return null;

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      const res = await fetch(`/api/pdf/student?semester=${semester}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(student),
      });

      if (!res.ok) {
        throw new Error("Could not download PDF from server.");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Marksheet_${student.roll_no}_${student.student_name.replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error downloading PDF.";
      alert(msg);
    } finally {
      setIsDownloading(false);
    }
  };

  const handlePrint = () => {
    if (activeTab === "print") {
      const iframe = document.getElementById("marksheet-preview-iframe") as HTMLIFrameElement;
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
        return;
      }
    }
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl w-full max-w-5xl h-[94vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Top Modal Navigation Toolbar */}
        <div className="bg-slate-900 px-5 py-3 flex justify-between items-center text-white shrink-0 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-600/30 text-blue-300">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">
                  {student.student_name}
                </span>
                <span className="font-mono text-xs text-blue-300 bg-blue-950 px-2 py-0.5 rounded border border-blue-800">
                  {student.roll_no}
                </span>
                <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
                  Semester {semester}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Official Institutional Legal Marksheet Template (Semester {semester}) • SGPGIMS Lucknow
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-slate-800 p-0.5 rounded-xl border border-slate-700 mr-2 text-xs">
              <button
                onClick={() => setActiveTab("react")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer font-medium ${
                  activeTab === "react"
                    ? "bg-blue-600 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <LayoutTemplate className="w-3.5 h-3.5" />
                <span>React Component</span>
              </button>
              <button
                onClick={() => setActiveTab("print")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer font-medium ${
                  activeTab === "print"
                    ? "bg-blue-600 text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>PDF Print View</span>
              </button>
            </div>

            {activeTab === "react" && (
              <>
                <button
                  onClick={() => setShowLayoutDrawer(!showLayoutDrawer)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    showLayoutDrawer
                      ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                      : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                  }`}
                  title="Adjust columns width, row height, and text orientation"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Dimensions & Layout</span>
                  {showLayoutDrawer ? (
                    <ChevronUp className="w-3 h-3 ml-0.5" />
                  ) : (
                    <ChevronDown className="w-3 h-3 ml-0.5" />
                  )}
                </button>

                <button
                  onClick={() => setIsDirectEditing(!isDirectEditing)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    isDirectEditing
                      ? "bg-amber-500 hover:bg-amber-600 text-white animate-pulse"
                      : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                  }`}
                  title="Enable direct in-browser text editing on the marksheet"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{isDirectEditing ? "Direct Edit: ON" : "Direct Edit"}</span>
                </button>
              </>
            )}

            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-xl transition-colors cursor-pointer"
            >
              <Printer className="w-4 h-4" />
              <span className="hidden sm:inline">Print</span>
            </button>

            <button
              onClick={handleDownloadPdf}
              disabled={isDownloading}
              className="flex items-center gap-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl shadow-md shadow-blue-600/30 transition-all cursor-pointer"
            >
              {isDownloading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <FileDown className="w-4 h-4" />
              )}
              <span>{isDownloading ? "Rendering PDF..." : "Download Official PDF"}</span>
            </button>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors ml-1 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Interactive Dimension, Row Height, Column Width & Text Orientation Drawer */}
        {showLayoutDrawer && activeTab === "react" && (
          <div className="bg-slate-900 border-b border-slate-800 px-5 py-3 text-white shrink-0 overflow-y-auto max-h-[48vh] space-y-3 shadow-inner animate-in fade-in slide-in-from-top-1 duration-150">
            {/* Top Toolbar Row of Drawer: Presets & Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-2.5">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Layout & Dimensions Control (Semester {semester})
                </span>
                <span className="text-[11px] text-slate-400 hidden md:inline">
                  • Adjust column widths, row height, padding & text orientation live
                </span>
              </div>

              <div className="flex items-center gap-2">
                {/* Presets */}
                <div className="flex items-center gap-1 bg-slate-800 p-0.5 rounded-lg border border-slate-700">
                  <span className="text-[10px] text-slate-400 px-1.5 font-medium">Presets:</span>
                  <button
                    onClick={() => applyPreset("standard")}
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded transition-all ${
                      layoutConfig.textDirectionCode === "vertical" && layoutConfig.textDirectionTitle === "vertical"
                        ? "bg-blue-600 text-white"
                        : "text-slate-300 hover:text-white"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => applyPreset("horizontal")}
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded transition-all ${
                      layoutConfig.textDirectionCode === "horizontal" && layoutConfig.textDirectionTitle === "horizontal"
                        ? "bg-blue-600 text-white"
                        : "text-slate-300 hover:text-white"
                    }`}
                  >
                    Horizontal
                  </button>
                  <button
                    onClick={() => applyPreset("compact")}
                    className="text-[10px] font-semibold px-2 py-0.5 rounded text-slate-300 hover:text-white"
                  >
                    Compact
                  </button>
                  <button
                    onClick={() => applyPreset("spacious")}
                    className="text-[10px] font-semibold px-2 py-0.5 rounded text-slate-300 hover:text-white"
                  >
                    Spacious
                  </button>
                </div>

                {/* Reset to standard */}
                <button
                  onClick={handleResetToStandard}
                  className="flex items-center gap-1 text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-lg border border-slate-700 transition-colors"
                  title="Reset to standard SGPGIMS regulations"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset</span>
                </button>

                {/* Save Preferences */}
                <button
                  onClick={handleSavePreferences}
                  className="flex items-center gap-1 text-[11px] font-bold bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded-lg shadow-sm transition-all"
                  title="Save layout preferences for this semester"
                >
                  {isSavedToast ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-300" />
                      <span>Saved!</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-3 h-3" />
                      <span>Save Layout</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Grid 1: Row Height, Cell Padding & Text Directions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Row Height */}
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/80 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">Table Row Height</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("rowMinHeight", -1, 24, 54)}
                      className="w-5 h-5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-bold flex items-center justify-center"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-400 font-bold min-w-[36px] text-center">
                      {layoutConfig.rowMinHeight}px
                    </span>
                    <button
                      onClick={() => handleStep("rowMinHeight", 1, 24, 54)}
                      className="w-5 h-5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-bold flex items-center justify-center"
                    >
                      +
                    </button>
                  </div>
                </div>
                <input
                  type="range"
                  min={24}
                  max={54}
                  step={1}
                  value={layoutConfig.rowMinHeight}
                  onChange={(e) => updateSetting("rowMinHeight", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
              </div>

              {/* Cell Padding */}
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/80 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">Cell Padding</span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStep("cellPadding", -1, 2, 24)}
                      className="w-5 h-5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-bold flex items-center justify-center"
                    >
                      -
                    </button>
                    <span className="font-mono text-blue-400 font-bold min-w-[36px] text-center">
                      {layoutConfig.cellPadding}px
                    </span>
                    <button
                      onClick={() => handleStep("cellPadding", 1, 2, 24)}
                      className="w-5 h-5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-bold flex items-center justify-center"
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
                  onChange={(e) => updateSetting("cellPadding", parseInt(e.target.value, 10))}
                  className="w-full accent-blue-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                />
              </div>

              {/* Course Code Text Direction */}
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/80 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">Course Code Direction</span>
                  <span className="text-[10px] font-mono text-blue-300">
                    {layoutConfig.textDirectionCode === "vertical" ? "Vertical 270°" : "Horizontal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1">
                  <button
                    onClick={() => updateSetting("textDirectionCode", "vertical")}
                    className={`text-[11px] py-1 px-2 rounded-lg font-bold transition-all ${
                      layoutConfig.textDirectionCode === "vertical"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-700 hover:bg-slate-600 text-slate-300"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => updateSetting("textDirectionCode", "horizontal")}
                    className={`text-[11px] py-1 px-2 rounded-lg font-bold transition-all ${
                      layoutConfig.textDirectionCode === "horizontal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-700 hover:bg-slate-600 text-slate-300"
                    }`}
                  >
                    Horizontal
                  </button>
                </div>
              </div>

              {/* Course Title Text Direction */}
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/80 space-y-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-200">Course Title Direction</span>
                  <span className="text-[10px] font-mono text-blue-300">
                    {layoutConfig.textDirectionTitle === "vertical" ? "Vertical 270°" : "Horizontal"}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1">
                  <button
                    onClick={() => updateSetting("textDirectionTitle", "vertical")}
                    className={`text-[11px] py-1 px-2 rounded-lg font-bold transition-all ${
                      layoutConfig.textDirectionTitle === "vertical"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-700 hover:bg-slate-600 text-slate-300"
                    }`}
                  >
                    Vertical 270°
                  </button>
                  <button
                    onClick={() => updateSetting("textDirectionTitle", "horizontal")}
                    className={`text-[11px] py-1 px-2 rounded-lg font-bold transition-all ${
                      layoutConfig.textDirectionTitle === "horizontal"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "bg-slate-700 hover:bg-slate-600 text-slate-300"
                    }`}
                  >
                    Horizontal
                  </button>
                </div>
              </div>
            </div>

            {/* Grid 2: Individual Column Widths (%) */}
            <div className="pt-2 border-t border-slate-800 space-y-1.5">
              <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
                <span>Table Column Widths (%)</span>
                <span className="text-[10px] text-slate-400">
                  Total: {layoutConfig.colWidthSno + layoutConfig.colWidthCode + layoutConfig.colWidthTitle + layoutConfig.colWidthCredits + layoutConfig.colWidthMarks + layoutConfig.colWidthGrade}%
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                {/* Sl.No */}
                <div className="bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
                  <div className="flex justify-between items-center text-[11px] text-slate-300 mb-1">
                    <span>Sl.No</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleStep("colWidthSno", -1, 3, 10)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-mono text-blue-400 font-bold min-w-[26px] text-center">
                        {layoutConfig.colWidthSno}%
                      </span>
                      <button
                        onClick={() => handleStep("colWidthSno", 1, 3, 10)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
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
                    onChange={(e) => updateSetting("colWidthSno", parseInt(e.target.value, 10))}
                    className="w-full accent-blue-500 cursor-pointer h-1 bg-slate-700 rounded-lg"
                  />
                </div>

                {/* Course Code */}
                <div className="bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
                  <div className="flex justify-between items-center text-[11px] text-slate-300 mb-1">
                    <span>Code</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleStep("colWidthCode", -1, 8, 24)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-mono text-blue-400 font-bold min-w-[26px] text-center">
                        {layoutConfig.colWidthCode}%
                      </span>
                      <button
                        onClick={() => handleStep("colWidthCode", 1, 8, 24)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>
                  <input
                    type="range"
                    min={8}
                    max={24}
                    step={1}
                    value={layoutConfig.colWidthCode}
                    onChange={(e) => updateSetting("colWidthCode", parseInt(e.target.value, 10))}
                    className="w-full accent-blue-500 cursor-pointer h-1 bg-slate-700 rounded-lg"
                  />
                </div>

                {/* Course Title */}
                <div className="bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
                  <div className="flex justify-between items-center text-[11px] text-slate-300 mb-1">
                    <span>Title</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleStep("colWidthTitle", -1, 12, 42)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-mono text-blue-400 font-bold min-w-[26px] text-center">
                        {layoutConfig.colWidthTitle}%
                      </span>
                      <button
                        onClick={() => handleStep("colWidthTitle", 1, 12, 42)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>
                  <input
                    type="range"
                    min={12}
                    max={42}
                    step={1}
                    value={layoutConfig.colWidthTitle}
                    onChange={(e) => updateSetting("colWidthTitle", parseInt(e.target.value, 10))}
                    className="w-full accent-blue-500 cursor-pointer h-1 bg-slate-700 rounded-lg"
                  />
                </div>

                {/* Credits */}
                <div className="bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
                  <div className="flex justify-between items-center text-[11px] text-slate-300 mb-1">
                    <span>Credits</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleStep("colWidthCredits", -1, 4, 14)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-mono text-blue-400 font-bold min-w-[26px] text-center">
                        {layoutConfig.colWidthCredits}%
                      </span>
                      <button
                        onClick={() => handleStep("colWidthCredits", 1, 4, 14)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>
                  <input
                    type="range"
                    min={4}
                    max={14}
                    step={1}
                    value={layoutConfig.colWidthCredits}
                    onChange={(e) => updateSetting("colWidthCredits", parseInt(e.target.value, 10))}
                    className="w-full accent-blue-500 cursor-pointer h-1 bg-slate-700 rounded-lg"
                  />
                </div>

                {/* Marks Grid */}
                <div className="bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
                  <div className="flex justify-between items-center text-[11px] text-slate-300 mb-1">
                    <span>Marks</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleStep("colWidthMarks", -1, 20, 48)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-mono text-blue-400 font-bold min-w-[26px] text-center">
                        {layoutConfig.colWidthMarks}%
                      </span>
                      <button
                        onClick={() => handleStep("colWidthMarks", 1, 20, 48)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
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
                    onChange={(e) => updateSetting("colWidthMarks", parseInt(e.target.value, 10))}
                    className="w-full accent-blue-500 cursor-pointer h-1 bg-slate-700 rounded-lg"
                  />
                </div>

                {/* Grade */}
                <div className="bg-slate-800/60 p-2 rounded-lg border border-slate-700/60">
                  <div className="flex justify-between items-center text-[11px] text-slate-300 mb-1">
                    <span>Grade</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleStep("colWidthGrade", -1, 3, 12)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        -
                      </button>
                      <span className="font-mono text-blue-400 font-bold min-w-[26px] text-center">
                        {layoutConfig.colWidthGrade}%
                      </span>
                      <button
                        onClick={() => handleStep("colWidthGrade", 1, 3, 12)}
                        className="w-4 h-4 rounded bg-slate-700 hover:bg-slate-600 text-[10px] font-bold text-slate-200 flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>
                  <input
                    type="range"
                    min={3}
                    max={12}
                    step={1}
                    value={layoutConfig.colWidthGrade}
                    onChange={(e) => updateSetting("colWidthGrade", parseInt(e.target.value, 10))}
                    className="w-full accent-blue-500 cursor-pointer h-1 bg-slate-700 rounded-lg"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal Body */}
        <div className="flex-1 bg-slate-100 dark:bg-slate-950 p-4 overflow-y-auto flex justify-center items-start">
          {activeTab === "react" ? (
            <div className="w-full flex justify-center my-2">
              <MarksheetRenderer
                semesterNumber={semester}
                student={student}
                sessionMonthYear={semester % 2 === 0 ? "JULY - 2026" : "JANUARY - 2026"}
                layoutConfig={layoutConfig}
                isDirectEditing={isDirectEditing}
              />
            </div>
          ) : (
            <>
              {isLoading && (
                <div className="m-auto text-center py-20">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Rendering Official Legal Marksheet...
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Applying approved SGPGIMS layout for Semester {semester}.
                  </p>
                </div>
              )}

              {errorMsg && (
                <div className="m-auto max-w-md p-4 rounded-2xl bg-red-50 text-red-700 text-xs border border-red-200 text-center">
                  {errorMsg}
                </div>
              )}

              {!isLoading && htmlContent && (
                <div className="w-full max-w-[220mm] shadow-2xl rounded-sm overflow-hidden bg-white my-2 border border-slate-300">
                  <iframe
                    id="marksheet-preview-iframe"
                    srcDoc={htmlContent}
                    title="Marksheet Preview"
                    className="w-full h-[900px] border-none"
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarksheetPreviewModal;
