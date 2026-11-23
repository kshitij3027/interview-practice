"""Snapshot loading and input validation for BatchPath."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z", re.ASCII)
_UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    tenant_id: str
    run_min: int
    earliest_min: int


@dataclass(frozen=True)
class Link:
    link_id: str
    revision: int
    op: str
    tenant_id: str
    prerequisite_id: str
    target_id: str
    lag_min: int | None


@dataclass
class Catalog:
    datasets: dict[str, Dataset]
    active_links: list[Link]
    tenants: set[str]


def identifier(value: str, maximum: int = 48) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1," + str(maximum) + r"}", value, re.ASCII))


def integer(value: str, lo: int, hi: int) -> int:
    if not isinstance(value, str) or not _UINT.fullmatch(value):
        raise CatalogError("invalid integer notation")
    number = int(value)
    if not lo <= number <= hi:
        raise CatalogError("integer outside allowed range")
    return number


def _rows(path: str | Path, columns: set[str]):
    try:
        with open(path, encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames is None or set(reader.fieldnames) != columns or len(reader.fieldnames) != len(columns):
                raise CatalogError(f"invalid CSV header: {path}")
            for index, row in enumerate(reader, start=2):
                if None in row or any(v is None for v in row.values()):
                    raise CatalogError(f"malformed CSV record {path}:{index}")
                yield row
    except (OSError, UnicodeError, csv.Error) as error:
        raise CatalogError(f"cannot read {path}: {error}") from error


def load_catalog(datasets_file: str | Path, links_file: str | Path) -> Catalog:
    datasets: dict[str, Dataset] = {}
    tenants: set[str] = set()
    for row in _rows(datasets_file, {"dataset_id", "tenant_id", "run_min", "earliest_min"}):
        dataset_id, tenant_id = row["dataset_id"], row["tenant_id"]
        if not identifier(dataset_id) or not identifier(tenant_id):
            raise CatalogError("invalid dataset identifier")
        entry = Dataset(dataset_id, tenant_id, integer(row["run_min"], 1, 1_000_000), integer(row["earliest_min"], 0, 1_000_000_000))
        if dataset_id in datasets and datasets[dataset_id] != entry:
            raise CatalogError("conflicting dataset declaration")
        datasets[dataset_id] = entry
        tenants.add(tenant_id)

    by_revision: dict[tuple[str, int], Link] = {}
    owners: dict[str, str] = {}
    for row in _rows(links_file, {"link_id", "revision", "op", "tenant_id", "prerequisite_id", "target_id", "lag_min"}):
        link_id, tenant_id = row["link_id"], row["tenant_id"]
        if not identifier(link_id) or not identifier(tenant_id) or tenant_id not in tenants:
            raise CatalogError("invalid link identifier or tenant")
        revision = integer(row["revision"], 1, 2_000_000_000)
        op = row["op"]
        source, target, raw_lag = row["prerequisite_id"], row["target_id"], row["lag_min"]
        if op == "upsert":
            if not identifier(source) or not identifier(target) or source not in datasets or target not in datasets:
                raise CatalogError("invalid linked dataset")
            if datasets[source].tenant_id != tenant_id or datasets[target].tenant_id != tenant_id:
                raise CatalogError("cross-tenant link")
            lag = integer(raw_lag, 0, 1_000_000)
        elif op == "retract":
            if source != "" or target != "" or raw_lag != "":
                raise CatalogError("invalid retraction")
            lag = None
        else:
            raise CatalogError("invalid link operation")
        if link_id in owners and owners[link_id] != tenant_id:
            raise CatalogError("link changed tenant")
        owners[link_id] = tenant_id
        link = Link(link_id, revision, op, tenant_id, source, target, lag)
        key = (link_id, revision)
        if key in by_revision and by_revision[key] != link:
            raise CatalogError("conflicting link revision")
        by_revision[key] = link

    latest: dict[str, Link] = {}
    for link in by_revision.values():
        if link.link_id not in latest or latest[link.link_id].revision < link.revision:
            latest[link.link_id] = link
    active = [link for link in latest.values() if link.op == "upsert"]
    return Catalog(datasets=datasets, active_links=active, tenants=tenants)
