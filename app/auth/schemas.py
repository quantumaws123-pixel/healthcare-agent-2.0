"""Auth schemas — register, login, tokens."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=8)
    name:     Optional[str] = None
    # Only "patient" and "doctor" are allowed via public signup.
    # "admin" is explicitly excluded — admins are created by other admins only.
    role:     Literal["doctor", "patient"] = "patient"


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class UserOut(BaseModel):
    id:         str
    email:      str
    name:       Optional[str] = None
    avatar_url: Optional[str] = None
    role:       str
    status:     str = "approved"   # default so null DB values don't cause validation errors
    is_active:  bool = True

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          UserOut


class RefreshRequest(BaseModel):
    refresh_token: str
