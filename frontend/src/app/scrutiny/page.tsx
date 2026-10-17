"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap } from "lucide-react";
import { Navbar, NavTab } from "../../components/Navbar";
import { ScrutinyVerificationStudio } from "../../components/ScrutinyStudio/ScrutinyVerificationStudio";
import { useAuth } from "../../context/AuthContext";

export default function ScrutinyPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const handleTabChange = (tab: NavTab) => {
    if (tab === ("scrutiny" as any)) {
      // already on scrutiny
    } else {
      router.push(`/?tab=${tab}`);
    }
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-xl shadow-indigo-600/30 animate-pulse">
            <GraduationCap className="w-7 h-7" />
          </div>
          <div className="text-center">
            <h2 className="text-sm font-bold text-white tracking-wide">VidyaMarksheet Scrutiny Studio</h2>
            <p className="text-xs text-blue-300/80 mt-1">Verifying institutional scrutiny credentials...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <Navbar activeTab={"scrutiny" as any} setActiveTab={handleTabChange} />
      <main className="flex-1">
        <ScrutinyVerificationStudio />
      </main>
    </div>
  );
}
