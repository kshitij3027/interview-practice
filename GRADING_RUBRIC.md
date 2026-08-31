# RiskPulse Grading Rubric — 100 points

Evaluator-only. Do not copy this file to the candidate branch.

## 1. Problem decomposition and semantic model — 15 points

- 13–15: Clearly separates arrival order, partition retry semantics, event-time finalization, merchant window state, and alert suppression. Explains boundary choices accurately.
- 9–12: Mostly correct decomposition with one minor ambiguity that does not undermine the design.
- 5–8: Understands sliding windows but muddles watermark/finalization or retry semantics.
- 0–4: Treats input order as event order or lacks a coherent state model.

## 2. Event-time ordering and lateness correctness — 25 points

Award for all of the following:

- compares an arriving event against the watermark derived from previously accepted events;
- accepts equality at the watermark and rejects only strict lateness;
- updates the max-seen timestamp only through accepted unique events;
- finalizes buffered events only when their timestamp is strictly earlier than the watermark;
- flushes all remaining buffered events at EOF;
- applies finalized events in deterministic `(occurred_at, event_id)` order;
- too-late events never affect merchant state.

23–25 requires all major boundaries correct. 16–22 allows one localized edge-case bug. 8–15 indicates a generally useful reorder design with substantive semantic errors. 0–7 is arrival-order processing, batch sorting of all history per step, or otherwise incorrect.

## 3. Merchant window and alert semantics — 20 points

- Maintains `[t-window_seconds, t]` exactly; events at the lower bound remain active.
- Counts only finalized declines.
- Tracks total declines and distinct card fingerprints correctly as events expire.
- Applies both thresholds.
- Enforces cooldown per merchant and allows equality at the boundary.
- Approvals do not trigger alerts.
- Alert payload counts/timestamps are accurate and deterministic.

18–20: complete; 13–17: one minor bug; 7–12: happy path only; 0–6: rescans history or produces materially incorrect counts.

## 4. Partition idempotency, corruption detection, and validation — 15 points

- Exact retry of current highest partition sequence is ignored once.
- Same sequence with conflicting contents fails.
- Sequence regression fails.
- Unknown merchant fails.
- Input timestamp/string/sequence validation remains intact or improves.
- Retry never enters the reorder buffer twice.

13–15: robust; 9–12: one missed validation; 5–8: duplicate handling exists but conflates retry and corruption; 0–4: no reliable source-sequence handling.

## 5. Complexity and production credibility — 10 points

- Avoids sorting all history or rescanning all merchant history per event.
- Reorder work scales with the live lateness buffer rather than total historical input.
- Merchant state expires incrementally.
- Candidate can explain time/memory complexity and hot-merchant/lateness-pathology behavior.

9–10: strong scaling argument; 6–8: acceptable with a visible hotspot; 3–5: works on fixture but not credible at stated scale; 0–2: explicitly unbounded or quadratic-style design.

## 6. Verification and adversarial testing — 10 points

High-value tests cover several of: watermark equality, strict finalization, same-time ordering, too-late exclusion, duplicate retry, conflicting retry, sequence regression, exact window boundary, exact cooldown boundary, EOF flush, approvals, multi-merchant isolation.

9–10: focused adversarial suite; 6–8: good core coverage; 3–5: mostly happy-path tests; 0–2: little meaningful verification.

## 7. Code quality and walkthrough — 5 points

Readable state ownership, clear names, no accidental global coupling, useful error messages, and a walkthrough that can defend the implementation choices.

## Score calibration

A solution that merely sorts the fixture once, ignores streaming/watermark semantics, or gets only the obvious decline threshold path should not exceed **55–60 points**, even if it produces plausible sample output. Correctness under event-time ordering and boundary behavior carries more weight than CLI polish.

No points are reserved for using an LLM. A deterministic implementation is fully valid. An LLM/heuristic component receives credit only if the candidate can preserve every exact observable guarantee and justify the operational tradeoff.
