from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SIZE_ORDER = {"S": 0, "M": 1, "L": 2, "XL": 3}
VALID_STATUSES = {"active", "maintenance", "offline"}


@dataclass(frozen=True)
class Locker:
    locker_id: str
    lat: float
    lon: float
    status: str
    max_parcel_size: str
    available_slots: int
    queue_minutes: int
    capabilities: frozenset[str]


@dataclass(frozen=True)
class Query:
    request_id: str | None
    lat: float
    lon: float
    parcel_size: str
    required_capabilities: frozenset[str]
    max_distance_meters: int
    limit: int


@dataclass(frozen=True)
class QueryRecord:
    request_id: str | None
    query: Query | None
    error_reason: str | None
    raw: Any = None
