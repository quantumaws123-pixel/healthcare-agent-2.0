# Implementation Plan: Backend ML System

## Overview

This implementation plan breaks down the Healthcare Agent 2.0 Backend ML System into discrete coding tasks. The system is a Python-based FastAPI application with PostgreSQL database, machine learning models for readmission prediction, and a digital twin engine for patient monitoring.

**Technology Stack**: Python 3.11+, FastAPI 0.115+, SQLAlchemy 2.0+, PostgreSQL 15+, scikit-learn 1.5+, XGBoost 2.0+, TensorFlow 2.17+, SHAP 0.45+, Hypothesis 6.100+

**Architecture**: Layered design with API layer, business logic layer, ML layer, and data layer.

## Tasks

- [x] 1. Set up project structure and core dependencies
  - Create directory structure: `app/`, `app/api/`, `app/models/`, `app/services/`, `app/repositories/`, `app/ml/`, `tests/`
  - Create `requirements.txt` with all dependencies (FastAPI, SQLAlchemy, asyncpg, Pydantic, scikit-learn, XGBoost, TensorFlow, SHAP, Hypothesis, pytest)
  - Create `app/__init__.py` and `app/main.py` with basic FastAPI application setup
  - Create `.env.example` with configuration template
  - _Requirements: 19.1, 19.2, 19.3_

- [x] 2. Define Pydantic data models and validation schemas
  - [x] 2.1 Create `app/models/schemas.py` with PatientRecord model
    - Define PatientRecord with all fields (demographics, vitals, ideal twin, real twin, computed scores)
    - Add field validation (age 0-120, BMI 10-60, vitals within physiological ranges)
    - Add custom validator for diastolic_bp < systolic_bp
    - _Requirements: 17.1, 17.2, 17.3, 17.4_
  
  - [x] 2.2 Create PredictionResult, PatientSummary, and DashboardStats models
    - Define PredictionResult with readmission_probability, risk_level, health_trend, scores, SHAP explanation
    - Define PatientSummary with condensed patient info for list view
    - Define DashboardStats with aggregated statistics
    - _Requirements: 1.1, 1.4, 12.1, 12.2, 12.3, 12.4_

  - [ ]* 2.3 Write property test for data validation rejection
    - **Property 5: Data Validation Rejection**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5**
    - Use Hypothesis to generate invalid PatientRecord instances (missing fields, out-of-range values, invalid enums)
    - Verify API returns HTTP 422 with validation error details
    - _Requirements: 17.6_


- [x] 3. Implement database layer with PostgreSQL and SQLAlchemy
  - [x] 3.1 Create `app/database/models.py` with SQLAlchemy ORM models
    - Define PatientRecordDB table with composite primary key (patient_id, day)
    - Define MLModelDB table for model metadata and versioning
    - Add indexes on patient_id, day, disease_type, risk_level, recovery_status
    - _Requirements: 2.1, 2.2, 2.6_
  
  - [x] 3.2 Create `app/database/connection.py` with async database engine and session factory
    - Set up async SQLAlchemy engine with connection pooling (pool_size=20, max_overflow=10)
    - Implement dependency injection for database sessions
    - Add health check function for database connectivity
    - _Requirements: 2.8, 19.2, 20.5_
  
  - [x] 3.3 Create Alembic migration for initial database schema
    - Initialize Alembic in project
    - Generate migration for patient_records and ml_models tables
    - Include all indexes and constraints
    - _Requirements: 2.1, 2.6_

  - [ ]* 3.4 Write property test for database persistence round-trip
    - **Property 2: Database Persistence Round-Trip**
    - **Validates: Requirements 2.1**
    - Use Hypothesis to generate valid PatientRecord instances
    - Write to database, read back, verify all fields are preserved
    - _Requirements: 2.3_

