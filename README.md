# EvalBoard — HARD One-Hour Full-Stack Interview Exercise

## Context
EvalBoard is an internal AI-evaluation console. The runnable starter uses a Node.js 20+ standard-library HTTP API, an in-memory fixture-backed store, and dependency-free browser ES modules. Engineers can filter evaluation suites, inspect suite details and available runs, and edit an owner note with optimistic concurrency.

## Existing behavior
- Suites are ordered by owner, name, then ID and can be filtered by owner/status.
- Detail shows dataset version, approved run, available runs, note, suite revision, and dataset revision.
- Note writes require the observed suite revision. Stale writes do not mutate.
- A changed trimmed note increments suite and global dataset revision once; the same normalized note is a no-op.
- Restarting restores checked-in fixtures.

Supplied data: fixtures/suites.json, fixtures/runs.json, fixtures/cases.json, and fixtures/observations.jsonl.

## Customer / business problem
Engineers currently compare offline evaluation exports manually before changing which model run is approved. Worker retries produce multiple observations for one case; candidate runs can be incomplete; important cases can regress even when averages look good; latency and cost also matter. Approval must remain safe when suite state changes during a delayed request or when a request is retried.

## Primary feature request
Add a server-authoritative candidate-vs-approved-baseline comparison and approval workflow. The user chooses a candidate run, requests a comparison, sees gate results plus case regressions, and can approve only when current server state still permits it.

## Deterministic evaluation semantics
Cases are rows matching the suiteId and datasetVersion. Each has positive integer weight and severity low, medium, high, or critical.

For each runId/caseId pair choose the effective observation by:
1. greatest numeric attempt;
2. then greatest recordedAt instant;
3. then lexicographically greatest observationId.

Row order must not matter. Missing observations and effective status=error are not covered. Covered observations require qualityMilli 0..1000, positive latencyMs, and non-negative costMicrousd.

Metrics:
- weighted coverage = covered case weight / total case weight;
- weighted quality = sum(qualityMilli * weight) / covered weight;
- p95 latency = nearest-rank percentile using rank ceil(0.95 * n);
- average cost = arithmetic mean costMicrousd across covered cases.

A candidate passes only when:
- weighted coverage is at least 95%;
- weighted quality is no more than 15 milli-points below baseline;
- p95 latency is no more than 20% above baseline;
- average cost is no more than 25% above baseline;
- every critical case is covered and no more than 40 milli-points below its baseline quality.

Threshold behavior must be deterministic; do not base pass/fail on rounded display values.

## Acceptance criteria
1. Add candidate selection and Compare UI without breaking current list/filter/detail/note behavior.
2. Compare only a run belonging to the selected suite. Reject dataset-version mismatch and comparing the approved run to itself.
3. Server owns case selection, effective observation selection, metrics, gate decisions, and approval eligibility.
4. Implement attempt/timestamp/ID precedence and input-order independence exactly.
5. Missing/error cases lower coverage but are excluded from quality, latency, and cost aggregates; zero coverage must have safe explicit output.
6. Return structured gate diagnostics and deterministic case-level regression information.
7. Malformed required fixture data must fail clearly rather than being guessed.
8. Comparison supports bounded delay_ms.
9. A slower obsolete comparison response must not repaint a newer suite/candidate comparison.
10. Comparison failure preserves last-known-good workspace/result when possible and shows an error.
11. Add Approve candidate. The request includes candidate run ID, a client request key, and the suite revision observed with the comparison.
12. Approval recomputes eligibility against current approved baseline/current server data; never trust client-supplied metrics or pass flags.
13. Approval requires active suite, current submitted revision, matching dataset version, and a freshly passing gate.
14. Approval supports bounded delay_ms so an intervening owner-note update can make it fail stale with zero promotion mutation.
15. Success changes approvedRunId and increments suite revision and global dataset revision exactly once while preserving note/metadata.
16. Request-key retry with the same normalized logical payload returns the original result with no new mutation. Same key with different candidate/revision fails. delay_ms does not define payload identity.
17. After success, reconcile list/detail/revisions without full reload, preserve valid filters, and clear or refresh comparison state for the new baseline.
18. Delayed approval responses must not overwrite a different suite opened meanwhile.
19. Prevent accidental duplicate in-flight Compare/Approve submissions without disabling normal browsing.
20. Existing starter tests and behavior must continue to pass.

## Constraints
Keep the existing no-framework Node/browser stack, one-process in-memory state, and server-owned fixtures. Do not add a database, external API, queue, websocket, or actual model call. Production may have about 50,000 cases with several observations per case, so avoid obviously quadratic matching.

## Out of scope
Authentication, running an LLM, uploading/editing evaluation artifacts, persistence across restart, background workers, distributed locking, charts, and visual polish.

## Setup / verification
Run:
    ./scripts/test.sh
    ./scripts/build.sh
    ./scripts/verify.sh
    ./scripts/run.sh

Open http://localhost:8080

## 60-minute AI-assisted interview instruction
You have 60 minutes and may use Claude Code, Codex, ChatGPT, or similar tools. Inspect fixtures, mutation/revision boundaries, routes, and browser state before coding. Implement incrementally and verify normal, incomplete-run, threshold-boundary, stale, retry, and slow/out-of-order behavior.
