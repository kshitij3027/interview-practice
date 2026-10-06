from copy import deepcopy
from threading import Lock

class NotFound(Exception):
    pass

class StaleRevision(Exception):
    def __init__(self, current):
        super().__init__("stale revision")
        self.current = current

class Store:
    def __init__(self, endpoints, deliveries, dataset_revision=41):
        self._lock = Lock()
        self.endpoints = deepcopy(endpoints)
        self.deliveries = deepcopy(deliveries)
        self.dataset_revision = dataset_revision

    def _endpoint_json(self, endpoint):
        return endpoint.json(self.dataset_revision)

    def list_endpoints(self, tenant="", status=""):
        with self._lock:
            out = []
            for e in self.endpoints:
                if tenant and e.tenant != tenant:
                    continue
                if status == "enabled" and not e.enabled:
                    continue
                if status == "paused" and e.enabled:
                    continue
                rows = [d for d in self.deliveries if d.endpointId == e.id]
                item = self._endpoint_json(e)
                item["failedCount"] = sum(d.status in {"failed", "quarantined"} for d in rows)
                item["totalCount"] = len(rows)
                out.append(item)
            out.sort(key=lambda x: (x["tenant"], x["name"], x["id"]))
            return out

    def get_endpoint(self, endpoint_id):
        with self._lock:
            endpoint = next((e for e in self.endpoints if e.id == endpoint_id), None)
            if not endpoint:
                raise NotFound()
            rows = [d.json() for d in self.deliveries if d.endpointId == endpoint_id]
            rows.sort(key=lambda x: (x["receivedAt"], x["id"]), reverse=True)
            return {"endpoint": self._endpoint_json(endpoint), "deliveries": rows}

    def set_enabled(self, endpoint_id, enabled, expected_revision):
        with self._lock:
            endpoint = next((e for e in self.endpoints if e.id == endpoint_id), None)
            if not endpoint:
                raise NotFound()
            if endpoint.revision != expected_revision:
                raise StaleRevision(self._endpoint_json(endpoint))
            if endpoint.enabled == enabled:
                return {"endpoint": self._endpoint_json(endpoint), "changed": False}
            endpoint.enabled = enabled
            endpoint.revision += 1
            self.dataset_revision += 1
            return {"endpoint": self._endpoint_json(endpoint), "changed": True}
