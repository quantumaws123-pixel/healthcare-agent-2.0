/**
 * Auth client — login, register, Google OAuth, token storage, refresh.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Role = "admin" | "doctor" | "patient";

export interface AuthUser {
  id:         string;
  email:      string;
  name:       string | null;
  avatar_url: string | null;
  role:       Role;
  is_active:  boolean;
}

export interface TokenResponse {
  access_token:  string;
  refresh_token: string;
  token_type:    string;
  user:          AuthUser;
}

// ── storage ──────────────────────────────────────────────────────────────

const KEYS = { access: "ha_access", refresh: "ha_refresh", user: "ha_user" };

export function saveSession(data: TokenResponse) {
  localStorage.setItem(KEYS.access,  data.access_token);
  localStorage.setItem(KEYS.refresh, data.refresh_token);
  localStorage.setItem(KEYS.user,    JSON.stringify(data.user));
}

export function clearSession() {
  Object.values(KEYS).forEach(k => localStorage.removeItem(k));
}

export function getAccessToken(): string | null {
  return localStorage.getItem(KEYS.access);
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(KEYS.user);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

// ── fetch helper (with auth header) ─────────────────────────────────────

async function authFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw { status: res.status, message: body.detail ?? body.message ?? `HTTP ${res.status}` };
  }
  return res.json();
}

// ── auth API calls ────────────────────────────────────────────────────────

export async function apiLogin(email: string, password: string): Promise<TokenResponse> {
  return authFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function apiRegister(
  email: string,
  password: string,
  name: string,
  role: Role,
): Promise<TokenResponse> {
  return authFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name, role }),
  });
}

export async function apiGetMe(): Promise<AuthUser> {
  return authFetch<AuthUser>("/auth/me");
}

export function getGoogleLoginUrl(): string {
  return `${BASE_URL}/auth/google`;
}
