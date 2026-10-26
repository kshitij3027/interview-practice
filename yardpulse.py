"""YardPulse command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from yardkit.data import load_queries, load_snapshot
from yardkit.engine import YardEngine


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="YardPulse container handling investigations")
    parser.add_argument("command", choices=("validate", "resolve"))
    parser.add_argument("--yards", required=True)
    parser.add_argument("--containers", required=True)
    parser.add_argument("--links", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--queries", required=True)
    args = parser.parse_args(argv)
    try:
        snapshot = load_snapshot(args.yards, args.containers, args.links, args.events)
        requests = load_queries(args.queries, snapshot)
        if args.command == "validate":
            print(f"valid snapshot: {len(snapshot.yards)} yards, {len(snapshot.containers)} containers, {len(snapshot.links)} links, {len(snapshot.events)} events, {len(requests)} queries")
            return 0
        valid = [q for q in requests if "status" not in q]
        responses = iter(YardEngine(snapshot).answer_all(valid))
        for query in requests:
            answer = query if "status" in query else next(responses)
            print(json.dumps(answer, separators=(",", ":"), ensure_ascii=False))
        try:
            next(responses)
        except StopIteration:
            return 0
        raise ValueError("resolver returned too many answers")
    except (OSError, ValueError, StopIteration) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
