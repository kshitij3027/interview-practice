"""Input boundaries for an offline site-demand assessment."""
import csv
import json
import re
from pathlib import Path
from .model import Catalog, Query, SessionRevision

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z", re.ASCII)
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
_MAX_TIME = 10**12


class CatalogError(ValueError):
    pass


class QueryError(ValueError):
    def __init__(self, reason: str, request_id: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.request_id = request_id


def _identifier(raw: object) -> bool:
    return isinstance(raw, str) and _ID.fullmatch(raw) is not None


def _number(raw: object, ceiling: int) -> int:
    if not isinstance(raw, str) or _DECIMAL.fullmatch(raw) is None:
        raise CatalogError("invalid canonical decimal")
    value = int(raw)
    if value > ceiling:
        raise CatalogError("value exceeds limit")
    return value


def _rows(path: str | Path, columns: set[str]):
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames is None or set(reader.fieldnames) != columns:
                raise CatalogError(f"unexpected CSV columns in {path}")
            for number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise CatalogError(f"malformed row {number} in {path}")
                yield row
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CatalogError(f"unable to read {path}: {exc}") from exc


def load_catalog(sites_file: str | Path, revisions_file: str | Path) -> Catalog:
    sites = set()
    for row in _rows(sites_file, {"site_id"}):
        site = row["site_id"]
        if not _identifier(site):
            raise CatalogError("invalid site identifier")
        sites.add(site)  # Repeated identical site IDs are harmless.
    if not sites:
        raise CatalogError("empty site catalog")

    seen: dict[tuple[str, int], SessionRevision] = {}
    for row in _rows(revisions_file, {"session_id", "revision", "site_id", "mode", "start_ms", "end_ms", "kw"}):
        session = row["session_id"]
        if not _identifier(session):
            raise CatalogError("invalid session identifier")
        revision = _number(row["revision"], 10**9)
        mode = row["mode"]
        if mode == "cancel":
            if any(row[key] != "" for key in ("site_id", "start_ms", "end_ms", "kw")):
                raise CatalogError("cancel records must leave value columns blank")
            value = SessionRevision(session, revision, None, mode, None, None, None)
        elif mode == "upsert":
            site = row["site_id"]
            if site not in sites:
                raise CatalogError("unknown site in session")
            start, end = _number(row["start_ms"], _MAX_TIME), _number(row["end_ms"], _MAX_TIME)
            kw = _number(row["kw"], 100_000)
            if start >= end:
                raise CatalogError("session interval must be nonempty")
            value = SessionRevision(session, revision, site, mode, start, end, kw)
        else:
            raise CatalogError("invalid session operation")
        key = (session, revision)
        if key in seen and seen[key] != value:
            raise CatalogError("conflicting replay of session revision")
        seen[key] = value
    return Catalog(frozenset(sites), tuple(seen.values()))


def parse_query(line: str, sites: frozenset[str]) -> Query:
    request_id = None
    try:
        obj = json.loads(line)
    except (ValueError, TypeError):
        raise QueryError("invalid_query") from None
    if not isinstance(obj, dict):
        raise QueryError("invalid_query")
    if _identifier(obj.get("request_id")):
        request_id = obj["request_id"]
    if request_id is None or not _identifier(obj.get("site_id")):
        raise QueryError("invalid_query", request_id)
    start, end = obj.get("from_ms"), obj.get("until_ms")
    if (type(start) is not int or type(end) is not int or
            not (0 <= start < end <= _MAX_TIME)):
        raise QueryError("invalid_query", request_id)
    if obj["site_id"] not in sites:
        raise QueryError("unknown_site", request_id)
    return Query(request_id, obj["site_id"], start, end)
