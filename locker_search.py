from __future__ import annotations

import argparse
import json
import sys

from locator.finder import LockerFinder
from locator.loader import DataValidationError, load_lockers, load_queries


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="locker_search.py")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "search"):
        p = sub.add_parser(name)
        p.add_argument("--lockers", required=True)
        p.add_argument("--queries", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        lockers = load_lockers(args.lockers)
        queries = load_queries(args.queries)
    except (OSError, DataValidationError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        invalid = sum(1 for record in queries if record.query is None)
        print(f"validated {len(lockers)} lockers / {len(queries)} queries ({invalid} invalid query records)")
        return 0
    finder = LockerFinder(lockers)
    try:
        results = finder.resolve_all(queries)
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    for result in results:
        print(json.dumps(result, separators=(",", ":"), sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
