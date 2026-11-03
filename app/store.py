"""In-memory fixture-backed state for the existing lot console."""
from copy import deepcopy
import json
from pathlib import Path
from threading import RLock

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "workspace.json"


class StoreError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class LotStore:
    def __init__(self, data=None):
        source = deepcopy(data) if data is not None else json.loads(FIXTURE.read_text())
        self.plants = {p["id"]: p for p in source["plants"]}
        self.specs = {s["product"]: s for s in source["specifications"]}
        self.lots = {lot["id"]: lot for lot in source["lots"]}
        self.samples = list(source["samples"])
        self.dataset_revision = 1
        self.lock = RLock()

    def list_lots(self, plant="", status="", q="", limit=50):
        if plant and plant not in self.plants:
            raise StoreError(400, "BAD_PLANT", "Unknown plant")
        if status not in ("", "open", "closed"):
            raise StoreError(400, "BAD_STATUS", "Invalid status filter")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise StoreError(400, "BAD_LIMIT", "Limit must be between 1 and 100")
        if not isinstance(q, str) or len(q) > 120:
            raise StoreError(400, "BAD_QUERY", "Search must be a short string")
        with self.lock:
            matches = [deepcopy(lot) for lot in self.lots.values()
                       if (not plant or lot["plantId"] == plant)
                       and (not status or lot["status"] == status)
                       and (not q or q.casefold() in (lot["id"] + " " + lot["product"] + " " + lot["note"]).casefold())]
            matches.sort(key=lambda x: x["id"])
            return {"lots": matches[:limit], "total": len(matches), "datasetRevision": self.dataset_revision}

    def detail(self, lot_id):
        with self.lock:
            lot = self.lots.get(lot_id)
            if lot is None:
                raise StoreError(404, "LOT_NOT_FOUND", "Unknown lot")
            return {"lot": deepcopy(lot), "specification": deepcopy(self.specs[lot["product"]]),
                    "samples": deepcopy([s for s in self.samples if s["lotId"] == lot_id]),
                    "datasetRevision": self.dataset_revision}

    def edit_note(self, lot_id, note, expected_revision):
        if not isinstance(note, str) or len(note.strip()) > 500:
            raise StoreError(400, "BAD_NOTE", "Note must be at most 500 characters")
        if type(expected_revision) is not int or expected_revision < 0:
            raise StoreError(400, "BAD_REVISION", "Expected revision must be a nonnegative integer")
        with self.lock:
            lot = self.lots.get(lot_id)
            if lot is None:
                raise StoreError(404, "LOT_NOT_FOUND", "Unknown lot")
            if lot["revision"] != expected_revision:
                raise StoreError(409, "STALE_LOT", "Lot changed; reload before editing")
            cleaned = note.strip()
            if lot["note"] != cleaned:
                lot["note"] = cleaned
                lot["revision"] += 1
                self.dataset_revision += 1
            return {"lot": deepcopy(lot), "datasetRevision": self.dataset_revision}


store = LotStore()
