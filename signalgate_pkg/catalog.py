"""Validated immutable signature snapshot. The matching method is your task."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,40}\Z", re.ASCII)
_INT = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
_HEX = re.compile(r"(?:[0-9a-f]{2}){1,64}\Z", re.ASCII)
_MAX_MS = 10**12


class CatalogError(ValueError):
    """An entire snapshot is unusable."""


@dataclass(frozen=True)
class Signature:
    signature_id: str
    region: str
    priority: int
    valid_from_ms: int
    valid_until_ms: int
    pattern: bytes
    enabled: bool


@dataclass(frozen=True)
class Catalog:
    regions: frozenset[str]
    signatures: tuple[Signature, ...]


def valid_id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _parse_int(raw: str, max_value: int = _MAX_MS) -> int:
    if not _INT.fullmatch(raw):
        raise CatalogError(f"noncanonical integer: {raw!r}")
    value = int(raw)
    if value > max_value:
        raise CatalogError(f"integer exceeds {max_value}")
    return value


def _rows(path: str | Path, required: set[str]):
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                raise CatalogError(f"{path}: missing required headers")
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise CatalogError(f"{path}: duplicated header")
            for number, row in enumerate(reader, 2):
                if None in row or any(row.get(key) is None for key in required):
                    raise CatalogError(f"{path}: malformed row {number}")
                if any(not isinstance(row[key], str) or not row[key] for key in required):
                    raise CatalogError(f"{path}: missing cell at row {number}")
                yield row
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CatalogError(f"{path}: {exc}") from exc


def load_catalog(regions_path: str | Path, signatures_path: str | Path) -> Catalog:
    regions: set[str] = set()
    for row in _rows(regions_path, {"region_id"}):
        region = row["region_id"]
        if not valid_id(region):
            raise CatalogError(f"invalid region ID: {region!r}")
        regions.add(region)
    if not regions:
        raise CatalogError("no declared regions")

    sigs: dict[str, Signature] = {}
    required = {"signature_id", "region", "priority", "valid_from_ms", "valid_until_ms", "pattern_hex", "enabled"}
    for row in _rows(signatures_path, required):
        sid, region = row["signature_id"], row["region"]
        if not valid_id(sid) or (region != "*" and region not in regions):
            raise CatalogError(f"invalid signature ID or region at {sid!r}")
        start = _parse_int(row["valid_from_ms"])
        until = _parse_int(row["valid_until_ms"])
        if start >= until:
            raise CatalogError(f"empty effective window: {sid}")
        pattern_hex = row["pattern_hex"]
        if not _HEX.fullmatch(pattern_hex):
            raise CatalogError(f"invalid lowercase hex pattern: {sid}")
        if row["enabled"] not in {"true", "false"}:
            raise CatalogError(f"invalid enabled flag: {sid}")
        sig = Signature(sid, region, _parse_int(row["priority"], 1000), start, until,
                        bytes.fromhex(pattern_hex), row["enabled"] == "true")
        if sid in sigs and sigs[sid] != sig:
            raise CatalogError(f"conflicting signature replay: {sid}")
        sigs[sid] = sig
    return Catalog(frozenset(regions), tuple(sigs[key] for key in sorted(sigs)))
