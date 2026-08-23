#!/usr/bin/env python3
"""Load recovery data and emit deterministic restart plans from the CLI."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from recovery import RecoveryPlanner


@dataclass(frozen=True)
class Service:
    service_id: str
    tier: int
    region: str


@dataclass(frozen=True)
class Dependency:
    service_id: str
    depends_on: str
    kind: str


def load_services(path: str | Path) -> dict[str, Service]:
    services: dict[str, Service] = {}
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            service_id = row["service_id"].strip()
            if not service_id:
                continue
            services[service_id] = Service(
                service_id=service_id,
                tier=int(row["tier"]),
                region=row["region"].strip(),
            )
    return services


def load_dependencies(path: str | Path) -> list[Dependency]:
    dependencies: list[Dependency] = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            dependencies.append(
                Dependency(
                    service_id=row["service_id"].strip(),
                    depends_on=row["depends_on"].strip(),
                    kind=row["kind"].strip().lower(),
                )
            )
    return dependencies


def load_incidents(path: str | Path) -> Iterable[dict]:
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on incident line {line_number}: {exc}") from exc


def plan_recovery(
    services: dict[str, Service],
    dependencies: list[Dependency],
    incident: dict,
) -> dict:
    """Return one recovery-plan result for an incident.

    This compatibility entry point builds an index for its supplied inputs. Code
    serving multiple incidents should construct ``RecoveryPlanner`` once instead.
    """
    return RecoveryPlanner.from_loaded(services, dependencies).plan(incident)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build deterministic service recovery plans")
    parser.add_argument("--services", required=True)
    parser.add_argument("--dependencies", required=True)
    parser.add_argument("--incidents", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        planner = RecoveryPlanner.from_paths(args.services, args.dependencies)
        for incident in load_incidents(args.incidents):
            if not isinstance(incident, Mapping):
                raise TypeError(
                    f"incident must be a JSON object, got {type(incident).__name__}"
                )
            print(json.dumps(planner.plan(incident), sort_keys=True))
    except (OSError, TypeError, ValueError) as exc:
        print(f"planner: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
