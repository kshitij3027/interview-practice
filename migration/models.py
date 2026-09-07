from dataclasses import dataclass


@dataclass(frozen=True)
class Schema:
    schema_id: str
    system: str
    status: str


@dataclass(frozen=True)
class Adapter:
    adapter_id: str
    from_schema: str
    to_schema: str
    region: str
    latency_ms: int
    quality_loss_ppm: int
    cost_micros: int


@dataclass(frozen=True)
class MigrationRequest:
    request_id: str
    from_schema: str
    to_schema: str
    region: str
    max_latency_ms: int
    max_quality_loss_ppm: int
    max_adapters: int
    disabled_adapters: tuple[str, ...]
