# Requirements Document

## Introduction

Healthcare Agent 2.0 is an AI-Based Digital Twin System for post-discharge patient monitoring and hospital readmission prediction. The system models each patient's expected recovery trajectory (Ideal Digital Twin) against their actual daily health behaviour (Real Digital Twin), computes deviation metrics through a Comparison Engine, and produces ML-driven predictions for readmission probability, risk level, recovery status, and doctor recommendations. Outputs are surfaced through a Streamlit doctor dashboard and a FastAPI backend. The system operates on a dataset of 100,000 daily observations across 3,334 patients tracked for 30 days post-discharge, covering eight disease types.

---

## Glossary

- **Ideal_Digital_Twin**: The expected recovery profile constructed from the doctor's discharge plan, including expected steps, sleep hours, diet plan, water intake goal, medication schedule, and exercise plan.
- **Real_Digital_Twin**: The actual daily health profile captured from patient-reported data and wearable sensors, including actual steps, medication adherence, sleep hours, water intake, exercise completion, diet compliance, mood, and symptoms.
- **Comparison_Engine**: The analytical module that computes Compliance_Score, Ideal_Health_Score, Real_Health_Score, Deviation_Score, Recovery_Score, and Health_Trend by contrasting the Ideal_Digital_Twin and Real_Digital_Twin.
- **Preprocessing_Pipeline**: The data processing module responsible for loading the dataset, handling missing values, engineering features, encoding categoricals, and normalising numerical columns.
- **ML_Model**: Any trained machine learning model (Logistic Regression, Random Forest, XGBoost, LightGBM, or LSTM) used to generate predictions.
- **Prediction_Engine**: The inference module that loads trained ML_Models and produces Risk_Level, Recovery_Status, Readmission_Probability, and Doctor_Recommendation for a given patient record.
- **Dashboard**: The Streamlit-based doctor-facing web application that displays patient overviews, trend charts, risk alerts, and AI recommendations.
- **API**: The FastAPI REST backend that exposes prediction and patient data endpoints consumed by the Dashboard and optional mobile clients.
- **Patient_Record**: A single row in the dataset, uniquely identified by Patient_ID and Day, containing all 51 columns.
- **Risk_Level**: A three-class categorical label (Low, Medium, High) representing the patient's near-term clinical risk.
- **Recovery_Status**: A six-class categorical label (Recovered, Improving, Stable, Delayed Recovery, Worsening, Critical) representing the patient's recovery trajectory.
- **Doctor_Recommendation**: A five-class categorical label (Continue Current Treatment, Increase Monitoring, Medication Adjustment, Immediate Doctor Review, Hospital Readmission) representing the AI-generated clinical action.
- **Readmission_Probability**: A continuous value in [0, 100] representing the predicted probability (as a percentage) of hospital readmission.
- **Compliance_Score**: A derived numeric score in [0, 100] measuring how closely the patient followed the doctor's discharge plan on a given day.
- **Deviation_Score**: A derived numeric score measuring the magnitude of divergence between the Ideal_Health_Score and Real_Health_Score on a given day.
- **Disease_Type**: One of eight disease categories in the dataset: Diabetes, Hypertension, Cardiac, Post Surgery, Kidney Disease, COPD, Asthma, Stroke Recovery.

---

## Requirements

---

### Requirement 1: Data Ingestion and Validation

**User Story:** As a data engineer, I want to load and validate the raw dataset, so that downstream modules receive clean, well-structured data.

#### Acceptance Criteria

