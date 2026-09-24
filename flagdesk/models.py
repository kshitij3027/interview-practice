from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class Flag:
    id: str
    key: str
    name: str
    owner: str
    status: str
    revision: int
    operator_note: str
    published_config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "owner": self.owner,
            "status": self.status,
            "revision": self.revision,
            "operatorNote": self.operator_note,
            "publishedConfig": self.published_config,
        }
