"""Request validation and response contracts."""

from dataclasses import dataclass
from .catalog import valid_id


@dataclass(frozen=True)
class Investigation:
    request_id: str
    site: str
    max_sources: int
    readings: tuple  # (mix_id, result), deduplicated


class QueryError(ValueError):
    def __init__(self, reason, request_id=None):
        super().__init__(reason)
        self.reason = reason
        self.request_id = request_id


def parse_query(raw, catalog):
    ident = raw.get("request_id") if isinstance(raw, dict) else None
    if not valid_id(ident, 128):
        ident = None
    if not isinstance(raw, dict) or ident is None:
        raise QueryError("invalid_query", ident)
    site, cap, readings = raw.get("site"), raw.get("max_sources"), raw.get("readings")
    if not valid_id(site) or type(cap) is not int or not 0 <= cap <= 3 or not isinstance(readings, list) or len(readings) > 40:
        raise QueryError("invalid_query", ident)
    seen = {}
    for reading in readings:
        if not isinstance(reading, dict) or not valid_id(reading.get("mix_id")) or reading.get("result") not in ("positive", "negative"):
            raise QueryError("invalid_query", ident)
        mix_id, result = reading["mix_id"], reading["result"]
        if mix_id in seen and seen[mix_id] != result:
            raise QueryError("invalid_query", ident)
        seen[mix_id] = result
    if site not in catalog.sites:
        raise QueryError("unknown_site", ident)
    for mix_id in seen:
        if mix_id not in catalog.mixes:
            raise QueryError("unknown_mix", ident)
        if catalog.mixes[mix_id] != site:
            raise QueryError("wrong_site", ident)
    return Investigation(ident, site, cap, tuple(sorted(seen.items())))


def invalid_response(exc):
    return {"request_id": exc.request_id, "status": "invalid", "reason": exc.reason}
