"""Starter harness for the MergeGuard interview exercise."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Record:
    record_id: str
    source: str
    created_at: datetime
    quality_score: int
    display_name: str


def parse_utc(value: str) -> datetime:
    value = value.strip()
    if not value.endswith("Z"):
        raise ValueError(f"timestamp must end in Z: {value!r}")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"invalid UTC timestamp: {value!r}") from exc


def load_records(path: str | Path) -> dict[str, Record]:
    records: dict[str, Record] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record_id = row["record_id"].strip()
            if not record_id:
                raise ValueError("record_id cannot be empty")
            if record_id in records:
                raise ValueError(f"duplicate record_id: {record_id}")
            try:
                quality = int(row["quality_score"])
            except ValueError as exc:
                raise ValueError(f"invalid quality_score for {record_id}") from exc
            if not 0 <= quality <= 100:
                raise ValueError(f"quality_score out of range for {record_id}")
            records[record_id] = Record(
                record_id=record_id,
                source=row["source"].strip(),
                created_at=parse_utc(row["created_at"]),
                quality_score=quality,
                display_name=row["display_name"].strip(),
            )
    return records


def load_separations(
    path: str | Path, records: dict[str, Record]
) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            left = row["record_a"].strip()
            right = row["record_b"].strip()
            if left not in records or right not in records:
                missing = left if left not in records else right
                raise ValueError(f"unknown record in separation: {missing}")
            if left == right:
                raise ValueError(f"self-separation is invalid: {left}")
            pairs.add(tuple(sorted((left, right))))
    return pairs


def load_events(path: str | Path, records: dict[str, Record]) -> list[dict]:
    events: list[dict] = []
    seen_ids: set[str] = set()
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}") from exc

            event_id = str(event.get("event_id", "")).strip()
            if not event_id or event_id in seen_ids:
                raise ValueError(f"missing or duplicate event_id: {event_id!r}")
            seen_ids.add(event_id)

            event_type = event.get("type")
            if event_type == "link":
                referenced = [event.get("left"), event.get("right")]
            elif event_type == "query":
                referenced = [event.get("record_id")]
            else:
                raise ValueError(f"unknown event type: {event_type!r}")

            for record_id in referenced:
                if record_id not in records:
                    raise ValueError(f"unknown record in event {event_id}: {record_id}")
            events.append(event)
    return events


def canonical_key(record: Record) -> tuple:
    """Smaller key means a better canonical record."""
    return (-record.quality_score, record.created_at, record.record_id)


class MergeGuard:
    def __init__(
        self,
        records: dict[str, Record],
        separations: set[tuple[str, str]],
    ) -> None:
        self.records = records
        self.separations = separations
        # Build whatever incremental indexes/state your design needs here.

    def link(self, left: str, right: str) -> dict:
        raise NotImplementedError("implement link semantics")

    def query(self, record_id: str) -> dict:
        raise NotImplementedError("implement query semantics")


def run_events(engine: MergeGuard, events: Iterable[dict]) -> Iterable[dict]:
    for event in events:
        if event["type"] == "link":
            payload = engine.link(event["left"], event["right"])
        else:
            payload = engine.query(event["record_id"])
        yield {"event_id": event["event_id"], **payload}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incremental customer-record reconciliation")
    parser.add_argument("--records", required=True)
    parser.add_argument("--separations", required=True)
    parser.add_argument("--events", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    records = load_records(args.records)
    separations = load_separations(args.separations, records)
    events = load_events(args.events, records)
    engine = MergeGuard(records, separations)
    for result in run_events(engine, events):
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
