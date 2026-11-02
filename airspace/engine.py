"""Customer-facing waypoint restriction lookup. The implementation is yours."""
from __future__ import annotations

from .io import Query, Zone


class AirspaceReview:
    def __init__(self, zones: list[Zone]):
        self.zones = zones

    def select(self, query: Query) -> list[str]:
        """Return up to query.limit matching zone IDs in contract rank order.

        Intentionally unimplemented: choose your own design and explain its tradeoffs.
        """
        return []
