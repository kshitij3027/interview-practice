"""Preprocessed recovery planning over hard service dependencies."""

from __future__ import annotations

import csv
import heapq
import time
from array import array
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


_INT_TYPE = "i" if array("i").itemsize >= 4 else "l"


class LoadedService(Protocol):
    tier: int
    region: str


class LoadedDependency(Protocol):
    service_id: str
    depends_on: str
    kind: str


ServiceRowSource = Callable[[], Iterator[tuple[str, int, str]]]
DependencyRowSource = Callable[[], Iterator[tuple[str, str, str]]]


@dataclass
class ServiceTable:
    """Integer interning and static attributes for services."""

    ids: list[str]
    index: dict[str, int]
    tier: array
    region_of: array
    region_ids: dict[str, int]


@dataclass
class Csr:
    """Compressed sparse row adjacency over integer service indices."""

    offsets: array
    targets: array

    def neighbours(self, node: int) -> memoryview:
        return memoryview(self.targets)[self.offsets[node] : self.offsets[node + 1]]


class RecoveryPlanner:
    """Static graph index that can answer many recovery incidents."""

    def __init__(
        self,
        table: ServiceTable,
        deps: Csr,
        dependents: Csr,
        ignored_dependency_rows: int,
        wave_policy: str = "single_component",
    ) -> None:
        if wave_policy not in {"single_component", "maximal"}:
            raise ValueError(f"unknown wave policy: {wave_policy}")
        self.table = table
        self.deps = deps
        self.dependents = dependents
        self.ignored_dependency_rows = ignored_dependency_rows
        self.wave_policy = wave_policy

    @classmethod
    def from_paths(
        cls,
        services_path: str | Path,
        dependencies_path: str | Path,
        wave_policy: str = "single_component",
    ) -> RecoveryPlanner:
        """Stream CSV inputs into a reusable planner."""

        def service_rows() -> Iterator[tuple[str, int, str]]:
            with open(services_path, newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    service_id = row["service_id"].strip()
                    if service_id:
                        yield service_id, int(row["tier"]), row["region"].strip()

        def dependency_rows() -> Iterator[tuple[str, str, str]]:
            with open(dependencies_path, newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    yield (
                        row["service_id"].strip(),
                        row["depends_on"].strip(),
                        row["kind"].strip().lower(),
                    )

        return cls._build(service_rows, dependency_rows, wave_policy)

    @classmethod
    def from_loaded(
        cls,
        services: Mapping[str, LoadedService],
        dependencies: Sequence[LoadedDependency],
        wave_policy: str = "single_component",
    ) -> RecoveryPlanner:
        """Build from the objects returned by ``planner``'s loader functions."""
        if not isinstance(dependencies, Sequence):
            raise TypeError("dependencies must be a re-iterable Sequence")

        def service_rows() -> Iterator[tuple[str, int, str]]:
            for service_id, service in services.items():
                if service_id:
                    yield service_id, int(service.tier), service.region

        def dependency_rows() -> Iterator[tuple[str, str, str]]:
            for dependency in dependencies:
                yield (
                    dependency.service_id,
                    dependency.depends_on,
                    dependency.kind.lower(),
                )

        return cls._build(service_rows, dependency_rows, wave_policy)

    @classmethod
    def _build(
        cls,
        service_rows: ServiceRowSource,
        dependency_rows: DependencyRowSource,
        wave_policy: str,
    ) -> RecoveryPlanner:
        ids: list[str] = []
        index: dict[str, int] = {}
        tiers = array(_INT_TYPE)
        region_of = array(_INT_TYPE)
        region_ids: dict[str, int] = {}

        for service_id, tier, region in service_rows():
            region_id = region_ids.setdefault(region, len(region_ids))
            node = index.get(service_id)
            if node is None:
                node = len(ids)
                index[service_id] = node
                ids.append(service_id)
                tiers.append(tier)
                region_of.append(region_id)
            else:
                tiers[node] = tier
                region_of[node] = region_id

        node_count = len(ids)
        deps_degree = array(_INT_TYPE, [0]) * node_count
        dependents_degree = array(_INT_TYPE, [0]) * node_count
        ignored = 0
        for service_id, depends_on, kind in dependency_rows():
            source = index.get(service_id)
            target = index.get(depends_on)
            if source is None or target is None:
                ignored += 1
                continue
            if kind != "hard":
                continue
            deps_degree[source] += 1
            dependents_degree[target] += 1

        deps_offsets = cls._offsets(deps_degree)
        dependents_offsets = cls._offsets(dependents_degree)
        deps_targets = array(_INT_TYPE, [0]) * deps_offsets[-1]
        dependents_targets = array(_INT_TYPE, [0]) * dependents_offsets[-1]
        deps_cursor = array(_INT_TYPE, deps_offsets[:-1])
        dependents_cursor = array(_INT_TYPE, dependents_offsets[:-1])

        for service_id, depends_on, kind in dependency_rows():
            source = index.get(service_id)
            target = index.get(depends_on)
            if source is None or target is None or kind != "hard":
                continue
            deps_targets[deps_cursor[source]] = target
            deps_cursor[source] += 1
            dependents_targets[dependents_cursor[target]] = source
            dependents_cursor[target] += 1

        deps = cls._compact(deps_offsets, deps_targets)
        dependents = cls._compact(dependents_offsets, dependents_targets)
        table = ServiceTable(ids, index, tiers, region_of, region_ids)
        return cls(table, deps, dependents, ignored, wave_policy)

    @staticmethod
    def _offsets(degrees: array) -> array:
        offsets = array(_INT_TYPE, [0])
        total = 0
        for degree in degrees:
            total += degree
            offsets.append(total)
        return offsets

    @staticmethod
    def _compact(offsets: array, targets: array) -> Csr:
        """Sort and deduplicate every CSR slice in place."""
        new_offsets = array(_INT_TYPE, [0]) * len(offsets)
        write = 0
        for node in range(len(offsets) - 1):
            new_offsets[node] = write
            previous = -1
            for target in sorted(targets[offsets[node] : offsets[node + 1]]):
                if target != previous:
                    targets[write] = target
                    write += 1
                    previous = target
        new_offsets[-1] = write
        del targets[write:]
        return Csr(new_offsets, targets)

    def _affected(
        self, failed: Sequence[str], region: str | None
    ) -> tuple[set[int], list[str]]:
        """Return affected retained nodes and sorted, unique unknown IDs."""
        unknown: set[str] = set()
        seeds: list[int] = []
        region_id = None if region is None else self.table.region_ids.get(region)
        for service_id in failed:
            node = self.table.index.get(service_id)
            if node is None:
                unknown.add(service_id)
            else:
                seeds.append(node)

        if region is not None and region_id is None:
            return set(), sorted(unknown)

        visited = set(seeds)
        stack = list(seeds)
        while stack:
            dependency = stack.pop()
            for dependent in self.dependents.neighbours(dependency):
                if dependent not in visited:
                    visited.add(dependent)
                    stack.append(dependent)

        if region is None:
            return visited, sorted(unknown)
        retained = {node for node in visited if self.table.region_of[node] == region_id}
        return retained, sorted(unknown)

    def diagnose(self, incident: Mapping[str, object]) -> dict[str, object]:
        """Plan an incident while collecting deliberately out-of-band diagnostics.

        Benchmark timing must use :meth:`plan`; this method counts graph work and
        samples phase timers, both of which perturb the operation being observed.
        """
        failed, region = self._validated_incident(incident)
        started = time.perf_counter()
        affected, unknown, reached_nodes, reverse_edges_scanned = (
            self._affected_with_counters(failed, region)
        )
        affected_ms = (time.perf_counter() - started) * 1_000
        waves, wave_metrics = self._waves_profiled(affected)
        return {
            "result": self._result(incident, affected, unknown, waves),
            "diagnostics": {
                "reached_nodes": reached_nodes,
                "reverse_edges_scanned": reverse_edges_scanned,
                "affected_ms": affected_ms,
                **wave_metrics,
            },
        }

    def _affected_with_counters(
        self, failed: Sequence[str], region: str | None
    ) -> tuple[set[int], list[str], int, int]:
        """Instrumented counterpart of ``_affected`` for diagnostic runs only."""
        unknown: set[str] = set()
        seeds: list[int] = []
        region_id = None if region is None else self.table.region_ids.get(region)
        for service_id in failed:
            node = self.table.index.get(service_id)
            if node is None:
                unknown.add(service_id)
            else:
                seeds.append(node)
        if region is not None and region_id is None:
            return set(), sorted(unknown), 0, 0

        visited = set(seeds)
        stack = list(seeds)
        reverse_edges_scanned = 0
        while stack:
            dependency = stack.pop()
            neighbours = self.dependents.neighbours(dependency)
            reverse_edges_scanned += len(neighbours)
            for dependent in neighbours:
                if dependent not in visited:
                    visited.add(dependent)
                    stack.append(dependent)
        if region is None:
            retained = visited
        else:
            retained = {
                node for node in visited if self.table.region_of[node] == region_id
            }
        return retained, sorted(unknown), len(visited), reverse_edges_scanned

    def plan(self, incident: Mapping[str, object]) -> dict[str, object]:
        """Produce a deterministic recovery plan for one incident."""
        failed, region = self._validated_incident(incident)
        affected, unknown = self._affected(failed, region)
        return self._result(incident, affected, unknown, self._waves(affected))

    @staticmethod
    def _validated_incident(
        incident: Mapping[str, object],
    ) -> tuple[Sequence[str], str | None]:
        failed = incident.get("failed_services", [])
        if not isinstance(failed, Sequence) or isinstance(failed, (str, bytes)):
            raise TypeError("failed_services must be a sequence of service IDs")
        if not all(isinstance(service_id, str) for service_id in failed):
            raise TypeError("failed_services must contain only strings")
        region = incident.get("region")
        if region is not None and not isinstance(region, str):
            raise TypeError("region must be a string or null")
        return failed, region

    def _result(
        self,
        incident: Mapping[str, object],
        affected: set[int],
        unknown: list[str],
        waves: list[list[str]],
    ) -> dict[str, object]:
        return {
            "incident_id": incident.get("incident_id"),
            "waves": waves,
            "service_count": len(affected),
            "unknown_services": unknown,
            "ignored_dependency_rows": self.ignored_dependency_rows,
        }

    def _waves_profiled(
        self, affected: set[int]
    ) -> tuple[list[list[str]], dict[str, int | float]]:
        """Instrumented wave construction; never used by the production path."""
        if not affected:
            return [], {
                "retained_edges": 0,
                "scc_count": 0,
                "wave_count": 0,
                "localisation_ms": 0.0,
                "scc_ms": 0.0,
                "condensation_ms": 0.0,
                "key_computation_ms": 0.0,
                "heap_scheduling_ms": 0.0,
                "wave_materialization_ms": 0.0,
            }

        started = time.perf_counter()
        nodes = sorted(affected)
        local = {global_node: local_node for local_node, global_node in enumerate(nodes)}
        adjacency: list[list[int]] = [[] for _ in nodes]
        retained_edges = 0
        for local_node, global_node in enumerate(nodes):
            for target in self.deps.neighbours(global_node):
                local_target = local.get(target)
                if local_target is not None:
                    adjacency[local_node].append(local_target)
                    retained_edges += 1
        localisation_ms = (time.perf_counter() - started) * 1_000

        started = time.perf_counter()
        components, component_of = self._strongly_connected_components(adjacency)
        scc_ms = (time.perf_counter() - started) * 1_000

        started = time.perf_counter()
        component_count = len(components)
        dag: list[list[int]] = [[] for _ in components]
        indegree = [0] * component_count
        for source, targets in enumerate(adjacency):
            source_component = component_of[source]
            for target in targets:
                target_component = component_of[target]
                if source_component != target_component:
                    dag[target_component].append(source_component)
                    indegree[source_component] += 1
        condensation_ms = (time.perf_counter() - started) * 1_000

        started = time.perf_counter()
        keys = [
            min(
                (self.table.tier[nodes[member]], self.table.ids[nodes[member]])
                for member in component
            )
            for component in components
        ]
        eligible = [(*keys[c], c) for c in range(component_count) if indegree[c] == 0]
        heapq.heapify(eligible)
        key_computation_ms = (time.perf_counter() - started) * 1_000

        waves: list[list[str]] = []
        heap_scheduling_ms = 0.0
        wave_materialization_ms = 0.0
        while eligible:
            started = time.perf_counter()
            batch_size = 1 if self.wave_policy == "single_component" else len(eligible)
            batch = [heapq.heappop(eligible)[-1] for _ in range(batch_size)]
            for component in batch:
                for dependent_component in dag[component]:
                    indegree[dependent_component] -= 1
                    if indegree[dependent_component] == 0:
                        heapq.heappush(
                            eligible, (*keys[dependent_component], dependent_component)
                        )
            heap_scheduling_ms += (time.perf_counter() - started) * 1_000

            started = time.perf_counter()
            wave = [
                self.table.ids[nodes[member]]
                for component in batch
                for member in components[component]
            ]
            waves.append(sorted(wave))
            wave_materialization_ms += (time.perf_counter() - started) * 1_000

        if sum(map(len, waves)) != len(nodes):
            raise RuntimeError("invalid SCC condensation graph")
        return waves, {
            "retained_edges": retained_edges,
            "scc_count": component_count,
            "wave_count": len(waves),
            "localisation_ms": localisation_ms,
            "scc_ms": scc_ms,
            "condensation_ms": condensation_ms,
            "key_computation_ms": key_computation_ms,
            "heap_scheduling_ms": heap_scheduling_ms,
            "wave_materialization_ms": wave_materialization_ms,
        }

    def _waves(self, affected: set[int]) -> list[list[str]]:
        if not affected:
            return []

        nodes = sorted(affected)
        local = {global_node: local_node for local_node, global_node in enumerate(nodes)}
        adjacency: list[list[int]] = [[] for _ in nodes]
        for local_node, global_node in enumerate(nodes):
            for target in self.deps.neighbours(global_node):
                local_target = local.get(target)
                if local_target is not None:
                    adjacency[local_node].append(local_target)

        components, component_of = self._strongly_connected_components(adjacency)
        component_count = len(components)
        dag: list[list[int]] = [[] for _ in components]
        indegree = [0] * component_count
        for source, targets in enumerate(adjacency):
            source_component = component_of[source]
            for target in targets:
                target_component = component_of[target]
                if source_component != target_component:
                    # A dependency enables its dependent during recovery.
                    dag[target_component].append(source_component)
                    indegree[source_component] += 1

        keys = [
            min(
                (self.table.tier[nodes[member]], self.table.ids[nodes[member]])
                for member in component
            )
            for component in components
        ]
        eligible = [(*keys[c], c) for c in range(component_count) if indegree[c] == 0]
        heapq.heapify(eligible)
        waves: list[list[str]] = []
        while eligible:
            batch_size = 1 if self.wave_policy == "single_component" else len(eligible)
            batch = [heapq.heappop(eligible)[-1] for _ in range(batch_size)]
            for component in batch:
                for dependent_component in dag[component]:
                    indegree[dependent_component] -= 1
                    if indegree[dependent_component] == 0:
                        heapq.heappush(
                            eligible, (*keys[dependent_component], dependent_component)
                        )
            wave = [
                self.table.ids[nodes[member]]
                for component in batch
                for member in components[component]
            ]
            waves.append(sorted(wave))

        if sum(map(len, waves)) != len(nodes):
            raise RuntimeError("invalid SCC condensation graph")
        return waves

    @staticmethod
    def _strongly_connected_components(
        adjacency: list[list[int]],
    ) -> tuple[list[list[int]], list[int]]:
        """Iterative Tarjan SCC, avoiding recursion on production-sized chains."""
        node_count = len(adjacency)
        index = [-1] * node_count
        low = [0] * node_count
        component_of = [-1] * node_count
        on_stack = bytearray(node_count)
        tarjan_stack: list[int] = []
        components: list[list[int]] = []
        counter = 0

        for start in range(node_count):
            if index[start] != -1:
                continue
            work: list[tuple[int, int]] = [(start, 0)]
            while work:
                node, next_edge = work[-1]
                if next_edge == 0 and index[node] == -1:
                    index[node] = low[node] = counter
                    counter += 1
                    tarjan_stack.append(node)
                    on_stack[node] = 1

                descended = False
                while next_edge < len(adjacency[node]):
                    target = adjacency[node][next_edge]
                    next_edge += 1
                    work[-1] = (node, next_edge)
                    if index[target] == -1:
                        work.append((target, 0))
                        descended = True
                        break
                    if on_stack[target]:
                        low[node] = min(low[node], index[target])
                if descended:
                    continue

                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    component: list[int] = []
                    while True:
                        member = tarjan_stack.pop()
                        on_stack[member] = 0
                        component_of[member] = len(components)
                        component.append(member)
                        if member == node:
                            break
                    components.append(component)

        return components, component_of
