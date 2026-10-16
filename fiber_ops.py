"""FiberWatch command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys

from netops.catalog import SnapshotError, load_snapshot
from netops.queries import QueryError, parse_query
from netops.resolver import NetworkAssessment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only fiber operations analysis")
    parser.add_argument("command", choices=("check", "assess"))
    parser.add_argument("--sites", required=True)
    parser.add_argument("--spans", required=True)
    parser.add_argument("--queries")
    args = parser.parse_args(argv)
    if args.command == "assess" and not args.queries:
        parser.error("assess requires --queries")
    try:
        snapshot = load_snapshot(args.sites, args.spans)
    except SnapshotError as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2
    if args.command == "check":
        print(json.dumps({"status": "ok", "sites": len(snapshot.sites), "spans": len(snapshot.spans)}, separators=(",", ":")))
        return 0
    service = NetworkAssessment(snapshot)
    known_spans = set(snapshot.spans)
    try:
        with open(args.queries, encoding="utf-8") as stream:
            for line in stream:
                try:
                    request = parse_query(line, known_spans)
                    result = service.assess(request)
                except QueryError as exc:
                    result = {"request_id": exc.request_id, "status": "invalid", "reason": exc.reason}
                print(json.dumps(result, separators=(",", ":")))
    except (OSError, UnicodeError) as exc:
        print(f"query stream error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

