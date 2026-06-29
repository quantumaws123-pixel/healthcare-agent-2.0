# Design Document: Backend ML System

## Overview

### System Purpose

The Healthcare Agent 2.0 Backend ML System is an AI-powered digital twin platform designed for post-discharge patient monitoring and hospital readmission risk prediction. The system creates and maintains dual digital representations of each patient:

- **Ideal Twin**: A computational model representing perfect adherence to the doctor's prescribed recovery plan
- **Real Twin**: A data-driven model reflecting actual patient behavior and physiological measurements

By continuously comparing these twins, the system computes deviation metrics, predicts readmission risk using machine learning models, and generates actionable recommendations for healthcare providers.

### Key Capabilities

1. **REST API**: FastAPI-based endpoints for patient data management, predictions, and dashboard analytics
2. **Machine Learning**: Multi-model ensemble (Logistic Regression, Random Forest, XGBoost, LSTM) for readmission prediction with SHAP-based explainability
3. **Digital Twin Engine**: Real-time comparison logic computing compliance, health scores, and deviation metrics
4. **Data Pipeline**: ETL system for feature engineering and data preprocessing
5. **Recommendation Engine**: Rule-based clinical decision support system
6. **Persistent Storage**: Relational database (PostgreSQL) with optimized schema for time-series patient data

### Design Principles

- **Modularity**: Clear separation between API layer, business logic, data access, and ML inference
- **Scalability**: Async I/O, connection pooling, and stateless design to support thousands of concurrent patients
- **Explainability**: SHAP integration to provide transparent, clinically interpretable model predictions
- **Performance**: Sub-500ms prediction latency and efficient database indexing for real-time responsiveness
- **Reliability**: ACID guarantees, comprehensive error handling, and graceful degradation
- **Maintainability**: Type safety with Pydantic, comprehensive logging, and model versioning

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[React Frontend<br/>TanStack Router + Query]
    end
    
    subgraph "API Layer"
        API[FastAPI Application<br/>REST Endpoints]
        CORS[CORS Middleware]
        VAL[Request Validation<br/>Pydantic Schemas]
    end
    
    subgraph "Business Logic Layer"
        DTE[Digital Twin Engine<br/>Comparison Logic]
        CC[Compliance Calculator]
        HSC[Health Score Calculator]
        PS[Prediction System<br/>Recovery Status & Trends]
        RE[Recommendation Engine<br/>Clinical Rules]
    end
    
    subgraph "ML Layer"
        MLM[ML Model Manager<br/>Model Loading & Versioning]
        INF[Inference Engine<br/>Multi-Model Ensemble]
        SHAP[SHAP Explainer<br/>Feature Attribution]
    end
    
    subgraph "Data Layer"
        DPP[Data Processing Pipeline<br/>ETL & Feature Engineering]
        DAO[Data Access Objects<br/>SQLAlchemy ORM]
        DB[(PostgreSQL Database<br/>Patient Records)]
    end
    
    subgraph "External"
        LOGS[Logging System<br/>Structured Logs]
        CACHE[Cache Layer<br/>Dashboard Stats]
    end
    
    FE -->|HTTP/JSON| API
    API --> CORS
    API --> VAL
    VAL --> DTE
    VAL --> PS
    VAL --> RE
    DTE --> CC
    DTE --> HSC
    PS --> INF
    RE --> DAO
    INF --> MLM
    INF --> SHAP
    DTE --> DAO
    CC --> DAO
    HSC --> DAO
    PS --> DAO
    DAO --> DB
    DPP --> DB
    API --> LOGS
    API --> CACHE
```


### System Architecture Layers

#### 1. API Layer (FastAPI)

**Responsibilities:**
- HTTP request handling and routing
- Request validation using Pydantic schemas
- Response serialization to JSON
- CORS configuration for frontend integration
- Rate limiting and authentication (future)
- Error handling and HTTP status code management

**Technology Stack:**
- FastAPI 0.115+ for async API framework
- Pydantic 2.x for data validation and serialization
- Uvicorn as ASGI server
- Python 3.11+ for performance and typing improvements

**Key Design Decisions:**
- Async/await throughout for non-blocking I/O
- Dependency injection for database sessions and service instances
- OpenAPI/Swagger auto-documentation
- Structured logging for request/response tracing

#### 2. Business Logic Layer

**Responsibilities:**
- Core domain logic for digital twin comparison
- Compliance and health score calculations
- Recovery status classification
- Health trend analysis
- Recommendation rule evaluation

**Components:**
- `DigitalTwinEngine`: Compares Ideal Twin vs Real Twin, computes deviations
- `ComplianceCalculator`: Weighted scoring across medication, exercise, diet, sleep, steps, water
- `HealthScoreCalculator`: Normalizes vitals, computes Ideal/Real/Deviation/Recovery scores
- `PredictionSystem`: Classifies recovery status, analyzes trends
- `RecommendationEngine`: Rule-based clinical decision support

**Design Patterns:**
- Strategy Pattern for scoring algorithms (enables A/B testing different formulas)
- Chain of Responsibility for recommendation prioritization
- Service Layer Pattern for clean separation from data access

#### 3. ML Layer

**Responsibilities:**
- Model training with multiple architectures
- Model versioning and serialization
- Real-time inference with <500ms latency
- SHAP-based model explainability
- Feature scaling and preprocessing
- Model performance monitoring

**Components:**
- `ModelTrainer`: Handles training pipeline for Logistic Regression, Random Forest, XGBoost, LSTM
- `ModelRegistry`: Manages model versions, metadata, and deployment
- `InferenceEngine`: Loads models, performs predictions, returns probabilities and risk levels
- `SHAPExplainer`: Computes feature attributions using SHAP values
- `FeaturePreprocessor`: Applies scaling, normalization, encoding consistent with training

**Technology Stack:**
- scikit-learn 1.5+ for classical ML models
- XGBoost 2.0+ for gradient boosting
- TensorFlow/Keras 2.17+ for LSTM models
- SHAP 0.45+ for explainability
- joblib for model serialization
- NumPy/Pandas for data manipulation

**Key Design Decisions:**
- Model versioning with semantic versioning (v1.0, v1.1, etc.)
- A/B testing support via traffic splitting
- Background dataset sampling (100 samples) for SHAP performance
- Model hot-swapping without server restart
- Separate training and inference code paths


#### 4. Data Layer

**Responsibilities:**
- Database connection management with pooling
- ORM-based data access
- Query optimization and indexing
- Transaction management
- Data validation at persistence layer

**Components:**
- `DatabaseSession`: Async SQLAlchemy session factory with dependency injection
- `PatientRepository`: CRUD operations for patient records
- `StatisticsRepository`: Aggregation queries for dashboard
- `ModelRepository`: Storage and retrieval of trained models

**Technology Stack:**
- SQLAlchemy 2.0+ with async support
- asyncpg for PostgreSQL async driver
- Alembic for database migrations
- PostgreSQL 15+ as relational database

**Key Design Decisions:**
- Async engine with connection pooling (pool_size=20, max_overflow=10)
- Repository pattern for data access abstraction
- Composite primary key (Patient_ID, Day) for time-series data
- Indexes on Patient_ID, Day, Disease_Type, Risk_Level
- ACID compliance for data integrity

#### 5. Data Processing Pipeline

**Responsibilities:**
- ETL for raw patient data ingestion
- Feature engineering for ML models
- Missing value imputation
- Categorical encoding (one-hot)
- Numerical normalization (min-max or z-score)
- Train/validation/test splitting (70/15/15) with patient-level stratification

**Components:**
- `DataLoader`: CSV and database data ingestion
- `FeatureEngineer`: Creates derived features (compliance_score, deviation_score, health_trend)
- `DataCleaner`: Handles missing values, outliers, invalid records
- `DataTransformer`: Encoding and normalization
- `DataSplitter`: Patient-aware splitting to prevent data leakage

**Key Design Decisions:**
- Patient-level splitting prevents same patient in train/test
- Median imputation for numerical, mode for categorical
- Pipeline persistence with joblib for consistent preprocessing
- Derived features computed at ingestion time for efficiency

## Components and Interfaces

### API Endpoints

#### 1. GET /patients

**Purpose**: Retrieve paginated list of patient summaries with optional filtering

**Request Parameters**:
- `page` (int, optional, default=1): Page number
- `page_size` (int, optional, default=10, max=100): Results per page
- `disease_type` (str, optional): Filter by Disease_Type enum
- `risk_level` (str, optional): Filter by Risk_Level enum

**Response Schema**:
```typescript
{
  data: PatientSummary[],
  pagination: {
    page: number,
    page_size: number,
    total: number,
    total_pages: number
  }
}
```

**Performance Target**: <200ms at p95

**Sorting Logic**: Risk_Level (Critical → High → Medium → Low), then Readmission_Probability descending


#### 2. GET /patients/{patient_id}/summary

**Purpose**: Retrieve 30-day daily trend data for a specific patient

**Path Parameters**:
- `patient_id` (str, required): Unique patient identifier

**Response Schema**:
```typescript
{
  patient_id: string,
  patient_name: string,
  disease_type: string,
  current_risk_level: string,
  current_recovery_status: string,
  daily_trends: DailyTrend[]  // Array of 30 days (or fewer if less data available)
}

