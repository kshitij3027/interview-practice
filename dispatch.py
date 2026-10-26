"""CLI entry point for one dispatch-planning snapshot."""
from __future__ import annotations

import argparse
import json
import sys

from assignment import plan
from records import SnapshotError, load_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a dispatch allocation from CSV snapshot files")
    parser.add_argument("--pods", default="fixtures/pods.csv")
    parser.add_argument("--responders", default="fixtures/responders.csv")
    parser.add_argument("--incidents", default="fixtures/incidents.csv")
    parser.add_argument("--routes", default="fixtures/routes.csv")
    parser.add_argument("--check-inputs", action="store_true", help="Validate the input files only")
    args = parser.parse_args(argv)

    try:
        snapshot = load_snapshot(args.pods, args.responders, args.incidents, args.routes)
    except SnapshotError as error:
        print(f"invalid_snapshot: {error}", file=sys.stderr)
        return 2

    if args.check_inputs:
        result = {"status": "valid_snapshot", "pods": len(snapshot.pods),
                  "responders": len(snapshot.responders), "incidents": len(snapshot.incidents),
                  "routes": len(snapshot.routes)}
    else:
        result = plan(snapshot)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
