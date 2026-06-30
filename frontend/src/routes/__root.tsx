import React from "react";
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";
import type { AuthUser } from "@/lib/auth";

export interface RouterContext {
  queryClient: QueryClient;
  auth: {
    user: AuthUser | null;
    isAuthenticated: boolean;
  };
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => <Outlet />,
});
