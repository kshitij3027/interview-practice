"""Validate and load a finite, immutable support operations snapshot."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\Z")
_NUMBER = re.compile(r"\d+\Z")


class SnapshotError(ValueError):
    pass


@dataclass(frozen=True)
class Interval:
    key: str
    owner: str
    start: int
    end: int


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    region: str
    opened_at: int
    budget_minutes: int


@dataclass(frozen=True)
class Snapshot:
    coverage: dict[str, Interval]
    blackouts: dict[str, Interval]
    tickets: dict[str, Ticket]
    pauses: dict[str, Interval]


def instant(value: str) -> int:
    if not isinstance(value, str) or not _TIME.fullmatch(value):
        raise ValueError("timestamp must have RFC3339 seconds and a timezone offset")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return int(dt.astimezone(timezone.utc).timestamp())
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid timestamp") from exc


def canonical(seconds: int) -> str:
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _key(value: str, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise SnapshotError(f"invalid {field}: {value!r}")
    return value


def _records(path: str | Path, columns: tuple[str, ...]):
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != set(columns):
                raise SnapshotError(f"{path}: expected columns {', '.join(columns)}")
            for number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise SnapshotError(f"{path}:{number}: malformed row")
                yield number, row
    except (OSError, UnicodeError, csv.Error) as exc:
        raise SnapshotError(f"{path}: {exc}") from exc


def _put(target: dict, key: str, record, label: str, row_number: int):
    if key in target and target[key] != record:
        raise SnapshotError(f"{label}:{row_number}: conflicting reuse of {key}")
    target[key] = record


def _intervals(path: str | Path, id_field: str, owner_field: str) -> dict[str, Interval]:
    out = {}
    for number, row in _records(path, (id_field, owner_field, "starts_at", "ends_at")):
        key = _key(row[id_field], id_field)
        owner = _key(row[owner_field], owner_field)
        try:
            start, end = instant(row["starts_at"]), instant(row["ends_at"])
        except ValueError as exc:
            raise SnapshotError(f"{path}:{number}: {exc}") from exc
        if start >= end:
            raise SnapshotError(f"{path}:{number}: empty or reversed interval")
        _put(out, key, Interval(key, owner, start, end), str(path), number)
    return out


def load_snapshot(coverage_path, blackouts_path, tickets_path, pauses_path) -> Snapshot:
    coverage = _intervals(coverage_path, "coverage_id", "region")
    regions = {record.owner for record in coverage.values()}
    if not regions:
        raise SnapshotError("at least one coverage region required")
    blackouts = _intervals(blackouts_path, "blackout_id", "region")
    for blackout in blackouts.values():
        if blackout.owner not in regions:
            raise SnapshotError(f"blackout {blackout.key}: unknown region")
    tickets: dict[str, Ticket] = {}
    for number, row in _records(tickets_path, ("ticket_id", "region", "opened_at", "budget_minutes")):
        key, region = _key(row["ticket_id"], "ticket_id"), _key(row["region"], "region")
        if region not in regions:
            raise SnapshotError(f"tickets:{number}: unknown region")
        try:
            opened_at = instant(row["opened_at"])
        except ValueError as exc:
            raise SnapshotError(f"tickets:{number}: {exc}") from exc
        raw = row["budget_minutes"]
        if not _NUMBER.fullmatch(raw) or int(raw) > 604800:
            raise SnapshotError(f"tickets:{number}: invalid budget")
        _put(tickets, key, Ticket(key, region, opened_at, int(raw)), str(tickets_path), number)
    pauses = _intervals(pauses_path, "pause_id", "ticket_id")
    for pause in pauses.values():
        if pause.owner not in tickets:
            raise SnapshotError(f"pause {pause.key}: unknown ticket")
    return Snapshot(coverage, blackouts, tickets, pauses)
