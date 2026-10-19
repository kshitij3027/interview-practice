"""Customer-facing estimation interface."""
from __future__ import annotations

from .catalog import Update
from .queries import QuoteRequest


class QuoteEngine:
    def __init__(self, events: list[Update]):
        self.events = events
        self.markets = {event.market for event in events}

    def quote(self, request: QuoteRequest) -> dict:
        raise NotImplementedError("Implement quote estimation during the interview")