- [x] 4. Create data repositories for database access
  - [x] 4.1 Create `app/repositories/patient_repository.py` with CRUD operations
    - Implement create_patient_record, get_patient_by_id, get_patients_paginated, get_patient_summary
    - Implement query filtering by disease_type and risk_level
    - Implement pagination logic with total count calculation
    - Add sorting by risk_level priority and readmission_probability
    - _Requirements: 2.4, 2.5, 13.1, 13.2, 13.3, 13.6_

  - [x] 4.2 Create `app/repositories/statistics_repository.py` for dashboard aggregations
    - Implement compute_dashboard_stats with unique patient count, risk distribution, recovery distribution
    - Implement average calculations for compliance and readmission probability
    - Implement high_risk_count calculation (High + Critical)
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 4.3 Write property tests for query correctness
    - **Property 3: Query Ordering Consistency**
    - **Property 4: Latest Record Selection**
    - **Validates: Requirements 2.4, 2.5, 18.3**
    - Test that 30-day trend queries return records in ascending day order
    - Test that patient summaries return only latest day record per patient
    - _Requirements: 2.5, 18.3_


- [x] 5. Implement Compliance Calculator service
  - [x] 5.1 Create `app/services/compliance_calculator.py` with compliance scoring logic
    - Implement calculate_compliance_score with weighted aggregation
    - Implement individual compliance calculations: medication (30%), exercise (20%), steps (15%), sleep (15%), diet (10%), water (10%)
    - Implement step and water compliance with capping at 100%
    - Implement sleep compliance formula: 100 - |expected - actual| / expected × 100
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ]* 5.2 Write property tests for compliance calculations
    - **Property 19: Compliance Percentage Calculation**
    - **Property 20: Step and Water Compliance Capping**
    - **Property 21: Sleep Compliance Formula**
    - **Property 22: Weighted Compliance Aggregation**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.6, 6.7**
    - Use Hypothesis to generate patient records with varying adherence patterns
    - Verify compliance calculations match expected formulas
    - Test that step/water compliance never exceeds 100%
    - _Requirements: 6.8_

- [x] 6. Implement Health Score Calculator service
  - [x] 6.1 Create `app/services/health_score_calculator.py` with health score calculations
    - Define VITAL_RANGES constants for normal ranges (heart_rate, blood pressure, SpO2, respiratory_rate, temperature)
    - Implement calculate_ideal_health_score based on expected vitals and perfect compliance
    - Implement calculate_real_health_score with vital normalization and weighted scoring
    - Implement calculate_recovery_score using linear regression on 7-30 day trends
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [ ]* 6.2 Write property tests for health score calculations
    - **Property 18: Health Score Range**
    - **Property 23: Vital Normalization Consistency**
    - **Property 24: Deviation Score Formula**
    - **Property 25: Recovery Score Trend Correlation**
    - **Property 26: Declining Score Trend Correlation**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6, 7.7, 7.8**
    - Use Hypothesis to generate vital signs and verify normalized scores in [0, 100]
    - Test that improving trends increase recovery_score
    - Test that declining trends decrease recovery_score
    - Verify deviation_score = |ideal - real|
    - _Requirements: 7.8_

- [x] 7. Implement Digital Twin Engine service
  - [x] 7.1 Create `app/services/digital_twin_engine.py` with comparison logic
    - Implement compute_deviations for steps, sleep, water intake
    - Flag medication and exercise compliance violations
    - Aggregate deviations into overall deviation_score [0-100]
    - Integrate ComplianceCalculator and HealthScoreCalculator
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 7.2 Write property tests for deviation calculations
    - **Property 16: Deviation Computation Correctness**
    - **Property 17: Deviation Score Range**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.6**
    - Use Hypothesis to generate expected/actual value pairs
    - Verify deviation = |expected - actual|
    - Verify aggregated deviation_score in [0, 100]
    - _Requirements: 5.6, 5.7, 5.8_


