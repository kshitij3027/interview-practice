#!/usr/bin/env python3
"""BundlePort batch interface."""

import argparse
import json
import sys
from pathlib import Path

from resolver.catalog import CatalogError, load_catalog, parse_request
from resolver.service import BundlePlanner


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate or plan offline bundles")
    parser.add_argument("command", choices=("validate", "plan"))
    parser.add_argument("--releases", required=True)
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--conflicts", required=True)
    parser.add_argument("--requests", required=True)
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.releases, args.requirements, args.conflicts)
        requests = Path(args.requests).read_text(encoding="utf-8").splitlines()
    except (CatalogError, OSError) as error:
        print(f"input error: {error}", file=sys.stderr)
        return 2
    if args.command == "validate":
        valid = sum(parse_request(line)[0] is not None for line in requests)
        print(json.dumps({"releases": len(catalog.releases), "requirements": len(catalog.requirements), "conflicts": len(catalog.conflicts), "requests": len(requests), "valid_requests": valid}, sort_keys=True))
        return 0
    planner = BundlePlanner(catalog)
    try:
        for line in requests:
            request, invalid = parse_request(line)
            print(json.dumps(invalid if invalid is not None else planner.plan_request(request), sort_keys=True))
    except NotImplementedError as error:
        print(error, file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