interface DailyTrend {
  day: number,
  compliance_score: number,
  deviation_score: number,
  recovery_score: number,
  health_trend: string,
  readmission_probability: number,
  real_health_score: number,
  ideal_health_score: number
}
```

**Error Handling**:
- 404 if patient_id does not exist
- 500 for database errors

**Performance Target**: <100ms at p95

#### 3. POST /predict

**Purpose**: Generate readmission prediction for patient record

**Request Body Schema**:
```typescript
interface PredictRequest {
  // Demographics
  patient_id: string,
  age: number,
  gender: "Male" | "Female" | "Other",
  bmi: number,
  smoking_status: "Never" | "Former" | "Current",
  alcohol_consumption: "None" | "Moderate" | "Heavy",
  disease_type: string,
  
  // Vitals
  heart_rate: number,
  systolic_bp: number,
  diastolic_bp: number,
  spo2: number,
  respiratory_rate: number,
  body_temperature: number,
  
  // Prescribed Plan (Ideal Twin)
  expected_steps: number,
  expected_sleep_hours: number,
  water_intake_goal: number,
  
  // Actual Behavior (Real Twin)
  actual_steps: number,
  actual_sleep_hours: number,
  water_intake: number,
  medication_taken: "Yes" | "No",
  exercise_completed: "Yes" | "No",
  diet_compliance: number  // 0-100
}
```

**Response Schema**:
```typescript
{
  patient_id: string,
  readmission_probability: number,  // 0-1
  risk_level: "Low" | "Medium" | "High" | "Critical",
  recovery_status: string,
  health_trend: "Increasing" | "Stable" | "Declining",
  compliance_score: number,  // 0-100
  deviation_score: number,  // 0-100
  ideal_health_score: number,  // 0-100
  real_health_score: number,  // 0-100
  recovery_score: number,  // 0-100
  doctor_recommendation: string,
  shap_explanation: {
    top_features: Array<{
      feature_name: string,
      shap_value: number,
      direction: "positive" | "negative"
    }>
  } | "unavailable"
}
```

**Validation**:
- All required fields present
- Numerical values in plausible ranges (e.g., age 0-120, BMI 10-60, vitals within physiological limits)
- Enum values match predefined options

**Performance Target**: <500ms at p95 (including ML inference and SHAP)


#### 4. GET /dashboard/stats

**Purpose**: Retrieve aggregated statistics for dashboard KPIs

**Response Schema**:
```typescript
{
  total_patients: number,
  high_risk_count: number,
  avg_compliance: number,
  avg_readmission_probability: number,
  risk_distribution: {
    low: number,
    medium: number,
    high: number,
    critical: number
  },
  recovery_distribution: {
    recovered: number,
    improving: number,
    stable: number,
    delayed_recovery: number,
    worsening: number,
    critical: number
  }
}
```

**Caching Strategy**: 5-minute TTL to reduce database load

**Performance Target**: <300ms at p95 (with caching)

#### 5. GET /model/info

**Purpose**: Retrieve current ML model version and metadata

**Response Schema**:
```typescript
{
  model_version: string,  // e.g., "v1.2"
  model_type: string,  // e.g., "XGBoost"
  training_date: string,  // ISO 8601
  dataset_size: number,
  evaluation_metrics: {
    accuracy: number,
    precision: number,
    recall: number,
    f1_score: number,
    auc_roc: number
  }
}
```

### Service Interfaces

#### DigitalTwinEngine

```python
class DigitalTwinEngine:
    """Compares Ideal Twin against Real Twin to compute deviation metrics."""
    
    def __init__(
        self,
        compliance_calculator: ComplianceCalculator,
        health_score_calculator: HealthScoreCalculator
    ):
        pass
    
    async def compute_deviations(
        self,
        patient_record: PatientRecord
    ) -> DeviationMetrics:
        """
        Computes deviation metrics between Ideal and Real twins.
        
        Returns:
            DeviationMetrics with step_deviation, sleep_deviation,
            water_deviation, medication_compliance, exercise_compliance,
            overall_deviation_score
        """
        pass
    
    async def compute_health_scores(
        self,
        patient_record: PatientRecord,
        historical_records: List[PatientRecord]
    ) -> HealthScores:
        """
        Computes Ideal, Real, Deviation, and Recovery scores.
        
        Args:
            patient_record: Current patient data
            historical_records: Last 30 days for trend analysis
        
        Returns:
            HealthScores with ideal_health_score, real_health_score,
            deviation_score, recovery_score
        """
        pass
```


#### ComplianceCalculator

```python
class ComplianceCalculator:
    """Calculates weighted compliance score from patient adherence metrics."""
    
    # Weights for compliance components
    MEDICATION_WEIGHT = 0.30
    EXERCISE_WEIGHT = 0.20
    STEPS_WEIGHT = 0.15
    SLEEP_WEIGHT = 0.15
    DIET_WEIGHT = 0.10
    WATER_WEIGHT = 0.10
    
    async def calculate_compliance_score(
        self,
        patient_records: List[PatientRecord],
        window_days: int = 7
    ) -> float:
        """
        Computes weighted compliance score over a time window.
        
        Args:
            patient_records: Patient data for the time window
            window_days: Number of days to analyze
        
        Returns:
            Compliance score between 0 and 100
        
        Algorithm:
            1. Medication compliance = (days with medication_taken="Yes") / total_days
            2. Exercise compliance = (days with exercise_completed="Yes") / total_days
            3. Step compliance = min(100, avg(actual_steps / expected_steps) * 100)
            4. Sleep compliance = 100 - avg(|actual - expected| / expected * 100)
            5. Diet compliance = avg(diet_compliance field)
            6. Water compliance = min(100, avg(water_intake / water_goal) * 100)
            7. Overall = sum(component * weight)
        """
        pass
