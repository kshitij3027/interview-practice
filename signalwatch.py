#!/usr/bin/env python3
"""SignalWatch command-line entry point."""
import argparse
import json
import sys

from signalwatch.catalog import load_catalog
from signalwatch.engine import SignatureScreen
from signalwatch.requests import Event, parse_event


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Incident signature screening")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "scan"):
        p = commands.add_parser(command)
        p.add_argument("--tenants", required=True)
        p.add_argument("--signatures", required=True)
        if command == "scan":
            p.add_argument("--events", required=True, help="JSONL path or - for stdin")
    args = parser.parse_args(argv)

    try:
        catalog = load_catalog(args.tenants, args.signatures)
    except (OSError, UnicodeError, ValueError, OverflowError) as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 2

    if args.command == "check":
        print(json.dumps({"tenants": len(catalog.tenants), "active_signatures": len(catalog.active)}, separators=(",", ":")))
        return 0

    screen = SignatureScreen(catalog)
    try:
        events = sys.stdin if args.events == "-" else open(args.events, encoding="utf-8")
        try:
            for line in events:
                parsed = parse_event(line)
                if isinstance(parsed, dict):
                    response = parsed
                elif parsed.tenant_id not in catalog.tenants:
                    response = {"event_id": parsed.event_id, "status": "invalid", "reason": "unknown_tenant"}
                else:
                    response = screen.evaluate(parsed)
                print(json.dumps(response, separators=(",", ":"), ensure_ascii=True))
        finally:
            if events is not sys.stdin:
                events.close()
    except (OSError, UnicodeError, NotImplementedError) as exc:
        print(f"screening error: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
