"""User ORM model — stored in the same DB as patient data."""
import enum
from sqlalchemy import (
    Column,
    String,
    Boolean,
    TIMESTAMP,
    Enum,
)
from sqlalchemy.sql import func
from app.database.models import Base


class UserRole(str, enum.Enum):
    admin   = "admin"
    doctor  = "doctor"
    patient = "patient"


class UserDB(Base):
    __tablename__ = "users"

    id              = Column(String(50),  primary_key=True)
    email           = Column(String(255), unique=True,  nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    google_id       = Column(String(255), unique=True,  nullable=True, index=True)
    name            = Column(String(100), nullable=True)
    avatar_url      = Column(String(500), nullable=True)
    role            = Column(Enum(UserRole, name="userrole"), nullable=False, default=UserRole.patient)
    is_active       = Column(Boolean,     default=True,  nullable=False)
    created_at      = Column(TIMESTAMP,   server_default=func.now(), nullable=False)
    updated_at      = Column(TIMESTAMP,   server_default=func.now(), onupdate=func.now(), nullable=False)
