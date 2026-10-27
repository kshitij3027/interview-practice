"""Fixture-backed operations workspace for contractor visits."""
from __future__ import annotations

import copy
import json
import threading
from pathlib import Path


class DomainError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details or {}


class VisitStore:
    def __init__(self, workspace_path: str | Path, credentials_path: str | Path):
        self._lock = threading.RLock()
        workspace = json.loads(Path(workspace_path).read_text(encoding="utf-8"))
        self.dataset_revision = workspace["datasetRevision"]
        self.sites = {s["id"]: s for s in workspace["sites"]}
        self.vendors = {v["id"]: v for v in workspace["vendors"]}
        self.visits = {v["id"]: v for v in workspace["visits"]}
        self.credential_rows = [json.loads(line) for line in Path(credentials_path).read_text(encoding="utf-8").splitlines() if line.strip()]
        self.tenants = sorted({site["tenantId"] for site in self.sites.values()})

    def _tenant(self, tenant_id):
        if tenant_id not in self.tenants:
            raise DomainError(400, "invalid_tenant", "Choose an existing tenant.")

    def _visit(self, tenant_id, visit_id):
        self._tenant(tenant_id)
        visit = self.visits.get(visit_id)
        if visit is None or visit["tenantId"] != tenant_id:
            raise DomainError(404, "visit_not_found", "Visit not found.")
        return visit

    def _view(self, visit):
        result = copy.deepcopy(visit)
        vendor = self.vendors[visit["vendorId"]]
        site = self.sites[visit["siteId"]]
        result["vendorName"] = vendor["name"]
        result["vendorActive"] = vendor["active"]
        result["siteName"] = site["name"]
        return result

    def list_visits(self, tenant_id, status="all", query="", limit=100):
        with self._lock:
            self._tenant(tenant_id)
            if status not in {"all", "requested", "confirmed", "issued", "cancelled"}:
                raise DomainError(400, "invalid_status", "Unknown visit status.")
            if not isinstance(query, str) or len(query) > 120:
                raise DomainError(400, "invalid_query", "Search must be text of at most 120 characters.")
            if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
                raise DomainError(400, "invalid_limit", "Limit must be between 1 and 100.")
            normalized = query.strip().casefold()
            matches = []
            for v in self.visits.values():
                if v["tenantId"] != tenant_id or (status != "all" and v["status"] != status):
                    continue
                if normalized:
                    haystack = " ".join((v["id"], v["purpose"], self.vendors[v["vendorId"]]["name"], self.sites[v["siteId"]]["name"]))
                    if normalized not in haystack.casefold():
                        continue
                matches.append(v)
            matches.sort(key=lambda v: (v["startAt"], v["id"]))
            return {"items": [self._view(v) for v in matches[:limit]], "total": len(matches), "datasetRevision": self.dataset_revision}

    def get_visit(self, tenant_id, visit_id):
        with self._lock:
            return {"visit": self._view(self._visit(tenant_id, visit_id)), "datasetRevision": self.dataset_revision}

    def update_note(self, tenant_id, visit_id, body):
        with self._lock:
            visit = self._visit(tenant_id, visit_id)
            if not isinstance(body, dict) or set(body) != {"note", "expectedRevision"}:
                raise DomainError(400, "invalid_body", "Expected note and expectedRevision only.")
            note, expected = body["note"], body["expectedRevision"]
            if not isinstance(note, str) or len(note.strip()) > 240:
                raise DomainError(400, "invalid_note", "Note must be text of at most 240 characters.")
            if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
                raise DomainError(400, "invalid_revision", "Expected revision must be a nonnegative integer.")
            if visit["revision"] != expected:
                raise DomainError(409, "stale_revision", "The visit changed. Refresh before saving.", {"currentRevision": visit["revision"]})
            cleaned = note.strip()
            if cleaned != visit["note"]:
                visit["note"] = cleaned
                visit["revision"] += 1
                self.dataset_revision += 1
            return {"visit": self._view(visit), "datasetRevision": self.dataset_revision}
