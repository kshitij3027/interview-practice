"""Customer audit engine boundary. Choose your own implementation strategy."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uplink import Asset, Fragment

class AuditEngine:
    def __init__(self, assets: dict[str, Asset], fragments: list[Fragment]) -> None:
        self.assets = assets
        self.fragments = fragments

    def answer(self, request: dict) -> dict:
        """Return one customer-facing result for a valid request."""
        raise NotImplementedError("The customer audit capability is not implemented")
