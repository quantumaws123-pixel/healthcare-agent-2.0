/* ── Core domain types aligned with the dataset ──────────────────────── */

export type RiskLevel = "Low" | "Medium" | "High" | "Critical";

export type RecoveryStatus =
  | "Recovered"
  | "Improving"
  | "Stable"
  | "Delayed Recovery"
  | "Worsening"
  | "Critical";

export type HealthTrend = "Increasing" | "Stable" | "Declining";

export type DiseaseType =
  | "Cardiac"
  | "Diabetes"
  | "Hypertension"
  | "COPD"
  | "Kidney Disease"
  | "Asthma"
  | "Stroke Recovery"
  | "Post Surgery";

export type DoctorRecommendation =
  | "Continue Current Treatment"
  | "Increase Monitoring"
  | "Medication Adjustment"
  | "Immediate Doctor Review"
  | "Hospital Readmission";

/* ── Patient record (one row = one day) ────────────────────────────────── */

export interface PatientRecord {
  // Identity
  patient_id: string;
  patient_name?: string;
  age: number;
  gender: "Male" | "Female" | "Other";
  bmi: number;
  disease_type: DiseaseType;
  smoking_status?: "Never" | "Former" | "Current";
  alcohol_consumption?: "None" | "Occasional" | "Moderate" | "Heavy";

  // Monitoring day
  day?: number;

  // Clinical vitals
  heart_rate: number;
  systolic_bp: number;
  diastolic_bp: number;
  spo2: number;
  respiratory_rate: number;
  body_temperature: number;

  // Ideal Twin (doctor plan)
  expected_steps: number;
  expected_sleep_hours: number;
  water_intake_goal: number;

  // Real Twin (actual behaviour)
  actual_steps: number;
  medication_taken: "Yes" | "No";
  actual_sleep_hours: number;
  water_intake: number;
  exercise_completed: "Yes" | "No";
  diet_compliance: number;

  // AI outputs
  compliance_score?: number;
  ideal_health_score?: number;
  real_health_score?: number;
  deviation_score?: number;
  recovery_score?: number;
  health_trend?: HealthTrend;
  readmission_probability?: number;
  risk_level?: RiskLevel;
  recovery_status?: RecoveryStatus;
  doctor_recommendation?: string;
  
  weight_kg?: number;
  expected_weight?: number;
  medication_deviation?: number;
  sleep_deviation?: number;
  exercise_deviation?: number;
  water_deviation?: number;
  heart_rate_deviation?: number;
  bp_deviation?: number;
  weight_deviation?: number;
  spo2_deviation?: number;
  temp_deviation?: number;
  ai_recommendations?: string[];
  shap_reasons?: string[];
}

/* ── Summarised patient (latest day) ──────────────────────────────────── */

export interface PatientSummary {
  Patient_ID: string;
  Age: number;
  Gender: string;
  Disease_Type: DiseaseType;
  Risk_Level: RiskLevel;
  Recovery_Status: RecoveryStatus;
  Readmission_Probability: number;
  Compliance_Score: number;
  Latest_Day: number;
  Doctor_Recommendation: DoctorRecommendation;
}

/* ── 30-day trend series ───────────────────────────────────────────────── */

export interface DailyTrend {
  day: number;
  compliance_score: number;
  deviation_score: number;
  recovery_score: number;
  health_trend: HealthTrend;
  readmission_probability: number;
  real_health_score: number;
  ideal_health_score: number;
  
  // New Digital Twin and Deviation fields
  weight_kg?: number;
  expected_weight?: number;
  medication_deviation?: number;
  sleep_deviation?: number;
  exercise_deviation?: number;
  water_deviation?: number;
  heart_rate_deviation?: number;
  bp_deviation?: number;
  weight_deviation?: number;
  spo2_deviation?: number;
  temp_deviation?: number;
  
  medication_taken?: string;
  exercise_completed?: string;
  actual_steps?: number;
  actual_sleep_hours?: number;
  water_intake?: number;
  expected_steps?: number;
  expected_sleep_hours?: number;
  water_intake_goal?: number;
  heart_rate?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  spo2?: number;
  body_temperature?: number;
  
  ai_recommendations?: string[];
  shap_reasons?: string[];
}

export interface PatientSummaryResponse {
  patient_id: string;
  patient_name: string | null;
  disease_type: DiseaseType;
  current_risk_level: RiskLevel;
  current_recovery_status: RecoveryStatus;
  daily_trends: DailyTrend[];
}

/* ── Prediction response from API ─────────────────────────────────────── */

export interface PredictionResponse {
  Risk_Level: RiskLevel;
  Recovery_Status: RecoveryStatus;
  Doctor_Recommendation: DoctorRecommendation;
  Readmission_Probability: number;
  shap_features?: ShapFeature[];
  explainability: "available" | "unavailable";
  AI_Recommendations?: string[];
  Shap_Reasons?: string[];
}

export interface ShapFeature {
  feature: string;
  shap_value: number;
  direction: "positive" | "negative";
}

/* ── Paginated list response ───────────────────────────────────────────── */

export interface PaginatedResponse<T> {
  data: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

/* ── Dashboard stats ───────────────────────────────────────────────────── */

export interface DashboardStats {
  total_patients: number;
  risk_distribution: Record<string, number>;
  recovery_distribution: Record<string, number>;
  avg_compliance: number;
  avg_readmission_probability: number;
  high_risk_count: number;
}

/* ── API error ─────────────────────────────────────────────────────────── */

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}
