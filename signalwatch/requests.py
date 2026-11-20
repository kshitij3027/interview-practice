"""Input request validation; each JSONL line is independent."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_TENANT_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")


@dataclass(frozen=True)
class Event:
    event_id: str
    tenant_id: str
    text: str
    limit: int


def parse_event(line: str) -> Event | dict:
    try:
        raw = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return {"event_id": None, "status": "invalid", "reason": "invalid_event"}
    event_id = None
    if isinstance(raw, dict):
        value = raw.get("event_id")
        if isinstance(value, str) and _REQUEST_ID.fullmatch(value):
            event_id = value
    invalid = {"event_id": event_id, "status": "invalid", "reason": "invalid_event"}
    if not isinstance(raw, dict) or event_id is None:
        return invalid
    tenant = raw.get("tenant_id")
    content = raw.get("text")
    limit = raw.get("limit")
    if not isinstance(tenant, str) or not _TENANT_ID.fullmatch(tenant):
        return invalid
    if not isinstance(content, str) or len(content) > 20_000 or any(not 32 <= ord(c) <= 126 for c in content):
        return invalid
    if type(limit) is not int or not 0 <= limit <= 10:
        return invalid
    return Event(event_id, tenant, content, limit)
