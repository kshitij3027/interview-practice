"""AidLink planning boundary. Implement the requested capability here."""
from __future__ import annotations

from .data import Catalog, Request


def plan(catalog: Catalog, request: Request) -> dict | None:
    """Return a valid shipment plan, or None while the feature is not built."""
    return None
