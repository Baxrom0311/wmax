from __future__ import annotations

import logging
import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger("wmax.auth.device")

INGEST_KEY_HEADER = "X-Ingest-Key"


async def verify_ingest_key(
    x_ingest_key: str | None = Header(default=None, alias=INGEST_KEY_HEADER),
) -> None:
    """Authenticates a wearable companion app uploading physiological readings.

    Without this, anyone who can reach the API can post readings for any
    patient_id — fabricating red alerts or masking a real deterioration.

    The key is shared by all devices; it authenticates the fleet, not the
    individual watch. Per-device credentials are the next step, but a fleet
    secret already closes the open-to-the-internet hole.
    """
    expected = settings.INGEST_API_KEY

    if not expected:
        # Production boot refuses to start without a key (see
        # validate_production_settings), so this branch is dev/test only.
        logger.warning(
            "INGEST_API_KEY is not configured — accepting unauthenticated ingest. "
            "This is only permitted outside production."
        )
        return

    if not x_ingest_key or not secrets.compare_digest(x_ingest_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Qurilma kaliti yaroqsiz",
        )
