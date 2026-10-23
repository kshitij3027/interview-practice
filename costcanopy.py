"""CostCanopy starter CLI. Python 3.11+; no external dependencies."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]{1,32}\Z")
MONEY = re.compile(r"(?:0|[1-9][0-9]*)\Z")
FIELDS = ["center_id", "parent_id", "budget_cents"]


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Center:
    center_id: str
    parent_id: str | None
    budget_cents: int


def load_centers(path: str | Path) -> dict[str, Center]:
    """Load and validate an immutable reporting-center snapshot."""
    centers: dict[str, Center] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = csv.DictReader(f)
        if rows.fieldnames != FIELDS:
            raise CatalogError("invalid centers header")
        for line, row in enumerate(rows, start=2):
            if None in row or any(value is None for value in row.values()):
                raise CatalogError(f"invalid centers row {line}")
            center_id = row["center_id"]
            parent = row["parent_id"] or None
            money = row["budget_cents"]
            if (not ID.fullmatch(center_id) or
                (parent is not None and not ID.fullmatch(parent)) or
                not MONEY.fullmatch(money) or int(money) > 10**12):
                raise CatalogError(f"invalid centers row {line}")
            center = Center(center_id, parent, int(money))
            if center_id in centers and centers[center_id] != center:
                raise CatalogError(f"conflicting center {center_id}")
            centers[center_id] = center
    if not centers:
        raise CatalogError("empty centers catalog")
    for center in centers.values():
        if center.parent_id is not None and center.parent_id not in centers:
            raise CatalogError(f"unknown parent of {center.center_id}")
    states: dict[str, int] = {}
    for start in centers:
        if states.get(start) == 2:
            continue
        trail: list[str] = []
        current: str | None = start
        while current is not None and states.get(current, 0) == 0:
            states[current] = 1
            trail.append(current)
            current = centers[current].parent_id
        if current is not None and states.get(current) == 1:
            raise CatalogError(f"cycle at {current}")
        for seen in trail:
            states[seen] = 2
    return centers


def inspect_operations(path: str | Path) -> tuple[int, int]:
    """Count input records and syntax-invalid JSON without interpreting requests."""
    count = 0
    malformed = 0
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            count += 1
            try:
                json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
    return count, malformed


def run_stream(centers: dict[str, Center], path: str | Path) -> None:
    """Candidate implements the customer capability here or in supporting modules."""
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                record = None
            request_id = record.get("request_id") if isinstance(record, dict) else None
            if not isinstance(request_id, str) or not request_id:
                request_id = None
            result = {"request_id": request_id, "status": "not_implemented"}
            print(json.dumps(result, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="costcanopy")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "process"):
        action = sub.add_parser(command)
        action.add_argument("--centers", required=True)
        action.add_argument("--operations", required=True)
    args = parser.parse_args(argv)
    try:
        centers = load_centers(args.centers)
        if args.command == "check":
            count, malformed = inspect_operations(args.operations)
            print(f"centers={len(centers)} records={count} malformed_json={malformed}")
        else:
            run_stream(centers, args.operations)
    except (CatalogError, OSError, UnicodeError) as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
