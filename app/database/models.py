"""SQLAlchemy ORM models for Healthcare Agent 2.0 Backend ML System.

This module defines the database schema for patient records and ML model metadata.
Implements Requirements 2.1, 2.2, and 2.6 from the requirements document.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    TIMESTAMP,
    Boolean,
    Text,
    Index,
)
from sqlalchemy.types import DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Import auth models so Base.metadata includes the users table
# (imported after Base is defined to avoid circular imports)
from app.auth.models import UserDB  # noqa: F401



class PatientRecordDB(Base):
    """Patient record table with composite primary key (patient_id, day).
    
    Stores time-series patient monitoring data including:
    - Demographics (age, gender, BMI, etc.)
    - Clinical vitals (heart rate, blood pressure, SpO2, etc.)
    - Ideal Twin data (prescribed plan: expected steps, sleep, water intake)
    - Real Twin data (actual behavior: actual steps, sleep, medication adherence)
    - Computed scores (compliance, health scores, deviation, recovery)
    - AI predictions (readmission probability, risk level, recommendations)
    
    **Validates: Requirements 2.1, 2.2, 2.6**
    """
    
    __tablename__ = "patient_records"
    
    # Composite Primary Key
    patient_id = Column(String(50), primary_key=True, nullable=False)
    day = Column(Integer, primary_key=True, nullable=False)
    
    # Demographics
    patient_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    bmi = Column(DECIMAL(5, 2), nullable=True)
    smoking_status = Column(String(20), nullable=True)
    alcohol_consumption = Column(String(20), nullable=True)
    disease_type = Column(String(50), nullable=True)
    
    # Clinical Vitals
    heart_rate = Column(Integer, nullable=True)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    spo2 = Column(DECIMAL(5, 2), nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    body_temperature = Column(DECIMAL(4, 2), nullable=True)
    
    # Ideal Twin (Prescribed Plan)
    expected_steps = Column(Integer, nullable=True)
    expected_sleep_hours = Column(DECIMAL(4, 2), nullable=True)
    water_intake_goal = Column(Integer, nullable=True)
    
    # Real Twin (Actual Behavior)
    actual_steps = Column(Integer, nullable=True)
    actual_sleep_hours = Column(DECIMAL(4, 2), nullable=True)
    water_intake = Column(Integer, nullable=True)
    medication_taken = Column(String(3), nullable=True)  # "Yes" or "No"
    exercise_completed = Column(String(3), nullable=True)  # "Yes" or "No"
    diet_compliance = Column(DECIMAL(5, 2), nullable=True)
    
    # Computed Scores
    compliance_score = Column(DECIMAL(5, 2), nullable=True)
    ideal_health_score = Column(DECIMAL(5, 2), nullable=True)
    real_health_score = Column(DECIMAL(5, 2), nullable=True)
    deviation_score = Column(DECIMAL(5, 2), nullable=True)
    recovery_score = Column(DECIMAL(5, 2), nullable=True)
    
    # AI Predictions
    readmission_probability = Column(DECIMAL(5, 4), nullable=True)
    risk_level = Column(String(20), nullable=True)
    health_trend = Column(String(20), nullable=True)
    recovery_status = Column(String(50), nullable=True)
    doctor_recommendation = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Define indexes for query performance (Requirement 2.6)
    __table_args__ = (
        Index("idx_patient_id", "patient_id"),
        Index("idx_day", "day"),
        Index("idx_disease_type", "disease_type"),
        Index("idx_risk_level", "risk_level"),
        Index("idx_recovery_status", "recovery_status"),
    )
    
    def __repr__(self):
        return (
            f"<PatientRecordDB(patient_id={self.patient_id}, "
            f"day={self.day}, "
            f"risk_level={self.risk_level}, "
            f"recovery_status={self.recovery_status})>"
        )


class MLModelDB(Base):
    """ML model metadata table for model versioning and tracking.
    
    Stores information about trained machine learning models including:
    - Model version and type (Logistic Regression, Random Forest, XGBoost, LSTM)
    - Training metadata (date, dataset size)
    - Evaluation metrics (accuracy, precision, recall, F1, AUC-ROC)
    - Deployment status (is_active flag)
    - File path to serialized model
    
    **Validates: Requirements 2.1, 2.2**
    """
    
    __tablename__ = "ml_models"
    
    # Primary Key
    model_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Model Identification
    model_version = Column(String(20), unique=True, nullable=False)
    model_type = Column(String(50), nullable=False)  # 'LogisticRegression', 'RandomForest', 'XGBoost', 'LSTM'
    model_path = Column(String(255), nullable=False)
    
    # Training Metadata
    training_date = Column(TIMESTAMP, nullable=False)
    dataset_size = Column(Integer, nullable=False)
    
    # Evaluation Metrics
    accuracy = Column(DECIMAL(5, 4), nullable=True)
    precision = Column(DECIMAL(5, 4), nullable=True)
    recall = Column(DECIMAL(5, 4), nullable=True)
    f1_score = Column(DECIMAL(5, 4), nullable=True)
    auc_roc = Column(DECIMAL(5, 4), nullable=True)
    
    # Deployment Status
    is_active = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self):
        return (
            f"<MLModelDB(model_id={self.model_id}, "
            f"model_version={self.model_version}, "
            f"model_type={self.model_type}, "
            f"is_active={self.is_active})>"
        )



class HospitalDB(Base):
    """Hospital entity — every doctor and patient belongs to one hospital."""

    __tablename__ = "hospitals"

    id          = Column(String(50),  primary_key=True)
    name        = Column(String(200), nullable=False)
    code        = Column(String(20),  nullable=False, unique=True, index=True)
    address     = Column(Text,        nullable=True)
    city        = Column(String(100), nullable=True)
    state       = Column(String(100), nullable=True)
    country     = Column(String(100), nullable=True, default="India")
    phone       = Column(String(20),  nullable=True)
    email       = Column(String(255), nullable=True)
    departments = Column(Text,        nullable=True)   # comma-separated list
    is_active   = Column(Boolean,     default=True,  nullable=False)
    created_at  = Column(TIMESTAMP,   server_default=func.now(), nullable=False)
    updated_at  = Column(TIMESTAMP,   server_default=func.now(), onupdate=func.now(), nullable=False)


class DoctorProfileDB(Base):
    """Doctor profile table - extends user account with doctor-specific information."""

    __tablename__ = "doctor_profiles"

    id               = Column(String(50),  primary_key=True)
    user_id          = Column(String(50),  nullable=False, unique=True, index=True)
    hospital_id      = Column(String(50),  nullable=True)   # FK → hospitals.id
    specialization   = Column(String(100), nullable=True)
    hospital         = Column(String(200), nullable=True)   # legacy free-text field kept
    license_number   = Column(String(50),  nullable=True)
    department       = Column(String(100), nullable=True)
    qualification    = Column(String(200), nullable=True)
    phone            = Column(String(20),  nullable=True)
    experience_years = Column(Integer,     nullable=True)
    availability     = Column(String(20),  nullable=True, default="Available")
    working_hours    = Column(String(100), nullable=True)
    avatar_url       = Column(String(500), nullable=True)
    approved_by      = Column(String(50),  nullable=True)
    approved_at      = Column(TIMESTAMP,   nullable=True)
    created_at       = Column(TIMESTAMP,   server_default=func.now(), nullable=False)
    updated_at       = Column(TIMESTAMP,   server_default=func.now(), onupdate=func.now(), nullable=False)


class PatientProfileDB(Base):
    """Patient profile table - full clinical demographics, links to patient records."""

    __tablename__ = "patient_profiles"

    id                      = Column(String(50),   primary_key=True)
    user_id                 = Column(String(50),   nullable=False, unique=True, index=True)
    patient_id              = Column(String(50),   nullable=True,  index=True)   # → patient_records
    hospital_id             = Column(String(50),   nullable=True)
    assigned_doctor_id      = Column(String(50),   nullable=True)  # FK → doctor_profiles.id
    # Demographics
    age                     = Column(Integer,      nullable=True)
    gender                  = Column(String(10),   nullable=True)
    height_cm               = Column(Integer,      nullable=True)
    weight_kg               = Column(DECIMAL(5,2), nullable=True)
    bmi                     = Column(DECIMAL(5,2), nullable=True)
    blood_group             = Column(String(5),    nullable=True)
    disease_type            = Column(String(50),   nullable=True)
    # Lifestyle
    smoking_status          = Column(String(20),   nullable=True)
    alcohol_consumption     = Column(String(20),   nullable=True)
    # Clinical
    allergies               = Column(Text,         nullable=True)
    existing_conditions     = Column(Text,         nullable=True)
    current_medication      = Column(Text,         nullable=True)
    # Emergency
    emergency_contact_name  = Column(String(100),  nullable=True)
    emergency_contact_phone = Column(String(20),   nullable=True)
    # Dates
    admission_date          = Column(String(20),   nullable=True)
    discharge_date          = Column(String(20),   nullable=True)
    monitoring_start_date   = Column(String(20),   nullable=True)
    monitoring_end_date     = Column(String(20),   nullable=True)
    # Status
    patient_status          = Column(String(20),   nullable=True, default="Monitoring")
    onboarding_completed    = Column(Boolean,      nullable=False, default=False)
    # Timestamps
    created_at              = Column(TIMESTAMP,    server_default=func.now(), nullable=False)
    updated_at              = Column(TIMESTAMP,    server_default=func.now(), onupdate=func.now(), nullable=False)


class CarePlanDB(Base):
    """Care plan created by a doctor — becomes the patient's Ideal Digital Twin targets."""

    __tablename__ = "care_plans"

    id                       = Column(String(50),   primary_key=True)
    patient_user_id          = Column(String(50),   nullable=False, index=True)
    doctor_user_id           = Column(String(50),   nullable=False, index=True)
    daily_steps_goal         = Column(Integer,      nullable=True, default=8000)
    sleep_hours_goal         = Column(DECIMAL(4,2), nullable=True, default=8.0)
    water_intake_goal_ml     = Column(Integer,      nullable=True, default=2000)
    medication_schedule      = Column(Text,         nullable=True)
    exercise_plan            = Column(Text,         nullable=True)
    diet_plan                = Column(Text,         nullable=True)
    followup_frequency_days  = Column(Integer,      nullable=True, default=7)
    monitoring_duration_days = Column(Integer,      nullable=True, default=30)
    risk_threshold           = Column(DECIMAL(4,3), nullable=True, default=0.5)
    emergency_threshold      = Column(DECIMAL(4,3), nullable=True, default=0.75)
    notes                    = Column(Text,         nullable=True)
    is_active                = Column(Boolean,      nullable=False, default=True)
    created_at               = Column(TIMESTAMP,    server_default=func.now(), nullable=False)
    updated_at               = Column(TIMESTAMP,    server_default=func.now(), onupdate=func.now(), nullable=False)


