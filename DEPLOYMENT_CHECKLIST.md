# Healthcare Agent 2.0 - Deployment Checklist

## ✅ **COMPLETED** - Setup & Configuration

### Backend (Render)
- [x] Service created on Render
- [x] Connected to GitHub repository
- [x] Auto-deploy enabled on `main` branch push
- [x] Environment variables configured:
  - [x] Database credentials (DATABASE_*)
  - [x] JWT secret and config
  - [x] Google OAuth credentials
  - [x] Frontend/Backend URLs
  - [x] CORS origins

### Frontend (Vercel)
- [x] Project deployed on Vercel
- [x] Connected to GitHub repository
- [x] Auto-deploy enabled
- [x] Environment variable configured: `VITE_API_URL`

### Database (Supabase)
- [x] PostgreSQL database provisioned
- [x] Patient records table created and populated (5,000 records)
- [x] ML models table created
- [x] Users table created for authentication
- [x] Indexes created for performance

---

## 🔄 **IN PROGRESS** - Auth System Deployment

### Current Status: Migration Fix Needed

**What was fixed:**
- ✅ Database schema mismatch resolved (VARCHAR → userrole ENUM)
- ✅ SQLAlchemy models updated to use ENUM type
- ✅ Code committed and pushed to GitHub
- ✅ Render auto-deploy triggered

**What needs to be done:**

### Step 1: Wait for Render Deployment
1. Go to: https://dashboard.render.com
2. Click on your backend service: `healthcare-agent-backend-3hju`
3. Watch the **"Events"** tab for deployment completion (~2-3 minutes)
4. Check for any red error messages
5. ✅ Mark complete when you see "Deploy live" message

### Step 2: Run Database Migration on Render
1. From the Render dashboard, click **"Shell"** tab
2. Run this command in the shell:
   ```bash
   python -m alembic upgrade head
   ```
3. ✅ Verify output shows: `Running upgrade a2f1c3d4e5b6 -> 328660e03ab4, fix_users_table_role_type`

### Step 3: Test Backend API
Test the health endpoint:
```bash
curl https://healthcare-agent-backend-3hju.onrender.com/health/detailed
```

Expected response:
```json
{
  "status": "healthy",
  "database": {"status": "healthy", ...},
  "inference_engine": {"loaded": true, "model_version": "v1.0"},
  ...
}
```

### Step 4: Test Live Login Page

Go to: **https://healthcare-agent-2-0-xi.vercel.app/login**

#### Test A: Email/Password Registration (Admin)
- [ ] Click "Create Account"
- [ ] Email: `admin@healthcare.com`
- [ ] Password: `Admin1234!`
- [ ] Name: `Test Admin`
- [ ] Role: **Admin** 🔒
- [ ] Click "Create Account"
- [ ] **Expected:** Redirected to dashboard, see all patient data

#### Test B: Email/Password Registration (Doctor)
- [ ] Open incognito/private window
- [ ] Create Account with role **Doctor**
- [ ] **Expected:** Dashboard access, no ML Models page

#### Test C: Email/Password Registration (Patient)
- [ ] Open another incognito window
- [ ] Create Account with role **Patient**
- [ ] **Expected:** Personal health portal only

#### Test D: Google OAuth
- [ ] Click "Continue with Google" button
- [ ] Sign in with Google
- [ ] **Expected:** Redirected back and logged in

#### Test E: Login with Existing Account
- [ ] Try logging in with admin credentials from Test A
- [ ] **Expected:** Successfully logged in

### Step 5: Test Role-Based Access Control

**As Admin:**
- [ ] Can see Dashboard with all metrics
- [ ] Can see Patients List
- [ ] Can click on a patient and see details
- [ ] Can see ML Models page
- [ ] Sidebar shows all menu items

**As Doctor:**
- [ ] Can see Dashboard
- [ ] Can see Patients List
- [ ] Can see patient details
- [ ] **Cannot** see ML Models page (hidden)

