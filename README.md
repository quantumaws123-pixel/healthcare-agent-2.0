# Healthcare Agent 2.0

An AI-powered **Digital Twin** platform for post-discharge patient monitoring and hospital readmission risk prediction.

The system creates two digital twins per patient:
- **Ideal Twin** — the doctor's prescribed plan (expected steps, sleep, medication, etc.)
- **Real Twin** — actual measured patient behaviour and clinical vitals

By comparing these twins it computes compliance scores, health scores, and a 30-day readmission probability using an XGBoost ML model with SHAP explainability.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Vite)                    │
│              http://localhost:5173  ←→  VITE_API_URL            │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST / JSON
┌────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend  :8000                        │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  /patients  │  │   /predict   │  │  /dashboard/stats    │   │
│  │  /model/info│  │   /health    │  │  /health/detailed    │   │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                │                      │               │
│  ┌──────▼────────────────▼──────────────────────▼───────────┐   │
│  │               Service Layer                              │   │
│  │  DigitalTwinEngine · ComplianceCalc · HealthScoreCalc    │   │
│  │  RecommendationEngine · InferenceEngine (XGBoost/SHAP)   │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  Data Layer                                              │   │
│  │  SQLAlchemy async · PatientRepository · ModelRegistry    │   │
│  │  FeatureEngineer · DataSplitter · ModelTrainer           │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │             ┌──────────────────┐  │
│                             │             │  Cache Backend   │  │
│                             │             │  Redis / memory  │  │
└─────────────────────────────┼─────────────┴──────────────────┘──┘
                              │
             ┌────────────────▼────────────────┐
             │        PostgreSQL 15             │
             │   patient_records  · ml_models   │
             └─────────────────────────────────┘
```

---

## Quick Start (local with Docker Compose)

**Prerequisites:** Docker Desktop, Python 3.11+

### Step 1 — Clone and configure

```bash
git clone <repo-url>
cd healthcare-agent-2.0
cp .env.example .env
# Edit .env and set DATABASE_PASSWORD=postgres (matches docker-compose defaults)
```

### Step 2 — Start services

```bash
docker-compose up --build -d
```

The API will be available at `http://localhost:8000` once the health check passes.

### Step 3 — Run database migrations

```bash
pip install -r requirements.txt
alembic upgrade head
```

### Step 4 — Load sample data

```bash
python scripts/load_sample_data.py
# Or load only the first 10 000 rows:
python scripts/load_sample_data.py --limit 10000
```

### Step 5 — Train the ML model

```bash
python scripts/train_model.py
```

The trained XGBoost model is saved to `./models/` and registered as active in the database. The API will use it immediately for predictions.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_HOST` | `localhost` | PostgreSQL hostname |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `DATABASE_NAME` | `healthcare_agent` | Database name |
| `DATABASE_USER` | `postgres` | Database username |
| `DATABASE_PASSWORD` | *(required)* | Database password |
| `DATABASE_POOL_SIZE` | `20` | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | `10` | Max connections beyond pool size |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8000` | API bind port |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `MODEL_VERSION` | `latest` | Model version to load for inference |
| `MODEL_PATH` | `./models` | Directory containing trained model files |
| `MODEL_TYPE` | `XGBoost` | Default model architecture |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`) |
| `LOG_FORMAT` | `json` | Log output format (`json` or `text`) |
| `CACHE_TTL_SECONDS` | `300` | Dashboard stats cache TTL in seconds |
| `CACHE_ENABLED` | `true` | Enable or disable the cache layer |
| `REDIS_URL` | *(optional)* | Redis connection URL — falls back to in-memory cache if unset |
| `RATE_LIMIT` | `1000` | Max API requests per hour per client |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/patients` | Paginated patient list with optional filters (`disease_type`, `risk_level`, `page`, `page_size`) |
| `GET` | `/patients/{patient_id}/summary` | 30-day daily trend data for a specific patient |
| `POST` | `/predict` | Submit a patient record and receive readmission risk prediction with SHAP explanations |
| `GET` | `/dashboard/stats` | Aggregated dashboard KPIs (total patients, risk distribution, avg compliance, etc.) |
| `GET` | `/model/info` | Current active model version, type, training date, and evaluation metrics |
| `GET` | `/health` | Simple liveness check (load-balancer / uptime monitoring) |
| `GET` | `/health/detailed` | Detailed health status: DB connectivity, inference engine, cache backend, app version |

### Example: Patient list with filters

```
GET /patients?disease_type=Diabetes&risk_level=High&page=1&page_size=20
```

### Example: Prediction request

```json
POST /predict
{
  "patient_id": "P001",
  "day": 15,
  "heart_rate": 88,
  "systolic_bp": 145,
  "diastolic_bp": 92,
  ...
}
```

### Example: Detailed health response

```json
GET /health/detailed
{
  "status": "healthy",
  "database": { "status": "healthy", "message": "Database connection successful" },
  "inference_engine": { "loaded": false, "model_version": null },
  "cache": { "backend": "in-memory" },
  "version": "1.0.0"
}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI 0.110+ with async/await |
| **Database** | PostgreSQL 15 via SQLAlchemy 2.x (asyncpg driver) |
| **Migrations** | Alembic |
| **ML Models** | XGBoost, scikit-learn (Logistic Regression, Random Forest), TensorFlow/Keras (LSTM) |
| **Explainability** | SHAP (SHapley Additive Explanations) |
| **Data Processing** | pandas, NumPy |
| **Caching** | Redis (optional) with in-memory fallback |
| **Validation** | Pydantic v2 + pydantic-settings |
| **Logging** | Python `logging` with structured JSON output |
| **Containerisation** | Docker + Docker Compose |
| **Serialisation** | joblib (classical models), TensorFlow SavedModel (LSTM) |
| **Python** | 3.11+ |

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for a step-by-step guide to deploying on the free tier using:
- **Supabase** — managed PostgreSQL
- **Render** — backend API hosting
- **Vercel** — frontend hosting
