# ThermoTrace — HARD 60-minute AI-assisted interview

## Context and existing behavior
Pharmaceutical cold-chain operators inspect shipment temperatures to decide whether goods need an inspection hold. The Node.js 20+ starter already runs using a standard-library HTTP API, an in-memory fixture-backed store, and browser ES modules. It lists shipments (site/customer/ID order), filters by site/state, searches ID/customer/product, shows selected details, and edits operator notes using shipment revisions. A changed note increments shipment and global revisions once, a trimmed no-op changes neither, and stale writes return 409. Obsolete list/detail responses do not replace new selections.

## Supplied data and customer need
shipments.json supplies safe [minC,maxC] bands, maxGapSeconds, triggerSeconds, lifecycle, and notes. readings.jsonl contains unsorted observations, duplicate IDs, contradictory older retries, a bad-quality sample, and equivalent instants with different UTC offsets. Operators currently review sensor data manually.

## Primary feature
Build one server-authoritative **temperature-excursion preview and review/hold workflow** for the selected shipment. Preview must be read-only and explain qualifying sustained excursions. Commit recalculates from server input, saves the assessment, sets a sticky temperatureHold on a qualifying excursion, and never automatically releases a hold.

## Acceptance criteria
- Deduplicate by sampleId, preferring greatest receivedAt instant, then lexicographically greatest normalized payload. Flag IDs attributed to multiple shipments. At equal observedAt instant, prefer latest receivedAt, then greatest sampleId. Input row order and timezone text must not affect results.
- Safe bounds are inclusive. Only successive good-quality readings strictly outside the band on the SAME side and separated by 0 < delta <= maxGapSeconds contribute an interval. Poor quality, in-range readings, excessive gaps, and direction changes break runs. Never extrapolate; never combine disjoint runs.
- A contiguous run with duration >= triggerSeconds qualifies. Preview returns holdRecommended, UTC start/end, direction, duration, supporting IDs, warning counts, and observed revision in deterministic order.
- Closed shipments may preview but cannot commit. Real commits advance shipment and global revisions once each; repeating an unchanged assessment with a new key is a no-op.
- Commit accepts expectedRevision, trimmed 8–64-character requestKey, optional integer delayMs 0..1500. The key identifies (shipmentId, expectedRevision), excluding delayMs. Same key/same request replays the ORIGINAL result; a key collision fails. Concurrent identical keys must not double-commit. Revalidate revisions AFTER delay, before mutation; invalid or stale requests mutate nothing.
- UI displays results/hold state, reconciles details without reload, preserves old data after network failures, and ignores delayed responses for a no-longer-selected shipment. Existing note workflow and tests remain green. Add targeted tests.

## Constraints and scope
Production: 200,000 readings/shipment, 5,000 shipments. Keep Node stdlib, one process, no database, framework, SDK, broker, or external API. Out of scope: releasing a hold, real device ingestion, shipping actions, auth, persistence, distributed coordination, and cosmetic polish.

## Start and verification
Run ./scripts/test.sh, ./scripts/build.sh, ./scripts/verify.sh, ./scripts/run.sh. Open http://localhost:8080. No npm install is needed.

## 60-minute AI-assisted interview
Use Claude Code, Codex or similar tools if useful. Inspect the fixtures, running app, store, routes, frontend and tests; implement incrementally, verify edge cases, and defend tradeoffs. One-shot happy paths are insufficient.
