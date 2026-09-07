from __future__ import annotations

from collections import defaultdict

from .models import Adapter, Schema


class Catalog:
    def __init__(self, schemas: dict[str, Schema], adapters: tuple[Adapter, ...]):
        self.schemas = dict(schemas)
        self.adapters = tuple(adapters)
        self.adapter_ids = frozenset(adapter.adapter_id for adapter in adapters)

        outgoing: dict[str, list[Adapter]] = defaultdict(list)
        for adapter in adapters:
            outgoing[adapter.from_schema].append(adapter)
        self.outgoing = {
            schema_id: tuple(sorted(values, key=lambda adapter: adapter.adapter_id))
            for schema_id, values in outgoing.items()
        }

    def eligible_outgoing(self, schema_id: str, region: str, disabled: frozenset[str]) -> tuple[Adapter, ...]:
        return tuple(
            adapter
            for adapter in self.outgoing.get(schema_id, ())
            if adapter.adapter_id not in disabled
            and (adapter.region == "*" or adapter.region == region)
        )
