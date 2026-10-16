"""Load and validate a read-only fiber network snapshot."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_NUMBER = re.compile(r"[0-9]+\Z")


class SnapshotError(ValueError):
    """The supplied network snapshot is inconsistent."""


@dataclass(frozen=True)
class Site:
    site_id: str
    kind: str
    active_accounts: int
    priority_accounts: int


@dataclass(frozen=True)
class Span:
    span_id: str
    site_a: str
    site_b: str
    enabled: bool


@dataclass(frozen=True)
class NetworkSnapshot:
    sites: dict[str, Site]
    spans: dict[str, Span]


def _rows(path: str | Path, columns: tuple[str, ...]):
    try:
        with open(path, newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != set(columns):
                raise SnapshotError(f"{path}: expected columns {', '.join(columns)}")
            for row_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise SnapshotError(f"{path}:{row_number}: malformed CSV row")
                yield row_number, row
    except (OSError, UnicodeError, csv.Error) as exc:
        raise SnapshotError(f"{path}: {exc}") from exc


def _id(value: str, label: str) -> str:
    if not _ID.fullmatch(value):
        raise SnapshotError(f"invalid {label}: {value!r}")
    return value


def _count(value: str, label: str) -> int:
    if not _NUMBER.fullmatch(value):
        raise SnapshotError(f"invalid {label}: {value!r}")
    number = int(value)
    if number > 1_000_000_000:
        raise SnapshotError(f"{label} exceeds allowed range")
    return number


def load_snapshot(sites_path: str | Path, spans_path: str | Path) -> NetworkSnapshot:
    sites: dict[str, Site] = {}
    for row_number, row in _rows(sites_path, ("site_id", "kind", "active_accounts", "priority_accounts")):
        site_id = _id(row["site_id"], "site_id")
        kind = row["kind"]
        if kind not in {"core", "exchange", "access"}:
            raise SnapshotError(f"sites row {row_number}: invalid kind")
        active = _count(row["active_accounts"], "active_accounts")
        priority = _count(row["priority_accounts"], "priority_accounts")
        if priority > active or (kind != "access" and (active != 0 or priority != 0)):
            raise SnapshotError(f"sites row {row_number}: invalid account counts")
        if site_id in sites:
            raise SnapshotError(f"sites row {row_number}: duplicate site {site_id}")
        sites[site_id] = Site(site_id, kind, active, priority)
    if not any(site.kind == "core" for site in sites.values()):
        raise SnapshotError("snapshot requires at least one core")

    spans: dict[str, Span] = {}
    for row_number, row in _rows(spans_path, ("span_id", "site_a", "site_b", "enabled")):
        span_id = _id(row["span_id"], "span_id")
        a, b = _id(row["site_a"], "site_a"), _id(row["site_b"], "site_b")
        if a not in sites or b not in sites:
            raise SnapshotError(f"spans row {row_number}: unknown site")
        if row["enabled"] not in {"true", "false"}:
            raise SnapshotError(f"spans row {row_number}: invalid enabled flag")
        span = Span(span_id, a, b, row["enabled"] == "true")
        if span_id in spans:
            if spans[span_id] != span:
                raise SnapshotError(f"spans row {row_number}: conflicting span {span_id}")
            continue
        spans[span_id] = span
    return NetworkSnapshot(sites, spans)

