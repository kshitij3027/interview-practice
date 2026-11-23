"""Customer-facing dataset readiness interface."""

from __future__ import annotations

from .catalog import Catalog
from .requests import Query


class BatchPath:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def assess(self, query: Query) -> dict:
        raise NotImplementedError("Implement the dataset readiness assessment during the interview")
