from __future__ import annotations

from .catalog import Catalog
from .io import Request


class CompatibilityPlanner:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def plan(self, request: Request) -> dict:
        raise NotImplementedError("implement CompatibilityPlanner.plan")
