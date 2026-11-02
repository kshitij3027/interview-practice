"""Input contract and validation. This file intentionally contains no zone-matching logic."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ID = re.compile(r"[A-Za-z0-9_-]+\Z")
_MAX_TIME = 10**12
_MAX_COORD = 10**9


class CatalogError(ValueError):
    pass


class QueryError(ValueError):
    pass


Point = tuple[int, int]
Ring = tuple[Point, ...]


@dataclass(frozen=True)
class Zone:
    zone_id: str
    region: str
    priority: int
    active_from_ms: int
    active_until_ms: int
    altitude_min_m: int
    altitude_max_m: int
    outer: Ring
    holes: tuple[Ring, ...]


@dataclass(frozen=True)
class Query:
    request_id: str
    region: str
    x: int
    y: int
    at_ms: int
    altitude_m: int
    limit: int


def _id(value: Any, maximum: int = 48) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= maximum and _ID.fullmatch(value) is not None


def _int(value: Any, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _ring(value: Any) -> Ring:
    if not isinstance(value, list) or not 3 <= len(value) <= 1000:
        raise CatalogError("ring must contain 3..1000 vertices")
    pts = []
    for p in value:
        if not isinstance(p, list) or len(p) != 2 or not all(_int(v, -_MAX_COORD, _MAX_COORD) for v in p):
            raise CatalogError("invalid vertex")
        pts.append((p[0], p[1]))
    if pts[0] == pts[-1]:
        raise CatalogError("closing vertex must be implicit")
    return tuple(pts)


def _zone(obj: Any) -> Zone:
    if not isinstance(obj, dict):
        raise CatalogError("zone must be a JSON object")
    try:
        zone_id, region, priority = obj["zone_id"], obj["region"], obj["priority"]
        start, end = obj["active_from_ms"], obj["active_until_ms"]
        low, high = obj["altitude_min_m"], obj["altitude_max_m"]
        outer, holes = obj["outer"], obj["holes"]
    except KeyError as e:
        raise CatalogError(f"missing zone field {e.args[0]}") from e
    if not _id(zone_id) or not _id(region):
        raise CatalogError("invalid zone or region ID")
    if not _int(priority, 0, 1000) or not _int(start, 0, _MAX_TIME) or not _int(end, 0, _MAX_TIME) or start >= end:
        raise CatalogError("invalid priority or time bounds")
    if not _int(low, 0, 100000) or not _int(high, 0, 100000) or low >= high:
        raise CatalogError("invalid altitude bounds")
    if not isinstance(holes, list) or len(holes) > 20:
        raise CatalogError("invalid holes")
    return Zone(zone_id, region, priority, start, end, low, high, _ring(outer), tuple(_ring(h) for h in holes))


def load_zones(path: str | Path) -> list[Zone]:
    unique: dict[str, Zone] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                try:
                    z = _zone(json.loads(line))
                except (json.JSONDecodeError, CatalogError) as e:
                    raise CatalogError(f"line {line_number}: {e}") from e
                existing = unique.get(z.zone_id)
                if existing is not None and existing != z:
                    raise CatalogError(f"line {line_number}: conflicting zone ID {z.zone_id}")
                unique[z.zone_id] = z
    except (OSError, UnicodeError) as e:
        raise CatalogError(str(e)) from e
    return list(unique.values())


def read_request_id(line: str) -> str | None:
    try:
        obj = json.loads(line)
        rid = obj.get("request_id") if isinstance(obj, dict) else None
        return rid if _id(rid, 128) else None
    except (ValueError, TypeError):
        return None


def parse_query(line: str) -> Query:
    try:
        obj = json.loads(line)
    except (json.JSONDecodeError, UnicodeError) as e:
        raise QueryError("bad JSON") from e
    if not isinstance(obj, dict):
        raise QueryError("query must be object")
    required = ("request_id", "region", "x", "y", "at_ms", "altitude_m")
    if any(k not in obj for k in required):
        raise QueryError("missing query field")
    rid, region, x, y = (obj[k] for k in required[:4])
    at_ms, altitude = obj["at_ms"], obj["altitude_m"]
    limit = obj.get("limit", 3)
    if not _id(rid, 128) or not _id(region):
        raise QueryError("invalid ID")
    if not _int(x, -_MAX_COORD, _MAX_COORD) or not _int(y, -_MAX_COORD, _MAX_COORD):
        raise QueryError("invalid point")
    if not _int(at_ms, 0, _MAX_TIME) or not _int(altitude, 0, 100000) or not _int(limit, 1, 10):
        raise QueryError("invalid time, altitude, or limit")
    return Query(rid, region, x, y, at_ms, altitude, limit)
