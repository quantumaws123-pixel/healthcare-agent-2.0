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

import { getAccessToken, getApiUrl } from "@/lib/auth";

const BASE_URL = getApiUrl();

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

export function getLatestPatientRecord(patientId: string): Promise<PatientRecord> {
  return apiFetch<PatientRecord>(`/patients/${encodeURIComponent(patientId)}/latest`);
}

export interface SimulationRequest {
  actual_steps?: number;
  actual_sleep_hours?: number;
  water_intake?: number;
  medication_taken?: "Yes" | "No";
  weight_kg?: number;
}

export interface SimulationResponse {
  original_recovery_score: number;
  original_risk_level: string;
  original_readmission_probability: number;
  simulated_recovery_score: number;
  simulated_risk_level: string;
  simulated_readmission_probability: number;
  original_recommendations: string[];
  simulated_recommendations: string[];
}

export function simulateRecovery(patientId: string, body: SimulationRequest): Promise<SimulationResponse> {
  return apiFetch<SimulationResponse>(`/patients/${encodeURIComponent(patientId)}/simulate`, {
    method: "POST",
    body: JSON.stringify(body),
  });
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
  patientLatest: (id: string) =>
    ["patient-latest", id] as const,
  dashboardStats: () =>
    ["dashboard-stats"] as const,
  prediction: (recordHash: string) =>
    ["prediction", recordHash] as const,
  modelInfo: () =>
    ["model-info"] as const,
};


/* ── Hospital workflow APIs ─────────────────────────────────────────────── */

export interface PatientProfile {
  id: string;
  user_id: string;
  patient_id?: string | null;
  age?: number | null;
  gender?: string | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  bmi?: number | null;
  blood_group?: string | null;
  disease_type?: string | null;
  smoking_status?: string | null;
  alcohol_consumption?: string | null;
  allergies?: string | null;
  existing_conditions?: string | null;
  current_medication?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  discharge_date?: string | null;
  monitoring_start_date?: string | null;
  patient_status?: string | null;
  onboarding_completed: boolean;
  assigned_doctor_id?: string | null;
}

export interface PatientOnboardingRequest {
  age: number;
  gender: string;
  height_cm?: number;
  weight_kg?: number;
  blood_group?: string;
  disease_type: string;
  smoking_status?: string;
  alcohol_consumption?: string;
  allergies?: string;
  existing_conditions?: string;
  current_medication?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  discharge_date?: string;
}

export interface CarePlan {
  id: string;
  patient_user_id: string;
  doctor_user_id: string;
  daily_steps_goal?: number;
  sleep_hours_goal?: number;
  water_intake_goal_ml?: number;
  medication_schedule?: string;
  exercise_plan?: string;
  diet_plan?: string;
  followup_frequency_days?: number;
  monitoring_duration_days?: number;
  risk_threshold?: number;
  emergency_threshold?: number;
  notes?: string;
  is_active: boolean;
}

export interface DailyVitalsRequest {
  log_date?: string;
  heart_rate?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  spo2?: number;
  body_temperature?: number;
  weight_kg?: number;
  actual_steps?: number;
  actual_sleep_hours?: number;
  water_intake_ml?: number;
  medication_taken?: "Yes" | "No";
  exercise_completed?: "Yes" | "No";
  diet_compliance?: number;
  pain_level?: number;
  mood?: string;
  symptoms?: string;
  notes?: string;
}

export interface DailyVitals extends DailyVitalsRequest {
  id: string;
  patient_user_id: string;
  log_date: string;
}

export interface MedicalHistory {
  id: string;
  patient_user_id: string;
  created_by_doctor_id?: string;
  past_diseases?: string;
  previous_admissions?: string;
  previous_surgeries?: string;
  family_history?: string;
  current_medications?: string;
  medication_history?: string;
  allergies?: string;
  lifestyle_smoking?: string;
  lifestyle_alcohol?: string;
  lifestyle_exercise?: string;
  lifestyle_diet?: string;
  doctor_notes?: string;
  discharge_summary?: string;
}

export interface DoctorPatient {
  user_id: string;
  name?: string;
  email: string;
  age?: number;
  gender?: string;
  disease_type?: string;
  patient_status?: string;
  onboarding_completed: boolean;
  assigned_doctor_id?: string;
}

const HOSPITAL_BASE = `/api/hospital`;

export function getMyPatientProfile(): Promise<PatientProfile> {
  return apiFetch<PatientProfile>(`${HOSPITAL_BASE}/patient/profile`);
}

export function completeOnboarding(data: PatientOnboardingRequest): Promise<PatientProfile> {
  return apiFetch<PatientProfile>(`${HOSPITAL_BASE}/patient/onboarding`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getCarePlan(patientUserId: string): Promise<CarePlan | null> {
  return apiFetch<CarePlan | null>(`${HOSPITAL_BASE}/care-plan/${patientUserId}`);
}

export function createCarePlan(data: Omit<CarePlan, "id" | "doctor_user_id" | "is_active">): Promise<CarePlan> {
  return apiFetch<CarePlan>(`${HOSPITAL_BASE}/care-plan`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function submitDailyVitals(data: DailyVitalsRequest): Promise<DailyVitals> {
  return apiFetch<DailyVitals>(`${HOSPITAL_BASE}/vitals`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getTodayVitals(): Promise<DailyVitals | null> {
  return apiFetch<DailyVitals | null>(`${HOSPITAL_BASE}/vitals/today`);
}

export function getVitalsHistory(limit = 30): Promise<DailyVitals[]> {
  return apiFetch<DailyVitals[]>(`${HOSPITAL_BASE}/vitals/history?limit=${limit}`);
}

export function getMedicalHistory(patientUserId: string): Promise<MedicalHistory | null> {
  return apiFetch<MedicalHistory | null>(`${HOSPITAL_BASE}/medical-history/${patientUserId}`);
}

export function getMyDoctorPatients(): Promise<DoctorPatient[]> {
  return apiFetch<DoctorPatient[]>(`${HOSPITAL_BASE}/doctor/my-patients`);
}

export function getAssignedDoctor(patientUserId: string): Promise<{ assigned_doctor: any | null }> {
  return apiFetch<{ assigned_doctor: any | null }>(
    `${HOSPITAL_BASE}/patient/${patientUserId}/assigned-doctor`
  );
}

export const hospitalQueryKeys = {
  myProfile:       () => ["my-patient-profile"]    as const,
  carePlan:        (id: string) => ["care-plan", id] as const,
  todayVitals:     () => ["today-vitals"]           as const,
  vitalsHistory:   () => ["vitals-history"]         as const,
  medicalHistory:  (id: string) => ["medical-history", id] as const,
  myDoctorPatients:() => ["my-doctor-patients"]     as const,
  assignedDoctor:  (id: string) => ["assigned-doctor", id] as const,
};
