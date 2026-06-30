"""JWT creation and verification utilities."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

SECRET_KEY      = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING")
ALGORITHM       = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_EXPIRE   = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES",  "60"))
REFRESH_EXPIRE  = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS",    "30"))


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE)
    return jwt.encode(
        {"sub": user_id, "role": role, "type": "access", "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE)
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
