from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Dependency, Event, Query, Snapshot, Task, Workflow
from .timeutil import parse_rfc3339


class DatasetError(ValueError):
    pass


def _nonempty(value: str, field: str) -> str:
    result = (value or "").strip()
    if not result:
        raise DatasetError(f"{field} must be non-empty")
    return result


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_snapshot(
    workflows_path: str | Path,
    tasks_path: str | Path,
    dependencies_path: str | Path,
    events_path: str | Path,
) -> Snapshot:
    workflows: dict[str, Workflow] = {}
    for row in _read_csv(workflows_path):
        workflow_id = _nonempty(row.get("workflow_id", ""), "workflow_id")
        if workflow_id in workflows:
            raise DatasetError(f"duplicate workflow_id: {workflow_id}")
        workflows[workflow_id] = Workflow(
            workflow_id=workflow_id,
            customer_id=_nonempty(row.get("customer_id", ""), "customer_id"),
            name=_nonempty(row.get("name", ""), "workflow name"),
        )

    tasks: dict[str, Task] = {}
    for row in _read_csv(tasks_path):
        task_id = _nonempty(row.get("task_id", ""), "task_id")
        if task_id in tasks:
            raise DatasetError(f"duplicate task_id: {task_id}")
        workflow_id = _nonempty(row.get("workflow_id", ""), "task workflow_id")
        try:
            priority = int(row.get("priority", ""))
        except (TypeError, ValueError) as exc:
            raise DatasetError(f"invalid priority for task {task_id}") from exc
        try:
            due_at = parse_rfc3339(row.get("due_at", ""))
        except ValueError as exc:
            raise DatasetError(f"invalid due_at for task {task_id}") from exc
        tasks[task_id] = Task(task_id, workflow_id, priority, due_at)

    dependency_keys: set[tuple[str, str]] = set()
    dependencies: list[Dependency] = []
    for row in _read_csv(dependencies_path):
        task_id = _nonempty(row.get("task_id", ""), "dependency task_id")
        prerequisite = _nonempty(
            row.get("prerequisite_task_id", ""), "prerequisite_task_id"
        )
        key = (task_id, prerequisite)
        if key in dependency_keys:
            continue
        dependency_keys.add(key)
        dependencies.append(Dependency(task_id, prerequisite))

    events_by_id: dict[str, Event] = {}
    slot_to_event_id: dict[tuple[str, object, int], str] = {}
    for row in _read_csv(events_path):
        event_id = _nonempty(row.get("event_id", ""), "event_id")
        task_id = _nonempty(row.get("task_id", ""), "event task_id")
        try:
            occurred_at = parse_rfc3339(row.get("occurred_at", ""))
        except ValueError as exc:
            raise DatasetError(f"invalid occurred_at for event {event_id}") from exc
        try:
            version = int(row.get("version", ""))
        except (TypeError, ValueError) as exc:
            raise DatasetError(f"invalid version for event {event_id}") from exc
        if version <= 0:
            raise DatasetError(f"version must be positive for event {event_id}")
        action = _nonempty(row.get("action", ""), "event action")
        if action not in {"complete", "reopen"}:
            raise DatasetError(f"invalid action for event {event_id}: {action}")
        event = Event(event_id, task_id, occurred_at, version, action)
        existing = events_by_id.get(event_id)
        if existing is not None:
            if existing != event:
                raise DatasetError(f"conflicting event_id: {event_id}")
            continue
        slot = (task_id, occurred_at, version)
        other_id = slot_to_event_id.get(slot)
        if other_id is not None and other_id != event_id:
            raise DatasetError(
                f"conflicting task/timestamp/version slot: {task_id} {version}"
            )
        slot_to_event_id[slot] = event_id
        events_by_id[event_id] = event

    snapshot = Snapshot(
        workflows=workflows,
        tasks=tasks,
        dependencies=tuple(dependencies),
        events=tuple(events_by_id.values()),
    )
    validate_snapshot(snapshot)
    return snapshot


def load_queries(path: str | Path) -> list[Query]:
    queries: list[Query] = []
    seen_request_ids: set[str] = set()
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                queries.append(
                    Query(
                        request_id=f"line-{line_number}",
                        workflow_id="",
                        as_of=parse_rfc3339("1970-01-01T00:00:00Z"),
                        limit=0,
                        valid=False,
                        invalid_reason="invalid_query",
                    )
                )
                continue

            request_id = str(raw.get("request_id", "")).strip()
            workflow_id = str(raw.get("workflow_id", "")).strip()
            valid = True
            if not request_id or request_id in seen_request_ids:
                valid = False
            else:
                seen_request_ids.add(request_id)
            try:
                as_of = parse_rfc3339(str(raw.get("as_of", "")))
            except ValueError:
                as_of = parse_rfc3339("1970-01-01T00:00:00Z")
                valid = False
            try:
                limit = int(raw.get("limit"))
            except (TypeError, ValueError):
                limit = 0
                valid = False
            if not workflow_id or not (1 <= limit <= 50):
                valid = False

            queries.append(
                Query(
                    request_id=request_id or f"line-{line_number}",
                    workflow_id=workflow_id,
                    as_of=as_of,
                    limit=limit,
                    valid=valid,
                    invalid_reason=None if valid else "invalid_query",
                )
            )
    return queries


def validate_snapshot(snapshot: Snapshot) -> None:
    for task in snapshot.tasks.values():
        if task.workflow_id not in snapshot.workflows:
            raise DatasetError(
                f"task {task.task_id} references unknown workflow {task.workflow_id}"
            )

    outgoing: dict[str, list[str]] = {task_id: [] for task_id in snapshot.tasks}
    indegree: dict[str, int] = {task_id: 0 for task_id in snapshot.tasks}

    for dep in snapshot.dependencies:
        if dep.task_id not in snapshot.tasks:
            raise DatasetError(f"dependency references unknown task {dep.task_id}")
        if dep.prerequisite_task_id not in snapshot.tasks:
            raise DatasetError(
                f"dependency references unknown prerequisite {dep.prerequisite_task_id}"
            )
        if dep.task_id == dep.prerequisite_task_id:
            raise DatasetError(f"self dependency for task {dep.task_id}")
        left = snapshot.tasks[dep.task_id]
        right = snapshot.tasks[dep.prerequisite_task_id]
        if left.workflow_id != right.workflow_id:
            raise DatasetError(
                f"cross-workflow dependency: {dep.task_id} <- {dep.prerequisite_task_id}"
            )
        outgoing[dep.prerequisite_task_id].append(dep.task_id)
        indegree[dep.task_id] += 1

    queue = [task_id for task_id, degree in indegree.items() if degree == 0]
    visited = 0
    cursor = 0
    while cursor < len(queue):
        task_id = queue[cursor]
        cursor += 1
        visited += 1
        for dependent in outgoing[task_id]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    if visited != len(snapshot.tasks):
        raise DatasetError("dependency graph contains a cycle")

    for event in snapshot.events:
        if event.task_id not in snapshot.tasks:
            raise DatasetError(
                f"event {event.event_id} references unknown task {event.task_id}"
            )
