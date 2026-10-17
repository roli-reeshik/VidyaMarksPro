"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  MessageSquare,
  Filter,
  CheckCircle2,
  Clock,
  Star,
  RefreshCw,
  Search,
  AlertTriangle,
  ChevronRight,
  User,
  ShieldCheck,
  FileEdit,
  Archive,
  BarChart3,
  X,
  Send,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface FeedbackItem {
  id: number;
  user_id: number | null;
  username: string;
  user_role: string;
  category: string;
  subject: string;
  feedback_text: string;
  rating: number;
  status: string;
  admin_notes: string | null;
  submitted_at: string | null;
  resolved_at: string | null;
}

interface FeedbackSummaryKPIs {
  total_submitted: number;
  pending_review: number;
  resolved_count: number;
  archived_count: number;
  average_rating: number;
}

export const FeedbackAdminView: React.FC = () => {
  const { user } = useAuth();
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [kpis, setKpis] = useState<FeedbackSummaryKPIs | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");

  // Active modal for editing status / admin notes
  const [activeFeedback, setActiveFeedback] = useState<FeedbackItem | null>(null);
  const [editStatus, setEditStatus] = useState<string>("NEW");
  const [editAdminNotes, setEditAdminNotes] = useState<string>("");
  const [isUpdating, setIsUpdating] = useState<boolean>(false);
  const [updateSuccess, setUpdateSuccess] = useState<string | null>(null);

  const fetchFeedbackData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch summary KPIs
      const kpiRes = await fetch("/api/v1/feedback/summary", { credentials: "include" });
      if (kpiRes.ok) {
        const kpiData = await kpiRes.json();
        setKpis(kpiData.kpis);
      }

      // 2. Fetch list with filters
      const params = new URLSearchParams();
      if (selectedCategory !== "all") params.append("category", selectedCategory);
      if (selectedStatus !== "all") params.append("status", selectedStatus);

      const listRes = await fetch(`/api/v1/feedback/all?${params.toString()}`, {
        credentials: "include",
      });

      if (!listRes.ok) {
        const errData = await listRes.json();
        throw new Error(errData.detail || "Failed to fetch feedback list.");
      }

      const listData = await listRes.json();
      setFeedbacks(listData.feedbacks || []);
    } catch (err: any) {
      setError(err.message || "Failed to load feedback records.");
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedStatus]);

  useEffect(() => {
    fetchFeedbackData();
  }, [fetchFeedbackData]);

  const handleOpenDetailModal = (item: FeedbackItem) => {
    setActiveFeedback(item);
    setEditStatus(item.status);
    setEditAdminNotes(item.admin_notes || "");
    setUpdateSuccess(null);
  };

  const handleSaveStatus = async () => {
    if (!activeFeedback) return;
    setIsUpdating(true);
    setUpdateSuccess(null);
    try {
      const res = await fetch(`/api/v1/feedback/${activeFeedback.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          status: editStatus,
          admin_notes: editAdminNotes.trim(),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to update feedback status.");
      }

      setUpdateSuccess("Feedback status and administrative notes updated successfully.");
      // Refresh list
      fetchFeedbackData();
      setTimeout(() => {
        setActiveFeedback(null);
      }, 1200);
    } catch (err: any) {
      alert(err.message || "Update failed.");
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case "RESOLVED":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      case "UNDER_REVIEW":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "ARCHIVED":
        return "bg-slate-500/20 text-slate-300 border-slate-500/40";
      default:
        return "bg-blue-500/20 text-blue-300 border-blue-500/40";
    }
  };

  const filteredFeedbacks = feedbacks.filter((f) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      f.subject.toLowerCase().includes(term) ||
      f.username.toLowerCase().includes(term) ||
      f.feedback_text.toLowerCase().includes(term) ||
      f.category.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-indigo-600/30 border border-indigo-500/40 text-indigo-400">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                Universal Feedback & Suggestion Registry
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Admin Exclusive
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Review, classify, and track institutional feedback submitted across faculty and student workflows.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchFeedbackData}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700/80 text-slate-200 hover:text-white rounded-xl text-xs font-semibold border border-slate-700 transition-all shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* KPI Cards Strip */}
      {kpis && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Total Submissions
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-mono">{kpis.total_submitted}</span>
              <span className="text-xs text-indigo-400 font-semibold bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                All Roles
              </span>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Pending Review
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-amber-400 font-mono">{kpis.pending_review}</span>
              <span className="text-xs text-amber-400 font-semibold bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Action Required
              </span>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Resolved Tickets
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-emerald-400 font-mono">{kpis.resolved_count}</span>
              <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                Completed
              </span>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-lg backdrop-blur-sm">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Average System Rating
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold text-amber-300 font-mono">
                {kpis.average_rating} / 5.0
              </span>
              <div className="flex items-center text-amber-400">
                <Star className="w-4 h-4 fill-amber-400" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Categories</option>
              <option value="UI/UX Improvement">UI/UX Improvement</option>
              <option value="Calculation/Grading Discrepancy">Calculation/Grading Discrepancy</option>
              <option value="Feature Request">Feature Request</option>
              <option value="Bug/Defect">Bug/Defect</option>
              <option value="General Feedback">General Feedback</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Statuses</option>
              <option value="NEW">NEW</option>
              <option value="UNDER_REVIEW">UNDER_REVIEW</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="ARCHIVED">ARCHIVED</option>
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search feedback text, subject, user..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Main Feedback Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-400 mb-2" />
            <span>Loading institutional feedback records...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-300 text-xs">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-rose-400" />
            <span>{error}</span>
          </div>
        ) : filteredFeedbacks.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <span className="font-semibold text-slate-300">No feedback entries found.</span>
            <p className="text-slate-500 mt-1">All recommendations have been processed or no entries match criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Submitter</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Subject</th>
                  <th className="py-3 px-4">Rating</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Submitted At</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredFeedbacks.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-400">#{item.id}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{item.username}</span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {item.user_role}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-lg text-[11px] bg-slate-800 text-slate-300 border border-slate-700">
                        {item.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-200 max-w-xs truncate" title={item.subject}>
                      {item.subject}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1 text-amber-400">
                        <Star className="w-3.5 h-3.5 fill-amber-400" />
                        <span className="font-bold">{item.rating}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getStatusBadgeStyle(
                          item.status
                        )}`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {item.submitted_at ? new Date(item.submitted_at).toLocaleDateString() : "-"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetailModal(item)}
                        className="px-2.5 py-1 bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 hover:text-white rounded-lg border border-indigo-500/40 text-[11px] font-semibold transition-all inline-flex items-center gap-1"
                      >
                        <FileEdit className="w-3 h-3" />
                        <span>Review</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Feedback Detail & Action Modal */}
      {activeFeedback && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-indigo-950 via-slate-900 to-indigo-950 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-600/30 border border-indigo-500/40 rounded-xl text-indigo-400">
                  <FileEdit className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Feedback Review #{activeFeedback.id}</h3>
                  <p className="text-xs text-slate-400">
                    Category: {activeFeedback.category} | Submitter: {activeFeedback.username} ({activeFeedback.user_role})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveFeedback(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4">
              {updateSuccess && (
                <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 rounded-xl text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{updateSuccess}</span>
                </div>
              )}

              {/* Subject & Submitter Banner */}
              <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400">Subject:</span>
                  <div className="flex items-center gap-1 text-amber-400 text-xs font-bold">
                    <Star className="w-4 h-4 fill-amber-400" />
                    <span>{activeFeedback.rating} / 5 Stars</span>
                  </div>
                </div>
                <h4 className="text-sm font-bold text-white">{activeFeedback.subject}</h4>
                <div className="text-xs text-slate-300 pt-2 border-t border-slate-800/80 whitespace-pre-wrap">
                  {activeFeedback.feedback_text}
                </div>
              </div>

              {/* Status Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Update Ticket Status
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {["NEW", "UNDER_REVIEW", "RESOLVED", "ARCHIVED"].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setEditStatus(st)}
                      className={`py-2 px-3 rounded-xl text-xs font-bold transition-all border ${
                        editStatus === st
                          ? "bg-indigo-600 text-white border-indigo-400 shadow-lg shadow-indigo-600/30"
                          : "bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Internal Admin Notes */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Internal Administrative Notes & Remediation Action
                </label>
                <textarea
                  rows={3}
                  placeholder="Record resolution notes, code changes, or follow-up instructions..."
                  value={editAdminNotes}
                  onChange={(e) => setEditAdminNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              {/* Footer */}
              <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setActiveFeedback(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 rounded-xl"
                >
                  Close
                </button>
                <button
                  type="button"
                  disabled={isUpdating}
                  onClick={handleSaveStatus}
                  className="px-5 py-2 text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 rounded-xl shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isUpdating ? <span>Updating...</span> : <span>Save & Apply Status</span>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
