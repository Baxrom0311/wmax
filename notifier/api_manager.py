from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nazorat.notifier.api_manager")

DATA_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip(),
    "system_mode": "hybrid",  # 'hybrid' | 'offline' | 'strict'
    "thresholds": {
        "spo2_min": 90.0,
        "hr_max": 100.0,
        "temp_max": 37.8,
        "rr_max": 24.0,
    },
}

SUPPORTED_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


def load_settings() -> dict[str, Any]:
    """Load settings from JSON or initialize with defaults from environment."""
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as err:
        logger.error("Failed to read settings file %s: %s", SETTINGS_FILE, err)
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    """Save settings atomically to JSON file."""
    try:
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        tmp.replace(SETTINGS_FILE)
    except Exception as err:
        logger.error("Failed to write settings file %s: %s", SETTINGS_FILE, err)


def get_all_api_keys() -> list[dict[str, Any]]:
    """Return all stored API keys with their IDs, masked views, and active status."""
    settings = load_settings()
    keys: list[dict[str, Any]] = settings.get("api_keys", [])

    # If api_keys is empty or missing, bootstrap from settings and .env
    if not keys:
        keys = []
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        custom_key = settings.get("gemini_api_key", "").strip()

        if env_key:
            keys.append({
                "id": "key_1",
                "name": "API Kalit #1 (.env)",
                "key": env_key,
                "is_active": True,
            })
        if custom_key and custom_key != env_key:
            keys.append({
                "id": f"key_{len(keys)+1}",
                "name": f"API Kalit #{len(keys)+1}",
                "key": custom_key,
                "is_active": False if keys else True,
            })

        settings["api_keys"] = keys
        if keys:
            active_k = next((k for k in keys if k.get("is_active")), keys[0])
            settings["gemini_api_key"] = active_k["key"]
            settings["active_key_id"] = active_k["id"]
        save_settings(settings)

    return keys


def get_active_api_key() -> str:
    """Return currently active Gemini API key."""
    keys = get_all_api_keys()
    for k in keys:
        if k.get("is_active"):
            return k["key"]
    if keys:
        return keys[0]["key"]
    return os.getenv("GEMINI_API_KEY", "").strip()


def mask_key(key: str) -> str:
    """Return masked API key representation for secure admin display."""
    if not key:
        return "Mavjud emas (O'rnatilmagan ❌)"
    if len(key) <= 12:
        return f"{key[:3]}...{key[-3:]}"
    return f"{key[:8]}...{key[-6:]}"


def add_api_key(new_key: str, name: str | None = None) -> tuple[bool, str, dict]:
    """Add a new API key to the pool and set it as active."""
    new_key = new_key.strip()
    if not new_key:
        return False, "Kalit bo'sh bo'lishi mumkin emas.", {}

    settings = load_settings()
    keys = get_all_api_keys()

    # Check if key already exists
    for k in keys:
        if k["key"] == new_key:
            for item in keys:
                item["is_active"] = (item["id"] == k["id"])
            settings["api_keys"] = keys
            settings["gemini_api_key"] = new_key
            settings["active_key_id"] = k["id"]
            save_settings(settings)
            return True, f"Ushbu kalit allaqachon mavjud edi ({k.get('name')}) va faollashtirildi.", k

    new_id = f"key_{int(time.time())}"
    key_name = name or f"API Kalit #{len(keys) + 1}"

    for item in keys:
        item["is_active"] = False

    new_item = {
        "id": new_id,
        "name": key_name,
        "key": new_key,
        "is_active": True,
    }
    keys.append(new_item)

    settings["api_keys"] = keys
    settings["gemini_api_key"] = new_key
    settings["active_key_id"] = new_id
    save_settings(settings)
    return True, f"Yangi kalit muvaffaqiyatli qo'shildi ({key_name}).", new_item


def set_active_api_key(key_id: str) -> tuple[bool, str]:
    """Select which key is active from the pool."""
    settings = load_settings()
    keys = get_all_api_keys()

    found = None
    for k in keys:
        if k["id"] == key_id:
            found = k
            k["is_active"] = True
        else:
            k["is_active"] = False

    if not found:
        return False, "Bunday kalit topilmadi."

    settings["api_keys"] = keys
    settings["gemini_api_key"] = found["key"]
    settings["active_key_id"] = found["id"]
    save_settings(settings)
    return True, f"Faol API kalit o'zgartirildi: <b>{mask_key(found['key'])}</b>"


