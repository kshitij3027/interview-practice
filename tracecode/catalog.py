"""Load and validate a manufacturer catalog before accepting scan requests."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z", re.ASCII)
_WEIGHTS = re.compile(r"[1-9]{1,8}\Z", re.ASCII)


class CatalogError(ValueError):
    """The manufacturer snapshot cannot be trusted."""


@dataclass(frozen=True)
class Model:
    model_id: str
    length: int
    weights: str


@dataclass(frozen=True)
class NumberBand:
    range_id: str
    model_id: str
    first_payload: str
    last_payload: str


@dataclass
class Catalog:
    models: dict[str, Model]
    bands: dict[str, list[NumberBand]]


def _rows(path: str | Path, fields: set[str]):
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames is None or set(reader.fieldnames) != fields or len(reader.fieldnames) != len(fields):
            raise CatalogError(f"{path}: expected headers {sorted(fields)}")
        for lineno, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise CatalogError(f"{path}:{lineno}: invalid CSV shape")
            yield lineno, row


def _id(value: str, field: str):
    if not _ID.fullmatch(value):
        raise CatalogError(f"invalid {field}: {value!r}")


def load_catalog(models_path: str | Path, ranges_path: str | Path) -> Catalog:
    models: dict[str, Model] = {}
    for line, row in _rows(models_path, {"model_id", "length", "weights"}):
        _id(row["model_id"], f"model_id at line {line}")
        if not re.fullmatch(r"(?:[8-9]|1[0-8])", row["length"], re.ASCII):
            raise CatalogError(f"invalid model length at line {line}")
        if not _WEIGHTS.fullmatch(row["weights"]):
            raise CatalogError(f"invalid model weights at line {line}")
        model = Model(row["model_id"], int(row["length"]), row["weights"])
        old = models.setdefault(model.model_id, model)
        if old != model:
            raise CatalogError(f"conflicting model {model.model_id!r}")

    band_ids: dict[str, NumberBand] = {}
    bands: dict[str, list[NumberBand]] = {model_id: [] for model_id in models}
    for line, row in _rows(ranges_path, {"range_id", "model_id", "first_payload", "last_payload"}):
        _id(row["range_id"], f"range_id at line {line}")
        _id(row["model_id"], f"range model_id at line {line}")
        model = models.get(row["model_id"])
        if model is None:
            raise CatalogError(f"unknown model in range at line {line}")
        width = model.length - 1
        first, last = row["first_payload"], row["last_payload"]
        if (len(first) != width or len(last) != width
                or not first.isascii() or not last.isascii()
                or not first.isdecimal() or not last.isdecimal() or first > last):
            raise CatalogError(f"invalid payload bounds at line {line}")
        band = NumberBand(row["range_id"], row["model_id"], first, last)
        old = band_ids.setdefault(band.range_id, band)
        if old != band:
            raise CatalogError(f"conflicting range {band.range_id!r}")
        if old is band:
            bands[band.model_id].append(band)
    return Catalog(models, bands)