- [x] 8. Implement Prediction System service
  - [x] 8.1 Create `app/services/prediction_system.py` with recovery status and trend analysis
    - Implement classify_recovery_status with rule-based classification (Recovered, Improving, Stable, Delayed Recovery, Worsening, Critical)
    - Implement analyze_health_trend using linear regression on 7-day real_health_score data
    - Implement slope-based classification: Increasing (>1.0), Stable (-1.0 to 1.0), Declining (<-1.0)
    - Handle edge case: <3 days of data defaults to "Stable"
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 8.2 Write property test for health trend analysis
    - **Property 27: Health Trend Slope Classification**
    - **Validates: Requirements 9.2, 9.3, 9.4**
    - Use Hypothesis to generate sequences of real_health_score values with known slopes
    - Verify classification matches slope thresholds (>1.0, [-1.0, 1.0], <-1.0)
    - Test edge case with <3 days returns "Stable"
    - _Requirements: 9.5_

- [x] 9. Implement Recommendation Engine service
  - [x] 9.1 Create `app/services/recommendation_engine.py` with rule-based recommendations
    - Define RECOMMENDATIONS priority dictionary
    - Implement generate_recommendation with prioritized rule evaluation
    - Implement rules: Hospital Readmission (prob > 0.85), Immediate Doctor Review (Critical/Worsening), Medication Adjustment (High risk/deviation > 40), Increase Monitoring (Medium risk/compliance < 60), Continue Current Treatment (default)
    - Add logging for recommendation reasoning
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [ ]* 9.2 Write property test for recommendation prioritization
    - **Property 28: Recommendation Prioritization**
    - **Validates: Requirements 10.6**
    - Use Hypothesis to generate patient metrics that trigger multiple rules
    - Verify highest priority recommendation is returned
    - _Requirements: 10.6, 10.7_

- [x] 10. Checkpoint - Ensure core business logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement data processing pipeline for ML
  - [ ] 11.1 Create `app/ml/data_loader.py` for CSV and database data ingestion
    - Implement load_from_csv and load_from_database functions
    - Handle corrupt/invalid records with logging and skipping
    - _Requirements: 11.1, 11.8_

  - [ ] 11.2 Create `app/ml/feature_engineer.py` for feature engineering and transformations
    - Implement missing value imputation (median for numerical, mode for categorical)
    - Implement one-hot encoding for categorical variables (Gender, Disease_Type, Smoking_Status, Alcohol_Consumption)
    - Implement min-max and z-score normalization functions
    - Implement derived feature creation (compliance_score, deviation_score, health_trend, recovery_score)
    - _Requirements: 11.2, 11.3, 11.4, 11.5_

  - [x] 11.3 Create `app/ml/data_splitter.py` for patient-aware train/val/test splitting
    - Implement patient-level stratified splitting (70% train, 15% val, 15% test)
    - Ensure no patient appears in multiple splits
    - _Requirements: 3.2, 11.6_

  - [ ]* 11.4 Write property tests for data processing
    - **Property 9: Data Split Patient Isolation**
    - **Property 10: Missing Value Imputation Completeness**
    - **Property 11: Categorical Encoding Correctness**
    - **Property 12: Feature Normalization Range**
    - **Property 34: Data Split Proportion Accuracy**
    - **Validates: Requirements 3.2, 11.2, 11.3, 11.4, 11.6**
    - Test that train/val/test sets have no patient overlap
    - Test that imputed data has no missing values
    - Test that one-hot encoding produces correct binary vectors
    - Test that normalized features are in expected ranges
    - Test that split proportions are approximately 70/15/15 (±2%)
    - _Requirements: 11.7_


- [x] 12. Implement ML model training pipeline
  - [x] 12.1 Create `app/ml/model_trainer.py` with training logic for multiple architectures
    - Implement train_logistic_regression function
    - Implement train_random_forest function
    - Implement train_xgboost function
    - Implement train_lstm function (TensorFlow/Keras)
    - Implement evaluation metrics computation (accuracy, precision, recall, F1, AUC-ROC)
    - Implement model serialization with joblib (classical ML) and TensorFlow SavedModel (LSTM)
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.6_

  - [x] 12.2 Create `app/ml/model_registry.py` for model versioning and metadata management
    - Implement save_model with version identifier and metadata storage
    - Implement load_model with version selection
    - Implement list_models to query available versions
    - Store training metadata (training_date, dataset_size, evaluation_metrics) in database
    - _Requirements: 16.1, 16.2, 16.4, 16.5_

  - [ ]* 12.3 Write property test for model serialization round-trip
    - **Property 8: Model Serialization Round-Trip**
    - **Validates: Requirements 3.6**
    - Train a simple model on synthetic data
    - Serialize to disk, deserialize, verify predictions are identical
    - _Requirements: 3.6, 3.7_

