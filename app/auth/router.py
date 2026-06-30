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

    # Normalise role to a plain string (the DB column is VARCHAR, not an enum type)
    role_str = body.role if isinstance(body.role, str) else str(body.role)

    user = UserDB(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        role=role_str,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    # commit so the row is actually persisted (flush alone only buffers it)
    await db.commit()
    logger.info("Registered user %s role=%s", user.email, user.role)
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
    redir = f"{BACKEND_URL}/auth/google/callback"
    async with httpx.AsyncClient() as c:
        tr = await c.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redir, "grant_type": "authorization_code"})
    if tr.status_code != 200:
        raise HTTPException(400, "Google token exchange failed")
    async with httpx.AsyncClient() as c:
        ir = await c.get("https://www.googleapis.com/oauth2/v2/userinfo",
                         headers={"Authorization": f"Bearer {tr.json()['access_token']}"})
    if ir.status_code != 200:
        raise HTTPException(400, "Failed to fetch Google profile")
    info = ir.json()
    user = (await db.execute(select(UserDB).where(UserDB.google_id == info["id"]))).scalar_one_or_none()
    if not user:
        user = (await db.execute(select(UserDB).where(UserDB.email == info["email"]))).scalar_one_or_none()
    if user:
        user.google_id = user.google_id or info["id"]
        user.avatar_url = info.get("picture")
        await db.flush()
    else:
        user = UserDB(id=str(uuid.uuid4()), email=info["email"],
                      google_id=info["id"], name=info.get("name"),
                      avatar_url=info.get("picture"), role="patient")
        db.add(user)
        await db.flush()
        await db.refresh(user)
    await db.commit()
    role_str = _get_role_str(user)
    a = create_access_token(user.id, role_str)
    r = create_refresh_token(user.id)
    return RedirectResponse(
        f"{FRONTEND_URL}/auth/callback?access_token={a}&refresh_token={r}&role={role_str}"
    )
