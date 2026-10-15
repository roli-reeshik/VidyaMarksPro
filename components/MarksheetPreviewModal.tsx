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
  Pencil
} from "lucide-react";
import { EvaluatedStudentRecord } from "../types/marksheet";
import {
  MarksheetRenderer,
  LayoutStudioConfig,
  DEFAULT_LAYOUT_CONFIG,
  getStoredLayoutConfig
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
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
