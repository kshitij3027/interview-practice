from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import Booking, Lane, Outage
from .time_utils import SLOT_SECONDS, parse_utc, require_aligned


def _require_text(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} must be non-empty")
    return text


def load_lanes(path: str | Path) -> dict[str, Lane]:
    lanes: dict[str, Lane] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            lane_id = _require_text(row.get("lane_id"), f"lanes row {row_number} lane_id")
            if lane_id in lanes:
                raise ValueError(f"duplicate lane_id: {lane_id}")
            site = _require_text(row.get("site"), f"lanes row {row_number} site")
            raw_caps = _require_text(row.get("capabilities"), f"lanes row {row_number} capabilities")
            caps = frozenset(part.strip() for part in raw_caps.split("|") if part.strip())
            if not caps:
                raise ValueError(f"lane {lane_id} must have at least one capability")
            open_from = parse_utc(row.get("open_from", ""), field=f"lane {lane_id} open_from")
            open_until = parse_utc(row.get("open_until", ""), field=f"lane {lane_id} open_until")
            require_aligned(open_from, field=f"lane {lane_id} open_from")
            require_aligned(open_until, field=f"lane {lane_id} open_until")
            if open_from >= open_until:
                raise ValueError(f"lane {lane_id} must open before it closes")
            lanes[lane_id] = Lane(lane_id, site, caps, open_from, open_until)
    return lanes


def load_bookings(path: str | Path) -> list[Booking]:
    bookings: list[Booking] = []
    seen: set[str] = set()
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            shipment_id = _require_text(row.get("shipment_id"), f"bookings row {row_number} shipment_id")
            if shipment_id in seen:
                raise ValueError(f"duplicate shipment_id: {shipment_id}")
            seen.add(shipment_id)
            site = _require_text(row.get("site"), f"shipment {shipment_id} site")
            lane_id = _require_text(row.get("lane_id"), f"shipment {shipment_id} lane_id")
            required = _require_text(row.get("required_capability"), f"shipment {shipment_id} required_capability")
            slot_start = parse_utc(row.get("slot_start", ""), field=f"shipment {shipment_id} slot_start")
            earliest = parse_utc(row.get("earliest_start", ""), field=f"shipment {shipment_id} earliest_start")
            latest = parse_utc(row.get("latest_start", ""), field=f"shipment {shipment_id} latest_start")
            for field, value in (("slot_start", slot_start), ("earliest_start", earliest), ("latest_start", latest)):
                require_aligned(value, field=f"shipment {shipment_id} {field}")
            try:
                priority = int(_require_text(row.get("priority"), f"shipment {shipment_id} priority"))
            except ValueError as exc:
                raise ValueError(f"shipment {shipment_id} priority must be an integer") from exc
            if priority <= 0:
                raise ValueError(f"shipment {shipment_id} priority must be positive")
            if not earliest <= slot_start <= latest:
                raise ValueError(f"shipment {shipment_id} baseline slot must be inside its replacement window")
            bookings.append(Booking(shipment_id, site, lane_id, slot_start, required, earliest, latest, priority))
    return bookings


def load_outages(path: str | Path) -> list[Outage]:
    outages: list[Outage] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"outages line {line_number} is not valid JSON") from exc
            outage_id = _require_text(payload.get("outage_id"), f"outages line {line_number} outage_id")
            if outage_id in seen:
                raise ValueError(f"duplicate outage_id: {outage_id}")
            seen.add(outage_id)
            site = _require_text(payload.get("site"), f"outage {outage_id} site")
            raw_lanes = payload.get("lane_ids")
            if not isinstance(raw_lanes, list) or not raw_lanes:
                raise ValueError(f"outage {outage_id} lane_ids must be a non-empty array")
            lane_ids = tuple(_require_text(item, f"outage {outage_id} lane_id") for item in raw_lanes)
            if len(set(lane_ids)) != len(lane_ids):
                raise ValueError(f"outage {outage_id} repeats a lane_id")
            start = parse_utc(str(payload.get("start", "")), field=f"outage {outage_id} start")
            end = parse_utc(str(payload.get("end", "")), field=f"outage {outage_id} end")
            require_aligned(start, field=f"outage {outage_id} start")
            require_aligned(end, field=f"outage {outage_id} end")
            if start >= end:
                raise ValueError(f"outage {outage_id} start must be before end")
            outages.append(Outage(outage_id, site, lane_ids, start, end))
    return outages


def validate_baseline(lanes: dict[str, Lane], bookings: Iterable[Booking], outages: Iterable[Outage]) -> None:
    occupied: set[tuple[str, object]] = set()
    for booking in bookings:
        lane = lanes.get(booking.lane_id)
        if lane is None:
            raise ValueError(f"shipment {booking.shipment_id} references unknown lane {booking.lane_id}")
        if lane.site != booking.site:
            raise ValueError(f"shipment {booking.shipment_id} site does not match lane site")
        if booking.required_capability not in lane.capabilities:
            raise ValueError(f"shipment {booking.shipment_id} baseline lane lacks required capability")
        slot_end_ts = booking.slot_start.timestamp() + SLOT_SECONDS
        if booking.slot_start < lane.open_from or slot_end_ts > lane.open_until.timestamp():
            raise ValueError(f"shipment {booking.shipment_id} baseline slot is outside lane operating window")
        key = (booking.lane_id, booking.slot_start)
        if key in occupied:
            raise ValueError(f"baseline double-booking at {booking.lane_id} {booking.slot_start.isoformat()}")
        occupied.add(key)

    for outage in outages:
        for lane_id in outage.lane_ids:
            lane = lanes.get(lane_id)
            if lane is None:
                raise ValueError(f"outage {outage.outage_id} references unknown lane {lane_id}")
            if lane.site != outage.site:
                raise ValueError(f"outage {outage.outage_id} lane {lane_id} belongs to a different site")