- [ ] 13. Implement ML inference engine
  - [x] 13.1 Create `app/ml/feature_preprocessor.py` for inference-time preprocessing
    - Implement apply_scaling (min-max, z-score) consistent with training
    - Implement apply_encoding (one-hot) consistent with training
    - Load preprocessing pipeline from disk (joblib)
    - _Requirements: 4.7_

  - [x] 13.2 Create `app/ml/inference_engine.py` with prediction logic
    - Implement load_model to load trained model into memory at startup
    - Implement predict function with feature preprocessing, inference, risk level classification
    - Implement risk_level classification: Low (<0.3), Medium (0.3-0.6), High (0.6-0.85), Critical (≥0.85)
    - Implement batch_predict for multiple patient records
    - Add timeout handling for 500ms inference deadline
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.7, 20.7_

  - [ ]* 13.3 Write property tests for inference
    - **Property 13: Prediction Probability Range**
    - **Property 14: Risk Level Classification Correctness**
    - **Validates: Requirements 4.2, 4.3**
    - Use Hypothesis to generate patient records
    - Verify readmission_probability in [0, 1]
    - Verify risk_level matches probability threshold rules
    - _Requirements: 4.2, 4.3_

- [x] 14. Implement SHAP explainability
  - [x] 14.1 Create `app/ml/shap_explainer.py` with SHAP value computation
    - Implement initialize_explainer with background dataset (100 samples)
    - Implement explain function with SHAP KernelExplainer
    - Rank features by absolute SHAP value magnitude
    - Return top 5 features with name, value, and direction
    - Add 1-second timeout with graceful fallback
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [ ]* 14.2 Write property test for SHAP feature count
    - **Property 15: SHAP Feature Count**
    - **Property 35: SHAP Value Feature Ranking**
    - **Validates: Requirements 4.4, 14.2, 14.3**
    - Verify SHAP explanation contains exactly 5 features
    - Verify features are ordered by descending |SHAP_value|
    - _Requirements: 4.4_

- [x] 15. Checkpoint - Ensure ML layer tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 16. Implement FastAPI endpoints
  - [x] 16.1 Create `app/api/routes/patients.py` with patient endpoints
    - Implement GET /patients with pagination, filtering (disease_type, risk_level), and sorting
    - Implement query parameter validation (page ≥ 1, page_size 1-100)
    - Implement pagination metadata calculation (total_pages = ceiling(total / page_size))
    - Implement sorting by risk_level priority then readmission_probability descending
    - _Requirements: 1.1, 1.5, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ] 16.2 Create `app/api/routes/patients.py` - patient summary endpoint
    - Implement GET /patients/{patient_id}/summary with 30-day daily trend data
    - Implement 404 error handling for non-existent patient_id
    - Return daily_trends array with compliance_score, deviation_score, recovery_score, health_trend, readmission_probability, real_health_score, ideal_health_score
    - _Requirements: 1.2, 1.6, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

  - [x] 16.3 Create `app/api/routes/predict.py` - prediction endpoint
    - Implement POST /predict with request body validation
    - Integrate DigitalTwinEngine, PredictionSystem, InferenceEngine, RecommendationEngine
    - Compute compliance_score, health_scores, deviations
    - Generate ML prediction with SHAP explanation
    - Generate clinical recommendation
    - Return complete PredictionResult
    - _Requirements: 1.3, 1.7, 4.1, 4.2, 4.3, 4.4_

  - [x] 16.4 Create `app/api/routes/dashboard.py` - dashboard stats endpoint
    - Implement GET /dashboard/stats with aggregated statistics
    - Integrate with StatisticsRepository for database aggregations
    - Implement 5-minute caching using Redis or in-memory cache
    - Return total_patients, high_risk_count, avg_compliance, avg_readmission_probability, risk_distribution, recovery_distribution
    - _Requirements: 1.4, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_

  - [x] 16.5 Create `app/api/routes/model.py` - model info endpoint
    - Implement GET /model/info to return current model version and metadata
    - Query model metadata from database or model registry
    - Return model_version, model_type, training_date, dataset_size, evaluation_metrics
    - _Requirements: 16.5_

  - [ ]* 16.6 Write property tests for API endpoints
    - **Property 1: API Pagination Correctness**
    - **Property 6: Filter Correctness**
    - **Property 7: Sort Order Correctness**
    - **Validates: Requirements 1.5, 13.1, 13.2, 13.3, 13.4, 13.6**
    - Use Hypothesis to generate page/page_size combinations
    - Verify pagination metadata and record counts
    - Verify filtering returns only matching records
    - Verify sort order follows priority rules
    - _Requirements: 1.5, 13.3, 13.4, 13.6_