```

#### HealthScoreCalculator

```python
class HealthScoreCalculator:
    """Calculates normalized health scores based on vitals and recovery trajectory."""
    
    # Normal ranges for vitals (age-adjusted)
    VITAL_RANGES = {
        "heart_rate": (60, 100),
        "systolic_bp": (90, 120),
        "diastolic_bp": (60, 80),
        "spo2": (95, 100),
        "respiratory_rate": (12, 20),
        "body_temperature": (36.1, 37.2)
    }
    
    async def calculate_ideal_health_score(
        self,
        patient_record: PatientRecord
    ) -> float:
        """
        Computes Ideal Health Score assuming perfect adherence.
        
        Based on:
        - Expected vitals for disease type and recovery stage
        - 100% compliance score
        - Optimal recovery trajectory
        
        Returns:
            Score between 0 and 100
        """
        pass
    
    async def calculate_real_health_score(
        self,
        patient_record: PatientRecord
    ) -> float:
        """
        Computes Real Health Score from actual measurements.
        
        Algorithm:
        1. Normalize each vital against normal range for patient's age/disease
        2. Compute vital_score = 100 * (1 - |actual - optimal| / range)
        3. Weight vitals: HR(20%), BP(25%), SpO2(20%), RR(15%), Temp(20%)
        4. Combine with compliance_score (50% vitals, 50% compliance)
        
        Returns:
            Score between 0 and 100
        """
        pass
    
    async def calculate_recovery_score(
        self,
        historical_records: List[PatientRecord]
    ) -> float:
        """
        Analyzes recovery trajectory over time.
        
        Algorithm:
        1. Extract real_health_score for last 7-30 days
        2. Fit linear regression to get trend slope
        3. Normalize slope to 0-100 scale
        4. Positive slope increases score, negative decreases
        
        Returns:
            Score between 0 and 100
        """
        pass
```


#### PredictionSystem

```python
class PredictionSystem:
    """Classifies recovery status and analyzes health trends."""
    
    def __init__(self, inference_engine: InferenceEngine):
        self.inference_engine = inference_engine
    
    async def classify_recovery_status(
        self,
        recovery_score: float,
        health_trend: str,
        risk_level: str
    ) -> str:
        """
        Classifies recovery status based on scoring rules.
        
        Rules:
        - Recovered: recovery_score > 85 AND health_trend = "Increasing"
        - Improving: 70 < recovery_score <= 85 AND health_trend = "Increasing"
        - Stable: 50 < recovery_score <= 70 AND health_trend = "Stable"
        - Delayed Recovery: 30 < recovery_score <= 50 AND health_trend = "Declining"
        - Worsening: 15 < recovery_score <= 30 AND health_trend = "Declining"
        - Critical: recovery_score <= 15 OR risk_level = "Critical"
        
        Returns:
            Recovery status string
        """
        pass
    
    async def analyze_health_trend(
        self,
        historical_records: List[PatientRecord]
    ) -> str:
        """
        Analyzes health trend direction using linear regression.
        
        Algorithm:
        1. Extract real_health_score from last 7 days
        2. If < 3 days available, return "Stable"
        3. Fit linear regression, compute slope
        4. If slope > 1.0: "Increasing"
        5. If -1.0 <= slope <= 1.0: "Stable"
        6. If slope < -1.0: "Declining"
        
        Returns:
            "Increasing", "Stable", or "Declining"
        """
        pass
    
    async def predict_readmission(
        self,
        patient_record: PatientRecord
    ) -> PredictionResult:
        """
        Generates readmission prediction with SHAP explanation.
        
        Returns:
            PredictionResult with readmission_probability, risk_level, shap_values
        """
        result = await self.inference_engine.predict(patient_record)
        return result
```

#### RecommendationEngine

```python
class RecommendationEngine:
    """Rule-based system for generating clinical recommendations."""
    
    # Recommendation priority (higher priority overrides lower)
    RECOMMENDATIONS = {
        1: "Continue Current Treatment",
        2: "Increase Monitoring",
        3: "Medication Adjustment",
        4: "Immediate Doctor Review",
        5: "Hospital Readmission"
    }
    
    async def generate_recommendation(
        self,
        risk_level: str,
        recovery_status: str,
        compliance_score: float,
        deviation_score: float,
        readmission_probability: float
    ) -> str:
        """
        Generates prioritized clinical recommendation.
        
        Rules (highest priority first):
        1. IF readmission_probability > 0.85 -> "Hospital Readmission"
        2. IF risk_level = "Critical" OR recovery_status IN ["Worsening", "Critical"] 
           -> "Immediate Doctor Review"
        3. IF risk_level = "High" OR deviation_score > 40 -> "Medication Adjustment"
        4. IF risk_level = "Medium" OR compliance_score < 60 -> "Increase Monitoring"
        5. ELSE -> "Continue Current Treatment"
        
        Returns:
            Recommendation string with reasoning logged
        """
        pass
```


#### InferenceEngine

```python
class InferenceEngine:
    """Manages ML model inference and SHAP explainability."""
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        shap_explainer: SHAPExplainer,
        feature_preprocessor: FeaturePreprocessor
    ):
        self.model = None
        self.model_version = None
    
    async def load_model(self, version: str = "latest") -> None:
        """Loads trained model from registry into memory."""
        pass
    
    async def predict(
        self,
        patient_record: PatientRecord
    ) -> PredictionResult:
        """
        Generates prediction with probability and risk level.
        
        Algorithm:
        1. Preprocess features (scaling, encoding)
        2. Run model inference -> probability (0-1)
        3. Classify risk level:
           - Low: probability < 0.3
           - Medium: 0.3 <= probability < 0.6
           - High: 0.6 <= probability < 0.85
           - Critical: probability >= 0.85
        4. Compute SHAP values for top 5 features
        5. Return PredictionResult
        
        Timeout: Must complete within 500ms
        
        Returns:
            PredictionResult with probability, risk_level, shap_explanation
        """
        pass
    
    async def batch_predict(
        self,
        patient_records: List[PatientRecord]
    ) -> List[PredictionResult]:
        """Optimized batch inference for multiple patients."""
        pass

class SHAPExplainer:
    """Computes SHAP values for model explainability."""
    
    def __init__(self, background_samples: np.ndarray):
        """
        Args:
            background_samples: 100 representative samples for SHAP kernel
        """
        self.explainer = None
    
    async def explain(
        self,
        model: Any,
        features: np.ndarray
    ) -> SHAPResult:
        """
        Computes SHAP values and returns top 5 features.
        
        Algorithm:
        1. Use SHAP KernelExplainer with background dataset
        2. Compute SHAP values for input features
        3. Rank by absolute SHAP value magnitude
        4. Return top 5 with feature name, value, and direction
        
        Timeout: Must complete within 1 second
        
        Returns:
            SHAPResult with top_features array
        """
        pass
