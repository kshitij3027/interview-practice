"""Scan validation and isolated error responses."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .catalog import Catalog

_SCAN_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)
_MODEL_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z", re.ASCII)


@dataclass(frozen=True)
class Scan:
    scan_id: str
    model_id: str
    max_penalty: int
    reads: tuple[dict[str, int], ...]


def parse_scan(line: str, catalog: Catalog) -> tuple[Scan | None, dict | None]:
    try:
        obj = json.loads(line)
    except (ValueError, TypeError):
        return None, {"scan_id": None, "status": "invalid", "reason": "invalid_scan"}
    scan_id = obj.get("scan_id") if isinstance(obj, dict) else None
    if not isinstance(scan_id, str) or not _SCAN_ID.fullmatch(scan_id):
        scan_id = None
    err = {"scan_id": scan_id, "status": "invalid", "reason": "invalid_scan"}
    if not isinstance(obj, dict) or scan_id is None:
        return None, err
    model_id = obj.get("model_id")
    cap = obj.get("max_penalty")
    reads = obj.get("reads")
    if (not isinstance(model_id, str) or not _MODEL_ID.fullmatch(model_id)
            or type(cap) is not int or not 0 <= cap <= 1000
            or not isinstance(reads, list)):
        return None, err
    model = catalog.models.get(model_id)
    if model is None:
        return None, {"scan_id": scan_id, "status": "invalid", "reason": "unknown_model"}
    if len(reads) != model.length:
        return None, err
    parsed = []
    for read in reads:
        if read == "?":
            parsed.append({str(d): 3 for d in range(10)})
        elif isinstance(read, dict) and read:
            if any(not isinstance(d, str) or len(d) != 1 or d not in "0123456789"
                   or type(cost) is not int or not 0 <= cost <= 9
                   for d, cost in read.items()):
                return None, err
            parsed.append(dict(read))
        else:
            return None, err
    return Scan(scan_id, model_id, cap, tuple(parsed)), None
