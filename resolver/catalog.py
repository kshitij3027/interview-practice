"""Immutable bundle catalog input handling and validation."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

PLATFORMS = frozenset({"linux-x64", "mac-arm64"})


class CatalogError(ValueError):
    pass


def version(text: str) -> tuple[int, int, int]:
    if not isinstance(text, str):
        raise ValueError("version must be text")
    parts = text.split(".")
    if len(parts) != 3 or any(not p or not p.isascii() or not p.isdecimal() or (len(p) > 1 and p[0] == "0") for p in parts):
        raise ValueError(f"bad version: {text!r}")
    return tuple(int(p) for p in parts)


def version_range(lower: str, upper: str) -> None:
    if version(lower) >= version(upper):
        raise ValueError("empty version range")


@dataclass(frozen=True)
class Release:
    name: str
    version: str
    platform: str
    download_kb: int
    active: bool


@dataclass(frozen=True)
class Requirement:
    parent_name: str
    parent_version: str
    target_name: str
    min_version: str
    max_version_exclusive: str


@dataclass(frozen=True)
class Catalog:
    releases: dict[tuple[str, str], Release]
    requirements: tuple[Requirement, ...]
    conflicts: frozenset[tuple[tuple[str, str], tuple[str, str]]]


def _rows(path: str, expected: tuple[str, ...]):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(reader.fieldnames) != set(expected) or len(reader.fieldnames) != len(expected):
            raise CatalogError(f"unexpected columns in {path}")
        for index, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise CatalogError(f"bad CSV row {path}:{index}")
            yield index, row


def _name(text: str) -> str:
    if not isinstance(text, str) or not text or text.strip() != text or not all(c.isascii() and (c.isalnum() or c in "-_") for c in text):
        raise ValueError(f"bad name: {text!r}")
    return text


def load_catalog(releases_path: str, requirements_path: str, conflicts_path: str) -> Catalog:
    releases: dict[tuple[str, str], Release] = {}
    requirements: set[Requirement] = set()
    conflicts: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    try:
        for _, r in _rows(releases_path, ("name", "version", "platform", "download_kb", "active")):
            _name(r["name"])
            version(r["version"])
            if r["platform"] not in PLATFORMS | {"*"}:
                raise ValueError("bad release platform")
            kb = r["download_kb"]
            if not kb.isascii() or not kb.isdecimal() or int(kb) <= 0:
                raise ValueError("invalid download size")
            if r["active"] not in ("true", "false"):
                raise ValueError("invalid active flag")
            item = Release(r["name"], r["version"], r["platform"], int(kb), r["active"] == "true")
            key = (item.name, item.version)
            if key in releases and releases[key] != item:
                raise CatalogError(f"conflicting release replay {key}")
            releases[key] = item
        for _, r in _rows(requirements_path, ("parent_name", "parent_version", "target_name", "min_version", "max_version_exclusive")):
            _name(r["parent_name"])
            _name(r["target_name"])
            version(r["parent_version"])
            version_range(r["min_version"], r["max_version_exclusive"])
            item = Requirement(**r)
            if (item.parent_name, item.parent_version) not in releases:
                raise ValueError("requirement parent not found")
            requirements.add(item)
        for _, r in _rows(conflicts_path, ("name", "version", "other_name", "other_version")):
            _name(r["name"])
            _name(r["other_name"])
            version(r["version"])
            version(r["other_version"])
            a, b = (r["name"], r["version"]), (r["other_name"], r["other_version"])
            if a not in releases or b not in releases or a == b:
                raise ValueError("invalid conflict endpoints")
            conflicts.add(tuple(sorted((a, b))))
    except (OSError, ValueError, TypeError) as exc:
        raise CatalogError(str(exc)) from exc
    return Catalog(releases, tuple(sorted(requirements, key=lambda r: (r.parent_name, version(r.parent_version), r.target_name, version(r.min_version), version(r.max_version_exclusive)))), frozenset(conflicts))


def parse_request(line: str) -> tuple[dict | None, dict | None]:
    """Return (valid_request, invalid_result), independently per input line."""
    try:
        obj = json.loads(line)
    except (ValueError, TypeError):
        obj = None
    request_id = obj.get("request_id") if isinstance(obj, dict) else None
    request_id = request_id if isinstance(request_id, str) and request_id else None
    invalid = {"request_id": request_id, "status": "invalid", "reason": "invalid_request"}
    if not isinstance(obj, dict) or set(obj) != {"request_id", "platform", "max_download_kb", "roots"}:
        return None, invalid
    if request_id is None or not isinstance(obj["platform"], str) or obj["platform"] not in PLATFORMS:
        return None, invalid
    budget = obj["max_download_kb"]
    if type(budget) is not int or budget <= 0 or not isinstance(obj["roots"], list) or not obj["roots"]:
        return None, invalid
    for root in obj["roots"]:
        if not isinstance(root, dict) or set(root) != {"name", "min_version", "max_version_exclusive"}:
            return None, invalid
        try:
            _name(root["name"])
            version_range(root["min_version"], root["max_version_exclusive"])
        except (ValueError, TypeError):
            return None, invalid
    return obj, None
