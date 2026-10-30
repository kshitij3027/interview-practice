"""JSON-lines interface for charge demand audits."""
import argparse
import json
import sys
from .engine import DemandSnapshot
from .io import CatalogError, QueryError, load_catalog, parse_query


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate charging demand windows")
    parser.add_argument("command", choices=["assess", "check-inputs"])
    parser.add_argument("--sites", default="fixtures/sites.csv")
    parser.add_argument("--sessions", default="fixtures/sessions.csv")
    parser.add_argument("--queries", default="fixtures/queries.jsonl")
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.sites, args.sessions)
    except CatalogError as exc:
        print(f"invalid catalog: {exc}", file=sys.stderr)
        return 2
    if args.command == "check-inputs":
        print(json.dumps({"sites": len(catalog.sites), "revisions": len(catalog.revisions)}, separators=(",", ":")))
        return 0
    snapshot = DemandSnapshot(catalog)
    try:
        with open(args.queries, encoding="utf-8") as stream:
            for line in stream:
                try:
                    request = parse_query(line, catalog.sites)
                except QueryError as exc:
                    result = {"request_id": exc.request_id, "status": "invalid", "reason": exc.reason}
                else:
                    result = snapshot.evaluate(request)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    except (OSError, UnicodeError) as exc:
        print(f"unable to read queries: {exc}", file=sys.stderr)
        return 2
    return 0
