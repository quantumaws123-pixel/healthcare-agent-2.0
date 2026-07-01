/**
 * /auth/callback — receives access_token + refresh_token from Google OAuth redirect,
 * stores them, then navigates to the appropriate dashboard.
 */
import { useEffect } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Heart, Loader2 } from "lucide-react";
import { getStoredUser } from "@/lib/auth";
import type { AuthUser } from "@/lib/auth";
import { useAuthContext } from "@/context/AuthContext";

export const Route = createFileRoute("/auth/callback")({
  component: AuthCallback,
});

function AuthCallback() {
  const navigate = useNavigate();
  const { setFromTokenResponse } = useAuthContext();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const access_token  = params.get("access_token");
    const refresh_token = params.get("refresh_token");
    const role          = params.get("role");
    const name          = params.get("name");
    const avatar_url    = params.get("avatar_url");
    const id            = params.get("id");
    const email         = params.get("email");

    if (access_token && refresh_token && role) {
      const existing = getStoredUser();
      const user: AuthUser = {
        id: id || existing?.id || "",
        email: email ? decodeURIComponent(email) : (existing?.email || ""),
        name: name ? decodeURIComponent(name) : (existing?.name || null),
        avatar_url: avatar_url ? decodeURIComponent(avatar_url) : (existing?.avatar_url || null),
        role: role as any,
        is_active: existing?.is_active ?? true,
      };
      setFromTokenResponse({ access_token, refresh_token, token_type: "bearer", user });
    }

    // Small delay so the spinner shows briefly
    setTimeout(() => navigate({ to: "/" }), 500);
  }, [navigate, setFromTokenResponse]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-gray-50 dark:bg-gray-950">
      <div className="w-12 h-12 rounded-2xl bg-primary-500 flex items-center justify-center">
        <Heart size={24} className="text-white" />
      </div>
      <Loader2 size={28} className="animate-spin text-primary-500" />
      <p className="text-sm text-gray-500">Signing you in…</p>
    </div>
  );
}
