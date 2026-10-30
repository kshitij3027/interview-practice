"""The requested byte-signature inspection capability goes here."""

from __future__ import annotations

from .catalog import Catalog
from .requests import ScanRequest


class SignalScanner:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def scan(self, request: ScanRequest) -> dict:
        # The operational API is wired up, but matching is intentionally absent.
        # Replace this result when you implement the customer requirement.
        return {"request_id": request.request_id, "status": "not_implemented"}
