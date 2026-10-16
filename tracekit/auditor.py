"""The exercise's audit boundary. See README.md for the customer contract."""
from __future__ import annotations
from .reader import Route

class ScanAuditor:
    def reconcile(self, route: Route, scans: tuple[str, ...], max_repairs: int) -> list[dict] | None:
        """Return an exact repair sequence, or None when beyond the budget."""
        raise NotImplementedError("Implement the customer audit contract")
