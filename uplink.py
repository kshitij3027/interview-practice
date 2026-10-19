"""SatLink interview starter: validated input loading and a command-line boundary.

The reconstruction engine itself is intentionally not supplied.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
LOWER_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z")
MAX_SIZE = 10**12
MAX_FRAGMENT = 65536
MAX_READ = 4096

class InputError(ValueError):
    """A snapshot cannot be loaded reliably."""

@dataclass(frozen=True)
class Asset:
    asset_id: str
    size: int
    expected_sha256: str | None

@dataclass(frozen=True)
class Fragment:
    capture_id: str
    asset_id: str
    offset: int
    data: bytes


def _identifier(value: object) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _integer(value: object, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def load_assets(path: str | Path) -> dict[str, Asset]:
    assets: dict[str, Asset] = {}
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["asset_id", "size", "expected_sha256"]:
            raise InputError("manifests.csv must have asset_id,size,expected_sha256 columns")
        for row_no, row in enumerate(reader, start=2):
            aid, size_s, sha = row["asset_id"], row["size"], row["expected_sha256"]
            if (not _identifier(aid) or not isinstance(size_s, str) or
                DECIMAL.fullmatch(size_s) is None or int(size_s) > MAX_SIZE or
                not isinstance(sha, str) or not (sha == "*" or LOWER_DIGEST.fullmatch(sha))):
                raise InputError(f"invalid manifest row {row_no}")
            asset = Asset(aid, int(size_s), None if sha == "*" else sha)
            if aid in assets and assets[aid] != asset:
                raise InputError(f"conflicting manifest for {aid}")
            assets[aid] = asset
    return assets


def load_fragments(path: str | Path, assets: dict[str, Asset]) -> list[Fragment]:
    captures: dict[str, Fragment] = {}
    with open(path, encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("fragment must be an object")
                cid, aid = record.get("capture_id"), record.get("asset_id")
                offset, encoded = record.get("offset"), record.get("payload_b64")
                if not _identifier(cid) or not _identifier(aid) or aid not in assets:
                    raise ValueError("invalid IDs")
                if not _integer(offset, 0, MAX_SIZE):
                    raise ValueError("invalid offset")
                if not isinstance(encoded, str) or any(ord(c) > 127 for c in encoded):
                    raise ValueError("invalid base64")
                payload = base64.b64decode(encoded, validate=True)
                if base64.b64encode(payload).decode("ascii") != encoded:
                    raise ValueError("noncanonical base64")
                if not 1 <= len(payload) <= MAX_FRAGMENT or offset + len(payload) > assets[aid].size:
                    raise ValueError("fragment outside asset or invalid length")
                fragment = Fragment(cid, aid, offset, payload)
                if cid in captures and captures[cid] != fragment:
                    raise ValueError("conflicting capture ID")
                captures[cid] = fragment
            except (ValueError, binascii.Error, TypeError) as exc:
                raise InputError(f"invalid fragment line {line_no}: {exc}") from exc
    return list(captures.values())


def query_id(value: object) -> str | None:
    if isinstance(value, dict) and _identifier(value.get("request_id")):
        return value["request_id"]
    return None


def parse_query(value: object) -> dict:
    if not isinstance(value, dict) or not _identifier(value.get("request_id")):
        raise ValueError("invalid request_id")
    if not _identifier(value.get("asset_id")) or value.get("kind") not in ("status", "read"):
        raise ValueError("invalid kind or asset_id")
    if value["kind"] == "read":
        start, end = value.get("start"), value.get("end")
        if (not _integer(start, 0, MAX_SIZE) or not _integer(end, 0, MAX_SIZE)
            or end < start or end - start > MAX_READ):
            raise ValueError("invalid range")
    return value


def iter_queries(path: str | Path) -> Iterator[tuple[str | None, dict | None]]:
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            try:
                raw = json.loads(line)
            except ValueError:
                yield None, None
                continue
            rid = query_id(raw)
            try:
                query = parse_query(raw)
            except ValueError:
                yield rid, None
            else:
                yield rid, query


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SatLink fragment-audit interview harness")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "audit"):
        sub = commands.add_parser(name)
        sub.add_argument("--manifests", required=True)
        sub.add_argument("--fragments", required=True)
        sub.add_argument("--queries", required=True)
    args = parser.parse_args(argv)
    try:
        assets = load_assets(args.manifests)
        fragments = load_fragments(args.fragments, assets)
        if args.command == "validate":
            print(json.dumps({"assets": len(assets), "unique_captures": len(fragments),
                              "query_lines": sum(1 for _ in iter_queries(args.queries))},
                             sort_keys=True))
            return 0
        from replay_engine import AuditEngine
        engine = AuditEngine(assets, fragments)
        for request_id, query in iter_queries(args.queries):
            if query is None:
                result = {"request_id": request_id, "status": "invalid", "reason": "invalid_request"}
            elif query["asset_id"] not in assets:
                result = {"request_id": request_id, "status": "invalid", "reason": "unknown_asset"}
            elif query["kind"] == "read" and query["end"] > assets[query["asset_id"]].size:
                result = {"request_id": request_id, "status": "invalid", "reason": "invalid_request"}
            else:
                result = engine.answer(query)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (InputError, OSError, NotImplementedError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
