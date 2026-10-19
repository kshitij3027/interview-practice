"""Customer-facing PromiseClock interface. The primary feature is not implemented."""
from __future__ import annotations

from typing import Any
from .data import Snapshot


class PromiseClock:
    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot

    def resolve(self, request: dict[str, Any]) -> dict[str, Any]:
        return {"request_id": request["request_id"], "status": "not_implemented"}
