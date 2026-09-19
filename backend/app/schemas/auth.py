from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import AuthRole


class LoginRequest(BaseModel):
    phone: str = Field(..., description="Phone number e.g. +998901234567")
    password: str = Field(..., min_length=4, description="User password")


class RelativeLoginRequest(BaseModel):
    phone: str = Field(..., description="Relative phone number")
    pin: str = Field(
        ..., min_length=4, max_length=10, description="Access PIN code"
    )


class PatientLoginRequest(BaseModel):
    phone: str = Field(..., description="Patient phone number e.g. +998901234567")
    pin: str = Field(
        ..., min_length=4, max_length=10, description="Patient access PIN code"
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    role: AuthRole
    full_name: str


class CurrentUser(BaseModel):
    id: UUID
    full_name: str
    role: AuthRole
    district: str | None = None
    phone: str | None = None


class LogoutResponse(BaseModel):
    success: bool
    message: str
