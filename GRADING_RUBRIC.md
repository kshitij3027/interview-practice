# Grading Rubric — 100 points

## 1. Functional correctness — 20 points
- **Excellent (18–20):** Selected-account health evaluation works end to end, effective vs derived classifications are both correct, explanation is useful, and existing override behavior still works.
- **Acceptable (14–17):** Core evaluation works with limited gaps in explanation or one secondary path.
- **Partial (8–13):** Happy path works but important semantics or UI reconciliation are incomplete.
- **Failing (0–7):** Feature is largely non-functional or materially incorrect.

## 2. Backend/domain behavior — 24 points
Evaluate event-time selection, global observation-ID deduplication, deterministic tie-breaking, `as_of` filtering, metric freshness, missing-value semantics, supported operators, all-conditions rule matching, first-match precedence, default classification, manual-override precedence, and snapshot revisions.

- **Excellent (21–24):** Domain behavior is deterministic, centralized/testable, and correct across the rule model.
- **Acceptable (16–20):** Mostly correct with one meaningful semantic gap.
- **Partial (9–15):** Several semantics are implemented inline or incorrectly.
- **Failing (0–8):** Straightforward last-row/counting logic or browser-authoritative policy evaluation.

## 3. Frontend behavior — 12 points
Evaluate selected-account report rendering, effective-vs-derived explanation, loading state, preservation of raw signals/account list, override-triggered reconciliation, and keeping last known-good evaluation on transient failure.

## 4. Integration & stale-response correctness — 14 points
Evaluate account/dataset revision propagation, stale delayed responses after override changes, account-switch request races, and coherent reconciliation without a full reload.

## 5. Edge cases & safety — 18 points
High-value evaluator checks include:
- duplicated `observation_id` with differing payloads;
- shuffled JSONL file order;
- same metric timestamp requiring deterministic tie-break;
- observation after `as_of`;
- stale latest metric vs never-observed metric;
- `{ "missing": true }` and `{ "missing": false }` behavior;
- first matching rule winning when later rules also match;
- manual override masking, but not erasing, the derived result;
- delayed response returning after a newer override revision;
- switching accounts while an older request is pending.

A visually correct happy path should receive fewer than half the points in this section if these semantics are not handled.

## 6. Tests — 6 points
- **5–6:** Focused tests cover the highest-risk deterministic semantics and at least one stale/race behavior.
- **3–4:** Meaningful feature tests beyond a basic happy path.
- **1–2:** Superficial tests only.
- **0:** No useful feature tests.

## 7. Code quality — 3 points
Reasonable boundaries, clear naming, no unnecessary framework rewrite, and policy logic that can be reasoned about independently of transport/UI code.

## 8. Verification/debugging — 3 points
Evidence the candidate ran existing tests/build, exercised the feature end to end, and deliberately checked at least one failure or stale-state path.

## Overall calibration
- **90–100 — Excellent:** Robust under evaluator cases; strong semantics, integration, and verification.
- **75–89 — Good/acceptable:** Core feature is solid with a few bounded gaps.
- **60–74 — Partial:** Useful progress, but at least one major correctness dimension remains weak.
- **Below 60 — Failing/incomplete:** Happy-path-only, brittle, or materially broken.

A solution that simply takes the last JSONL row for each metric and displays a classification, without correct dedupe/order/freshness/rule precedence/revision-race handling, should **not score above roughly 60–65** even if the UI looks polished.
