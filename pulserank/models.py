from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    service_id: str
    region: str
    budget_us: int


@dataclass(frozen=True)
class Observation:
    request_id: str
    revision: int
    op: str
    service_id: str | None
    region: str | None
    at_ms: int | None
    latency_us: int | None


@dataclass(frozen=True)
class Query:
    query_id: str
    service_id: str
    region: str
    from_ms: int
    until_ms: int


@dataclass(frozen=True)
class Snapshot:
    scopes: dict[tuple[str, str], Scope]
    latest: dict[str, Observation]
    rows_seen: int

    @property
    def live(self) -> list[Observation]:
        return [row for row in self.latest.values() if row.op == "upsert"]