```

## Data Models

### Database Schema

```sql
-- Patient Records Table (Time-Series Data)
CREATE TABLE patient_records (
    patient_id VARCHAR(50) NOT NULL,
    day INTEGER NOT NULL,
    
    -- Demographics
    patient_name VARCHAR(100),
    age INTEGER,
    gender VARCHAR(10),
    bmi DECIMAL(5,2),
    smoking_status VARCHAR(20),
    alcohol_consumption VARCHAR(20),
    disease_type VARCHAR(50),
    
    -- Vitals
    heart_rate INTEGER,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    spo2 DECIMAL(5,2),
    respiratory_rate INTEGER,
    body_temperature DECIMAL(4,2),
    
    -- Ideal Twin (Prescribed Plan)
    expected_steps INTEGER,
    expected_sleep_hours DECIMAL(4,2),
    water_intake_goal INTEGER,
    
    -- Real Twin (Actual Behavior)
    actual_steps INTEGER,
    actual_sleep_hours DECIMAL(4,2),
    water_intake INTEGER,
    medication_taken VARCHAR(3),
    exercise_completed VARCHAR(3),
    diet_compliance DECIMAL(5,2),
    
    -- Computed Scores
    compliance_score DECIMAL(5,2),
    ideal_health_score DECIMAL(5,2),
    real_health_score DECIMAL(5,2),
    deviation_score DECIMAL(5,2),
    recovery_score DECIMAL(5,2),
    
    -- AI Predictions
    readmission_probability DECIMAL(5,4),
    risk_level VARCHAR(20),
    health_trend VARCHAR(20),
    recovery_status VARCHAR(50),
    doctor_recommendation TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (patient_id, day),
    INDEX idx_patient_id (patient_id),
    INDEX idx_day (day),
    INDEX idx_disease_type (disease_type),
    INDEX idx_risk_level (risk_level),
    INDEX idx_recovery_status (recovery_status)
);
```


### Pydantic Models

```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List
from datetime import datetime

class PatientRecord(BaseModel):
    """Complete patient record with all fields."""
    
    # Demographics
    patient_id: str
    patient_name: Optional[str] = None
    age: int = Field(ge=0, le=120)
    gender: Literal["Male", "Female", "Other"]
    bmi: float = Field(ge=10.0, le=60.0)
    smoking_status: Literal["Never", "Former", "Current"]
    alcohol_consumption: Literal["None", "Moderate", "Heavy"]
    disease_type: str
    
    # Vitals
    heart_rate: int = Field(ge=30, le=220)
    systolic_bp: int = Field(ge=60, le=250)
    diastolic_bp: int = Field(ge=40, le=150)
    spo2: float = Field(ge=70.0, le=100.0)
    respiratory_rate: int = Field(ge=8, le=40)
    body_temperature: float = Field(ge=35.0, le=42.0)
    
    # Ideal Twin
    expected_steps: int = Field(ge=0)
    expected_sleep_hours: float = Field(ge=0.0, le=24.0)
    water_intake_goal: int = Field(ge=0)
    
    # Real Twin
    actual_steps: int = Field(ge=0)
    actual_sleep_hours: float = Field(ge=0.0, le=24.0)
    water_intake: int = Field(ge=0)
    medication_taken: Literal["Yes", "No"]
    exercise_completed: Literal["Yes", "No"]
    diet_compliance: float = Field(ge=0.0, le=100.0)
    
    # Computed fields (optional for input, required for output)
    compliance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    ideal_health_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    real_health_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    deviation_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    recovery_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    readmission_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_level: Optional[Literal["Low", "Medium", "High", "Critical"]] = None
    health_trend: Optional[Literal["Increasing", "Stable", "Declining"]] = None
    recovery_status: Optional[str] = None
    doctor_recommendation: Optional[str] = None
    
    day: Optional[int] = None
    
    @validator('diastolic_bp')
    def validate_blood_pressure(cls, v, values):
        """Ensure diastolic BP is less than systolic BP."""
        if 'systolic_bp' in values and v >= values['systolic_bp']:
            raise ValueError('Diastolic BP must be less than Systolic BP')
        return v

class PredictionResult(BaseModel):
    """ML prediction output with explainability."""
    
    patient_id: str
    readmission_probability: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    recovery_status: str
    health_trend: Literal["Increasing", "Stable", "Declining"]
    compliance_score: float = Field(ge=0.0, le=100.0)
    deviation_score: float = Field(ge=0.0, le=100.0)
    ideal_health_score: float = Field(ge=0.0, le=100.0)
    real_health_score: float = Field(ge=0.0, le=100.0)
    recovery_score: float = Field(ge=0.0, le=100.0)
    doctor_recommendation: str
    shap_explanation: Optional[dict] = None

class PatientSummary(BaseModel):
    """Condensed patient info for list view."""
    
    patient_id: str
    patient_name: str
    age: int
    gender: str
    disease_type: str
    risk_level: str
    recovery_status: str
    compliance_score: float
    readmission_probability: float
    last_updated: datetime

class DashboardStats(BaseModel):
    """Aggregated statistics for dashboard."""
    
    total_patients: int
    high_risk_count: int
    avg_compliance: float
    avg_readmission_probability: float
    risk_distribution: dict[str, int]
    recovery_distribution: dict[str, int]
```


### Model Training Schema

```sql
-- Model Metadata Table
CREATE TABLE ml_models (
    model_id SERIAL PRIMARY KEY,
    model_version VARCHAR(20) UNIQUE NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- 'LogisticRegression', 'RandomForest', 'XGBoost', 'LSTM'
    model_path VARCHAR(255) NOT NULL,
    training_date TIMESTAMP NOT NULL,
    dataset_size INTEGER NOT NULL,
    accuracy DECIMAL(5,4),
    precision DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_roc DECIMAL(5,4),
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- A/B Testing Configuration
CREATE TABLE model_deployment_config (
    config_id SERIAL PRIMARY KEY,
    model_version VARCHAR(20) NOT NULL,
    traffic_percentage INTEGER NOT NULL,  -- 0-100
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_version) REFERENCES ml_models(model_version)
);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be combined or are redundant:

- Deviation calculations for steps, sleep, and water (5.1-5.3) can be combined into a single property about deviation computation
- Compliance calculations for medication and exercise (6.1-6.2) follow the same pattern and can be combined
- Health score range validation properties (5.6-5.8, 6.8, 7.8) all test the same constraint (0-100 range) and can be combined
- Trend classification properties (9.2-9.4) can be combined into a single property about slope-based classification
- Filtering properties (13.1-13.2) follow the same pattern and can be combined
- Validation properties (17.1-17.5) can be consolidated into broader validation properties

### Property 1: API Pagination Correctness

*For any* valid page number and page_size parameter combination, the paginated API response SHALL return exactly page_size records (or fewer if on the last page), and the pagination metadata SHALL correctly reflect page, page_size, total records, and total_pages values consistent with the pagination formula: total_pages = ceiling(total / page_size).

**Validates: Requirements 1.5, 13.3, 13.4**

