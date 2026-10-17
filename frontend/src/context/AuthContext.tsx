"use client";

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";

export interface UserProfile {
  username: string;
  role: string;
  full_name: string;
  must_change_password: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  loginUser: (profile: UserProfile) => void;
  logoutUser: () => Promise<void>;
  updateUserMustChangePassword: (mustChange: boolean) => void;
  isPasswordModalOpen: boolean;
  setIsPasswordModalOpen: (open: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);

  const logoutUser = useCallback(async () => {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Ignore network errors during logout
    } finally {
      sessionStorage.removeItem("vidya_user_profile");
      localStorage.removeItem("vidya_user_profile");
      setUser(null);
      setIsPasswordModalOpen(false);
      router.push("/login");
    }
  }, [router]);

  // Reset inactivity timer
  const resetInactivityTimer = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }
    if (user) {
      inactivityTimerRef.current = setTimeout(() => {
        console.warn("[VidyaMarksheet Auth] Session expired due to 30 minutes of inactivity.");
        logoutUser();
      }, INACTIVITY_TIMEOUT_MS);
    }
  }, [user, logoutUser]);

  // Activity event listeners
  useEffect(() => {
    if (!user) return;

    const activityEvents = ["mousemove", "keydown", "click", "scroll", "touchstart"];
    const handleActivity = () => resetInactivityTimer();

    activityEvents.forEach((evt) => window.addEventListener(evt, handleActivity, { passive: true }));
    resetInactivityTimer();

    return () => {
      activityEvents.forEach((evt) => window.removeEventListener(evt, handleActivity));
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
      }
    };
  }, [user, resetInactivityTimer]);

  // Initial authentication check
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Clean up any legacy persistent localStorage to force login screen
        localStorage.removeItem("vidya_user_profile");

        const stored = sessionStorage.getItem("vidya_user_profile");
        if (stored) {
          const parsed = JSON.parse(stored) as UserProfile;
          setUser(parsed);
          if (parsed.must_change_password) {
            setIsPasswordModalOpen(true);
          }
        } else if (pathname !== "/login") {
          // If accessing protected page without stored profile, verify /api/v1/auth/me
          const res = await fetch("/api/v1/auth/me", { credentials: "include" });
          if (res.ok) {
            const data = await res.json();
            const profile: UserProfile = {
              username: data.username,
              role: data.role,
              full_name: data.full_name,
              must_change_password: data.must_change_password,
            };
            sessionStorage.setItem("vidya_user_profile", JSON.stringify(profile));
            setUser(profile);
            if (profile.must_change_password) {
              setIsPasswordModalOpen(true);
            }
          } else {
            router.push("/login");
          }
        }
      } catch {
        if (pathname !== "/login") {
          router.push("/login");
        }
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, [pathname, router]);

  const loginUser = (profile: UserProfile) => {
    sessionStorage.setItem("vidya_user_profile", JSON.stringify(profile));
    setUser(profile);
    setIsPasswordModalOpen(profile.must_change_password);
    router.push("/");
  };

  const updateUserMustChangePassword = (mustChange: boolean) => {
    if (user) {
      const updated = { ...user, must_change_password: mustChange };
      localStorage.setItem("vidya_user_profile", JSON.stringify(updated));
      setUser(updated);
      setIsPasswordModalOpen(mustChange);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        loginUser,
        logoutUser,
        updateUserMustChangePassword,
        isPasswordModalOpen,
        setIsPasswordModalOpen,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
