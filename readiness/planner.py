from __future__ import annotations

from .models import Query, Snapshot


class ReadinessResolver:
    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot

    def resolve_all(self, queries: list[Query]) -> list[dict]:
        raise NotImplementedError("historical readiness resolution is not implemented")