### Property 2: Database Persistence Round-Trip

*For any* valid PatientRecord with all required fields, writing the record to the database and then reading it back SHALL produce an equivalent record with all field values preserved.

**Validates: Requirements 2.1**

### Property 3: Query Ordering Consistency

*For any* patient with multiple day records in the database, querying for that patient's 30-day trend SHALL return records ordered by day in strictly ascending order.

**Validates: Requirements 2.5, 18.3**

### Property 4: Latest Record Selection

*For any* set of patient records with multiple days per patient, querying for patient summaries SHALL return only the record with the maximum day value for each unique patient_id.

**Validates: Requirements 2.4**

### Property 5: Data Validation Rejection

*For any* PatientRecord that violates field constraints (missing required fields, numerical values outside physiologically plausible ranges, invalid enum values, scores outside 0-100 or 0-1 ranges), the API SHALL reject the request with HTTP 422 and return a detailed list of validation errors.

**Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6**


### Property 6: Filter Correctness

*For any* disease_type or risk_level filter parameter, all returned patient records SHALL match the specified filter value exactly.

**Validates: Requirements 13.1, 13.2**

### Property 7: Sort Order Correctness

*For any* set of patient summaries, the returned list SHALL be sorted first by risk_level in priority order (Critical, High, Medium, Low) and then by readmission_probability in descending order within each risk level group.

**Validates: Requirements 13.6**

### Property 8: Model Serialization Round-Trip

*For any* trained ML model, serializing the model to disk and then deserializing it SHALL produce a model that generates identical predictions for the same input features.

**Validates: Requirements 3.6**

### Property 9: Data Split Patient Isolation

*For any* data split into training, validation, and test sets, each unique patient_id SHALL appear in exactly one set (no patient records SHALL appear in multiple sets).

**Validates: Requirements 11.6**

### Property 10: Missing Value Imputation Completeness

*For any* patient dataset with missing values, after applying the data processing pipeline, the resulting feature matrix SHALL contain no missing values (all NaN values SHALL be imputed).

**Validates: Requirements 11.2**

### Property 11: Categorical Encoding Correctness

*For any* categorical variable value in the input data, the one-hot encoding SHALL produce a binary vector where exactly one position is 1 and all others are 0, with the number of positions equal to the number of unique categories.

**Validates: Requirements 11.3**

### Property 12: Feature Normalization Range

*For any* numerical feature after normalization using min-max scaling, the normalized value SHALL be in the range [0, 1]. For z-score normalization, the mean SHALL be 0 and standard deviation SHALL be 1 across the feature.

**Validates: Requirements 11.4**

### Property 13: Prediction Probability Range

*For any* valid PatientRecord input to the inference engine, the returned readmission_probability SHALL be a value in the range [0, 1].

**Validates: Requirements 4.2**

### Property 14: Risk Level Classification Correctness

*For any* readmission_probability value, the risk_level SHALL be classified as: "Low" if probability < 0.3, "Medium" if 0.3 ≤ probability < 0.6, "High" if 0.6 ≤ probability < 0.85, and "Critical" if probability ≥ 0.85.

**Validates: Requirements 4.3**

### Property 15: SHAP Feature Count

*For any* prediction with SHAP explanation enabled, the returned SHAP explanation SHALL contain exactly 5 features ranked by absolute SHAP value magnitude.

**Validates: Requirements 4.4, 14.2, 14.3**

### Property 16: Deviation Computation Correctness

*For any* pair of expected and actual values (steps, sleep hours, water intake), the computed deviation SHALL equal the absolute difference |expected - actual|.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 17: Deviation Score Range

*For any* set of individual deviations, the aggregated Deviation_Score SHALL be a value in the range [0, 100].

**Validates: Requirements 5.6**

### Property 18: Health Score Range

*For any* computed health score (Ideal_Health_Score, Real_Health_Score, Recovery_Score), the value SHALL be in the range [0, 100].

**Validates: Requirements 5.7, 5.8, 6.8, 7.1, 7.2, 7.8**


### Property 19: Compliance Percentage Calculation

*For any* sequence of binary adherence values (medication_taken, exercise_completed), the compliance percentage SHALL equal (count of "Yes" values / total count) × 100.

**Validates: Requirements 6.1, 6.2**

### Property 20: Step and Water Compliance Capping

*For any* actual and expected values for steps or water intake, the compliance score SHALL equal min(100, (actual / expected) × 100), ensuring the score never exceeds 100% even when actual exceeds expected.

**Validates: Requirements 6.3, 6.6**

### Property 21: Sleep Compliance Formula

*For any* expected and actual sleep hours, the sleep compliance SHALL equal 100 - (|expected - actual| / expected) × 100, where the result is clamped to [0, 100].

**Validates: Requirements 6.4**

### Property 22: Weighted Compliance Aggregation

*For any* set of sub-compliance scores (medication, exercise, steps, sleep, diet, water), the overall Compliance_Score SHALL equal the weighted sum: 0.30×medication + 0.20×exercise + 0.15×steps + 0.15×sleep + 0.10×diet + 0.10×water.

**Validates: Requirements 6.7**

### Property 23: Vital Normalization Consistency

*For any* vital sign measurement and patient characteristics (age, disease_type), the normalization function SHALL produce consistent normalized values when called multiple times with the same inputs.

**Validates: Requirements 7.3**

### Property 24: Deviation Score Formula

*For any* Ideal_Health_Score and Real_Health_Score, the Deviation_Score SHALL equal the absolute difference |Ideal_Health_Score - Real_Health_Score|.

**Validates: Requirements 7.4**

### Property 25: Recovery Score Trend Correlation

*For any* improving sequence of Real_Health_Score values over 7 days (positive slope > 1.0), the Recovery_Score SHALL be greater than the Recovery_Score for a stable sequence (slope ≈ 0) with the same average value.

**Validates: Requirements 7.6**

### Property 26: Declining Score Trend Correlation

*For any* declining sequence of Real_Health_Score values over 7 days (negative slope < -1.0), the Recovery_Score SHALL be less than the Recovery_Score for a stable sequence (slope ≈ 0) with the same average value.

**Validates: Requirements 7.7**

### Property 27: Health Trend Slope Classification

*For any* sequence of at least 3 Real_Health_Score values, the Health_Trend SHALL be classified as: "Increasing" if linear regression slope > 1.0, "Stable" if -1.0 ≤ slope ≤ 1.0, and "Declining" if slope < -1.0.

**Validates: Requirements 9.2, 9.3, 9.4**

### Property 28: Recommendation Prioritization

*For any* combination of patient metrics that trigger multiple recommendation rules simultaneously, the returned recommendation SHALL be the one with the highest priority level (Hospital Readmission > Immediate Doctor Review > Medication Adjustment > Increase Monitoring > Continue Current Treatment).

**Validates: Requirements 10.6**

### Property 29: Dashboard Unique Patient Count

*For any* set of patient records from the last 30 days, the total_patients count SHALL equal the number of unique patient_id values in that set.

**Validates: Requirements 12.1**

### Property 30: Dashboard Risk Distribution Accuracy

*For any* set of patient records, the risk_distribution counts SHALL equal the actual counts of patients in each Risk_Level category (Low, Medium, High, Critical), and the sum of all category counts SHALL equal total_patients.

