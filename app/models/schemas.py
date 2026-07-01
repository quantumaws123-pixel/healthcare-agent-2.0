"""
Pydantic data models and validation schemas for Healthcare Agent 2.0 Backend ML System.

This module defines the core data models with validation for patient records,
predictions, and dashboard statistics.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime


class PatientRecord(BaseModel):
    """
    Complete patient record with all fields for digital twin comparison and ML prediction.
    
    Validates Requirements 17.1, 17.2, 17.3, 17.4
    """
    
    # Demographics
    patient_id: str = Field(..., description="Unique patient identifier")
    patient_name: Optional[str] = Field(None, description="Patient full name")
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    gender: Literal["Male", "Female", "Other"] = Field(..., description="Patient gender")
    bmi: float = Field(..., ge=10.0, le=60.0, description="Body Mass Index")
    smoking_status: Optional[Literal["Never", "Former", "Current"]] = Field(None, description="Smoking history")
    alcohol_consumption: Optional[Literal["None", "Moderate", "Heavy", "Occasional"]] = Field(None, description="Alcohol consumption level")
    disease_type: str = Field(..., description="Primary disease diagnosis")
    
    # Vitals - within physiological ranges
    heart_rate: int = Field(..., ge=30, le=220, description="Heart rate in beats per minute")
    systolic_bp: int = Field(..., ge=60, le=250, description="Systolic blood pressure in mmHg")
    diastolic_bp: int = Field(..., ge=40, le=150, description="Diastolic blood pressure in mmHg")
    spo2: float = Field(..., ge=70.0, le=100.0, description="Blood oxygen saturation percentage")
    respiratory_rate: int = Field(..., ge=8, le=40, description="Respiratory rate in breaths per minute")
    body_temperature: float = Field(..., ge=35.0, le=42.0, description="Body temperature in Celsius")
    
    # Ideal Twin (Prescribed Plan)
    expected_steps: int = Field(..., ge=0, description="Doctor-prescribed daily step goal")
    expected_sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Doctor-prescribed sleep hours")
    water_intake_goal: int = Field(..., ge=0, description="Doctor-prescribed water intake in mL")
    
    # Real Twin (Actual Behavior)
    actual_steps: int = Field(..., ge=0, description="Actual steps taken")
    actual_sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Actual sleep hours")
    water_intake: int = Field(..., ge=0, description="Actual water intake in mL")
    medication_taken: Literal["Yes", "No"] = Field(..., description="Whether medication was taken as prescribed")
    exercise_completed: Literal["Yes", "No"] = Field(..., description="Whether exercise was completed")
    diet_compliance: float = Field(..., ge=0.0, le=100.0, description="Diet compliance percentage")
    
    # Computed fields (optional for input, required for output)
    compliance_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Overall compliance score")
    ideal_health_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Expected health score with perfect adherence")
    real_health_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Actual health score based on measurements")
    deviation_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Deviation between ideal and real health scores")
    recovery_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Recovery progress score")
    readmission_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Predicted readmission probability")
    risk_level: Optional[Literal["Low", "Medium", "High", "Critical"]] = Field(None, description="Risk level classification")
    health_trend: Optional[Literal["Increasing", "Stable", "Declining"]] = Field(None, description="Health trend direction")
    recovery_status: Optional[str] = Field(None, description="Recovery status classification")
    doctor_recommendation: Optional[str] = Field(None, description="AI-generated clinical recommendation")
    
    day: Optional[int] = Field(None, description="Day number in monitoring period")
    
    # Digital Twin and Deviation fields
    weight_kg: Optional[float] = Field(None, description="Actual weight in kg")
    expected_weight: Optional[float] = Field(None, description="Expected weight in kg")
    medication_deviation: Optional[float] = Field(None, description="Medication deviation")
    sleep_deviation: Optional[float] = Field(None, description="Sleep deviation")
    exercise_deviation: Optional[float] = Field(None, description="Exercise deviation")
    water_deviation: Optional[float] = Field(None, description="Water deviation")
    heart_rate_deviation: Optional[float] = Field(None, description="Heart rate deviation")
    bp_deviation: Optional[float] = Field(None, description="BP deviation")
    weight_deviation: Optional[float] = Field(None, description="Weight deviation")
    spo2_deviation: Optional[float] = Field(None, description="SpO2 deviation")
    temp_deviation: Optional[float] = Field(None, description="Temperature deviation")
    
    # AI Explainability and recommendation fields
    ai_recommendations: Optional[list[str]] = Field(None, description="AI-generated personalized recommendations")
    shap_reasons: Optional[list[str]] = Field(None, description="SHAP feature attribution explanations")
    
    @field_validator('diastolic_bp')
    @classmethod
    def validate_blood_pressure(cls, v: int, info) -> int:
        """
        Ensure diastolic BP is less than systolic BP.
        
        Validates Requirement 17.3
        """
        # Access systolic_bp from the values being validated
        if 'systolic_bp' in info.data and v >= info.data['systolic_bp']:
            raise ValueError('Diastolic BP must be less than Systolic BP')
        return v
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "patient_id": "P001",
                "patient_name": "John Doe",
                "age": 65,
                "gender": "Male",
                "bmi": 28.5,
                "smoking_status": "Former",
                "alcohol_consumption": "Moderate",
                "disease_type": "Heart Failure",
                "heart_rate": 78,
                "systolic_bp": 130,
                "diastolic_bp": 85,
                "spo2": 96.5,
                "respiratory_rate": 16,
                "body_temperature": 36.8,
                "expected_steps": 5000,
                "expected_sleep_hours": 8.0,
                "water_intake_goal": 2000,
                "actual_steps": 4200,
                "actual_sleep_hours": 7.5,
                "water_intake": 1800,
                "medication_taken": "Yes",
                "exercise_completed": "Yes",
                "diet_compliance": 85.0,
                "day": 1
            }
        }
    }


class SHAPFeature(BaseModel):
    """
    Individual SHAP feature attribution for model explainability.
    
    Validates Requirements 14.3, 14.4
    """
    feature_name: str = Field(..., description="Name of the feature")
    shap_value: float = Field(..., description="SHAP value indicating contribution magnitude")
    direction: Literal["positive", "negative"] = Field(..., description="Direction of contribution to prediction")


class SHAPExplanation(BaseModel):
    """
    SHAP-based model explainability with top contributing features.
    
    Validates Requirements 14.1, 14.2, 14.3
    """
    top_features: list[SHAPFeature] = Field(..., description="Top 5 features with highest SHAP values", max_length=5)


class PredictionResult(BaseModel):
    """
    ML prediction output with explainability for readmission risk assessment.
    
    Validates Requirements 1.1, 1.4, 4.2, 4.3, 4.4
    """
    patient_id: str = Field(..., description="Unique patient identifier")
    readmission_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted readmission probability (0-1)")
    risk_level: Literal["Low", "Medium", "High", "Critical"] = Field(..., description="Risk level classification")
    recovery_status: str = Field(..., description="Recovery status classification")
    health_trend: Literal["Increasing", "Stable", "Declining"] = Field(..., description="Health trend direction")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Overall compliance score")
    deviation_score: float = Field(..., ge=0.0, le=100.0, description="Deviation between ideal and real health scores")
    ideal_health_score: float = Field(..., ge=0.0, le=100.0, description="Expected health score with perfect adherence")
    real_health_score: float = Field(..., ge=0.0, le=100.0, description="Actual health score based on measurements")
    recovery_score: float = Field(..., ge=0.0, le=100.0, description="Recovery progress score")
    doctor_recommendation: str = Field(..., description="AI-generated clinical recommendation")
    shap_explanation: Optional[SHAPExplanation | Literal["unavailable"]] = Field(
        None, 
        description="SHAP-based feature attribution or 'unavailable' if computation failed"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_id": "P001",
                "readmission_probability": 0.42,
                "risk_level": "Medium",
                "recovery_status": "Improving",
                "health_trend": "Increasing",
                "compliance_score": 78.5,
                "deviation_score": 15.2,
                "ideal_health_score": 85.0,
                "real_health_score": 72.3,
                "recovery_score": 68.0,
                "doctor_recommendation": "Increase Monitoring",
                "shap_explanation": {
                    "top_features": [
                        {"feature_name": "compliance_score", "shap_value": 0.15, "direction": "positive"},
                        {"feature_name": "age", "shap_value": -0.12, "direction": "negative"},
                        {"feature_name": "heart_rate", "shap_value": -0.08, "direction": "negative"},
                        {"feature_name": "systolic_bp", "shap_value": 0.06, "direction": "positive"},
                        {"feature_name": "recovery_score", "shap_value": 0.05, "direction": "positive"}
                    ]
                }
            }
        }
    }


class PatientSummary(BaseModel):
    """
    Condensed patient information for list view and dashboard.
    
    Validates Requirements 1.1, 12.1
    """
    patient_id: str = Field(..., description="Unique patient identifier")
    patient_name: str = Field(..., description="Patient full name")
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    gender: str = Field(..., description="Patient gender")
    disease_type: str = Field(..., description="Primary disease diagnosis")
    risk_level: str = Field(..., description="Current risk level classification")
    recovery_status: str = Field(..., description="Current recovery status classification")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="Overall compliance score")
    readmission_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted readmission probability")
    last_updated: datetime = Field(..., description="Timestamp of last data update")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_id": "P001",
                "patient_name": "John Doe",
                "age": 65,
                "gender": "Male",
                "disease_type": "Heart Failure",
                "risk_level": "Medium",
                "recovery_status": "Improving",
                "compliance_score": 78.5,
                "readmission_probability": 0.42,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
    }


class DashboardStats(BaseModel):
    """
    Aggregated statistics for dashboard KPIs and visualizations.
    
    Validates Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
    """
    total_patients: int = Field(..., ge=0, description="Total number of unique active patients")
    high_risk_count: int = Field(..., ge=0, description="Count of patients with High or Critical risk level")
    avg_compliance: float = Field(..., ge=0.0, le=100.0, description="Mean compliance score across all active patients")
    avg_readmission_probability: float = Field(..., ge=0.0, le=1.0, description="Mean readmission probability across all active patients")
    risk_distribution: dict[str, int] = Field(
        ..., 
        description="Count of patients in each risk level category"
    )
    recovery_distribution: dict[str, int] = Field(
        ..., 
        description="Count of patients in each recovery status category"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_patients": 150,
                "high_risk_count": 25,
                "avg_compliance": 72.3,
                "avg_readmission_probability": 0.38,
                "risk_distribution": {
                    "low": 45,
                    "medium": 80,
                    "high": 20,
                    "critical": 5
                },
                "recovery_distribution": {
                    "recovered": 10,
                    "improving": 50,
                    "stable": 60,
                    "delayed_recovery": 20,
                    "worsening": 8,
                    "critical": 2
                }
            }
        }
    }
