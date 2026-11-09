"""Command-line entry point for independent access-review queries."""
import argparse
import json
import sys
from pathlib import Path

from .data import InvalidCatalog, load_snapshot, parse_query
from .engine import VaultScope


def run(argv=None):
    parser = argparse.ArgumentParser(description="VaultScope access audit")
    parser.add_argument("audit", choices=["audit"])
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--queries", required=True)
    args = parser.parse_args(argv)
    try:
        snapshot = load_snapshot(args.catalog)
    except (InvalidCatalog, OSError, UnicodeError, ValueError) as error:
        print(f"invalid catalog: {error}", file=sys.stderr)
        return 2
    auditor = VaultScope(snapshot)
    try:
        with Path(args.queries).open(encoding="utf-8") as stream:
            for line in stream:
                query, error = parse_query(line)
                if error is not None:
                    response = error
                elif query["user_id"] not in snapshot["users"] or query["resource_id"] not in snapshot["resources"]:
                    response = {"query_id": query["query_id"], "status": "invalid", "reason": "unknown_entity"}
                elif snapshot["users"][query["user_id"]] != snapshot["resources"][query["resource_id"]]:
                    response = {"query_id": query["query_id"], "status": "invalid", "reason": "tenant_mismatch"}
                else:
                    response = auditor.decide(query)
                print(json.dumps(response, ensure_ascii=False, separators=(",", ":")))
    except (OSError, UnicodeError) as error:
        print(f"could not read queries: {error}", file=sys.stderr)
        return 2
    return 0
