"use client";

import React from "react";
import { GraduationCap, FileSpreadsheet, Scale, BookOpen, Sliders, Eye, ShieldCheck, TableProperties } from "lucide-react";
import { INSTITUTIONAL_INFO } from "../data/semesterData";

export type NavTab = "upload" | "template" | "debug" | "audit" | "register" | "schemas" | "grading";

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white shadow-xl sticky top-0 z-50">
      {/* Top institutional strip */}
      <div className="bg-blue-950/80 px-4 py-1.5 border-b border-blue-900/50 text-xs text-blue-200 flex flex-wrap justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-semibold tracking-wide text-white">
            {INSTITUTIONAL_INFO.institution_name}
          </span>
          <span className="hidden md:inline text-blue-300">| Code: {INSTITUTIONAL_INFO.college_code}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="bg-emerald-950/80 text-emerald-300 px-2 py-0.5 rounded font-mono text-[11px] border border-emerald-700/50 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            PostgreSQL: vidya_examination_db
          </span>
          <span className="bg-blue-900/80 text-blue-200 px-2 py-0.5 rounded font-mono text-[11px] border border-blue-700/50">
            INC Gazette Compliant
          </span>
          <span className="hidden sm:inline text-slate-300 font-medium">
            Session: 2025–2026
          </span>
        </div>
      </div>

      {/* Main navigation header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-500 shadow-md shadow-blue-500/20 text-white flex items-center justify-center">
            <GraduationCap className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-blue-200 bg-clip-text text-transparent">
                VidyaMarksheet
              </h1>
              <span className="text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full uppercase tracking-wider">
                Phase 4 Pro
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              B.Sc. Nursing Examination Tabulation & Gazette Print Engine
            </p>
          </div>
        </div>

        {/* Tab switcher */}
        <nav className="flex flex-wrap items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 shadow-inner">
          <button
            onClick={() => setActiveTab("upload")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "upload"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-300 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Datasheet & Review</span>
          </button>

          <button
            onClick={() => setActiveTab("template")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "template"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-300 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Marksheet Template</span>
          </button>

          <button
            onClick={() => setActiveTab("debug")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "debug"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-300 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>5 Debug Previews</span>
          </button>

          <button
            onClick={() => setActiveTab("audit")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "audit"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-300 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>INC Gazette Audit</span>
          </button>

          <button
            onClick={() => setActiveTab("register")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "register"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-300 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <TableProperties className="w-3.5 h-3.5" />
            <span>Tabulation Register (TR)</span>
          </button>

          <button
            onClick={() => setActiveTab("schemas")}
            className={`hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "schemas"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Schemas</span>
          </button>

          <button
            onClick={() => setActiveTab("grading")}
            className={`hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "grading"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                : "text-slate-400 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>10-Point Scale</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
