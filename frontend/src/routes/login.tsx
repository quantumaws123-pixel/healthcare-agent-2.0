import React, { useState, useEffect } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Mail, Lock, User, Loader2, Eye, EyeOff, AlertCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getGoogleLoginUrl, type Role } from "@/lib/auth";
import { cn } from "@/lib/utils";

const GOOGLE_ERROR_MESSAGES: Record<string, string> = {
  google_token_failed:       "Google sign-in failed: could not exchange authorisation code. Please try again.",
  google_token_missing:      "Google sign-in failed: no access token received from Google.",
  google_profile_failed:     "Google sign-in failed: could not retrieve your Google profile.",
  google_profile_incomplete: "Google sign-in failed: your Google account is missing required information.",
  google_unexpected_error:   "Google sign-in encountered an unexpected error. Please try again.",
  google_auth_failed:        "Google sign-in failed. Please try again or use email/password.",
  google_not_registered:     "This Google account is not registered. Please wait until the administrator registers your account.",
};

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

type Tab = "login" | "register";

const ROLES: { value: Role; label: string; desc: string }[] = [
  { value: "patient", label: "Patient",  desc: "Monitor my recovery & health data" },
  { value: "doctor",  label: "Doctor",   desc: "Manage and monitor my patients" },
];

function LoginPage() {
  const navigate  = useNavigate();
  const { login, register } = useAuth();
  const [tab,      setTab]      = useState<Tab>("login");
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [name,     setName]     = useState("");
  const [role,     setRole]     = useState<Role>("patient");
  const [showPw,   setShowPw]   = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  // Show error messages redirected back from the Google OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const errCode = params.get("error");
    if (errCode) {
      setError(GOOGLE_ERROR_MESSAGES[errCode] ?? "Sign-in failed. Please try again.");
      // Remove the ?error= param from the URL so it doesn't persist on refresh
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (tab === "login") {
        await login(email, password);
        navigate({ to: "/" });
      } else {
        // Handle registration
        try {
          await register(email, password, name, role);
          navigate({ to: "/" });
        } catch (err: any) {
          // Check if it's doctor pending approval (202)
          if (err?.message?.includes("pending") || err?.message?.includes("approval")) {
            setError("✅ Registration successful! Your doctor account is pending admin approval. You will receive an email once approved.");
            setTab("login"); // Switch to login tab
            return;
          }
          throw err; // Re-throw other errors
        }
      }
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-blue-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-2xl bg-primary-500 flex items-center justify-center shadow-lg">
            <Heart size={24} className="text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-white leading-tight">Healthcare</p>
            <p className="text-xl font-bold text-primary-500 leading-tight">Agent 2.0</p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-gray-900 rounded-3xl shadow-float border border-gray-100 dark:border-gray-800 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-100 dark:border-gray-800">
            {(["login", "register"] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null); }}
                className={cn(
                  "flex-1 py-4 text-sm font-semibold capitalize transition-colors",
                  tab === t
                    ? "text-primary-600 border-b-2 border-primary-500 bg-primary-50/50 dark:bg-primary-900/20"
                    : "text-gray-500 hover:text-gray-900 dark:hover:text-white"
                )}
              >
                {t === "login" ? "Sign In" : "Create Account"}
              </button>
            ))}
          </div>

          <div className="p-7">
            {/* Google button */}
            <a
              href={getGoogleLoginUrl()}
              className="flex items-center justify-center gap-3 w-full h-11 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors shadow-sm mb-5"
            >
              <svg width="18" height="18" viewBox="0 0 18 18">
                <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z"/>
                <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z"/>
                <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z"/>
                <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z"/>
              </svg>
              Continue with Google
            </a>

            <div className="flex items-center gap-3 mb-5">
              <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
              <span className="text-xs text-gray-400">or</span>
              <div className="flex-1 h-px bg-gray-100 dark:bg-gray-800" />
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-center gap-2 p-3 rounded-xl bg-danger-50 dark:bg-red-900/20 text-danger-600 dark:text-red-400 text-sm mb-4"
                >
                  <AlertCircle size={15} className="shrink-0" />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name — register only */}
              <AnimatePresence>
                {tab === "register" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}
                  >
                    <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Full Name</label>
                    <div className="relative">
                      <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text" value={name} onChange={e => { setName(e.target.value); setError(null); }}
                        placeholder="Dr. John Smith" autoComplete="off"
                        className="w-full h-11 pl-10 pr-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400"
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Email */}
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Email</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="email" value={email} onChange={e => { setEmail(e.target.value); setError(null); }}
                    placeholder="you@hospital.com" required autoComplete="email"
                    className="w-full h-11 pl-10 pr-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Password</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type={showPw ? "text" : "password"} value={password}
                    onChange={e => { setPassword(e.target.value); setError(null); }}
                    placeholder={tab === "register" ? "Min. 8 characters" : "Your password"}
                    required minLength={tab === "register" ? 8 : undefined}
                    autoComplete={tab === "register" ? "new-password" : "current-password"}
                    className="w-full h-11 pl-10 pr-10 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400"
                  />
                  <button type="button" onClick={() => setShowPw(v => !v)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {/* Role selector — register only */}
              <AnimatePresence>
                {tab === "register" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}
                  >
                    <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Account Type</label>
                    <div className="grid grid-cols-2 gap-3">
                      {ROLES.map(r => (
                        <button
                          key={r.value} type="button" onClick={() => setRole(r.value)}
                          className={cn(
                            "flex flex-col items-center gap-2 p-4 rounded-xl border text-sm font-medium transition-all",
                            role === r.value
                              ? "border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                              : "border-gray-200 dark:border-gray-700 text-gray-500 hover:border-gray-300"
                          )}
                        >
                          <span className="text-2xl">
                            {r.value === "patient" ? "🧑‍⚕️" : "👨‍⚕️"}
                          </span>
                          {r.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-xs text-gray-400 mt-2 text-center">
                      {ROLES.find(r => r.value === role)?.desc}
                    </p>
                    {role === "doctor" && (
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-2 text-center bg-amber-50 dark:bg-amber-900/20 p-2 rounded-lg">
                        ⚠️ Doctor accounts require admin approval before activation
                      </p>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              <button
                type="submit" disabled={loading}
                className="w-full h-11 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-semibold shadow-sm transition-colors disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                {tab === "login" ? "Sign In" : "Create Account"}
              </button>
            </form>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Healthcare Agent 2.0 · Secure clinical monitoring platform
        </p>
      </motion.div>
    </div>
  );
}