class PatientVitalsDailyDB(Base):
    """Daily vital submission by the patient — updates the Real Twin."""

    __tablename__ = "patient_vitals_daily"

    id                 = Column(String(50),   primary_key=True)
    patient_user_id    = Column(String(50),   nullable=False, index=True)
    log_date           = Column(String(20),   nullable=False)   # YYYY-MM-DD
    heart_rate         = Column(Integer,      nullable=True)
    systolic_bp        = Column(Integer,      nullable=True)
    diastolic_bp       = Column(Integer,      nullable=True)
    spo2               = Column(DECIMAL(5,2), nullable=True)
    body_temperature   = Column(DECIMAL(4,2), nullable=True)
    weight_kg          = Column(DECIMAL(5,2), nullable=True)
    actual_steps       = Column(Integer,      nullable=True)
    actual_sleep_hours = Column(DECIMAL(4,2), nullable=True)
    water_intake_ml    = Column(Integer,      nullable=True)
    medication_taken   = Column(String(3),    nullable=True)
    exercise_completed = Column(String(3),    nullable=True)
    diet_compliance    = Column(DECIMAL(5,2), nullable=True)
    pain_level         = Column(Integer,      nullable=True)   # 0-10
    mood               = Column(String(20),   nullable=True)
    symptoms           = Column(Text,         nullable=True)
    notes              = Column(Text,         nullable=True)
    created_at         = Column(TIMESTAMP,    server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_vitals_patient_date", "patient_user_id", "log_date"),
    )


