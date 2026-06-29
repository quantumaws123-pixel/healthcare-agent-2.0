# Requirements Document

## Introduction

The Healthcare Agent 2.0 Backend ML System is an AI-powered digital twin platform for post-discharge patient monitoring and hospital readmission prediction. The system creates two digital twins (Ideal Twin representing the doctor's prescribed plan and Real Twin representing actual patient behavior) to track patient recovery, predict readmission risk using machine learning models, monitor compliance with medical prescriptions, and provide real-time recommendations for healthcare providers.

This document specifies the requirements for the backend API, database, machine learning models, digital twin engine, data processing pipeline, compliance calculation algorithms, health score calculation algorithms, prediction system, and recommendation engine.

## Glossary

- **Backend_API**: The FastAPI-based REST API that exposes endpoints for patient data management, predictions, and dashboard statistics
- **Database**: The relational database (MySQL or PostgreSQL) that persists patient records, clinical data, and AI-generated outputs
- **ML_Model**: Machine learning models (Logistic Regression, Random Forest, XGBoost, LSTM) that predict hospital readmission risk
- **Digital_Twin_Engine**: The computational engine that compares Ideal Twin (doctor's plan) against Real Twin (actual patient behavior) to compute deviation metrics
- **Data_Processing_Pipeline**: The ETL (Extract, Transform, Load) system that ingests patient data and performs feature engineering for ML models
- **Compliance_Calculator**: The algorithm that computes a compliance score based on adherence to medication, exercise, diet, and sleep plans
- **Health_Score_Calculator**: The algorithm that computes Ideal Health Score, Real Health Score, Deviation Score, and Recovery Score
- **Prediction_System**: The system that generates risk level (Low/Medium/High/Critical), recovery status, and readmission probability
- **Recommendation_Engine**: The rule-based system that generates doctor recommendations based on patient state and AI predictions
- **SHAP_Explainer**: The SHAP (SHapley Additive exPlanations) library integration that provides model explainability
- **Patient_Record**: A single day's worth of patient monitoring data including demographics, vitals, prescribed plan, actual behavior, and AI outputs
- **Ideal_Twin**: The theoretical patient state following the doctor's prescribed plan perfectly
- **Real_Twin**: The actual patient state based on observed behavior and clinical measurements
- **Readmission_Probability**: A value between 0 and 1 representing the likelihood of hospital readmission within 30 days

## Requirements

### Requirement 1: REST API Endpoints

**User Story:** As a frontend application, I want to interact with the backend via REST API endpoints, so that I can retrieve patient data, request predictions, and display dashboard statistics.

#### Acceptance Criteria

1. THE Backend_API SHALL expose a GET endpoint `/patients` that returns paginated patient summaries
2. THE Backend_API SHALL expose a GET endpoint `/patients/{patient_id}/summary` that returns 30-day daily trend data for a specific patient
3. THE Backend_API SHALL expose a POST endpoint `/predict` that accepts patient record data and returns prediction results
4. THE Backend_API SHALL expose a GET endpoint `/dashboard/stats` that returns aggregated statistics for the dashboard
5. WHEN a client requests `/patients` with optional query parameters (page, page_size, disease_type, risk_level), THE Backend_API SHALL filter and paginate results accordingly
6. WHEN a client requests `/patients/{patient_id}/summary` with a non-existent patient ID, THE Backend_API SHALL return HTTP 404 with an error message
7. WHEN a client sends invalid data to `/predict`, THE Backend_API SHALL return HTTP 422 with validation error details
8. THE Backend_API SHALL return responses in JSON format with appropriate Content-Type headers
9. THE Backend_API SHALL handle CORS (Cross-Origin Resource Sharing) to allow requests from the frontend application

### Requirement 2: Database Schema and Persistence

**User Story:** As the Backend API, I want to store and retrieve patient records from a relational database, so that patient data persists across application restarts and supports complex queries.

#### Acceptance Criteria

1. THE Database SHALL store patient records with all fields defined in the PatientRecord type schema
2. THE Database SHALL use a primary key composed of Patient_ID and Day to uniquely identify each patient monitoring record
3. WHEN the Backend_API receives a write request, THE Database SHALL persist the data with ACID (Atomicity, Consistency, Isolation, Durability) guarantees
4. WHEN the Backend_API queries for patient summaries, THE Database SHALL return only the latest day record for each patient
5. WHEN the Backend_API queries for a patient's 30-day trend, THE Database SHALL return records ordered by Day in ascending order
6. THE Database SHALL support indexing on Patient_ID, Day, Disease_Type, and Risk_Level fields for query performance
7. THE Database SHALL enforce data type constraints (e.g., Compliance_Score between 0 and 100, Risk_Level as enum)
8. THE Database SHALL handle concurrent read and write operations without data corruption

### Requirement 3: Machine Learning Model Training and Evaluation

**User Story:** As a data scientist, I want to train and evaluate multiple ML models for readmission prediction, so that I can select the best-performing model for production deployment.

#### Acceptance Criteria

1. THE ML_Model SHALL support training with Logistic Regression, Random Forest, XGBoost, and LSTM architectures
2. WHEN training data is provided, THE ML_Model SHALL split data into training (70%), validation (15%), and test (15%) sets
3. THE ML_Model SHALL use features including clinical vitals, compliance scores, health scores, deviation scores, and patient demographics
4. THE ML_Model SHALL predict a binary classification target (readmission within 30 days: Yes/No)
5. WHEN model training completes, THE ML_Model SHALL report evaluation metrics including accuracy, precision, recall, F1-score, and AUC-ROC
6. THE ML_Model SHALL serialize trained models to disk in a format that supports versioning
7. WHEN multiple models are trained, THE ML_Model SHALL support A/B testing or model comparison based on evaluation metrics
8. THE ML_Model SHALL handle missing values in input features through imputation or feature engineering

### Requirement 4: Machine Learning Model Inference

**User Story:** As the Backend API, I want to load a trained ML model and generate predictions for patient records, so that I can provide readmission risk predictions to healthcare providers.

#### Acceptance Criteria

1. WHEN the Backend_API starts, THE ML_Model SHALL load the latest trained model from disk into memory
2. WHEN the Backend_API receives a prediction request, THE ML_Model SHALL generate a readmission probability between 0 and 1
3. THE ML_Model SHALL transform the readmission probability into a Risk_Level (Low: <0.3, Medium: 0.3-0.6, High: 0.6-0.85, Critical: >0.85)
4. WHEN a prediction is generated, THE ML_Model SHALL compute SHAP values for the top 5 contributing features
5. THE ML_Model SHALL return predictions within 500 milliseconds for real-time API responsiveness
6. IF the ML_Model encounters an error during inference, THEN THE Backend_API SHALL return HTTP 500 with an error message
7. THE ML_Model SHALL handle input feature scaling and normalization consistent with training preprocessing

### Requirement 5: Digital Twin Comparison Logic

**User Story:** As the system, I want to compare the Ideal Twin (doctor's plan) against the Real Twin (actual behavior), so that I can compute deviation metrics and identify non-compliance.

#### Acceptance Criteria

1. THE Digital_Twin_Engine SHALL compute the deviation between Expected_Steps and Actual_Steps
2. THE Digital_Twin_Engine SHALL compute the deviation between Expected_Sleep_Hours and Actual_Sleep_Hours
3. THE Digital_Twin_Engine SHALL compute the deviation between Water_Intake_Goal and Water_Intake
4. WHEN Medication_Taken is "No", THE Digital_Twin_Engine SHALL flag a medication compliance violation
5. WHEN Exercise_Completed is "No", THE Digital_Twin_Engine SHALL flag an exercise compliance violation
6. THE Digital_Twin_Engine SHALL aggregate all deviations into a single Deviation_Score between 0 and 100
7. THE Digital_Twin_Engine SHALL compute the Ideal_Health_Score based on doctor's prescribed plan and expected outcomes
8. THE Digital_Twin_Engine SHALL compute the Real_Health_Score based on actual patient behavior and measured vitals

### Requirement 6: Compliance Score Calculation

**User Story:** As the system, I want to calculate a compliance score based on patient adherence to the doctor's plan, so that healthcare providers can quickly assess patient compliance.

#### Acceptance Criteria

1. THE Compliance_Calculator SHALL compute medication compliance as the percentage of days where Medication_Taken is "Yes"
2. THE Compliance_Calculator SHALL compute exercise compliance as the percentage of days where Exercise_Completed is "Yes"
3. THE Compliance_Calculator SHALL compute step compliance as (Actual_Steps / Expected_Steps) capped at 100%
4. THE Compliance_Calculator SHALL compute sleep compliance as 100 - |Expected_Sleep_Hours - Actual_Sleep_Hours| / Expected_Sleep_Hours × 100
5. THE Compliance_Calculator SHALL compute diet compliance using the Diet_Compliance field as a percentage
6. THE Compliance_Calculator SHALL compute water intake compliance as (Water_Intake / Water_Intake_Goal) capped at 100%
7. THE Compliance_Calculator SHALL aggregate sub-scores with weights: medication (30%), exercise (20%), steps (15%), sleep (15%), diet (10%), water (10%)
8. THE Compliance_Calculator SHALL output a Compliance_Score between 0 and 100

### Requirement 7: Health Score Calculation

**User Story:** As the system, I want to calculate multiple health scores to track patient recovery progress, so that healthcare providers can monitor patient trajectory over time.

#### Acceptance Criteria

1. THE Health_Score_Calculator SHALL compute Ideal_Health_Score based on expected vitals, compliance, and recovery trajectory
2. THE Health_Score_Calculator SHALL compute Real_Health_Score based on actual vitals (Heart_Rate, Systolic_BP, Diastolic_BP, SpO2, Respiratory_Rate, Body_Temperature)
3. THE Health_Score_Calculator SHALL normalize vitals by comparing against normal ranges for the patient's age and disease type
4. THE Health_Score_Calculator SHALL compute Deviation_Score as |Ideal_Health_Score - Real_Health_Score|
5. THE Health_Score_Calculator SHALL compute Recovery_Score by analyzing trend direction over the last 7 days
6. WHEN Real_Health_Score is improving over time, THE Health_Score_Calculator SHALL increase Recovery_Score
7. WHEN Real_Health_Score is declining over time, THE Health_Score_Calculator SHALL decrease Recovery_Score
8. THE Health_Score_Calculator SHALL output all health scores on a scale of 0 to 100

### Requirement 8: Recovery Status Classification

**User Story:** As a healthcare provider, I want to see a patient's recovery status classification, so that I can quickly identify patients who need intervention.

#### Acceptance Criteria

1. WHEN Recovery_Score is above 85 and Health_Trend is "Increasing", THE Prediction_System SHALL classify Recovery_Status as "Recovered"
2. WHEN Recovery_Score is between 70 and 85 and Health_Trend is "Increasing", THE Prediction_System SHALL classify Recovery_Status as "Improving"
3. WHEN Recovery_Score is between 50 and 70 and Health_Trend is "Stable", THE Prediction_System SHALL classify Recovery_Status as "Stable"
4. WHEN Recovery_Score is between 30 and 50 and Health_Trend is "Declining", THE Prediction_System SHALL classify Recovery_Status as "Delayed Recovery"
5. WHEN Recovery_Score is between 15 and 30 and Health_Trend is "Declining", THE Prediction_System SHALL classify Recovery_Status as "Worsening"
6. WHEN Recovery_Score is below 15 or Risk_Level is "Critical", THE Prediction_System SHALL classify Recovery_Status as "Critical"
7. THE Prediction_System SHALL update Recovery_Status daily as new patient data is ingested

### Requirement 9: Health Trend Analysis

**User Story:** As the system, I want to analyze the direction of health metrics over time, so that I can detect improving or declining patient conditions.

#### Acceptance Criteria

1. THE Prediction_System SHALL compute Health_Trend by analyzing Real_Health_Score over the last 7 days
2. WHEN the linear regression slope of Real_Health_Score is greater than 1.0, THE Prediction_System SHALL set Health_Trend to "Increasing"
3. WHEN the linear regression slope of Real_Health_Score is between -1.0 and 1.0, THE Prediction_System SHALL set Health_Trend to "Stable"
4. WHEN the linear regression slope of Real_Health_Score is less than -1.0, THE Prediction_System SHALL set Health_Trend to "Declining"
5. IF fewer than 3 days of data are available, THEN THE Prediction_System SHALL default Health_Trend to "Stable"
6. THE Prediction_System SHALL update Health_Trend daily as new patient data is ingested

### Requirement 10: Doctor Recommendation Generation

**User Story:** As a healthcare provider, I want to receive automated recommendations based on patient state, so that I can take appropriate clinical actions.

#### Acceptance Criteria

1. WHEN Risk_Level is "Low" and Recovery_Status is "Recovered" or "Improving", THE Recommendation_Engine SHALL recommend "Continue Current Treatment"
2. WHEN Risk_Level is "Medium" or Compliance_Score is below 60, THE Recommendation_Engine SHALL recommend "Increase Monitoring"
3. WHEN Risk_Level is "High" or Deviation_Score is above 40, THE Recommendation_Engine SHALL recommend "Medication Adjustment"
4. WHEN Risk_Level is "Critical" or Recovery_Status is "Worsening" or "Critical", THE Recommendation_Engine SHALL recommend "Immediate Doctor Review"
5. WHEN Readmission_Probability is above 0.85, THE Recommendation_Engine SHALL recommend "Hospital Readmission"
6. THE Recommendation_Engine SHALL prioritize more severe recommendations when multiple conditions are met
7. THE Recommendation_Engine SHALL log the reasoning for each recommendation for audit purposes

### Requirement 11: Data Processing Pipeline for ETL

**User Story:** As the system, I want to ingest raw patient data and transform it into features suitable for ML models, so that predictions are based on properly engineered features.

#### Acceptance Criteria

1. THE Data_Processing_Pipeline SHALL load patient records from the Database or CSV files
2. THE Data_Processing_Pipeline SHALL handle missing values by applying median imputation for numerical fields and mode imputation for categorical fields
3. THE Data_Processing_Pipeline SHALL encode categorical variables (Gender, Disease_Type, Smoking_Status, Alcohol_Consumption) using one-hot encoding
4. THE Data_Processing_Pipeline SHALL normalize numerical features (vitals, scores) using min-max scaling or z-score normalization
5. THE Data_Processing_Pipeline SHALL create derived features including compliance_score, deviation_score, health_trend, and recovery_score
6. THE Data_Processing_Pipeline SHALL split data by Patient_ID to prevent data leakage (same patient's records must not appear in both training and test sets)
7. THE Data_Processing_Pipeline SHALL output processed data in a format compatible with ML_Model training and inference
8. WHEN the Data_Processing_Pipeline encounters corrupt or invalid records, THE Data_Processing_Pipeline SHALL log errors and skip those records

### Requirement 12: Dashboard Statistics Aggregation

**User Story:** As the frontend application, I want to retrieve aggregated statistics for the dashboard, so that I can display KPIs and summary metrics.

#### Acceptance Criteria

1. THE Backend_API SHALL compute total_patients as the count of unique Patient_IDs with data in the last 30 days
2. THE Backend_API SHALL compute risk_distribution as the count of patients in each Risk_Level category
3. THE Backend_API SHALL compute recovery_distribution as the count of patients in each Recovery_Status category
4. THE Backend_API SHALL compute avg_compliance as the mean Compliance_Score across all active patients
5. THE Backend_API SHALL compute avg_readmission_probability as the mean Readmission_Probability across all active patients
6. THE Backend_API SHALL compute high_risk_count as the count of patients with Risk_Level "High" or "Critical"
7. THE Backend_API SHALL cache dashboard statistics for 5 minutes to reduce database query load
8. WHEN the Backend_API receives a request for `/dashboard/stats`, THE Backend_API SHALL return statistics in the DashboardStats JSON format

### Requirement 13: Patient Data Filtering and Pagination

**User Story:** As a healthcare provider using the frontend, I want to filter and paginate patient lists, so that I can efficiently navigate large patient populations.

#### Acceptance Criteria

1. WHEN a client requests `/patients` with a `disease_type` parameter, THE Backend_API SHALL return only patients matching that Disease_Type
2. WHEN a client requests `/patients` with a `risk_level` parameter, THE Backend_API SHALL return only patients matching that Risk_Level
3. WHEN a client requests `/patients` with `page=2` and `page_size=20`, THE Backend_API SHALL return records 21-40
4. THE Backend_API SHALL return pagination metadata including page, page_size, total, and total_pages
5. WHEN no query parameters are provided, THE Backend_API SHALL default to page=1 and page_size=10
6. THE Backend_API SHALL return patient summaries sorted by Risk_Level (Critical, High, Medium, Low) and then by Readmission_Probability descending
7. WHEN a filter results in zero patients, THE Backend_API SHALL return an empty data array with total=0

### Requirement 14: SHAP Explainability Integration

**User Story:** As a healthcare provider, I want to understand which features contributed most to a readmission prediction, so that I can make informed clinical decisions.

#### Acceptance Criteria

1. WHEN the ML_Model generates a prediction, THE SHAP_Explainer SHALL compute SHAP values for all input features
2. THE SHAP_Explainer SHALL rank features by absolute SHAP value magnitude
3. THE Backend_API SHALL return the top 5 features with the highest SHAP values in the prediction response
4. THE Backend_API SHALL return each feature's name, SHAP value, and direction (positive or negative contribution)
5. WHEN SHAP computation fails or times out, THE Backend_API SHALL return explainability="unavailable" in the response
6. THE SHAP_Explainer SHALL use a background dataset of 100 representative samples for SHAP kernel computation
7. THE SHAP_Explainer SHALL compute SHAP values within 1 second to maintain API responsiveness

### Requirement 15: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error handling and logging, so that I can debug issues and monitor system health.

#### Acceptance Criteria

1. WHEN the Backend_API encounters an unhandled exception, THE Backend_API SHALL return HTTP 500 with a generic error message
2. WHEN the Backend_API encounters a client error (invalid input), THE Backend_API SHALL return HTTP 4xx with detailed validation errors
3. THE Backend_API SHALL log all requests with timestamp, endpoint, method, status code, and response time
4. THE Backend_API SHALL log all errors with stack traces to a centralized logging system
5. WHEN the Database connection fails, THE Backend_API SHALL log the error and attempt to reconnect with exponential backoff
6. WHEN the ML_Model fails to load, THE Backend_API SHALL log the error and return HTTP 503 (Service Unavailable) for prediction requests
7. THE Backend_API SHALL log warnings when API response times exceed 1 second
8. THE Backend_API SHALL support configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Requirement 16: Model Versioning and Deployment

**User Story:** As a data scientist, I want to version ML models and deploy new models without downtime, so that I can continuously improve prediction accuracy.

#### Acceptance Criteria

1. THE ML_Model SHALL serialize trained models with a version identifier (e.g., model_v1.0.pkl, model_v1.1.pkl)
2. THE Backend_API SHALL load the model version specified in a configuration file
3. WHEN a new model version is deployed, THE Backend_API SHALL support hot-swapping without restarting the server
4. THE ML_Model SHALL store training metadata (training date, dataset size, evaluation metrics) alongside the serialized model
5. THE Backend_API SHALL expose a GET endpoint `/model/info` that returns the current model version and metadata
6. WHEN multiple model versions exist, THE Backend_API SHALL support A/B testing by routing a percentage of requests to each model
7. THE ML_Model SHALL support rollback to a previous model version in case of performance degradation

### Requirement 17: Data Validation and Sanitization

**User Story:** As the Backend API, I want to validate and sanitize all input data, so that I prevent invalid data from corrupting the database or causing model errors.

#### Acceptance Criteria

1. WHEN a client submits a Patient_Record, THE Backend_API SHALL validate that all required fields are present
2. THE Backend_API SHALL validate that numerical fields (Age, BMI, vitals) are within physiologically plausible ranges
3. THE Backend_API SHALL validate that categorical fields (Gender, Disease_Type, Risk_Level) match predefined enum values
4. THE Backend_API SHALL validate that Compliance_Score is between 0 and 100
5. THE Backend_API SHALL validate that Readmission_Probability is between 0 and 1
6. WHEN validation fails, THE Backend_API SHALL return HTTP 422 with a list of validation errors
7. THE Backend_API SHALL sanitize string inputs to prevent SQL injection and XSS attacks
8. THE Backend_API SHALL reject requests with payload sizes exceeding 1 MB

### Requirement 18: Patient Summary Generation

**User Story:** As the frontend application, I want to retrieve a 30-day summary for a specific patient, so that I can visualize health trends and compliance over time.

#### Acceptance Criteria

1. WHEN a client requests `/patients/{patient_id}/summary`, THE Backend_API SHALL retrieve all records for that Patient_ID from the last 30 days
2. THE Backend_API SHALL return daily trend data including day, compliance_score, deviation_score, recovery_score, health_trend, readmission_probability, real_health_score, and ideal_health_score
3. THE Backend_API SHALL return records ordered by day in ascending order
4. WHEN a patient has fewer than 30 days of data, THE Backend_API SHALL return all available records
5. WHEN a Patient_ID does not exist in the Database, THE Backend_API SHALL return HTTP 404 with an error message
6. THE Backend_API SHALL compute trend data efficiently using database indexes to support sub-100ms response times

### Requirement 19: Configuration Management

**User Story:** As a system administrator, I want to configure system parameters externally, so that I can adjust settings without modifying code.

#### Acceptance Criteria

1. THE Backend_API SHALL load configuration from environment variables or a configuration file
2. THE Backend_API SHALL support configuration of database connection parameters (host, port, username, password, database name)
3. THE Backend_API SHALL support configuration of API server parameters (host, port, CORS origins)
4. THE Backend_API SHALL support configuration of ML model paths and versioning
5. THE Backend_API SHALL support configuration of log levels and log output destinations
6. THE Backend_API SHALL support configuration of pagination defaults (default page size, max page size)
7. WHEN a required configuration parameter is missing, THE Backend_API SHALL fail to start and log a descriptive error message
8. THE Backend_API SHALL validate configuration parameters at startup and reject invalid configurations

### Requirement 20: Performance and Scalability

**User Story:** As a system administrator, I want the system to handle high request volumes efficiently, so that it can scale to support thousands of patients.

#### Acceptance Criteria

1. THE Backend_API SHALL handle at least 100 concurrent requests without performance degradation
2. THE Backend_API SHALL respond to `/patients` requests within 200 milliseconds at the 95th percentile
3. THE Backend_API SHALL respond to `/predict` requests within 500 milliseconds at the 95th percentile
4. THE Backend_API SHALL respond to `/dashboard/stats` requests within 300 milliseconds at the 95th percentile using caching
5. THE Database SHALL support connection pooling to handle concurrent database queries efficiently
6. THE Backend_API SHALL implement rate limiting to prevent abuse (e.g., 1000 requests per hour per client)
7. THE ML_Model SHALL support batch prediction to process multiple patient records in a single inference call
8. THE Backend_API SHALL support horizontal scaling by running multiple server instances behind a load balancer
