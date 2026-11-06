"""CryoRelay snapshot reader and command-line entry point (standard library only)."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z", re.ASCII)
REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)
NUMBER = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)


class SnapshotError(ValueError):
    pass


@dataclass(frozen=True)
class Hub:
    hub_id: str
    transfer_min: int
    cold_storage: bool


@dataclass(frozen=True)
class Service:
    service_id: str
    from_hub: str
    to_hub: str
    depart_min: int
    arrive_min: int
    cold_enabled: bool
    slots: int


@dataclass(frozen=True)
class Request:
    request_id: str
    origin: str
    destination: str
    ready_min: int
    deadline_min: int
    max_legs: int
    requires_cold: bool


def _id(value: Any, request: bool = False) -> str:
    if not isinstance(value, str) or not (REQUEST_ID if request else ID).fullmatch(value):
        raise ValueError("invalid identifier")
    return value


def _csv_int(value: str, maximum: int) -> int:
    if not isinstance(value, str) or not NUMBER.fullmatch(value):
        raise ValueError("invalid decimal integer")
    n = int(value)
    if n > maximum:
        raise ValueError("integer out of range")
    return n


def _flag(value: str) -> bool:
    if value not in ("true", "false"):
        raise ValueError("expected true or false")
    return value == "true"


def _read_rows(path: Path, columns: set[str]):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames is None or set(reader.fieldnames) != columns:
            raise SnapshotError(f"{path}: incorrect CSV header")
        for line, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("incorrect number of CSV fields")
                yield line, row
            except ValueError as exc:
                raise SnapshotError(f"{path}:{line}: {exc}") from exc


def load_snapshot(hubs_path: Path, services_path: Path) -> tuple[dict[str, Hub], dict[str, Service]]:
    hubs: dict[str, Hub] = {}
    services: dict[str, Service] = {}
    for line, row in _read_rows(hubs_path, {"hub_id", "transfer_min", "cold_storage"}):
        try:
            hub = Hub(_id(row["hub_id"]), _csv_int(row["transfer_min"], 180), _flag(row["cold_storage"]))
            if hub.hub_id in hubs and hubs[hub.hub_id] != hub:
                raise ValueError("conflicting hub ID")
            hubs[hub.hub_id] = hub
        except ValueError as exc:
            raise SnapshotError(f"{hubs_path}:{line}: {exc}") from exc
    for line, row in _read_rows(services_path, {"service_id", "from_hub", "to_hub", "depart_min", "arrive_min", "cold_enabled", "slots"}):
        try:
            svc = Service(_id(row["service_id"]), _id(row["from_hub"]), _id(row["to_hub"]),
                          _csv_int(row["depart_min"], 10080), _csv_int(row["arrive_min"], 10080),
                          _flag(row["cold_enabled"]), _csv_int(row["slots"], 999))
            if svc.from_hub not in hubs or svc.to_hub not in hubs:
                raise ValueError("unknown hub")
            if svc.depart_min >= svc.arrive_min:
                raise ValueError("arrival must follow departure")
            if svc.service_id in services and services[svc.service_id] != svc:
                raise ValueError("conflicting service ID")
            services[svc.service_id] = svc
        except ValueError as exc:
            raise SnapshotError(f"{services_path}:{line}: {exc}") from exc
    return hubs, services


def _json_int(value: Any, maximum: int, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        raise ValueError("invalid integer field")
    return value


def parse_request(value: Any, hubs: dict[str, Hub]) -> Request:
    if not isinstance(value, dict):
        raise ValueError("request must be an object")
    try:
        req = Request(request_id=_id(value["request_id"], request=True),
                      origin=_id(value["origin"]), destination=_id(value["destination"]),
                      ready_min=_json_int(value["ready_min"], 10080),
                      deadline_min=_json_int(value["deadline_min"], 10080),
                      max_legs=_json_int(value["max_legs"], 6, 1),
                      requires_cold=value["requires_cold"])
    except KeyError as exc:
        raise ValueError(f"missing field: {exc.args[0]}") from exc
    if type(req.requires_cold) is not bool:
        raise ValueError("requires_cold must be boolean")
    if req.origin not in hubs or req.destination not in hubs:
        raise ValueError("unknown hub")
    if req.ready_min > req.deadline_min:
        raise ValueError("deadline before ready time")
    return req


class RelayPlanner:
    def __init__(self, hubs: dict[str, Hub], services: dict[str, Service]):
        self.hubs = hubs
        self.services = services

    def plan(self, request: Request) -> dict[str, Any]:
        """Return the customer's exact response for this independent request."""
        return {"request_id": request.request_id, "status": "not_implemented"}


def run(hubs_path: Path, services_path: Path, requests_path: Path, output) -> None:
    hubs, services = load_snapshot(hubs_path, services_path)
    planner = RelayPlanner(hubs, services)
    with requests_path.open(encoding="utf-8") as stream:
        for raw in stream:
            obj: Any = None
            try:
                obj = json.loads(raw)
                request = parse_request(obj, hubs)
                answer = planner.plan(request)
            except (ValueError, TypeError) as exc:
                possible_id = obj.get("request_id") if isinstance(obj, dict) else None
                request_id = possible_id if isinstance(possible_id, str) and REQUEST_ID.fullmatch(possible_id) else None
                answer = {"request_id": request_id, "status": "invalid_request", "error": str(exc)}
            output.write(json.dumps(answer, separators=(",", ":"), ensure_ascii=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CryoRelay scheduled sample transfer review")
    parser.add_argument("--hubs", type=Path, default=Path("fixtures/hubs.csv"))
    parser.add_argument("--services", type=Path, default=Path("fixtures/services.csv"))
    parser.add_argument("--requests", type=Path, default=Path("fixtures/requests.jsonl"))
    args = parser.parse_args(argv)
    try:
        run(args.hubs, args.services, args.requests, sys.stdout)
    except (SnapshotError, OSError, csv.Error) as exc:
        print(f"snapshot error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
