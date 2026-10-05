#!/usr/bin/env python3
import argparse
import json
import sys

from queuepulse import BacklogResolver, load_queries, load_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(prog="queuepulse")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "resolve"):
        p = sub.add_parser(name)
        p.add_argument("--queues", required=True)
        p.add_argument("--events", required=True)
        p.add_argument("--queries", required=True)
    args = parser.parse_args()
    try:
        snapshot = load_snapshot(args.queues, args.events)
        queries = load_queries(args.queries)
    except ValueError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        bad = sum(q.error is not None for q in queries)
        print(f"validated {len(snapshot.queues)} queues / {snapshot.raw_revision_rows} raw revision rows / {snapshot.effective_posted_events} effective posted events / {len(queries)} queries ({bad} invalid query records)")
        return 0
    resolver = BacklogResolver(snapshot)
    for result in resolver.resolve_all(queries):
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
