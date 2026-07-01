"""FastAPI auth dependencies — get_current_user, require_role."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import get_db_session
from app.auth.jwt import decode_token
from app.auth.models import UserDB, UserRole

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db_session),
) -> UserDB:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        if user.status == "pending":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is pending administrator approval")
        if user.status == "rejected":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your registration request has been rejected")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been deactivated. Please contact your administrator.")

    return user


def require_role(*roles: UserRole):
    """Dependency factory — checks that the current user has one of the given roles.

    Works whether user.role is a plain string (VARCHAR column) or a UserRole enum.
    """
    # Normalise the allowed roles to plain strings for comparison
    allowed = {r.value if hasattr(r, "value") else str(r) for r in roles}

    async def _check(current_user: UserDB = Depends(get_current_user)) -> UserDB:
        # Normalise user's role to a plain string as well
        user_role = current_user.role
        if hasattr(user_role, "value"):
            user_role = user_role.value
        else:
            user_role = str(user_role)

        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed)}",
            )
        return current_user

    return _check
