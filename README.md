# ReturnDock — HARD One-Hour Full-Stack Interview Exercise

## Context

ReturnDock is an internal warehouse-operations console for a marketplace returns team. Operators use it to inspect open return cases, filter them by warehouse or receipt state, and add or clear a manual exception when a package needs human follow-up.

The starter application already works. It uses a Go 1.23 standard-library HTTP API, an in-memory fixture-backed domain store, a dependency-free browser ES-module frontend with explicit client state, and existing tests for the current manual-exception workflow.

## Existing behavior

- The dashboard lists return cases ordered by warehouse, then created time, then return ID.
- Operators can filter by warehouse and receipt state (`awaiting`, `partial`, `received`).
- Selecting a return shows the expected parcel IDs, parcels already received, case revision, and current manual exception.
- Operators can add or clear one manual exception with a non-empty reason.
- Exception writes require the case revision observed by the client. Stale writes fail without mutation.
- A changed exception increments that case revision and the global dataset revision exactly once. Repeating the same exception value/reason is a no-op.
- Restarting the backend resets state from the checked-in fixtures.

## Customer/business problem

Warehouse receipt scanners export batches of carrier events into `fixtures/carrier_scans.csv`. The feed is realistic rather than clean: rows may be duplicated, conflicting rows may reuse a scan ID, scans can arrive out of order, a parcel may appear in more than one still-open return because labels are occasionally reused, and a later event can retract an earlier physical receipt.

Today operators compare the carrier CSV against ReturnDock manually and edit cases one by one. Operations wants a batch reconciliation workflow that explains what each scan batch would change, lets an operator apply the valid case updates, and remains safe when another operator edits a case between preview and apply.

## Primary feature request

**Add a server-authoritative carrier-scan reconciliation workflow that previews one scan batch, deterministically derives each affected return case's parcel receipt state, and applies the valid case changes with partial-conflict reporting and retry safety.**

## Acceptance criteria

1. Add UI controls to choose one `batch_id` present in `fixtures/carrier_scans.csv`, preview it, and apply the preview. The browser must not be the authoritative source of scan rows or derived receipt state.
2. Preview must not mutate return cases. It must return a server-generated opaque preview ID, the dataset revision observed, and per-case proposed changes plus diagnostics.
3. Scan identity is `scan_id`. Exact duplicate rows for the same ID count once. If the same `scan_id` appears with materially different payload, choose one deterministically using greatest `ingested_at`; if those tie, choose the lexicographically greatest canonical payload. Report how many duplicate/conflicting rows were collapsed.
4. For a parcel within the selected batch, derive its effective event from that batch's canonical rows using greatest `scanned_at`, then greatest `ingested_at`, then lexicographically greatest `scan_id`. `received` means the parcel is physically present; `retracted` means it is not. Input row order must never change the result.
5. A scan only affects a return that expects its `parcel_id`. A non-empty `return_id_hint` may disambiguate a reused parcel ID only when that hinted return exists, is not closed, and expects the parcel. Otherwise the scan is invalid or ambiguous and must be reported without changing any case.
6. If exactly one non-closed return expects the parcel, that return is used even when the hint is blank. If multiple non-closed returns expect it and no valid hint selects one, report the parcel as ambiguous and do not guess.
7. A `received` event counts only when its `warehouse` equals the target return's warehouse. A `retracted` event may remove a parcel previously marked received only for the same resolved return. Unknown return hints, unknown parcel IDs, unsupported event kinds, invalid timestamps, and wrong-warehouse receipts must be reported and must not prevent independent valid rows from being previewed.
8. Proposed case receipt state is derived from the case's current `received_parcels` plus the selected batch's effective parcel events. Receipt status is `awaiting` when zero expected parcels are received, `partial` when some but not all are received, and `received` when all expected parcels are received. Never count a parcel not present in that case's expected parcel list.
9. A preview must capture the revision of every case it proposes to change. Cases for which the batch produces no effective change may be reported but must not be treated as mutations.
10. Apply must reference the server-owned preview ID rather than trusting client-authored parcel lists or statuses. Before changing a proposed case, compare its current revision with the revision captured by preview.
11. Apply is **partially successful by case**: a stale case must be skipped with a conflict result, while independent cases whose captured revisions are still current may be applied. One stale case must not roll back successful independent cases.
12. Each successfully changed case increments its own revision exactly once. The global dataset revision increments exactly once for the overall apply request if at least one case changed, regardless of how many cases succeeded. If nothing changes, the dataset revision does not increment.
13. Apply must accept a client-generated request key. Retrying the same key for the same preview must return the original per-case result without changing any case or revision again. Reusing the key for a different preview must fail clearly.
14. A preview may be applied at most once logically. A second apply with a new request key must not silently re-run the old preview against newer state; return a clear already-applied/consumed result.
15. The apply endpoint must support an optional bounded `delay_ms` query parameter so partial stale behavior can be reproduced locally: start apply, mutate one affected case through the existing manual-exception workflow, then let apply finish.
16. After apply, reconcile the visible case list, selected case detail, case revisions, receipt states, received-parcel lists, dataset revision, and per-case apply results without a full browser reload. Preserve active filters and selection when still valid.
17. On partial conflict, keep the preview/apply explanation visible, refresh current state for conflicted cases, and make a fresh preview straightforward. Do not make skipped cases appear successfully reconciled.
18. If the user changes batch selection or starts a newer preview while an older preview request is in flight, a slower older response must never replace the newer preview in the UI.
19. A transient preview/apply failure must preserve the last known-good case data and preview when available and show an actionable error rather than clearing the workspace.
20. Existing case ordering/filtering, manual-exception validation, no-op behavior, optimistic concurrency, case revisions, and global dataset revision behavior must continue to work unchanged.

## Constraints

- Keep the Go standard-library backend and dependency-free browser ES-module frontend.
- Keep mutable state in one process and in memory; no database, Redis, queue, auth provider, websocket service, or external API.
- `fixtures/carrier_scans.csv` is read-only server-owned input.
- The backend is authoritative for scan canonicalization, parcel-to-return resolution, preview state, receipt-state derivation, revisions, and idempotency results.
- You may add domain/service modules, routes, frontend state/actions, DOM rendering, and focused tests.
- Do not replace the starter with a framework or make setup the main challenge.

## Out of scope

- Uploading arbitrary CSV files from the browser.
- Editing the scan fixture.
- Creating or closing return cases.
- Persisting previews or reconciliation results across process restarts.
- Authentication/authorization or modeling individual operator identity.
- Distributed locking or multiple backend processes.
- Carrier API calls, notifications, or barcode hardware integration.
- Visual polish beyond a clear usable workflow.

## Setup / run

```bash
./scripts/run.sh
```

Open `http://localhost:8080`.

## Tests / build

```bash
./scripts/test.sh
./scripts/build.sh
```

Existing tests cover the current return-case and manual-exception behavior plus fixture loading. Add focused feature tests around the reconciliation semantics you consider highest risk.

## 60-minute interview instruction

You have **60 minutes**. Treat this as an AI-assisted live product-engineering interview. Inspect the return fixtures, scan feed, store mutation boundary, revision behavior, HTTP routes, and frontend state before changing code. Choose a correctness-first slice, implement incrementally, and verify ordinary, retry, partial-conflict, and out-of-order UI behavior.

A polished batch screen that depends on CSV row order, guesses ambiguous parcel ownership, applies stale cases, double-applies a retry, or breaks the existing manual-exception workflow should score poorly. Prioritize observable correctness and dangerous state transitions over cosmetic completeness.
