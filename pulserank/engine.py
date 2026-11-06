"""Customer-facing latency investigation interface."""
from .models import Query, Snapshot


class LatencyAudit:
    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot

    def assess(self, query: Query) -> dict:
        return {"query_id": query.query_id, "status": "not_implemented"}
