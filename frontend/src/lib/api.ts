/**
 * API client for Healthcare Agent 2.0 backend (FastAPI).
 * All endpoints map to the REST API defined in requirements.
 */

import type {
  PatientSummary,
  DailyTrend,
  PredictionResponse,
  PaginatedResponse,
  DashboardStats,
  PatientRecord,
  ApiError,
  PatientSummaryResponse,
} from "@/types";

import { getAccessToken } from "@/lib/auth";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/* ── Base fetch helper ──────────────────────────────────────────────────── */

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? body?.message ?? message;
    } catch {
      // ignore
    }
    const err: ApiError = { status: res.status, message };
    throw err;
  }

  return res.json() as Promise<T>;
}

/* ── Patients ───────────────────────────────────────────────────────────── */

export interface GetPatientsParams {
  page?: number;
  page_size?: number;
  disease_type?: string;
  risk_level?: string;
  patient_id?: string;
}

export function getPatients(
  params: GetPatientsParams = {}
): Promise<PaginatedResponse<PatientSummary>> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  if (params.disease_type) qs.set("disease_type", params.disease_type);
  if (params.risk_level) qs.set("risk_level", params.risk_level);
  if (params.patient_id) qs.set("patient_id", params.patient_id);

  return apiFetch<PaginatedResponse<PatientSummary>>(
    `/patients?${qs.toString()}`
  );
}

export function getPatientSummary(patientId: string): Promise<PatientSummaryResponse> {
  return apiFetch<PatientSummaryResponse>(`/patients/${encodeURIComponent(patientId)}/summary`);
}

/* ── Prediction ─────────────────────────────────────────────────────────── */

export function predict(record: Partial<PatientRecord>): Promise<PredictionResponse> {
  return apiFetch<PredictionResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(record),
  });
}

/* ── Dashboard stats ────────────────────────────────────────────────────── */

export function getDashboardStats(): Promise<DashboardStats> {
  return apiFetch<DashboardStats>("/dashboard/stats");
}

/* ── Model Info ─────────────────────────────────────────────────────────── */

export interface ModelInfo {
  model_version: string;
  model_type: string;
  training_date: string;
  dataset_size: number;
  evaluation_metrics: {
    accuracy: number | null;
    precision: number | null;
    recall: number | null;
    f1_score: number | null;
    auc_roc: number | null;
  };
}

export function getModelInfo(): Promise<ModelInfo> {
  return apiFetch<ModelInfo>("/model/info");
}

/* ── Query keys — used by TanStack Query ────────────────────────────────── */

export const queryKeys = {
  patients: (params?: GetPatientsParams) =>
    ["patients", params] as const,
  patientSummary: (id: string) =>
    ["patient-summary", id] as const,
  dashboardStats: () =>
    ["dashboard-stats"] as const,
  prediction: (recordHash: string) =>
    ["prediction", recordHash] as const,
  modelInfo: () =>
    ["model-info"] as const,
};