**Validates: Requirements 12.2**


### Property 31: Dashboard Recovery Distribution Accuracy

*For any* set of patient records, the recovery_distribution counts SHALL equal the actual counts of patients in each Recovery_Status category, and the sum of all category counts SHALL equal total_patients.

**Validates: Requirements 12.3**

### Property 32: Dashboard Average Calculations

*For any* set of patient records, the avg_compliance SHALL equal the arithmetic mean of all Compliance_Score values, and avg_readmission_probability SHALL equal the arithmetic mean of all Readmission_Probability values.

**Validates: Requirements 12.4, 12.5**

### Property 33: High Risk Count Filter

*For any* set of patient records, the high_risk_count SHALL equal the count of records where Risk_Level is either "High" or "Critical".

**Validates: Requirements 12.6**

### Property 34: Data Split Proportion Accuracy

*For any* dataset split into training, validation, and test sets, the proportions SHALL be approximately 70%, 15%, and 15% respectively (within ±2% tolerance to account for rounding with integer record counts).

**Validates: Requirements 3.2**

### Property 35: SHAP Value Feature Ranking

*For any* set of SHAP values computed for input features, the returned features SHALL be ordered by descending absolute SHAP value magnitude (|SHAP_value|).

**Validates: Requirements 14.2**

### Property 36: Input Sanitization Safety

*For any* string input containing SQL injection patterns (e.g., `'; DROP TABLE--`) or XSS patterns (e.g., `<script>alert('XSS')</script>`), the sanitized output SHALL not contain executable SQL commands or script tags.

**Validates: Requirements 17.7**

## Error Handling

### Error Handling Strategy

The system implements a layered error handling approach:

1. **Validation Layer**: Pydantic models validate input at API boundary
2. **Business Logic Layer**: Custom exceptions for domain-specific errors
3. **Data Layer**: Database constraint violations and connection errors
4. **ML Layer**: Model loading, inference, and SHAP computation errors
5. **HTTP Layer**: FastAPI exception handlers map exceptions to HTTP status codes

### Error Types and HTTP Status Codes

```python
class APIError(Exception):
    """Base exception for API errors."""
    status_code: int = 500
    detail: str = "Internal server error"

class ValidationError(APIError):
    """Input validation failed."""
    status_code = 422
    
class NotFoundError(APIError):
    """Resource not found."""
    status_code = 404
    
class DatabaseError(APIError):
    """Database operation failed."""
    status_code = 500
    
class ModelInferenceError(APIError):
    """ML model inference failed."""
    status_code = 503  # Service Unavailable
    detail = "Prediction service temporarily unavailable"
    
class SHAPComputationError(APIError):
    """SHAP explainability computation failed."""
    status_code = 200  # Return prediction without explanation
    detail = "Prediction successful, explainability unavailable"
```

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "age",
        "issue": "value must be between 0 and 120"
      },
      {
        "field": "systolic_bp",
        "issue": "value must be greater than diastolic_bp"
      }
    ]
  }
}
```


### Graceful Degradation

- **SHAP Timeout**: If SHAP computation exceeds 1 second, return prediction without explanation
- **Model Loading Failure**: API returns 503 for prediction endpoints, continues serving patient data endpoints
- **Database Connection Loss**: Implement exponential backoff reconnection (1s, 2s, 4s, 8s, 16s max)
- **Cache Miss**: If dashboard stats cache expires during high load, serve stale data with warning header
- **Partial Data**: If a patient has <30 days of data, return available days rather than failing

### Logging Strategy

```python
import structlog

logger = structlog.get_logger()

# Log levels:
# DEBUG: Detailed diagnostic information
# INFO: General system events (API requests, predictions)
# WARNING: Unusual conditions that don't prevent operation (SHAP timeout, slow queries)
# ERROR: Errors that prevent specific operations (inference failure, validation error)
# CRITICAL: System-wide failures (database down, model missing)

# Example structured logs:
logger.info(
    "prediction_generated",
    patient_id=patient_id,
    readmission_probability=prob,
    risk_level=risk,
    inference_time_ms=elapsed_ms
)

logger.warning(
    "shap_computation_timeout",
    patient_id=patient_id,
    timeout_ms=1000
)

logger.error(
    "database_connection_failed",
    error=str(exc),
    retry_attempt=attempt,
    next_retry_seconds=backoff
)
```

## Testing Strategy

### Testing Approach

The backend ML system will employ a comprehensive dual-testing strategy:

1. **Property-Based Tests**: Validate universal properties across randomized inputs using Hypothesis library
2. **Unit Tests**: Verify specific examples, edge cases, and integration points using pytest

### Property-Based Testing

**Library**: Hypothesis 6.100+

**Configuration**: Each property test runs a minimum of 100 iterations to thoroughly explore the input space.

**Test Organization**: Property tests are organized by component and tagged with design property references.

**Tag Format**: `# Feature: backend-ml-system, Property {number}: {property_text}`

**Example Property Test**:

```python
from hypothesis import given, strategies as st
import pytest

@given(
    page=st.integers(min_value=1, max_value=1000),
    page_size=st.integers(min_value=1, max_value=100)
)
@pytest.mark.property
def test_pagination_correctness(page, page_size):
    """
    Feature: backend-ml-system, Property 1: API Pagination Correctness
    
    For any valid page number and page_size, verify pagination math is correct.
    """
    # Setup: Create test data with known size
    total_records = 247
    
    # Execute: Calculate pagination
    expected_total_pages = math.ceil(total_records / page_size)
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_records)
    expected_count = end_idx - start_idx if page <= expected_total_pages else 0
    
    # Call API
    response = client.get(f"/patients?page={page}&page_size={page_size}")
    
    # Assert: Verify pagination metadata
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["page"] == page
    assert data["pagination"]["page_size"] == page_size
    assert data["pagination"]["total"] == total_records
    assert data["pagination"]["total_pages"] == expected_total_pages
    assert len(data["data"]) == expected_count
```


### Unit Testing

**Library**: pytest 8.0+

**Coverage Target**: 85% code coverage minimum

**Test Categories**:

1. **Example Tests**: Verify specific scenarios work correctly
2. **Edge Case Tests**: Test boundary conditions and special cases
3. **Integration Tests**: Test component interactions and infrastructure
4. **Smoke Tests**: Verify configuration and setup

**Example Unit Tests**:

```python
def test_get_patients_endpoint_exists():
    """Verify /patients endpoint returns expected structure."""
    response = client.get("/patients")
    assert response.status_code == 200
    assert "data" in response.json()
    assert "pagination" in response.json()

def test_patient_summary_not_found():
    """Edge case: Non-existent patient ID returns 404."""
    response = client.get("/patients/INVALID_ID/summary")
    assert response.status_code == 404
    assert "error" in response.json()

def test_invalid_prediction_request():
    """Edge case: Invalid patient data returns 422."""
    invalid_data = {"age": -5, "bmi": 200}  # Invalid values
    response = client.post("/predict", json=invalid_data)
    assert response.status_code == 422
    assert "details" in response.json()["error"]

def test_recovery_status_critical():
    """Edge case: Recovery score < 15 classified as Critical."""
    recovery_score = 10
    health_trend = "Declining"
    risk_level = "High"
    
    status = prediction_system.classify_recovery_status(
        recovery_score, health_trend, risk_level
    )
    assert status == "Critical"
```

