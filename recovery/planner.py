from __future__ import annotations

from .models import Booking, Lane, Outage, RecoveryPlan


class RecoveryPlanner:
    def __init__(self, lanes: dict[str, Lane], bookings: list[Booking]) -> None:
        self.lanes = lanes
        self.bookings = tuple(bookings)

    def plan(self, outage: Outage) -> RecoveryPlan:
        raise NotImplementedError("recovery planning is not implemented")
