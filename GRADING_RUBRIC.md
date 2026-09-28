# GateQueue Grading Rubric — 100 points

Evaluator material.

## Scoring

1. Problem decomposition and model — 18 points
2. Algorithm / data-structure choice — 20 points
3. Correctness under the contract — 22 points
4. Complexity and scalability — 12 points
5. Edge cases and malformed data — 10 points
6. Verification and testing — 8 points
7. Code quality — 5 points
8. Explanation and tradeoff defense — 5 points

### 1. Problem decomposition and model — 18 points

Top work precisely models task state, direct-prerequisite readiness, authoritative complete/reopen events, same-instant version ordering, arbitrary historical query order, deterministic business ordering, and reusable preprocessing.

### 2. Algorithm / data-structure choice — 20 points

Top work uses a production-credible strategy that processes historical state transitions incrementally, updates only directly affected readiness metadata, and maintains efficient access to the best currently runnable tasks. Correct handling of removals/re-additions or stale ordering entries matters.

### 3. Correctness under the contract — 22 points

Award for exact event visibility at occurred_at <= as_of, same-time version ordering, no-op transitions, reopen blocking and re-complete unblocking, completed-task exclusion, original query output order, exact deterministic ranking, and query-local invalid results.

### 4. Complexity and scalability — 12 points

Strong answers give honest preprocessing, transition-update, query, and memory complexity and discuss 50M events, 8M dependency edges, high-fanout gates, and stale-entry cleanup where relevant.

### 5. Edge cases and malformed data — 10 points

Look for offset-equivalent timestamps, duplicate deliveries, same-time versions, repeated no-op actions, zero-prerequisite tasks, workflow isolation, unknown workflows, invalid limits, event-at-query boundaries, reopen/recomplete cycles, and deterministic ties.

### 6. Verification and testing — 8 points

Full credit requires focused tests that target semantic boundaries and failure modes rather than only the sample fixture.

### 7. Code quality — 5 points

Readable decomposition, controlled mutation, clear naming, useful invariants, no accidental quadratic copying, and valid JSONL output.

### 8. Explanation and tradeoff defense — 5 points

Candidate can explain why the design is correct, what naive approaches get wrong, where time/memory pressure comes from, and what alternatives trade exactness for simplicity.

## Score cap

A happy-path implementation that independently replays or scans the full event corpus or full workflow for each query, ignores reopen semantics, or cannot defend production behavior should not score above 58/100.
