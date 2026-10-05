from __future__ import annotations

import argparse
import json
import sys

from bundlelock.catalog import Catalog
from bundlelock.io import iter_request_payloads, parse_request
from bundlelock.planner import CompatibilityPlanner


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="compat_plan.py")
    sub = root.add_subparsers(dest="command", required=True)
    for name in ("validate", "resolve"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--packages", required=True)
        cmd.add_argument("--versions", required=True)
        cmd.add_argument("--dependencies", required=True)
        cmd.add_argument("--installed", required=True)
        cmd.add_argument("--requests", required=True)
    return root


def load(args) -> Catalog:
    return Catalog.load(args.packages, args.versions, args.dependencies, args.installed)


def main() -> int:
    args = parser().parse_args()
    try:
        catalog = load(args)
    except (OSError, ValueError) as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        total = invalid = 0
        for _, payload, decoded in iter_request_payloads(args.requests):
            total += 1
            if not decoded:
                invalid += 1
                continue
            try:
                parse_request(payload, catalog)
            except ValueError:
                invalid += 1
        print(
            f"validated {len(catalog.packages)} packages / "
            f"{len(catalog.releases)} releases / "
            f"{catalog.dependency_count()} dependencies / "
            f"{len(catalog.installed)} installed / "
            f"{total} requests ({invalid} invalid request records)"
        )
        return 0

    planner = CompatibilityPlanner(catalog)
    for request_id, payload, decoded in iter_request_payloads(args.requests):
        if not decoded:
            print(json.dumps({"request_id": request_id, "status": "invalid", "reason": "invalid_request"}))
            continue
        try:
            request = parse_request(payload, catalog)
        except ValueError:
            print(json.dumps({"request_id": request_id, "status": "invalid", "reason": "invalid_request"}))
            continue
        try:
            result = planner.plan(request)
        except NotImplementedError as exc:
            print(str(exc), file=sys.stderr)
            return 3
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
