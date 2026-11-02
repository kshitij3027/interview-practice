"""CacheFlow replay boundary."""
from __future__ import annotations

from .io import Catalog, Event


class CacheReplay:
    def __init__(self, catalog: Catalog, capacity_kb: int):
        self.catalog = catalog
        self.capacity_kb = capacity_kb

    def apply(self, event: Event) -> dict:
        return {"event_id": event.event_id, "status": "not_implemented"}
