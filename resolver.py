"""Starter harness for the RoutePolicy exercise."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Rule:
    rule_id: str
    tenant: str
    region: str
    path_pattern: str
    valid_from: datetime
    valid_to: Optional[datetime]
    priority: int
    action: str
    destination: Optional[str]


@dataclass(frozen=True)
class Request:
    request_id: str
    tenant: str
    region: str
    event_time: datetime
    path: str


def parse_utc_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and require an explicit UTC offset."""
    if not value:
        raise ValueError("timestamp is required")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"timezone-less timestamp is not allowed: {value!r}")
    if dt.utcoffset().total_seconds() != 0:
        raise ValueError(f"timestamp must be UTC: {value!r}")
    return dt


def validate_path(value: str, *, allow_wildcards: bool) -> tuple[str, ...]:
    if not value:
        raise ValueError("path cannot be empty")
    parts = tuple(value.split("/"))
    if any(part == "" for part in parts):
        raise ValueError(f"empty path segment in {value!r}")
    if len(parts) > 32:
        raise ValueError("path exceeds maximum depth 32")
    if not allow_wildcards and any(part in {"*", "**"} for part in parts):
        raise ValueError("request paths cannot contain wildcard segments")
    if allow_wildcards and sum(part == "**" for part in parts) > 1:
        raise ValueError("a rule may contain at most one ** segment")
    return parts


def load_rules(path: str | Path) -> list[Rule]:
    rules: list[Rule] = []
    seen: dict[str, Rule] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row_number, row in enumerate(csv.DictReader(fh), start=2):
            try:
                valid_from = parse_utc_timestamp(row["valid_from"])
                valid_to = parse_utc_timestamp(row["valid_to"]) if row["valid_to"] else None
                validate_path(row["path_pattern"], allow_wildcards=True)
                if valid_to is not None and valid_to <= valid_from:
                    raise ValueError("valid_to must be after valid_from")
                action = row["action"]
                destination = row["destination"] or None
                if action not in {"route", "block"}:
                    raise ValueError(f"unsupported action {action!r}")
                if action == "route" and destination is None:
                    raise ValueError("route rule requires destination")
                if action == "block" and destination is not None:
                    raise ValueError("block rule must not have destination")
                rule = Rule(
                    rule_id=row["rule_id"],
                    tenant=row["tenant"],
                    region=row["region"],
                    path_pattern=row["path_pattern"],
                    valid_from=valid_from,
                    valid_to=valid_to,
                    priority=int(row["priority"]),
                    action=action,
                    destination=destination,
                )
            except Exception as exc:
                raise ValueError(f"invalid rule row {row_number}: {exc}") from exc

            previous = seen.get(rule.rule_id)
            if previous is None:
                seen[rule.rule_id] = rule
                rules.append(rule)
            elif previous != rule:
                raise ValueError(f"conflicting rows for rule_id {rule.rule_id!r}")
    return rules


def load_requests(path: str | Path) -> Iterable[Request]:
    with open(path, encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                validate_path(row["path"], allow_wildcards=False)
                yield Request(
                    request_id=row["request_id"],
                    tenant=row["tenant"],
                    region=row["region"],
                    event_time=parse_utc_timestamp(row["event_time"]),
                    path=row["path"],
                )
            except Exception as exc:
                raise ValueError(f"invalid request line {line_number}: {exc}") from exc


class PolicyResolver:
    """Build any static indexes you need in __init__, then resolve many requests."""

    def __init__(self, rules: Iterable[Rule]):
        self.rules = list(rules)
        # Build your production-credible representation here.

    def resolve(self, request: Request) -> Optional[Rule]:
        """Return the winning rule, or None when no policy matches."""
        raise NotImplementedError("implement PolicyResolver.resolve")


def result_for(request: Request, rule: Optional[Rule]) -> dict:
    if rule is None:
        return {
            "request_id": request.request_id,
            "matched_rule_id": None,
            "action": "default",
            "destination": None,
        }
    return {
        "request_id": request.request_id,
        "matched_rule_id": rule.rule_id,
        "action": rule.action,
        "destination": rule.destination,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve transaction routing policies")
    parser.add_argument("--rules", required=True)
    parser.add_argument("--requests", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    resolver = PolicyResolver(load_rules(args.rules))
    for request in load_requests(args.requests):
        print(json.dumps(result_for(request, resolver.resolve(request)), sort_keys=True))


if __name__ == "__main__":
    main()
