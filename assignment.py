"""Incident-dispatch planning entry point. Choose the implementation strategy."""
from __future__ import annotations

from records import Snapshot


def plan(snapshot: Snapshot) -> dict:
    """Return a customer-facing plan for the validated snapshot."""
    return {"status": "not_implemented"}
