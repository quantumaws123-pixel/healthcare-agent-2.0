/**
 * useAuth — single source of truth for auth state across the app.
 * Reads from localStorage on mount; exposes login/register/logout.
 */
import { useState, useCallback } from "react";
import {
  AuthUser, Role, TokenResponse,
  apiLogin, apiRegister, saveSession, clearSession, getStoredUser, getAccessToken,
} from "@/lib/auth";

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser());

  const isAuthenticated = Boolean(user && getAccessToken());

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    saveSession(data);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (email: string, password: string, name: string, role: Role) => {
    const data = await apiRegister(email, password, name, role);
    saveSession(data);
    setUser(data.user);
    return data.user;
  }, []);

  const setFromTokenResponse = useCallback((data: TokenResponse) => {
    saveSession(data);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  return { user, isAuthenticated, login, register, logout, setFromTokenResponse };
}
