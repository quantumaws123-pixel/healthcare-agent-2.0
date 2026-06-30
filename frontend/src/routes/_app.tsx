import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/layout/AppShell";
import { getAccessToken, getStoredUser } from "@/lib/auth";

export const Route = createFileRoute("/_app")({
  // Guard: redirect to /login if not authenticated
  beforeLoad: () => {
    if (!getAccessToken() || !getStoredUser()) {
      throw redirect({ to: "/login" });
    }
  },
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
});
