"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  KeyRound,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Lock,
  RefreshCw,
  Search,
  X,
  UserCheck,
  UserX,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface ManagedUser {
  id: number;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  must_change_password: boolean;
  failed_login_attempts: number;
  is_locked: boolean;
  created_at?: string;
  last_login_at?: string;
}

interface AuditLogEntry {
  id: number;
  username: string;
  action: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
}

const AVAILABLE_ROLES = [
  {
    role: "Faculty",
    label: "Faculty (Evaluator)",
    description: "Evaluates student courses, verifies marks, and previews semester marksheets.",
    badgeClass: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  },
  {
    role: "Operator",
    label: "Operator (Data Entry & Ledger)",
    description: "Uploads datasheets, manages student records, and generates tabulation registers.",
    badgeClass: "bg-blue-500/20 text-blue-300 border-blue-500/40",
  },
  {
    role: "SubDean",
    label: "Sub-Dean (Approval & Lock)",
    description: "Approve semester registrations, final delivery locks, and executive overrides.",
    badgeClass: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
  },
  {
    role: "Viewer",
    label: "Viewer (Read-Only)",
    description: "Read-only access for institutional observers, students, or guest auditors.",
    badgeClass: "bg-slate-500/20 text-slate-300 border-slate-500/40",
  },
  {
    role: "Scrutiny",
    label: "Scrutiny (Audit & Review)",
    description: "Validates moderation, cross-checks calculations against INC Gazette criteria.",
    badgeClass: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  },
  {
    role: "Admin",
    label: "Admin (Full Control)",
    description: "Full system control, institutional user management, and security policies.",
    badgeClass: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  },
];

