#!/usr/bin/env python3
"""PulseRank command-line entry point."""
import argparse
import json
import sys
from pulserank.engine import LatencyAudit
from pulserank.input import SnapshotError, load_snapshot, parse_query


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regional API latency audit")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "audit"):
        p = commands.add_parser(name)
        p.add_argument("--scopes", required=True)
        p.add_argument("--observations", required=True)
        if name == "audit":
            p.add_argument("--queries", required=True)
    args = parser.parse_args(argv)
    try:
        snapshot = load_snapshot(args.scopes, args.observations)
    except SnapshotError as exc:
        print(f"snapshot_error: {exc}", file=sys.stderr)
        return 2
    if args.command == "check":
        print(json.dumps({"status": "ok", "scopes": len(snapshot.scopes),
                          "rows": snapshot.rows_seen, "logical_requests": len(snapshot.latest),
                          "live_requests": len(snapshot.live)}, separators=(",", ":")))
        return 0
    engine = LatencyAudit(snapshot)
    try:
        with open(args.queries, encoding="utf-8") as source:
            for raw in source:
                parsed = parse_query(raw, snapshot.scopes)
                result = engine.assess(parsed) if not isinstance(parsed, dict) else parsed
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    except (OSError, UnicodeError) as exc:
        print(f"query_input_error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
