"""Helpers for IANA timezone validation and resolution."""

from __future__ import annotations

from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_IANA_TIMEZONE = "Europe/Madrid"


def validate_iana_timezone(value: str) -> str:
    name = (value or "").strip()
    if not name:
        raise ValueError("Zona horaria vacía")
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Zona horaria IANA no válida: {name}") from exc
    return name


def resolve_effective_timezone(
    query_tz: Optional[str],
    stored_tz: Optional[str],
) -> str:
    """
    query_tz wins when provided (non-empty); else stored_tz; else default.
    """
    if query_tz is not None and str(query_tz).strip():
        return validate_iana_timezone(query_tz)
    if stored_tz is not None and str(stored_tz).strip():
        return validate_iana_timezone(stored_tz)
    return DEFAULT_IANA_TIMEZONE
