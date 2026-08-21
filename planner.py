#!/usr/bin/env python3
"""Recovery planning CLI starter.

The parsing/index-loading utilities are implemented so interview time can focus on
solving the customer problem. The recovery-planning behavior is intentionally not
implemented.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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

    Implement this function. You may introduce a preprocessed planner/index object
    and change the CLI to reuse it across incidents; the current signature exists
    only as a minimal starting interface.
    """
    raise NotImplementedError("implement recovery planning")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build deterministic service recovery plans")
    parser.add_argument("--services", required=True)
    parser.add_argument("--dependencies", required=True)
    parser.add_argument("--incidents", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    services = load_services(args.services)
    dependencies = load_dependencies(args.dependencies)

    for incident in load_incidents(args.incidents):
        result = plan_recovery(services, dependencies, incident)
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
