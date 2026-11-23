#!/usr/bin/env python3
"""BatchPath CLI."""

from __future__ import annotations

import argparse
import json
import sys

from batchpath.catalog import CatalogError, load_catalog
from batchpath.engine import BatchPath
from batchpath.requests import parse_query


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BatchPath snapshot tools")
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("validate", "assess"):
        command = commands.add_parser(action)
        command.add_argument("--datasets", required=True)
        command.add_argument("--links", required=True)
        if action == "assess":
            command.add_argument("--queries", required=True)
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.datasets, args.links)
    except CatalogError as error:
        print(f"catalog error: {error}", file=sys.stderr)
        return 2
    if args.action == "validate":
        print(json.dumps({"datasets": len(catalog.datasets), "active_links": len(catalog.active_links), "tenants": len(catalog.tenants)}, separators=(",", ":")))
        return 0
    assessor = BatchPath(catalog)
    try:
        with open(args.queries, encoding="utf-8") as stream:
            for line in stream:
                query, error = parse_query(line)
                result = error if error is not None else assessor.assess(query)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=True))
    except (OSError, UnicodeError) as error:
        print(f"query input error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