**As Patient:**
- [ ] **Cannot** see Dashboard (redirected to personal portal)
- [ ] See personal health card only
- [ ] No access to other patients' data

---

## 📊 **Performance & Functionality Checks**

### Backend API Endpoints
Test these endpoints (use Postman or curl):

```bash
# 1. Health check
GET https://healthcare-agent-backend-3hju.onrender.com/health/detailed

# 2. Get dashboard stats (requires auth token)
GET https://healthcare-agent-backend-3hju.onrender.com/api/dashboard/stats
Headers: Authorization: Bearer <your_access_token>

# 3. Get patients list
GET https://healthcare-agent-backend-3hju.onrender.com/api/patients?page=1&page_size=10
Headers: Authorization: Bearer <your_access_token>

# 4. Get model info
GET https://healthcare-agent-backend-3hju.onrender.com/api/models/info
Headers: Authorization: Bearer <your_access_token>
```

### Frontend Pages
- [ ] **Login Page** (`/login`) - Loads correctly
- [ ] **Dashboard** (`/`) - Shows charts and metrics
- [ ] **Patients List** (`/patients`) - Paginated table loads
- [ ] **Patient Details** (`/patients/:id`) - Charts and trend data
- [ ] **ML Models** (`/models`) - Model metrics display
- [ ] **Auth Callback** (`/auth/callback`) - Google OAuth redirect

---

## 🐛 **Common Issues & Solutions**

### Issue: "500 Internal Server Error" on Registration
**Solution:** Run the migration on Render:
```bash
python -m alembic upgrade head
```

### Issue: CORS Error in Browser Console
**Solution:** Check `CORS_ORIGINS` environment variable on Render includes your frontend URL:
```
https://healthcare-agent-2-0-xi.vercel.app
```

### Issue: "Invalid token" or auth not persisting
**Solution:** Check `JWT_SECRET_KEY` is set on Render and matches across deployments

### Issue: Google OAuth fails
**Solution:** Verify these environment variables on Render:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `FRONTEND_URL`
- `BACKEND_URL`

### Issue: Frontend shows "Network Error"
**Solution:** Check `VITE_API_URL` on Vercel points to: `https://healthcare-agent-backend-3hju.onrender.com`

---

## 📝 **Post-Deployment Cleanup**

Once everything works:

1. **Delete test scripts:**
   ```powershell
   rm test_auth.py
   rm check_db_schema.py
   ```

2. **Commit cleanup:**
   ```bash
   git add -A
   git commit -m "chore: remove test scripts after successful deployment"
   git push
   ```

3. **Document any custom configurations** added during deployment

---

## 🎉 **Success Criteria**

The deployment is complete when ALL of these are true:

- [ ] Backend is deployed on Render and healthy
- [ ] Frontend is deployed on Vercel and loads
- [ ] Database migration has run successfully
- [ ] User registration works (email/password)
- [ ] Google OAuth login works
- [ ] All 3 user roles work correctly (admin, doctor, patient)
- [ ] Dashboard shows real data (167 patients, compliance %, etc.)
- [ ] Patient list is paginated and filterable
- [ ] Patient detail page shows 30-day trends
- [ ] ML Models page shows XGBoost metrics
- [ ] No CORS errors in browser console
- [ ] No 500 errors on any page

---

## 🔗 **Quick Links**

- **Live Frontend:** https://healthcare-agent-2-0-xi.vercel.app
- **Live Backend API:** https://healthcare-agent-backend-3hju.onrender.com
- **API Docs (Swagger):** https://healthcare-agent-backend-3hju.onrender.com/docs
- **Render Dashboard:** https://dashboard.render.com
- **Vercel Dashboard:** https://vercel.com/dashboard
- **GitHub Repo:** https://github.com/quantumaws123-pixel/healthcare-agent-2.0

---

**Last Updated:** 2026-06-30  
**Status:** Auth system fix deployed, migration pending on Render
