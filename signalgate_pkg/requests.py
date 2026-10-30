"""Wire-format query validation. Matches must be implemented separately."""

from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass

_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)
_MAX_MS = 10**12


@dataclass(frozen=True)
class ScanRequest:
    request_id: str
    region: str
    seen_at_ms: int
    chunks: tuple[bytes, ...]
    limit: int


class RequestError(ValueError):
    def __init__(self, reason: str, request_id: str | None):
        super().__init__(reason)
        self.reason = reason
        self.request_id = request_id


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def parse_request(line: str, regions: frozenset[str]) -> ScanRequest:
    try:
        item = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        raise RequestError("invalid_request", None) from None
    if not isinstance(item, dict):
        raise RequestError("invalid_request", None)
    rid = item.get("request_id")
    rid = rid if _valid_id(rid) else None
    region = item.get("region")
    when = item.get("seen_at_ms")
    limit = item.get("limit", 5)
    chunks = item.get("chunks_b64")
    if rid is None or not _valid_id(region) or type(when) is not int or not 0 <= when <= _MAX_MS:
        raise RequestError("invalid_request", rid)
    if type(limit) is not int or not 1 <= limit <= 20:
        raise RequestError("invalid_request", rid)
    if not isinstance(chunks, list) or not 1 <= len(chunks) <= 128:
        raise RequestError("invalid_request", rid)

    decoded = []
    total = 0
    for chunk in chunks:
        if not isinstance(chunk, str):
            raise RequestError("invalid_request", rid)
        try:
            data = base64.b64decode(chunk, validate=True)
            if base64.b64encode(data).decode("ascii") != chunk:
                raise ValueError("noncanonical base64")
        except (ValueError, binascii.Error, UnicodeEncodeError):
            raise RequestError("invalid_request", rid) from None
        if len(data) > 65536:
            raise RequestError("invalid_request", rid)
        total += len(data)
        if total > 1048576:
            raise RequestError("invalid_request", rid)
        decoded.append(data)
    if region not in regions:
        raise RequestError("unknown_region", rid)
    return ScanRequest(rid, region, when, tuple(decoded), limit)
