# Deployment Guide — Healthcare Agent 2.0

## Free Stack: Supabase (DB) + Render (Backend) + Vercel (Frontend)

### Step 1: Set up Supabase Database
1. Go to supabase.com → New Project
2. Note your connection string (Settings → Database → Connection string → URI)
3. It looks like: `postgresql://postgres:[PASSWORD]@db.[ref].supabase.co:5432/postgres`

### Step 2: Run Database Migrations
```bash
# On your local machine with Python installed
pip install -r requirements.txt
export DATABASE_HOST=db.[ref].supabase.co
export DATABASE_PORT=5432
export DATABASE_NAME=postgres
export DATABASE_USER=postgres
export DATABASE_PASSWORD=your-supabase-password
alembic upgrade head
```

### Step 3: Load Sample Data
```bash
python scripts/load_sample_data.py
```

### Step 4: Deploy Backend to Render
1. Go to render.com → New Web Service
2. Connect your GitHub repo
3. Set Root Directory to `.` (project root)
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   - `DATABASE_HOST` = your Supabase host
   - `DATABASE_PASSWORD` = your Supabase password
   - `DATABASE_USER` = postgres
   - `DATABASE_NAME` = postgres
7. Deploy!

### Step 5: Deploy Frontend to Vercel
1. Go to vercel.com → New Project
2. Import your GitHub repo
3. Set Root Directory to `frontend`
4. Add Environment Variable:
   - `VITE_API_URL` = your Render backend URL (e.g. https://healthcare-agent-backend.onrender.com)
5. Deploy!

### Step 6: Optional - Train ML Model
Once deployed with data loaded:
```bash
python scripts/train_model.py
```
This trains XGBoost on your patient data. Until then, the backend uses heuristic predictions.
