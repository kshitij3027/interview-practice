# POST-PRACTICE ONLY — GateQueue Interviewer Notes

## Intended underlying structure
Treat the snapshot as a static dependency DAG plus a time-ordered stream of reversible task-state changes. A strong exact implementation preprocesses task/dependency indexes, reorders historical queries by time while preserving their original output positions, applies state changes incrementally, tracks how many direct prerequisites of each task are currently incomplete, and keeps efficient per-workflow access to runnable tasks in the required business order.

## Strong solution approaches
A global historical sweep or a per-workflow sweep are both defensible. When a task actually changes completion state, update only its direct dependents. Repeated complete/reopen actions that do not change state must not update counts. For top results, a lazy priority structure with validity/version checks or another ordered structure can work.

## Complexity
With T tasks, D dependencies, E events, Q queries, and F dependent-edge updates caused by real state changes, a strong design is around O(T + D + E log E + Q log Q) preprocessing plus O(F log T + output work) for the sweep, subject to the chosen ordered structure. A gate with 100k direct dependents legitimately costs proportional work when it flips state.

## Why naive approaches fail
Replaying all events for every query is Q×E-shaped work. Rechecking every task/dependency on each query approaches Q×(T+D). Input-order query processing fails when queries move backward in time. File-order event processing fails on shuffled data. Destructive top-k extraction can incorrectly alter later read-only results.

## Subtle traps and hidden checks
- Events exactly at as_of are visible.
- Offset-equivalent timestamps must compare as the same instant.
- Same-task/same-time changes follow ascending version.
- Repeated complete or reopen actions are no-ops when state is already equal.
- A prerequisite can complete, reopen, and complete again, toggling an unfinished dependent ready/blocked/ready.
- Completed descendants do not automatically reopen.
- Duplicate dependency rows and duplicate event deliveries count once.
- Ordering is priority descending, then due time ascending, then task_id.
- Invalid queries are isolated; unknown workflow and malformed query have different reasons.
- Lazy ordering structures need protection against stale entries during repeated readiness oscillation.

## Alternative defensible designs
Per-workflow sweeps, checkpointed historical states, or a custom ordered set/tree are all reasonable. External sorting/sharding can be discussed for the 50M-event production shape. Approximate readiness or ranking gives up the exact output contract.

## Likely AI-agent failure modes
Common failures are per-query DFS over the tiny fixture, ignoring historical as_of, sorting by due date before priority, applying duplicate/no-op events more than once, inventing descendant-reopen cascades, mishandling arbitrary query order, or permanently removing runnable tasks while answering one query.

## What should be discovered from the data
The fixture contains a prerequisite that completes, reopens, and later completes again; a task that has two same-instant versions; a duplicate dependency row; a duplicate event delivery; and two queries that encode the same instant with different offsets.

## Recommended prioritization
First establish exact state/readiness semantics, then build reusable indexes, implement the historical processing path, verify reopen/no-op/time-boundary behavior, and finish by checking complexity and deterministic ordering.

## Walkthrough inspection points
Inspect duplicate handling, real state flips vs no-ops, direct-dependent updates, arbitrary historical query order, non-mutating top-k selection, high-fanout behavior, stale-ordering cleanup, and stated time/space complexity.
