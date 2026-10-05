from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .catalog import Catalog
from .models import TargetRequirement, Version


@dataclass(frozen=True)
class Request:
    request_id: str | None
    targets: tuple[TargetRequirement, ...]
    blocked_versions: frozenset[tuple[str, Version]]
    allow_canary: bool
    max_changes: int


def _request_id(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def parse_request(payload: Any, catalog: Catalog) -> Request:
    if not isinstance(payload, dict):
        raise ValueError("invalid request")
    targets_raw = payload.get("targets")
    blocked_raw = payload.get("blocked_versions")
    allow_canary = payload.get("allow_canary")
    max_changes = payload.get("max_changes")
    if not isinstance(targets_raw, list) or not targets_raw:
        raise ValueError("invalid request")
    if not isinstance(blocked_raw, list) or not isinstance(allow_canary, bool):
        raise ValueError("invalid request")
    if isinstance(max_changes, bool) or not isinstance(max_changes, int) or max_changes < 0:
        raise ValueError("invalid request")

    targets, seen = [], set()
    for raw in targets_raw:
        if not isinstance(raw, dict):
            raise ValueError("invalid request")
        package_id = raw.get("package_id")
        if not isinstance(package_id, str) or not package_id or package_id not in catalog.packages:
            raise ValueError("invalid request")
        try:
            minimum = Version.parse(raw.get("min_version"))
            maximum = Version.parse(raw.get("max_version_exclusive"))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid request") from exc
        if minimum >= maximum:
            raise ValueError("invalid request")
        target = TargetRequirement(package_id, minimum, maximum)
        if target not in seen:
            seen.add(target)
            targets.append(target)

    blocked = set()
    for raw in blocked_raw:
        if not isinstance(raw, str) or raw.count("@") != 1:
            raise ValueError("invalid request")
        package_id, raw_version = raw.split("@", 1)
        try:
            version = Version.parse(raw_version)
        except ValueError as exc:
            raise ValueError("invalid request") from exc
        if (package_id, version) not in catalog.releases:
            raise ValueError("invalid request")
        blocked.add((package_id, version))

    return Request(_request_id(payload.get("request_id")), tuple(targets), frozenset(blocked), allow_canary, max_changes)


def iter_request_payloads(path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                yield None, None, False
                continue
            request_id = _request_id(payload.get("request_id")) if isinstance(payload, dict) else None
            yield request_id, payload, True
