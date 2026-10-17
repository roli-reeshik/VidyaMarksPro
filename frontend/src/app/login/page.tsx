"use client";

import React, { useState } from "react";
import { GraduationCap, ShieldCheck, Lock, User, AlertCircle, ArrowRight, ShieldAlert } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { INSTITUTIONAL_INFO } from "../../data/semesterData";

export default function LoginPage() {
  const { loginUser } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLocked, setIsLocked] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password || loading || isRedirecting) return;

    setLoading(true);
    setErrorMessage(null);
    setIsLocked(false);

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (res.status === 423) {
        setIsLocked(true);
        setErrorMessage(data.detail || "Account temporarily locked due to multiple failed login attempts.");
        setLoading(false);
        return;
      }

      if (!res.ok) {
        setErrorMessage(data.detail || "Invalid institutional credentials. Please try again.");
        setLoading(false);
        return;
      }

      // Success
      setIsRedirecting(true);
      loginUser(data.user);
    } catch {
      setErrorMessage("Network connection error. Ensure FastAPI backend is running on port 8000.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-3xl shadow-2xl shadow-blue-950/50 p-8 backdrop-blur-md relative z-10">
        {/* Header Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-500 shadow-lg shadow-blue-600/30 text-white mb-3.5">
            <GraduationCap className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">VidyaMarksheet</h1>
          <p className="text-xs text-blue-300 font-medium mt-1">
            {INSTITUTIONAL_INFO.institution_name}
          </p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <span className="text-[10px] font-mono bg-blue-950 text-blue-300 px-2.5 py-0.5 rounded-full border border-blue-800/60">
              College Code: {INSTITUTIONAL_INFO.college_code}
            </span>
            <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-2.5 py-0.5 rounded-full border border-emerald-800/60">
              INC Gazette Compliant
            </span>
          </div>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div
            className={`p-3.5 rounded-2xl border text-xs flex items-start gap-2.5 mb-5 ${
              isLocked
                ? "bg-amber-950/60 border-amber-700/60 text-amber-200"
                : "bg-rose-950/60 border-rose-800/60 text-rose-200"
            }`}
          >
            {isLocked ? (
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-semibold">{isLocked ? "Account Locked" : "Authentication Failed"}</p>
              <p className="mt-0.5 text-[11px] opacity-90">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Institutional Username / User ID
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                placeholder="Enter your Username or User ID"
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter password"
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || isRedirecting || !username || !password}
              className={`w-full py-3 rounded-xl text-xs font-bold tracking-wide transition-all shadow-lg flex items-center justify-center gap-2 ${
                !loading && !isRedirecting && username && password
                  ? "bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-600/30"
                  : isRedirecting
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-emerald-600/30"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>
                {isRedirecting
                  ? "Authenticated! Opening Portal..."
                  : loading
                  ? "Authenticating Session..."
                  : "Secure Login to Portal"}
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>

        {/* Security Notice Footer */}
        <div className="mt-8 pt-4 border-t border-slate-800/80 text-center">
          <p className="text-[11px] text-slate-500">
            Protected by Enterprise RBAC & Brute-Force Rate Limiting.
          </p>
          <p className="text-[10px] text-slate-600 mt-1">
            Developed at VidyaLabs | Priyanka Kumari
          </p>
        </div>
      </div>
    </div>
  );
}