class MedicalHistoryDB(Base):
    """Doctor-managed clinical medical history for a patient."""

    __tablename__ = "medical_history"

    id                   = Column(String(50),  primary_key=True)
    patient_user_id      = Column(String(50),  nullable=False, index=True)
    created_by_doctor_id = Column(String(50),  nullable=True)
    past_diseases        = Column(Text,        nullable=True)
    previous_admissions  = Column(Text,        nullable=True)
    previous_surgeries   = Column(Text,        nullable=True)
    family_history       = Column(Text,        nullable=True)
    current_medications  = Column(Text,        nullable=True)
    medication_history   = Column(Text,        nullable=True)
    allergies            = Column(Text,        nullable=True)
    lifestyle_smoking    = Column(String(20),  nullable=True)
    lifestyle_alcohol    = Column(String(20),  nullable=True)
    lifestyle_exercise   = Column(String(50),  nullable=True)
    lifestyle_diet       = Column(String(50),  nullable=True)
    doctor_notes         = Column(Text,        nullable=True)
    discharge_summary    = Column(Text,        nullable=True)
    created_at           = Column(TIMESTAMP,   server_default=func.now(), nullable=False)
    updated_at           = Column(TIMESTAMP,   server_default=func.now(), onupdate=func.now(), nullable=False)
