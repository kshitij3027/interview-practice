from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

from .model import Locker, Query, QueryRecord, SIZE_ORDER, VALID_STATUSES

_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class DataValidationError(ValueError):
    pass


def _parse_float(value: str, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DataValidationError(f"invalid {field}") from exc
    if not math.isfinite(number):
        raise DataValidationError(f"invalid {field}")
    return number


def _parse_nonnegative_int(value: str, field: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        raise DataValidationError(f"invalid {field}")
    return int(value)


def _parse_capability_field(value: str) -> frozenset[str]:
    if value == "":
        return frozenset()
    tokens = value.split("|")
    if any(not _CAPABILITY_RE.fullmatch(token) for token in tokens):
        raise DataValidationError("invalid capability token")
    if len(tokens) != len(set(tokens)):
        raise DataValidationError("duplicate capability token")
    return frozenset(tokens)


def load_lockers(path: str | Path) -> list[Locker]:
    lockers: list[Locker] = []
    seen: set[str] = set()
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        expected = {"locker_id", "lat", "lon", "status", "max_parcel_size", "available_slots", "queue_minutes", "capabilities"}
        if set(reader.fieldnames or []) != expected:
            raise DataValidationError("unexpected lockers.csv columns")
        for row in reader:
            locker_id = row["locker_id"].strip()
            if not locker_id or locker_id in seen:
                raise DataValidationError("duplicate or empty locker_id")
            seen.add(locker_id)
            lat = _parse_float(row["lat"], "latitude")
            lon = _parse_float(row["lon"], "longitude")
            if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
                raise DataValidationError("coordinate out of range")
            status = row["status"].strip()
            if status not in VALID_STATUSES:
                raise DataValidationError("invalid status")
            max_size = row["max_parcel_size"].strip()
            if max_size not in SIZE_ORDER:
                raise DataValidationError("invalid max_parcel_size")
            available_slots = _parse_nonnegative_int(row["available_slots"], "available_slots")
            queue_minutes = _parse_nonnegative_int(row["queue_minutes"], "queue_minutes")
            capabilities = _parse_capability_field(row["capabilities"].strip())
            lockers.append(Locker(locker_id, lat, lon, status, max_size, available_slots, queue_minutes, capabilities))
    return lockers


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _valid_capability_token(value: Any) -> bool:
    return isinstance(value, str) and bool(_CAPABILITY_RE.fullmatch(value))


def parse_query_object(obj: Any) -> QueryRecord:
    request_id: str | None = None
    if isinstance(obj, dict) and isinstance(obj.get("request_id"), str) and obj["request_id"]:
        request_id = obj["request_id"]
    if not isinstance(obj, dict):
        return QueryRecord(request_id, None, "invalid_query", obj)
    required = {"request_id", "lat", "lon", "parcel_size", "required_capabilities", "max_distance_meters", "limit"}
    if set(obj.keys()) != required:
        return QueryRecord(request_id, None, "invalid_query", obj)
    if not isinstance(obj["request_id"], str) or not obj["request_id"]:
        return QueryRecord(None, None, "invalid_query", obj)
    if not _finite_number(obj["lat"]) or not _finite_number(obj["lon"]):
        return QueryRecord(request_id, None, "invalid_query", obj)
    lat = float(obj["lat"]); lon = float(obj["lon"])
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return QueryRecord(request_id, None, "invalid_query", obj)
    parcel_size = obj["parcel_size"]
    if parcel_size not in SIZE_ORDER:
        return QueryRecord(request_id, None, "invalid_query", obj)
    capabilities = obj["required_capabilities"]
    if not isinstance(capabilities, list) or any(not _valid_capability_token(v) for v in capabilities):
        return QueryRecord(request_id, None, "invalid_query", obj)
    max_distance = obj["max_distance_meters"]; limit = obj["limit"]
    if not isinstance(max_distance, int) or isinstance(max_distance, bool) or not (1 <= max_distance <= 200_000):
        return QueryRecord(request_id, None, "invalid_query", obj)
    if not isinstance(limit, int) or isinstance(limit, bool) or not (1 <= limit <= 20):
        return QueryRecord(request_id, None, "invalid_query", obj)
    query = Query(request_id, lat, lon, parcel_size, frozenset(capabilities), max_distance, limit)
    return QueryRecord(request_id, query, None, obj)


def load_queries(path: str | Path) -> list[QueryRecord]:
    records: list[QueryRecord] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                records.append(QueryRecord(None, None, "invalid_query", None)); continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                records.append(QueryRecord(None, None, "invalid_query", stripped)); continue
            records.append(parse_query_object(obj))
    return records
