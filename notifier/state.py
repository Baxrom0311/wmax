"""Local delivery ledger for the notifier.

Telegram has no idempotency key, so the notifier must remember what it already
sent. The `notifications` table records *that* a patient was notified (used for
the 6-hour cooldown), but not which task reminder or which individual alert row
has been handled — and adding columns would mean a schema reset.

This file fills that gap. It is intentionally local state: docker-compose runs a
single notifier container, and a duplicate replica would double-message
clinicians regardless of where the ledger lives.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger("wmax.notifier.state")

STATE_FILE = Path(
    os.getenv("NOTIFIER_STATE_FILE", str(Path(__file__).resolve().parent / "sent_state.json"))
)
# Keep the ledger from growing without bound; entries far older than any
# cooldown window carry no information.
MAX_ENTRIES = 5000

_lock = threading.Lock()


def _load() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"sent": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data.get("sent"), dict):
                return {"sent": {}}
            return data
    except Exception as err:
        logger.error("Could not read notifier state %s: %s", STATE_FILE, err)
        return {"sent": {}}


def _save(data: dict[str, Any]) -> None:
    try:
        tmp = STATE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, STATE_FILE)
    except Exception as err:
        logger.error("Could not persist notifier state %s: %s", STATE_FILE, err)


def already_sent(key: str) -> bool:
    """True when `key` has already been delivered."""
    with _lock:
        return key in _load()["sent"]


def mark_sent(key: str, timestamp: str) -> None:
    """Records `key` as delivered, trimming the oldest entries when full."""
    with _lock:
        data = _load()
        sent: dict[str, str] = data["sent"]
        sent[key] = timestamp

        if len(sent) > MAX_ENTRIES:
            for old_key in sorted(sent, key=lambda k: sent[k])[: len(sent) - MAX_ENTRIES]:
                del sent[old_key]

        _save(data)
