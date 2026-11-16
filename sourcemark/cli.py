"""SourceMark command line interface."""

import argparse
import json
import sys
from pathlib import Path
from .catalog import Catalog, CatalogError
from .contracts import parse_query, QueryError, invalid_response
from .engine import SourceAttributor


def main(argv=None):
    parser = argparse.ArgumentParser(description="SourceMark supplier-lot review")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "assess"):
        item = sub.add_parser(command)
        item.add_argument("--lots", required=True)
        item.add_argument("--mixes", required=True)
        item.add_argument("--membership", required=True)
        if command == "assess":
            item.add_argument("--requests", required=True)
    args = parser.parse_args(argv)
    try:
        catalog = Catalog.load(args.lots, args.mixes, args.membership)
        if args.command == "check":
            print(json.dumps({"sites": len(catalog.sites), "lots": len(catalog.lots),
                              "mixes": len(catalog.mixes), "memberships": catalog.membership_count}, separators=(",", ":")))
            return 0
        engine = SourceAttributor(catalog)
        with Path(args.requests).open("r", encoding="utf-8") as handle:
            for physical_line in handle:
                try:
                    raw = json.loads(physical_line)
                except (ValueError, UnicodeError):
                    raw = None
                try:
                    result = engine.assess(parse_query(raw, catalog))
                except QueryError as exc:
                    result = invalid_response(exc)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
        return 0
    except (CatalogError, OSError, UnicodeError) as exc:
        print(f"SourceMark: {exc}", file=sys.stderr)
        return 2
