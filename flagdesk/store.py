from __future__ import annotations
import copy, json, threading
from pathlib import Path
from typing import Any
from .models import Flag

class StoreError(Exception): pass
class NotFound(StoreError): pass
class ValidationError(StoreError): pass
class StaleRevision(StoreError):
    def __init__(self, current: dict[str, Any]):
        super().__init__("stale revision")
        self.current = current

class FlagStore:
    def __init__(self, fixture_path: str | Path):
        payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        self._lock = threading.RLock()
        self._dataset_revision = int(payload["datasetRevision"])
        self._flags: dict[str, Flag] = {}
        for raw in payload["flags"]:
            flag = Flag(
                id=raw["id"], key=raw["key"], name=raw["name"], owner=raw["owner"],
                status=raw["status"], revision=int(raw["revision"]),
                operator_note=raw.get("operatorNote", ""),
                published_config=copy.deepcopy(raw["publishedConfig"]),
            )
            if flag.id in self._flags:
                raise ValidationError(f"duplicate flag id: {flag.id}")
            self._flags[flag.id] = flag

    @property
    def dataset_revision(self) -> int:
        with self._lock:
            return self._dataset_revision

    def list_flags(self, status: str | None = None, owner: str | None = None) -> dict[str, Any]:
        with self._lock:
            flags = list(self._flags.values())
            if status: flags = [f for f in flags if f.status == status]
            if owner: flags = [f for f in flags if f.owner == owner]
            flags.sort(key=lambda f: (f.owner, f.key))
            return {"datasetRevision": self._dataset_revision,
                    "flags": [self._summary(f) for f in flags]}

    def get_flag(self, flag_id: str) -> dict[str, Any]:
        with self._lock:
            return self._detail(self._require(flag_id))

    def update_note(self, flag_id: str, expected_revision: int, note: str) -> dict[str, Any]:
        normalized = note.strip()
        if len(normalized) > 240:
            raise ValidationError("note must be at most 240 characters")
        with self._lock:
            flag = self._require(flag_id)
            if expected_revision != flag.revision:
                raise StaleRevision(self._detail(flag))
            changed = normalized != flag.operator_note
            if changed:
                flag.operator_note = normalized
                flag.revision += 1
                self._dataset_revision += 1
            return {"changed": changed, "datasetRevision": self._dataset_revision,
                    "flag": self._detail(flag)}

    def _require(self, flag_id: str) -> Flag:
        flag = self._flags.get(flag_id)
        if flag is None: raise NotFound(flag_id)
        return flag

    @staticmethod
    def _summary(flag: Flag) -> dict[str, Any]:
        return {"id": flag.id, "key": flag.key, "name": flag.name, "owner": flag.owner,
                "status": flag.status, "revision": flag.revision}

    @staticmethod
    def _detail(flag: Flag) -> dict[str, Any]:
        return copy.deepcopy(flag.to_dict())
