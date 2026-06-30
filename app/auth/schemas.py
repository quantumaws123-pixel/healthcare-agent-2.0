"""Pydantic schemas for auth endpoints."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=8)
    name:     Optional[str] = None
    role:     Literal["admin", "doctor", "patient"] = "patient"


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class UserOut(BaseModel):
    id:         str
    email:      str
    name:       Optional[str]
    avatar_url: Optional[str]
    role:       str
    is_active:  bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          UserOut


class RefreshRequest(BaseModel):
    refresh_token: str
