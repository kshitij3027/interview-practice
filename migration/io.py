from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Adapter, MigrationRequest, Schema


class DatasetError(ValueError):
    pass


def _non_negative_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise DatasetError(f"{field} must be an integer") from exc
    if parsed < 0:
        raise DatasetError(f"{field} must be non-negative")
    return parsed


def load_schemas(path: str | Path) -> dict[str, Schema]:
    schemas: dict[str, Schema] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            schema = Schema(
                schema_id=row["schema_id"].strip(),
                system=row["system"].strip(),
                status=row["status"].strip(),
            )
            if not schema.schema_id:
                raise DatasetError("schema_id must be non-empty")
            if schema.status not in {"active", "deprecated"}:
                raise DatasetError(f"invalid schema status for {schema.schema_id}")
            previous = schemas.get(schema.schema_id)
            if previous is not None and previous != schema:
                raise DatasetError(f"conflicting schema definition: {schema.schema_id}")
            schemas[schema.schema_id] = schema
    return schemas


def load_adapters(path: str | Path, schemas: dict[str, Schema]) -> tuple[Adapter, ...]:
    by_id: dict[str, Adapter] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            adapter = Adapter(
                adapter_id=row["adapter_id"].strip(),
                from_schema=row["from_schema"].strip(),
                to_schema=row["to_schema"].strip(),
                region=row["region"].strip(),
                latency_ms=_non_negative_int(row["latency_ms"], "latency_ms"),
                quality_loss_ppm=_non_negative_int(row["quality_loss_ppm"], "quality_loss_ppm"),
                cost_micros=_non_negative_int(row["cost_micros"], "cost_micros"),
            )
            if not adapter.adapter_id:
                raise DatasetError("adapter_id must be non-empty")
            if adapter.region == "":
                raise DatasetError(f"adapter region must be non-empty: {adapter.adapter_id}")
            if adapter.from_schema not in schemas or adapter.to_schema not in schemas:
                raise DatasetError(f"unknown adapter endpoint: {adapter.adapter_id}")
            previous = by_id.get(adapter.adapter_id)
            if previous is not None and previous != adapter:
                raise DatasetError(f"conflicting adapter definition: {adapter.adapter_id}")
            by_id[adapter.adapter_id] = adapter
    return tuple(sorted(by_id.values(), key=lambda adapter: adapter.adapter_id))


def load_requests(path: str | Path) -> tuple[MigrationRequest, ...]:
    requests: list[MigrationRequest] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise DatasetError(f"invalid JSON on request line {line_number}") from exc
            disabled = value.get("disabled_adapters", [])
            if not isinstance(disabled, list) or not all(isinstance(item, str) for item in disabled):
                raise DatasetError(f"disabled_adapters must be a string array on line {line_number}")
            request = MigrationRequest(
                request_id=str(value["request_id"]),
                from_schema=str(value["from_schema"]),
                to_schema=str(value["to_schema"]),
                region=str(value["region"]),
                max_latency_ms=_non_negative_int(str(value["max_latency_ms"]), "max_latency_ms"),
                max_quality_loss_ppm=_non_negative_int(str(value["max_quality_loss_ppm"]), "max_quality_loss_ppm"),
                max_adapters=_non_negative_int(str(value["max_adapters"]), "max_adapters"),
                disabled_adapters=tuple(disabled),
            )
            requests.append(request)
    return tuple(requests)


def validate_dataset(
    schemas_path: str | Path,
    adapters_path: str | Path,
    requests_path: str | Path,
) -> dict[str, int]:
    schemas = load_schemas(schemas_path)
    adapters = load_adapters(adapters_path, schemas)
    requests = load_requests(requests_path)
    return {
        "schemas": len(schemas),
        "adapters": len(adapters),
        "requests": len(requests),
    }
