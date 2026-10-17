"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, ShieldAlert, KeyRound } from "lucide-react";
import { Navbar, NavTab } from "../../components/Navbar";
import { Footer } from "../../components/Footer";
import { ExecutiveDashboard } from "../../components/Dashboard/ExecutiveDashboard";
import { ChangePasswordModal } from "../../components/ChangePasswordModal";
import { useAuth } from "../../context/AuthContext";

export default function DashboardPage() {
  const { user, loading, isPasswordModalOpen, setIsPasswordModalOpen } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard" as any);
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const handleTabChange = (tab: NavTab) => {
    if (tab === "dashboard") {
      setActiveTab("dashboard");
    } else {
      router.push(`/?tab=${tab}`);
    }
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-500 flex items-center justify-center text-white shadow-xl shadow-blue-600/30 animate-pulse">
            <GraduationCap className="w-7 h-7" />
          </div>
          <div className="text-center">
            <h2 className="text-sm font-bold text-white tracking-wide">VidyaMarksheet Dashboard</h2>
            <p className="text-xs text-blue-300/80 mt-1">Verifying institutional authorization...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar activeTab={"dashboard" as any} setActiveTab={handleTabChange} />

      {user?.must_change_password && (
        <div className="bg-gradient-to-r from-amber-950/80 via-orange-950/70 to-amber-950/80 border-b border-amber-800/60 px-4 py-2 text-xs text-amber-200 flex flex-wrap items-center justify-between gap-2 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Security Policy:</strong> Initial default password in use for <strong>{user.username}</strong> ({user.role}).
            </span>
          </div>
          <button
            onClick={() => setIsPasswordModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1 bg-amber-600/30 hover:bg-amber-600/50 text-amber-200 hover:text-white border border-amber-500/40 rounded-lg text-xs font-semibold transition-all shadow-sm"
          >
            <KeyRound className="w-3.5 h-3.5 text-amber-300" />
            <span>Update Password Now</span>
          </button>
        </div>
      )}

      <ChangePasswordModal
        isOpen={isPasswordModalOpen}
        isForced={user?.must_change_password ?? false}
        onClose={() => setIsPasswordModalOpen(false)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ExecutiveDashboard />
      </main>

      <Footer />
    </div>
  );
}