export const UserManagementView: React.FC = () => {
  const { user: currentAdmin } = useAuth();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("ALL");

  // Create User Form State
  const [newUsername, setNewUsername] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newRole, setNewRole] = useState("Faculty");
  const [newPassword, setNewPassword] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  // Reset Password Modal State
  const [resetTargetUser, setResetTargetUser] = useState<ManagedUser | null>(null);
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [isResetting, setIsResetting] = useState(false);

  // Fetch Users List
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/users", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      } else {
        setActionMessage({ text: "Failed to load user roster.", type: "error" });
      }
    } catch {
      setActionMessage({ text: "Network error loading users.", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  // Fetch Security Audit Logs
  const fetchAuditLogs = async () => {
    try {
      const res = await fetch("/api/v1/auth/audit-logs?limit=30", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch {
      // Ignore background log fetch error
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchAuditLogs();
  }, []);

  // Handle Create User
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || !newFullName.trim() || !newPassword) {
      setActionMessage({ text: "Please fill in all required fields.", type: "error" });
      return;
    }

    setIsCreating(true);
    setActionMessage(null);

    try {
      const res = await fetch("/api/v1/auth/admin/create-user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          username: newUsername.trim(),
          full_name: newFullName.trim(),
          role: newRole,
          password: newPassword,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setActionMessage({
          text: `User '${newUsername}' successfully created with role '${newRole}'.`,
          type: "success",
        });
        setNewUsername("");
        setNewFullName("");
        setNewPassword("");
        setNewRole("Faculty");
        fetchUsers();
        fetchAuditLogs();
      } else {
        setActionMessage({ text: data.detail || "Failed to create user.", type: "error" });
      }
    } catch {
      setActionMessage({ text: "Network error while creating user.", type: "error" });
    } finally {
      setIsCreating(false);
    }
  };

  // Handle Role Change
  const handleUpdateRole = async (userId: number, newAssignedRole: string) => {
    try {
      const res = await fetch(`/api/v1/auth/admin/users/${userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ user_id: userId, role: newAssignedRole }),
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage({ text: `Role updated to '${newAssignedRole}'.`, type: "success" });
        fetchUsers();
        fetchAuditLogs();
      } else {
        setActionMessage({ text: data.detail || "Failed to update role.", type: "error" });
      }
    } catch {
      setActionMessage({ text: "Network error while updating role.", type: "error" });
    }
  };

  // Handle Toggle Active/Inactive
  const handleToggleActive = async (targetUser: ManagedUser) => {
    if (targetUser.username.toLowerCase() === currentAdmin?.username.toLowerCase()) {
      setActionMessage({ text: "You cannot deactivate your own active admin account.", type: "error" });
      return;
    }

    try {
      const res = await fetch(`/api/v1/auth/admin/users/${targetUser.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ user_id: targetUser.id, is_active: !targetUser.is_active }),
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage({
          text: `User '${targetUser.username}' is now ${!targetUser.is_active ? "Active" : "Deactivated"}.`,
          type: "success",
        });
        fetchUsers();
        fetchAuditLogs();
      } else {
        setActionMessage({ text: data.detail || "Failed to update user status.", type: "error" });
      }
    } catch {
      setActionMessage({ text: "Network error while updating user status.", type: "error" });
    }
  };

  // Handle Delete User
  const handleDeleteUser = async (targetUser: ManagedUser) => {
    if (targetUser.username.toLowerCase() === currentAdmin?.username.toLowerCase()) {
      setActionMessage({ text: "You cannot delete your own admin account.", type: "error" });
      return;
    }

    if (!confirm(`Are you sure you want to permanently delete user '${targetUser.username}' (${targetUser.full_name})?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/v1/auth/admin/users/${targetUser.id}`, {
        method: "DELETE",
        credentials: "include",
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage({ text: `User '${targetUser.username}' deleted successfully.`, type: "success" });
        fetchUsers();
        fetchAuditLogs();
      } else {
        setActionMessage({ text: data.detail || "Failed to delete user.", type: "error" });
      }
    } catch {
      setActionMessage({ text: "Network error while deleting user.", type: "error" });
    }
  };

  // Handle Password Reset
  const handleResetPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetTargetUser || !resetNewPassword) return;

    setIsResetting(true);
    try {
      const res = await fetch("/api/v1/auth/admin/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          target_username: resetTargetUser.username,
          new_password: resetNewPassword,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage({
          text: `Password for '${resetTargetUser.username}' reset successfully.`,
          type: "success",
        });
        setResetTargetUser(null);
        setResetNewPassword("");
        fetchUsers();
        fetchAuditLogs();
      } else {
        setActionMessage({ text: data.detail || "Failed to reset password.", type: "error" });
      }
    } catch {
      setActionMessage({ text: "Network error while resetting password.", type: "error" });
    } finally {
      setIsResetting(false);
    }
  };

  // Filtered Users
  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "ALL" || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const getRoleBadge = (roleName: string) => {
    const roleDef = AVAILABLE_ROLES.find((r) => r.role === roleName);
    return roleDef ? roleDef.badgeClass : "bg-slate-500/20 text-slate-300 border-slate-500/40";
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Institutional User Administration & RBAC Engine
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Admin Privilege: Create institutional users by Name and User ID, grant access as per role (Faculty, Operator, Sub-Dean, Viewer), and manage security credentials.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => {
            fetchUsers();
            fetchAuditLogs();
          }}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-xl border border-slate-700 text-xs font-semibold transition-all shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-blue-400" : ""}`} />
          <span>Refresh Roster</span>
        </button>
      </div>

      {/* Action Notification Alert */}
      {actionMessage && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-medium shadow-md ${
            actionMessage.type === "success"
              ? "bg-emerald-950/70 border-emerald-700/60 text-emerald-200"
              : "bg-rose-950/70 border-rose-700/60 text-rose-200"
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMessage.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionMessage.text}</span>
          </div>
          <button
            onClick={() => setActionMessage(null)}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Role Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {AVAILABLE_ROLES.map((r) => {
          const count = users.filter((u) => u.role === r.role).length;
          return (
            <div
              key={r.role}
              onClick={() => setRoleFilter(roleFilter === r.role ? "ALL" : r.role)}
              className={`cursor-pointer p-3.5 rounded-xl border transition-all ${
                roleFilter === r.role
                  ? "bg-blue-950/60 border-blue-500 ring-2 ring-blue-500/30"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${r.badgeClass}`}>
                  {r.role}
                </span>
                <span className="text-base font-bold text-white">{count}</span>
              </div>
              <p className="text-[10px] text-slate-400 mt-2 font-medium line-clamp-1">{r.label}</p>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Create User Form + User Roster Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Create New User Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl h-fit">
          <div className="flex items-center gap-2.5 pb-4 border-b border-slate-800 mb-5">
            <div className="p-2 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30">
              <UserPlus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Create New User</h3>
              <p className="text-[11px] text-slate-400">Assign Institutional Role & Access</p>
            </div>
          </div>

          <form onSubmit={handleCreateUser} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Full Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={newFullName}
                onChange={(e) => setNewFullName(e.target.value)}
                placeholder="e.g. Dr. Sunita Rao"
                required
                className="w-full px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Institutional Username / User ID <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                placeholder="e.g. faculty_srao or FAC001"
                required
                className="w-full px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <p className="text-[10px] text-slate-500 mt-1">Unique institutional login identifier</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Grant Access Role <span className="text-rose-400">*</span>
              </label>
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
              >
                {AVAILABLE_ROLES.map((r) => (
                  <option key={r.role} value={r.role} className="bg-slate-900 text-white">
                    {r.label}
                  </option>
                ))}
              </select>
              <p className="text-[10px] text-blue-400/90 mt-1.5 leading-relaxed bg-blue-950/40 p-2 rounded-lg border border-blue-900/40">
                {AVAILABLE_ROLES.find((r) => r.role === newRole)?.description}
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Initial Password <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="e.g. Temp@1234 or custom"
                required
                className="w-full px-3 py-2 bg-slate-800/90 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
            </div>

            <button
              type="submit"
              disabled={isCreating || !newUsername || !newFullName || !newPassword}
              className="w-full py-2.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-blue-600/30 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <UserPlus className="w-4 h-4" />
              <span>{isCreating ? "Creating Account..." : "Create User & Grant Role"}</span>
            </button>
          </form>
        </div>

        {/* Right Column: User Roster Table */}
        <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800 mb-5">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  Institutional Users Roster
                  <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700 font-mono">
                    {filteredUsers.length} Users
                  </span>
                </h3>
                <p className="text-[11px] text-slate-400">All registered institutional accounts</p>
              </div>

              {/* Search & Filter */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search name or user ID..."
                    className="pl-8 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-48 sm:w-56"
                  />
                </div>

                {roleFilter !== "ALL" && (
                  <button
                    onClick={() => setRoleFilter("ALL")}
                    className="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700 flex items-center gap-1"
                  >
                    <span>Clear Filter ({roleFilter})</span>
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider bg-slate-950/40">
                    <th className="py-2.5 px-3">User & ID</th>
                    <th className="py-2.5 px-3">Granted Role</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Admin Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-slate-500 text-xs">
                        No users match the specified criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((u) => {
                      const isCurrent = u.username.toLowerCase() === currentAdmin?.username.toLowerCase();
                      return (
                        <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="py-3 px-3">
                            <div className="flex items-center gap-2.5">
                              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white text-[11px] shrink-0">
                                {u.full_name ? u.full_name.charAt(0).toUpperCase() : u.username.charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <p className="font-semibold text-white flex items-center gap-1.5">
                                  {u.full_name}
                                  {isCurrent && (
                                    <span className="text-[9px] bg-blue-900/60 text-blue-300 border border-blue-700/60 px-1.5 rounded">
                                      You
                                    </span>
                                  )}
                                </p>
                                <p className="text-[11px] font-mono text-slate-400">@{u.username}</p>
                              </div>
                            </div>
                          </td>

                          <td className="py-3 px-3">
                            <div className="flex items-center gap-2">
                              <select
                                value={u.role}
                                disabled={isCurrent}
                                onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                                className={`text-[11px] font-semibold px-2 py-0.5 rounded border focus:outline-none focus:ring-2 focus:ring-blue-500 ${getRoleBadge(
                                  u.role
                                )} bg-slate-900 disabled:opacity-80`}
                              >
                                {AVAILABLE_ROLES.map((r) => (
                                  <option key={r.role} value={r.role} className="bg-slate-900 text-white">
                                    {r.role}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </td>

                          <td className="py-3 px-3">
                            <div className="flex items-center gap-1.5">
                              {u.is_locked ? (
                                <span className="inline-flex items-center gap-1 text-[10px] bg-amber-950/80 text-amber-300 border border-amber-700/60 px-2 py-0.5 rounded-full font-semibold">
                                  <Lock className="w-2.5 h-2.5" /> Locked
                                </span>
                              ) : u.is_active ? (
                                <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 px-2 py-0.5 rounded-full font-semibold">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Active
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-[10px] bg-rose-950/80 text-rose-300 border border-rose-700/60 px-2 py-0.5 rounded-full font-semibold">
                                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span> Deactivated
                                </span>
                              )}
                            </div>
                          </td>

                          <td className="py-3 px-3 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              {/* Reset Password Button */}
                              <button
                                onClick={() => {
                                  setResetTargetUser(u);
                                  setResetNewPassword("");
                                }}
                                title="Reset Password"
                                className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition-colors"
                              >
                                <KeyRound className="w-3.5 h-3.5 text-amber-400" />
                              </button>

                              {/* Toggle Active / Deactivate */}
                              {!isCurrent && (
                                <button
                                  onClick={() => handleToggleActive(u)}
                                  title={u.is_active ? "Deactivate User" : "Activate User"}
                                  className={`p-1.5 rounded-lg border transition-colors ${
                                    u.is_active
                                      ? "bg-slate-800 hover:bg-amber-950/60 text-slate-300 hover:text-amber-300 border-slate-700"
                                      : "bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 border-emerald-800/60"
                                  }`}
                                >
                                  {u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                                </button>
                              )}

                              {/* Delete User */}
                              {!isCurrent && (
                                <button
                                  onClick={() => handleDeleteUser(u)}
                                  title="Delete Account"
                                  className="p-1.5 bg-slate-800 hover:bg-rose-950/60 text-slate-300 hover:text-rose-400 rounded-lg border border-slate-700 transition-colors"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Security Audit Log Preview */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white">Recent Security & RBAC Audit Trail</h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Chronological Security Audit</span>
        </div>

        <div className="overflow-x-auto max-h-48">
          <table className="w-full text-left text-[11px]">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800 bg-slate-950/30">
                <th className="py-2 px-3">Timestamp</th>
                <th className="py-2 px-3">Username</th>
                <th className="py-2 px-3">Action</th>
                <th className="py-2 px-3">Details / User Agent</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 font-mono">
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-4 text-center text-slate-500">
                    No security events logged yet.
                  </td>
                </tr>
              ) : (
                auditLogs.slice(0, 10).map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/30 text-slate-300">
                    <td className="py-1.5 px-3 text-slate-400 whitespace-nowrap">
                      {l.timestamp ? new Date(l.timestamp).toLocaleString() : "-"}
                    </td>
                    <td className="py-1.5 px-3 font-semibold text-white">{l.username || "-"}</td>
                    <td className="py-1.5 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          l.action === "LOGIN_SUCCESS"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800/50"
                            : l.action.includes("USER_")
                            ? "bg-blue-950 text-blue-300 border border-blue-800/50"
                            : l.action === "LOCKED_OUT"
                            ? "bg-amber-950 text-amber-300 border border-amber-800/50"
                            : "bg-rose-950 text-rose-300 border border-rose-800/50"
                        }`}
                      >
                        {l.action}
                      </span>
                    </td>
                    <td className="py-1.5 px-3 text-slate-400 truncate max-w-xs">{l.user_agent}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Reset Password Modal */}
      {resetTargetUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl relative">
            <button
              onClick={() => setResetTargetUser(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-500/30">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Reset User Password</h4>
                <p className="text-xs text-slate-400">
                  Target User: <strong>{resetTargetUser.full_name}</strong> (@{resetTargetUser.username})
                </p>
              </div>
            </div>

            <form onSubmit={handleResetPasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  New Strong Password
                </label>
                <input
                  type="password"
                  value={resetNewPassword}
                  onChange={(e) => setResetNewPassword(e.target.value)}
                  placeholder="Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 symbol"
                  required
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setResetTargetUser(null)}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isResetting || !resetNewPassword}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-blue-600/30 disabled:opacity-50"
                >
                  {isResetting ? "Updating..." : "Confirm Password Reset"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
