"""Validate individual operator requests without stopping the stream."""

from __future__ import annotations

import json
from typing import Any


class QueryError(ValueError):
    def __init__(self, request_id: str | None, reason: str):
        super().__init__(reason)
        self.request_id = request_id
        self.reason = reason


def parse_query(line: str, known_spans: set[str]) -> dict[str, Any]:
    try:
        value = json.loads(line)
    except (ValueError, TypeError):
        raise QueryError(None, "invalid_query") from None
    request_id = value.get("request_id") if isinstance(value, dict) else None
    if not isinstance(request_id, str) or not request_id:
        request_id = None
    if not isinstance(value, dict) or request_id is None:
        raise QueryError(request_id, "invalid_query")
    if value.get("type") == "span":
        span_id = value.get("span_id")
        if not isinstance(span_id, str) or not span_id:
            raise QueryError(request_id, "invalid_query")
        if span_id not in known_spans:
            raise QueryError(request_id, "unknown_span")
        return {"request_id": request_id, "type": "span", "span_id": span_id}
    if value.get("type") == "top":
        limit = value.get("limit")
        if type(limit) is not int or not (1 <= limit <= 50):
            raise QueryError(request_id, "invalid_query")
        return {"request_id": request_id, "type": "top", "limit": limit}
    raise QueryError(request_id, "invalid_query")

