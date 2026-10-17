"use client";

import React, { useState } from "react";
import { ShieldCheck, CheckCircle2, AlertCircle, X, KeyRound, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose?: () => void;
  isForced?: boolean;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  isOpen,
  onClose,
  isForced = false,
}) => {
  const { user, updateUserMustChangePassword } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  // Real-time strength checks
  const checks = {
    length: newPassword.length >= 8,
    upper: /[A-Z]/.test(newPassword),
    lower: /[a-z]/.test(newPassword),
    digit: /\d/.test(newPassword),
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(newPassword),
    notUsername: user?.username ? newPassword.toLowerCase() !== user.username.toLowerCase() : true,
    match: newPassword.length > 0 && newPassword === confirmPassword,
  };

  const isFormValid =
    oldPassword.length > 0 &&
    checks.length &&
    checks.upper &&
    checks.lower &&
    checks.digit &&
    checks.special &&
    checks.notUsername &&
    checks.match;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid || loading) return;

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await fetch("/api/v1/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to update password.");
      }

      setSuccessMsg("Password updated successfully! Active sessions synchronized.");
      updateUserMustChangePassword(false);

      setTimeout(() => {
        setOldPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setSuccessMsg(null);
        if (onClose) onClose();
      }, 1500);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-lg bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl shadow-blue-950/40 overflow-hidden text-slate-100 relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Strip */}
        <div className="bg-gradient-to-r from-blue-900/80 via-indigo-900/80 to-blue-950 px-6 py-4 border-b border-blue-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-600/30 border border-blue-400/40 text-blue-300">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                {isForced ? "Security Action Required: Update Password" : "Change Institutional Password"}
              </h2>
              <p className="text-xs text-blue-200/80">
                {isForced
                  ? "First login detected. SGPGIMS Institutional Security Policy requires password rotation."
                  : "Rotate your credentials to maintain compliance with INC security guidelines."}
              </p>
            </div>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              title={isForced ? "Dismiss / Remind Later (Demo Mode)" : "Close"}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800/50 text-rose-200 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-800/50 text-emerald-200 text-xs flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Current Password */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Current Password
            </label>
            <div className="relative">
              <input
                type={showOldPassword ? "text" : "password"}
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                required
                placeholder="Enter current password"
                className="w-full px-3.5 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowOldPassword(!showOldPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
              >
                {showOldPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              New Password
            </label>
            <div className="relative">
              <input
                type={showNewPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                placeholder="Enter new strong password"
                className="w-full px-3.5 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200"
              >
                {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Confirm New Password */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Confirm new password"
              className="w-full px-3.5 py-2.5 bg-slate-800/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Institutional Password Policy Checklist */}
          <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 space-y-1.5 text-xs">
            <span className="font-semibold text-slate-400 block mb-1 text-[11px] uppercase tracking-wider">
              SGPGIMS Strong Password Requirements:
            </span>
            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              <span className={`flex items-center gap-1.5 ${checks.length ? "text-emerald-400" : "text-slate-500"}`}>
                <CheckCircle2 className="w-3.5 h-3.5" /> 8+ Characters
              </span>
              <span className={`flex items-center gap-1.5 ${checks.upper ? "text-emerald-400" : "text-slate-500"}`}>
                <CheckCircle2 className="w-3.5 h-3.5" /> 1+ Uppercase (A-Z)
              </span>
              <span className={`flex items-center gap-1.5 ${checks.lower ? "text-emerald-400" : "text-slate-500"}`}>
                <CheckCircle2 className="w-3.5 h-3.5" /> 1+ Lowercase (a-z)
              </span>
              <span className={`flex items-center gap-1.5 ${checks.digit ? "text-emerald-400" : "text-slate-500"}`}>
                <CheckCircle2 className="w-3.5 h-3.5" /> 1+ Digit (0-9)
              </span>
              <span className={`flex items-center gap-1.5 ${checks.special ? "text-emerald-400" : "text-slate-500"}`}>
                <CheckCircle2 className="w-3.5 h-3.5" /> 1+ Symbol (!@#$%^&*)
              </span>
              <span className={`flex items-center gap-1.5 ${checks.match ? "text-emerald-400" : "text-slate-500"}`}>
                <CheckCircle2 className="w-3.5 h-3.5" /> Passwords Match
              </span>
            </div>
          </div>

          {/* Submit Action */}
          <div className="pt-2 flex items-center justify-end gap-3">
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-colors ${
                  isForced
                    ? "text-amber-400 hover:text-amber-300 hover:bg-amber-950/40 border border-amber-800/40"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                {isForced ? "Remind Me Later (Demo Access)" : "Cancel"}
              </button>
            )}
            <button
              type="submit"
              disabled={!isFormValid || loading}
              className={`px-5 py-2.5 rounded-xl text-xs font-bold tracking-wide transition-all shadow-md flex items-center gap-2 ${
                isFormValid && !loading
                  ? "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-600/30"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{loading ? "Updating Credentials..." : "Update Password & Continue"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
