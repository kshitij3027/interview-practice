"""Validated, immutable lot-and-sampling snapshot."""

import csv
import re
from dataclasses import dataclass
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]+\Z")


class CatalogError(ValueError):
    pass


def valid_id(value, limit=48):
    return isinstance(value, str) and 1 <= len(value) <= limit and ID.fullmatch(value) is not None


def read_rows(path, expected):
    try:
        with Path(path).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames is None or len(reader.fieldnames) != len(expected) or set(reader.fieldnames) != set(expected):
                raise CatalogError(f"{path}: invalid CSV header")
            for line_no, row in enumerate(reader, 2):
                if None in row or any(value is None for value in row.values()):
                    raise CatalogError(f"{path}:{line_no}: malformed CSV row")
                yield line_no, row
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CatalogError(f"{path}: {exc}") from exc


@dataclass(frozen=True)
class Catalog:
    lots: dict
    mixes: dict
    membership: dict
    sites: frozenset
    membership_count: int

    @classmethod
    def load(cls, lots_path, mixes_path, membership_path):
        lots = {}
        mixes = {}
        edges = set()
        for line, row in read_rows(lots_path, ("lot_id", "site", "ingredient")):
            lot_id, site, ingredient = row["lot_id"], row["site"], row["ingredient"]
            if not all(valid_id(v) for v in (lot_id, site, ingredient)):
                raise CatalogError(f"{lots_path}:{line}: invalid lot declaration")
            val = (site, ingredient)
            if lot_id in lots and lots[lot_id] != val:
                raise CatalogError(f"{lots_path}:{line}: conflicting lot {lot_id}")
            lots[lot_id] = val
        for line, row in read_rows(mixes_path, ("mix_id", "site")):
            mix_id, site = row["mix_id"], row["site"]
            if not all(valid_id(v) for v in (mix_id, site)):
                raise CatalogError(f"{mixes_path}:{line}: invalid mix declaration")
            if mix_id in mixes and mixes[mix_id] != site:
                raise CatalogError(f"{mixes_path}:{line}: conflicting mix {mix_id}")
            mixes[mix_id] = site
        for line, row in read_rows(membership_path, ("mix_id", "lot_id")):
            mix_id, lot_id = row["mix_id"], row["lot_id"]
            if not all(valid_id(v) for v in (mix_id, lot_id)):
                raise CatalogError(f"{membership_path}:{line}: invalid membership")
            if mix_id not in mixes or lot_id not in lots:
                raise CatalogError(f"{membership_path}:{line}: unknown membership reference")
            if mixes[mix_id] != lots[lot_id][0]:
                raise CatalogError(f"{membership_path}:{line}: cross-site membership")
            edges.add((mix_id, lot_id))
        membership = {mix_id: set() for mix_id in mixes}
        for mix_id, lot_id in edges:
            membership[mix_id].add(lot_id)
        return cls(lots, mixes, {k: frozenset(v) for k, v in membership.items()},
                   frozenset([v[0] for v in lots.values()] + list(mixes.values())), len(edges))
