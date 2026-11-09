"""Input and CLI harness for a transit summary release planner (stdlib only)."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass

ID = re.compile(r"[A-Za-z0-9_-]+\Z")
COUNT = re.compile(r"(?:0|[1-9][0-9]*)\Z")


@dataclass(frozen=True)
class Station:
    station_id: str
    route_id: str
    sector_id: str


@dataclass(frozen=True)
class Fare:
    fare_id: str
    family: str


@dataclass(frozen=True)
class Ride:
    trip_id: str
    station_id: str
    slot: int
    fare_id: str


@dataclass(frozen=True)
class Query:
    request_id: str
    sector_id: str
    from_slot: int
    until_slot: int
    k: int
    max_suppressed: int
    geo_weight: int
    time_weight: int
    fare_weight: int
    suppress_penalty: int


class InputError(ValueError):
    pass


class RequestError(ValueError):
    def __init__(self, reason: str, request_id: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.request_id = request_id


def valid_id(value: object, max_length: int = 48) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= max_length and ID.fullmatch(value) is not None


def natural(value: str, ceiling: int, field: str) -> int:
    if not isinstance(value, str) or not COUNT.fullmatch(value):
        raise InputError(f"invalid {field}")
    number = int(value)
    if number > ceiling:
        raise InputError(f"{field} exceeds limit")
    return number


def read_rows(path: str, fields: set[str]):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(fields) or set(reader.fieldnames) != fields:
            raise InputError(f"incorrect CSV header: {path}")
        for row_number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise InputError(f"malformed CSV at {path}:{row_number}")
            yield row


def insert_once(catalog: dict, key: str, value: object, label: str):
    prior = catalog.get(key)
    if prior is not None and prior != value:
        raise InputError(f"conflicting {label} ID: {key}")
    catalog[key] = value


class Snapshot:
    def __init__(self, stations: dict[str, Station], fares: dict[str, Fare], rides: dict[str, Ride]):
        self.stations = stations
        self.fares = fares
        self.rides = rides
        self.sectors = {station.sector_id for station in stations.values()}

    @classmethod
    def load(cls, stations_path: str, fares_path: str, rides_path: str) -> "Snapshot":
        stations: dict[str, Station] = {}
        for row in read_rows(stations_path, {"station_id", "route_id", "sector_id"}):
            if not all(valid_id(x) for x in row.values()):
                raise InputError("invalid station reference")
            item = Station(**row)
            insert_once(stations, item.station_id, item, "station")
        fares: dict[str, Fare] = {}
        for row in read_rows(fares_path, {"fare_id", "family"}):
            if not all(valid_id(x) for x in row.values()):
                raise InputError("invalid fare reference")
            item = Fare(**row)
            insert_once(fares, item.fare_id, item, "fare")
        rides: dict[str, Ride] = {}
        for row in read_rows(rides_path, {"trip_id", "station_id", "slot", "fare_id"}):
            if not all(valid_id(row[x]) for x in ("trip_id", "station_id", "fare_id")):
                raise InputError("invalid trip ID/reference")
            slot = natural(row["slot"], 671, "slot")
            if row["station_id"] not in stations or row["fare_id"] not in fares:
                raise InputError("trip has unknown reference")
            item = Ride(row["trip_id"], row["station_id"], slot, row["fare_id"])
            insert_once(rides, item.trip_id, item, "trip")
        return cls(stations, fares, rides)


def parse_query(line: str, sectors: set[str]) -> Query:
    try:
        item = json.loads(line)
    except (ValueError, TypeError):
        raise RequestError("invalid_query")
    if not isinstance(item, dict):
        raise RequestError("invalid_query")
    request_id = item.get("request_id")
    recovered = request_id if valid_id(request_id, 128) else None
    keys = ("from_slot", "until_slot", "k", "max_suppressed", "geo_weight", "time_weight", "fare_weight", "suppress_penalty")
    ranges = ((0, 671), (1, 672), (2, 10000), (0, 1000000000), (0, 100), (0, 100), (0, 100), (0, 1000))
    if recovered is None or not valid_id(item.get("sector_id")):
        raise RequestError("invalid_query", recovered)
    values = [item.get(key) for key in keys]
    if any(type(v) is not int or not lo <= v <= hi for v, (lo, hi) in zip(values, ranges)):
        raise RequestError("invalid_query", recovered)
    if values[0] >= values[1]:
        raise RequestError("invalid_query", recovered)
    if item["sector_id"] not in sectors:
        raise RequestError("unknown_sector", recovered)
    return Query(recovered, item["sector_id"], *values)


class ReleasePlanner:
    """Implement the customer release capability here; you own the approach."""

    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot

    def plan(self, query: Query) -> dict:
        return {"request_id": query.request_id, "status": "not_implemented"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TransitShield ridership release review")
    parser.add_argument("command", choices=("check", "plan"))
    parser.add_argument("--stations", required=True)
    parser.add_argument("--fares", required=True)
    parser.add_argument("--rides", required=True)
    parser.add_argument("--queries")
    args = parser.parse_args(argv)
    try:
        snapshot = Snapshot.load(args.stations, args.fares, args.rides)
        if args.command == "check":
            print(json.dumps({"stations": len(snapshot.stations), "fares": len(snapshot.fares), "rides": len(snapshot.rides), "sectors": len(snapshot.sectors)}, separators=(",", ":")))
            return 0
        if not args.queries:
            parser.error("plan requires --queries")
        planner = ReleasePlanner(snapshot)
        with open(args.queries, encoding="utf-8") as handle:
            for line in handle:
                try:
                    query = parse_query(line, snapshot.sectors)
                    result = planner.plan(query)
                except RequestError as exc:
                    result = {"request_id": exc.request_id, "status": "invalid", "reason": exc.reason}
                print(json.dumps(result, separators=(",", ":")))
        return 0
    except (InputError, OSError, UnicodeError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
