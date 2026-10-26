"""Catalog and request boundary for the AidLink practice service."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
_LIMIT = 1_000_000


class CatalogError(ValueError):
    pass


def valid_id(value):
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def valid_number(value):
    return type(value) is int and 0 <= value <= _LIMIT


def csv_number(value, *, positive=False):
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise CatalogError(f"invalid catalog number: {value!r}")
    number = int(value)
    if number > _LIMIT or (positive and number == 0):
        raise CatalogError(f"out-of-range catalog number: {value!r}")
    return number


@dataclass(frozen=True)
class Depot:
    depot_id: str
    stock: int


@dataclass(frozen=True)
class Clinic:
    clinic_id: str
    critical: int
    routine: int


@dataclass(frozen=True)
class Lane:
    lane_id: str
    depot_id: str
    clinic_id: str
    capacity: int
    cost_cents: int


@dataclass(frozen=True)
class Catalog:
    depots: dict[str, Depot]
    clinics: dict[str, Clinic]
    lanes: dict[str, Lane]


@dataclass(frozen=True)
class Request:
    request_id: str
    disabled_lanes: frozenset[str]
    stock_overrides: dict[str, int]
    need_overrides: dict[str, tuple[int, int]]


def rows(path: str | Path, required: tuple[str, ...]):
    with open(path, newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or not set(required).issubset(reader.fieldnames):
            raise CatalogError(f"invalid header in {path}")
        for line, row in enumerate(reader, 2):
            if None in row or any(row.get(k) is None for k in required):
                raise CatalogError(f"invalid CSV row {path}:{line}")
            yield row


def _save(table, key, value, kind):
    if not valid_id(key):
        raise CatalogError(f"invalid {kind} ID: {key!r}")
    previous = table.get(key)
    if previous is not None and previous != value:
        raise CatalogError(f"conflicting {kind} definition: {key}")
    table[key] = value


def load_catalog(depots_path, clinics_path, lanes_path) -> Catalog:
    depots, clinics, lanes = {}, {}, {}
    for row in rows(depots_path, ("depot_id", "stock")):
        obj = Depot(row["depot_id"], csv_number(row["stock"]))
        _save(depots, obj.depot_id, obj, "depot")
    for row in rows(clinics_path, ("clinic_id", "critical", "routine")):
        obj = Clinic(row["clinic_id"], csv_number(row["critical"]), csv_number(row["routine"]))
        _save(clinics, obj.clinic_id, obj, "clinic")
    for row in rows(lanes_path, ("lane_id", "depot_id", "clinic_id", "capacity", "cost_cents")):
        obj = Lane(row["lane_id"], row["depot_id"], row["clinic_id"], csv_number(row["capacity"], positive=True), csv_number(row["cost_cents"]))
        _save(lanes, obj.lane_id, obj, "lane")
    if not depots or not clinics:
        raise CatalogError("at least one depot and clinic are required")
    for lane in lanes.values():
        if not valid_id(lane.depot_id) or lane.depot_id not in depots or not valid_id(lane.clinic_id) or lane.clinic_id not in clinics:
            raise CatalogError(f"unknown endpoint in lane {lane.lane_id}")
    return Catalog(depots, clinics, lanes)


def parse_request(line: str, catalog: Catalog):
    """Return (recoverable request_id, request or None, error or None)."""
    try:
        value = json.loads(line)
    except (ValueError, TypeError):
        return None, None, "invalid_request"
    if not isinstance(value, dict):
        return None, None, "invalid_request"
    raw_id = value.get("request_id")
    rid = raw_id if isinstance(raw_id, str) and 0 < len(raw_id) <= 128 else None
    if rid is None:
        return None, None, "invalid_request"
    disabled = value.get("disabled_lanes", [])
    stocks = value.get("stock_overrides", {})
    needs = value.get("need_overrides", {})
    if not isinstance(disabled, list) or not isinstance(stocks, dict) or not isinstance(needs, dict):
        return rid, None, "invalid_request"
    if any(not valid_id(v) for v in disabled):
        return rid, None, "invalid_request"
    if any(not valid_id(k) or not valid_number(v) for k, v in stocks.items()):
        return rid, None, "invalid_request"
    for k, v in needs.items():
        if not valid_id(k) or not isinstance(v, dict) or set(v) != {"critical", "routine"}:
            return rid, None, "invalid_request"
        if not valid_number(v["critical"]) or not valid_number(v["routine"]):
            return rid, None, "invalid_request"
    if any(k not in catalog.lanes for k in disabled) or any(k not in catalog.depots for k in stocks) or any(k not in catalog.clinics for k in needs):
        return rid, None, "unknown_reference"
    parsed = Request(rid, frozenset(disabled), dict(stocks), {k: (v["critical"], v["routine"]) for k, v in needs.items()})
    return rid, parsed, None
