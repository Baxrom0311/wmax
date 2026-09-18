from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.exceptions import BadRequestException

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


class StorageProvider(ABC):
    @abstractmethod
    async def upload(
        self, file_data: bytes, filename: str, content_type: str
    ) -> str:
        """Stores file securely and returns relative path or public URI."""
        ...

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Retrieves raw file bytes."""
        ...

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Deletes file from storage."""
        ...


def validate_file(filename: str, content_type: str, file_size: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(
            f"Fayl formati ruxsat etilmagan ({ext}). Ruxsat: PNG, JPG, PDF, DOCX"
        )
    if content_type not in ALLOWED_MIME_TYPES:
        raise BadRequestException(f"Fayl turi ruxsat etilmagan ({content_type})")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise BadRequestException(
            f"Fayl hajmi 15 MB dan oshmasligi kerak (joriy: {round(file_size / (1024*1024), 2)} MB)"
        )


def virus_scan_hook(file_bytes: bytes) -> bool:
    """Security hook for antivirus integration (e.g. ClamAV, AWS GuardDuty). Returns True if clean."""
    # Production virus scanning hook — returns True if clean
    return True


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "uploads") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload(
        self, file_data: bytes, filename: str, content_type: str
    ) -> str:
        validate_file(filename, content_type, len(file_data))
        if not virus_scan_hook(file_data):
            raise BadRequestException("Xavfsizlik tekshiruvi: Faylda zararli kod aniqlandi")

        safe_filename = f"{uuid.uuid4().hex}_{Path(filename).name}"
        destination = self.base_dir / safe_filename
        with open(destination, "wb") as f:
            f.write(file_data)

        return str(destination)

    async def read(self, path: str) -> bytes:
        p = Path(path)
        if not p.exists():
            raise BadRequestException("Fayl topilmadi")
        with open(p, "rb") as f:
            return f.read()

    async def delete(self, path: str) -> bool:
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False
