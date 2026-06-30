# Authentication System Fix Summary

## Problem Identified

The login page was not working due to a **database schema mismatch**:

### Root Cause
- Supabase (your PostgreSQL provider) has a built-in `userrole` ENUM type with values: `['admin', 'doctor', 'patient']`
- Our initial migration created the `role` column as `VARCHAR(20)` 
- When trying to insert users, PostgreSQL rejected the VARCHAR value because the actual column type was `userrole` ENUM

### Error Message
```
column "role" is of type userrole but expression is of type character varying
HINT: You will need to rewrite or cast the expression.
```

---

## Fixes Applied

### 1. Database Migration (`328660e03ab4_fix_users_table_role_type.py`)
**Created a new migration to cast the role column:**
```sql
ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole
```

This changes the column from VARCHAR to the existing ENUM type.

### 2. Updated SQLAlchemy Model (`app/auth/models.py`)
**Changed from:**
```python
role = Column(String(20), nullable=False, default="patient")
```

**To:**
```python
from sqlalchemy import Enum as SQLEnum

role = Column(
    SQLEnum(UserRole, name="userrole", create_type=False),
    nullable=False,
    default=UserRole.patient
)
```

Key points:
- `create_type=False` tells SQLAlchemy NOT to create the ENUM (it already exists in Supabase)
- Uses the Python `UserRole` enum class for type safety
- Properly maps to the database `userrole` ENUM type

### 3. Updated Environment Variables (`.env`)
**Added missing variables:**
```env
# Authentication & Security
JWT_SECRET_KEY=your-super-secret-random-string-at-least-32-chars-long-abc123xyz789
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=30

# Google OAuth Configuration
GOOGLE_CLIENT_ID=<YOUR_GOOGLE_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_GOOGLE_CLIENT_SECRET>

# URLs (for OAuth redirects)
FRONTEND_URL=https://healthcare-agent-2-0-xi.vercel.app
BACKEND_URL=https://healthcare-agent-backend-3hju.onrender.com

# CORS Configuration (added production frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://healthcare-agent-2-0-xi.vercel.app
```

### 4. Fixed Circular Import (`app/database/models.py`)
**Added explicit import of UserDB:**
```python
# Import auth models so Base.metadata includes the users table
from app.auth.models import UserDB  # noqa: F401
```

This ensures the users table is registered with SQLAlchemy's metadata.

---

## Installation Steps (Local)

If you need to set up on a new machine:

```powershell
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install missing auth dependencies (if needed)
pip install email-validator python-jose[cryptography]

# 3. Run database migrations
python -m alembic upgrade head

# 4. Test the auth system
python test_auth.py
```

---

## Deployment Steps (Render)

### Step 1: Add Environment Variables on Render Dashboard

Go to **dashboard.render.com** → Your backend service → **Environment** tab

Add these 5 variables (if not already present):

| Key | Value |
|-----|-------|
| `JWT_SECRET_KEY` | `<Generate a random 32+ character string>` |
| `GOOGLE_CLIENT_ID` | `<Your Google OAuth Client ID>` |
| `GOOGLE_CLIENT_SECRET` | `<Your Google OAuth Client Secret>` |
| `FRONTEND_URL` | `https://healthcare-agent-2-0-xi.vercel.app` |
| `BACKEND_URL` | `https://healthcare-agent-backend-3hju.onrender.com` |
| `CORS_ORIGINS` | `https://healthcare-agent-2-0-xi.vercel.app,http://localhost:5173,http://localhost:3000` |

### Step 2: Trigger Manual Deploy on Render

1. Go to your Render service
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Wait 2-3 minutes for deployment to complete
4. Check logs for any errors

### Step 3: Run Migration on Render

After deploy, run the migration in the Render Shell:

```bash
# Open Render Shell (from dashboard) and run:
python -m alembic upgrade head
```

---

## Testing the Login Page

Once Render is deployed, test the live frontend:

**URL:** https://healthcare-agent-2-0-xi.vercel.app/login

### Test A - Register New Admin
1. Click "Create Account" tab
2. Fill in:
   - Email: `admin@healthcare.com`
   - Password: `Admin1234!`
   - Name: `System Admin`
   - Role: Click **Admin** (🔒)
3. Click "Create Account"
4. **Expected:** Redirected to dashboard with full data access

### Test B - Register Doctor
1. Open incognito window
2. Create Account:
   - Email: `doctor@healthcare.com`
   - Password: `Doctor123!`
   - Name: `Dr Smith`
   - Role: **Doctor**
3. **Expected:** Dashboard access (no ML Models page)

### Test C - Register Patient
1. Open another incognito window
2. Create Account:
   - Email: `patient@healthcare.com`
   - Password: `Patient123!`
   - Name: `John Doe`
   - Role: **Patient**
3. **Expected:** Personal health portal only

### Test D - Google OAuth
1. Click "Continue with Google"
2. Sign in with Google account
3. **Expected:** Logged in and redirected to dashboard

---

## Status

✅ **Local Testing:** Passed (test_auth.py runs successfully)  
✅ **Code Committed:** Pushed to GitHub (commit `9ca1bcd`)  
⏳ **Render Deployment:** Needs migration run on Render  
⏳ **Live Testing:** Pending Render deployment completion

---

## Files Changed

1. `app/auth/models.py` - Updated to use SQLEnum  
2. `alembic/versions/328660e03ab4_fix_users_table_role_type.py` - New migration
3. `.env` - Added missing auth and CORS config
4. `app/database/models.py` - Added explicit UserDB import
5. `test_auth.py` - Created test script (can be deleted after verification)
6. `check_db_schema.py` - Created diagnostic script (can be deleted)

---

## Next Steps

1. ✅ **Verify Render deployment completes** (check logs for errors)
2. ✅ **Run migration on Render:** `python -m alembic upgrade head`
3. ✅ **Test the live login page** with all 3 roles
4. ✅ **Test Google OAuth** sign-in
5. ✅ **Clean up test files** (delete `test_auth.py` and `check_db_schema.py`)