- [x] 17. Implement error handling and middleware
  - [x] 17.1 Create `app/api/middleware/error_handler.py` with exception handlers
    - Implement FastAPI exception handler for ValidationError (HTTP 422)
    - Implement exception handler for NotFoundError (HTTP 404)
    - Implement exception handler for DatabaseError (HTTP 500)
    - Implement exception handler for ModelInferenceError (HTTP 503)
    - Implement exception handler for SHAPComputationError (graceful degradation)
    - Return structured error responses with error code, message, and details
    - _Requirements: 15.1, 15.2, 4.6, 14.5_

  - [x] 17.2 Create `app/api/middleware/cors.py` with CORS configuration
    - Configure CORS middleware for frontend origins
    - Allow credentials, methods, and headers as needed
    - _Requirements: 1.9_

  - [x] 17.3 Create `app/utils/logger.py` with structured logging
    - Set up structlog for JSON logging
    - Implement log formatting with timestamp, level, event, context fields
    - Configure log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - _Requirements: 15.3, 15.4, 15.8_


- [x] 18. Implement configuration management
  - [x] 18.1 Create `app/config/settings.py` with Pydantic Settings classes
    - Define DatabaseConfig with connection parameters
    - Define APIConfig with server parameters and CORS origins
    - Define MLConfig with model paths and timeouts
    - Define CacheConfig with Redis URL and TTL
    - Define AppConfig as top-level configuration
    - Implement load_config from environment variables and optional YAML file
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8_

  - [ ]* 18.2 Write unit tests for configuration loading
    - Test loading from environment variables
    - Test loading from YAML config file
    - Test configuration validation (reject invalid values)
    - Test required parameter checking
    - _Requirements: 19.7, 19.8_

- [ ] 19. Implement database connection resilience
  - [x] 19.1 Create `app/database/connection_manager.py` with retry logic
    - Implement exponential backoff for database connection failures (1s, 2s, 4s, 8s, 16s max)
    - Add connection pool health checks
    - Log connection failures and retry attempts
    - _Requirements: 15.5_

  - [ ]* 19.2 Write integration tests for database resilience
    - Test connection retry on failure
    - Test connection pool behavior under load
    - _Requirements: 2.8, 15.5_

- [x] 20. Implement caching layer for dashboard stats
  - [x] 20.1 Create `app/cache/redis_cache.py` with Redis caching
    - Implement cache initialization and connection
    - Implement get/set functions with TTL support
    - Implement cache invalidation on data updates
    - Add fallback to in-memory cache if Redis unavailable
    - _Requirements: 12.7_

  - [ ]* 20.2 Write unit tests for caching
    - Test cache hit/miss scenarios
    - Test TTL expiration
    - Test cache invalidation
    - _Requirements: 12.7_

