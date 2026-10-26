"""Input contracts for the terminal's immutable investigation snapshot."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
_UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z")


@dataclass(frozen=True)
class Yard:
    yard_id: str
    max_group_kg: int


@dataclass(frozen=True)
class Container:
    container_id: str
    yard_id: str
    gross_kg: int


@dataclass(frozen=True)
class Link:
    link_id: str
    left_id: str
    right_id: str


@dataclass(frozen=True)
class Event:
    event_id: str
    occurred_ms: int
    sequence: int
    link_id: str
    state: str


@dataclass(frozen=True)
class Snapshot:
    yards: dict[str, Yard]
    containers: dict[str, Container]
    links: dict[str, Link]
    events: tuple[Event, ...]


def _id(value: str, field: str) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ValueError(f"invalid {field}: {value!r}")
    return value


def _uint(value: str, field: str, maximum: int = 10**12) -> int:
    if not isinstance(value, str) or _UINT.fullmatch(value) is None:
        raise ValueError(f"invalid {field}: {value!r}")
    parsed = int(value)
    if parsed > maximum:
        raise ValueError(f"invalid {field}: exceeds {maximum}")
    return parsed


def _rows(path: str | Path, columns: tuple[str, ...]):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(columns):
            raise ValueError(f"{path}: expected columns {','.join(columns)}")
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}:{line}: malformed CSV row")
            yield row


def load_snapshot(yards_path: str, containers_path: str, links_path: str, events_path: str) -> Snapshot:
    yards: dict[str, Yard] = {}
    for row in _rows(yards_path, ("yard_id", "max_group_kg")):
        entry = Yard(_id(row["yard_id"], "yard_id"), _uint(row["max_group_kg"], "max_group_kg"))
        if entry.yard_id in yards:
            raise ValueError(f"duplicate yard {entry.yard_id}")
        yards[entry.yard_id] = entry

    containers: dict[str, Container] = {}
    for row in _rows(containers_path, ("container_id", "yard_id", "gross_kg")):
        entry = Container(_id(row["container_id"], "container_id"), _id(row["yard_id"], "yard_id"), _uint(row["gross_kg"], "gross_kg", 10**9))
        if entry.container_id in containers or entry.yard_id not in yards:
            raise ValueError(f"duplicate container or unknown yard: {entry.container_id}")
        containers[entry.container_id] = entry

    links: dict[str, Link] = {}
    for row in _rows(links_path, ("link_id", "left_id", "right_id")):
        link_id = _id(row["link_id"], "link_id")
        a, b = _id(row["left_id"], "left_id"), _id(row["right_id"], "right_id")
        if a == b or a not in containers or b not in containers or containers[a].yard_id != containers[b].yard_id:
            raise ValueError(f"invalid endpoints for link {link_id}")
        entry = Link(link_id, *sorted((a, b)))
        if link_id in links and links[link_id] != entry:
            raise ValueError(f"conflicting definition of link {link_id}")
        links[link_id] = entry

    events: dict[str, Event] = {}
    pairs: dict[tuple[int, int], str] = {}
    for row in _rows(events_path, ("event_id", "occurred_ms", "sequence", "link_id", "state")):
        entry = Event(_id(row["event_id"], "event_id"), _uint(row["occurred_ms"], "occurred_ms"), _uint(row["sequence"], "sequence"), _id(row["link_id"], "link_id"), row["state"])
        if entry.link_id not in links or entry.state not in ("open", "close"):
            raise ValueError(f"unknown link or invalid state: {entry.event_id}")
        old = events.get(entry.event_id)
        if old is not None:
            if old != entry:
                raise ValueError(f"conflicting event replay {entry.event_id}")
            continue
        pair = (entry.occurred_ms, entry.sequence)
        if pair in pairs:
            raise ValueError(f"duplicate ordering pair: {pair}")
        pairs[pair] = entry.event_id
        events[entry.event_id] = entry

    return Snapshot(yards, containers, links, tuple(sorted(events.values(), key=lambda item: (item.occurred_ms, item.sequence))))


def parse_query(line: str, snapshot: Snapshot) -> dict:
    try:
        raw = json.loads(line)
    except (json.JSONDecodeError, UnicodeError):
        return {"request_id": None, "status": "invalid", "reason": "invalid_query"}
    if not isinstance(raw, dict):
        return {"request_id": None, "status": "invalid", "reason": "invalid_query"}
    request_id = raw.get("request_id")
    if not isinstance(request_id, str) or not (1 <= len(request_id) <= 128):
        request_id = None
    error = {"request_id": request_id, "status": "invalid", "reason": "invalid_query"}
    if request_id is None:
        return error
    kind, time = raw.get("kind"), raw.get("as_of_ms")
    if kind not in ("group", "connected") or type(time) is not int or not (0 <= time <= 10**12):
        return error
    fields = ("container_id",) if kind == "group" else ("left_id", "right_id")
    if any(not isinstance(raw.get(field), str) or _ID.fullmatch(raw[field]) is None for field in fields):
        return error
    if any(raw[field] not in snapshot.containers for field in fields):
        return {"request_id": request_id, "status": "invalid", "reason": "unknown_container"}
    return {key: raw[key] for key in ("request_id", "kind", "as_of_ms", *fields)}


def load_queries(path: str, snapshot: Snapshot) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [parse_query(line, snapshot) for line in handle]
