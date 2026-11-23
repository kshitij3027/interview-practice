"""Query parsing. Invalid physical lines are independent of subsequent lines."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z", re.ASCII)
_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)


@dataclass(frozen=True)
class Query:
    request_id: str
    tenant_id: str
    target_id: str
    deadline_min: int


def parse_query(line: str) -> tuple[Query | None, dict | None]:
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None, {"request_id": None, "status": "invalid", "reason": "invalid_query"}
    request_id = data.get("request_id") if isinstance(data, dict) else None
    good_id = isinstance(request_id, str) and bool(_REQUEST_ID.fullmatch(request_id))
    retained = request_id if good_id else None
    if (
        not isinstance(data, dict)
        or not good_id
        or not isinstance(data.get("tenant_id"), str)
        or not _ID.fullmatch(data["tenant_id"])
        or not isinstance(data.get("target_id"), str)
        or not _ID.fullmatch(data["target_id"])
        or type(data.get("deadline_min")) is not int
        or not 0 <= data["deadline_min"] <= 1_000_000_000_000_000
    ):
        return None, {"request_id": retained, "status": "invalid", "reason": "invalid_query"}
    return Query(request_id, data["tenant_id"], data["target_id"], data["deadline_min"]), None
