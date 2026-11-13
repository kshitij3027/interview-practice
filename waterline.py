#!/usr/bin/env python3
"""WaterLine customer exercise: validated input and a deliberately unfinished impact review."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

_IDENT = re.compile(r"^[A-Za-z0-9_-]{1,48}$")
_QUERY_IDENT = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class CatalogError(ValueError):
    pass


def _uid(value: object, label: str, query: bool = False) -> str:
    if not isinstance(value, str) or not (_QUERY_IDENT if query else _IDENT).fullmatch(value):
        raise ValueError(f"invalid {label}")
    return value


def _uint(value: str, label: str, max_value: int) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError(f"invalid {label}")
    number = int(value)
    if number > max_value:
        raise ValueError(f"out of range {label}")
    return number


def _rows(path: str, expected: tuple[str, ...]):
    with open(path, newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or len(reader.fieldnames) != len(expected) or set(reader.fieldnames) != set(expected):
            raise CatalogError(f"{path}: expected columns {', '.join(expected)}")
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise CatalogError(f"{path}:{line}: malformed CSV row")
            yield line, row


def load_catalog(nodes_path: str, pipes_path: str):
    nodes = {}
    pipes = {}
    try:
        for line, row in _rows(nodes_path, ("node_id", "source", "meters", "demand_lps", "critical")):
            node = _uid(row["node_id"], "node_id")
            if row["source"] not in ("yes", "no"):
                raise ValueError("source must be yes/no")
            meters = _uint(row["meters"], "meters", 1_000_000)
            demand = _uint(row["demand_lps"], "demand_lps", 1_000_000_000)
            critical = _uint(row["critical"], "critical", 1_000_000)
            if critical > meters or (row["source"] == "yes" and (meters or demand or critical)):
                raise ValueError("invalid node counts")
            record = (row["source"] == "yes", meters, demand, critical)
            if node in nodes and nodes[node] != record:
                raise ValueError(f"conflicting node {node}")
            nodes[node] = record
        for line, row in _rows(pipes_path, ("pipe_id", "a", "b")):
            pipe = _uid(row["pipe_id"], "pipe_id")
            a, b = _uid(row["a"], "a"), _uid(row["b"], "b")
            if a not in nodes or b not in nodes:
                raise ValueError(f"unknown endpoint for {pipe}")
            record = (a, b)
            if pipe in pipes and pipes[pipe] != record:
                raise ValueError(f"conflicting pipe {pipe}")
            pipes[pipe] = record
    except (ValueError, UnicodeError, OSError, csv.Error) as exc:
        raise CatalogError(str(exc)) from exc
    return nodes, pipes


def parse_query(raw: str, pipes: dict):
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return None, {"request_id": None, "status": "invalid", "reason": "invalid_query"}
    recovered = None
    if isinstance(obj, dict) and isinstance(obj.get("request_id"), str) and _QUERY_IDENT.fullmatch(obj["request_id"]):
        recovered = obj["request_id"]
    if not isinstance(obj, dict):
        return None, {"request_id": None, "status": "invalid", "reason": "invalid_query"}
    ids = obj.get("close_pipes")
    if recovered is None or not isinstance(ids, list) or len(ids) > 2 or any(not isinstance(x, str) or not _IDENT.fullmatch(x) for x in ids):
        return None, {"request_id": recovered, "status": "invalid", "reason": "invalid_query"}
    if any(x not in pipes for x in ids):
        return None, {"request_id": recovered, "status": "invalid", "reason": "unknown_pipe"}
    return {"request_id": recovered, "close_pipes": list(dict.fromkeys(ids))}, None


class WaterLine:
    def __init__(self, nodes: dict, pipes: dict):
        self.nodes = nodes
        self.pipes = pipes

    def review(self, query: dict) -> dict:
        # Starter placeholder. Replace with correct, scalable customer behavior.
        return {
            "request_id": query["request_id"], "status": "ok",
            "affected_meters": 0, "affected_demand_lps": 0,
            "affected_critical": 0,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review hypothetical water-network pipe closures")
    parser.add_argument("--nodes", default="fixtures/nodes.csv")
    parser.add_argument("--pipes", default="fixtures/pipes.csv")
    parser.add_argument("--requests", default="fixtures/requests.jsonl")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        nodes, pipes = load_catalog(args.nodes, args.pipes)
    except CatalogError as exc:
        print(f"catalog error: {exc}", file=sys.stderr)
        return 2
    if args.validate_only:
        print(json.dumps({"nodes": len(nodes), "pipes": len(pipes)}, separators=(",", ":")))
        return 0
    engine = WaterLine(nodes, pipes)
    try:
        with open(args.requests, encoding="utf-8") as stream:
            for raw in stream:
                query, error = parse_query(raw, pipes)
                result = error if error is not None else engine.review(query)
                print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))
    except (UnicodeError, OSError) as exc:
        print(f"request stream error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