- [ ] 21. Implement input sanitization for security
  - [x] 21.1 Create `app/utils/sanitizer.py` with input sanitization functions
    - Implement SQL injection prevention (parameterized queries via SQLAlchemy)
    - Implement XSS prevention using bleach library
    - Implement request size validation (max 1 MB)
    - _Requirements: 17.7, 17.8_

  - [ ]* 21.2 Write property test for input sanitization
    - **Property 36: Input Sanitization Safety**
    - **Validates: Requirements 17.7**
    - Use Hypothesis to generate strings with SQL injection and XSS patterns
    - Verify sanitized output does not contain executable commands or scripts
    - _Requirements: 17.7_

- [x] 22. Checkpoint - Ensure API and infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 23. Implement model hot-swapping and A/B testing support
  - [ ] 23.1 Create `app/ml/model_deployment.py` for model hot-swapping
    - Implement reload_model function to swap models without server restart
    - Implement A/B testing configuration with traffic percentage routing
    - Store deployment config in database (model_deployment_config table)
    - _Requirements: 16.3, 16.6_

  - [ ]* 23.2 Write integration tests for model deployment
    - Test model hot-swapping without server restart
    - Test A/B testing traffic routing
    - Test rollback to previous model version
    - _Requirements: 16.3, 16.6, 16.7_

- [ ] 24. Write integration tests for complete prediction workflow
  - [ ]* 24.1 Write end-to-end test for POST /predict endpoint
    - Send valid patient record to /predict endpoint
    - Verify response contains all required fields (readmission_probability, risk_level, scores, recommendation, SHAP explanation)
    - Verify response latency < 500ms
    - _Requirements: 1.3, 4.5, 20.3_

  - [ ]* 24.2 Write integration tests for dashboard statistics
    - **Property 29: Dashboard Unique Patient Count**
    - **Property 30: Dashboard Risk Distribution Accuracy**
    - **Property 31: Dashboard Recovery Distribution Accuracy**
    - **Property 32: Dashboard Average Calculations**
    - **Property 33: High Risk Count Filter**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
    - Create test patient records with known distributions
    - Call /dashboard/stats endpoint
    - Verify total_patients, risk_distribution, recovery_distribution, averages, high_risk_count
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 24.3 Write integration test for patient summary endpoint
    - Create patient records spanning 30 days
    - Call /patients/{patient_id}/summary
    - Verify daily_trends array has correct data and ordering
    - Test edge case: patient with <30 days of data
    - Test edge case: non-existent patient returns 404
    - _Requirements: 1.2, 1.6, 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 25. Implement performance optimizations
  - [ ] 25.1 Add database query optimization
    - Review slow queries using EXPLAIN ANALYZE
    - Add missing indexes if needed
    - Implement read replicas for dashboard aggregations
    - _Requirements: 2.6, 20.1, 20.2_

  - [ ] 25.2 Implement rate limiting middleware
    - Create rate limiting middleware (1000 requests/hour per client)
    - Use Redis for distributed rate limiting
    - Return HTTP 429 when rate limit exceeded
    - _Requirements: 20.6_

  - [ ]* 25.3 Write performance tests
    - Test 100 concurrent requests without degradation
    - Measure p50, p95, p99 latencies for all endpoints
    - Verify /patients response time <200ms at p95
    - Verify /predict response time <500ms at p95
    - Verify /dashboard/stats response time <300ms at p95 (with cache)
    - Verify /patients/{id}/summary response time <100ms at p95
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 18.6_

- [x] 26. Create Docker configuration for deployment
  - [x] 26.1 Create Dockerfile for containerization
    - Use python:3.11-slim base image
    - Install system dependencies (gcc, postgresql-client)
    - Copy requirements.txt and install Python dependencies
    - Copy application code
    - Create non-root user for security
    - Add health check endpoint
    - Configure uvicorn with 4 workers
    - _Requirements: 20.8_

  - [x] 26.2 Create docker-compose.yml for local development
    - Define services: api, database (PostgreSQL), cache (Redis)
    - Configure networking and volumes
    - Set environment variables
    - _Requirements: 19.2_


