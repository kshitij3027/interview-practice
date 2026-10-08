# StockAudit — HARD 60-Minute AI-Assisted Full-Stack Interview

## Context
StockAudit is a warehouse cycle-count operations console. A bin stores one SKU and has a case size. Multiple handheld counters may independently count the same bin. The supplied scan feed includes duplicate delivery, later corrections, mixed case/each units, and out-of-order arrival.

The already-working starter uses Node.js 20+ standard-library HTTP, in-memory inventory state, and dependency-free browser ES modules. No npm install is required.

## Existing behavior
- Browse bins sorted by zone then ID, search by bin/SKU/label, and filter by zone and active/locked status.
- Selected bin shows SKU, on-hand units, case size, state, revision and operator note.
- Notes require expectedRevision; a trimmed no-op changes no revisions, a change increments bin and dataset revision once, and a stale write returns 409.
- Slower list/detail responses do not overwrite newly chosen filters or bin selection. Restart restores sample data.

## Customer/business problem
Operators currently combine handheld scanner reports manually. Summing the feed blindly double-counts network retries and independent counters. Taking the last delivered event ignores superseded device corrections, per-case multipliers, and disagreement between devices. Supervisors need an explainable count review before applying an inventory adjustment, even if another operator edits the bin in the meantime.

## Primary feature request
Add ONE server-authoritative cycle-count preview-and-accept workflow to the selected bin. Reconcile the checked-in scanner feed, explain the proposed signed variance, then accept that exact reviewed result with stale-state and retry protection. Implement all coordinated backend, API, domain and browser changes without breaking existing note editing.

## Data and deterministic rules
- Inventory is in fixtures/bins.json; scanner events are split across fixtures/count_scans_*.jsonl. Treat all shards as one unordered feed.
- Each event carries scanId, binId, counter, observedAt, receivedAt, sequence, unit, and quantity. Timestamps are ISO 8601 with explicit UTC offset. Sequence and quantity are positive safe integers. unit is case or each. A case contributes the selected bin's caseSize units.
- Repeated scanId: choose the record with latest receivedAt INSTANT, then lexicographically greatest canonical JSON payload after normalizing timestamps to UTC. An ID reused across bins is conflicting evidence and cannot silently contribute.
- For each (binId,counter,sequence), only one surviving scan contributes: latest receivedAt instant, then greatest scanId. A sequence correction replaces rather than adds to an older scan.
- Sum each counter's surviving scan quantities after unit conversion. Do NOT add different counters together. A bin is reconcilable only if at least one counter exists, all effective counters agree exactly, and no malformed/conflicting evidence affects the bin. Missing scans are not zero.
- Proposed variance = agreedCount - current onHand. A zero variance is a legitimate no-op.

## Acceptance criteria
1. Add Preview Count / Accept Count controls and an understandable per-counter summary, discarded retry/correction counts, conflicts/warnings, reconciled count, and signed variance.
2. Handle unordered data, duplicate IDs, sequence corrections, UTC-equivalent instants, counter disagreement and mixed case/each inputs deterministically, independent of JSONL shard/row order.
3. Validate types, known bin IDs, offset-aware timestamps, units and strictly positive safe integer sequence/quantities. Report bad evidence without crashing unrelated valid bins.
4. Preview must not change inventory quantity, note, lifecycle state, any revision, or accepted review history. Keep the reviewed result on the server under an opaque ID with observed bin revision; do not trust a client-supplied computed count.
5. Reject acceptance for locked bins, non-reconcilable previews and stale observed bin revisions. Revalidate right before mutation (including after any simulated delay). Rejections are atomic and change nothing.
6. A successful changed acceptance sets onHand to the reviewed count, adds exactly one audit entry, and increments bin and dataset revisions exactly once each, regardless of number of scans. Zero variance must not increment inventory revisions.
7. Accept uses a trimmed 8–64 character client request key bound to normalized (binId,previewId). Same key and logical request replays ORIGINAL outcome, without another adjustment; same key with different identity fails. A consumed preview cannot be applied again under a new key.
8. Preview and acceptance support optional integer delayMs 0..1500 for race testing, excluded from idempotency identity. An intervening note edit makes a delayed acceptance stale with zero inventory mutation. Simultaneous identical-key requests cannot double-accept.
9. Reconcile bin detail, current quantity, versions, and audit history in the browser after acceptance. Keep filters/selection and last-known-good data on network error. Stale acceptance should offer a fresh preview without clearing context.
10. Older preview/accept responses must not repaint a newly selected bin. An older preview for the same bin must not supersede a more recent preview. Prevent accidental repeat submissions while browsing remains usable.
11. Preserve baseline filtering/search, note editing, revision/no-op semantics and starter tests; add targeted tests for the new domain and concurrency behavior.

## Constraints and expected deliverable
The production shape is 100,000 bins and millions of scanner events. Design scoped previews without repeatedly scanning the global feed. Keep one-process, fixture-backed, in-memory storage; no database, auth, external scanner integration, queue, web framework, or service SDK. Deliver runnable domain/API/UI behavior, regression-safe code and high-risk tests. Choose and defend your own implementation strategy.

## Out of scope
Physical stock movement, second-person approval, multi-process durability, real device ingestion, permission systems, inventory transfers and visual polish.

## Setup, run, verify
From the repository root run these commands, in order:

    ./scripts/test.sh
    ./scripts/build.sh
    ./scripts/verify.sh
    ./scripts/run.sh

Open http://localhost:8080. Optional: PORT=8081 ./scripts/run.sh.

## 60-minute AI-assisted interview instruction
You have exactly 60 minutes. Claude Code, Codex, ChatGPT or other AI assistants may be used. Inspect fixture shards, store revision boundaries, API routes, browser request ordering and starter tests before coding. Implement incrementally. Verify duplicate scans, conflicting device evidence, unit conversion, stale delayed acceptance, safe retries and preserving the existing note workflow. A happy-path-only build is insufficient.
