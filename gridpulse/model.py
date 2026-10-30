"""Validated charging records shared by the CLI and the demand engine."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionRevision:
    session_id: str
    revision: int
    site_id: str | None
    mode: str
    start_ms: int | None
    end_ms: int | None
    kw: int | None


@dataclass(frozen=True)
class Catalog:
    sites: frozenset[str]
    revisions: tuple[SessionRevision, ...]


@dataclass(frozen=True)
class Query:
    request_id: str
    site_id: str
    from_ms: int
    until_ms: int
