from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Client:
    client_id: str
    region: str
    display_name: str


@dataclass(frozen=True)
class Policy:
    region: str
    window_minutes: int
    max_k: int


@dataclass(frozen=True)
class AccessEvent:
    event_id: str
    client_id: str
    credential_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class Query:
    request_id: str
    region: str
    as_of: datetime
    k: int
