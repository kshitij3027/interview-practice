"""Inventory snapshot input and validation (provided infrastructure)."""
import csv
import re
from dataclasses import dataclass

ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
FIELDS = ["lot_id", "store_id", "sku", "ready_min", "expiry_min", "units"]


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Lot:
    lot_id: str
    store_id: str
    sku: str
    ready_min: int
    expiry_min: int
    units: int


def valid_id(value, request=False):
    return isinstance(value, str) and bool((REQUEST_ID if request else ID).fullmatch(value))


def csv_uint(value, maximum):
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise CatalogError("noncanonical numeric value")
    n = int(value)
    if n > maximum:
        raise CatalogError("numeric value out of range")
    return n


def load_lots(path):
    unique = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, strict=True)
            if reader.fieldnames is None or len(reader.fieldnames) != len(FIELDS) or set(reader.fieldnames) != set(FIELDS):
                raise CatalogError("lot CSV headers are invalid")
            for line, row in enumerate(reader, 2):
                if None in row or any(row.get(key) is None for key in FIELDS):
                    raise CatalogError(f"invalid lot row at line {line}")
                lot_id, store, sku = (row[key] for key in FIELDS[:3])
                if not all(valid_id(v) for v in (lot_id, store, sku)):
                    raise CatalogError(f"invalid lot identifier at line {line}")
                ready = csv_uint(row["ready_min"], 10**9)
                expiry = csv_uint(row["expiry_min"], 10**9)
                units = csv_uint(row["units"], 10**6)
                if ready >= expiry:
                    raise CatalogError(f"invalid lot time interval at line {line}")
                lot = Lot(lot_id, store, sku, ready, expiry, units)
                old = unique.get(lot_id)
                if old is not None and old != lot:
                    raise CatalogError(f"conflicting lot definition: {lot_id}")
                unique[lot_id] = lot
    except (UnicodeError, csv.Error) as exc:
        raise CatalogError(f"cannot read CSV: {exc}") from exc
    result = {}
    for lot in unique.values():
        result.setdefault((lot.store_id, lot.sku), []).append(lot)
    for lots in result.values():
        lots.sort(key=lambda x: (x.ready_min, x.expiry_min, x.lot_id))
    return result
