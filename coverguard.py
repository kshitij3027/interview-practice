"""ProofSpan customer-evidence auditor: complete input handling, unfinished decision capability."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]+\Z", re.ASCII)
UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
MAX_TIME = 10**12


def valid_id(value: object, limit: int = 48) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= limit and ID.fullmatch(value) is not None


def csv_integer(value: str, lo: int, hi: int, field: str) -> int:
    if not isinstance(value, str) or UINT.fullmatch(value) is None:
        raise ValueError(f"invalid {field}: expected canonical unsigned integer")
    number = int(value)
    if not lo <= number <= hi:
        raise ValueError(f"out-of-range {field}")
    return number


def read_table(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(columns) or set(reader.fieldnames) != set(columns):
            raise ValueError(f"{path}: expected CSV header {','.join(columns)}")
        rows = []
        for number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}:{number}: malformed CSV row")
            rows.append(row)
        return rows


@dataclass(frozen=True)
class Snapshot:
    scopes: dict[str, str]
    probes: dict[str, tuple[str, str]]
    # observation ID -> (probe ID, start ms, end ms), after latest-revision selection
    active: dict[str, tuple[str, int, int]]


def load_snapshot(scopes_file: Path, probes_file: Path, observations_file: Path) -> Snapshot:
    scopes: dict[str, str] = {}
    for row in read_table(scopes_file, ("scope_id", "site_name")):
        scope_id, site_name = row["scope_id"], row["site_name"]
        if not valid_id(scope_id) or not (1 <= len(site_name) <= 80) or any(not (32 <= ord(c) <= 126) for c in site_name):
            raise ValueError("invalid scope declaration")
        previous = scopes.setdefault(scope_id, site_name)
        if previous != site_name:
            raise ValueError(f"conflicting scope ID: {scope_id}")

    probes: dict[str, tuple[str, str]] = {}
    for row in read_table(probes_file, ("probe_id", "scope_id", "vendor_id")):
        probe_id, scope_id, vendor_id = row["probe_id"], row["scope_id"], row["vendor_id"]
        if not all(valid_id(v) for v in (probe_id, scope_id, vendor_id)) or scope_id not in scopes:
            raise ValueError("invalid probe declaration or unknown scope")
        value = (scope_id, vendor_id)
        if probe_id in probes and probes[probe_id] != value:
            raise ValueError(f"conflicting probe ID: {probe_id}")
        probes[probe_id] = value

    seen: dict[tuple[str, int], tuple[str, str, str, str]] = {}
    latest: dict[str, tuple[int, str, str, int, int]] = {}
    for row in read_table(observations_file, ("observation_id", "revision", "op", "probe_id", "start_ms", "end_ms")):
        observation_id = row["observation_id"]
        if not valid_id(observation_id):
            raise ValueError("invalid observation ID")
        rev = csv_integer(row["revision"], 1, 2_000_000_000, "revision")
        op = row["op"]
        if op == "retract":
            if any(row[column] != "" for column in ("probe_id", "start_ms", "end_ms")):
                raise ValueError("retraction must have blank business fields")
            probe, start, end = "", -1, -1
        elif op == "upsert":
            probe = row["probe_id"]
            if not valid_id(probe) or probe not in probes:
                raise ValueError("unknown probe or invalid probe ID")
            start = csv_integer(row["start_ms"], 0, MAX_TIME, "start_ms")
            end = csv_integer(row["end_ms"], 0, MAX_TIME, "end_ms")
            if start >= end:
                raise ValueError("empty or reversed observation interval")
        else:
            raise ValueError("invalid observation operation")

        signature = (op, probe, row["start_ms"], row["end_ms"])
        key = (observation_id, rev)
        if key in seen and seen[key] != signature:
            raise ValueError(f"conflicting observation revision: {observation_id}/{rev}")
        seen[key] = signature
        if observation_id not in latest or rev > latest[observation_id][0]:
            latest[observation_id] = (rev, op, probe, start, end)

    active = {observation_id: (probe, start, end)
              for observation_id, (rev, op, probe, start, end) in latest.items()
              if op == "upsert"}
    return Snapshot(scopes, probes, active)


def parse_audit(line: str) -> tuple[dict | None, dict | None]:
    try:
        item = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, {"audit_id": None, "status": "invalid", "reason": "invalid_audit"}
    audit_id = item.get("audit_id") if isinstance(item, dict) else None
    safe_id = audit_id if valid_id(audit_id, 128) else None
    invalid = {"audit_id": safe_id, "status": "invalid", "reason": "invalid_audit"}
    if not isinstance(item, dict) or safe_id is None or not valid_id(item.get("scope_id")):
        return None, invalid
    for field in ("from_ms", "until_ms", "min_vendors"):
        if type(item.get(field)) is not int:
            return None, invalid
    if not (0 <= item["from_ms"] < item["until_ms"] <= MAX_TIME and 1 <= item["min_vendors"] <= 4):
        return None, invalid
    return item, None


class CoverageAudit:
    """Implement the customer-facing assessment in evaluate()."""

    def __init__(self, snapshot: Snapshot) -> None:
        self.snapshot = snapshot

    def evaluate(self, audit: dict) -> dict:
        # Valid input is wired end-to-end; business calculations are for the interview.
        return {"audit_id": audit["audit_id"], "status": "unimplemented"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ProofSpan vendor evidence coverage audit")
    parser.add_argument("--scopes", default="fixtures/scopes.csv")
    parser.add_argument("--probes", default="fixtures/probes.csv")
    parser.add_argument("--observations", default="fixtures/observations.csv")
    parser.add_argument("--audits", default="fixtures/audits.jsonl", help="JSONL path, or '-' for stdin")
    args = parser.parse_args(argv)
    try:
        snapshot = load_snapshot(Path(args.scopes), Path(args.probes), Path(args.observations))
    except (ValueError, OSError, csv.Error, UnicodeError) as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 2
    evaluator = CoverageAudit(snapshot)
    try:
        if args.audits == "-":
            source = sys.stdin
        else:
            source = open(args.audits, "r", encoding="utf-8")
        with source if source is not sys.stdin else _NoClose(source) as handle:
            for line in handle:
                audit, error = parse_audit(line)
                if error is not None:
                    result = error
                elif audit["scope_id"] not in snapshot.scopes:
                    result = {"audit_id": audit["audit_id"], "status": "invalid", "reason": "unknown_scope"}
                else:
                    result = evaluator.evaluate(audit)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    except (OSError, UnicodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    return 0


class _NoClose:
    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        return self.stream

    def __exit__(self, *_):
        return False


if __name__ == "__main__":
    raise SystemExit(main())
