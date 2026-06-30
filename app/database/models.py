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
