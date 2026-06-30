import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import {
  AuthUser, Role, TokenResponse,
  apiLogin, apiRegister, saveSession, clearSession, getStoredUser, getAccessToken,
} from "@/lib/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (email: string, password: string, name: string, role: Role) => Promise<AuthUser>;
  setFromTokenResponse: (data: TokenResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
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
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, register, setFromTokenResponse, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used inside <AuthProvider>");
  return ctx;
}
