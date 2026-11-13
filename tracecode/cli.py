"""Command-line interface. Print one response per physical scan line."""
from __future__ import annotations

import argparse
import json
import sys

from .catalog import CatalogError, load_catalog
from .contracts import parse_scan
from .engine import SerialRecovery


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manufacturer serial-label audit")
    parser.add_argument("command", choices=["check", "recover"])
    parser.add_argument("--models", required=True)
    parser.add_argument("--ranges", required=True)
    parser.add_argument("--scans")
    args = parser.parse_args(argv)
    if args.command == "recover" and not args.scans:
        parser.error("recover requires --scans")
    try:
        catalog = load_catalog(args.models, args.ranges)
        if args.command == "check":
            print(json.dumps({"status": "valid", "models": len(catalog.models),
                              "ranges": sum(map(len, catalog.bands.values()))}, separators=(",", ":")))
            return 0
        engine = SerialRecovery(catalog)
        with open(args.scans, encoding="utf-8") as stream:
            for line in stream:
                scan, error = parse_scan(line, catalog)
                result = error if error is not None else engine.recover(scan)
                print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (CatalogError, OSError, UnicodeError, ValueError) as exc:
        print(f"TraceCode input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
