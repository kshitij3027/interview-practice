"""Validated, revision-aware catalog snapshot loading."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
_PHRASE = re.compile(r"[a-z0-9]{1,24}(?: [a-z0-9]{1,24}){0,7}\Z")
_UINT = re.compile(r"(?:0|[1-9][0-9]*)\Z")


@dataclass(frozen=True)
class Signature:
    signature_id: str
    tenant_id: str
    phrase: str
    priority: int


@dataclass(frozen=True)
class Catalog:
    tenants: dict[str, str]
    active: tuple[Signature, ...]


def _csv_rows(path: str | Path, columns: set[str]):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(columns) or set(reader.fieldnames) != columns:
            raise ValueError(f"invalid CSV header: {path}")
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"invalid CSV row {line}: {path}")
            yield row


def _id(value: str) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _integer(value: str, low: int, high: int) -> int:
    if not isinstance(value, str) or _UINT.fullmatch(value) is None:
        raise ValueError("invalid canonical integer")
    number = int(value)
    if not low <= number <= high:
        raise ValueError("integer out of range")
    return number


def load_catalog(tenants_path: str | Path, signatures_path: str | Path) -> Catalog:
    tenants: dict[str, str] = {}
    for row in _csv_rows(tenants_path, {"tenant_id", "display_name"}):
        tenant, name = row["tenant_id"], row["display_name"]
        if not _id(tenant) or not 1 <= len(name) <= 80 or any(not 32 <= ord(c) <= 126 for c in name):
            raise ValueError("invalid tenant declaration")
        if tenant in tenants and tenants[tenant] != name:
            raise ValueError("conflicting tenant declaration")
        tenants[tenant] = name
    if not tenants:
        raise ValueError("empty tenant catalog")

    versions: dict[tuple[str, int], tuple[str, str, str, int | None]] = {}
    owners: dict[str, str] = {}
    newest: dict[str, tuple[int, str, str, str, int | None]] = {}
    for row in _csv_rows(signatures_path, {"signature_id", "revision", "op", "tenant_id", "phrase", "priority"}):
        sid, tenant, op, phrase = (row[key] for key in ("signature_id", "tenant_id", "op", "phrase"))
        if not _id(sid) or not _id(tenant) or tenant not in tenants:
            raise ValueError("invalid signature/tenant reference")
        revision = _integer(row["revision"], 1, 2_000_000_000)
        if op == "upsert":
            if _PHRASE.fullmatch(phrase) is None:
                raise ValueError("invalid signature phrase")
            priority: int | None = _integer(row["priority"], 1, 9)
        elif op == "retract":
            if phrase != "" or row["priority"] != "":
                raise ValueError("invalid retraction")
            priority = None
        else:
            raise ValueError("invalid signature operation")
        if sid in owners and owners[sid] != tenant:
            raise ValueError("signature crossed tenant boundary")
        owners[sid] = tenant
        key = (sid, revision)
        payload = (tenant, op, phrase, priority)
        if key in versions and versions[key] != payload:
            raise ValueError("conflicting signature revision")
        versions[key] = payload
        if sid not in newest or revision > newest[sid][0]:
            newest[sid] = (revision, tenant, op, phrase, priority)

    active = []
    for sid, (_revision, tenant, op, phrase, priority) in newest.items():
        if op == "upsert":
            assert priority is not None
            active.append(Signature(sid, tenant, phrase, priority))
    return Catalog(tenants, tuple(sorted(active, key=lambda s: (s.tenant_id, s.signature_id))))
