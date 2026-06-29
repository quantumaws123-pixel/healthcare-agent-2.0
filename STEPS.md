# Healthcare Agent 2.0 — Complete Setup & Deployment Guide

## Your Supabase Connection Details
- **Host**: `aws-1-ap-northeast-1.pooler.supabase.com`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres.zkbilwspywgiocmtgfqg`
- **Password**: (set in `.env` — do not share publicly)

---

## PART 1: Local Setup (Run Backend on Your Machine)

### Step 1 — Install Python dependencies
```powershell
cd "c:\Users\Gilson K\Downloads\healthcare-agent-2.0\healthcare-agent-2.0"
pip install -r requirements.txt
pip install psycopg2-binary==2.9.10
```

### Step 2 — Run database migrations (creates tables in Supabase)
```powershell
alembic upgrade head
```
Expected output: `Running upgrade -> b1e039b53fc2, Initial database schema`

### Step 3 — Load sample patient data
```powershell
python scripts/load_sample_data.py --limit 5000
```
This loads 5000 rows from `Healthcare_Digital_Twin_100000_generated_check.csv` into Supabase.
To load all 100,000 rows (takes ~5 min):
```powershell
python scripts/load_sample_data.py
```

### Step 4 — Train the ML model (optional but recommended)
```powershell
python scripts/train_model.py
```
This trains XGBoost on the loaded data and saves the model to `./models/`. Until this is done, the `/predict` endpoint uses heuristic risk levels.

### Step 5 — Start the backend server
```powershell
python -m uvicorn app.main:app --reload --port 8000
```
Server will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs
Health check at: http://localhost:8000/health/detailed

### Step 6 — Start the frontend
Open a **new terminal**:
```powershell
cd "c:\Users\Gilson K\Downloads\healthcare-agent-2.0\healthcare-agent-2.0\frontend"
npm install
npm run dev
```
Frontend will be at: http://localhost:5173

---

## PART 2: Deploy to Production (Free Hosting)

### Stack
| Layer | Platform | Cost |
|-------|----------|------|
| Frontend (React/Vite) | Vercel | Free forever |
| Backend (FastAPI + ML) | Render | Free (cold starts after 15min idle) |
| Database (PostgreSQL) | Supabase | Free forever |

---

### Step A — Push code to GitHub
1. Create a new GitHub repository at https://github.com/new
2. In your project folder, run:
```powershell
git init
git add .
git commit -m "Initial commit - Healthcare Agent 2.0"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git push -u origin main
```

---

### Step B — Deploy Backend to Render

1. Go to https://render.com → **New Web Service**
2. Connect your GitHub account and select your repo
3. Configure:
   - **Name**: `healthcare-agent-backend`
   - **Root Directory**: `.` (leave blank / project root)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt && pip install psycopg2-binary==2.9.10`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables** (click "Add Environment Variable" for each):

| Key | Value |
|-----|-------|
| `DATABASE_HOST` | `aws-1-ap-northeast-1.pooler.supabase.com` |
| `DATABASE_PORT` | `5432` |
| `DATABASE_NAME` | `postgres` |
| `DATABASE_USER` | `postgres.zkbilwspywgiocmtgfqg` |
| `DATABASE_PASSWORD` | `quantumaws123-pixel` |
| `DATABASE_POOL_SIZE` | `5` |
| `DATABASE_MAX_OVERFLOW` | `5` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` (update after Vercel deploy) |

5. Click **Create Web Service** → Wait for deploy (~3-5 minutes)
6. Copy your backend URL: `https://healthcare-agent-backend.onrender.com`

---

### Step C — Deploy Frontend to Vercel

1. Go to https://vercel.com → **New Project**
2. Import your GitHub repo
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite (auto-detected)
4. Add **Environment Variable**:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://healthcare-agent-backend.onrender.com` |

5. Click **Deploy** → Wait ~2 minutes
6. Your app is live at: `https://your-project.vercel.app`

---

### Step D — Update CORS on Render

After getting your Vercel URL, go back to Render → your service → **Environment** tab and update:
- `CORS_ORIGINS` = `https://your-project.vercel.app,http://localhost:5173`

Then click **Save Changes** (Render auto-redeploys).

---

## PART 3: Verify Everything Works

### Test the API (replace with your actual Render URL)
```powershell
# Health check
curl https://healthcare-agent-backend.onrender.com/health/detailed

# Get patients list
curl https://healthcare-agent-backend.onrender.com/patients

# Dashboard stats
curl https://healthcare-agent-backend.onrender.com/dashboard/stats
```

Or open: https://healthcare-agent-backend.onrender.com/docs (Swagger UI)

---

## PART 4: Troubleshooting

### "getaddrinfo failed" when running locally
- **Cause**: Your machine can't reach Supabase's direct connection (IPv6 only)
- **Fix**: Use Session Pooler (already configured in `.env`)
- Check `.env` has: `DATABASE_HOST=aws-1-ap-northeast-1.pooler.supabase.com`

### "Application startup failed" locally
- **Cause**: `DATABASE_PASSWORD` env var not loaded
- **Fix**: Make sure `.env` file exists in project root with all credentials

### Frontend shows no data
- **Cause**: `VITE_API_URL` not set or CORS not configured
- **Fix**: Set `VITE_API_URL` in Vercel environment variables

### Render deploy fails
- **Cause**: Missing `psycopg2-binary` in build command
- **Fix**: Build command must be: `pip install -r requirements.txt && pip install psycopg2-binary==2.9.10`

### ML model not trained (predictions use heuristics)
- Run `python scripts/train_model.py` locally after loading data
- The trained model file will need to be included in your git repo (./models/ folder) or retrained after deploy

---

## PART 5: Important Notes

### Security
- ⚠️ Your Supabase password was shared in chat — **reset it now**:
  1. Supabase Dashboard → Settings → Database → Reset database password
  2. Update `.env` and Render environment variables with new password

### Free Tier Limits
- **Render**: Backend sleeps after 15 min of inactivity → first request takes ~30s to wake
- **Supabase**: 500MB storage, no expiry on free tier
- **Vercel**: Unlimited deployments, free forever for frontend

### Data Loading
- The CSV file (`Healthcare_Digital_Twin_100000_generated_check.csv`) is 100,000 rows
- Start with `--limit 5000` for testing
- Load all data for production: `python scripts/load_sample_data.py`

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `alembic upgrade head` | Create/update database tables |
| `python scripts/load_sample_data.py --limit 5000` | Load sample data |
| `python scripts/train_model.py` | Train XGBoost ML model |
| `python -m uvicorn app.main:app --reload --port 8000` | Start backend locally |
| `cd frontend && npm run dev` | Start frontend locally |
| `alembic downgrade base` | Drop all tables (careful!) |