- [ ] 27. Create documentation and examples
  - [x] 27.1 Create README.md with setup instructions
    - Document installation steps (Python environment, dependencies)
    - Document configuration (environment variables, config file)
    - Document running the application (uvicorn command)
    - Document database migrations (Alembic commands)
    - _Requirements: 19.1, 19.2, 19.7_

  - [ ] 27.2 Create API documentation using FastAPI's auto-documentation
    - Add docstrings to all endpoint functions
    - Add request/response examples to OpenAPI schema
    - Verify Swagger UI at /docs is functional
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 27.3 Create example scripts for common tasks
    - Create script for training ML models (scripts/train_model.py)
    - Create script for loading sample data (scripts/load_sample_data.py)
    - Create script for testing predictions (scripts/test_prediction.py)
    - _Requirements: 3.1, 3.2_

- [x] 28. Final integration and wiring
  - [x] 28.1 Wire all services in main.py with dependency injection
    - Initialize database connection on startup
    - Load ML model on startup
    - Initialize SHAP explainer with background dataset
    - Register all route handlers
    - Configure middleware (CORS, error handling, logging)
    - Add startup and shutdown event handlers
    - _Requirements: 4.1, 15.6_

  - [x] 28.2 Create health check endpoint
    - Implement GET /health endpoint
    - Check database connectivity
    - Check ML model loaded
    - Return service status
    - _Requirements: 15.5_

  - [ ]* 28.3 Write smoke tests for application startup
    - Test application starts without errors
    - Test all endpoints are registered
    - Test database connection established
    - Test ML model loaded successfully
    - _Requirements: 15.6_

- [x] 29. Final checkpoint - Run full test suite and verify all requirements
  - Ensure all tests pass, ask the user if questions arise.


## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP development
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties using Hypothesis library (100+ iterations per test)
- Unit tests validate specific examples, edge cases, and integration points
- The implementation follows a layered architecture: Data Layer → Business Logic Layer → ML Layer → API Layer
- Database migrations should be run before starting the application
- ML models need to be trained before inference can work (use training scripts in task 27.3)
- Configuration can be provided via environment variables or YAML config file
- Docker configuration enables containerized deployment
- Performance targets: /patients <200ms, /predict <500ms, /dashboard/stats <300ms (cached), /patients/{id}/summary <100ms

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "2.2", "3.1"] },
    { "id": 2, "tasks": ["2.3", "3.2", "3.3"] },
    { "id": 3, "tasks": ["3.4", "4.1", "4.2"] },
    { "id": 4, "tasks": ["4.3", "5.1", "6.1", "7.1"] },
    { "id": 5, "tasks": ["5.2", "6.2", "7.2", "8.1"] },
    { "id": 6, "tasks": ["8.2", "9.1", "11.1"] },
    { "id": 7, "tasks": ["9.2", "11.2", "11.3"] },
    { "id": 8, "tasks": ["11.4", "12.1", "12.2"] },
    { "id": 9, "tasks": ["12.3", "13.1", "13.2"] },
    { "id": 10, "tasks": ["13.3", "14.1"] },
    { "id": 11, "tasks": ["14.2", "16.1", "16.2"] },
    { "id": 12, "tasks": ["16.3", "16.4", "16.5"] },
    { "id": 13, "tasks": ["16.6", "17.1", "17.2", "17.3", "18.1"] },
    { "id": 14, "tasks": ["18.2", "19.1", "20.1", "21.1"] },
    { "id": 15, "tasks": ["19.2", "20.2", "21.2", "23.1"] },
    { "id": 16, "tasks": ["23.2", "24.1", "24.2", "24.3"] },
    { "id": 17, "tasks": ["25.1", "25.2", "26.1"] },
    { "id": 18, "tasks": ["25.3", "26.2", "27.1", "27.2", "27.3"] },
    { "id": 19, "tasks": ["28.1", "28.2"] },
    { "id": 20, "tasks": ["28.3"] }
  ]
}
```
