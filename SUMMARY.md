# Prototype Summary - Healthcare Agent 2.0

This document summarizes all the modifications, bug fixes, and deployment steps completed during this pair-programming session to make the **Healthcare Agent 2.0** prototype fully functional and live.

---

## 🛠️ 1. Codebase Bug Fixes

We identified and resolved several critical bugs across the backend, database loader, machine learning pipeline, and frontend:

### Database & Data Loading (`scripts/load_sample_data.py`)
- **Readmission Probability Overflow**: The CSV represented `Readmission_Probability` as a percentage (e.g. `32.0`), which caused database overflow errors on the `DECIMAL(5, 4)` column (max value `9.9999`). Scaled it by dividing by `100.0` (to `[0.0, 1.0]`).
- **Water Intake Scale**: Scaled water intake fields from Liters (in CSV) to mL (expected by DB integer columns) by multiplying by `1000`.

### Data Validation (`app/models/schemas.py`)
- **Optional Fields**: Made `smoking_status` and `alcohol_consumption` optional (`Optional[...]`) in the Pydantic schema to prevent validation failures on records containing `None`.
- **New Literal Value**: Added `"Occasional"` to the `alcohol_consumption` Literal to match the raw data in the CSV.
- *Result*: This allowed **100% of the 5,000 patient records** to load and train successfully (previously 3,800 records were skipped).

### Machine Learning Pipeline (`app/ml/` & `scripts/`)
- **Categorical Encoding Bug (`app/ml/feature_engineer.py`)**: Added `medication_taken` and `exercise_completed` to `CATEGORICAL_COLUMNS` so they are one-hot encoded. Previously, they remained as string values (`'Yes'`/`'No'`), which crashed the XGBoost training matrix.
- **Model Registration Commit (`scripts/train_model.py`)**: Added `await session.commit()` after registering the model to persist the active model in the database (previously it was rolled back on session close).
- **FeaturePreprocessor Persistence (`scripts/train_model.py`)**: Added code to save the fitted `FeaturePreprocessor` to disk as `models/preprocessor_v1.0.joblib` during training so that the backend can use it for inference.

### Backend Startup & OS Compatibility
- **InferenceEngine Lifecycle (`app/main.py`)**: Updated the lifespan startup hook to instantiate the `InferenceEngine` and load the active model and preprocessor on startup.
- **Linux Path Compatibility (`app/ml/model_registry.py`)**: Added code to replace backslashes (`\`) with forward slashes (`/`) in the model path when running on Linux (Render) to prevent `FileNotFoundError` on models registered from Windows.

### Frontend Build & Routing (`frontend/`)
- **Removed Unused Leftovers**: Deleted `client.tsx` and `ssr.tsx` which were causing compilation errors due to missing TanStack Start and Vinxi dependencies.
- **Build Script (`package.json`)**: Changed the build script to use `tsc --noEmit && vite build` instead of `tsc -b` to prevent emitting conflicting `.js` files in the source directory.
- **Type Corrections**: Fixed a `children` type mismatch in `FloatingPanel.tsx` and removed the unsupported `scrollRestoration` option in `router.tsx`.
- **Vercel SPA Routing (`vercel.json`)**: Created `vercel.json` with rewrite rules to prevent `404 NOT FOUND` errors when refreshing sub-pages on Vercel.

---

## 📈 2. ML Model Performance

The XGBoost model was successfully trained on the full dataset:
- **Dataset Size**: 5,000 records (167 unique patients)
- **AUC-ROC**: **0.9872**
- **F1 Score**: **0.9370**
- **Accuracy**: **92.93%**
- **Model Path**: `models/xgboost_v1.0.pkl`
- **Preprocessor Path**: `models/preprocessor_v1.0.joblib`

---

## 🌐 3. Deployed Infrastructure

The prototype is fully deployed and live in the cloud:

| Component | Platform | URL | Status |
|-----------|----------|-----|--------|
| **Database** | Supabase | `aws-1-ap-northeast-1.pooler.supabase.com` | **Active & Populated** |
| **Backend API** | Render | [healthcare-agent-backend-3hju.onrender.com](https://healthcare-agent-backend-3hju.onrender.com/) | **Live (Model Loaded)** |
| **Frontend UI** | Vercel | [healthcare-agent-2-0-xi.vercel.app](https://healthcare-agent-2-0-xi.vercel.app/) | **Live & Connected** |

---

## 🧪 4. Local Run Commands

To run the project locally on your machine:

### Backend
```powershell
# Activate virtual environment and start Uvicorn
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health/detailed`

### Frontend
```powershell
# Go to frontend folder and start Vite
cd frontend
npm run dev
```
- Local URL: `http://localhost:5173`
