"""Customer-facing matching interface. You choose the index and matching strategy."""
from __future__ import annotations

from data_io import Listing, Query


class Gallery:
    def __init__(self, listings: list[Listing]) -> None:
        self.listings = listings

    def find(self, query: Query) -> list[tuple[Listing, int]]:
        """Return exact, correctly ordered eligible matches as (listing, bit_errors)."""
        raise NotImplementedError("candidate matching implementation is required")