1. THE Preprocessing_Pipeline SHALL load the CSV dataset file and produce a structured dataframe with all 51 expected columns present.
2. WHEN the loaded dataframe contains fewer than the 51 expected columns, THE Preprocessing_Pipeline SHALL raise a descriptive error that names each missing column.
3. WHEN the CSV file path does not exist or the file is unreadable, THE Preprocessing_Pipeline SHALL raise a descriptive error identifying the file path and the OS-level reason for failure before any further processing is attempted.
4. WHEN a Patient_Record contains a Patient_ID that is null, an empty string, or does not match the pattern `HDT-[A-Z]+-[0-9]+-[0-9]+-[0-9]+`, OR contains a Day value that is null, non-integer, or not parseable as an integer, THE Preprocessing_Pipeline SHALL flag that record by appending it to a rejection log with the Patient_ID (or a row-index placeholder if Patient_ID itself is null), the Day value, and a reason string identifying which field failed validation; THE Preprocessing_Pipeline SHALL then exclude flagged records from further processing — IF the rejection-log append operation fails for any reason, THE Preprocessing_Pipeline SHALL retain the affected record in processing rather than silently dropping it.
5. IF any patient has Day values where at least one value falls outside [1, 30], THE Preprocessing_Pipeline SHALL emit a data quality warning that includes the Patient_ID and the out-of-range Day values.
6. WHEN the dataset is loaded and all validation checks have run, THE Preprocessing_Pipeline SHALL produce and both return and print a validation summary that includes: total row count, count of excluded records, unique patient count, and per-Disease_Type row distribution.

---

### Requirement 2: Missing Value Handling

**User Story:** As a data scientist, I want missing values handled consistently, so that ML models train on complete feature matrices without information leakage.

#### Acceptance Criteria

