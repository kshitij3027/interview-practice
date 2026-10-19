"""PromiseClock CLI for immutable support-operation snapshots."""
from __future__ import annotations

import argparse
import json
import sys

from slaops.data import SnapshotError, load_snapshot
from slaops.requests import QueryError, parse_request
from slaops.resolver import PromiseClock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Support SLA operations")
    parser.add_argument("command", choices=("check", "assess"))
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--blackouts", required=True)
    parser.add_argument("--tickets", required=True)
    parser.add_argument("--pauses", required=True)
    parser.add_argument("--queries")
    args = parser.parse_args(argv)
    if args.command == "assess" and not args.queries:
        parser.error("assess requires --queries")
    try:
        snapshot = load_snapshot(args.coverage, args.blackouts, args.tickets, args.pauses)
    except SnapshotError as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2
    if args.command == "check":
        print(json.dumps({"status": "ok", "regions": len({i.owner for i in snapshot.coverage.values()}),
                          "coverage": len(snapshot.coverage), "blackouts": len(snapshot.blackouts),
                          "tickets": len(snapshot.tickets), "pauses": len(snapshot.pauses)}, separators=(",", ":")))
        return 0
    resolver = PromiseClock(snapshot)
    try:
        with open(args.queries, encoding="utf-8") as handle:
            for line in handle:
                try:
                    query = parse_request(line, set(snapshot.tickets))
                    response = resolver.resolve(query)
                except QueryError as exc:
                    response = {"request_id": exc.request_id, "status": "invalid", "reason": exc.reason}
                print(json.dumps(response, separators=(",", ":")))
    except (OSError, UnicodeError) as exc:
        print(f"query error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