### ML Model Testing

**Training Tests**:
- Verify model converges on synthetic data with known patterns
- Test train/val/test split patient isolation (no patient appears in multiple sets)
- Verify evaluation metrics are computed correctly
- Test model serialization and deserialization

**Inference Tests**:
- Property test: All predictions are in [0, 1] range
- Property test: Risk level classification matches probability thresholds
- Property test: SHAP returns exactly 5 features
- Performance test: Inference completes within 500ms
- Edge case: Handle missing features gracefully

**Feature Engineering Tests**:
- Property test: No missing values after imputation
- Property test: One-hot encoding produces correct binary vectors
- Property test: Normalized features in expected range
- Property test: Derived features computed correctly

### Integration Testing

**Database Integration**:
- Test ACID transaction behavior
- Test concurrent read/write operations
- Test connection pooling under load
- Test index performance on large datasets

**API Integration**:
- Test CORS headers are present
- Test error response formats
- Test API response times under load
- Test rate limiting behavior

**End-to-End Tests**:
- Test complete prediction workflow: input → preprocessing → inference → SHAP → response
- Test dashboard stats computation with real data
- Test patient summary generation with 30 days of data

### Performance Testing

**Load Testing** (using Locust or Apache Bench):
- Verify 100 concurrent requests without degradation
- Measure p50, p95, p99 latencies for all endpoints
- Test database connection pool exhaustion scenarios
- Verify cache effectiveness for dashboard stats

**Benchmarks**:
- `/patients`: <200ms at p95
- `/predict`: <500ms at p95
- `/dashboard/stats`: <300ms at p95 (with cache)
- `/patients/{id}/summary`: <100ms at p95

## Deployment Architecture

### Production Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer (AWS ALB)                 │
│                    SSL Termination + Health Checks           │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  FastAPI App    │     │  FastAPI App    │
│  Container 1    │     │  Container 2    │
│  (ECS/K8s)      │     │  (ECS/K8s)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  PostgreSQL     │     │  Redis Cache    │
│  (RDS/Aurora)   │     │  (ElastiCache)  │
│  Read Replicas  │     │  Dashboard Stats│
└─────────────────┘     └─────────────────┘
```


### Container Configuration

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Environment Variables**:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://frontend.example.com
LOG_LEVEL=INFO

# ML Model
MODEL_VERSION=latest
MODEL_PATH=/app/models
SHAP_TIMEOUT_MS=1000

# Cache
REDIS_URL=redis://cache:6379
CACHE_TTL_SECONDS=300

# Performance
RATE_LIMIT_PER_HOUR=1000
MAX_REQUEST_SIZE_MB=1
```

### Horizontal Scaling Strategy

**Stateless Design**: All application state stored in database/cache, enabling horizontal scaling

**Auto-Scaling Triggers**:
- CPU utilization > 70% for 2 minutes → Scale up
- Request latency p95 > 1 second for 5 minutes → Scale up
- CPU utilization < 30% for 10 minutes → Scale down

**Scaling Limits**:
- Minimum instances: 2 (high availability)
- Maximum instances: 10 (cost control)
- Scale up: Add 1 instance at a time
- Scale down: Remove 1 instance at a time
- Cooldown period: 5 minutes between scaling actions

### Database Optimization

**Connection Pooling**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # Persistent connections
    max_overflow=10,  # Burst capacity
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Disable SQL logging in production
)
```

**Query Optimization**:
- Composite index on (patient_id, day) for time-series queries
- Separate indexes on disease_type, risk_level for filtering
- Use of `EXPLAIN ANALYZE` to identify slow queries
- Read replicas for dashboard aggregations

**Caching Strategy**:
- Cache dashboard stats in Redis with 5-minute TTL
- Cache patient summaries with 1-minute TTL
- Invalidate cache on data updates using pub/sub

## Security Considerations

### Authentication and Authorization (Future)

The current design does not include authentication, but production deployment should include:

- **OAuth 2.0** with OIDC for healthcare provider authentication
- **Role-Based Access Control (RBAC)**: Separate permissions for doctors, nurses, administrators
- **API Keys**: For programmatic access from frontend or third-party systems
- **JWT Tokens**: Short-lived access tokens with refresh tokens

### Data Security

**In Transit**:
- TLS 1.3 for all API communication
- Certificate pinning for mobile clients

**At Rest**:
- PostgreSQL encryption at rest using AWS RDS encryption
- Encrypted backups stored in S3 with KMS keys
- Model files encrypted with AES-256

**PII Protection**:
- Patient names and IDs should be pseudonymized
- Audit logging for all patient data access
- Data retention policy (e.g., 7 years per HIPAA)

### Input Validation and Sanitization

**SQL Injection Prevention**:
- Use parameterized queries (SQLAlchemy ORM automatically parameterizes)
- Never concatenate user input into SQL strings
- Input sanitization using `bleach` library

**XSS Prevention**:
- Sanitize all string inputs before storage
- Encode outputs in API responses
- Content-Security-Policy headers

**Request Size Limits**:
- Max request body: 1 MB
- Max URL length: 2048 characters
- Rate limiting: 1000 requests/hour per IP


## Configuration Management

### Configuration Hierarchy

1. **Default Values**: Hardcoded in application config classes
2. **Config File**: YAML/JSON config file for environment-specific settings
3. **Environment Variables**: Override config file (12-factor app pattern)
4. **Command-Line Args**: Highest priority for development/debugging

### Configuration Schema

```python
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseSettings):
    url: str
    pool_size: int = 20
    max_overflow: int = 10
    echo: bool = False
    
    class Config:
        env_prefix = "DB_"

class APIConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]
    rate_limit_per_hour: int = 1000
    max_request_size_mb: int = 1
    
    class Config:
        env_prefix = "API_"

class MLConfig(BaseSettings):
    model_version: str = "latest"
    model_path: str = "./models"
    shap_timeout_ms: int = 1000
    inference_timeout_ms: int = 500
    
    class Config:
        env_prefix = "ML_"

