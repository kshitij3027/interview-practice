#!/usr/bin/env python3
"""Generate a deterministic, adversarial RecoveryWave scale fixture."""

from __future__ import annotations

import argparse
import csv
import json
import random
import tempfile
from collections.abc import Iterator
from pathlib import Path


DEFAULT_SEED = 20260822
HUB_PERCENTS = (100, 5, 15, 30)
REGIONS = (("region-01", 1), ("region-05", 5), ("region-20", 20))


def service_id(node: int) -> str:
    return f"svc-{node:06d}"


def region_for(worker: int) -> str:
    bucket = worker % 100
    for name, upper_bound in REGIONS:
        if bucket < upper_bound:
            return name
    return "region-80"


def dependency_rows(
    service_count: int, cluster_size: int, dependency_row_count: int
) -> Iterator[tuple[str, str, str]]:
    """Yield exactly ``dependency_row_count`` rows without retaining them."""
    hub_count = len(HUB_PERCENTS)
    worker_count = service_count - hub_count
    emitted = 0

    def rows() -> Iterator[tuple[str, str, str]]:
        # Every worker is in the main hub's blast radius. The other hubs form
        # declared fan-in sweep points independent of measured planner output.
        for worker in range(worker_count):
            node = hub_count + worker
            yield service_id(node), service_id(0), "hard"
            for hub, percent in enumerate(HUB_PERCENTS[1:], start=1):
                if worker < worker_count * percent // 100:
                    yield service_id(node), service_id(hub), "hard"

            position = worker % cluster_size
            cluster_start = node - position
            if position:
                yield service_id(node), service_id(node - 1), "hard"
                yield service_id(node), service_id(cluster_start), "hard"
            if position > 7:
                yield service_id(node), service_id(node - 7), "hard"
            if worker % 4 == 0:
                yield service_id(node), service_id(0), "soft"
            if worker % 20 == 0:
                yield service_id(node), service_id(0), "hard"  # duplicate
            if worker % 1_000 == 0:
                yield service_id(node), service_id(node), "hard"
            if position and worker % 1_000 == 1:
                yield service_id(node - 1), service_id(node), "hard"  # 2-node SCC

        # One large SCC in addition to the many small cycles.
        if worker_count >= 100:
            yield service_id(hub_count), service_id(hub_count + 99), "hard"

        # Unknown endpoints are malformed even when soft, per the README.
        for number in range(min(1_000, max(1, dependency_row_count // 1_000))):
            kind = "hard" if number % 2 == 0 else "soft"
            yield service_id(hub_count + number % worker_count), f"unknown-{number}", kind

    for row in rows():
        if emitted >= dependency_row_count:
            return
        emitted += 1
        yield row

    # Fill to the requested row count with duplicates. This preserves the
    # graph shape while exercising streaming deduplication at production scale.
    worker = 0
    while emitted < dependency_row_count:
        yield service_id(hub_count + worker % worker_count), service_id(0), "hard"
        worker += 1
        emitted += 1


def generate(
    output: Path,
    service_count: int,
    dependency_row_count: int,
    cluster_size: int,
    seed: int,
) -> dict[str, object]:
    if service_count <= len(HUB_PERCENTS):
        raise ValueError(f"service count must exceed {len(HUB_PERCENTS)}")
    if cluster_size < 10:
        raise ValueError("cluster size must be at least 10")
    if dependency_row_count < service_count:
        raise ValueError("dependency rows must be at least the service count")
    output.mkdir(parents=True, exist_ok=True)
    services_path = output / "services.csv"
    dependencies_path = output / "dependencies.csv"
    if services_path.exists() or dependencies_path.exists():
        raise FileExistsError(f"refusing to overwrite scale fixture in {output}")

    rng = random.Random(seed)
    with services_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("service_id", "tier", "region"))
        for node in range(service_count):
            if node < len(HUB_PERCENTS):
                region = "region-01" if node == 0 else "region-80"
            else:
                region = region_for(node - len(HUB_PERCENTS))
            writer.writerow((service_id(node), rng.randrange(4), region))

    with dependencies_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("service_id", "depends_on", "kind"))
        writer.writerows(
            dependency_rows(service_count, cluster_size, dependency_row_count)
        )

    worker_count = service_count - len(HUB_PERCENTS)
    config: dict[str, object] = {
        "seed": seed,
        "service_count": service_count,
        "dependency_row_count": dependency_row_count,
        "cluster_size": cluster_size,
        "hub_count": len(HUB_PERCENTS),
        "hub_fan_in_percent": list(HUB_PERCENTS),
        "regions": {
            "region-01": sum(region_for(worker) == "region-01" for worker in range(worker_count)) + 1,
            "region-05": sum(region_for(worker) == "region-05" for worker in range(worker_count)),
            "region-20": sum(region_for(worker) == "region-20" for worker in range(worker_count)),
            "region-80": sum(region_for(worker) == "region-80" for worker in range(worker_count)) + 3,
        },
        "services_path": str(services_path),
        "dependencies_path": str(dependencies_path),
    }
    (output / "fixture.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return config


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--out",
        type=Path,
        help="new output directory (default: a temporary directory outside the repo)",
    )
    result.add_argument("--services", type=int, default=200_000)
    result.add_argument("--dependency-rows", type=int, default=1_000_000)
    result.add_argument("--cluster-size", type=int, default=5_000)
    result.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return result


def main() -> int:
    args = parser().parse_args()
    output = args.out or Path(tempfile.mkdtemp(prefix="recoverywave-scale-"))
    try:
        config = generate(
            output, args.services, args.dependency_rows, args.cluster_size, args.seed
        )
    except (OSError, ValueError) as exc:
        raise SystemExit(f"gen_scale_fixture: {exc}") from exc
    print(json.dumps(config, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
