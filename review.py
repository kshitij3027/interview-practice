#!/usr/bin/env python3
"""One response for each physical query line; catalog failures terminate before output."""
from __future__ import annotations

import argparse
import json
import sys

from airspace.engine import AirspaceReview
from airspace.io import CatalogError, QueryError, load_zones, parse_query, read_request_id


def main() -> int:
    parser = argparse.ArgumentParser(description="SkyParcel waypoint restriction review")
    parser.add_argument("--zones", required=True, help="JSONL zone snapshot")
    parser.add_argument("--queries", required=True, help="JSONL waypoint review requests")
    args = parser.parse_args()

    try:
        resolver = AirspaceReview(load_zones(args.zones))
    except CatalogError as e:
        print(f"catalog_error: {e}", file=sys.stderr)
        return 2

    try:
        with open(args.queries, encoding="utf-8") as f:
            for line in f:
                try:
                    query = parse_query(line)
                except QueryError:
                    response = {"request_id": read_request_id(line), "status": "error", "error": "invalid_request"}
                else:
                    response = {"request_id": query.request_id, "status": "ok", "zone_ids": resolver.select(query)}
                print(json.dumps(response, separators=(",", ":"), ensure_ascii=True))
    except (OSError, UnicodeError) as e:
        print(f"query_file_error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
