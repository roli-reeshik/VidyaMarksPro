"use client";

import React from "react";
import Link from "next/link";
import {
  GraduationCap,
  FileSpreadsheet,
  Scale,
  BookOpen,
  Sliders,
  Eye,
  ShieldCheck,
  TableProperties,
  User,
  Users,
  KeyRound,
  LogOut,
  LogIn,
  BarChart3,
  MessageSquare,
  FileCheck,
  ShieldAlert,
  Activity,
} from "lucide-react";
import { INSTITUTIONAL_INFO } from "../data/semesterData";
import { useAuth } from "../context/AuthContext";
import { FeedbackModal } from "./FeedbackModal";

export type NavTab =
  | "dashboard"
  | "upload"
  | "scrutiny"
  | "remediations"
  | "template"
  | "debug"
  | "audit"
  | "register"
  | "feedback"
  | "users"
  | "diagnostics"
  | "schemas"
  | "grading";

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

const getRoleBadgeStyle = (role: string) => {
  switch (role) {
    case "Admin":
      return "bg-rose-500/25 text-rose-200 border-rose-500/50";
    case "SubDean":
      return "bg-indigo-500/25 text-indigo-200 border-indigo-500/50";
    case "Scrutiny":
      return "bg-amber-500/25 text-amber-200 border-amber-500/50";
    case "Operator":
      return "bg-blue-500/25 text-blue-200 border-blue-500/50";
    case "Faculty":
      return "bg-emerald-500/25 text-emerald-200 border-emerald-500/50";
    default:
      return "bg-slate-500/25 text-slate-300 border-slate-500/50";
  }
};

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const { user, logoutUser, setIsPasswordModalOpen } = useAuth();
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = React.useState<boolean>(false);

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white shadow-xl sticky top-0 z-50">
      {/* Top institutional strip */}
      <div className="bg-blue-950/90 px-4 py-1.5 border-b border-blue-900/60 text-xs text-blue-200 flex flex-wrap justify-between items-center gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-semibold tracking-wide text-white">
            {INSTITUTIONAL_INFO.institution_name}
          </span>
          <span className="hidden md:inline text-blue-300">| Code: {INSTITUTIONAL_INFO.college_code}</span>
        </div>

        {/* User Profile & Auth Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Universal Feedback Trigger */}
          <button
            onClick={() => setIsFeedbackModalOpen(true)}
            className="flex items-center gap-1.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white px-2.5 py-0.5 rounded text-[11px] font-semibold transition-all shadow-sm shadow-amber-600/30 cursor-pointer"
          >
            <MessageSquare className="w-3 h-3" />
            <span>Feedback & Suggestions</span>
          </button>

          {user ? (
            <>
              <div className="flex items-center gap-2 bg-slate-900/80 px-2.5 py-0.5 rounded-lg border border-slate-800">
                <User className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-medium text-white text-[11px]">{user.full_name}</span>
                <span
                  className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${getRoleBadgeStyle(
                    user.role
                  )}`}
                >
                  {user.role}
                </span>
              </div>

              <button
                onClick={() => setIsPasswordModalOpen(true)}
                title="Change Institutional Password"
                className="flex items-center gap-1 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 hover:text-white px-2 py-0.5 rounded text-[11px] border border-slate-700/60 transition-colors"
              >
                <KeyRound className="w-3 h-3 text-amber-400" />
                <span className="hidden sm:inline">Change Password</span>
              </button>

              <button
                onClick={logoutUser}
                title="Logout Session"
                className="flex items-center gap-1 bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 hover:text-rose-100 px-2 py-0.5 rounded text-[11px] border border-rose-800/50 transition-colors"
              >
                <LogOut className="w-3 h-3" />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-0.5 rounded text-[11px] font-semibold transition-colors shadow-sm"
            >
              <LogIn className="w-3 h-3" />
              <span>Sign In</span>
            </Link>
          )}

          <span className="bg-emerald-950/80 text-emerald-300 px-2 py-0.5 rounded font-mono text-[11px] border border-emerald-700/50 hidden lg:flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            PostgreSQL: vidya_examination_db
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
            onClick={() => setActiveTab("dashboard")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "dashboard"
                ? "bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-md shadow-indigo-600/30"
                : "text-indigo-300 hover:text-white hover:bg-slate-700/60"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Analytics Dashboard</span>
          </button>

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
            onClick={() => setActiveTab("scrutiny")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "scrutiny"
                ? "bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-md shadow-indigo-600/30"
                : "text-indigo-300 hover:text-white hover:bg-slate-700/60 border border-indigo-500/30"
            }`}
          >
            <FileCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>Scrutiny Studio</span>
          </button>

          {(user?.role === "Admin" || user?.role === "Sub-Dean" || user?.role === "SubDean") && (
            <button
              onClick={() => setActiveTab("remediations")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "remediations"
                  ? "bg-gradient-to-r from-rose-600 to-amber-600 text-white shadow-md shadow-rose-600/30"
                  : "text-rose-300 hover:text-white hover:bg-rose-950/40 border border-rose-800/40"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Remediations</span>
            </button>
          )}

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

          {(user?.role === "Admin" || user?.role === "Sub-Dean" || user?.role === "SubDean") && (
            <button
              onClick={() => setActiveTab("feedback")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "feedback"
                  ? "bg-amber-600 text-white shadow-md shadow-amber-600/30"
                  : "text-amber-300 hover:text-white hover:bg-amber-950/40 border border-amber-800/40"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
              <span>Feedback Console</span>
            </button>
          )}

          {user?.role === "Admin" && (
            <button
              onClick={() => setActiveTab("users")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "users"
                  ? "bg-rose-600 text-white shadow-md shadow-rose-600/30"
                  : "text-rose-300 hover:text-white hover:bg-rose-950/40 border border-rose-800/40"
              }`}
            >
              <Users className="w-3.5 h-3.5 text-rose-400" />
              <span>User Management</span>
            </button>
          )}

          {user?.role === "Admin" && (
            <button
              onClick={() => setActiveTab("diagnostics")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "diagnostics"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                  : "text-emerald-300 hover:text-white hover:bg-emerald-950/40 border border-emerald-800/40"
              }`}
            >
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span>Diagnostic Suite</span>
            </button>
          )}

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

      <FeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
      />
    </header>
  );
};
