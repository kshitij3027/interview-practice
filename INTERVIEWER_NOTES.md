# POST-PRACTICE ONLY — Interviewer Notes

**Do not read this file before completing the 60-minute exercise.**

## Intended solution outline

A strong solution usually introduces a focused server-side health-policy evaluator rather than putting policy semantics in the route or browser. It should load the policy fixture, build one deterministic canonical observation set, derive the latest eligible state per metric as of the policy cutoff, classify each metric as fresh/stale/missing, then evaluate rules in fixture order. The evaluation should be based on one account/override revision snapshot and return both the policy-derived result and the effective result after manual-override precedence.

For deduplication, any deterministic rule is acceptable if it is documented and independent of file order. One practical choice is to canonicalize duplicate payloads and choose the lexicographically smallest stable representation for a duplicate ID. For equal timestamps across different observations of the same metric, use a stable tie-break such as `observation_id` rather than input order.

The client should treat evaluations as versioned asynchronous work. A request generation/account ID check handles account-switch races; comparing returned account/dataset revisions against the newest locally known revisions handles stale responses after override mutation. A successful override mutation should advance known revisions and trigger/reconcile the health evaluation without losing filters or selection.

## Likely failure modes

- Using JSONL file order as event order.
- Keeping the first or last duplicate solely because it appeared first/last in the file, making shuffled fixtures change results.
- Selecting the latest observation before filtering out post-`as_of` observations.
- Treating stale metrics as fresh values, or treating stale and never-observed identically in the explanation.
- Treating any one condition as enough for a multi-condition rule.
- Evaluating all rules and letting the last match win instead of first-match precedence.
- Treating `missing:false` as equivalent to a numeric comparison.
- Returning only the manual override and losing the underlying derived classification.
- Computing policy results in the browser from raw signals.
- Refreshing after an override but allowing an older delayed promise to repaint stale results afterward.
- Guarding only by revision but not by selected account, so account A's response can overwrite account B's panel.
- Clearing all report/account state when a health request fails.

## Hidden checks / subtle traps

- `obs-003` appears twice with different payloads. Shuffling the fixture must not alter which duplicate wins under the candidate's documented rule.
- `acct-104` has two `weekly_active_ratio` observations at exactly the same timestamp (`obs-007` and `obs-012`); tie-breaking must be stable.
- `acct-105` has a `weekly_active_ratio` observation after policy `as_of`; it cannot become the current value.
- `acct-103`'s usage observation is old enough to exceed its 72-hour freshness window, so the missing-usage rule is relevant even though a historical value exists.
- `acct-102` can satisfy more than one concerning condition depending on duplicate canonicalization; policy order must control the winning classification/rule.
- A stale metric should be described differently from one never seen at all.
- A manual override should change only the effective classification; the derived result remains observable.
- Start a delayed evaluation, then set an override. The delayed response must not visually undo the override.
- Start a delayed evaluation for account A, switch to B, and ensure A's late response cannot replace B's panel.
- Existing stale-write protection for manual overrides must remain intact.

## Expected prioritization

1. Pure/deterministic backend observation canonicalization and metric-state derivation.
2. Rule evaluator plus focused tests for precedence, freshness, and duplicate/tie behavior.
3. Health API contract carrying account/dataset revisions and optional local delay.
4. Minimal frontend health panel.
5. Request-generation/revision guards and override-triggered reconciliation.
6. Error-state polish and extra tests.

A correct backend with a rough but usable UI is preferable to a polished frontend with nondeterministic or stale policy semantics.

## What to inspect after the hour

Look for deterministic helpers that can be unit tested, an explicit distinction among fresh/stale/missing metric states, first-match rule semantics, both derived and effective classifications, revision-aware client reconciliation, preservation of current override invariants, and evidence the candidate deliberately verified races rather than relying only on generated code.