def delete_api_key_by_id(key_id: str) -> tuple[bool, str]:
    """Delete a specific API key by its ID from the pool."""
    settings = load_settings()
    keys = get_all_api_keys()

    target = None
    remaining = []
    for k in keys:
        if k["id"] == key_id:
            target = k
        else:
            remaining.append(k)

    if not target:
        return False, "O'chirish uchun bunday kalit topilmadi."

    # If the deleted key was active, activate the first remaining key
    if target.get("is_active") and remaining:
        remaining[0]["is_active"] = True
        settings["gemini_api_key"] = remaining[0]["key"]
        settings["active_key_id"] = remaining[0]["id"]
    elif not remaining:
        settings["gemini_api_key"] = ""
        settings["active_key_id"] = None

    settings["api_keys"] = remaining
    save_settings(settings)
    return True, f"API kalit muvaffaqiyatli o'chirildi: <code>{mask_key(target['key'])}</code>"


def set_api_key(new_key: str) -> None:
    """Set and persist new Gemini API key (backward compatible)."""
    add_api_key(new_key)


def delete_api_key() -> None:
    """Delete the active API key (backward compatible)."""
    keys = get_all_api_keys()
    if keys:
        delete_api_key_by_id(keys[0]["id"])


def get_model() -> str:
    """Get active Gemini model name."""
    settings = load_settings()
    return settings.get("gemini_model", "gemini-3.5-flash-lite")


def set_model(model_name: str) -> bool:
    """Set active Gemini model name."""
    settings = load_settings()
    settings["gemini_model"] = model_name.strip()
    save_settings(settings)
    return True


def get_system_mode() -> str:
    """Get system AI mode: hybrid, offline, or strict."""
    settings = load_settings()
    return settings.get("system_mode", "hybrid")


def set_system_mode(mode: str) -> None:
    """Set system AI mode."""
    settings = load_settings()
    settings["system_mode"] = mode.strip()
    save_settings(settings)


def get_thresholds() -> dict[str, float]:
    """Get clinical thresholds."""
    settings = load_settings()
    return settings.get("thresholds", DEFAULT_SETTINGS["thresholds"])


def set_threshold(param: str, val: float) -> tuple[bool, str]:
    """Update a specific clinical threshold."""
    settings = load_settings()
    thresh = settings.setdefault("thresholds", dict(DEFAULT_SETTINGS["thresholds"]))

    param_map = {
        "spo2": "spo2_min",
        "spo2_min": "spo2_min",
        "hr": "hr_max",
        "hr_max": "hr_max",
        "puls": "hr_max",
        "temp": "temp_max",
        "temp_max": "temp_max",
        "harorat": "temp_max",
        "rr": "rr_max",
        "rr_max": "rr_max",
        "nafas": "rr_max",
    }
    target = param_map.get(param.lower())
    if not target:
        return False, f"Noma'lum parametr: <code>{param}</code>. Mavjud parametrlar: spo2, hr, temp, rr."

    thresh[target] = float(val)
    save_settings(settings)
    return True, f"Klinik ostona yangilandi: <b>{target} = {val}</b>"


async def test_gemini_api(api_key: str | None = None, model: str | None = None) -> tuple[bool, float, str]:
    """
    Test Gemini API connectivity with a lightweight prompt.
    Returns: (success: bool, latency_sec: float, message: str)
    """
    key = api_key or get_active_api_key()
    if not key:
        return False, 0.0, "API kalit kiritilmagan."

    target_model = model or get_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [{"text": "Ping"}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 5,
            "temperature": 0.0,
        },
    }

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                params={"key": key},
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            latency = round(time.perf_counter() - t0, 2)
            if resp.status_code == 200:
                return True, latency, f"Ulanish muvaffaqiyatli! ({latency}s)"
            else:
                error_msg = resp.text
                try:
                    err_json = resp.json()
                    error_msg = err_json.get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                return False, latency, f"HTTP {resp.status_code}: {error_msg[:120]}"
    except httpx.TimeoutException:
        return False, 10.0, "Ulanish vaqti tugadi (Timeout: 10s)."
    except Exception as err:
        latency = round(time.perf_counter() - t0, 2)
        return False, latency, f"Ulanishda xatolik: {str(err)[:120]}"
