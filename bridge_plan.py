from __future__ import annotations

import argparse
import json

from migration.catalog import Catalog
from migration.io import DatasetError, load_adapters, load_requests, load_schemas, validate_dataset
from migration.planner import MigrationPlanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BridgePlan schema migration planner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("validate", "plan"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--schemas", required=True)
        sub.add_argument("--adapters", required=True)
        sub.add_argument("--requests", required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            summary = validate_dataset(args.schemas, args.adapters, args.requests)
            print(json.dumps({"status": "ok", **summary}, sort_keys=True))
            return 0

        schemas = load_schemas(args.schemas)
        adapters = load_adapters(args.adapters, schemas)
        requests = load_requests(args.requests)
        planner = MigrationPlanner(Catalog(schemas, adapters))
        for request in requests:
            print(json.dumps(planner.plan(request), sort_keys=True))
        return 0
    except DatasetError as exc:
        print(json.dumps({"status": "dataset_error", "message": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
