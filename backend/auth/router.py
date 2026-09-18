from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .security import (
    ACCESS_TOKEN_TTL_MIN,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    phone: str
    password: str


class RelativeLoginRequest(BaseModel):
    phone: str
    pin: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    role: Literal["doctor", "nurse", "admin"]
    full_name: str


# Demo accounts according to AGENTS.md and seed
DEMO_USERS = {
    "+998901234567": {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "password": "nazorat123",
        "full_name": "Dr. Bahrom Alimov",
        "role": "doctor",
        "district": "Urganch",
    },
    "901234567": {
        "id": UUID("00000000-0000-0000-0000-000000000001"),
        "password": "nazorat123",
        "full_name": "Dr. Bahrom Alimov",
        "role": "doctor",
        "district": "Urganch",
    },
    "+998901234568": {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "password": "nazorat123",
        "full_name": "Hamshira Dilnoza",
        "role": "nurse",
        "district": "Xiva",
    },
    "901234568": {
        "id": UUID("00000000-0000-0000-0000-000000000002"),
        "password": "nazorat123",
        "full_name": "Hamshira Dilnoza",
        "role": "nurse",
        "district": "Xiva",
    },
}

DEMO_RELATIVE_PIN = "112233"


@router.post("/login", response_model=TokenPair)
async def login(req: LoginRequest):
    user = DEMO_USERS.get(req.phone)
    if not user or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telefon raqami yoki parol noto'g'ri",
        )

    token_data = {
        "sub": str(user["id"]),
        "full_name": user["full_name"],
        "role": user["role"],
        "district": user["district"],
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_TTL_MIN * 60,
        role=user["role"],
        full_name=user["full_name"],
    )


@router.post("/relative/login", response_model=TokenPair)
async def relative_login(req: RelativeLoginRequest):
    if req.pin != DEMO_RELATIVE_PIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN-kod noto'g'ri",
        )

    token_data = {
        "sub": "00000000-0000-0000-0000-000000000099",
        "full_name": "Yaqin qarindosh",
        "role": "doctor",  # Access relative endpoints
        "district": "Urganch",
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_TTL_MIN * 60,
        role="doctor",
        full_name="Yaqin qarindosh",
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(req: RefreshRequest):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Noto'g'ri refresh token")
        
        token_data = {
            "sub": payload["sub"],
            "full_name": payload.get("full_name", ""),
            "role": payload.get("role", "doctor"),
            "district": payload.get("district"),
        }
        return TokenPair(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=ACCESS_TOKEN_TTL_MIN * 60,
            role=payload.get("role", "doctor"),
            full_name=payload.get("full_name", ""),
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token eskirgan yoki noto'g'ri")
