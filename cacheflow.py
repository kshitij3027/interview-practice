"""Validate and replay a CacheFlow event tape."""
from __future__ import annotations

import argparse
import csv
import json
import sys

from cachekit.engine import CacheReplay
from cachekit.io import Event, load_catalog, load_event_tape, number


def main() -> int:
    parser = argparse.ArgumentParser(description="CacheFlow operational replay")
    parser.add_argument("command", choices=("validate", "replay"))
    parser.add_argument("--tenants", required=True)
    parser.add_argument("--objects", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--capacity-kb", required=True)
    args = parser.parse_args()
    try:
        capacity = number(args.capacity_kb, 0, 10**9)
        catalog = load_catalog(args.tenants, args.objects)
        entries, ordered = load_event_tape(args.events, catalog)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(json.dumps({"status": "valid", "tenants": len(catalog.tenants),
                          "objects": len(catalog.objects), "unique_events": len(ordered),
                          "input_lines": len(entries)}, separators=(",", ":")))
        return 0
    engine = CacheReplay(catalog, capacity)
    replies = {event.event_id: engine.apply(event) for event in ordered}
    for entry in entries:
        response = entry if isinstance(entry, dict) else replies[entry.event_id]
        print(json.dumps(response, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
