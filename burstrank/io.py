from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import AccessEvent, Client, Policy, Query


class DataValidationError(ValueError):
    pass


def parse_instant(value: str) -> datetime:
    text = value.strip()
    if not text:
        raise DataValidationError("timestamp must not be empty")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise DataValidationError(f"invalid RFC3339 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise DataValidationError(f"timestamp must include an offset: {value}")
    return parsed.astimezone(timezone.utc)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_clients(path: str | Path) -> dict[str, Client]:
    clients: dict[str, Client] = {}
    for row in _read_csv(path):
        client_id = row["client_id"].strip()
        region = row["region"].strip()
        display_name = row["display_name"].strip()
        if not client_id or not region or not display_name:
            raise DataValidationError("clients require non-empty client_id, region, and display_name")
        if client_id in clients:
            raise DataValidationError(f"duplicate client_id: {client_id}")
        clients[client_id] = Client(client_id, region, display_name)
    if not clients:
        raise DataValidationError("at least one client is required")
    return clients


def load_policies(path: str | Path) -> dict[str, Policy]:
    policies: dict[str, Policy] = {}
    for row in _read_csv(path):
        region = row["region"].strip()
        try:
            window_minutes = int(row["window_minutes"])
            max_k = int(row["max_k"])
        except ValueError as exc:
            raise DataValidationError("policy window_minutes and max_k must be integers") from exc
        if not region or window_minutes <= 0 or max_k <= 0:
            raise DataValidationError("policies require a region and positive window_minutes/max_k")
        if region in policies:
            raise DataValidationError(f"duplicate policy region: {region}")
        policies[region] = Policy(region, window_minutes, max_k)
    if not policies:
        raise DataValidationError("at least one policy is required")
    return policies


def load_events(path: str | Path, clients: dict[str, Client]) -> list[AccessEvent]:
    by_id: dict[str, tuple[str, str, datetime]] = {}
    events: list[AccessEvent] = []
    for row in _read_csv(path):
        event_id = row["event_id"].strip()
        client_id = row["client_id"].strip()
        credential_id = row["credential_id"].strip()
        occurred_at = parse_instant(row["occurred_at"])
        if not event_id or not client_id or not credential_id:
            raise DataValidationError("events require non-empty event_id, client_id, and credential_id")
        if client_id not in clients:
            raise DataValidationError(f"unknown client_id in events: {client_id}")
        signature = (client_id, credential_id, occurred_at)
        if event_id in by_id:
            if by_id[event_id] != signature:
                raise DataValidationError(f"conflicting reuse of event_id: {event_id}")
            continue
        by_id[event_id] = signature
        events.append(AccessEvent(event_id, client_id, credential_id, occurred_at))
    return events


def load_queries(path: str | Path) -> list[Query]:
    queries: list[Query] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DataValidationError(f"invalid JSON on query line {line_number}") from exc
            request_id = str(row.get("request_id", "")).strip()
            region = str(row.get("region", "")).strip()
            if not request_id or request_id in seen:
                raise DataValidationError("query request_id values must be unique and non-empty")
            seen.add(request_id)
            try:
                k = int(row.get("k"))
            except (TypeError, ValueError) as exc:
                raise DataValidationError(f"query {request_id} has non-integer k") from exc
            queries.append(Query(request_id, region, parse_instant(str(row.get("as_of", ""))), k))
    return queries


@dataclass(frozen=True)
class Dataset:
    clients: dict[str, Client]
    policies: dict[str, Policy]
    events: list[AccessEvent]
    queries: list[Query]


def load_dataset(clients_path: str, policies_path: str, events_path: str, queries_path: str) -> Dataset:
    clients = load_clients(clients_path)
    policies = load_policies(policies_path)
    for client in clients.values():
        if client.region not in policies:
            raise DataValidationError(f"client {client.client_id} references unknown policy region {client.region}")
    events = load_events(events_path, clients)
    queries = load_queries(queries_path)
    return Dataset(clients, policies, events, queries)
