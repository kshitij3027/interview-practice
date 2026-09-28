from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Workflow:
    workflow_id: str
    customer_id: str
    name: str


@dataclass(frozen=True)
class Task:
    task_id: str
    workflow_id: str
    priority: int
    due_at: datetime


@dataclass(frozen=True)
class Dependency:
    task_id: str
    prerequisite_task_id: str


@dataclass(frozen=True)
class Event:
    event_id: str
    task_id: str
    occurred_at: datetime
    version: int
    action: str


@dataclass(frozen=True)
class Query:
    request_id: str
    workflow_id: str
    as_of: datetime
    limit: int
    valid: bool = True
    invalid_reason: str | None = None


@dataclass(frozen=True)
class Snapshot:
    workflows: dict[str, Workflow]
    tasks: dict[str, Task]
    dependencies: tuple[Dependency, ...]
    events: tuple[Event, ...]
