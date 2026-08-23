#!/usr/bin/env python3
"""Reproduce RecoveryWave latency, memory, and diagnostic scale validation."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
import tracemalloc
from array import array
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from recovery import RecoveryPlanner  # noqa: E402


QUANTILE_MINIMUM = 200
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
LATENCY_LIMIT_MS = 100.0


def nearest_rank(values: list[float], percentile: float) -> float:
    """Return the nearest-rank quantile (rank=ceil(p*n), one-indexed)."""
    if not values:
        raise ValueError("cannot calculate a quantile of an empty sample")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def distribution(values: list[float]) -> dict[str, Any]:
    ordered = sorted(values)
    result: dict[str, Any] = {"n": len(ordered)}
    if len(ordered) >= QUANTILE_MINIMUM:
        result.update(
            {
                "p50": nearest_rank(ordered, 0.50),
                "p95": nearest_rank(ordered, 0.95),
                "p99": nearest_rank(ordered, 0.99),
                "max": ordered[-1],
                "quantile_convention": "nearest-rank",
            }
        )
    else:
        result["sorted_tail"] = ordered[-min(10, len(ordered)) :]
        result["quantiles_omitted"] = f"requires at least {QUANTILE_MINIMUM} samples"
    return result


def rss_sample() -> dict[str, int | str]:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return {"raw": raw, "raw_unit": "bytes", "bytes": raw}
    return {"raw": raw, "raw_unit": "KiB", "bytes": raw * 1024}


def machine_header() -> dict[str, object]:
    return {
        "machine": platform.machine(),
        "processor": platform.processor(),
        "os": platform.platform(),
        "python": sys.version,
        "array_i_itemsize": array("i").itemsize,
        "pid": os.getpid(),
    }


def make_workload(config: dict[str, Any], samples: int) -> list[dict[str, Any]]:
    service_count = config["service_count"]
    cluster_size = config["cluster_size"]
    hub_count = config["hub_count"]
    worker_count = service_count - hub_count
    cluster_count = max(1, math.ceil(worker_count / cluster_size))
    incidents: list[dict[str, Any]] = []

    def node(cluster: int, position: int) -> str:
        start = hub_count + (cluster % cluster_count) * cluster_size
        length = min(cluster_size, service_count - start)
        position = min(max(0, position), max(0, length - 1))
        return f"svc-{start + position:06d}"

    for number in range(samples):
        cluster = number % cluster_count
        jitter = number // cluster_count
        end = cluster_size - 1
        definitions = [
            ("leaf", [node(cluster, end - jitter % 5)], None),
            ("near_leaf", [node(cluster, end - max(10, cluster_size // 100) - jitter % 11)], None),
            ("mid_graph", [node(cluster, end - max(20, cluster_size // 5) - jitter % 31)], None),
            ("near_root", [node(cluster, 1 + jitter % max(1, cluster_size // 100))], None),
            (
                "multi_seed",
                [
                    node(cluster, end - max(10, cluster_size // 10)),
                    node(cluster + 1, end - max(10, cluster_size // 10)),
                ],
                None,
            ),
            ("inside_scc", [node(cluster, max(1, cluster_size * 4 // 5))], None),
            ("region_scoped", [node(cluster, max(1, cluster_size // 5))], "region-80"),
            ("region_scoped_hub", ["svc-000000"], "region-01"),
        ]
        for stratum, failed, region in definitions:
            incident: dict[str, Any] = {
                "incident_id": f"{stratum}-{number:04d}",
                "failed_services": failed,
                "_stratum": stratum,
            }
            if region is not None:
                incident["region"] = region
            incidents.append(incident)
    return incidents


def public_incident(incident: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in incident.items() if not key.startswith("_")}


def build_planner(config: dict[str, Any]) -> tuple[RecoveryPlanner, float]:
    started = time.perf_counter()
    planner = RecoveryPlanner.from_paths(
        config["services_path"], config["dependencies_path"]
    )
    return planner, (time.perf_counter() - started) * 1_000


def graph_summary(planner: RecoveryPlanner) -> dict[str, int]:
    return {
        "services": len(planner.table.ids),
        "unique_hard_edges": len(planner.deps.targets),
        "ignored_dependency_rows": planner.ignored_dependency_rows,
    }


def timing_worker(config: dict[str, Any]) -> dict[str, Any]:
    planner, build_ms = build_planner(config)
    incidents = config["incidents"]
    warmup_count = config["warmup"]
    for incident in incidents[:warmup_count]:
        planner.plan(public_incident(incident))

    records = []
    for incident in incidents:
        started = time.perf_counter()
        result = planner.plan(public_incident(incident))
        latency_ms = (time.perf_counter() - started) * 1_000
        records.append(
            {
                "incident_id": incident["incident_id"],
                "stratum": incident["_stratum"],
                "result_size": result["service_count"],
                "latency_ms": latency_ms,
            }
        )

    started = time.perf_counter()
    service_count_checksum = 0
    for number in range(config["throughput_queries"]):
        incident = incidents[number % len(incidents)]
        service_count_checksum += planner.plan(public_incident(incident))["service_count"]
    throughput_seconds = time.perf_counter() - started

    sweep = []
    for hub, fan_in in enumerate(config["hub_fan_in_percent"]):
        for region in [None, "region-01", "region-05", "region-20", "region-80"]:
            values = []
            result_size = 0
            incident = {
                "incident_id": "sweep",
                "failed_services": [f"svc-{hub:06d}"],
                **({} if region is None else {"region": region}),
            }
            for _ in range(config["sweep_repetitions"]):
                started = time.perf_counter()
                result = planner.plan(incident)
                values.append((time.perf_counter() - started) * 1_000)
                result_size = result["service_count"]
            sweep.append(
                {
                    "fan_in_percent": fan_in,
                    "region": region,
                    "result_size": result_size,
                    "latency_ms": distribution(values),
                    "crosses_100_ms": max(values) >= LATENCY_LIMIT_MS,
                }
            )
    return {
        "run": "A-timing",
        "header": machine_header(),
        "graph": graph_summary(planner),
        "build_ms": build_ms,
        "warmup_incidents": warmup_count,
        "records": records,
        "throughput": {
            "queries": config["throughput_queries"],
            "seconds": throughput_seconds,
            "queries_per_second": config["throughput_queries"] / throughput_seconds,
            "service_count_checksum": service_count_checksum,
            "gated": False,
        },
        "hub_region_sweep": sweep,
    }


def memory_worker(config: dict[str, Any]) -> dict[str, Any]:
    planner, build_ms = build_planner(config)
    samples = [{"point": "after_build", **rss_sample()}]
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for incident in config["incidents"]:
        by_stratum[incident["_stratum"]].append(incident)
    checksum = 0
    for stratum, incidents in by_stratum.items():
        for incident in incidents:
            checksum += planner.plan(public_incident(incident))["service_count"]
        samples.append({"point": f"after_stratum:{stratum}", **rss_sample()})

    # The sweep includes large, out-of-band results which are not represented
    # by the latency workload but may establish the process RSS high-water.
    for hub, fan_in in enumerate(config["hub_fan_in_percent"]):
        for region in [None, "region-01", "region-05", "region-20", "region-80"]:
            incident = {
                "incident_id": "memory-sweep",
                "failed_services": [f"svc-{hub:06d}"],
                **({} if region is None else {"region": region}),
            }
            checksum += planner.plan(incident)["service_count"]
            label = "all" if region is None else region
            samples.append(
                {"point": f"after_sweep:fan_in={fan_in}%:region={label}", **rss_sample()}
            )
    incidents = config["incidents"]
    for number in range(config["throughput_queries"]):
        checksum += planner.plan(public_incident(incidents[number % len(incidents)]))[
            "service_count"
        ]
    samples.append({"point": "after_full_query_run", **rss_sample()})
    return {
        "run": "B-memory",
        "header": machine_header(),
        "graph": graph_summary(planner),
        "build_ms": build_ms,
        "samples": samples,
        "service_count_checksum": checksum,
    }


def diagnostics_worker(config: dict[str, Any]) -> dict[str, Any]:
    tracemalloc.start()
    planner, build_ms = build_planner(config)
    records = []
    for incident in config["incidents"]:
        started = time.perf_counter()
        diagnosed = planner.diagnose(public_incident(incident))
        latency_ms = (time.perf_counter() - started) * 1_000
        result = diagnosed["result"]
        metrics = diagnosed["diagnostics"]
        records.append(
            {
                "incident_id": incident["incident_id"],
                "stratum": incident["_stratum"],
                "seed_count": len(incident["failed_services"]),
                "region": incident.get("region"),
                "result_size": result["service_count"],
                "latency_ms": latency_ms,
                **metrics,
            }
        )
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "run": "C-diagnostics",
        "header": machine_header(),
        "graph": graph_summary(planner),
        "build_ms": build_ms,
        "tracemalloc_current_bytes": current,
        "tracemalloc_peak_bytes": peak,
        "records": records,
        "warning": "instrumented latency and memory are explanatory, not gate inputs",
    }


def run_worker(mode: str, config_path: Path) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    worker = {
        "timing": timing_worker,
        "memory": memory_worker,
        "diagnostics": diagnostics_worker,
    }[mode]
    print(json.dumps(worker(config), separators=(",", ":")))
    return 0


def run_child(mode: str, config_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", mode, "--config", str(config_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"{mode} worker failed: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def histogram(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"<10": 0, "10-99": 0, "100-999": 0, "1000-5000": 0, ">5000": 0}
    for record in records:
        size = record["result_size"]
        if size < 10:
            counts["<10"] += 1
        elif size < 100:
            counts["10-99"] += 1
        elif size < 1_000:
            counts["100-999"] += 1
        elif size <= 5_000:
            counts["1000-5000"] += 1
        else:
            counts[">5000"] += 1
    return counts


def assemble_report(
    fixture: dict[str, Any], timing: dict[str, Any], memory: dict[str, Any], diagnostics: dict[str, Any]
) -> dict[str, Any]:
    by_stratum: dict[str, list[float]] = defaultdict(list)
    in_band = []
    for record in timing["records"]:
        by_stratum[record["stratum"]].append(record["latency_ms"])
        if 10 <= record["result_size"] <= 5_000:
            in_band.append(record["latency_ms"])
    pooled = distribution(in_band)
    if len(in_band) < QUANTILE_MINIMUM:
        latency_verdict = "insufficient_samples"
    else:
        latency_verdict = "pass" if pooled["p95"] < LATENCY_LIMIT_MS else "fail"
    memory_samples = []
    for sample in memory["samples"]:
        memory_samples.append(
            {**sample, "verdict": "pass" if sample["bytes"] < MEMORY_LIMIT_BYTES else "fail"}
        )
    memory_verdict = (
        "pass" if all(sample["verdict"] == "pass" for sample in memory_samples) else "fail"
    )
    return {
        "methodology": {
            "process_isolation": ["A-timing", "B-memory", "C-diagnostics"],
            "latency_gate": "nearest-rank p95 < 100 ms for every sampled result in 10..5000, pooled",
            "memory_gate": "ru_maxrss < 512 MiB at every sample point",
            "minimum_quantile_sample": QUANTILE_MINIMUM,
            "workload_selection": "declared structural strata; no result-based filtering",
        },
        "fixture": fixture,
        "graph": timing["graph"],
        "result_size_histogram": histogram(timing["records"]),
        "latency": {
            "verdict": latency_verdict,
            "pooled_in_band_ms": pooled,
            "by_stratum_ms": {
                stratum: distribution(values) for stratum, values in sorted(by_stratum.items())
            },
            "build_ms": timing["build_ms"],
            "warmup_incidents": timing["warmup_incidents"],
            "throughput": timing["throughput"],
            "hub_region_sweep": timing["hub_region_sweep"],
        },
        "memory": {
            "verdict": memory_verdict,
            "limit_bytes": MEMORY_LIMIT_BYTES,
            "samples": memory_samples,
            "build_ms": memory["build_ms"],
        },
        "diagnostics": diagnostics,
        "timing_records": timing["records"],
    }


def orchestrate(args: argparse.Namespace) -> int:
    fixture_dir = args.fixture or Path(tempfile.mkdtemp(prefix="recoverywave-scale-"))
    if args.fixture:
        fixture = json.loads((fixture_dir / "fixture.json").read_text(encoding="utf-8"))
    else:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "gen_scale_fixture.py"),
            "--out", str(fixture_dir),
            "--services", str(args.services),
            "--dependency-rows", str(args.dependency_rows),
            "--cluster-size", str(args.cluster_size),
            "--seed", str(args.seed),
        ]
        generated = subprocess.run(command, text=True, capture_output=True, check=False)
        if generated.returncode:
            raise RuntimeError(generated.stderr.strip())
        fixture = json.loads(generated.stdout)

    incidents = make_workload(fixture, args.samples_per_stratum)
    worker_config = {
        **fixture,
        "incidents": incidents,
        "warmup": min(args.warmup, len(incidents)),
        "throughput_queries": args.throughput_queries,
        "sweep_repetitions": args.sweep_repetitions,
    }
    config_path = fixture_dir / "benchmark-config.json"
    config_path.write_text(json.dumps(worker_config), encoding="utf-8")
    timing = run_child("timing", config_path)
    memory = run_child("memory", config_path)
    diagnostics = run_child("diagnostics", config_path)
    report = assemble_report(fixture, timing, memory, diagnostics)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
        print(str(args.report))
    else:
        print(rendered, end="")

    failed = report["latency"]["verdict"] == "fail" or report["memory"]["verdict"] == "fail"
    insufficient = report["latency"]["verdict"] == "insufficient_samples"
    return 1 if failed or (insufficient and not args.allow_insufficient_samples) else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--fixture", type=Path, help="reuse an existing generated fixture")
    result.add_argument("--report", type=Path, help="write the JSON report to this path")
    result.add_argument("--services", type=int, default=200_000)
    result.add_argument("--dependency-rows", type=int, default=1_000_000)
    result.add_argument("--cluster-size", type=int, default=5_000)
    result.add_argument("--seed", type=int, default=20260822)
    result.add_argument("--samples-per-stratum", type=int, default=250)
    result.add_argument("--warmup", type=int, default=50)
    result.add_argument("--throughput-queries", type=int, default=10_000)
    result.add_argument("--sweep-repetitions", type=int, default=20)
    result.add_argument("--allow-insufficient-samples", action="store_true")
    result.add_argument("--worker", choices=("timing", "memory", "diagnostics"), help=argparse.SUPPRESS)
    result.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        if args.worker:
            if not args.config:
                raise ValueError("--config is required in worker mode")
            return run_worker(args.worker, args.config)
        return orchestrate(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"bench_scale: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
