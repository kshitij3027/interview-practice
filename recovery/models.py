from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Lane:
    lane_id: str
    site: str
    capabilities: frozenset[str]
    open_from: datetime
    open_until: datetime


@dataclass(frozen=True, slots=True)
class Booking:
    shipment_id: str
    site: str
    lane_id: str
    slot_start: datetime
    required_capability: str
    earliest_start: datetime
    latest_start: datetime
    priority: int


@dataclass(frozen=True, slots=True)
class Outage:
    outage_id: str
    site: str
    lane_ids: tuple[str, ...]
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class Assignment:
    shipment_id: str
    lane_id: str
    slot_start: datetime


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    outage_id: str
    assignments: tuple[Assignment, ...]
    unassigned: tuple[str, ...]
    assigned_priority: int
    assigned_count: int
    total_displacement_minutes: int
