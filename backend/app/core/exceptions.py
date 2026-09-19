from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class BaseAppException(HTTPException):
    """Base exception for all application errors following standardized schema."""

    def __init__(
        self,
        status_code: int,
        message: str,
        code: str = "ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.code = code
        self.details = details or {}


class NotFoundException(BaseAppException):
    def __init__(
        self,
        resource: str | None = None,
        identifier: Any = None,
        message: str | None = None,
        resource_name: str | None = None,
    ):
        _resource = resource or resource_name or "Resource"
        _msg = message or f"{_resource} topilmadi" + (f": {identifier}" if identifier else "")
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=_msg,
            code="NOT_FOUND",
            details={"resource": _resource, "identifier": str(identifier) if identifier else None},
        )


class AuthenticationException(BaseAppException):
    def __init__(self, message: str = "Autentifikatsiya muvaffaqiyatsiz"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            code="AUTHENTICATION_FAILED",
        )


class ValidationAppException(BaseAppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            code="VALIDATION_ERROR",
            details=details,
        )


ValidationException = ValidationAppException


class UnauthorizedException(BaseAppException):
    def __init__(self, message: str = "Autentifikatsiya talab qilinadi"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            code="UNAUTHORIZED",
        )


class ForbiddenException(BaseAppException):
    def __init__(self, message: str = "Ushbu amalni bajarish uchun ruxsat yo'q"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            code="FORBIDDEN",
        )


class ConflictException(BaseAppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            code="CONFLICT",
        )


class AIProviderException(BaseAppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=f"AI tahlil xizmatida xatolik: {message}",
            code="AI_PROVIDER_ERROR",
            details=details,
        )


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "code": exc.code,
            "details": exc.details,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | ValidationError
) -> JSONResponse:
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        errors.append({"field": loc, "issue": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Kiritilgan ma'lumotlar formati noto'g'ri",
            "code": "VALIDATION_ERROR",
            "details": {"errors": errors},
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled server exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Ichki server xatoligi yuz berdi. Iltimos qaytadan urinib ko'ring.",
            "code": "INTERNAL_SERVER_ERROR",
            "details": {},
        },
    )
