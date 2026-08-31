#!/usr/bin/env python3
"""Starter harness for the RiskPulse interview exercise."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class MerchantPolicy:
    merchant_id: str
    window_seconds: int
    min_declines: int
    min_distinct_cards: int
    cooldown_seconds: int


@dataclass(frozen=True)
class Event:
    event_id: str
    source_partition: str
    source_seq: int
    merchant_id: str
    occurred_at: datetime
    card_fingerprint: str
    outcome: str


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty string")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp must include timezone information: {value!r}")
    return parsed.astimezone(timezone.utc)


def format_timestamp(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _positive_int(raw: str, field: str, merchant_id: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} for merchant {merchant_id!r} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{field} for merchant {merchant_id!r} must be positive")
    return value


def load_policies(path: str | Path) -> dict[str, MerchantPolicy]:
    policies: dict[str, MerchantPolicy] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "merchant_id",
            "window_seconds",
            "min_declines",
            "min_distinct_cards",
            "cooldown_seconds",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"merchant CSV must include columns: {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            merchant_id = (row.get("merchant_id") or "").strip()
            if not merchant_id:
                raise ValueError(f"empty merchant_id on row {row_number}")
            policy = MerchantPolicy(
                merchant_id=merchant_id,
                window_seconds=_positive_int(row["window_seconds"], "window_seconds", merchant_id),
                min_declines=_positive_int(row["min_declines"], "min_declines", merchant_id),
                min_distinct_cards=_positive_int(
                    row["min_distinct_cards"], "min_distinct_cards", merchant_id
                ),
                cooldown_seconds=_positive_int(
                    row["cooldown_seconds"], "cooldown_seconds", merchant_id
                ),
            )
            previous = policies.get(merchant_id)
            if previous is not None and previous != policy:
                raise ValueError(f"conflicting policy rows for merchant {merchant_id!r}")
            policies[merchant_id] = policy
    if not policies:
        raise ValueError("merchant policy file is empty")
    return policies


def parse_event(payload: object, line_number: int) -> Event:
    if not isinstance(payload, dict):
        raise ValueError(f"event line {line_number} must be a JSON object")

    def required_string(field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"event line {line_number}: {field} must be a non-empty string")
        return value.strip()

    source_seq = payload.get("source_seq")
    if isinstance(source_seq, bool) or not isinstance(source_seq, int) or source_seq < 0:
        raise ValueError(f"event line {line_number}: source_seq must be a non-negative integer")
    outcome = required_string("outcome")
    if outcome not in {"declined", "approved"}:
        raise ValueError(f"event line {line_number}: unsupported outcome {outcome!r}")

    return Event(
        event_id=required_string("event_id"),
        source_partition=required_string("source_partition"),
        source_seq=source_seq,
        merchant_id=required_string("merchant_id"),
        occurred_at=parse_timestamp(required_string("occurred_at")),
        card_fingerprint=required_string("card_fingerprint"),
        outcome=outcome,
    )


def iter_events(path: str | Path) -> Iterator[Event]:
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"event line {line_number}: invalid JSON") from exc
            yield parse_event(payload, line_number)


class RiskPulseEngine:
    """Implement the stream processor described in README.md."""

    def __init__(self, policies: dict[str, MerchantPolicy], allowed_lateness_seconds: int = 90):
        if allowed_lateness_seconds < 0:
            raise ValueError("allowed_lateness_seconds must be non-negative")
        self.policies = dict(policies)
        self.allowed_lateness_seconds = allowed_lateness_seconds

    def consume(self, events: Iterable[Event]) -> Iterator[dict[str, object]]:
        raise NotImplementedError("implement the RiskPulse stream processor")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect merchant decline bursts in event time")
    parser.add_argument("--merchants", required=True, help="merchant policy CSV")
    parser.add_argument("--events", required=True, help="authorization event JSONL")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policies = load_policies(args.merchants)
    engine = RiskPulseEngine(policies)
    for output in engine.consume(iter_events(args.events)):
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
