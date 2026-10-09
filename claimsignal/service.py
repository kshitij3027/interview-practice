"""Business-level resolution entry point."""
from __future__ import annotations

from .data import Case, Rule


class ClaimResolver:
    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def resolve_case(self, case: Case) -> dict:
        raise NotImplementedError("Implement the requested case resolver")
