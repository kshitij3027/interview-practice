"""Validate one operator request without abandoning later records."""
from __future__ import annotations

import json
from typing import Any
from .data import instant


class QueryError(ValueError):
    def __init__(self, request_id: str | None, reason: str):
        super().__init__(reason)
        self.request_id = request_id
        self.reason = reason


def parse_request(line: str, known_tickets: set[str]) -> dict[str, Any]:
    try:
        record = json.loads(line)
    except (ValueError, TypeError):
        raise QueryError(None, "invalid_query") from None
    request_id = record.get("request_id") if isinstance(record, dict) else None
    request_id = request_id if isinstance(request_id, str) and request_id else None
    if not isinstance(record, dict) or request_id is None:
        raise QueryError(request_id, "invalid_query")
    kind = record.get("type")
    try:
        as_of = instant(record.get("as_of"))
    except ValueError:
        raise QueryError(request_id, "invalid_query") from None
    if kind == "ticket":
        ticket_id = record.get("ticket_id")
        if not isinstance(ticket_id, str) or not ticket_id:
            raise QueryError(request_id, "invalid_query")
        if ticket_id not in known_tickets:
            raise QueryError(request_id, "unknown_ticket")
        return {"request_id": request_id, "type": kind, "as_of": as_of, "ticket_id": ticket_id}
    if kind == "overdue":
        limit = record.get("limit")
        if type(limit) is not int or not 1 <= limit <= 50:
            raise QueryError(request_id, "invalid_query")
        return {"request_id": request_id, "type": kind, "as_of": as_of, "limit": limit}
    raise QueryError(request_id, "invalid_query")
