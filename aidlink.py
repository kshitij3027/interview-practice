"""AidLink interview CLI; no external dependencies."""
from __future__ import annotations

import argparse
import json
import sys

from aidlink_pkg.data import CatalogError, load_catalog, parse_request
from aidlink_pkg.planner import plan


def emit(item):
    print(json.dumps(item, separators=(",", ":"), ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description="AidLink planning workspace")
    parser.add_argument("command", choices=("check", "plan"))
    parser.add_argument("--depots", required=True)
    parser.add_argument("--clinics", required=True)
    parser.add_argument("--lanes", required=True)
    parser.add_argument("--requests", required=True)
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.depots, args.clinics, args.lanes)
        valid = invalid = 0
        with open(args.requests, encoding="utf-8") as stream:
            for line in stream:
                rid, request, error = parse_request(line, catalog)
                if error:
                    invalid += 1
                    if args.command == "plan":
                        emit({"request_id": rid, "status": "invalid", "reason": error})
                    continue
                valid += 1
                if args.command == "plan":
                    result = plan(catalog, request)
                    emit(result if result is not None else {"request_id": rid, "status": "not_implemented"})
        if args.command == "check":
            emit({"status": "ok", "depots": len(catalog.depots), "clinics": len(catalog.clinics), "lanes": len(catalog.lanes), "valid_requests": valid, "invalid_requests": invalid})
        return 0
    except (CatalogError, OSError, UnicodeError) as exc:
        print(f"catalog/input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
