"""Validated immutable input schema for MirrorTrace. Standard library only."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

_ID = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
_MARKET = re.compile(r"[A-Z]{2,4}\Z")
_HEX = re.compile(r"[0-9A-Fa-f]{32}\Z")
_FIELDS = ["listing_id", "market", "seller_id", "first_seen_ms", "last_seen_ms", "fingerprint_hex", "risk_score"]


@dataclass(frozen=True)
class Listing:
    listing_id: str
    market: str
    seller_id: str
    first_seen_ms: int
    last_seen_ms: int | None
    fingerprint: int
    risk_score: int


@dataclass(frozen=True)
class Query:
    request_id: str
    market: str
    seller_id: str
    as_of_ms: int
    fingerprint: int
    max_bit_errors: int
    limit: int
    min_risk_score: int


def _identifier(value: object, name: str, pattern: re.Pattern[str] = _ID) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError(f"invalid {name}")
    return value


def _integer(value: object, name: str, lo: int, hi: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"invalid {name}")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        number = int(value)
    else:
        raise ValueError(f"invalid {name}")
    if number < lo or number > hi:
        raise ValueError(f"out-of-range {name}")
    return number


def _fingerprint(value: object) -> int:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError("invalid fingerprint_hex")
    return int(value, 16)


def load_listings(path: str | Path) -> list[Listing]:
    by_id: dict[str, Listing] = {}
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != _FIELDS:
            raise ValueError("unexpected listing CSV header")
        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("wrong field count")
                first = _integer(row["first_seen_ms"], "first_seen_ms", 0, 10**12)
                last_raw = row["last_seen_ms"]
                last = None if last_raw == "*" else _integer(last_raw, "last_seen_ms", 0, 10**12)
                if last is not None and last <= first:
                    raise ValueError("last_seen_ms must be after first_seen_ms")
                entry = Listing(
                    _identifier(row["listing_id"], "listing_id"),
                    _identifier(row["market"], "market", _MARKET),
                    _identifier(row["seller_id"], "seller_id"),
                    first, last, _fingerprint(row["fingerprint_hex"]),
                    _integer(row["risk_score"], "risk_score", 0, 100),
                )
                previous = by_id.setdefault(entry.listing_id, entry)
                if previous != entry:
                    raise ValueError("conflicting listing_id replay")
            except ValueError as exc:
                raise ValueError(f"listings row {row_number}: {exc}") from exc
    return list(by_id.values())


def parse_query(obj: object) -> Query:
    if not isinstance(obj, dict):
        raise ValueError("request must be a JSON object")
    # JSON integer syntax is required here; a stringified number is not accepted.
    for key in ("as_of_ms", "max_bit_errors", "limit", "min_risk_score"):
        if not isinstance(obj.get(key), int) or isinstance(obj[key], bool):
            raise ValueError(f"invalid {key}")
    return Query(
        _identifier(obj.get("request_id"), "request_id"),
        _identifier(obj.get("market"), "market", _MARKET),
        _identifier(obj.get("seller_id"), "seller_id"),
        _integer(obj["as_of_ms"], "as_of_ms", 0, 10**12),
        _fingerprint(obj.get("fingerprint_hex")),
        _integer(obj["max_bit_errors"], "max_bit_errors", 0, 3),
        _integer(obj["limit"], "limit", 1, 20),
        _integer(obj["min_risk_score"], "min_risk_score", 0, 100),
    )


def read_requests(path: str | Path) -> Iterator[tuple[str | None, Query | None, str | None]]:
    with open(path, encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            request_id: str | None = None
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and isinstance(obj.get("request_id"), str) and _ID.fullmatch(obj["request_id"]):
                    request_id = obj["request_id"]
                query = parse_query(obj)
            except (ValueError, TypeError) as exc:
                yield request_id, None, f"requests line {line_number}: {exc}"
                continue
            yield request_id, query, None
