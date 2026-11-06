"""Input boundary shared by the CLI and local checks."""
import csv
import json
import re
from pathlib import Path
from .models import Scope, Observation, Query, Snapshot

ID = re.compile(r"[A-Za-z0-9_-]+\Z")
DIGITS = re.compile(r"(?:0|[1-9][0-9]*)\Z")
SCOPES = {"service_id", "region", "budget_us"}
ROWS = {"request_id", "revision", "op", "service_id", "region", "at_ms", "latency_us"}


class SnapshotError(ValueError):
    pass


def _id(value: object, max_length: int = 48) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= max_length and ID.fullmatch(value) is not None


def _csv_int(value: str | None, low: int, high: int) -> int:
    if not isinstance(value, str) or DIGITS.fullmatch(value) is None:
        raise ValueError("expected canonical unsigned integer")
    parsed = int(value)
    if not low <= parsed <= high:
        raise ValueError("integer out of range")
    return parsed


def _read_csv(path: str | Path, fields: set[str]):
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames is None or set(reader.fieldnames) != fields or len(reader.fieldnames) != len(fields):
            raise SnapshotError(f"{path}: invalid CSV header")
        for lineno, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise SnapshotError(f"{path}:{lineno}: malformed CSV row")
            yield lineno, row


def load_snapshot(scopes_path: str | Path, observations_path: str | Path) -> Snapshot:
    scopes: dict[tuple[str, str], Scope] = {}
    try:
        for lineno, row in _read_csv(scopes_path, SCOPES):
            try:
                if not _id(row["service_id"]) or not _id(row["region"]):
                    raise ValueError("invalid scope identifier")
                scope = Scope(row["service_id"], row["region"], _csv_int(row["budget_us"], 0, 10**9))
                key = (scope.service_id, scope.region)
                if key in scopes and scopes[key] != scope:
                    raise ValueError("conflicting scope")
                scopes[key] = scope
            except ValueError as exc:
                raise SnapshotError(f"{scopes_path}:{lineno}: {exc}") from exc
        if not scopes:
            raise SnapshotError("no scopes declared")
        observed: dict[tuple[str, int], Observation] = {}
        latest: dict[str, Observation] = {}
        rows_seen = 0
        for lineno, row in _read_csv(observations_path, ROWS):
            rows_seen += 1
            try:
                request_id = row["request_id"]
                if not _id(request_id):
                    raise ValueError("invalid request ID")
                revision = _csv_int(row["revision"], 1, 10**9)
                op = row["op"]
                if op == "cancel":
                    if any(row[k] != "" for k in ("service_id", "region", "at_ms", "latency_us")):
                        raise ValueError("cancellation must have blank value fields")
                    value = Observation(request_id, revision, op, None, None, None, None)
                elif op == "upsert":
                    service_id, region = row["service_id"], row["region"]
                    if not _id(service_id) or not _id(region) or (service_id, region) not in scopes:
                        raise ValueError("invalid service/region reference")
                    value = Observation(request_id, revision, op, service_id, region,
                                        _csv_int(row["at_ms"], 0, 10**12),
                                        _csv_int(row["latency_us"], 0, 10**9))
                else:
                    raise ValueError("invalid operation")
                key = (request_id, revision)
                if key in observed and observed[key] != value:
                    raise ValueError("conflicting request revision")
                observed[key] = value
                if request_id not in latest or latest[request_id].revision < revision:
                    latest[request_id] = value
            except ValueError as exc:
                raise SnapshotError(f"{observations_path}:{lineno}: {exc}") from exc
        return Snapshot(scopes, latest, rows_seen)
    except (csv.Error, UnicodeError, OSError) as exc:
        raise SnapshotError(f"cannot load snapshot: {exc}") from exc


def parse_query(raw: str, scopes: dict[tuple[str, str], Scope]) -> Query | dict:
    obj: object = None
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError("expected JSON object")
        query_id = obj.get("query_id")
        if not _id(query_id, 128):
            raise ValueError("invalid query ID")
        service_id, region = obj.get("service_id"), obj.get("region")
        if not _id(service_id) or not _id(region):
            raise ValueError("invalid scope identifier")
        first, last = obj.get("from_ms"), obj.get("until_ms")
        if (type(first) is not int or type(last) is not int or
                not 0 <= first < last <= 10**12):
            raise ValueError("invalid time range")
        if (service_id, region) not in scopes:
            return {"query_id": query_id, "status": "invalid", "reason": "unknown_scope"}
        return Query(query_id, service_id, region, first, last)
    except (ValueError, TypeError):
        recovered = obj.get("query_id") if isinstance(obj, dict) else None
        return {"query_id": recovered if _id(recovered, 128) else None,
                "status": "invalid", "reason": "invalid_query"}
