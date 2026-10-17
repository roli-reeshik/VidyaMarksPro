"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, Activity } from "lucide-react";
import { Navbar } from "../../../components/Navbar";
import { Footer } from "../../../components/Footer";
import { DiagnosticConsole } from "../../../components/DiagnosticConsole";
import { useAuth } from "../../../context/AuthContext";

export default function AdminDiagnosticsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/login");
      } else if (user.role !== "Admin") {
        router.push("/");
      }
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-700 flex items-center justify-center text-white shadow-xl shadow-emerald-600/30 animate-pulse">
            <Activity className="w-7 h-7" />
          </div>
          <div className="text-center">
            <h2 className="text-sm font-bold text-white tracking-wide">VidyaMarksheet Diagnostic Console</h2>
            <p className="text-xs text-slate-400 mt-1">Verifying System Administrator privileges...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar activeTab={"diagnostics" as any} setActiveTab={(tab) => router.push(`/?tab=${tab}`)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DiagnosticConsole />
      </main>

      <Footer />
    </div>
  );
}
