"""Input contract for one incident-dispatch planning snapshot."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"[A-Za-z0-9_-]{1,48}\Z")
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z")


class SnapshotError(ValueError):
    pass


@dataclass(frozen=True)
class Pod:
    pod_id: str
    max_parallel: int


@dataclass(frozen=True)
class Responder:
    responder_id: str
    pod_id: str
    capacity: int


@dataclass(frozen=True)
class Incident:
    incident_id: str
    severity: str


@dataclass(frozen=True)
class Route:
    incident_id: str
    responder_id: str
    eta_minutes: int


@dataclass(frozen=True)
class Snapshot:
    pods: tuple[Pod, ...]
    responders: tuple[Responder, ...]
    incidents: tuple[Incident, ...]
    routes: tuple[Route, ...]


def _read_csv(path: str | Path, columns: tuple[str, ...]):
    try:
        with open(path, encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != list(columns):
                raise SnapshotError(f"{path}: expected header {','.join(columns)}")
            for line_no, row in enumerate(reader, 2):
                if None in row or any(row[column] is None for column in columns):
                    raise SnapshotError(f"{path}:{line_no}: malformed CSV record")
                yield line_no, row
    except (OSError, UnicodeError, csv.Error) as error:
        raise SnapshotError(f"{path}: cannot read snapshot: {error}") from error


def _id(text: str, location: str) -> str:
    if not _ID.fullmatch(text):
        raise SnapshotError(f"{location}: invalid ID {text!r}")
    return text


def _number(text: str, bound: int, location: str) -> int:
    if not _DECIMAL.fullmatch(text):
        raise SnapshotError(f"{location}: invalid integer {text!r}")
    value = int(text)
    if value > bound:
        raise SnapshotError(f"{location}: exceeds limit {bound}")
    return value


def _add_by_id(table: dict, key, item, location: str) -> None:
    previous = table.setdefault(key, item)
    if previous != item:
        raise SnapshotError(f"{location}: conflicting reuse of {key!r}")


def load_snapshot(pods_path: str | Path, responders_path: str | Path,
                  incidents_path: str | Path, routes_path: str | Path) -> Snapshot:
    pods: dict[str, Pod] = {}
    for line, row in _read_csv(pods_path, ("pod_id", "max_parallel")):
        where = f"{pods_path}:{line}"
        pod = Pod(_id(row["pod_id"], where), _number(row["max_parallel"], 20, where))
        _add_by_id(pods, pod.pod_id, pod, where)

    responders: dict[str, Responder] = {}
    for line, row in _read_csv(responders_path, ("responder_id", "pod_id", "capacity")):
        where = f"{responders_path}:{line}"
        responder = Responder(_id(row["responder_id"], where),
                              _id(row["pod_id"], where), _number(row["capacity"], 8, where))
        if responder.pod_id not in pods:
            raise SnapshotError(f"{where}: unknown pod {responder.pod_id}")
        _add_by_id(responders, responder.responder_id, responder, where)

    incidents: dict[str, Incident] = {}
    for line, row in _read_csv(incidents_path, ("incident_id", "severity")):
        where = f"{incidents_path}:{line}"
        incident = Incident(_id(row["incident_id"], where), row["severity"])
        if incident.severity not in {"sev0", "sev1", "sev2"}:
            raise SnapshotError(f"{where}: invalid severity {incident.severity!r}")
        _add_by_id(incidents, incident.incident_id, incident, where)

    routes: dict[tuple[str, str], Route] = {}
    for line, row in _read_csv(routes_path, ("incident_id", "responder_id", "eta_minutes")):
        where = f"{routes_path}:{line}"
        route = Route(_id(row["incident_id"], where), _id(row["responder_id"], where),
                      _number(row["eta_minutes"], 240, where))
        if route.incident_id not in incidents or route.responder_id not in responders:
            raise SnapshotError(f"{where}: unknown incident or responder")
        _add_by_id(routes, (route.incident_id, route.responder_id), route, where)

    return Snapshot(tuple(sorted(pods.values(), key=lambda x: x.pod_id)),
                    tuple(sorted(responders.values(), key=lambda x: x.responder_id)),
                    tuple(sorted(incidents.values(), key=lambda x: x.incident_id)),
                    tuple(sorted(routes.values(), key=lambda x: (x.incident_id, x.responder_id))))
