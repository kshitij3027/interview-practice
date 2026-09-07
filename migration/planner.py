from __future__ import annotations

from .catalog import Catalog
from .models import MigrationRequest


class MigrationPlanner:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def plan(self, request: MigrationRequest) -> dict[str, object]:
        if request.from_schema not in self.catalog.schemas or request.to_schema not in self.catalog.schemas:
            return {
                "request_id": request.request_id,
                "status": "invalid",
                "reason": "unknown_schema",
            }

        if request.from_schema == request.to_schema:
            return {
                "request_id": request.request_id,
                "status": "planned",
                "adapter_ids": [],
                "schemas": [request.from_schema],
                "total_cost_micros": 0,
                "total_quality_loss_ppm": 0,
                "total_latency_ms": 0,
            }

        return {
            "request_id": request.request_id,
            "status": "not_implemented",
        }
