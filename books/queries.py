"""Independent quote-query parsing and per-record recovery."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .catalog import valid_id


@dataclass(frozen=True)
class QuoteRequest:
    request_id: str
    market: str
    as_of_ms: int
    action: str
    lots: int


def invalid_request(raw: object) -> dict:
    request_id = raw.get("request_id") if isinstance(raw, dict) else None
    if not valid_id(request_id):
        request_id = None
    return {"request_id": request_id, "status": "invalid", "reason": "invalid_query"}


def parse_query(raw: object) -> QuoteRequest | dict:
    invalid = invalid_request(raw)
    if not isinstance(raw, dict):
        return invalid
    keys = ("request_id", "market")
    if any(not valid_id(raw.get(key)) for key in keys):
        return invalid
    time, lots = raw.get("as_of_ms"), raw.get("lots")
    if (type(time) is not int or not 0 <= time <= 10**12 or
            type(lots) is not int or not 1 <= lots <= 10**9 or
            raw.get("action") not in ("buy", "sell")):
        return invalid
    return QuoteRequest(raw["request_id"], raw["market"], time, raw["action"], lots)


def read_queries(path: str | Path) -> Iterator[QuoteRequest | dict]:
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            try:
                raw = json.loads(line)
            except (ValueError, UnicodeError):
                yield invalid_request(None)
                continue
            yield parse_query(raw)
