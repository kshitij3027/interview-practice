import json
from pathlib import Path
from .models import Endpoint, Delivery

VALID_STATUSES = {"delivered", "failed", "quarantined"}
VALID_SIMULATIONS = {"success", "retry_once", "permanent_error"}

def load_fixtures(endpoint_path="fixtures/endpoints.json", delivery_path="fixtures/deliveries.jsonl"):
    endpoint_rows = json.loads(Path(endpoint_path).read_text())
    endpoints = []
    ids = set()
    for row in endpoint_rows:
        e = Endpoint(**row)
        if not all((e.id.strip(), e.tenant.strip(), e.name.strip(), e.url.strip())):
            raise ValueError("endpoint has blank required field")
        if e.id in ids:
            raise ValueError(f"duplicate endpoint id: {e.id}")
        if e.revision < 1:
            raise ValueError("endpoint revision must be positive")
        ids.add(e.id)
        endpoints.append(e)

    deliveries = []
    delivery_ids = set()
    for raw in Path(delivery_path).read_text().splitlines():
        if not raw.strip():
            continue
        d = Delivery(**json.loads(raw))
        if d.id in delivery_ids:
            raise ValueError(f"duplicate delivery id: {d.id}")
        if d.endpointId not in ids:
            raise ValueError(f"unknown endpoint for delivery: {d.id}")
        if d.sequence < 1 or not d.eventId.strip() or not d.streamKey.strip() or not d.receivedAt.strip():
            raise ValueError(f"invalid delivery: {d.id}")
        if d.status not in VALID_STATUSES:
            raise ValueError(f"invalid delivery status: {d.id}")
        if d.simulation not in VALID_SIMULATIONS:
            raise ValueError(f"invalid simulation: {d.id}")
        delivery_ids.add(d.id)
        deliveries.append(d)
    return endpoints, deliveries
