from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Queue:
    queue_id: str
    snapshot_start: datetime
    opening_backlog: int


@dataclass(frozen=True)
class EventRevision:
    event_id: str
    revision: int
    queue_id: str
    occurred_at: datetime
    delta_items: int
    state: str


@dataclass(frozen=True)
class EffectiveEvent:
    event_id: str
    queue_id: str
    occurred_at: datetime
    delta_items: int


@dataclass(frozen=True)
class QueryRecord:
    line_number: int
    query_key: str | None
    queue_id: str | None
    start_at: datetime | None
    end_at: datetime | None
    limit_items: int | None
    error: str | None = None


@dataclass(frozen=True)
class Snapshot:
    queues: dict[str, Queue]
    effective_events_by_queue: dict[str, tuple[EffectiveEvent, ...]]
    raw_revision_rows: int
    effective_posted_events: int


def parse_rfc3339(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty string")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid RFC3339 timestamp: {value}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"timestamp must include an explicit offset: {value}")
    return dt.astimezone(timezone.utc)


def format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _int_csv(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text and (text.isdigit() or (text.startswith("-") and text[1:].isdigit())):
            return int(text)
    raise ValueError(f"{field} must be an integer")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value.strip()


def load_queues(path: str | Path) -> dict[str, Queue]:
    queues: dict[str, Queue] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"queue_id", "snapshot_start", "opening_backlog"}
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError("queues.csv has unexpected columns")
        for row in reader:
            queue_id = _text(row["queue_id"], "queue_id")
            if queue_id in queues:
                raise ValueError(f"duplicate queue_id: {queue_id}")
            start = parse_rfc3339(row["snapshot_start"])
            opening = _int_csv(row["opening_backlog"], "opening_backlog")
            if opening < 0:
                raise ValueError(f"negative opening backlog for {queue_id}")
            queues[queue_id] = Queue(queue_id, start, opening)
    if not queues:
        raise ValueError("queues.csv must contain at least one queue")
    return queues


def load_events(path: str | Path, queues: dict[str, Queue]) -> tuple[dict[str, tuple[EffectiveEvent, ...]], int, int]:
    seen: dict[tuple[str, int], EventRevision] = {}
    owner: dict[str, str] = {}
    raw_rows = 0
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"event_id", "revision", "queue_id", "occurred_at", "delta_items", "state"}
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError("events.csv has unexpected columns")
        for row in reader:
            raw_rows += 1
            event_id = _text(row["event_id"], "event_id")
            revision = _int_csv(row["revision"], "revision")
            if revision <= 0:
                raise ValueError(f"revision must be positive for {event_id}")
            queue_id = _text(row["queue_id"], "queue_id")
            if queue_id not in queues:
                raise ValueError(f"unknown queue_id in events: {queue_id}")
            previous = owner.setdefault(event_id, queue_id)
            if previous != queue_id:
                raise ValueError(f"event_id reused across queues: {event_id}")
            occurred_at = parse_rfc3339(row["occurred_at"])
            if occurred_at < queues[queue_id].snapshot_start:
                raise ValueError(f"event occurs before snapshot_start: {event_id}")
            delta = _int_csv(row["delta_items"], "delta_items")
            state = _text(row["state"], "state")
            if state not in {"posted", "voided"}:
                raise ValueError(f"unsupported state for {event_id}: {state}")
            record = EventRevision(event_id, revision, queue_id, occurred_at, delta, state)
            key = (event_id, revision)
            if key in seen and seen[key] != record:
                raise ValueError(f"conflicting duplicate revision: {event_id}@{revision}")
            seen[key] = record

    highest: dict[str, EventRevision] = {}
    for record in seen.values():
        current = highest.get(record.event_id)
        if current is None or record.revision > current.revision:
            highest[record.event_id] = record

    grouped: dict[str, list[EffectiveEvent]] = {qid: [] for qid in queues}
    effective_count = 0
    for record in highest.values():
        if record.state == "posted":
            grouped[record.queue_id].append(EffectiveEvent(record.event_id, record.queue_id, record.occurred_at, record.delta_items))
            effective_count += 1

    frozen: dict[str, tuple[EffectiveEvent, ...]] = {}
    for queue_id, records in grouped.items():
        records.sort(key=lambda r: (r.occurred_at, r.event_id))
        frozen[queue_id] = tuple(records)
    return frozen, raw_rows, effective_count


def load_snapshot(queues_path: str | Path, events_path: str | Path) -> Snapshot:
    queues = load_queues(queues_path)
    events, raw_rows, effective_count = load_events(events_path, queues)
    return Snapshot(queues, events, raw_rows, effective_count)


def load_queries(path: str | Path) -> list[QueryRecord]:
    records: list[QueryRecord] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"query_key", "queue_id", "start_at", "end_at", "limit_items"}
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError("queries.csv has unexpected columns")
        for line_number, row in enumerate(reader, 2):
            query_key = row.get("query_key", "").strip() or None
            try:
                if query_key is None:
                    raise ValueError
                queue_id = _text(row.get("queue_id"), "queue_id")
                start_at = parse_rfc3339(row.get("start_at"))
                end_at = parse_rfc3339(row.get("end_at"))
                limit_items = _int_csv(row.get("limit_items"), "limit_items")
                if end_at <= start_at:
                    raise ValueError
                records.append(QueryRecord(line_number, query_key, queue_id, start_at, end_at, limit_items))
            except (ValueError, TypeError):
                records.append(QueryRecord(line_number, query_key, None, None, None, None, "invalid_query"))
    return records


class BacklogResolver:
    """Resolve historical queue-overload queries against one immutable snapshot.

    Parsing, validation, and the public interface are provided. The query capability
    is the interview task; choose the internal representation and supporting code
    that best satisfy the README contract and production constraints.
    """

    def __init__(self, snapshot: Snapshot) -> None:
        self.snapshot = snapshot

    def resolve_all(self, queries: Iterable[QueryRecord]) -> list[dict]:
        results: list[dict] = []
        for query in queries:
            if query.error is not None:
                results.append({"query_key": query.query_key, "status": "invalid", "reason": query.error})
                continue
            if query.queue_id not in self.snapshot.queues:
                results.append({"query_key": query.query_key, "status": "invalid", "reason": "unknown_queue"})
                continue
            queue = self.snapshot.queues[query.queue_id]
            assert query.start_at is not None
            if query.start_at < queue.snapshot_start:
                results.append({"query_key": query.query_key, "status": "invalid", "reason": "before_snapshot"})
                continue
            results.append(self.resolve(query))
        return results

    def resolve(self, query: QueryRecord) -> dict:
        raise NotImplementedError("implement the historical backlog resolver")
