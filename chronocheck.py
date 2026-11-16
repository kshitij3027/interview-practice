"""ChronoCheck snapshot, request and CLI scaffolding. The audit capability is unfinished."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z")
SIGNED = re.compile(r"(?:0|-?[1-9][0-9]*)\Z")
CLOCK_COLUMNS = ("clock_id", "tenant_id")
MEAS_COLUMNS = ("measurement_id", "revision", "op", "tenant_id", "clock_a", "clock_b", "delta_us")


def valid_id(value, request=False):
    return isinstance(value, str) and bool((REQUEST_ID if request else ID).fullmatch(value))


def integer(value, signed=False, maximum=None):
    pattern = SIGNED if signed else UINT
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError(f"invalid decimal integer {value!r}")
    result = int(value)
    if maximum is not None and abs(result) > maximum:
        raise ValueError("integer outside supported bounds")
    return result


def read_csv(path, columns):
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(columns) or set(reader.fieldnames) != set(columns):
            raise ValueError(f"{path}: unexpected CSV header")
        for line_no, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"{path}:{line_no}: malformed CSV row")
            yield row


def load_snapshot(clock_file, measurement_file):
    clocks = {}
    for row in read_csv(clock_file, CLOCK_COLUMNS):
        clock_id, tenant_id = row["clock_id"], row["tenant_id"]
        if not valid_id(clock_id) or not valid_id(tenant_id):
            raise ValueError("invalid clock declaration")
        if clock_id in clocks and clocks[clock_id] != tenant_id:
            raise ValueError(f"conflicting clock declaration: {clock_id}")
        clocks[clock_id] = tenant_id

    revisions = {}
    tenants = {}
    latest = {}
    for row in read_csv(measurement_file, MEAS_COLUMNS):
        mid, tenant = row["measurement_id"], row["tenant_id"]
        if not valid_id(mid) or not valid_id(tenant):
            raise ValueError("invalid measurement identity")
        revision = integer(row["revision"], maximum=2_000_000_000)
        if revision < 1:
            raise ValueError("revision must be positive")
        op, a, b, raw_delta = row["op"], row["clock_a"], row["clock_b"], row["delta_us"]
        if op == "upsert":
            if not valid_id(a) or not valid_id(b) or clocks.get(a) != tenant or clocks.get(b) != tenant:
                raise ValueError(f"unknown or cross-tenant measurement: {mid}")
            delta = integer(raw_delta, signed=True, maximum=1_000_000_000_000)
        elif op == "retract":
            if any((a, b, raw_delta)):
                raise ValueError("retraction fields must be blank")
            delta = None
        else:
            raise ValueError(f"invalid measurement operation: {op}")
        record = (op, tenant, a, b, delta)
        key = (mid, revision)
        if key in revisions and revisions[key] != record:
            raise ValueError(f"conflicting measurement revision: {mid}/{revision}")
        revisions[key] = record
        if mid in tenants and tenants[mid] != tenant:
            raise ValueError(f"measurement changed tenant: {mid}")
        tenants[mid] = tenant
        if mid not in latest or revision > latest[mid][0]:
            latest[mid] = (revision, record)
    active = {mid: item[1] for mid, item in latest.items() if item[1][0] == "upsert"}
    return clocks, active


def parse_request(line, clocks):
    try:
        data = json.loads(line)
    except (ValueError, TypeError):
        data = None
    rid = data.get("request_id") if isinstance(data, dict) else None
    rid = rid if valid_id(rid, request=True) else None
    error = {"request_id": rid, "status": "invalid", "reason": "invalid_query"}
    if not isinstance(data, dict) or rid is None:
        return None, error
    tenant, source, target = (data.get(k) for k in ("tenant_id", "source_clock", "target_clock"))
    if not all(valid_id(v) for v in (tenant, source, target)):
        return None, error
    if clocks.get(source) != tenant or clocks.get(target) != tenant:
        return None, {"request_id": rid, "status": "invalid", "reason": "unknown_clock"}
    return (rid, tenant, source, target), None


class ChronoCheck:
    def __init__(self, clocks, active_measurements):
        self.clocks = clocks
        self.active_measurements = active_measurements

    def assess(self, request):
        # Replace this placeholder with the customer-facing audit capability.
        rid, tenant, source, target = request
        return {"request_id": rid, "status": "not_implemented", "delta_us": None}


def run(argv=None):
    parser = argparse.ArgumentParser(description="Clock calibration snapshot audit")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "audit"):
        p = sub.add_parser(name)
        p.add_argument("--clocks", required=True)
        p.add_argument("--measurements", required=True)
        if name == "audit":
            p.add_argument("--requests", required=True)
    args = parser.parse_args(argv)
    try:
        clocks, active = load_snapshot(args.clocks, args.measurements)
        engine = ChronoCheck(clocks, active)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2
    if args.command == "check":
        print(f"validated {len(clocks)} clocks and {len(active)} active measurements")
        return 0
    try:
        with open(args.requests, encoding="utf-8") as inp:
            for line in inp:
                request, error = parse_request(line, clocks)
                result = error if error is not None else engine.assess(request)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    except (OSError, UnicodeError) as exc:
        print(f"request error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
