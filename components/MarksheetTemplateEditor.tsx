"use client";

import React, { useState, useEffect } from "react";
import {
  Sliders,
  Type,
  Layout,
  Columns,
  RotateCcw,
  Save,
  CheckCircle2,
  Printer,
  Sparkles,
  ChevronRight,
  Eye,
  FileSpreadsheet
} from "lucide-react";
import { MarksheetTemplateConfig, EvaluatedStudentRecord } from "../types/marksheet";
import { MarksheetLayoutStudio } from "./MarksheetLayoutStudio";

const DEFAULT_CONFIG: MarksheetTemplateConfig = {
  institution_name: "SGPGIMS, LUCKNOW, UTTAR PRADESH",
  college_name: "COLLEGE OF NURSING",
  college_code: "0103",
  exam_title: "B.Sc.NURSING FIRST YEAR (FIRST SEMESTER) UNIVERSITY EXAMINATION JANUARY - 2026",
  place: "LUCKNOW",
  issue_date: "12/10/2026",
  paper_size: "8.5in 14in",
  top_margin: "2.5in",
  bottom_margin: "0.25in",
  left_margin: "0.25in",
  right_margin: "0.25in",
  row_padding: "standard",
  font_size_header: "11pt",
  font_size_demo: "11pt",
  font_size_table: "10pt",
  font_size_signatures: "10.5pt",
  col_label_sno: "Sl.No.",
  col_label_course_code: "Course Code",
  col_label_course_title: "Title of Course",
  col_label_credits: "Course Credits",
  col_label_internal: "Internal Assesment Marks",
  col_label_external: "End Semester University Exam Marks",
  col_label_total: "Total Marks",
  col_label_grade: "Letter Grade",
  col_label_grade_point: "Grade Point",
  col_label_credit_points: "Credit Points",
  show_sno: true,
  show_course_code: true,
  show_course_title: true,
  show_credits: true,
  show_internal: true,
  show_external: true,
  show_total: true,
  show_grade: true,
  show_grade_point: true,
  show_credit_points: true,
  sig1_title: "Prepared By",
  sig2_title: "Checked By",
  sig3_title: "Sub-Dean (Nursing)",
  sig4_title: "Executive Registrar",
  show_sig4: false,
  statutory_note: "<b>Note:</b> In case of any discrepancy in the marksheet, candidate may apply for correction within a period of four weeks from the date of issue to the office of the Executive Registrar."
};

interface MarksheetTemplateEditorProps {
  currentStudents?: EvaluatedStudentRecord[];
  onNavigateToDebug?: () => void;
}

