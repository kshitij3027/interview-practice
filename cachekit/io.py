"""Catalog and event-tape loading for CacheFlow."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
_EVENT_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    quota_kb: int


@dataclass(frozen=True)
class ObjectDef:
    object_id: str
    tenant_id: str
    size_kb: int
    ttl_ms: int


@dataclass(frozen=True)
class Event:
    event_id: str
    at_ms: int
    sequence: int
    kind: str
    tenant_id: str
    object_id: str


@dataclass(frozen=True)
class Catalog:
    tenants: dict[str, Tenant]
    objects: dict[str, ObjectDef]


def number(value: str, low: int, high: int) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError("invalid unsigned integer")
    result = int(value)
    if not low <= result <= high:
        raise ValueError("integer outside permitted range")
    return result


def identifier(value: str, event: bool = False) -> str:
    if not isinstance(value, str) or not (_EVENT_ID if event else _ID).fullmatch(value):
        raise ValueError("invalid identifier")
    return value


def _rows(path: str | Path, columns: set[str]):
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(columns) or set(reader.fieldnames) != columns:
            raise ValueError(f"invalid CSV headers in {path}")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"malformed CSV row in {path}")
            yield row


def _unique(target: dict, key: str, item):
    if key in target and target[key] != item:
        raise ValueError(f"conflicting catalog identifier: {key}")
    target[key] = item


def load_catalog(tenants_path: str | Path, objects_path: str | Path) -> Catalog:
    tenants: dict[str, Tenant] = {}
    objects: dict[str, ObjectDef] = {}
    for row in _rows(tenants_path, {"tenant_id", "quota_kb"}):
        item = Tenant(identifier(row["tenant_id"]), number(row["quota_kb"], 0, 10**9))
        _unique(tenants, item.tenant_id, item)
    if not tenants:
        raise ValueError("empty tenant catalog")
    for row in _rows(objects_path, {"object_id", "tenant_id", "size_kb", "ttl_ms"}):
        item = ObjectDef(identifier(row["object_id"]), identifier(row["tenant_id"]),
                         number(row["size_kb"], 1, 10**9), number(row["ttl_ms"], 0, 10**12))
        if item.tenant_id not in tenants:
            raise ValueError(f"unknown tenant for {item.object_id}")
        _unique(objects, item.object_id, item)
    return Catalog(tenants, objects)


def _query_integer(value, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid event integer")
    return value


def _parse_event(raw: str, catalog: Catalog) -> Event | dict:
    value = None
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("not an object")
        event_id = identifier(value.get("event_id"), event=True)
        event = Event(event_id,
                      _query_integer(value.get("at_ms"), 0, 10**12),
                      _query_integer(value.get("sequence"), 0, 10**6),
                      value.get("kind"), identifier(value.get("tenant_id")),
                      identifier(value.get("object_id")))
        if event.kind not in ("fetch", "invalidate"):
            raise ValueError("unknown event kind")
    except (ValueError, TypeError, json.JSONDecodeError):
        maybe_id = value.get("event_id") if isinstance(value, dict) else None
        safe_id = maybe_id if isinstance(maybe_id, str) and _EVENT_ID.fullmatch(maybe_id) else None
        return {"event_id": safe_id, "status": "invalid", "reason": "invalid_event"}
    definition = catalog.objects.get(event.object_id)
    if event.tenant_id not in catalog.tenants or definition is None or definition.tenant_id != event.tenant_id:
        return {"event_id": event.event_id, "status": "invalid", "reason": "unknown_reference"}
    return event


def load_event_tape(path: str | Path, catalog: Catalog) -> tuple[list[Event | dict], list[Event]]:
    entries: list[Event | dict] = []
    unique: dict[str, Event] = {}
    clock: dict[tuple[int, int], str] = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            entry = _parse_event(line, catalog)
            entries.append(entry)
            if isinstance(entry, dict):
                continue
            old = unique.get(entry.event_id)
            if old is not None:
                if old != entry:
                    raise ValueError(f"conflicting event replay: {entry.event_id}")
                continue
            key = (entry.at_ms, entry.sequence)
            if key in clock:
                raise ValueError(f"duplicate chronological position: {key}")
            clock[key] = entry.event_id
            unique[entry.event_id] = entry
    return entries, sorted(unique.values(), key=lambda item: (item.at_ms, item.sequence))
