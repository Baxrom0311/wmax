from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_principal
from app.auth.service import AuthService
from app.core.db import get_session
from app.core.rate_limit import enforce_login_rate_limit, login_limiter
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    LogoutResponse,
    PatientLoginRequest,
    RequestCodeRequest,
    RequestCodeResponse,
    RefreshRequest,
    RelativeLoginRequest,
    TokenPair,
    VerifyCodeRequest,
)
from app.schemas.relative import RelativeLoginResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


@router.post("/request-code", response_model=RequestCodeResponse, summary="Request SMS login code")
async def request_code(
    req: RequestCodeRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RequestCodeResponse:
    client_ip = _client_ip(request)
    rate_keys = [f"sms:ip:{client_ip}", f"sms:phone:{req.phone.strip()}"]
    for key in rate_keys:
        enforce_login_rate_limit(key)
    service = AuthService(session)
    expires_in, dev_code = await service.request_code(req.phone)
    return RequestCodeResponse(expires_in=expires_in, dev_code=dev_code)


@router.post("/verify-code", response_model=TokenPair, summary="Verify SMS code and issue tokens")
async def verify_code(
    req: VerifyCodeRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    client_ip = _client_ip(request)
    rate_keys = [f"sms-verify:ip:{client_ip}", f"sms-verify:phone:{req.phone.strip()}"]
    for key in rate_keys:
        enforce_login_rate_limit(key)
    service = AuthService(session)
    tokens = await service.verify_code(req.phone, req.code)
    for key in rate_keys:
        login_limiter.reset(key)
    return tokens


@router.post("/login", response_model=TokenPair, summary="Clinician login with phone & password")
async def login(
    req: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    client_ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Throttle per IP *and* per account so neither a single host nor a
    # distributed attempt can grind through the password space.
    rate_keys = [f"login:ip:{client_ip}", f"login:phone:{req.phone.strip()}"]
    for key in rate_keys:
        enforce_login_rate_limit(key)

    tokens = await service.login(req, client_ip=client_ip, user_agent=user_agent)
    for key in rate_keys:
        login_limiter.reset(key)
    return tokens


@router.post(
    "/relative/login",
    response_model=RelativeLoginResponse,
    summary="Caregiver / Relative login with PIN code",
)
async def relative_login(
    req: RelativeLoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RelativeLoginResponse:
    service = AuthService(session)
    client_ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    # A 6-digit PIN is only safe behind a hard attempt limit.
    rate_keys = [f"relative:ip:{client_ip}", f"relative:phone:{req.phone.strip()}"]
    for key in rate_keys:
        enforce_login_rate_limit(key)

    tokens = await service.relative_login(
        req, client_ip=client_ip, user_agent=user_agent
    )
    for key in rate_keys:
        login_limiter.reset(key)
    return tokens


@router.post(
    "/patient/login",
    response_model=TokenPair,
    summary="Patient login with phone & PIN",
)
async def patient_login(
    req: PatientLoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    service = AuthService(session)
    client_ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    rate_keys = [f"patient:ip:{client_ip}", f"patient:phone:{req.phone.strip()}"]
    for key in rate_keys:
        enforce_login_rate_limit(key)

    tokens = await service.patient_login(
        req, client_ip=client_ip, user_agent=user_agent
    )
    for key in rate_keys:
        login_limiter.reset(key)
    return tokens


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
    client_ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")
    return await service.refresh_tokens(
        req.refresh_token, client_ip=client_ip, user_agent=user_agent
    )


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
    current_user: CurrentUser = Depends(get_current_principal),
) -> CurrentUser:
    return current_user