export const MarksheetTemplateEditor: React.FC<MarksheetTemplateEditorProps> = ({
  currentStudents = [],
  onNavigateToDebug
}) => {
  const [editorMode, setEditorMode] = useState<"studio" | "institutional">("studio");
  const [config, setConfig] = useState<MarksheetTemplateConfig>(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState<"text" | "rows" | "columns">("text");
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [isLoadingPreview, setIsLoadingPreview] = useState<boolean>(false);
  const [selectedStudentIdx, setSelectedStudentIdx] = useState<number>(0);

  // Load saved config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch("/api/pdf/template-config");
        if (res.ok) {
          const remoteConfig: MarksheetTemplateConfig = await res.json();
          setConfig(remoteConfig);
        } else {
          const cached = localStorage.getItem("vidya_marksheet_template_config");
          if (cached) setConfig(JSON.parse(cached));
        }
      } catch {
        const cached = localStorage.getItem("vidya_marksheet_template_config");
        if (cached) setConfig(JSON.parse(cached));
      }
    };
    fetchConfig();
  }, []);

  // Refresh preview HTML when config changes
  useEffect(() => {
    let isCancelled = false;
    const updatePreview = async () => {
      setIsLoadingPreview(true);
      try {
        // Post config to backend to keep it active
        await fetch("/api/pdf/template-config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(config)
        });

        // Use selected uploaded student or fetch debug sample
        let studentToPreview: EvaluatedStudentRecord | null = null;
        if (currentStudents.length > 0 && currentStudents[selectedStudentIdx]) {
          studentToPreview = currentStudents[selectedStudentIdx];
        } else {
          const debugRes = await fetch("/api/pdf/debug-categories");
          if (debugRes.ok) {
            const categories = await debugRes.json();
            if (categories.length > 0) studentToPreview = categories[0].student;
          }
        }

        if (studentToPreview && !isCancelled) {
          const res = await fetch("/api/pdf/preview-html?semester=1", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(studentToPreview)
          });
          if (res.ok) {
            const html = await res.text();
            if (!isCancelled) setPreviewHtml(html);
          }
        }
      } catch (err) {
        console.error("Preview render failed:", err);
      } finally {
        if (!isCancelled) setIsLoadingPreview(false);
      }
    };

    const timer = setTimeout(updatePreview, 300);
    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [config, selectedStudentIdx, currentStudents]);

  const handleSave = async () => {
    try {
      localStorage.setItem("vidya_marksheet_template_config", JSON.stringify(config));
      await fetch("/api/pdf/template-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config)
      });
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 3000);
    } catch {
      alert("Template settings saved to browser storage.");
    }
  };

  const handleReset = () => {
    if (confirm("Reset marksheet template to standard SGPGIMS regulations?")) {
      setConfig(DEFAULT_CONFIG);
      localStorage.removeItem("vidya_marksheet_template_config");
    }
  };

  const handlePrint = () => {
    const iframe = document.getElementById("template-live-preview-iframe") as HTMLIFrameElement;
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    }
  };

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="flex bg-slate-200/80 dark:bg-slate-800/80 p-1 rounded-2xl border border-slate-300/60 dark:border-slate-700/60 w-fit">
        <button
          onClick={() => setEditorMode("studio")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            editorMode === "studio"
              ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Interactive Layout Studio & Live Editor</span>
        </button>
        <button
          onClick={() => setEditorMode("institutional")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            editorMode === "institutional"
              ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
          }`}
        >
          <Type className="w-3.5 h-3.5" />
          <span>Institutional Text & Signatories</span>
        </button>
      </div>

      {editorMode === "studio" ? (
        <MarksheetLayoutStudio
          currentStudents={currentStudents}
          onNavigateToDebug={onNavigateToDebug}
        />
      ) : (
        <div className="space-y-6">
          {/* Header bar */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-0.5 rounded-full border border-blue-200 dark:border-blue-800">
                    Template Customizer
                  </span>
                  <span className="text-xs text-slate-400">Institutional Layout Engine</span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                  Institutional Text & Headings Configuration
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                  Adjust typography, margins, table rows, column titles, and institutional signatories. Changes apply live to all generated marksheets.
                </p>
              </div>

              <div className="flex items-center gap-2.5 self-end md:self-auto">
                <button
                  onClick={handleReset}
                  className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Reset Standard</span>
                </button>

                <button
                  onClick={handleSave}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-md shadow-blue-600/20 transition-all"
                >
                  {isSaved ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Saved!</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-3.5 h-3.5" />
                      <span>Save Template</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Editor Grid: Left Controls, Right Preview */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Controls (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
          {/* Sub-tabs */}
          <div className="flex rounded-xl bg-slate-200/80 dark:bg-slate-800/80 p-1 border border-slate-300/50 dark:border-slate-700/50">
            <button
              onClick={() => setActiveTab("text")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeTab === "text"
                  ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              <Type className="w-3.5 h-3.5" />
              <span>Text & Headings</span>
            </button>
            <button
              onClick={() => setActiveTab("rows")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeTab === "rows"
                  ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              <Layout className="w-3.5 h-3.5" />
              <span>Rows & Margins</span>
            </button>
            <button
              onClick={() => setActiveTab("columns")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeTab === "columns"
                  ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Columns</span>
            </button>
          </div>

          {/* Controls Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
            {activeTab === "text" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Examination Header Title (Single Bold Line)
                  </label>
                  <textarea
                    rows={2}
                    value={config.exam_title}
                    onChange={(e) => setConfig({ ...config, exam_title: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-1 focus:ring-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">Appears at the very top of the marksheet in capital letters.</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      College Name
                    </label>
                    <input
                      type="text"
                      value={config.college_name}
                      onChange={(e) => setConfig({ ...config, college_name: e.target.value })}
                      className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Institute / University
                    </label>
                    <input
                      type="text"
                      value={config.institution_name}
                      onChange={(e) => setConfig({ ...config, institution_name: e.target.value })}
                      className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Issue Date
                    </label>
                    <input
                      type="text"
                      value={config.issue_date}
                      onChange={(e) => setConfig({ ...config, issue_date: e.target.value })}
                      className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Place
                    </label>
                    <input
                      type="text"
                      value={config.place}
                      onChange={(e) => setConfig({ ...config, place: e.target.value })}
                      className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>
                </div>

                <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-2 uppercase tracking-wide">
                    Signatory Titles
                  </h4>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-slate-400 font-medium">Signatory 1</span>
                      <input
                        type="text"
                        value={config.sig1_title}
                        onChange={(e) => setConfig({ ...config, sig1_title: e.target.value })}
                        className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white mt-0.5"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-medium">Signatory 2</span>
                      <input
                        type="text"
                        value={config.sig2_title}
                        onChange={(e) => setConfig({ ...config, sig2_title: e.target.value })}
                        className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white mt-0.5"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-medium">Signatory 3</span>
                      <input
                        type="text"
                        value={config.sig3_title}
                        onChange={(e) => setConfig({ ...config, sig3_title: e.target.value })}
                        className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white mt-0.5"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Statutory Disclaimer / Discrepancy Note
                  </label>
                  <textarea
                    rows={2}
                    value={config.statutory_note}
                    onChange={(e) => setConfig({ ...config, statutory_note: e.target.value })}
                    className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            )}

            {activeTab === "rows" && (
              <div className="space-y-4">
                {/* Top margin letterhead clearance */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Letterhead Top Margin Clearance
                    </label>
                    <span className="text-xs font-mono font-bold text-blue-600 dark:text-blue-400">
                      {config.top_margin}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1.0"
                    max="3.5"
                    step="0.1"
                    value={parseFloat(config.top_margin.replace("in", "")) || 2.5}
                    onChange={(e) => setConfig({ ...config, top_margin: `${e.target.value}in` })}
                    className="w-full accent-blue-600 cursor-pointer"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Standard SGPGIMS pre-printed institutional letterhead requires 2.5 inches clearance.
                  </p>
                </div>

                {/* Table Row Density */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Table Row Padding / Height
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {(["compact", "standard", "relaxed"] as const).map((density) => (
                      <button
                        key={density}
                        onClick={() => setConfig({ ...config, row_padding: density })}
                        className={`text-xs py-2 px-3 rounded-xl border font-medium capitalize transition-all ${
                          config.row_padding === density
                            ? "bg-blue-50 dark:bg-blue-950/60 border-blue-500 text-blue-700 dark:text-blue-300"
                            : "border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50"
                        }`}
                      >
                        {density}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Font Sizes */}
                <div className="border-t border-slate-100 dark:border-slate-800 pt-3 space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                    Typography Sizing
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="text-[11px] text-slate-400">Header Line</span>
                      <select
                        value={config.font_size_header}
                        onChange={(e) => setConfig({ ...config, font_size_header: e.target.value })}
                        className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white mt-1"
                      >
                        <option value="10pt">10 pt</option>
                        <option value="11pt">11 pt (Standard)</option>
                        <option value="12pt">12 pt</option>
                      </select>
                    </div>

                    <div>
                      <span className="text-[11px] text-slate-400">Marks Table Font</span>
                      <select
                        value={config.font_size_table}
                        onChange={(e) => setConfig({ ...config, font_size_table: e.target.value })}
                        className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white mt-1"
                      >
                        <option value="9pt">9 pt (Compact)</option>
                        <option value="9.5pt">9.5 pt</option>
                        <option value="10pt">10 pt (Standard)</option>
                        <option value="10.5pt">10.5 pt</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Paper Format */}
                <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Paper Print Size
                  </label>
                  <select
                    value={config.paper_size}
                    onChange={(e) => setConfig({ ...config, paper_size: e.target.value })}
                    className="w-full text-xs p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  >
                    <option value="8.5in 14in">Legal Format (8.5&quot; &times; 14&quot;) - Official SGPGIMS</option>
                    <option value="8.27in 11.69in">A4 Format (8.27&quot; &times; 11.69&quot;)</option>
                  </select>
                </div>
              </div>
            )}

            {activeTab === "columns" && (
              <div className="space-y-3">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Customize table column header text:
                </p>

                <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Sl.No. Header</span>
                    <input
                      type="text"
                      value={config.col_label_sno}
                      onChange={(e) => setConfig({ ...config, col_label_sno: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Course Code Header</span>
                    <input
                      type="text"
                      value={config.col_label_course_code}
                      onChange={(e) => setConfig({ ...config, col_label_course_code: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Title of Course Header</span>
                    <input
                      type="text"
                      value={config.col_label_course_title}
                      onChange={(e) => setConfig({ ...config, col_label_course_title: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Credits Header</span>
                    <input
                      type="text"
                      value={config.col_label_credits}
                      onChange={(e) => setConfig({ ...config, col_label_credits: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Internal Assessment Header</span>
                    <input
                      type="text"
                      value={config.col_label_internal}
                      onChange={(e) => setConfig({ ...config, col_label_internal: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">End Semester Exam Header</span>
                    <input
                      type="text"
                      value={config.col_label_external}
                      onChange={(e) => setConfig({ ...config, col_label_external: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 font-medium">Total Marks Header</span>
                    <input
                      type="text"
                      value={config.col_label_total}
                      onChange={(e) => setConfig({ ...config, col_label_total: e.target.value })}
                      className="w-full text-xs p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Live Preview Panel (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex flex-wrap justify-between items-center gap-3">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                Live Interactive Print Preview
              </span>
              {isLoadingPreview && (
                <span className="text-[11px] text-blue-500 animate-pulse font-medium">
                  Updating...
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {currentStudents.length > 0 && (
                <select
                  value={selectedStudentIdx}
                  onChange={(e) => setSelectedStudentIdx(parseInt(e.target.value, 10))}
                  className="text-xs py-1.5 px-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                >
                  {currentStudents.slice(0, 10).map((s, idx) => (
                    <option key={idx} value={idx}>
                      {s.student_name} ({s.roll_no})
                    </option>
                  ))}
                </select>
              )}

              <button
                onClick={handlePrint}
                className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print</span>
              </button>
            </div>
          </div>

          {/* Marksheet viewport */}
          <div className="bg-slate-200 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-2xl p-3 overflow-hidden shadow-inner flex justify-center">
            <div className="w-full max-w-[850px] bg-white rounded-lg shadow-xl overflow-hidden min-h-[700px] border border-slate-300">
              {previewHtml ? (
                <iframe
                  id="template-live-preview-iframe"
                  srcDoc={previewHtml}
                  className="w-full h-[780px] border-none"
                  title="Marksheet Live Preview"
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-[600px] text-slate-400 text-xs">
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-2"></div>
                  <span>Rendering live marksheet preview...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )}
</div>
);
};
