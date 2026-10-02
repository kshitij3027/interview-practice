from __future__ import annotations

from typing import Iterable

from .model import Locker, Query, QueryRecord


class LockerFinder:
    """Resolver for one immutable locker snapshot."""

    def __init__(self, lockers: Iterable[Locker]):
        self._lockers = tuple(lockers)

    def resolve(self, query: Query) -> dict:
        raise NotImplementedError("implement the locker search strategy")

    def resolve_all(self, records: Iterable[QueryRecord]) -> list[dict]:
        results: list[dict] = []
        for record in records:
            if record.query is None:
                results.append({"request_id": record.request_id, "status": "invalid", "reason": record.error_reason or "invalid_query"})
                continue
            results.append(self.resolve(record.query))
        return results
