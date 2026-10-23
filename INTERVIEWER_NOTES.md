# POST-PRACTICE ONLY — CostCanopy Interviewer Notes

**DO NOT SHOW THE CANDIDATE BEFORE THE 60-MINUTE EXERCISE.** This document intentionally discloses the problem structure, strong solutions, hidden checks, and common mistakes.

## Intended underlying structure

The reporting-center catalog is a fixed rooted forest. Validate it and flatten each component via deterministic **iterative** depth-first traversal, assigning every center an entry position and exclusive subtree endpoint. All descendants of a center then occupy one contiguous range. Keep a pair of **Fenwick trees** (or segment trees): one tracks cents at each individual center, the other tracks the count of active charges. Query the two aggregates over the center's subtree.

Keep a charge-state map keyed by immutable charge ID with center position, amount, active flag, and a tombstone when voided. Post adds (amount,1) at a position; revise removes the old contribution and adds the new one, including a move between different roots; void removes the current contribution exactly once. A separate applied-events map stores the canonical payload of successfully applied event IDs, with no request_id and no ignored metadata. Syntactic validation must precede event-ID equality. Event dedup/conflict checks precede current charge-state checks, so a retry after void cannot resurrect a charge. Failed events are never reserved.

Build and validate the center index in O(N) expected time, or O(N log N) including sorting for deterministic traversal. Each mutation changes no more than two points in each indexed aggregate, **O(log N)**; each query performs two range summaries, **O(log N)**; total roughly O(N + (M+Q) log N). Memory O(N+C+E). Python memory overhead may exceed the 768MB target for millions of charge and event objects; candidate should discuss compaction, packed indices, event retention, and measurements rather than assert a guarantee.

Alternatives: tree-ordered segment tree is equally strong; flattening plus balanced cumulative arrays is acceptable if update cost measured; SQL materialized rollups could be defensible operationally but must handle updates and depth efficiently. Explicit ancestor propagation is O(height), reaching 250,000 updates per event on a chain. Scanning every descendant's charges is O(N+C) per query. Precomputed ancestor memberships can be quadratic. Recursive DFS crashes on deep trees.

## Subtle traps / hidden checks

1. Charge amount zero still contributes 1 to active_charges; boolean true is **not** an integer amount.
2. The queried cost center's *own* budget applies to all descendant spending. Budgets of children must not be summed. Over budget means strictly greater, not greater-or-equal.
3. A revise can move a charge from API to WEST, across sibling groups, or from GLOBAL to ALPHA, a different root. Old and new group totals and counts must reconcile.
4. A revise at the same center with identical amount is still a successful new event; it is not automatically an event replay.
5. Post event e1, revise e2, void e3, then replay e1 with another request_id. Response must be duplicate and charge remains voided.
6. Reuse e1 for a different operation or altered amount must yield event_conflict without state change. Do not accidentally resolve a current charge conflict first.
7. Rejected mutation e4 (unknown center or unknown charge) does not reserve e4. Reusing e4 later for a valid operation can apply.
8. Charge IDs are never reusable: after void c1, new post with another event ID for c1 means charge_exists. Later revise or void of c1 means inactive_charge.
9. Two valid events may share a request_id and must each execute: request IDs are correlation fields, not idempotency keys.
10. Multiple independent roots: querying GLOBAL must never include ALPHA. Input row order may change traversal indexing but not computed numeric answers.
11. A chain of 250,000 catalog centers must not use recursive validation or traversal. Verify half-open subtree indices are correct even for leaves and roots.
12. Input JSON may be malformed, an array, null, or missing fields. Emit exactly one invalid response per line and continue. Preserve only syntactically valid request_id.
13. IDs are case-sensitive ASCII with 1–32 length (except request_id up to 128 chars). Numeric money is bounded inclusive by 10^12. Reject floats, booleans, negatives and unsupported types.
14. Catalog may contain identical replay rows; conflicting duplicate definitions, unknown parents or cycles must reject the whole catalog before processing any operation.
15. Event equivalence uses type, charge ID, center ID and amount when relevant. Request ID and ignored extra fields do not affect equivalence.
16. Repeated summaries are not cached forever: invalidate or update cached aggregates after every accepted mutation.
17. Out-of-order *business corrections* still apply in stream order, not sorted by request ID or event ID. There are no historical as-of snapshots.

## What the supplied data should reveal

Fixture centers form two roots (GLOBAL and ALPHA), including a nested zero-budget leaf. Operations show multi-level summaries, same-branch and cross-root changes, a repeated event ID after a void, conflicting event IDs, unknown/voided charges, unknown centers, invalid boolean amount, invalid request ID, and a malformed JSON line near the end. Do not infer the solution merely by inspecting the limited happy path.

## Strong hidden checks

- Generate a chain of 100k centers and interleave 50k summaries with revisions at its bottom. Ancestor walks should fail reasonable performance targets.
- Generate random forests and random mutations, compare summary cents/counts to a slow oracle that walks each active charge's ancestors.
- Post c1 at API with 7 cents; revise to WEST with zero cents; GLOBAL total 0 count 1; then void and replay original post; GLOBAL must stay total 0 count 0.
- Post two charges 2 and 3 cents in DATA, revise one to 0: DATA total 3 count 2. Replay revision with a new request ID: duplicate and unchanged. Conflicting event ID: invalid.
- Query a zero-budget center with zero and then one cent; equality versus strict threshold matters.
- Interleave invalid attempts using the same event ID and a later successful event ID, checking failed attempts never reserve it.
- Shuffle center rows repeatedly. Add ignored metadata to replay, but don't change business payload.
- Include max integer money and thousands of charges; totals may exceed per-charge limit while remaining exact Python integers.

## AI-agent failure modes

Generated code often uses recursive DFS; loops over all ancestors on mutation; accumulates children's budgets instead of local budget; forgets to subtract old center after revise; treats zero charge as inactive; dedups on request_id; includes request_id in event fingerprint; marks unsuccessful events as applied; verifies current charge state before accepting valid replay; treats Python booleans as amounts; floats cents; serializes logs into stdout; stops on malformed JSON, or never implements the missing processor because baseline tests already pass.

## Suggested prioritization and walkthrough

Minutes 0–10: customer and data reading, disambiguate identities and invariants. 10–25: build scalable reporting-group aggregation and prove subgroup sums. 25–42: add mutation lifecycle, canonical replay handling, invalid states. 42–52: exercise adversarial transitions and CLI. 52–60: run original commands, benchmark deep chain, explain complexity and memory tradeoffs. After the hour inspect the actual output schema, preservation of exact 1:1 line mapping, charge tombstones, event replay map, rebooking invariants, deep-chain behavior, and the candidate's ability to explain AI-authored code.
