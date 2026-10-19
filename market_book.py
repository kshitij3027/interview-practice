"""Dealer quote snapshot CLI."""
from __future__ import annotations

import argparse
import json
import sys

from books.catalog import load_updates
from books.engine import QuoteEngine
from books.queries import QuoteRequest, read_queries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dealer quote operations")
    parser.add_argument("command", choices=("validate", "quote"))
    parser.add_argument("--events", required=True)
    parser.add_argument("--queries", required=True)
    options = parser.parse_args(argv)
    try:
        events = load_updates(options.events)
        queries = list(read_queries(options.queries))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2
    engine = QuoteEngine(events)
    if options.command == "validate":
        invalid = sum(isinstance(request, dict) for request in queries)
        print(f"validated {len(events)} unique updates, {len(engine.markets)} markets, {len(queries)} queries ({invalid} invalid)")
        return 0
    for request in queries:
        if isinstance(request, dict):
            output = request
        elif request.market not in engine.markets:
            output = {"request_id": request.request_id, "status": "invalid", "reason": "unknown_market"}
        else:
            output = engine.quote(request)
        print(json.dumps(output, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
