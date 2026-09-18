from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.service import AuthService
from app.core.db import get_session
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    RelativeLoginRequest,
    TokenPair,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair, summary="Clinician login with phone & password")
async def login(
    req: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await service.login(req, client_ip=client_ip, user_agent=user_agent)


@router.post(
    "/relative/login",
    response_model=TokenPair,
    summary="Caregiver / Relative login with PIN code",
)
async def relative_login(
    req: RelativeLoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await service.relative_login(req, client_ip=client_ip, user_agent=user_agent)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh access token with refresh token rotation",
)
async def refresh(
    req: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await service.refresh_tokens(req.refresh_token, client_ip=client_ip, user_agent=user_agent)


@router.post("/logout", response_model=LogoutResponse, summary="Logout and revoke refresh token")
async def logout(
    req: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> LogoutResponse:
    service = AuthService(session)
    await service.revoke_token(req.refresh_token)
    return LogoutResponse(success=True, message="Muvaffaqiyatli chiqildi")


@router.get("/me", response_model=CurrentUser, summary="Get currently authenticated user")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    return current_user
