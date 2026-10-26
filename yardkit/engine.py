"""Customer-facing resolution boundary; implement the feature here."""
from __future__ import annotations
from .data import Snapshot


class YardEngine:
    def __init__(self, snapshot: Snapshot):
        self.snapshot = snapshot

    def answer_all(self, requests: list[dict]) -> list[dict]:
        """Return results in the same order as the validated requests."""
        return [{"request_id": request["request_id"], "status": "not_implemented"} for request in requests]
