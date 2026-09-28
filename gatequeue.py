from __future__ import annotations

import argparse
import json
import sys

from readiness.loader import DatasetError, load_queries, load_snapshot
from readiness.planner import ReadinessResolver


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gatequeue")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "resolve"):
        p = sub.add_parser(command)
        p.add_argument("--workflows", required=True)
        p.add_argument("--tasks", required=True)
        p.add_argument("--dependencies", required=True)
        p.add_argument("--events", required=True)
        p.add_argument("--queries", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        snapshot = load_snapshot(
            args.workflows, args.tasks, args.dependencies, args.events
        )
        queries = load_queries(args.queries)
    except (DatasetError, OSError) as exc:
        print(f"dataset error: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(
            "validated "
            f"{len(snapshot.workflows)} workflows / "
            f"{len(snapshot.tasks)} tasks / "
            f"{len(snapshot.dependencies)} dependencies / "
            f"{len(snapshot.events)} deduplicated events / "
            f"{len(queries)} queries"
        )
        return 0

    resolver = ReadinessResolver(snapshot)
    try:
        results = resolver.resolve_all(queries)
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    for result in results:
        print(json.dumps(result, separators=(",", ":"), sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
