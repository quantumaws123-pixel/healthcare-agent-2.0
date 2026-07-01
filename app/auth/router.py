"""Auth router — register, login, Google OAuth, refresh, /me."""
import os, uuid, logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
import httpx

from app.database.connection import get_db_session
from app.auth.models import UserDB, UserRole
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut, RefreshRequest
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    pw_bytes = password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "https://healthcare-agent-2-0-xi.vercel.app")
BACKEND_URL          = os.getenv("BACKEND_URL",  "https://healthcare-agent-backend-3hju.onrender.com")


def _get_role_str(user: UserDB) -> str:
    """Safely extract the role as a plain string regardless of type."""
    role = user.role
    if isinstance(role, str):
        return role
    # UserRole enum or any other type
    return str(role.value) if hasattr(role, "value") else str(role)


def _tokens(user: UserDB) -> TokenResponse:
    role_str = _get_role_str(user)
    return TokenResponse(
        access_token=create_access_token(user.id, role_str),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    existing = (await db.execute(select(UserDB).where(UserDB.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Normalize role to a plain string
    role_str = body.role if isinstance(body.role, str) else str(body.role)
    
    # Doctors start as pending, others are approved immediately
    status = "pending" if role_str == "doctor" else "approved"
    is_active = status == "approved"  # Only approved users can login

    user = UserDB(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        role=role_str,
        status=status,
        is_active=is_active,
    )
    db.add(user)
    await db.flush()
    
    # Create profile based on role
    if role_str == "doctor":
        from app.database.models import DoctorProfileDB
        doctor_profile = DoctorProfileDB(
            id=str(uuid.uuid4()),
            user_id=user.id,
        )
        db.add(doctor_profile)
    elif role_str == "patient":
        from app.database.models import PatientProfileDB
        patient_profile = PatientProfileDB(
            id=str(uuid.uuid4()),
            user_id=user.id,
        )
        db.add(patient_profile)
        
        # Initialize 30 days of time-series clinical records for the patient
        from app.auth.patient_setup import ensure_patient_records
        await ensure_patient_records(user.id, user.email, user.name, db)
    
    await db.refresh(user)
    await db.commit()
    
    logger.info("Registered user %s role=%s status=%s", user.email, user.role, user.status)
    
    # If doctor, return special message (use JSONResponse to avoid raising an exception and triggering traceback logging in get_db_session)
    if status == "pending":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={"detail": "Doctor registration submitted. Your account is pending admin approval."}
        )
    
    return _tokens(user)


@router.get("/debug-register")
async def debug_register(db: AsyncSession = Depends(get_db_session)):
    """Debug endpoint — tests DB write without auth logic."""
    from sqlalchemy import text
    result = await db.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    return {"users_table_exists": True, "user_count": count}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    user = (await db.execute(select(UserDB).where(UserDB.email == body.email))).scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    if user.status == "pending":
        raise HTTPException(403, "Your account is pending admin approval")
    if user.status == "rejected":
        raise HTTPException(403, "Your account application was rejected")
        
    # Automatically verify and initialize patient records if missing
    role_str = _get_role_str(user)
    if role_str == "patient":
        from app.auth.patient_setup import ensure_patient_records
        await ensure_patient_records(user.id, user.email, user.name, db)
        await db.commit()
        
    return _tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db_session)):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user = (await db.execute(select(UserDB).where(UserDB.id == payload["sub"]))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return _tokens(user)


@router.get("/me", response_model=UserOut)
async def me(current_user: UserDB = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.get("/google")
async def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(501, "Google OAuth not configured — set GOOGLE_CLIENT_ID")
    redir = f"{BACKEND_URL}/auth/google/callback"
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redir}&scope=openid%20email%20profile"
        f"&access_type=offline&prompt=consent"
    )


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db_session)):
    """Handle Google OAuth2 callback — exchange code for tokens and redirect to frontend."""
    redir = f"{BACKEND_URL}/auth/google/callback"
    error_redirect = f"{FRONTEND_URL}/login?error=google_auth_failed"

    try:
        # Step 1: Exchange auth code for Google tokens
        async with httpx.AsyncClient(timeout=15.0) as c:
            tr = await c.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redir,
                "grant_type": "authorization_code",
            })

        if tr.status_code != 200:
            logger.error(
                "Google token exchange failed: status=%s body=%s "
                "client_id_set=%s secret_set=%s redirect_uri=%s",
                tr.status_code, tr.text[:500],
                bool(GOOGLE_CLIENT_ID), bool(GOOGLE_CLIENT_SECRET), redir,
            )
            return RedirectResponse(f"{FRONTEND_URL}/login?error=google_token_failed")

        google_tokens = tr.json()
        access_token_google = google_tokens.get("access_token")
        if not access_token_google:
            logger.error("Google token response missing access_token: %s", google_tokens)
            return RedirectResponse(f"{FRONTEND_URL}/login?error=google_token_missing")

        # Step 2: Fetch the user's Google profile
        async with httpx.AsyncClient(timeout=10.0) as c:
            ir = await c.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token_google}"},
            )

        if ir.status_code != 200:
            logger.error("Google userinfo failed: status=%s body=%s", ir.status_code, ir.text[:300])
            return RedirectResponse(f"{FRONTEND_URL}/login?error=google_profile_failed")

        info = ir.json()
        google_id = info.get("id") or info.get("sub")
        email     = info.get("email")

        if not google_id or not email:
            logger.error("Google profile missing required fields: %s", info)
            return RedirectResponse(f"{FRONTEND_URL}/login?error=google_profile_incomplete")

        # Step 3: Upsert user in DB
        user = (await db.execute(select(UserDB).where(UserDB.google_id == google_id))).scalar_one_or_none()
        if not user:
            user = (await db.execute(select(UserDB).where(UserDB.email == email))).scalar_one_or_none()

        if user:
            # Existing user — link Google ID and refresh avatar
            if not user.google_id:
                user.google_id = google_id
            user.avatar_url = info.get("picture") or user.avatar_url
            if not user.name:
                user.name = info.get("name")
            await db.flush()
        else:
            # Automatically register unregistered Google login as patient
            import uuid
            from app.auth.models import UserRole
            from app.database.models import PatientProfileDB

            user = UserDB(
                id=str(uuid.uuid4()),
                email=email,
                google_id=google_id,
                name=info.get("name") or email.split("@")[0],
                avatar_url=info.get("picture"),
                role=UserRole.patient,
                status="approved",
                is_active=True,
            )
            db.add(user)
            await db.flush()

            patient_profile = PatientProfileDB(
                id=str(uuid.uuid4()),
                user_id=user.id,
            )
            db.add(patient_profile)
            await db.flush()
            logger.info("Automatically registered new Google OAuth user as patient: %s", email)

        # Automatically verify and initialize patient records if missing
        role_str = _get_role_str(user)
        if role_str == "patient":
            from app.auth.patient_setup import ensure_patient_records
            await ensure_patient_records(user.id, user.email, user.name, db)
            
            # Update all existing patient records with their Google name
            from app.database.models import PatientRecordDB
            from sqlalchemy import update
            await db.execute(
                update(PatientRecordDB)
                .where(PatientRecordDB.patient_id == user.id)
                .values(patient_name=user.name)
            )

        await db.commit()

        import urllib.parse
        role_str = _get_role_str(user)
        a = create_access_token(user.id, role_str)
        r = create_refresh_token(user.id)
        logger.info("Google OAuth success: user=%s role=%s", email, role_str)

        name_param = urllib.parse.quote(user.name or "")
        avatar_param = urllib.parse.quote(user.avatar_url or "")
        id_param = user.id
        email_param = urllib.parse.quote(user.email)

        return RedirectResponse(
            f"{FRONTEND_URL}/auth/callback?access_token={a}&refresh_token={r}&role={role_str}"
            f"&name={name_param}&avatar_url={avatar_param}&id={id_param}&email={email_param}"
        )

    except Exception as exc:
        logger.exception("Unexpected error in Google OAuth callback: %s", exc)
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_unexpected_error")