class CacheConfig(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    ttl_seconds: int = 300
    
    class Config:
        env_prefix = "CACHE_"

class AppConfig(BaseSettings):
    database: DatabaseConfig
    api: APIConfig
    ml: MLConfig
    cache: CacheConfig
    log_level: str = "INFO"
    
    @classmethod
    def load_config(cls, config_file: str = None) -> "AppConfig":
        """Load configuration from file and environment."""
        if config_file:
            with open(config_file) as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        return cls()
```

### Example Configuration File

```yaml
# config/production.yaml
database:
  url: postgresql+asyncpg://user:pass@db.example.com:5432/healthcare
  pool_size: 30
  max_overflow: 20
  echo: false

api:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - https://healthcare-frontend.example.com
  rate_limit_per_hour: 5000
  max_request_size_mb: 1

ml:
  model_version: v1.2
  model_path: /app/models
  shap_timeout_ms: 1000
  inference_timeout_ms: 500

cache:
  redis_url: redis://cache.example.com:6379
  ttl_seconds: 300

log_level: INFO
```

## Monitoring and Observability

### Metrics to Track

**API Metrics**:
- Request rate (requests/second)
- Response latency (p50, p95, p99)
- Error rate (4xx, 5xx responses)
- Endpoint-specific latencies

**ML Metrics**:
- Prediction latency
- SHAP computation time
- Model inference errors
- Prediction distribution (risk levels)

**Database Metrics**:
- Connection pool utilization
- Query latency
- Active connections
- Slow query count

**Business Metrics**:
- Total active patients
- High-risk patient count
- Average compliance score
- Prediction request volume

### Logging Best Practices

**Structured Logging Format** (JSON):
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "event": "prediction_generated",
  "patient_id": "P12345",
  "readmission_probability": 0.67,
  "risk_level": "High",
  "inference_time_ms": 342,
  "shap_time_ms": 856,
  "request_id": "req-abc-123"
}
```

**Log Aggregation**: Use ELK stack (Elasticsearch, Logstash, Kibana) or CloudWatch Logs

**Alerting Rules**:
- Error rate > 5% for 5 minutes → Page on-call
- API latency p95 > 2 seconds for 10 minutes → Alert
- Database connection pool exhausted → Page immediately
- Model inference error rate > 10% → Page on-call

## Implementation Roadmap

### Phase 1: Core API and Database (Weeks 1-3)

**Week 1**:
- [ ] Set up project structure (FastAPI + SQLAlchemy)
- [ ] Define Pydantic models for all data types
- [ ] Implement database schema and migrations
- [ ] Create patient repository with CRUD operations

**Week 2**:
- [ ] Implement GET /patients endpoint with filtering and pagination
- [ ] Implement GET /patients/{id}/summary endpoint
- [ ] Implement POST /predict endpoint skeleton
- [ ] Implement GET /dashboard/stats endpoint
- [ ] Add request validation and error handling

**Week 3**:
- [ ] Implement database connection pooling
- [ ] Add indexes for query optimization
- [ ] Implement CORS middleware
- [ ] Write unit tests for API endpoints
- [ ] Set up structured logging

### Phase 2: Business Logic (Weeks 4-5)

**Week 4**:
- [ ] Implement ComplianceCalculator with all scoring logic
- [ ] Implement HealthScoreCalculator with vital normalization
- [ ] Implement DigitalTwinEngine with deviation computation
- [ ] Write property-based tests for calculators

**Week 5**:
- [ ] Implement PredictionSystem for recovery status and trends
- [ ] Implement RecommendationEngine with prioritization logic
- [ ] Integrate business logic with API endpoints
- [ ] Write unit tests for business logic components


### Phase 3: ML Pipeline (Weeks 6-8)

**Week 6**:
- [ ] Implement DataProcessingPipeline for ETL
- [ ] Implement feature engineering (encoding, normalization, derived features)
- [ ] Implement patient-aware train/val/test splitting
- [ ] Write property-based tests for data pipeline

**Week 7**:
- [ ] Implement ModelTrainer for Logistic Regression, Random Forest, XGBoost
- [ ] Train baseline models on synthetic/sample data
- [ ] Implement model evaluation metrics computation
- [ ] Implement model serialization and versioning

**Week 8**:
- [ ] Implement InferenceEngine with model loading
- [ ] Integrate SHAP explainability
- [ ] Optimize inference performance (<500ms target)
- [ ] Write property-based tests for ML components

### Phase 4: Advanced Features (Weeks 9-10)

**Week 9**:
- [ ] Implement Redis caching for dashboard stats
- [ ] Implement model hot-swapping without restart
- [ ] Implement A/B testing infrastructure
- [ ] Add performance monitoring and metrics

**Week 10**:
- [ ] LSTM model implementation and training
- [ ] Advanced SHAP visualizations
- [ ] Rate limiting middleware
- [ ] Comprehensive integration testing

### Phase 5: Production Readiness (Weeks 11-12)

**Week 11**:
- [ ] Containerize application with Docker
- [ ] Set up CI/CD pipeline (GitHub Actions/GitLab CI)
- [ ] Load testing and performance optimization
- [ ] Security audit and penetration testing

**Week 12**:
- [ ] Deploy to staging environment
- [ ] User acceptance testing with frontend
- [ ] Documentation (API docs, deployment guide, runbooks)
- [ ] Production deployment

## Technical Debt and Future Enhancements

### Known Technical Debt

1. **Authentication/Authorization**: Not implemented in initial version
2. **Audit Logging**: Patient data access audit trail not implemented
3. **Data Versioning**: Model input feature versioning for reproducibility
4. **Advanced Caching**: Patient-level caching not implemented
5. **Async ML Inference**: Prediction requests block API thread

### Future Enhancements

1. **Real-Time Streaming**: Kafka/RabbitMQ for real-time patient data ingestion
2. **Advanced ML Models**: Transformer models, ensemble voting, AutoML
3. **Explainability Improvements**: LIME, counterfactual explanations, attention maps
4. **Multi-Tenancy**: Support for multiple healthcare organizations
5. **Mobile SDK**: Native mobile SDKs for iOS/Android
6. **Batch Prediction API**: Bulk prediction endpoint for operational efficiency
7. **Model Drift Detection**: Automated monitoring of model performance degradation
8. **Feature Store**: Centralized feature management and versioning
9. **GraphQL API**: Alternative to REST for flexible frontend queries
10. **FHIR Integration**: HL7 FHIR standard for healthcare interoperability

## Dependencies

### Python Dependencies

```txt
# Core Framework
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-settings==2.5.0

# Database
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
alembic==1.13.0

# ML Libraries
scikit-learn==1.5.2
xgboost==2.1.1
tensorflow==2.17.0
shap==0.45.0
numpy==1.26.4
pandas==2.2.3

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.2
structlog==24.4.0
redis==5.1.1
httpx==0.27.2

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
hypothesis==6.112.0
pytest-cov==5.0.0
locust==2.32.0

# Security
bleach==6.2.0
cryptography==43.0.1
```

### System Dependencies

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker 24+ (for containerization)
- Git (for version control)

## References

### Technical Documentation

1. [FastAPI Documentation](https://fastapi.tiangolo.com/) - Web framework
2. [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/) - ORM and async patterns
3. [SHAP Documentation](https://shap.readthedocs.io/) - Model explainability
4. [Hypothesis Documentation](https://hypothesis.readthedocs.io/) - Property-based testing
5. [Pydantic Documentation](https://docs.pydantic.dev/) - Data validation

### Research Papers

1. Lundberg, S. M., & Lee, S. I. (2017). "A Unified Approach to Interpreting Model Predictions" - SHAP methodology
2. Digital Twin architectures for healthcare monitoring systems
3. Hospital readmission prediction using machine learning: A systematic review

### Standards and Best Practices

1. [HL7 FHIR Standard](https://www.hl7.org/fhir/) - Healthcare data interoperability (future consideration)
2. [HIPAA Compliance Guidelines](https://www.hhs.gov/hipaa/) - Healthcare data privacy regulations
3. [12-Factor App Methodology](https://12factor.net/) - Cloud-native application design
4. [OpenAPI Specification](https://swagger.io/specification/) - API documentation standard

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Authors**: Backend ML System Design Team  
**Status**: Ready for Review
