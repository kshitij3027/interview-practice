"""Catalog loading and query validation for the ScanLedger exercise."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CODE = re.compile(r"[A-Z][A-Z0-9_]{1,15}\Z", re.ASCII)

@dataclass(frozen=True)
class Route:
    route_id: str
    carrier: str
    sequence: tuple[str, ...]

def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)

def valid_code(value: Any) -> bool:
    return isinstance(value, str) and CODE.fullmatch(value) is not None

def load_routes(path: str | Path) -> dict[str, Route]:
    routes: dict[str, Route] = {}
    with open(path, encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        if rows.fieldnames != ["route_id", "carrier", "sequence"]:
            raise ValueError("route catalog must have route_id,carrier,sequence header")
        for line_number, row in enumerate(rows, start=2):
            if None in row or set(row) != {"route_id", "carrier", "sequence"}:
                raise ValueError(f"routes.csv line {line_number}: invalid column count")
            route_id, carrier, sequence_text = row.values()
            if not _nonempty_str(route_id) or not _nonempty_str(carrier) or not _nonempty_str(sequence_text):
                raise ValueError(f"routes.csv line {line_number}: missing required field")
            sequence = tuple(sequence_text.split("|"))
            if not sequence or not all(valid_code(code) for code in sequence):
                raise ValueError(f"routes.csv line {line_number}: invalid sequence")
            route = Route(route_id, carrier, sequence)
            if route_id in routes and routes[route_id] != route:
                raise ValueError(f"routes.csv line {line_number}: conflicting route_id {route_id}")
            routes[route_id] = route
    if not routes:
        raise ValueError("route catalog is empty")
    return routes

@dataclass(frozen=True)
class AuditRequest:
    request_id: str
    route_id: str
    scans: tuple[str, ...]
    max_repairs: int

def preserved_request_id(payload: Any) -> str | None:
    if isinstance(payload, dict) and _nonempty_str(payload.get("request_id")):
        return payload["request_id"]
    return None

def parse_request(payload: Any) -> AuditRequest:
    if not isinstance(payload, dict):
        raise ValueError("query must be an object")
    request_id = payload.get("request_id")
    route_id = payload.get("route_id")
    scans = payload.get("scans")
    budget = payload.get("max_repairs")
    if not _nonempty_str(request_id) or not _nonempty_str(route_id):
        raise ValueError("request_id and route_id must be nonempty strings")
    if not isinstance(scans, list) or not all(valid_code(token) for token in scans):
        raise ValueError("scans must be a list of checkpoint codes")
    if type(budget) is not int or budget < 0 or budget > 16:
        raise ValueError("max_repairs must be an integer from 0 to 16")
    return AuditRequest(request_id, route_id, tuple(scans), budget)
