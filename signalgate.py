"""SignalGate snapshot CLI. `scan` requires the candidate's implementation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from signalgate_pkg.catalog import CatalogError, load_catalog
from signalgate_pkg.requests import RequestError, parse_request
from signalgate_pkg.scanner import SignalScanner


def process(command: str, regions_file: str, signatures_file: str, requests_file: str) -> int:
    try:
        catalog = load_catalog(regions_file, signatures_file)
        scanner = SignalScanner(catalog)
        valid_count = 0
        invalid_count = 0
        with open(requests_file, encoding="utf-8") as stream:
            for line in stream:
                try:
                    request = parse_request(line, catalog.regions)
                except RequestError as exc:
                    invalid_count += 1
                    if command == "scan":
                        print(json.dumps({"request_id": exc.request_id, "status": "invalid", "reason": exc.reason}, separators=(",", ":")))
                    continue
                valid_count += 1
                if command == "scan":
                    print(json.dumps(scanner.scan(request), separators=(",", ":")))
        if command == "check":
            print(f"Snapshot OK: {len(catalog.regions)} regions, {len(catalog.signatures)} signatures, "
                  f"{valid_count} valid requests, {invalid_count} invalid requests", file=sys.stderr)
        return 0
    except (CatalogError, OSError, UnicodeError, ValueError) as exc:
        print(f"Snapshot invalid: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect an immutable binary signature snapshot")
    parser.add_argument("command", choices=["check", "scan"])
    parser.add_argument("--regions", required=True, type=Path)
    parser.add_argument("--signatures", required=True, type=Path)
    parser.add_argument("--requests", required=True, type=Path)
    args = parser.parse_args(argv)
    return process(args.command, args.regions, args.signatures, args.requests)


if __name__ == "__main__":
    raise SystemExit(main())