1. WHEN Blood_Glucose values are missing for a Patient_Record, THE Preprocessing_Pipeline SHALL impute them using the per-patient median computed from non-missing days for that patient; IF fewer than two non-missing Blood_Glucose values exist for that patient, THE Preprocessing_Pipeline SHALL fall back to the per-Disease_Type median; IF the per-Disease_Type median is also unavailable (i.e., all Blood_Glucose values for that Disease_Type are missing), THE Preprocessing_Pipeline SHALL fall back to the global median across all non-missing Blood_Glucose values.
2. WHEN Cholesterol values are missing for a Patient_Record, THE Preprocessing_Pipeline SHALL impute them using the per-patient median computed from non-missing days for that patient; IF fewer than two non-missing Cholesterol values exist for that patient, THE Preprocessing_Pipeline SHALL fall back to the per-Disease_Type median; IF the per-Disease_Type median is also unavailable (i.e., all Cholesterol values for that Disease_Type are missing), THE Preprocessing_Pipeline SHALL fall back to the global median across all non-missing Cholesterol values.
3. WHEN Mood values are missing for a Patient_Record, THE Preprocessing_Pipeline SHALL impute the missing value using the most frequent Mood value observed for that patient across all non-missing days (the patient's personal mode); IF two or more Mood values share the highest frequency for that patient, THE Preprocessing_Pipeline SHALL select the lexicographically first value among the tied modes to ensure deterministic imputation; THE Preprocessing_Pipeline SHALL fall back to the global mode across all non-missing Mood values only when no non-missing Mood values exist for that patient.
4. THE Preprocessing_Pipeline SHALL produce a missing-value audit report — computed before any imputation is applied — that lists each column, its original missing count, its missing percentage (rounded to two decimal places), and the imputation strategy that will be applied; this report SHALL be generated even when no columns have missing values.
5. WHEN imputation is complete, IF any of the four target columns — Risk_Level, Recovery_Status, Readmission_Probability, or Doctor_Recommendation — contain one or more missing values, THE Preprocessing_Pipeline SHALL raise an error that names each affected target column and its remaining missing count.

---

### Requirement 3: Feature Engineering

**User Story:** As a data scientist, I want derived features computed from raw columns, so that ML models capture behavioural compliance and health deviation signals.

#### Acceptance Criteria

1. THE Preprocessing_Pipeline SHALL compute a Steps_Compliance ratio as Actual_Steps divided by Expected_Steps, capped at 1.0, for each Patient_Record where Expected_Steps is greater than zero.
2. THE Preprocessing_Pipeline SHALL compute a Sleep_Deviation value as the absolute difference between Actual_Sleep_Hours and Expected_Sleep_Hours for each Patient_Record.
3. THE Preprocessing_Pipeline SHALL compute a Water_Compliance ratio as Water_Intake divided by Water_Intake_Goal, capped at 1.0, for each Patient_Record where Water_Intake_Goal is greater than zero.
4. THE Preprocessing_Pipeline SHALL compute a Rolling_7Day_Compliance feature as the 7-day rolling mean of Compliance_Score per patient ordered by Day, using min_periods=1 so that each of the first six days uses the mean of all available Compliance_Score values up to and including that day.
5. THE Preprocessing_Pipeline SHALL compute a Rolling_7Day_Deviation feature as the 7-day rolling mean of Deviation_Score per patient ordered by Day, using min_periods=1 so that each of the first six days uses the mean of all available Deviation_Score values up to and including that day.
6. THE Preprocessing_Pipeline SHALL compute a Medication_Adherence_Rate feature as the cumulative ratio of days where Medication_Taken is "Yes" to the total days observed so far for that patient, ordered by Day; null Medication_Taken values SHALL be excluded from both the numerator and the denominator when computing this ratio.
7. WHEN Expected_Steps is zero or null for a Patient_Record, THE Preprocessing_Pipeline SHALL set Steps_Compliance to null for that record and log a warning that includes the Patient_ID, the Day value, and the reason (zero or null Expected_Steps); THE Preprocessing_Pipeline SHALL NOT attempt the division.
8. WHEN Water_Intake_Goal is zero or null for a Patient_Record, THE Preprocessing_Pipeline SHALL set Water_Compliance to null for that record and log a warning that includes the Patient_ID, the Day value, and the reason (zero or null Water_Intake_Goal); THE Preprocessing_Pipeline SHALL NOT attempt the division.

---

### Requirement 4: Data Encoding and Normalisation

**User Story:** As a data scientist, I want categorical variables encoded and numerical features normalised, so that ML models receive correctly formatted input tensors.

#### Acceptance Criteria

1. THE Preprocessing_Pipeline SHALL apply label encoding to Risk_Level, Recovery_Status, and Doctor_Recommendation target columns and persist the integer-to-label mapping for each target as a serialisable artefact, such that for any valid label string the round-trip of encode-then-decode returns the original string.
2. THE Preprocessing_Pipeline SHALL apply one-hot encoding to Disease_Type, Gender, and Smoking_Status columns, dropping the first category to avoid multicollinearity.
3. THE Preprocessing_Pipeline SHALL apply min-max normalisation to all continuous numerical feature columns — explicitly excluding label-encoded target columns, one-hot encoded columns, and binary indicator columns (Medication_Taken, Exercise_Completed) — computing normalisation parameters exclusively from the training split to prevent data leakage.
4. WHEN normalisation parameters are fitted on the training split, THE Preprocessing_Pipeline SHALL persist them as a serialisable artefact so that the same scaling can be applied to inference-time inputs without refitting.
5. THE Preprocessing_Pipeline SHALL produce a finalised feature matrix and target vectors with no null values before passing data to the ML_Model training modules.
6. IF a categorical value is encountered during label encoding or one-hot encoding that was not present in the training split, THE Preprocessing_Pipeline SHALL raise a descriptive error that identifies the column name and the unseen value, and SHALL NOT silently assign a default encoding.

---

### Requirement 5: Digital Twin Comparison Engine

**User Story:** As a clinician, I want the system to quantify the gap between a patient's expected and actual recovery each day, so that I can identify patients who are diverging from their treatment plan.

#### Acceptance Criteria

1. THE Comparison_Engine SHALL compute Compliance_Score for each Patient_Record as a weighted composite of Steps_Compliance, Medication_Taken adherence (Yes→1.0, No→0.0), Sleep_Deviation normalised to a 0–1 scale using the formula max(0, 1 − Sleep_Deviation / 4) where the denominator 4 represents a cap of 4 hours deviation, Water_Compliance, Exercise_Completed adherence (Yes→1.0, No→0.0), and Diet_Compliance divided by 100; the weighted sum SHALL then be multiplied by 100 to produce a score in [0, 100]; the six component weights SHALL sum to 1.0.
2. THE Comparison_Engine SHALL compute Ideal_Health_Score for each Patient_Record by computing the equal-weight average of two normalised groups: group 1 is the mean of min-max normalised Expected_Steps, Expected_Sleep_Hours, and Water_Intake_Goal; group 2 is the mean of disease-type-appropriate clinical vitals benchmarks for Heart_Rate, Systolic_BP, SpO2, and Body_Temperature expressed as normalised proximity to their ideal range; the two group means SHALL be averaged with equal weight to produce a score in [0, 1].
3. THE Comparison_Engine SHALL compute Real_Health_Score for each Patient_Record by computing the equal-weight average of two normalised groups: group 1 is the mean of min-max normalised Actual_Steps, Actual_Sleep_Hours, and Water_Intake; group 2 is the mean of min-max normalised observed clinical vitals Heart_Rate, Systolic_BP, SpO2, and Body_Temperature; the two group means SHALL be averaged with equal weight to produce a score in [0, 1].
4. THE Comparison_Engine SHALL compute Deviation_Score for each Patient_Record as the absolute difference between Ideal_Health_Score and Real_Health_Score, resulting in a value in [0, 1].
5. THE Comparison_Engine SHALL compute Recovery_Score for each Patient_Record using the formula: Recovery_Score = clamp((Compliance_Score / 100 − Deviation_Score + Day / 30) / 3 × 100, 0, 100), where Day is the monitoring day in [1, 30].
6. IF Recovery_Score for a Patient_Record increased by more than 0.5 compared to the prior day's Recovery_Score, THE Comparison_Engine SHALL assign Health_Trend as Increasing; IF Recovery_Score decreased by more than 0.5, THE Comparison_Engine SHALL assign Health_Trend as Declining; IF the change is within ±0.5 (inclusive), THE Comparison_Engine SHALL assign Health_Trend as Stable; for Day 1 records, THE Comparison_Engine SHALL assign Health_Trend as Stable.
7. WHEN the Comparison_Engine is initialised, IF the six Compliance_Score component weights do not sum to 1.0 within an absolute tolerance of 0.001, THE Comparison_Engine SHALL raise a configuration error that reports the actual sum before any Patient_Record is processed.

---

### Requirement 6: ML Model Training — Classification

**User Story:** As a data scientist, I want multi-class classification models trained and evaluated, so that I can select the best performing model for each target label.

#### Acceptance Criteria

1. THE ML_Model training module SHALL train at least four classifiers — Logistic Regression, Random Forest, XGBoost, and LightGBM — on each of the three classification targets: Risk_Level (3-class), Recovery_Status (6-class), and Doctor_Recommendation (5-class).
2. THE ML_Model training module SHALL partition the dataset using a stratified train/validation/test split of 70%/15%/15%, stratified on Disease_Type and Risk_Level jointly, before any feature transformation; the validation split SHALL be used exclusively for model selection and the test split SHALL be used exclusively for final evaluation.
3. THE ML_Model training module SHALL evaluate each classifier using weighted F1-score, macro F1-score, accuracy, and a per-class classification report on the held-out test split.
4. THE ML_Model training module SHALL log training duration, model size in bytes, and all evaluation metrics per model and target to a structured machine-readable results artefact (e.g., JSON).
5. WHEN a classifier achieves a weighted F1-score below 0.60 on the test split for any target, THE ML_Model training module SHALL emit a warning to both the console and the structured results artefact identifying the model name, the target column, and the observed weighted F1-score.
6. THE ML_Model training module SHALL persist each trained model as a serialisable artefact that the Prediction_Engine can load without retraining.
7. THE ML_Model training module SHALL select, for each classification target, the model with the highest weighted F1-score on the validation split as the primary model artefact for that target; IF two models are tied on validation weighted F1-score, THE ML_Model training module SHALL select the one with the shorter training duration as the tiebreaker.

---

### Requirement 7: ML Model Training — Regression

**User Story:** As a data scientist, I want a regression model trained for readmission probability, so that the system produces a continuous risk score for each patient-day.

#### Acceptance Criteria

1. THE ML_Model training module SHALL train at least three regressors — Random Forest, XGBoost, and LightGBM — to predict Readmission_Probability, using the same 70%/15%/15% stratified train/validation/test split defined in Requirement 6.
2. THE ML_Model training module SHALL evaluate each regressor using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and R-squared (R²) on the held-out test split.
3. WHEN a regressor produces predictions outside the range [0, 100] — whether during training-time metric computation or inference-time output from the Prediction_Engine — THE ML_Model training module SHALL clip those predicted values to [0, 100] before computing evaluation metrics, and THE Prediction_Engine SHALL clip those values before returning them in any response.
4. THE ML_Model training module SHALL select the regressor with the lowest RMSE on the validation split as the primary Readmission_Probability model and persist it as a serialisable artefact loadable by the Prediction_Engine without retraining.
5. IF a tree-based regressor (Random Forest, XGBoost, or LightGBM) is trained, THE ML_Model training module SHALL log its feature importances to the structured results artefact.
6. WHEN any regressor achieves an R² below 0.0 on the test split, THE ML_Model training module SHALL emit a warning to both the console and the structured results artefact identifying the model name and the observed R² value.

---

### Requirement 8: Prediction Engine (Inference)

**User Story:** As a backend developer, I want a unified inference module, so that the API can serve real-time predictions for any patient record without retraining.

#### Acceptance Criteria

1. WHEN a valid Patient_Record is submitted for inference, THE Prediction_Engine SHALL apply the persisted normalisation artefact to numerical features, run all four primary model artefacts, and return Risk_Level, Recovery_Status, Doctor_Recommendation, and Readmission_Probability in a single response object.
2. THE Prediction_Engine SHALL load the following artefacts exactly once at startup and cache them in memory: the normalisation scaler, the label-mapping artefact, the primary Risk_Level classifier, the primary Recovery_Status classifier, the primary Doctor_Recommendation classifier, and the primary Readmission_Probability regressor.
3. WHEN a required artefact file is missing at startup, THE Prediction_Engine SHALL raise a descriptive error that names the missing artefact file path and SHALL halt initialisation without loading any remaining artefacts.
4. WHEN an input feature value is outside the min-max bounds recorded in the normalisation artefact, THE Prediction_Engine SHALL log a warning that identifies the feature name and its received value before proceeding with inference.
5. THE Prediction_Engine SHALL decode all numeric classification outputs to their original string labels using the persisted label-mapping artefact before including them in the response object.
6. THE Prediction_Engine SHALL complete a single-record inference request within 500 milliseconds, measured on a single CPU core with no GPU, after all artefacts have been loaded into memory.
7. WHEN an input Patient_Record is missing one or more required feature columns, THE Prediction_Engine SHALL raise a descriptive error that names each missing column and SHALL NOT proceed with inference.
8. THE Prediction_Engine SHALL clip the raw Readmission_Probability regressor output to the range [0, 100] before including it in the response object, regardless of the model's raw output value.

---

### Requirement 9: REST API Backend

**User Story:** As a frontend developer, I want a REST API that exposes patient data and predictions, so that the Dashboard and mobile clients can retrieve information without direct database access.

#### Acceptance Criteria

1. THE API SHALL expose a POST endpoint at `/predict` that accepts a JSON body containing a Patient_Record and returns Risk_Level, Recovery_Status, Doctor_Recommendation, and Readmission_Probability as a JSON response.
2. THE API SHALL expose a GET endpoint at `/patients/{patient_id}/summary` that returns all available days of trend data for a given patient sorted by Day ascending, including daily Compliance_Score, Deviation_Score, Recovery_Score, Health_Trend, and Readmission_Probability values.
3. THE API SHALL expose a GET endpoint at `/patients` that returns a paginated list of all patients with their latest Risk_Level, Recovery_Status, and Readmission_Probability, supporting `page` (default 1) and `page_size` (default 20, maximum 100) query parameters.
4. WHEN a request to `/predict` contains a JSON body missing any required field, THE API SHALL return an HTTP 422 response with a descriptive error message that lists all missing field names.
5. WHEN a request to `/patients/{patient_id}/summary` references a Patient_ID that does not exist in the dataset, THE API SHALL return an HTTP 404 response with a descriptive error message that includes the requested Patient_ID.
6. THE API SHALL ensure that at least 95% of requests complete within 1000 milliseconds for single-patient endpoints and within 3000 milliseconds for list endpoints, measured under a concurrent load of up to 50 requests.
7. THE API SHALL validate all seven numeric fields on the `/predict` endpoint against the following clinically plausible ranges — Heart_Rate: [30, 250] bpm; Systolic_BP: [50, 300] mmHg; Diastolic_BP: [30, 200] mmHg; SpO2: [50, 100] percent; Respiratory_Rate: [5, 60] breaths/min; Body_Temperature: [34.0, 42.0] °C; Blood_Glucose: [20, 600] mg/dL — and IF any value falls outside its range, THE API SHALL return an HTTP 422 response that identifies each out-of-range field by name and includes its received value.
8. WHEN the Prediction_Engine raises an unhandled exception during inference for a `/predict` request, THE API SHALL return an HTTP 500 response with a generic error message and SHALL NOT expose internal stack traces or model artefact paths in the response body.

---

### Requirement 10: Doctor Dashboard

**User Story:** As a doctor, I want a web-based dashboard, so that I can monitor all post-discharge patients, identify high-risk individuals, and review AI recommendations at a glance.

#### Acceptance Criteria

1. THE Dashboard SHALL display a patient list view showing each patient's Patient_ID, Disease_Type, latest Risk_Level, latest Recovery_Status, and latest Readmission_Probability, sortable by Risk_Level descending by default.
2. WHEN a doctor selects a patient from the patient list view, THE Dashboard SHALL display a per-patient detail view that renders all three of the following charts: a line chart of Recovery_Score over all available days, a line chart of Compliance_Score over all available days, and a line chart of Readmission_Probability over all available days; all three charts MUST be rendered simultaneously for this criterion to be satisfied.
3. THE Dashboard SHALL display a risk alert panel that lists all patients whose latest Risk_Level is High, ordered by descending Readmission_Probability; IF no patients have Risk_Level High, THE Dashboard SHALL display a message indicating that no high-risk patients are currently flagged.
4. WHEN a patient's latest Readmission_Probability exceeds 70, THE Dashboard SHALL render that patient's row in the patient list view with a red background colour; rows with Readmission_Probability of 70 or below SHALL NOT have a red background.
5. WHEN a doctor views the per-patient detail view, THE Dashboard SHALL display the AI-generated Doctor_Recommendation alongside a plain-language explanation of the top three SHAP-contributing features; IF the explainability field for that prediction is flagged as unavailable, THE Dashboard SHALL display a notice stating that the explanation is not available for this prediction in place of the feature chart.
6. THE Dashboard SHALL display summary statistics including total patient count, percentage of patients in each Risk_Level category (Low, Medium, High), and percentage of patients in each Recovery_Status category.
7. WHEN a doctor selects filter values from the Disease_Type and Risk_Level dropdown selectors, THE Dashboard SHALL update the patient list view to show only patients matching all selected filter criteria; IF the filtered result set is empty, THE Dashboard SHALL display a message indicating no patients match the selected filters.
8. WHEN the data source becomes unreachable, THE Dashboard SHALL display a user-visible error banner at the top of the page indicating a data connection issue; the last successfully loaded patient data SHALL remain visible in a read-only state beneath the error banner rather than being cleared.

---

### Requirement 11: Model Explainability

**User Story:** As a clinician, I want to understand why the AI produced a given recommendation, so that I can trust and act on the output responsibly.

#### Acceptance Criteria

1. THE Prediction_Engine SHALL compute SHAP values for each prediction and return the features with the highest absolute SHAP value, up to three, alongside their direction (positive for values strictly greater than zero, negative for values strictly less than zero); IF fewer than three features have non-zero SHAP values, THE Prediction_Engine SHALL return only the available non-zero features without padding to three.
2. WHEN a doctor opens the per-patient detail view, THE Dashboard SHALL render a horizontal bar chart of SHAP feature contributions for the most recent prediction, where "most recent" is determined by the highest Day value for that patient; IF the explainability field is flagged as unavailable, THE Dashboard SHALL display a notice stating the explanation is not available in place of the SHAP chart.
3. IF SHAP computation raises an exception for a given model type, THE Prediction_Engine SHALL log an error entry that includes the model type and the full exception message, skip SHAP computation for that request, and return the prediction with the explainability field set to a string value of "unavailable".

---

### Requirement 12: Property-Based Testing

**User Story:** As a quality engineer, I want property-based tests for core computational modules, so that correctness invariants are verified across a broad range of generated inputs.

#### Acceptance Criteria

1. THE Preprocessing_Pipeline SHALL be covered by a property-based test verifying that, for any input dataframe where all 51 required columns are present with valid dtypes and no null values exist in the following required columns — Patient_ID, Day, Disease_Type, Gender, Smoking_Status, Risk_Level, Recovery_Status, Readmission_Probability, Doctor_Recommendation — the output feature matrix contains no null values.
2. THE Comparison_Engine SHALL be covered by a property-based test verifying that Deviation_Score is always non-negative for any combination of Ideal_Health_Score and Real_Health_Score values drawn from [0, 1].
3. THE Comparison_Engine SHALL be covered by a property-based test verifying that Compliance_Score remains within [0, 100] for any combination of the six adherence components where Steps_Compliance ∈ [0, 1], Medication_Taken ∈ {0.0, 1.0}, normalised Sleep_Deviation ∈ [0, 1], Water_Compliance ∈ [0, 1], Exercise_Completed ∈ {0.0, 1.0}, and Diet_Compliance ∈ [0, 100].
4. THE Prediction_Engine SHALL be covered by a property-based test verifying that Readmission_Probability output is always within [0, 100] for any raw model output value drawn from an unbounded float range.
5. THE Preprocessing_Pipeline SHALL be covered by a property-based test verifying the round-trip property: for any label string drawn from the valid label sets — Risk_Level: {Low, Medium, High}; Recovery_Status: {Recovered, Improving, Stable, Delayed Recovery, Worsening, Critical}; Doctor_Recommendation: {Continue Current Treatment, Increase Monitoring, Medication Adjustment, Immediate Doctor Review, Hospital Readmission} — encoding the label with the label encoder and then decoding it with the persisted mapping artefact returns the original string.
6. THE Comparison_Engine SHALL be covered by a property-based test verifying the idempotence property: for any Patient_Record that has already been processed by the Comparison_Engine (i.e., all six outputs — Compliance_Score, Ideal_Health_Score, Real_Health_Score, Deviation_Score, Recovery_Score, Health_Trend — are already populated), running the Comparison_Engine on that same record a second time produces identical values for all six outputs.
7. WHEN a POST request to `/predict` is missing one or more required fields, THE API SHALL return HTTP 422.
8. IF a POST request to `/predict` contains malformed JSON or any field value that fails clinical range validation, THE API SHALL return HTTP 422.
9. WHEN a POST request to `/predict` is well-formed and contains valid values for all required fields — Patient_ID, Day, Disease_Type, Gender, Age, Heart_Rate, Systolic_BP, Diastolic_BP, SpO2, Respiratory_Rate, Body_Temperature, Blood_Glucose, Actual_Steps, Medication_Taken, Actual_Sleep_Hours, Water_Intake, Exercise_Completed, Diet_Compliance — THE API SHALL return HTTP 200 with a response body containing all four prediction fields: Risk_Level, Recovery_Status, Doctor_Recommendation, and Readmission_Probability.
