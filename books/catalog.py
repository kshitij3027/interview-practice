"""Snapshot input validation for dealer quotes."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
_COLUMNS = ("update_id", "received_ms", "sequence", "market", "quote_id", "side", "price_cents", "available_lots")


def valid_id(value: object) -> bool:
    return isinstance(value, str) and bool(_ID.fullmatch(value))


def integer(value: str, name: str, low: int, high: int) -> int:
    if not value or not value.isascii() or not value.isdecimal():
        raise ValueError(f"{name}: expected unsigned decimal integer")
    result = int(value)
    if not low <= result <= high:
        raise ValueError(f"{name}: out of range")
    return result


@dataclass(frozen=True)
class Update:
    update_id: str
    received_ms: int
    sequence: int
    market: str
    quote_id: str
    side: str
    price_cents: int
    available_lots: int


def load_updates(path: str | Path) -> list[Update]:
    by_id: dict[str, Update] = {}
    positions: dict[tuple[int, int], str] = {}
    owners: dict[str, tuple[str, str]] = {}
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(_COLUMNS):
            raise ValueError("update CSV header mismatch")
        for line, row in enumerate(reader, 2):
            try:
                if None in row or any(not valid_id(row[k]) for k in ("update_id", "market", "quote_id")):
                    raise ValueError("invalid ID or columns")
                if row["side"] not in ("ask", "bid"):
                    raise ValueError("invalid side")
                obj = Update(
                    update_id=row["update_id"],
                    received_ms=integer(row["received_ms"], "received_ms", 0, 10**12),
                    sequence=integer(row["sequence"], "sequence", 0, 10**12),
                    market=row["market"], quote_id=row["quote_id"], side=row["side"],
                    price_cents=integer(row["price_cents"], "price_cents", 1, 10**8),
                    available_lots=integer(row["available_lots"], "available_lots", 0, 10**9),
                )
                previous = by_id.get(obj.update_id)
                if previous is not None:
                    if previous != obj:
                        raise ValueError("conflicting update_id")
                    continue
                pos = (obj.received_ms, obj.sequence)
                if pos in positions:
                    raise ValueError("colliding event order")
                owner = (obj.market, obj.side)
                if obj.quote_id in owners and owners[obj.quote_id] != owner:
                    raise ValueError("quote_id moved across market or side")
                owners[obj.quote_id] = owner
                positions[pos] = obj.update_id
                by_id[obj.update_id] = obj
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"updates.csv line {line}: {exc}") from exc
    return sorted(by_id.values(), key=lambda event: (event.received_ms, event.sequence))
