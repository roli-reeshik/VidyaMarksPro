"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { ChangePasswordModal } from "../../components/ChangePasswordModal";
import { useAuth } from "../../context/AuthContext";

export default function ChangePasswordPage() {
  const router = useRouter();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <ChangePasswordModal
        isOpen={true}
        isForced={user?.must_change_password ?? false}
        onClose={() => router.push("/")}
      />
    </div>
  );
}
