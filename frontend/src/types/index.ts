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
  Patient_ID: string;
  Age: number;
  Gender: "Male" | "Female" | "Other";
  Height_cm: number;
  Weight_kg: number;
  BMI: number;
  Disease_Type: DiseaseType;
  Comorbidities: string;
  Smoking_Status: "Never" | "Former" | "Current";
  Alcohol_Consumption: "None" | "Occasional" | "Moderate" | "Heavy";
  Allergy_Status: string;

  // Monitoring day
  Day: number;

  // Clinical vitals
  Heart_Rate: number;
  Systolic_BP: number;
  Diastolic_BP: number;
  SpO2: number;
  Respiratory_Rate: number;
  Body_Temperature: number;
  Blood_Glucose: number | null;
  Cholesterol: number | null;

  // Subjective measures
  Pain_Level: number;
  Fatigue_Score: number;
  Symptom_Severity: number;

  // Ideal Twin (doctor plan)
  Medication_Name: string;
  Medication_Dosage: string;
  Medication_Frequency: string;
  Expected_Steps: number;
  Expected_Sleep_Hours: number;
  Diet_Plan: string;
  Water_Intake_Goal: number;
  Exercise_Plan: string;
  Follow_Up_Date: string;

  // Real Twin (actual behaviour)
  Actual_Steps: number;
  Medication_Taken: "Yes" | "No";
  Actual_Sleep_Hours: number;
  Water_Intake: number;
  Exercise_Completed: "Yes" | "No";
  Diet_Compliance: number;
  Mood: string | null;
  Symptoms: string;
  Missed_Medication_Count: number;
  Missed_Exercise_Count: number;

  // AI outputs
  Compliance_Score: number;
  Ideal_Health_Score: number;
  Real_Health_Score: number;
  Deviation_Score: number;
  Recovery_Score: number;
  Health_Trend: HealthTrend;
  Readmission_Probability: number;
  Risk_Level: RiskLevel;
  Recovery_Status: RecoveryStatus;
  Doctor_Recommendation: DoctorRecommendation;
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
}

/* ── Prediction response from API ─────────────────────────────────────── */

export interface PredictionResponse {
  Risk_Level: RiskLevel;
  Recovery_Status: RecoveryStatus;
  Doctor_Recommendation: DoctorRecommendation;
  Readmission_Probability: number;
  shap_features?: ShapFeature[];
  explainability: "available" | "unavailable";
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
  risk_distribution: Record<RiskLevel, number>;
  recovery_distribution: Record<RecoveryStatus, number>;
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
