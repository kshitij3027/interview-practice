from __future__ import annotations

from datetime import datetime, timezone

SLOT_MINUTES = 15
SLOT_SECONDS = SLOT_MINUTES * 60


def parse_utc(value: str, *, field: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError(f"{field} must be non-empty")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include timezone information")
    return parsed.astimezone(timezone.utc)


def require_aligned(value: datetime, *, field: str) -> None:
    if value.second != 0 or value.microsecond != 0 or value.minute % SLOT_MINUTES != 0:
        raise ValueError(f"{field} must align to a 15-minute boundary")


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
