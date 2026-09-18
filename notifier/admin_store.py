from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("nazorat.notifier.admin_store")

SUPER_ADMIN_ID: int = int(os.getenv("SUPER_ADMIN_ID", "6956456422"))

DATA_DIR = Path(__file__).resolve().parent
ADMINS_FILE = DATA_DIR / "admins.json"


def _default_data() -> dict[str, Any]:
    return {
        "super_admin_id": SUPER_ADMIN_ID,
        "admins": {
            str(SUPER_ADMIN_ID): {
                "id": SUPER_ADMIN_ID,
                "name": "Super Admin",
                "role": "super_admin",
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    }


def load_admins_data() -> dict[str, Any]:
    """Load admins from JSON file or initialize with default super admin."""
    if not ADMINS_FILE.exists():
        data = _default_data()
        save_admins_data(data)
        return data

    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure super admin is always present
            str_super_id = str(SUPER_ADMIN_ID)
            if str_super_id not in data.get("admins", {}):
                data.setdefault("admins", {})[str_super_id] = {
                    "id": SUPER_ADMIN_ID,
                    "name": "Super Admin",
                    "role": "super_admin",
                    "added_at": datetime.now(timezone.utc).isoformat(),
                }
                save_admins_data(data)
            return data
    except Exception as err:
        logger.error("Failed to read admins file %s: %s", ADMINS_FILE, err)
        return _default_data()


def save_admins_data(data: dict[str, Any]) -> None:
    """Save admins data to JSON file atomically."""
    try:
        tmp_file = ADMINS_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(ADMINS_FILE)
    except Exception as err:
        logger.error("Failed to write admins file %s: %s", ADMINS_FILE, err)


def is_super_admin(user_id: int | str) -> bool:
    """Check if the given Telegram user ID is the Super Admin."""
    try:
        return int(user_id) == SUPER_ADMIN_ID
    except (ValueError, TypeError):
        return False


def is_admin(user_id: int | str) -> bool:
    """Check if the given Telegram user ID is either Super Admin or an appointed Admin."""
    try:
        uid = int(user_id)
        if uid == SUPER_ADMIN_ID:
            return True
        data = load_admins_data()
        return str(uid) in data.get("admins", {})
    except (ValueError, TypeError):
        return False


def get_all_admins() -> list[dict[str, Any]]:
    """Return a list of all administrators."""
    data = load_admins_data()
    return list(data.get("admins", {}).values())


def add_admin(user_id: int | str, name: str, role: str = "admin") -> tuple[bool, str]:
    """Add a new administrator."""
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return False, "Noto'g'ri Telegram ID formati (faqat raqamlar bo'lishi kerak)."

    data = load_admins_data()
    admins = data.setdefault("admins", {})

    str_uid = str(uid)
    if str_uid in admins and admins[str_uid].get("role") == "super_admin":
        return False, "Foydalanuvchi allaqachon Super Admin hisoblanadi."

    is_update = str_uid in admins
    admins[str_uid] = {
        "id": uid,
        "name": name.strip() or f"Admin_{uid}",
        "role": role,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    save_admins_data(data)

    action_text = "tahrirlandi" if is_update else "muvaffaqiyatli qo'shildi"
    return True, f"Administrator {action_text}: <b>{admins[str_uid]['name']}</b> (ID: <code>{uid}</code>)"


def remove_admin(user_id: int | str) -> tuple[bool, str]:
    """Remove an administrator. Super Admin cannot be removed."""
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return False, "Noto'g'ri Telegram ID formati."

    if uid == SUPER_ADMIN_ID:
        return False, "Super Adminni o'chirib bo'lmaydi."

    data = load_admins_data()
    admins = data.get("admins", {})

    str_uid = str(uid)
    if str_uid not in admins:
        return False, f"ID <code>{uid}</code> ga ega administrator topilmadi."

    deleted_name = admins[str_uid].get("name", "Noma'lum")
    del admins[str_uid]
    save_admins_data(data)

    return True, f"Administrator o'chirildi: <b>{deleted_name}</b> (ID: <code>{uid}</code>)"
