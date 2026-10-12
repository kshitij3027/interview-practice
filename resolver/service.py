"""Bundle selection service. The requested capability is not supplied."""

from __future__ import annotations

from .catalog import Catalog


class BundlePlanner:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def plan_request(self, request: dict) -> dict:
        """Return a plan for one validated request under the documented contract."""
        raise NotImplementedError("bundle planning is the interview feature")
